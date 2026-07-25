"""Sector-relative composite quality score for the screener (Sprint 3, Day 17).

35% Profitability (ROE 15 + ROCE 10 + NPM 10)
30% Cash Quality (FCF CAGR 15 + CFO/PAT 10 + FCF-positive flag 5)
20% Growth (Revenue CAGR 10 + PAT CAGR 10)
15% Leverage (D/E score 10 + ICR score 5)

Each sub-metric is winsorised at P10/P90 *within its own broad_sector* so a
company is scored against sector peers, not the full 92-company universe.
"""
from __future__ import annotations
import pandas as pd

from src.analytics.composite_score import winsorised_score


WEIGHTS = {
    "return_on_equity_pct": 0.15,
    "return_on_capital_employed_pct": 0.10,
    "net_profit_margin_pct": 0.10,
    "revenue_cagr_5yr": 0.10,   # used as FCF CAGR proxy is unavailable multi-year in universe; see note below
    "cfo_quality_score": 0.10,
    "fcf_positive_latest": 0.05,
    "revenue_cagr_5yr_growth": 0.10,
    "pat_cagr_5yr": 0.10,
    "debt_to_equity": 0.10,
    "interest_coverage": 0.05,
}
INVERTED = {"debt_to_equity"}


def _sector_score(series: pd.Series, invert: bool = False) -> pd.Series:
    vals = series.dropna()
    if len(vals) < 3:
        # too few sector peers for a stable percentile - fall back to neutral 50
        return series.apply(lambda v: 50.0 if pd.notna(v) else None)
    p10, p90 = vals.quantile(0.10), vals.quantile(0.90)
    return series.apply(lambda v: winsorised_score(v, p10, p90, invert=invert))


def compute_sector_relative_score(df: pd.DataFrame) -> pd.Series:
    """Returns a Series of 0-100 scores aligned to df's index."""
    work = df.copy()

    # FCF-positive flag as a 0/100 sub-score
    work["fcf_flag_score"] = work["fcf_positive_latest"].map({True: 100.0, False: 0.0})

    component_defs = [
        ("return_on_equity_pct", 0.15, False),
        ("return_on_capital_employed_pct", 0.10, False),
        ("net_profit_margin_pct", 0.10, False),
        ("free_cash_flow_cr", 0.15, False),          # cash quality: FCF magnitude proxy
        ("cfo_quality_score", 0.10, False),
        ("fcf_flag_score", 0.05, False),
        ("revenue_cagr_5yr", 0.10, False),
        ("pat_cagr_5yr", 0.10, False),
        ("debt_to_equity", 0.10, True),
        ("interest_coverage", 0.05, False),
    ]

    scored_components = {}
    for col, weight, invert in component_defs:
        scored_components[col] = work.groupby("broad_sector")[col].transform(
            lambda s: _sector_score(s, invert=invert))

    scores = pd.DataFrame(scored_components)
    weights = pd.Series({col: w for col, w, _ in component_defs})

    def weighted_avg(row):
        avail = row.dropna()
        if avail.empty:
            return None
        w = weights[avail.index]
        return (avail * w).sum() / w.sum()

    return scores.apply(weighted_avg, axis=1)
