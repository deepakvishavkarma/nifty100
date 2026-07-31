"""Shared, cached data-loading layer for the Streamlit dashboard (Sprint 4, Day 22).

Every DB-touching function is wrapped in @st.cache_data(ttl=600) so repeated
navigation between pages doesn't re-hit SQLite on every rerun.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = ROOT / "data" / "nifty100.db"


def _connect():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT c.id AS company_id, c.company_name, c.about_company, c.face_value, "
        "c.book_value, s.broad_sector, s.sub_sector "
        "FROM companies c LEFT JOIN sectors s ON c.id = s.company_id", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_latest_common_year(table: str = "financial_ratios") -> str:
    conn = _connect()
    counts = pd.read_sql(f"SELECT year, COUNT(*) n FROM {table} GROUP BY year", conn)
    conn.close()
    threshold = counts["n"].max() * 0.5
    return counts[counts["n"] >= threshold]["year"].max()


@st.cache_data(ttl=600)
def get_ratios(ticker: str | None = None, year: str | None = None) -> pd.DataFrame:
    conn = _connect()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df.sort_values("year")


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql(
        "SELECT pg.peer_group_name, pg.company_id, pg.is_benchmark, c.company_name "
        "FROM peer_groups pg LEFT JOIN companies c ON pg.company_id = c.id "
        "WHERE pg.peer_group_name = ?", conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_group_for_company(ticker: str) -> str | None:
    conn = _connect()
    row = pd.read_sql("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", conn, params=[ticker])
    conn.close()
    return row["peer_group_name"].iloc[0] if len(row) else None


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql("SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_capital_allocation(year: str | None = None) -> pd.DataFrame:
    conn = _connect()
    path = ROOT / "output" / "capital_allocation.csv"
    conn.close()
    df = pd.read_csv(path)
    if year:
        df = df[df["year"] == year]
    return df


@st.cache_data(ttl=600)
def get_screener_universe(year: str | None = None) -> pd.DataFrame:
    """Full flat table used by the screener + sector screens."""
    conn = _connect()
    if year is None:
        year = get_latest_common_year()
    fr = pd.read_sql("SELECT * FROM financial_ratios WHERE year = ?", conn, params=[year])
    mc = pd.read_sql("SELECT * FROM market_cap WHERE year = ?", conn, params=[year])
    sectors = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    pl = pd.read_sql("SELECT company_id, sales, net_profit FROM profitandloss WHERE year = ?", conn, params=[year])
    conn.close()

    df = (fr
          .merge(mc.drop(columns=["year"]), on="company_id", how="left")
          .merge(sectors, on="company_id", how="left")
          .merge(companies, on="company_id", how="left")
          .merge(pl, on="company_id", how="left"))
    df["fcf_yield_pct"] = df.apply(
        lambda r: (r["free_cash_flow_cr"] / r["market_cap_crore"] * 100)
        if pd.notna(r["free_cash_flow_cr"]) and pd.notna(r["market_cap_crore"]) and r["market_cap_crore"]
        else None, axis=1)
    df["fcf_positive_latest"] = df["free_cash_flow_cr"] > 0

    try:
        import sys as _sys
        _sys.path.insert(0, str(ROOT))
        from src.screener.composite import compute_sector_relative_score
        df["composite_quality_score"] = compute_sector_relative_score(df)
    except Exception:
        df["composite_quality_score"] = None

    return df
