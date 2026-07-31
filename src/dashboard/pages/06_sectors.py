"""Sector Analysis screen (Sprint 4, Day 25)."""
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_screener_universe

st.set_page_config(page_title="Sector Analysis | Nifty 100 Analytics", layout="wide")
st.title("🏭 Sector Analysis")

universe = get_screener_universe()
sectors = sorted(universe["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Sector", ["All"] + sectors)

plot_df = universe if selected_sector == "All" else universe[universe["broad_sector"] == selected_sector]
plot_df = plot_df.dropna(subset=["sales", "return_on_equity_pct", "market_cap_crore"])

if plot_df.empty:
    st.info("Not enough data to plot for this sector.")
else:
    st.subheader(f"{selected_sector} — Revenue vs ROE (bubble = Market Cap)")
    fig = px.scatter(
        plot_df, x="sales", y="return_on_equity_pct", size="market_cap_crore",
        color="sub_sector", hover_name="company_name",
        labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE %", "market_cap_crore": "Market Cap"},
        size_max=50,
    )
    fig.update_layout(height=500, margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Sector Median KPIs")
median_kpis = universe.groupby("broad_sector").agg(
    median_roe=("return_on_equity_pct", "median"),
    median_de=("debt_to_equity", "median"),
    median_pe=("pe_ratio", "median"),
    median_rev_cagr=("revenue_cagr_5yr", "median"),
    companies=("company_id", "count"),
).reset_index().rename(columns={
    "broad_sector": "Sector", "median_roe": "Median ROE %", "median_de": "Median D/E",
    "median_pe": "Median P/E", "median_rev_cagr": "Median Rev CAGR 5yr %", "companies": "Companies",
}).round(2)

fig2 = px.bar(median_kpis, x="Sector", y="Median ROE %", color="Sector")
fig2.update_layout(height=400, margin=dict(t=20, b=10, l=10, r=10), showlegend=False)
st.plotly_chart(fig2, width='stretch')
st.dataframe(median_kpis, width='stretch', hide_index=True)
