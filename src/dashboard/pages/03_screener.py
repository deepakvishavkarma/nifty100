"""Financial Screener screen (Sprint 4, Day 24)."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_screener_universe

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = ROOT / "config" / "screener_config.yaml"

st.set_page_config(page_title="Screener | Nifty 100 Analytics", layout="wide")
st.title("🔍 Financial Screener")

universe = get_screener_universe()
config = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {"presets": {}}

SLIDER_DEFS = [
    ("min_roe", "ROE min (%)", "return_on_equity_pct", ">="),
    ("max_de", "D/E max", "debt_to_equity", "<="),
    ("min_fcf", "FCF min (Cr)", "free_cash_flow_cr", ">="),
    ("min_revenue_cagr", "Revenue CAGR 5yr min (%)", "revenue_cagr_5yr", ">="),
    ("min_pat_cagr", "PAT CAGR 5yr min (%)", "pat_cagr_5yr", ">="),
    ("min_opm", "OPM min (%)", "operating_profit_margin_pct", ">="),
    ("max_pe", "P/E max", "pe_ratio", "<="),
    ("max_pb", "P/B max", "pb_ratio", "<="),
    ("min_div_yield", "Dividend Yield min (%)", "dividend_yield_pct", ">="),
    ("min_icr", "ICR min", "interest_coverage", ">="),
]

PRESET_DEFAULTS = {
    "Quality Compounder": {"min_roe": 15, "max_de": 1.0, "min_fcf": 0, "min_revenue_cagr": 10},
    "Value Pick": {"max_pe": 35, "max_pb": 5, "max_de": 2.0, "min_div_yield": 1},
    "Growth Accelerator": {"min_pat_cagr": 20, "min_revenue_cagr": 15, "max_de": 2.0},
    "Dividend Champion": {"min_div_yield": 2, "min_fcf": 0},
    "Debt-Free Blue Chip": {"max_de": 0.05, "min_roe": 12},
    "Turnaround Watch": {"min_revenue_cagr": 10},
}

if "slider_values" not in st.session_state:
    st.session_state.slider_values = {}

st.sidebar.subheader("Preset Screens")
preset_cols = st.sidebar.columns(2)
preset_names = list(PRESET_DEFAULTS.keys())
for i, name in enumerate(preset_names):
    if preset_cols[i % 2].button(name, width='stretch'):
        st.session_state.slider_values = PRESET_DEFAULTS[name]
        st.rerun()

if st.sidebar.button("Reset filters", width='stretch'):
    st.session_state.slider_values = {}
    st.rerun()

st.sidebar.subheader("Custom Filters")


def _bounds(col):
    vals = universe[col].dropna()
    if vals.empty:
        return 0.0, 100.0
    return float(vals.min()), float(vals.max())


active_filters = {}
for key, label, col, op in SLIDER_DEFS:
    lo, hi = _bounds(col)
    if lo == hi:
        hi = lo + 1
    default = st.session_state.slider_values.get(key, lo if op == ">=" else hi)
    default = max(lo, min(hi, default))
    value = st.sidebar.slider(label, min_value=round(lo, 2), max_value=round(hi, 2), value=round(float(default), 2))
    is_at_default = (op == ">=" and value <= lo) or (op == "<=" and value >= hi)
    if not is_at_default:
        active_filters[col] = (op, value)

# --- Apply filters ---
filtered = universe.copy()
for col, (op, value) in active_filters.items():
    if op == ">=":
        filtered = filtered[filtered[col] >= value]
    else:
        filtered = filtered[filtered[col] <= value]

st.markdown(f"### {len(filtered)} companies match your filters")

display_cols = ["company_id", "company_name", "broad_sector", "composite_quality_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
                 "revenue_cagr_5yr", "pat_cagr_5yr", "pe_ratio", "pb_ratio", "dividend_yield_pct"]
display_cols = [c for c in display_cols if c in filtered.columns]

result_table = filtered[display_cols].rename(columns={
    "company_id": "Ticker", "company_name": "Company", "broad_sector": "Sector",
    "composite_quality_score": "Quality Score", "return_on_equity_pct": "ROE %",
    "debt_to_equity": "D/E", "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "Rev CAGR 5yr %", "pat_cagr_5yr": "PAT CAGR 5yr %",
    "pe_ratio": "P/E", "pb_ratio": "P/B", "dividend_yield_pct": "Div Yield %",
}).sort_values("Quality Score", ascending=False, na_position="last").round(2)

st.dataframe(result_table, width='stretch', hide_index=True)

csv_bytes = result_table.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="screener_results.csv", mime="text/csv")
