"""Command line entry point: `python -m ingestion {anp,sgs,sidra,all}`."""
from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

import duckdb
from dotenv import load_dotenv

from ingestion.anp import LoadResult, load_anp
from ingestion.config import Settings, load_settings
from ingestion.db import connect
from ingestion.sgs import load_sgs
from ingestion.sidra import load_sidra


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("anp", "Load ANP fuel-price CSVs into raw.anp_precos"),
        ("sgs", "Load BCB SGS series into raw.bcb_sgs"),
        ("sidra", "Load IBGE SIDRA IPCA into raw.ibge_ipca"),
        ("all", "Run anp, sgs and sidra in sequence (DuckDB is single-writer)"),
    ):
        cmd = sub.add_parser(name, help=helptext)
        cmd.add_argument("--db", type=Path, help="DuckDB file to write")
        cmd.add_argument("--force", action="store_true", help="Reload unchanged data too")
        if name in ("anp", "all"):
            cmd.add_argument("--raw-dir", type=Path, help="Folder with the ANP CSVs")
        if name in ("sgs", "all"):
            cmd.add_argument("--start", type=date.fromisoformat, help="SGS start, YYYY-MM-DD")
    return parser


def run(
    con: duckdb.DuckDBPyConnection, args: argparse.Namespace, settings: Settings
) -> list[LoadResult]:
    results: list[LoadResult] = []
    if args.command in ("anp", "all"):
        results += load_anp(con, args.raw_dir or settings.anp_raw_dir, force=args.force)
    if args.command in ("sgs", "all"):
        start = args.start or date.fromisoformat(settings.api_start_date)
        results += load_sgs(con, start=start, force=args.force)
    if args.command in ("sidra", "all"):
        results += load_sidra(con, force=args.force)
    return results


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    con = connect(args.db or settings.duckdb_path)
    try:
        results = run(con, args, settings)
    finally:
        con.close()
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
