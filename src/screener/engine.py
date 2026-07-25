"""Screener filter engine (Sprint 3, Day 15).

Loads the latest-year snapshot of financial_ratios + market_cap + sectors +
companies into a single "universe" DataFrame, and applies YAML-configured
threshold filters against it.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "config" / "screener_config.yaml"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text())


def _latest_common_year(conn) -> str:
    """Pick the year with the broadest company coverage (see Sprint 2 retro
    for why chronological max is unsafe with stray stub periods)."""
    counts = pd.read_sql(
        "SELECT year, COUNT(*) n FROM financial_ratios GROUP BY year", conn
    )
    threshold = counts["n"].max() * 0.5
    return counts[counts["n"] >= threshold]["year"].max()


def load_universe(conn, year: str | None = None) -> pd.DataFrame:
    """Build the flat screener universe: one row per company at `year`
    (defaults to the broadest-coverage latest year)."""
    if year is None:
        year = _latest_common_year(conn)

    fr = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year='{year}'", conn)
    mc = pd.read_sql(f"SELECT * FROM market_cap WHERE year='{year}'", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    pl = pd.read_sql(f"SELECT company_id, sales FROM profitandloss WHERE year='{year}'", conn)

    df = (fr
          .merge(mc.drop(columns=["year"]), on="company_id", how="left")
          .merge(sectors, on="company_id", how="left")
          .merge(companies, on="company_id", how="left")
          .merge(pl, on="company_id", how="left"))

    df["fcf_yield_pct"] = df.apply(
        lambda r: (r["free_cash_flow_cr"] / r["market_cap_crore"] * 100)
        if pd.notna(r["free_cash_flow_cr"]) and pd.notna(r["market_cap_crore"]) and r["market_cap_crore"] != 0
        else None, axis=1)

    # 3-year-back D/E for the Turnaround Watch "declining D/E" filter
    de_3y_ago = _de_n_years_ago(conn, year, n=3)
    df = df.merge(de_3y_ago, on="company_id", how="left")
    df["de_declining_yoy"] = df["debt_to_equity"] < df["debt_to_equity_3y_ago"]
    df["fcf_positive_latest"] = df["free_cash_flow_cr"] > 0

    df["year"] = year
    return df


def _de_n_years_ago(conn, year: str, n: int) -> pd.DataFrame:
    """For each company, find its D/E value from n periods back in its own
    chronological sequence (positional, matching the CAGR engine convention)."""
    all_ratios = pd.read_sql(
        "SELECT company_id, year, debt_to_equity FROM financial_ratios ORDER BY company_id, year", conn
    )
    rows = []
    for cid, cdf in all_ratios.groupby("company_id"):
        cdf = cdf.reset_index(drop=True)
        idx = cdf.index[cdf["year"] == year]
        if len(idx) == 0:
            continue
        i = idx[0]
        if i - n < 0:
            rows.append({"company_id": cid, "debt_to_equity_3y_ago": None})
        else:
            rows.append({"company_id": cid, "debt_to_equity_3y_ago": cdf.loc[i - n, "debt_to_equity"]})
    return pd.DataFrame(rows)


def apply_filter(df: pd.DataFrame, metric: str, condition: dict, config: dict) -> pd.DataFrame:
    """Apply a single {min/max/eq: value} condition, honouring the Financials
    D/E carve-out and the ICR 'Debt Free' = infinity rule."""
    out = df

    if metric == "debt_to_equity" and "max" in condition and config.get("financials_skip_de_filter", True):
        mask = (out["broad_sector"] == "Financials") | (out["debt_to_equity"] <= condition["max"])
        return out[mask]

    if metric == "interest_coverage" and "min" in condition and config.get("icr_debt_free_as_infinity", True):
        mask = (out["icr_label"] == "Debt Free") | (out["interest_coverage"] >= condition["min"])
        return out[mask]

    if "min" in condition:
        out = out[out[metric] >= condition["min"]]
    if "max" in condition:
        out = out[out[metric] <= condition["max"]]
    if "eq" in condition:
        out = out[out[metric] == condition["eq"]]
    return out


def apply_custom_filter(df: pd.DataFrame, filters: dict, config: dict) -> pd.DataFrame:
    out = df.copy()
    for metric, condition in filters.items():
        out = apply_filter(out, metric, condition, config)
    return out
