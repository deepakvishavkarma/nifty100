# Nifty 100 Financial Intelligence Platform

A 4-sprint-built analytics platform covering ETL, ratio computation, screening/peer comparison,
and an interactive dashboard for 92 Nifty 100 companies.

## Setup (fresh clone, ~15 min)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas openpyxl pyyaml matplotlib streamlit plotly pytest
```

## Build the database (Sprints 1-3, run once)

```bash
python db/build_db.py                          # Sprint 1: ETL -> nifty100.db
python src/analytics/populate_ratios.py         # Sprint 2: Ratio Engine -> financial_ratios table
python -m src.screener.export_screener          # Sprint 3: screener_output.xlsx
python -m src.analytics.peer                    # Sprint 3: peer_percentiles table
python -m src.analytics.export_peer_comparison   # Sprint 3: peer_comparison.xlsx
python -m src.analytics.radar_charts             # Sprint 3: reports/radar_charts/*.png
```

## Run the dashboard (Sprint 4)

```bash
python src/analytics/valuation.py               # generates output/valuation_summary.xlsx first
streamlit run src/dashboard/app.py
```

The app opens at `http://localhost:8501`. Use the sidebar **pages** menu to move between screens.

## Dashboard screens

| # | Screen | What it shows |
|---|---|---|
| 1 | **Home / Overview** | 6 summary KPI tiles (avg ROE, median P/E, median D/E, total companies, median Rev CAGR 5yr, debt-free count), sector donut chart, top-5 companies by composite quality score. Year selector in sidebar. |
| 2 | **Company Profile** | Search any of the 92 companies. Company card, 6 KPI tiles, 10yr Revenue/Net Profit bar chart, ROE vs ROCE dual-axis line chart, pros/cons badges. |
| 3 | **Financial Screener** | 10 metric sliders + 6 preset buttons (Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch). Live-updating results table with CSV download. |
| 4 | **Peer Comparison** | Pick one of 11 peer groups, see an 8-axis radar chart (company vs peer average) and a side-by-side KPI table with the benchmark company highlighted. |
| 5 | **Trend Analysis** | Search a company, overlay up to 3 metrics on a 10-year line chart with YoY % change annotated on each point. |
| 6 | **Sector Analysis** | Bubble chart (Revenue x ROE, bubble size = Market Cap) per sector, plus a sector median KPI bar chart. |
| 7 | **Capital Allocation Map** | Treemap of all companies by 8 capital-allocation patterns (Reinvestor, Distress Signal, etc.), with a drill-down company list per pattern. |
| 8 | **Annual Reports** | Search a company, see every available annual report year with a clickable BSE link, or a "Report unavailable" badge if the link is missing. |

## Data notes

- Universe is **92 companies** (not the full Nifty 100) after the Sprint 1 data-availability filter —
  see `output/sprint2_retro.md` for why.
- All dashboard queries default to the year with the broadest company coverage, not the
  chronologically latest label (some companies carry a stray single-year stub period).
- 46/92 companies have no assigned peer group; the Peer Comparison and radar-chart tooling handle
  this gracefully rather than erroring.

## Performance

Company Profile screen load time was measured across 10 tickers (spanning IT, Financials, FMCG,
Energy, Healthcare, and one thin-history company): all loaded in well under 1 second, against a
3-second target (see `output/sprint4_retro.md`).

## Project status

| Sprint | Scope | Status |
|---|---|---|
| 1 | ETL pipeline, 12-table SQLite DB, 16 DQ rules | ✅ Complete |
| 2 | Ratio Engine — 50+ KPIs, CAGR, cash flow quality | ✅ Complete |
| 3 | Screener (6 presets), Peer Comparison (11 groups), radar charts | ✅ Complete |
| 4 | Streamlit Dashboard (8 screens), Valuation module | ✅ Complete |
| 5-6 | NLP/clustering, REST API, testing & QA | Not yet started |
