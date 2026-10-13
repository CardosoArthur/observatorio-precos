"""Load ANP fuel-price CSV files into the DuckDB raw layer.

The raw table keeps every value exactly as delivered (all VARCHAR). The only
changes are structural: fully empty lines are dropped and lineage columns are
added. Typing, cleaning and de-duplication belong to dbt staging.

Idempotency: each file is replaced atomically (delete its rows + insert, in one
transaction) and a file whose SHA-256 is unchanged is skipped.
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from ingestion.db import RAW_SCHEMA, ensure_metadata_table

log = logging.getLogger(__name__)

SOURCE = "anp"
TABLE = f"{RAW_SCHEMA}.anp_precos"
METADATA_TABLE = f"{RAW_SCHEMA}._load_metadata"

# Header exactly as published by ANP, and the snake_case names used in raw.
SOURCE_COLUMNS = (
    "Regiao - Sigla", "Estado - Sigla", "Municipio", "Revenda", "CNPJ da Revenda",
    "Nome da Rua", "Numero Rua", "Complemento", "Bairro", "Cep", "Produto",
    "Data da Coleta", "Valor de Venda", "Valor de Compra", "Unidade de Medida",
    "Bandeira",
)
RAW_COLUMNS = (
    "regiao_sigla", "estado_sigla", "municipio", "revenda", "cnpj_revenda",
    "nome_rua", "numero_rua", "complemento", "bairro", "cep", "produto",
    "data_coleta", "valor_venda", "valor_compra", "unidade_medida", "bandeira",
)

CSV_OPTIONS = "delim=';', quote='\"', escape='\"', header=true"
COLUMNS_SPEC = "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in RAW_COLUMNS) + "}"


class SchemaDriftError(ValueError):
    """The CSV header does not match the expected ANP layout."""


@dataclass(frozen=True)
class LoadResult:
    source_file: str
    status: str  # "loaded" | "skipped" | "failed"
    rows_read: int = 0
    rows_dropped_empty: int = 0
    rows_loaded: int = 0
    error: str | None = None


def ensure_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Create the raw table and the load-metadata table if they do not exist."""
    ensure_metadata_table(con)
    columns = ",\n    ".join(f"{c} VARCHAR" for c in RAW_COLUMNS)
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            {columns},
            _source_file  VARCHAR   NOT NULL,
            _source_group VARCHAR   NOT NULL,
            _ingested_at  TIMESTAMP NOT NULL
        )
        """
    )


def discover_files(raw_dir: Path) -> list[Path]:
    """All CSV files under raw_dir, in a stable order."""
    return sorted(p for p in raw_dir.rglob("*.csv") if p.is_file())


def source_file_key(path: Path, raw_dir: Path) -> str:
    """Stable, OS-independent identifier of a file (relative POSIX path)."""
    return path.relative_to(raw_dir).as_posix()


def source_group(path: Path, raw_dir: Path) -> str:
    """First folder under raw_dir (semestral, mensal, ...) or 'root'."""
    parts = path.relative_to(raw_dir).parts
    return parts[0] if len(parts) > 1 else "root"


def read_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        first_line = fh.readline().rstrip("\r\n")
    return tuple(name.strip() for name in first_line.split(";"))


def validate_header(path: Path) -> None:
    header = read_header(path)
    if header != SOURCE_COLUMNS:
        raise SchemaDriftError(
            f"Unexpected header in {path.name}: expected {len(SOURCE_COLUMNS)} columns "
            f"{SOURCE_COLUMNS}, got {len(header)} columns {header}"
        )


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _read_csv_sql(path: Path) -> str:
    return f"read_csv({_sql_literal(path.as_posix())}, {CSV_OPTIONS}, columns={COLUMNS_SPEC})"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _already_loaded(con: duckdb.DuckDBPyConnection, rel: str, digest: str) -> bool:
    """True when the same file content was loaded and its rows are still there."""
    row = con.execute(
        f"""
        SELECT file_sha256, rows_loaded FROM {METADATA_TABLE}
        WHERE source = ? AND source_file = ? AND status = 'success'
        ORDER BY loaded_at DESC LIMIT 1
        """,
        [SOURCE, rel],
    ).fetchone()
    if row is None or row[0] != digest:
        return False
    current = con.execute(
        f"SELECT count(*) FROM {TABLE} WHERE _source_file = ?", [rel]
    ).fetchone()[0]
    return current == row[1]


def _record_metadata(
    con: duckdb.DuckDBPyConnection,
    *,
    rel: str,
    digest: str,
    size: int,
    status: str,
    rows_read: int | None,
    rows_dropped: int | None,
    rows_loaded: int | None,
    error: str | None,
    loaded_at: datetime,
    duration: float,
) -> None:
    con.execute(
        f"INSERT INTO {METADATA_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [SOURCE, rel, digest, size, rows_read, rows_dropped, rows_loaded,
         status, error, loaded_at, duration],
    )


def _replace_file_rows(
    con: duckdb.DuckDBPyConnection,
    path: Path,
    rel: str,
    group: str,
    digest: str,
    size: int,
    started: float,
) -> tuple[int, int, int]:
    """Atomically replace all rows of one file. Returns (read, dropped, loaded)."""
    ingested_at = _utc_now()
    columns = ", ".join(RAW_COLUMNS)
    all_null = " AND ".join(f"{c} IS NULL" for c in RAW_COLUMNS)

    con.execute("BEGIN TRANSACTION")
    try:
        con.execute(f"DELETE FROM {TABLE} WHERE _source_file = ?", [rel])
        con.execute(
            f"CREATE OR REPLACE TEMP TABLE _anp_stage AS SELECT * FROM {_read_csv_sql(path)}"
        )
        rows_read = con.execute("SELECT count(*) FROM _anp_stage").fetchone()[0]
        rows_loaded = con.execute(
            f"""
            INSERT INTO {TABLE}
            SELECT {columns}, ?, ?, ? FROM _anp_stage WHERE NOT ({all_null})
            """,
            [rel, group, ingested_at],
        ).fetchone()[0]
        con.execute("DROP TABLE IF EXISTS _anp_stage")
        rows_dropped = rows_read - rows_loaded
        _record_metadata(
            con, rel=rel, digest=digest, size=size, status="success",
            rows_read=rows_read, rows_dropped=rows_dropped, rows_loaded=rows_loaded,
            error=None, loaded_at=ingested_at, duration=time.monotonic() - started,
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return rows_read, rows_dropped, rows_loaded


def load_file(
    con: duckdb.DuckDBPyConnection, path: Path, raw_dir: Path, *, force: bool = False
) -> LoadResult:
    """Load one CSV. Never raises for a bad file: failures are returned and recorded."""
    rel = source_file_key(path, raw_dir)
    group = source_group(path, raw_dir)
    size = path.stat().st_size
    digest = sha256_file(path)
    started = time.monotonic()

    if not force and _already_loaded(con, rel, digest):
        log.info("skip (unchanged) file=%s", rel)
        return LoadResult(rel, "skipped")

    try:
        validate_header(path)
        rows_read, dropped, loaded = _replace_file_rows(
            con, path, rel, group, digest, size, started
        )
    except Exception as exc:  # recorded and reported; other files still load
        log.exception("failed file=%s", rel)
        message = f"{type(exc).__name__}: {exc}"
        _record_metadata(
            con, rel=rel, digest=digest, size=size, status="failed",
            rows_read=None, rows_dropped=None, rows_loaded=None, error=message,
            loaded_at=_utc_now(), duration=time.monotonic() - started,
        )
        return LoadResult(rel, "failed", error=message)

    log.info(
        "loaded file=%s read=%s dropped_empty=%s loaded=%s",
        rel, rows_read, dropped, loaded,
    )
    return LoadResult(rel, "loaded", rows_read, dropped, loaded)


def load_anp(
    con: duckdb.DuckDBPyConnection, raw_dir: Path, *, force: bool = False
) -> list[LoadResult]:
    """Load every CSV under raw_dir into raw.anp_precos."""
    files = discover_files(raw_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found under {raw_dir.resolve()}")
    ensure_tables(con)
    results = [load_file(con, path, raw_dir, force=force) for path in files]
    counts = {s: sum(r.status == s for r in results) for s in ("loaded", "skipped", "failed")}
    log.info(
        "ANP done: files=%s loaded=%s skipped=%s failed=%s rows_loaded=%s",
        len(results), counts["loaded"], counts["skipped"], counts["failed"],
        sum(r.rows_loaded for r in results),
    )
    return results
