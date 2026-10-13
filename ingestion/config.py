"""Runtime configuration read from environment variables, with safe defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    duckdb_path: Path
    anp_raw_dir: Path
    api_start_date: str
    log_level: str


def load_settings() -> Settings:
    """Build settings from the environment (a .env file is loaded by the CLI)."""
    return Settings(
        duckdb_path=Path(os.getenv("DUCKDB_PATH", "warehouse/observatorio.duckdb")),
        anp_raw_dir=Path(os.getenv("ANP_RAW_DIR", "data/raw/anp")),
        api_start_date=os.getenv("API_START_DATE", "2022-01-01"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
