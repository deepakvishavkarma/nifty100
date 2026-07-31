"""Home / Overview screen (Sprint 4, Day 23)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_screener_universe, get_latest_common_year

st.set_page_config(page_title="Home | Nifty 100 Analytics", layout="wide")
st.title("🏠 Home / Overview")

available_years = ["2019-03", "2020-03", "2021-03", "2022-03", "2023-03", "2024-03"]
default_year = get_latest_common_year()
year = st.sidebar.selectbox(
    "Year", available_years,
    index=available_years.index(default_year) if default_year in available_years else len(available_years) - 1,
)

companies = get_companies()
universe = get_screener_universe(year)

# --- 6 summary KPI tiles ---
col1, col2, col3, col4, col5, col6 = st.columns(6)
avg_roe = universe["return_on_equity_pct"].mean()
median_pe = universe["pe_ratio"].median()
median_de = universe["debt_to_equity"].median()
total_companies = len(companies)
median_rev_cagr = universe["revenue_cagr_5yr"].median()
debt_free_count = (universe["debt_to_equity"] == 0).sum()

col1.metric("Average ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
col2.metric("Median P/E", f"{median_pe:.1f}x" if pd.notna(median_pe) else "N/A")
col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
col4.metric("Total Companies", total_companies)
col5.metric("Median Rev CAGR 5yr", f"{median_rev_cagr:.1f}%" if pd.notna(median_rev_cagr) else "N/A")
col6.metric("Debt-Free Companies", int(debt_free_count))

st.divider()

# --- Sector donut chart ---
left, right = st.columns([1, 1])
with left:
    st.subheader("Sector Breakdown")
    sector_counts = companies["broad_sector"].value_counts().reset_index()
    sector_counts.columns = ["Sector", "Companies"]
    fig = px.pie(sector_counts, names="Sector", values="Companies", hole=0.5)
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=420)
    st.plotly_chart(fig, width='stretch')

# --- Top 5 by composite quality score ---
with right:
    st.subheader("Top 5 by Composite Quality Score")
    if "composite_quality_score" in universe.columns and universe["composite_quality_score"].notna().any():
        top5 = universe.sort_values("composite_quality_score", ascending=False).head(5)
        st.dataframe(
            top5[["company_id", "company_name", "broad_sector", "composite_quality_score"]]
            .rename(columns={"company_id": "Ticker", "company_name": "Company",
                              "broad_sector": "Sector", "composite_quality_score": "Quality Score"})
            .round(1),
            width='stretch', hide_index=True,
        )
    else:
        st.info("Composite quality score not available for this year — run the Sprint 3 screener pipeline first.")

st.caption(f"Data as of FY {year}. Universe: {len(universe)} companies with ratio data for this year.")
