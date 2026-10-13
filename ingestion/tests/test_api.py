"""Tests for the SGS and SIDRA loaders using fake HTTP responses (no network)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from ingestion.db import connect
from ingestion.sgs import date_windows, load_sgs
from ingestion.sidra import load_sidra


@pytest.fixture()
def con(tmp_path: Path):
    connection = connect(tmp_path / "t.duckdb")
    yield connection
    connection.close()


def sgs_fetch(value: str = "5.0"):
    def fetch(url: str):
        return [{"data": "01/01/2026", "valor": value}, {"data": "02/01/2026", "valor": value}]
    return fetch


def test_date_windows_cover_range_without_overlap():
    wins = date_windows(date(2022, 1, 1), date(2026, 10, 12))
    assert wins[0][0] == date(2022, 1, 1) and wins[-1][1] == date(2026, 10, 12)
    for (_, prev_end), (next_start, _) in zip(wins, wins[1:], strict=False):
        assert (next_start - prev_end).days == 1


def test_sgs_loads_each_series_and_keeps_strings(con):
    start, end = date(2026, 1, 1), date(2026, 1, 31)
    res = load_sgs(con, start=start, end=end, fetch=sgs_fetch())
    assert [r.status for r in res] == ["loaded"] * 3
    n, valor = con.execute("SELECT count(*), min(valor) FROM raw.bcb_sgs").fetchone()
    assert n == 6 and valor == "5.0"


def test_sgs_second_run_skipped_and_force_is_idempotent(con):
    start, end = date(2026, 1, 1), date(2026, 1, 31)
    load_sgs(con, start=start, end=end, fetch=sgs_fetch())
    assert {r.status for r in load_sgs(con, start=start, end=end, fetch=sgs_fetch())} == {"skipped"}
    load_sgs(con, start=start, end=end, fetch=sgs_fetch(), force=True)
    assert con.execute("SELECT count(*) FROM raw.bcb_sgs").fetchone()[0] == 6


def test_sgs_changed_payload_replaces_rows(con):
    start, end = date(2026, 1, 1), date(2026, 1, 31)
    load_sgs(con, start=start, end=end, fetch=sgs_fetch("5.0"))
    load_sgs(con, start=start, end=end, fetch=sgs_fetch("6.0"))
    assert con.execute("SELECT DISTINCT valor FROM raw.bcb_sgs").fetchall() == [("6.0",)]


def test_sgs_empty_payload_fails_and_keeps_existing_data(con):
    start, end = date(2026, 1, 1), date(2026, 1, 31)
    load_sgs(con, start=start, end=end, fetch=sgs_fetch())
    res = load_sgs(con, start=start, end=end, fetch=lambda url: [])
    assert {r.status for r in res} == {"failed"}
    assert con.execute("SELECT count(*) FROM raw.bcb_sgs").fetchone()[0] == 6


def test_sgs_one_series_failing_does_not_block_others(con):
    def fetch(url: str):
        if "sgs.11/" in url:
            raise RuntimeError("boom")
        return [{"data": "01/01/2026", "valor": "1"}]

    res = load_sgs(con, start=date(2026, 1, 1), end=date(2026, 1, 31), fetch=fetch)
    assert {r.source_file: r.status for r in res} == {
        "sgs/1": "loaded", "sgs/11": "failed", "sgs/432": "loaded",
    }


SIDRA_PAYLOAD = [
    {"NC": "Nível", "V": "Valor", "D2C": "Variável (Código)", "D3N": "Mês"},  # header row
    {"V": "0.82", "MN": "%", "D2C": "63", "D2N": "IPCA - Variação mensal",
     "D3C": "202609", "D3N": "setembro 2026", "D4C": "7169", "D4N": "Índice geral"},
    {"V": "-0.32", "MN": "%", "D2C": "63", "D2N": "IPCA - Variação mensal",
     "D3C": "202608", "D3N": "agosto 2026", "D4C": "7169", "D4N": "Índice geral"},
]


def test_sidra_drops_header_and_keeps_values(con):
    res = load_sidra(con, fetch=lambda url: SIDRA_PAYLOAD)
    assert res[0].status == "loaded" and res[0].rows_loaded == 2
    rows = con.execute(
        "SELECT periodo_codigo, valor FROM raw.ibge_ipca ORDER BY periodo_codigo"
    ).fetchall()
    assert rows == [("202608", "-0.32"), ("202609", "0.82")]


def test_sidra_idempotent_and_bad_shape_fails(con):
    load_sidra(con, fetch=lambda url: SIDRA_PAYLOAD)
    assert load_sidra(con, fetch=lambda url: SIDRA_PAYLOAD)[0].status == "skipped"
    bad = load_sidra(con, fetch=lambda url: {"erro": "x"})
    assert bad[0].status == "failed"
    assert con.execute("SELECT count(*) FROM raw.ibge_ipca").fetchone()[0] == 2
