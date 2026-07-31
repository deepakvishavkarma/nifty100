# Sprint 4 Retrospective — Streamlit Dashboard + Valuation

## Exit criteria results

| Criterion | Target | Actual | Status |
|---|---|---|---|
| All 8 screens load without errors | 0 exceptions | 0 exceptions (verified via `AppTest`, all 9 scripts incl. main app) | ✅ |
| Company Profile load time | < 3s | 0.34-1.06s across 10 tickers (first run includes cache warm-up) | ✅ |
| Screener CSV download | valid file, correct headers | confirmed at the data layer — well-formed CSV with expected columns | ✅ |
| `valuation_summary.xlsx` row count | 92 rows | 92 rows | ✅ |

## Testing approach

Streamlit apps can't be exercised through a normal browser in this environment, so verification
used two layers instead of a manual click-through:

1. **`streamlit.testing.v1.AppTest`** — actually executes each page's Python inside a simulated
   Streamlit runtime and captures unhandled exceptions. This is a stronger check than an HTTP 200,
   which only confirms the page shell loaded, not that the script ran clean.
2. **Live headless server + curl** — confirmed the app binds and serves all 8 page routes.

## Bug found and fixed during QA

`AppTest` caught a real bug on the Home screen: `get_screener_universe()` already joins in
`company_name`, but the Top-5 table was merging the companies table again, creating a duplicate
column and a `KeyError`. This would have crashed the Home screen for every user on first load —
exactly the kind of thing that's easy to miss reading code but immediate once the page actually
runs. Fixed by removing the redundant merge.

## Edge cases verified (Day 27 spec)

- **10 tickers across 6 sectors** (TCS, INFY, HDFCBANK, ICICIBANK, HINDUNILVR, NESTLEIND,
  RELIANCE, ONGC, SUNPHARMA, JIOFIN) — all load without error.
- **Partial-data company (JIOFIN, 2yr history)** — Profile and Trend screens don't crash; Trend
  screen explicitly notes when fewer than 10 years of history are available.
- **Extreme screener slider values** (all sliders at min, then all at max) — both extremes run
  clean; an all-max query correctly returns zero or very few rows without raising.
- **Not-found ticker search** — shows "Ticker not found — please try another" rather than
  crashing, and further interaction on that screen is safely blocked (`st.stop()`).

## Deprecation cleanup

Streamlit 1.60 warns that `use_container_width` is being retired in favour of `width='stretch'`/
`width='content'`. Since this codebase will likely outlive that migration window, all chart/table
calls were updated during this sprint rather than leaving a known deprecation for Sprint 5-6 to
trip over.

## Design decisions

- **Composite quality score is computed on-the-fly in `get_screener_universe()`**, not stored in
  `financial_ratios`, reusing the Sprint 3 `compute_sector_relative_score()` function directly so
  scoring logic has exactly one implementation across the Screener export and the dashboard.
- **Year selection** on Home and Capital Allocation screens defaults to the broadest-coverage year
  (matching the Sprint 2/3 convention), with a manual override dropdown, rather than silently
  always pinning to one hardcoded year.
- **CSV export** builds the file entirely from the already-filtered, already-renamed display
  DataFrame, so the downloaded file's headers match exactly what the user sees on screen.

## Sign-off

Sprint 4 dashboard and valuation module are functionally complete, verified against real data with
automated execution testing (not just static review), and one genuine bug was caught and fixed
before delivery. Recommend proceeding to Sprint 5 (NLP/Clustering/Reports).
