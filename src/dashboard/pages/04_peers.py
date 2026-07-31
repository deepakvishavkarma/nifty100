"""Peer Comparison screen (Sprint 4, Day 24)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_screener_universe, get_peers

st.set_page_config(page_title="Peer Comparison | Nifty 100 Analytics", layout="wide")
st.title("⚖️ Peer Comparison")

PEER_GROUPS = [
    "Private Banks", "Public Sector Banks", "IT Services", "Pharmaceuticals",
    "Automobiles", "Life Insurance", "Oil & Gas", "Power & Utilities",
    "Steel", "FMCG", "Consumer Finance",
]
RADAR_METRICS = [
    ("return_on_equity_pct", "ROE"), ("return_on_capital_employed_pct", "ROCE"),
    ("net_profit_margin_pct", "NPM"), ("debt_to_equity", "D/E"),
    ("free_cash_flow_cr", "FCF"), ("pat_cagr_5yr", "PAT CAGR 5yr"),
    ("revenue_cagr_5yr", "Rev CAGR 5yr"), ("composite_quality_score", "Composite"),
]

group_name = st.selectbox("Peer Group", PEER_GROUPS)

members = get_peers(group_name)
universe = get_screener_universe()
group_universe = universe[universe["company_id"].isin(members["company_id"])].merge(
    members[["company_id", "is_benchmark"]], on="company_id", how="left")

if group_universe.empty:
    st.warning("No data available for this peer group in the latest year.")
    st.stop()

benchmark_row = group_universe[group_universe["is_benchmark"] == 1]
benchmark_id = benchmark_row["company_id"].iloc[0] if len(benchmark_row) else group_universe["company_id"].iloc[0]

company_list = group_universe["company_id"].tolist()
selected_company = st.selectbox(
    "Company (for radar chart)", company_list,
    index=company_list.index(benchmark_id) if benchmark_id in company_list else 0,
)


def _minmax_scale(series):
    vals = series.dropna()
    if len(vals) < 2:
        return series.apply(lambda v: 50.0 if pd.notna(v) else 0.0)
    lo, hi = vals.min(), vals.max()
    if hi == lo:
        return series.apply(lambda v: 50.0 if pd.notna(v) else 0.0)
    return series.apply(lambda v: (v - lo) / (hi - lo) * 100 if pd.notna(v) else 0.0)


scaled = group_universe.copy()
for col, _ in RADAR_METRICS:
    invert = col == "debt_to_equity"
    s = _minmax_scale(scaled[col])
    scaled[col + "_score"] = (100 - s) if invert else s

company_scores = scaled[scaled["company_id"] == selected_company][[c + "_score" for c, _ in RADAR_METRICS]].iloc[0].tolist()
peer_avg_scores = scaled[[c + "_score" for c, _ in RADAR_METRICS]].mean().tolist()
labels = [lbl for _, lbl in RADAR_METRICS]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=company_scores + company_scores[:1], theta=labels + labels[:1],
                               fill="toself", name=selected_company))
fig.add_trace(go.Scatterpolar(r=peer_avg_scores + peer_avg_scores[:1], theta=labels + labels[:1],
                               name=f"{group_name} avg", line=dict(dash="dash")))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                   height=450, margin=dict(t=30, b=10, l=40, r=40))
st.plotly_chart(fig, width='stretch')

st.divider()

st.subheader(f"{group_name} — side-by-side comparison")
table_cols = ["company_id", "company_name", "return_on_equity_pct", "return_on_capital_employed_pct",
              "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr",
              "pat_cagr_5yr", "revenue_cagr_5yr"]
table_cols = [c for c in table_cols if c in group_universe.columns]
display_df = group_universe[table_cols + ["is_benchmark"]].rename(columns={
    "company_id": "Ticker", "company_name": "Company", "return_on_equity_pct": "ROE %",
    "return_on_capital_employed_pct": "ROCE %", "net_profit_margin_pct": "NPM %",
    "debt_to_equity": "D/E", "free_cash_flow_cr": "FCF (Cr)",
    "pat_cagr_5yr": "PAT CAGR 5yr %", "revenue_cagr_5yr": "Rev CAGR 5yr %",
}).round(2)

styled = display_df.drop(columns=["is_benchmark"]).style.apply(
    lambda _: ["background-color: #FFD966" if v == 1 else "" for v in display_df["is_benchmark"]], axis=0
)
st.dataframe(styled, width='stretch', hide_index=True)
st.caption(f"🟡 Benchmark company: **{benchmark_id}**")
