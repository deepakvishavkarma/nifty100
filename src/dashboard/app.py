"""Nifty 100 Financial Intelligence Platform — Streamlit dashboard entry point.

Run with: streamlit run src/dashboard/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Nifty 100 Financial Intelligence Platform")
st.markdown(
    """
Welcome — use the sidebar to navigate between the 8 analytics screens:

1. **Home / Overview** — universe-level summary KPIs and sector breakdown
2. **Company Profile** — search any of the 92 companies for a full financial snapshot
3. **Financial Screener** — filter the universe with live sliders or preset screens
4. **Peer Comparison** — radar chart + side-by-side table within a peer group
5. **Trend Analysis** — multi-metric overlay charts over time
6. **Sector Analysis** — bubble chart and sector median KPIs
7. **Capital Allocation Map** — treemap of capital allocation patterns
8. **Annual Reports** — browse annual report links per company

All data is served from `data/nifty100.db`, built in Sprints 1–3.
"""
)

st.info("Select a screen from the sidebar (**pages** menu, top-left) to get started.")
