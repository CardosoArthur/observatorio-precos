"""Shared logic to load an API payload into a raw table, idempotently.

Unit of load = one "source key" (an SGS series, the SIDRA table query). Each key is
replaced atomically (delete its rows + insert + metadata row, one transaction).
A payload whose SHA-256 is unchanged is skipped. An empty payload is a failure and
never deletes data that is already loaded.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Sequence
from datetime import datetime, timezone

import duckdb

from ingestion.anp import LoadResult
from ingestion.db import RAW_SCHEMA, ensure_metadata_table

log = logging.getLogger(__name__)
METADATA_TABLE = f"{RAW_SCHEMA}._load_metadata"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def payload_digest(rows: Sequence[Sequence[str | None]]) -> tuple[str, int]:
    """SHA-256 and size in bytes of the rows, serialised in a stable way."""
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(blob)


def _already_loaded(
    con: duckdb.DuckDBPyConnection, table: str, source: str, key: str, digest: str
) -> bool:
    """True if the last successful load of this key had the same digest and rows remain."""
    last = con.execute(
        f"SELECT file_sha256 FROM {METADATA_TABLE} "
        "WHERE source = ? AND source_file = ? AND status = 'success' "
        "ORDER BY loaded_at DESC LIMIT 1",
        [source, key],
    ).fetchone()
    if last is None or last[0] != digest:
        return False
    present = con.execute(
        f"SELECT count(*) FROM {table} WHERE _source_key = ?", [key]
    ).fetchone()
    return bool(present and present[0] > 0)


def _record(
    con: duckdb.DuckDBPyConnection, source: str, key: str, digest: str, size: int,
    status: str, rows: int | None, error: str | None, started: float,
) -> None:
    con.execute(
        f"INSERT INTO {METADATA_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [source, key, digest, size, rows, 0 if rows is not None else None, rows,
         status, error, _utc_now(), time.monotonic() - started],
    )


def replace_key_rows(
    con: duckdb.DuckDBPyConnection,
    *,
    source: str,
    table: str,
    columns: Sequence[str],
    key: str,
    rows: Sequence[Sequence[str | None]],
    force: bool = False,
    started: float | None = None,
) -> LoadResult:
    """Replace all rows of `key` in `table` with `rows` (data columns only)."""
    started = time.monotonic() if started is None else started
    ensure_metadata_table(con)
    digest, size = payload_digest(rows)

    if not rows:
        message = "EmptyPayload: API returned no rows; existing data left untouched"
        _record(con, source, key, digest, size, "failed", None, message, started)
        log.error("failed key=%s %s", key, message)
        return LoadResult(key, "failed", error=message)

    if not force and _already_loaded(con, table, source, key, digest):
        log.info("skip (unchanged) key=%s", key)
        return LoadResult(key, "skipped")

    ingested_at = _utc_now()
    placeholders = ", ".join("?" for _ in range(len(columns) + 2))
    cols = ", ".join([*columns, "_source_key", "_ingested_at"])
    try:
        con.execute("BEGIN")
        con.execute(f"DELETE FROM {table} WHERE _source_key = ?", [key])
        con.executemany(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            [[*row, key, ingested_at] for row in rows],
        )
        _record(con, source, key, digest, size, "success", len(rows), None, started)
        con.execute("COMMIT")
    except Exception as exc:
        con.execute("ROLLBACK")
        message = f"{type(exc).__name__}: {exc}"
        _record(con, source, key, digest, size, "failed", None, message, started)
        log.exception("failed key=%s", key)
        return LoadResult(key, "failed", error=message)

    log.info("loaded key=%s rows=%s", key, len(rows))
    return LoadResult(key, "loaded", len(rows), 0, len(rows))
