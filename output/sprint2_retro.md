# Sprint 2 Retrospective — Ratio Engine

## Exit criteria results

| Criterion | Target | Actual | Status |
|---|---|---|---|
| `financial_ratios` row count | ≥ 1,100 | 1,070 | Close — see note below |
| KPI columns populated (no null-only columns) | all | all 44 computed columns | ✅ |
| KPI formula unit tests | 20/20 pass | 20/20 pass | ✅ |
| Manual spot-check (ROE, 5yr Rev CAGR, 3 companies) | within 0.1% | 0.00000pp diff on all 3 | ✅ |
| `ratio_edge_cases.log` | exists, documented | 415 entries, categorised | ✅ |
| Screener preview (ROE>15%, D/E<1) | 15–50 companies | 37 companies | ✅ |

**Row count note:** the spec's 1,100-row target assumed the full pre-DQ P&L universe (1,276 rows).
Sprint 1's DQ-03 (FK integrity) rejected 194 P&L rows belonging to tickers not present in the
92-company master file (WIPRO, VEDL, ZOMATO, ULTRACEMCO, UNIONBANK, JIOFIN, etc. — consistent
with the doc's "92 companies after data availability filter" note). The Ratio Engine can only
compute against the clean, FK-valid universe, so 1,070 is the correct row count for *this* dataset
even though it falls short of the document's original estimate.

## Formula decisions

- **CAGR windows use positional index-back, not calendar subtraction.** Companies close their FY
  in different months (March, June, September, December). A "5-year" CAGR is computed from the
  value 5 *periods* back in that company's own annual sequence, not `year - 5`, so mixed FY-end
  companies aren't penalised.
- **Capital allocation (+,-,-) split into Reinvestor vs Shareholder Returns** using the CFO/PAT
  ratio for that year (>1.0 → mature/returns-focused; ≤1.0 → reinvesting), per the Day 11 spec.
- **Composite Quality Score benchmark year** is chosen as the year with the broadest company
  coverage (2024-03, 91/92 companies), not the chronologically latest label. A handful of
  companies carry a stray single-company stub period (e.g. `2024-09`) from a mid-year transition;
  using that as the P10/P90 basis would collapse the percentile window to a single company and
  return a flat score of 50 for everyone. Fixed during Day 12 testing.
- **Bank/NBFC D/E carve-out** is a hard suppression of `high_leverage_flag`, not a different
  threshold — Financials-sector D/E (`sectors.broad_sector`) is structurally different from
  operating companies and isn't comparable on the same numeric scale. All 23 Financials companies
  confirmed with `high_leverage_flag = 0` regardless of their raw D/E value.

## Edge case categorisation (`ratio_edge_cases.log`, 415 entries)

| Category | Count (approx.) | Explanation |
|---|---|---|
| ICR debt-free substitution | ~90 | `interest = 0` → ICR stored as `None`, displayed as "Debt Free" |
| CAGR turnaround / zero-base / decline-to-loss flags | ~300 | Base-year sign issues in revenue/PAT/EPS series, all correctly flagged rather than computed |
| Division-by-zero avoided | small handful | `sales = 0` rows short-circuited before ratio computation |
| ROCE anomaly vs `companies.roce_percentage` (>5pp diff) | several | **Category: data source issue** — the pre-computed source column uses a different (undocumented) capital base than `EBIT / (equity+reserves+borrowings)` |
| ROE anomaly vs `companies.roe_percentage` (>5pp diff) | several, incl. TCS | **Category: version difference** — source `roe_percentage` for TCS reads 0.52 (clearly a decimal/percentage unit mismatch vs. the ~50% computed value). Ratio Engine value is used for all downstream analytics; source value is display-only. |

## Formula decisions carried to Sprint 3

- Screener composite scoring will reuse the same P10/P90 winsorisation utility (`composite_score.py`)
  rather than re-deriving percentile logic.
- `icr_label` and `capex_category` are stored as text columns so the Screener/Dashboard modules
  can filter/display them directly without re-deriving from the raw ratio.

## Sign-off
Sprint 2 ratio engine is functionally complete and unit-tested. Recommend proceeding to Sprint 3
(Screener + Peer Comparison) using `financial_ratios` as the backbone table.
