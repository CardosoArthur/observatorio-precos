"""Command line entry point: `python -m ingestion anp`."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from ingestion.anp import load_anp
from ingestion.config import load_settings
from ingestion.db import connect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    anp = sub.add_parser("anp", help="Load ANP fuel-price CSVs into raw.anp_precos")
    anp.add_argument("--raw-dir", type=Path, help="Folder with the ANP CSVs")
    anp.add_argument("--db", type=Path, help="DuckDB file to write")
    anp.add_argument("--force", action="store_true", help="Reload unchanged files too")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    con = connect(args.db or settings.duckdb_path)
    try:
        results = load_anp(con, args.raw_dir or settings.anp_raw_dir, force=args.force)
    finally:
        con.close()
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
