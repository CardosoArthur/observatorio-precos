"""Tests for the Parquet export of the marts."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from ingestion.export import EXPORT_TABLES, export_marts


@pytest.fixture()
def con(tmp_path: Path):
    connection = duckdb.connect(str(tmp_path / "t.duckdb"))
    connection.execute("CREATE SCHEMA marts")
    for table in EXPORT_TABLES:
        connection.execute(f"CREATE TABLE marts.{table} AS SELECT 1 AS id, 'x' AS name")
    yield connection
    connection.close()


def test_export_writes_one_parquet_per_table(con, tmp_path):
    out = tmp_path / "out"
    rows = export_marts(con, out)
    assert rows == {table: 1 for table in EXPORT_TABLES}
    for table in EXPORT_TABLES:
        path = (out / f"{table}.parquet").as_posix()
        assert duckdb.sql(f"SELECT count(*) FROM read_parquet('{path}')").fetchone()[0] == 1


def test_export_refuses_empty_table(con, tmp_path):
    con.execute(f"DELETE FROM marts.{EXPORT_TABLES[0]}")
    with pytest.raises(ValueError, match="empty"):
        export_marts(con, tmp_path / "out")
