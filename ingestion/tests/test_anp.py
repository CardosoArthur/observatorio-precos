"""Tests for the ANP raw loader, using tiny CSVs that mimic the real files."""
from __future__ import annotations

from pathlib import Path

import pytest

from ingestion import anp
from ingestion.db import connect

BOM = "﻿"


def make_row(
    *,
    cnpj: str = " 12.486.809/0004-05",
    produto: str = "GASOLINA",
    data: str = "01/09/2026",
    valor: str = "7,25",
) -> list[str]:
    return [
        "N", "AC", "RIO BRANCO", "POSTO TESTE LTDA", cnpj, "AVENIDA BRASIL", "100", "",
        "CENTRO", "69900-000", produto, data, valor, "", "R$ / litro", "VIBRA",
    ]


def write_csv(
    path: Path,
    rows: list[list[str]],
    *,
    header: tuple[str, ...] = anp.SOURCE_COLUMNS,
    empty_lines: int = 0,
) -> None:
    """Write a CSV like ANP does: UTF-8 with BOM, CRLF, ';' separator."""
    lines = [";".join(header)] + [";".join(r) for r in rows]
    lines += [";" * (len(header) - 1)] * empty_lines
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((BOM + "\r\n".join(lines) + "\r\n").encode("utf-8"))


@pytest.fixture()
def raw_dir(tmp_path: Path) -> Path:
    root = tmp_path / "raw" / "anp"
    write_csv(
        root / "semestral" / "a.csv",
        [make_row(), make_row(produto="ETANOL", valor="4,99"), make_row(data="02/09/2026")],
        empty_lines=2,
    )
    write_csv(root / "mensal" / "b.csv", [make_row(data="03/09/2026"), make_row(valor="7,30")])
    return root


@pytest.fixture()
def con(tmp_path: Path):
    connection = connect(tmp_path / "warehouse.duckdb")
    yield connection
    connection.close()


def count(con, where: str = "1=1") -> int:
    return con.execute(f"SELECT count(*) FROM raw.anp_precos WHERE {where}").fetchone()[0]


def statuses(results: list[anp.LoadResult]) -> dict[str, str]:
    return {r.source_file: r.status for r in results}


def test_loads_values_as_raw_strings_and_drops_empty_lines(con, raw_dir):
    results = anp.load_anp(con, raw_dir)

    assert statuses(results) == {"mensal/b.csv": "loaded", "semestral/a.csv": "loaded"}
    assert count(con) == 5  # 3 + 2 real rows; the 2 empty lines were dropped
    row = con.execute(
        "SELECT cnpj_revenda, valor_venda, data_coleta, complemento FROM raw.anp_precos "
        "WHERE _source_file = 'semestral/a.csv' AND produto = 'ETANOL'"
    ).fetchone()
    # raw keeps source text untouched: leading space, decimal comma, dd/mm/yyyy, empty -> NULL
    assert row == (" 12.486.809/0004-05", "4,99", "01/09/2026", None)


def test_source_group_comes_from_folder(con, raw_dir):
    anp.load_anp(con, raw_dir)
    groups = dict(
        con.execute(
            "SELECT _source_file, any_value(_source_group) FROM raw.anp_precos GROUP BY 1"
        ).fetchall()
    )
    assert groups == {"semestral/a.csv": "semestral", "mensal/b.csv": "mensal"}


def test_metadata_records_counts(con, raw_dir):
    anp.load_anp(con, raw_dir)
    row = con.execute(
        "SELECT rows_read, rows_dropped_empty, rows_loaded, status, length(file_sha256) "
        "FROM raw._load_metadata WHERE source_file = 'semestral/a.csv'"
    ).fetchone()
    assert row == (5, 2, 3, "success", 64)


def test_second_run_skips_unchanged_files_and_does_not_duplicate(con, raw_dir):
    anp.load_anp(con, raw_dir)
    results = anp.load_anp(con, raw_dir)

    assert set(statuses(results).values()) == {"skipped"}
    assert count(con) == 5
    assert con.execute("SELECT count(*) FROM raw._load_metadata").fetchone()[0] == 2


def test_force_reload_is_idempotent(con, raw_dir):
    anp.load_anp(con, raw_dir)
    results = anp.load_anp(con, raw_dir, force=True)

    assert set(statuses(results).values()) == {"loaded"}
    assert count(con) == 5  # replaced, not appended


def test_changed_file_replaces_only_its_own_rows(con, raw_dir):
    anp.load_anp(con, raw_dir)
    write_csv(raw_dir / "semestral" / "a.csv", [make_row(valor="9,99")])

    results = anp.load_anp(con, raw_dir)

    assert statuses(results) == {"mensal/b.csv": "skipped", "semestral/a.csv": "loaded"}
    assert count(con, "_source_file = 'semestral/a.csv'") == 1
    assert count(con, "_source_file = 'mensal/b.csv'") == 2
    assert count(con, "valor_venda = '9,99'") == 1


def test_raw_keeps_overlap_between_files(con, tmp_path):
    root = tmp_path / "raw"
    write_csv(root / "mensal" / "m.csv", [make_row()])
    write_csv(root / "ultimas_4_semanas" / "u.csv", [make_row()])

    anp.load_anp(con, root)

    # same natural key delivered by two files: raw keeps both, staging will dedupe
    assert count(con) == 2


def test_header_drift_fails_without_loading_rows(con, tmp_path):
    root = tmp_path / "raw"
    bad_header = anp.SOURCE_COLUMNS[:-1]  # last column missing
    write_csv(root / "semestral" / "bad.csv", [make_row()[:-1]], header=bad_header)

    results = anp.load_anp(con, root)

    assert results[0].status == "failed"
    assert "SchemaDriftError" in (results[0].error or "")
    assert count(con) == 0
    failed = con.execute(
        "SELECT status, error FROM raw._load_metadata WHERE source_file = 'semestral/bad.csv'"
    ).fetchone()
    assert failed[0] == "failed" and "SchemaDriftError" in failed[1]


def test_one_bad_file_does_not_block_the_others(con, raw_dir):
    write_csv(raw_dir / "semestral" / "bad.csv", [make_row()[:-1]], header=anp.SOURCE_COLUMNS[:-1])

    results = anp.load_anp(con, raw_dir)

    assert statuses(results)["semestral/bad.csv"] == "failed"
    assert count(con) == 5  # the two good files still loaded


def test_no_files_raises(con, tmp_path):
    with pytest.raises(FileNotFoundError):
        anp.load_anp(con, tmp_path / "empty")
