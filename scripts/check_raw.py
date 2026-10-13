"""Sanity-check the raw layer: row counts and real date ranges per source.

Run from the repository root:
    python scripts/check_raw.py
Read-only: nothing is written to the warehouse.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

DB = Path(os.getenv("DUCKDB_PATH", "warehouse/observatorio.duckdb"))

QUERIES = {
    "SGS per series (dates parsed from dd/MM/yyyy)": """
        SELECT serie_codigo, serie_nome, count(*) AS n,
               min(strptime(data, '%d/%m/%Y'))::DATE AS data_min,
               max(strptime(data, '%d/%m/%Y'))::DATE AS data_max,
               count(*) FILTER (WHERE strptime(data, '%d/%m/%Y') > current_date) AS future_rows
        FROM raw.bcb_sgs GROUP BY 1, 2 ORDER BY 1
    """,
    "SIDRA IPCA per variable": """
        SELECT variavel_codigo, variavel_nome, unidade_medida, count(*) AS n,
               min(periodo_codigo) AS periodo_min, max(periodo_codigo) AS periodo_max
        FROM raw.ibge_ipca GROUP BY 1, 2, 3 ORDER BY 1
    """,
    "ANP per source group": """
        SELECT _source_group, count(*) AS n, count(DISTINCT _source_file) AS files
        FROM raw.anp_precos GROUP BY 1 ORDER BY 1
    """,
    "Load metadata (last status per source key)": """
        SELECT source, source_file, status, rows_loaded, loaded_at
        FROM raw._load_metadata
        QUALIFY row_number() OVER (PARTITION BY source, source_file ORDER BY loaded_at DESC) = 1
        ORDER BY source, source_file
    """,
}

if __name__ == "__main__":
    con = duckdb.connect(str(DB), read_only=True)
    for title, sql in QUERIES.items():
        print(f"\n== {title}")
        for row in con.execute(sql).fetchall():
            print(row)
    con.close()
