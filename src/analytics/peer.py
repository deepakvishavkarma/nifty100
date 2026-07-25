"""Peer percentile ranking engine (Sprint 3, Day 18).

Loads peer_groups (from Sprint 1) + the screener universe (latest common
year), computes PERCENT_RANK for 10 metrics within each of the 11 peer
groups, and writes the result into a `peer_percentiles` table in SQLite.

Companies not assigned to any peer group are skipped without raising an
error, per the Day-18 spec.
"""
from __future__ import annotations
import sys
import sqlite3
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.screener.engine import load_universe

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "nifty100.db"

# Metric -> (column in the universe frame, invert=True means lower is better)
PEER_METRICS = {
    "roe": ("return_on_equity_pct", False),
    "roce": ("return_on_capital_employed_pct", False),
    "net_profit_margin": ("net_profit_margin_pct", False),
    "debt_to_equity": ("debt_to_equity", True),          # inverse: lower D/E = higher percentile
    "free_cash_flow": ("free_cash_flow_cr", False),
    "pat_cagr_5yr": ("pat_cagr_5yr", False),
    "revenue_cagr_5yr": ("revenue_cagr_5yr", False),
    "eps_cagr_5yr": ("eps_cagr_5yr", False),
    "interest_coverage": ("interest_coverage", False),
    "asset_turnover": ("asset_turnover", False),
}

PEER_PERCENTILES_SCHEMA = """
DROP TABLE IF EXISTS peer_percentiles;
CREATE TABLE peer_percentiles (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    peer_group_name TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    percentile_rank REAL,
    year TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE INDEX idx_peerpct_group ON peer_percentiles(peer_group_name);
CREATE INDEX idx_peerpct_company ON peer_percentiles(company_id);
"""


def percent_rank(series: pd.Series) -> pd.Series:
    """Excel-style PERCENT_RANK: (rank - 1) / (n - 1), 0..1, ties averaged."""
    vals = series.dropna()
    if len(vals) <= 1:
        return series.apply(lambda v: 1.0 if pd.notna(v) else None)
    ranks = vals.rank(method="average", ascending=True)
    pct = (ranks - 1) / (len(vals) - 1)
    return series.index.to_series().map(pct)


def compute_peer_percentiles(universe: pd.DataFrame, peer_groups: pd.DataFrame) -> pd.DataFrame:
    merged = peer_groups.merge(universe, on="company_id", how="left")
    assigned_ids = set(peer_groups["company_id"])
    unassigned = universe[~universe["company_id"].isin(assigned_ids)]
    for cid in unassigned["company_id"]:
        print(f"  {cid}: No peer group assigned")

    rows = []
    for group_name, gdf in merged.groupby("peer_group_name"):
        gdf = gdf.set_index("company_id")
        for metric_name, (col, invert) in PEER_METRICS.items():
            pct = percent_rank(gdf[col])
            if invert:
                pct = pct.apply(lambda v: 1 - v if pd.notna(v) else None)
            for cid, value in gdf[col].items():
                rows.append({
                    "company_id": cid, "peer_group_name": group_name, "metric": metric_name,
                    "value": None if pd.isna(value) else value,
                    "percentile_rank": pct.get(cid), "year": gdf.loc[cid, "year"],
                })
    return pd.DataFrame(rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(PEER_PERCENTILES_SCHEMA)

    universe = load_universe(conn)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)

    result = compute_peer_percentiles(universe, peer_groups)
    result.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()

    n_groups = result["peer_group_name"].nunique()
    print(f"\npeer_percentiles rows written: {len(result)}")
    print(f"peer groups covered: {n_groups} / 11")
    conn.close()


if __name__ == "__main__":
    main()
