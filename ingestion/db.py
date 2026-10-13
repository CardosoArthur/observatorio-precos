"""DuckDB connection helpers and the shared load-metadata table."""
from __future__ import annotations

from pathlib import Path

import duckdb

RAW_SCHEMA = "raw"

LOAD_METADATA_DDL = f"""
CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}._load_metadata (
    source              VARCHAR   NOT NULL,
    source_file         VARCHAR   NOT NULL,
    file_sha256         VARCHAR   NOT NULL,
    file_size_bytes     BIGINT    NOT NULL,
    rows_read           BIGINT,
    rows_dropped_empty  BIGINT,
    rows_loaded         BIGINT,
    status              VARCHAR   NOT NULL,
    error               VARCHAR,
    loaded_at           TIMESTAMP NOT NULL,
    duration_seconds    DOUBLE
)
"""


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    """Open (and create if needed) the DuckDB file and the raw schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
    return con


def ensure_metadata_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(LOAD_METADATA_DDL)
