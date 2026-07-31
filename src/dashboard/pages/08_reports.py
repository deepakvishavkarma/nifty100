"""Annual Reports screen (Sprint 4, Day 25)."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports | Nifty 100 Analytics", layout="wide")
st.title("📄 Annual Reports")

companies = get_companies()
search_options = (companies["company_id"] + " — " + companies["company_name"]).tolist()
query = st.text_input("Search by company name or ticker", "")
matches = [s for s in search_options if query.upper() in s.upper()] if query else search_options

if not matches:
    st.warning("Ticker not found — please try another")
    st.stop()

selection = st.selectbox("Select company", matches, index=0)
ticker = selection.split(" — ")[0]

docs = get_documents(ticker)
if docs.empty:
    st.info("No annual report links available for this company.")
    st.stop()

st.subheader(f"Annual Reports — {ticker}")
for _, row in docs.iterrows():
    year = row.get("year")
    url = row.get("annual_report")
    col1, col2 = st.columns([1, 5])
    col1.write(f"**{year}**")
    if pd.notna(url) and str(url).strip():
        col2.markdown(f"[Open report ↗]({url})")
    else:
        col2.markdown(":red-background[Report unavailable]")
