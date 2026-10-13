"""Build docs/data/dashboard.json from the mart Parquet export.

Every number shown in the dashboard is computed here from the mart,
never typed by hand. Run after `python -m ingestion export`.

Usage:
    python scripts/build_dashboard_data.py
    python scripts/build_dashboard_data.py --exports exports --out docs/data/dashboard.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

MIN_OBS = 30  # cells with fewer observations are too noisy to compare
BASE_MONTH = "2022-01-01"  # same start as the API loads (ADR-006)
PRODUCTS_REQUIRED = {"GASOLINA", "ETANOL", "DIESEL S10"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exports", default="exports")
    parser.add_argument("--out", default="docs/data/dashboard.json")
    args = parser.parse_args()

    mart = Path(args.exports) / "mart_preco_inflacao_mensal.parquet"
    if not mart.exists():
        raise SystemExit(f"Missing {mart}. Run: python -m ingestion export")

    con = duckdb.connect()
    con.execute(
        f"""
        CREATE VIEW base AS
        SELECT CAST(mes_referencia AS DATE) AS m, produto, uf,
               preco_medio AS p, n_observacoes AS n,
               ipca_mensal_pct AS ipca, usd_brl_venda_medio AS usd
        FROM read_parquet('{mart.as_posix()}')
        """
    )

    found = {r[0] for r in con.execute("SELECT DISTINCT produto FROM base").fetchall()}
    missing = PRODUCTS_REQUIRED - found
    if missing:
        raise SystemExit(f"Products not found in mart: {missing}. Found: {sorted(found)}")

    # Latest month with a published IPCA = last "full" month (current month is partial)
    latest = con.execute("SELECT max(m) FROM base WHERE ipca IS NOT NULL").fetchone()[0]

    # National price = weighted by number of observations
    con.execute(
        """
        CREATE VIEW national AS
        SELECT m, produto, sum(p * n) / sum(n) AS price
        FROM base GROUP BY 1, 2
        """
    )

    # --- IPCA index (Jan/22 = 1) used to deflate prices -----------------------
    ipca = dict(
        con.execute(
            "SELECT m, max(ipca) FROM base WHERE ipca IS NOT NULL GROUP BY 1 ORDER BY 1"
        ).fetchall()
    )
    months = sorted(m for m in ipca if str(m) >= BASE_MONTH and m <= latest)
    index: dict = {}
    for i, m in enumerate(months):
        index[m] = 1.0 if i == 0 else index[months[i - 1]] * (1 + ipca[m] / 100)

    # --- Insight 1: gasoline nominal vs real ----------------------------------
    gas = dict(
        con.execute("SELECT m, price FROM national WHERE produto='GASOLINA'").fetchall()
    )
    gasoline = [
        {"m": str(m), "nominal": gas[m], "real": gas[m] / index[m]}
        for m in months
        if m in gas
    ]

    # --- Price change by fuel, first month vs latest --------------------------
    first = months[0]
    fuels = []
    for produto, p0, p1 in con.execute(
        """
        SELECT a.produto, a.price, b.price
        FROM national a JOIN national b USING (produto)
        WHERE a.m = ? AND b.m = ? ORDER BY a.produto
        """,
        [first, latest],
    ).fetchall():
        fuels.append({"produto": produto, "first": p0, "last": p1, "pct": (p1 / p0 - 1) * 100})

    # --- Insight 2: ethanol / gasoline ratio by UF (latest month) -------------
    ratio = con.execute(
        f"""
        SELECT e.uf, e.p / g.p * 100 AS ratio
        FROM base e JOIN base g ON e.uf = g.uf AND e.m = g.m
        WHERE e.m = ? AND e.produto='ETANOL' AND g.produto='GASOLINA'
          AND e.n >= {MIN_OBS} AND g.n >= {MIN_OBS}
        ORDER BY ratio
        """,
        [latest],
    ).fetchall()

    # --- Insight 3: gasoline price by UF (latest month) -----------------------
    spread = con.execute(
        f"""
        SELECT uf, p FROM base
        WHERE m = ? AND produto='GASOLINA' AND n >= {MIN_OBS} ORDER BY p
        """,
        [latest],
    ).fetchall()

    # --- Insight 4: diesel S10 vs USD/BRL -------------------------------------
    diesel_usd = con.execute(
        """
        SELECT d.m, d.price AS diesel, u.usd
        FROM national d
        JOIN (SELECT m, max(usd) AS usd FROM base WHERE usd IS NOT NULL GROUP BY 1) u USING (m)
        WHERE d.produto='DIESEL S10' AND d.m <= ? ORDER BY d.m
        """,
        [latest],
    ).df()
    corr_levels = float(diesel_usd["diesel"].corr(diesel_usd["usd"]))
    corr_changes = float(
        diesel_usd["diesel"].pct_change().corr(diesel_usd["usd"].pct_change())
    )

    payload = {
        "latest_month": str(latest),
        "first_month": str(first),
        "min_obs": MIN_OBS,
        "ipca_acum_pct": (index[latest] - 1) * 100,
        "gasoline": gasoline,
        "fuels": fuels,
        "ratio": [{"uf": u, "ratio": r} for u, r in ratio],
        "spread": [{"uf": u, "price": p} for u, p in spread],
        "diesel_usd": [
            {"m": str(r.m), "diesel": r.diesel, "usd": r.usd} for r in diesel_usd.itertuples()
        ],
        "corr_levels": corr_levels,
        "corr_changes": corr_changes,
        "n_months_corr": int(len(diesel_usd)),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out} (latest month: {latest}, {len(gasoline)} months)")


if __name__ == "__main__":
    main()