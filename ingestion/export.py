"""Export the dbt marts to Parquet files for dashboards (Evidence, Power BI, etc.).

Only the monthly mart and the two small dimensions are exported; the 4.2M-row fact stays
in the warehouse. Parquet keeps types and is far smaller than CSV.
"""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)

EXPORT_TABLES = (
    "mart_preco_inflacao_mensal",
    "dim_produto",
    "dim_localidade",
)


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def export_marts(con: duckdb.DuckDBPyConnection, out_dir: Path) -> dict[str, int]:
    """Write marts.<table> to <out_dir>/<table>.parquet. Returns rows per table.

    Raises if a table is missing or empty: an empty export would silently blank a dashboard.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: dict[str, int] = {}
    for table in EXPORT_TABLES:
        count = con.execute(f"SELECT count(*) FROM marts.{table}").fetchone()[0]
        if count == 0:
            raise ValueError(f"marts.{table} is empty; refusing to export")
        target = out_dir / f"{table}.parquet"
        con.execute(
            f"COPY marts.{table} TO {_sql_literal(target.as_posix())} "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        rows[table] = count
        log.info("exported table=%s rows=%s file=%s", table, count, target)
    return rows
