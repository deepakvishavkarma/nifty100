"""Capital Allocation Map screen (Sprint 4, Day 25)."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_capital_allocation, get_companies, get_latest_common_year

st.set_page_config(page_title="Capital Allocation Map | Nifty 100 Analytics", layout="wide")
st.title("🗺️ Capital Allocation Map")

available_years = ["2019-03", "2020-03", "2021-03", "2022-03", "2023-03", "2024-03"]
default_year = get_latest_common_year()
year = st.selectbox(
    "Year", available_years,
    index=available_years.index(default_year) if default_year in available_years else len(available_years) - 1,
)

alloc = get_capital_allocation(year)
companies = get_companies()
alloc = alloc.merge(companies[["company_id", "company_name", "broad_sector"]], on="company_id", how="left")

if alloc.empty:
    st.info("No capital allocation data available for this year.")
    st.stop()

st.subheader(f"Capital Allocation Patterns — FY {year}")
fig = px.treemap(
    alloc, path=["pattern_label", "company_id"], color="pattern_label",
)
fig.update_layout(height=550, margin=dict(t=20, b=10, l=10, r=10))
st.plotly_chart(fig, width='stretch')

st.divider()
pattern_choice = st.selectbox("View companies in pattern", sorted(alloc["pattern_label"].unique()))
subset = alloc[alloc["pattern_label"] == pattern_choice][["company_id", "company_name", "broad_sector"]]
st.dataframe(
    subset.rename(columns={"company_id": "Ticker", "company_name": "Company", "broad_sector": "Sector"}),
    width='stretch', hide_index=True,
)
st.caption(f"{len(subset)} companies classified as **{pattern_choice}** in FY {year}.")
