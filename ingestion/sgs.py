"""Load BCB SGS series (USD/BRL, Selic daily, Selic target) into raw.bcb_sgs.

Raw keeps `data` (dd/MM/yyyy) and `valor` exactly as the API returns them (VARCHAR).
SGS limits date-range queries on daily series, so the history is fetched in
windows of ~5 years. Series 432 may return dates in the future; raw keeps whatever
the API served (the request ends today) and dbt staging filters `data <= current_date`.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import duckdb

from ingestion.anp import LoadResult
from ingestion.api_load import replace_key_rows
from ingestion.db import RAW_SCHEMA
from ingestion.http import get_json

log = logging.getLogger(__name__)

SOURCE = "sgs"
TABLE = f"{RAW_SCHEMA}.bcb_sgs"
COLUMNS = ("serie_codigo", "serie_nome", "data", "valor")
SERIES: dict[int, str] = {1: "usd_brl_venda", 11: "selic_diaria", 432: "selic_meta"}
WINDOW_DAYS = 1800  # ~4.9 years, safely under the API range limit
URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    "?formato=json&dataInicial={start}&dataFinal={end}"
)

Fetch = Callable[[str], Any]


def ensure_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            serie_codigo VARCHAR, serie_nome VARCHAR, data VARCHAR, valor VARCHAR,
            _source_key VARCHAR NOT NULL, _ingested_at TIMESTAMP NOT NULL
        )
        """
    )


def date_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Consecutive, non-overlapping windows covering [start, end]."""
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=WINDOW_DAYS - 1), end)
        windows.append((cursor, stop))
        cursor = stop + timedelta(days=1)
    return windows


def fetch_series(code: int, start: date, end: date, fetch: Fetch) -> list[dict[str, Any]]:
    """Fetch one series over [start, end], window by window."""
    out: list[dict[str, Any]] = []
    for win_start, win_end in date_windows(start, end):
        url = URL.format(
            code=code, start=win_start.strftime("%d/%m/%Y"), end=win_end.strftime("%d/%m/%Y")
        )
        data = fetch(url)
        if not isinstance(data, list):  # SGS returns an object on errors
            raise ValueError(f"Unexpected SGS response for series {code}: {str(data)[:200]}")
        out.extend(data)
    return out


def load_sgs(
    con: duckdb.DuckDBPyConnection,
    *,
    start: date,
    end: date | None = None,
    force: bool = False,
    fetch: Fetch = get_json,
) -> list[LoadResult]:
    """Load every configured series. A failing series does not block the others."""
    ensure_table(con)
    end = end or date.today()
    results: list[LoadResult] = []
    for code, name in SERIES.items():
        key = f"sgs/{code}"
        started = time.monotonic()
        try:
            payload = fetch_series(code, start, end, fetch)
        except Exception as exc:  # network/HTTP/shape problem: record and move on
            log.exception("fetch failed key=%s", key)
            results.append(LoadResult(key, "failed", error=f"{type(exc).__name__}: {exc}"))
            continue
        rows = [(str(code), name, r.get("data"), r.get("valor")) for r in payload]
        results.append(
            replace_key_rows(
                con, source=SOURCE, table=TABLE, columns=COLUMNS, key=key,
                rows=rows, force=force, started=started,
            )
        )
    return results
