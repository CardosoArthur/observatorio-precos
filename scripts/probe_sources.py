"""Probe the three public sources and print the real coverage of each.

ANP files are read from data/raw/anp/**/*.csv (manual download); SGS and SIDRA are called live.

Run from the repository root:
    pip install requests pandas
    python scripts/probe_sources.py

Nothing here writes to a warehouse; it only reports what each source serves today.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("probe")

TIMEOUT = 60
HEADERS = {"User-Agent": "observatorio-precos/0.1 (portfolio project)"}

ANP_DIR = Path("data/raw/anp")  # subfolders: semestral/, mensal/, ultimas_4_semanas/
SGS_SERIES = {1: "usd_brl_venda", 11: "selic_diaria", 432: "selic_meta"}
SIDRA_IPCA_URL = "https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63/p/last%206/c315/7169"

# Only these columns are loaded: keeps memory low (~4M rows across 17 files).
ANP_USECOLS = [
    "Estado - Sigla", "CNPJ da Revenda", "Produto", "Data da Coleta",
    "Valor de Venda", "Unidade de Medida", "Bandeira",
]
KEY = ["cnpj", "produto", "data"]


def get(url: str) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


def read_anp_csv(path: Path) -> pd.DataFrame:
    """Read one ANP CSV (UTF-8 with BOM, ';' separated), keeping only the probe columns."""
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str, usecols=ANP_USECOLS)
    df["cnpj"] = df["CNPJ da Revenda"].str.replace(r"\D", "", regex=True)  # digits only
    return df


def probe_anp() -> None:
    """Per file: rows, date range, products; then cross-file overlap on (cnpj, produto, data)."""
    files = sorted(ANP_DIR.rglob("*.csv"))
    if not files:
        raise SystemExit(f"No CSV files found in {ANP_DIR.resolve()}")

    keys: list[pd.DataFrame] = []
    products: dict[str, int] = {}
    units: dict[str, int] = {}
    brands: dict[str, int] = {}
    cnpj_lens: dict[int, int] = {}
    for path in files:
        df = read_anp_csv(path)
        dates = pd.to_datetime(df["Data da Coleta"], format="%d/%m/%Y", errors="coerce")
        price = pd.to_numeric(df["Valor de Venda"].str.replace(",", ".", regex=False), errors="coerce")
        rel = str(path.relative_to(ANP_DIR))
        log.info(
            "ANP %s rows=%s date_min=%s date_max=%s bad_dates=%s bad_prices=%s price_min=%s price_max=%s",
            rel, len(df), dates.min().date(), dates.max().date(),
            int(dates.isna().sum()), int(price.isna().sum()), price.min(), price.max(),
        )
        for col, acc in (("Produto", products), ("Unidade de Medida", units), ("Bandeira", brands)):
            for k, v in df[col].fillna("<NULL>").value_counts().items():
                acc[k] = acc.get(k, 0) + int(v)
        for k, v in df["cnpj"].fillna("").str.len().value_counts().items():
            cnpj_lens[int(k)] = cnpj_lens.get(int(k), 0) + int(v)
        keys.append(
            pd.DataFrame({
                "cnpj": df["cnpj"].astype("category"),
                "produto": df["Produto"].astype("category"),
                "data": df["Data da Coleta"].astype("category"),
                "source_file": rel,
            })
        )
        del df

    log.info("ANP products (all files)=%s", dict(sorted(products.items(), key=lambda x: -x[1])))
    log.info("ANP units (all files)=%s", units)
    log.info("ANP cnpj digit lengths=%s (14 expected)", cnpj_lens)
    log.info("ANP distinct brands=%s; top=%s", len(brands),
             dict(sorted(brands.items(), key=lambda x: -x[1])[:15]))

    allkeys = pd.concat(keys, ignore_index=True)
    for col in ("cnpj", "produto", "data"):
        allkeys[col] = allkeys[col].astype(str)
    log.info("ANP total_rows=%s", len(allkeys))

    # 1) duplicates of the natural key inside the same file
    within = allkeys.duplicated(subset=[*KEY, "source_file"], keep=False)
    log.info("ANP rows with repeated key INSIDE the same file=%s", int(within.sum()))

    # 2) same key present in more than one file
    deduped = allkeys.drop_duplicates(subset=[*KEY, "source_file"])
    cross = deduped.duplicated(subset=KEY, keep=False)
    log.info("ANP rows whose key appears in MORE THAN ONE file=%s", int(cross.sum()))
    if cross.any():
        pairs = (
            deduped[cross].sort_values("source_file")
            .groupby(KEY)["source_file"].agg(" | ".join).value_counts().head(10)
        )
        log.info("ANP overlap by file combination:\n%s", pairs)


def probe_sgs() -> None:
    """Print the last 3 observations of each SGS series."""
    for code, name in SGS_SERIES.items():
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/3?formato=json"
        data: list[dict[str, Any]] = get(url).json()
        log.info("SGS %s (%s) last=%s", code, name, data)


def probe_sidra() -> None:
    """Print the latest IPCA monthly variation periods served by SIDRA."""
    rows = get(SIDRA_IPCA_URL).json()[1:]  # first item is the header row
    for r in rows:
        log.info("SIDRA IPCA %s = %s%%", r["D3N"], r["V"])


if __name__ == "__main__":
    for step in (probe_anp, probe_sgs, probe_sidra):
        try:  # one failing source must not hide the others
            step()
        except Exception:
            log.exception("%s failed", step.__name__)
