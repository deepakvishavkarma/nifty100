"""Sprint 2 orchestrator: run the full Ratio Engine and populate the DB.

Reads companies / sectors / P&L / balance sheet / cash flow from the Sprint 1
SQLite database, computes 50+ KPIs per company-year, and writes:
  - financial_ratios table (SQLite) - 40+ columns, 1,100+ rows
  - output/capital_allocation.csv
  - output/ratio_edge_cases.log
"""
import sys
import sqlite3
import csv
from pathlib import Path
from collections import defaultdict

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.analytics import ratios as R
from src.analytics import cagr as C
from src.analytics import cashflow_kpis as CF
from src.analytics.composite_score import winsorised_score, composite_quality_score

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "nifty100.db"
OUT_DIR = ROOT / "output"


def load_tables(conn):
    companies = pd.read_sql("SELECT * FROM companies", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
    cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    return companies, sectors, pl, bs, cf


def build_series(df: pd.DataFrame, company_id: str, value_col: str):
    sub = df[df["company_id"] == company_id].sort_values("year")
    return list(zip(sub["year"], sub[value_col]))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript((ROOT / "db" / "migration_sprint2.sql").read_text())

    companies, sectors, pl, bs, cf = load_tables(conn)
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    pl = pl.merge(bs[["company_id", "year", "equity_capital", "reserves", "borrowings",
                       "total_assets", "investments"]], on=["company_id", "year"], how="left")
    pl = pl.merge(cf[["company_id", "year", "operating_activity", "investing_activity",
                       "financing_activity"]], on=["company_id", "year"], how="left")

    rows = []
    capital_allocation_rows = []
    edge_cases = []

    for cid, cdf in pl.groupby("company_id"):
        cdf = cdf.sort_values("year").reset_index(drop=True)
        sector = sector_map.get(cid)

        revenue_series = list(zip(cdf["year"], cdf["sales"]))
        pat_series = list(zip(cdf["year"], cdf["net_profit"]))
        eps_series = list(zip(cdf["year"], cdf["eps"]))
        cfo_hist, pat_hist = [], []

        for i, row in cdf.iterrows():
            year = row["year"]
            eb = R.ebit(row["operating_profit"], row["depreciation"])
            npm = R.net_profit_margin(row["net_profit"], row["sales"])
            opm = R.operating_profit_margin(row["operating_profit"], row["sales"])
            opm_flag = R.opm_cross_check(opm, row["opm_percentage"])
            roe = R.return_on_equity(row["net_profit"], row["equity_capital"], row["reserves"])
            roce = R.return_on_capital_employed(eb, row["equity_capital"], row["reserves"], row["borrowings"])
            roa = R.return_on_assets(row["net_profit"], row["total_assets"])

            de = R.debt_to_equity(row["borrowings"], row["equity_capital"], row["reserves"])
            hlf = R.high_leverage_flag(de, sector)
            icr = R.interest_coverage(row["operating_profit"], row["other_income"], row["interest"])
            icr_lbl = R.icr_label(icr)
            icr_risk = R.icr_risk_flag(icr)
            ndebt = R.net_debt(row["borrowings"], row["investments"])
            at = R.asset_turnover(row["sales"], row["total_assets"])

            fcf = CF.free_cash_flow(row["operating_activity"], row["investing_activity"])
            capex = abs(row["investing_activity"]) if pd.notna(row["investing_activity"]) else None
            capex_int = CF.capex_intensity(row["investing_activity"], row["sales"])
            capex_cat = CF.capex_category(capex_int)
            fcf_conv = CF.fcf_conversion_rate(fcf, row["operating_profit"])

            cfo_hist.append(row["operating_activity"])
            pat_hist.append(row["net_profit"])
            cfo_q_score = CF.cfo_quality_score(cfo_hist, pat_hist)
            cfo_q_label = CF.cfo_quality_label(cfo_q_score)

            bvps = None
            if pd.notna(row["equity_capital"]) and pd.notna(row["reserves"]) and row["equity_capital"] not in (0,):
                comp = companies.loc[companies["id"] == cid]
                fv = comp["face_value"].iloc[0] if len(comp) else None
                if fv:
                    shares = row["equity_capital"] / fv
                    if shares:
                        bvps = (row["equity_capital"] + row["reserves"]) / shares

            windows_rev = C.compute_all_windows(revenue_series[: i + 1])
            windows_pat = C.compute_all_windows(pat_series[: i + 1])
            windows_eps = C.compute_all_windows(eps_series[: i + 1])

            cfo_pat_ratio_latest = (row["operating_activity"] / row["net_profit"]
                                     if row["net_profit"] not in (0, None) and pd.notna(row["operating_activity"]) else None)
            cfo_s, cfi_s, cff_s, pattern = CF.capital_allocation_pattern(
                row["operating_activity"], row["investing_activity"], row["financing_activity"],
                cfo_pat_ratio_latest)
            capital_allocation_rows.append({
                "company_id": cid, "year": year, "cfo_sign": cfo_s, "cfi_sign": cfi_s,
                "cff_sign": cff_s, "pattern_label": pattern,
            })

            # --- edge case logging ---
            if icr is None and row["interest"] in (0, None):
                edge_cases.append(f"{cid} {year}: ICR=None (debt-free substitution, interest=0)")
            for label, wdict in [("revenue", windows_rev), ("pat", windows_pat), ("eps", windows_eps)]:
                for w in (3, 5, 10):
                    flagval = wdict[f"cagr_{w}yr_flag"]
                    if flagval and flagval != C.FLAG_INSUFFICIENT:
                        edge_cases.append(f"{cid} {year}: {label}_cagr_{w}yr flag={flagval}")
            if row["sales"] in (0, None):
                edge_cases.append(f"{cid} {year}: division-by-zero avoided, sales=0/null")

            rows.append({
                "company_id": cid, "year": year,
                "net_profit_margin_pct": npm, "operating_profit_margin_pct": opm,
                "opm_cross_check_flag": int(opm_flag),
                "return_on_equity_pct": roe, "return_on_capital_employed_pct": roce,
                "return_on_assets_pct": roa,
                "debt_to_equity": de, "high_leverage_flag": int(hlf),
                "interest_coverage": icr, "icr_label": icr_lbl, "icr_risk_flag": int(icr_risk),
                "net_debt_cr": ndebt, "asset_turnover": at,
                "free_cash_flow_cr": fcf, "capex_cr": capex, "capex_intensity_pct": capex_int,
                "capex_category": capex_cat, "fcf_conversion_pct": fcf_conv,
                "cfo_quality_score": cfo_q_score, "cfo_quality_label": cfo_q_label,
                "earnings_per_share": row["eps"], "book_value_per_share": bvps,
                "dividend_payout_ratio_pct": row["dividend_payout"],
                "total_debt_cr": row["borrowings"], "cash_from_operations_cr": row["operating_activity"],
                "revenue_cagr_3yr": windows_rev["cagr_3yr"], "revenue_cagr_3yr_flag": windows_rev["cagr_3yr_flag"],
                "revenue_cagr_5yr": windows_rev["cagr_5yr"], "revenue_cagr_5yr_flag": windows_rev["cagr_5yr_flag"],
                "revenue_cagr_10yr": windows_rev["cagr_10yr"], "revenue_cagr_10yr_flag": windows_rev["cagr_10yr_flag"],
                "pat_cagr_3yr": windows_pat["cagr_3yr"], "pat_cagr_3yr_flag": windows_pat["cagr_3yr_flag"],
                "pat_cagr_5yr": windows_pat["cagr_5yr"], "pat_cagr_5yr_flag": windows_pat["cagr_5yr_flag"],
                "pat_cagr_10yr": windows_pat["cagr_10yr"], "pat_cagr_10yr_flag": windows_pat["cagr_10yr_flag"],
                "eps_cagr_3yr": windows_eps["cagr_3yr"], "eps_cagr_3yr_flag": windows_eps["cagr_3yr_flag"],
                "eps_cagr_5yr": windows_eps["cagr_5yr"], "eps_cagr_5yr_flag": windows_eps["cagr_5yr_flag"],
                "eps_cagr_10yr": windows_eps["cagr_10yr"], "eps_cagr_10yr_flag": windows_eps["cagr_10yr_flag"],
            })

    ratios_df = pd.DataFrame(rows)

    # --- Composite Quality Score: winsorised P10/P90 across latest year ---
    # Use the year with the broadest company coverage as the cross-sectional
    # benchmark - the chronologically max label can be a single stray company
    # (e.g. a mid-year transition row) which would collapse P10=P90.
    year_counts = ratios_df["year"].value_counts()
    latest_year = year_counts[year_counts >= year_counts.max() * 0.5].index.max()
    latest = ratios_df[ratios_df["year"] == latest_year]
    p10_90 = {}
    for col, invert in [("return_on_equity_pct", False), ("free_cash_flow_cr", False),
                         ("return_on_capital_employed_pct", False), ("debt_to_equity", True)]:
        vals = latest[col].dropna()
        p10_90[col] = (vals.quantile(0.10), vals.quantile(0.90), invert) if len(vals) else (0, 1, invert)

    def score_row(row):
        roe_s = winsorised_score(row["return_on_equity_pct"], *p10_90["return_on_equity_pct"][:2])
        fcf_s = winsorised_score(row["free_cash_flow_cr"], *p10_90["free_cash_flow_cr"][:2])
        roce_s = winsorised_score(row["return_on_capital_employed_pct"], *p10_90["return_on_capital_employed_pct"][:2])
        de_s = winsorised_score(row["debt_to_equity"], *p10_90["debt_to_equity"][:2], invert=True)
        return composite_quality_score(roe_s, fcf_s, roce_s, de_s)

    ratios_df["composite_quality_score"] = ratios_df.apply(score_row, axis=1)

    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    # --- Bank/NBFC ROCE + ROE anomaly cross-check vs companies.xlsx (Day 13) ---
    financials_ids = set(sectors[sectors["broad_sector"] == "Financials"]["company_id"])
    latest_ratios = ratios_df[ratios_df["year"] == latest_year].set_index("company_id")
    for _, comp in companies.iterrows():
        cid = comp["id"]
        if cid not in latest_ratios.index:
            continue
        computed_roce = latest_ratios.loc[cid, "return_on_capital_employed_pct"]
        source_roce = comp["roce_percentage"]
        if pd.notna(computed_roce) and pd.notna(source_roce) and abs(computed_roce - source_roce) > 5:
            tag = "sector-relative (Financials)" if cid in financials_ids else "non-financial"
            edge_cases.append(
                f"{cid}: ROCE anomaly ({tag}) - computed={computed_roce:.2f}%, source={source_roce}% "
                f"[category: data source issue - source pre-computed via different methodology]")
        computed_roe = latest_ratios.loc[cid, "return_on_equity_pct"]
        source_roe = comp["roe_percentage"]
        if pd.notna(computed_roe) and pd.notna(source_roe) and abs(computed_roe - source_roe) > 5:
            edge_cases.append(
                f"{cid}: ROE anomaly - computed={computed_roe:.2f}%, source={source_roe}% "
                f"[category: version difference - use ratio engine value for analytics, source for display only]")

    pd.DataFrame(capital_allocation_rows).to_csv(OUT_DIR / "capital_allocation.csv", index=False)
    with open(OUT_DIR / "ratio_edge_cases.log", "w") as f:
        f.write(f"Ratio Engine edge case log - {len(edge_cases)} entries\n")
        f.write("=" * 60 + "\n")
        for line in edge_cases:
            f.write(line + "\n")

    print(f"financial_ratios rows written: {len(ratios_df)}")
    print(f"capital_allocation.csv rows: {len(capital_allocation_rows)}")
    print(f"ratio_edge_cases.log entries: {len(edge_cases)}")

    conn.close()


if __name__ == "__main__":
    main()
