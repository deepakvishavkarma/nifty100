"""Company Profile screen (Sprint 4, Day 23)."""
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf, get_pros_cons

st.set_page_config(page_title="Company Profile | Nifty 100 Analytics", layout="wide")
st.title("🏢 Company Profile")

_t0 = time.time()
companies = get_companies()
search_options = (companies["company_id"] + " — " + companies["company_name"]).tolist()

query = st.text_input("Search by company name or ticker", "")
matches = [s for s in search_options if query.upper() in s.upper()] if query else search_options

if not matches:
    st.warning("Ticker not found — please try another")
    st.stop()

selection = st.selectbox("Select company", matches, index=0)
ticker = selection.split(" — ")[0]

row = companies[companies["company_id"] == ticker]
if row.empty:
    st.warning("Ticker not found — please try another")
    st.stop()
row = row.iloc[0]

# --- Company card ---
st.subheader(f"{row['company_name']} ({ticker})")
c1, c2, c3 = st.columns(3)
c1.write(f"**Sector:** {row['broad_sector'] or 'N/A'}")
c2.write(f"**Sub-sector:** {row['sub_sector'] or 'N/A'}")
c3.write(f"**NSE Ticker:** {ticker}")
if row.get("about_company"):
    st.caption(row["about_company"])

st.divider()

ratios = get_ratios(ticker)
if ratios.empty:
    st.info("No ratio history available for this company yet.")
    st.stop()

latest = ratios.iloc[-1]

# --- 6 KPI tiles ---
k1, k2, k3, k4, k5, k6 = st.columns(6)


def _fmt(v, suffix=""):
    return f"{v:.1f}{suffix}" if pd.notna(v) else "N/A"


k1.metric("ROE", _fmt(latest.get("return_on_equity_pct"), "%"))
k2.metric("ROCE", _fmt(latest.get("return_on_capital_employed_pct"), "%"))
k3.metric("Net Profit Margin", _fmt(latest.get("net_profit_margin_pct"), "%"))
k4.metric("D/E", _fmt(latest.get("debt_to_equity")))
k5.metric("Revenue CAGR 5yr", _fmt(latest.get("revenue_cagr_5yr"), "%"))
k6.metric("FCF (Cr)", _fmt(latest.get("free_cash_flow_cr")))

st.caption(f"Latest available year: {latest['year']}")
st.divider()

# --- 10yr Revenue & Net Profit bar chart ---
pl = get_pl(ticker).tail(10)
if len(pl) >= 2:
    left, right = st.columns(2)
    with left:
        st.subheader("Revenue & Net Profit (10yr)")
        fig = go.Figure()
        fig.add_bar(x=pl["year"], y=pl["sales"], name="Revenue")
        fig.add_bar(x=pl["year"], y=pl["net_profit"], name="Net Profit")
        fig.update_layout(barmode="group", height=380, margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(fig, width='stretch')

    with right:
        st.subheader("ROE vs ROCE (10yr)")
        r10 = ratios.tail(10)
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=r10["year"], y=r10["return_on_equity_pct"], name="ROE %"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=r10["year"], y=r10["return_on_capital_employed_pct"], name="ROCE %"), secondary_y=True)
        fig2.update_layout(height=380, margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(fig2, width='stretch')
else:
    st.info("Fewer than 2 years of financial history available for chart display.")

st.divider()

# --- Pros and cons ---
st.subheader("Pros & Cons")
pc = get_pros_cons(ticker)
if pc.empty:
    st.caption("No pros/cons data available for this company.")
else:
    p1, p2 = st.columns(2)
    with p1:
        for _, r in pc.iterrows():
            if pd.notna(r.get("pros")) and r["pros"]:
                st.success(f"✅ {r['pros']}")
    with p2:
        for _, r in pc.iterrows():
            if pd.notna(r.get("cons")) and r["cons"]:
                st.error(f"❌ {r['cons']}")

_elapsed = time.time() - _t0
st.caption(f"Page loaded in {_elapsed:.2f}s")
