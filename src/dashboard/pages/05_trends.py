"""Trend Analysis screen (Sprint 4, Day 25)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis | Nifty 100 Analytics", layout="wide")
st.title("📈 Trend Analysis")

companies = get_companies()
search_options = (companies["company_id"] + " — " + companies["company_name"]).tolist()
query = st.text_input("Search by company name or ticker", "")
matches = [s for s in search_options if query.upper() in s.upper()] if query else search_options

if not matches:
    st.warning("Ticker not found — please try another")
    st.stop()

selection = st.selectbox("Select company", matches, index=0)
ticker = selection.split(" — ")[0]

METRIC_OPTIONS = {
    "ROE %": "return_on_equity_pct", "ROCE %": "return_on_capital_employed_pct",
    "Net Profit Margin %": "net_profit_margin_pct", "D/E": "debt_to_equity",
    "Revenue CAGR 5yr %": "revenue_cagr_5yr", "PAT CAGR 5yr %": "pat_cagr_5yr",
    "FCF (Cr)": "free_cash_flow_cr", "Composite Quality Score": "composite_quality_score",
}
selected_metrics = st.multiselect(
    "Metrics to overlay (up to 3)", list(METRIC_OPTIONS.keys()),
    default=["ROE %"], max_selections=3,
)

ratios = get_ratios(ticker).tail(10)
if ratios.empty:
    st.info("No ratio history available for this company.")
    st.stop()

if not selected_metrics:
    st.info("Select at least one metric to plot.")
    st.stop()

fig = go.Figure()
for label in selected_metrics:
    col = METRIC_OPTIONS[label]
    if col not in ratios.columns:
        continue
    series = ratios[col]
    yoy = series.pct_change() * 100
    text = [f"{v:+.1f}%" if pd.notna(v) else "" for v in yoy]
    fig.add_trace(go.Scatter(
        x=ratios["year"], y=series, mode="lines+markers+text", name=label,
        text=text, textposition="top center",
    ))

fig.update_layout(height=480, margin=dict(t=30, b=10, l=10, r=10),
                   title=f"{ticker} — {', '.join(selected_metrics)} (10yr, YoY % annotated)")
st.plotly_chart(fig, width='stretch')

if len(ratios) < 10:
    st.caption(f"Note: only {len(ratios)} years of history available for this company.")
