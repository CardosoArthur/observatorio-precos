"""Load IBGE SIDRA IPCA (table 7060, general index) into raw.ibge_ipca.

The SIDRA response is a JSON list whose first item is a header row (dropped here).
Every value is kept as delivered, including SIDRA markers such as '-' or '...'.
Variables: 63 monthly change, 69 change in the year, 2265 change in 12 months, 66 weight.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import duckdb

from ingestion.anp import LoadResult
from ingestion.api_load import replace_key_rows
from ingestion.db import RAW_SCHEMA
from ingestion.http import get_json

log = logging.getLogger(__name__)

SOURCE = "sidra"
TABLE = f"{RAW_SCHEMA}.ibge_ipca"
KEY = "sidra/7060"
URL = "https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63,69,2265,66/p/all/c315/7169"
COLUMNS = (
    "variavel_codigo", "variavel_nome", "periodo_codigo", "periodo_nome",
    "classificacao_codigo", "classificacao_nome", "unidade_medida", "valor",
)
# SIDRA response key for each raw column (D2=variable, D3=period, D4=classification).
SIDRA_KEYS = ("D2C", "D2N", "D3C", "D3N", "D4C", "D4N", "MN", "V")

Fetch = Callable[[str], Any]


def ensure_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            variavel_codigo VARCHAR, variavel_nome VARCHAR,
            periodo_codigo VARCHAR, periodo_nome VARCHAR,
            classificacao_codigo VARCHAR, classificacao_nome VARCHAR,
            unidade_medida VARCHAR, valor VARCHAR,
            _source_key VARCHAR NOT NULL, _ingested_at TIMESTAMP NOT NULL
        )
        """
    )


def parse_rows(payload: Any) -> list[tuple[str | None, ...]]:
    """Drop the header row and map each record to the raw columns."""
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected SIDRA response: {str(payload)[:200]}")
    return [tuple(rec.get(k) for k in SIDRA_KEYS) for rec in payload[1:]]


def load_sidra(
    con: duckdb.DuckDBPyConnection, *, force: bool = False, fetch: Fetch = get_json
) -> list[LoadResult]:
    ensure_table(con)
    started = time.monotonic()
    try:
        rows = parse_rows(fetch(URL))
    except Exception as exc:
        log.exception("fetch failed key=%s", KEY)
        return [LoadResult(KEY, "failed", error=f"{type(exc).__name__}: {exc}")]
    return [
        replace_key_rows(
            con, source=SOURCE, table=TABLE, columns=COLUMNS, key=KEY,
            rows=rows, force=force, started=started,
        )
    ]
