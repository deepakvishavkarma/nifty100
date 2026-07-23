"""16 Data Quality rules applied at ETL load time (see project spec, Section 14)."""
import pandas as pd


def run_dq_rules(clean: dict[str, pd.DataFrame]) -> list[dict]:
    """Run all 16 DQ rules against the cleaned tables. Returns a list of
    violation records: {rule_id, table, company_id, year, field, issue, severity}.
    """
    v = []
    companies = clean["companies"]
    pl = clean["profitandloss"]
    bs = clean["balancesheet"]
    cf = clean["cashflow"]
    docs = clean["documents"]

    def add(rule_id, table, company_id, year, field, issue, severity):
        v.append({
            "rule_id": rule_id, "table": table, "company_id": company_id,
            "year": year, "field": field, "issue": issue, "severity": severity,
        })

    # DQ-01: Company PK uniqueness
    dup_ids = companies["id"][companies["id"].duplicated(keep=False)]
    for cid in dup_ids.unique():
        add("DQ-01", "companies", cid, None, "id", "Duplicate company ticker", "CRITICAL")

    # DQ-02: Annual PK uniqueness (company_id, year) in P&L, BS, CF
    for tname, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        dups = df[df.duplicated(subset=["company_id", "year"], keep=False)]
        for _, row in dups.iterrows():
            add("DQ-02", tname, row["company_id"], row["year"], "company_id+year",
                "Duplicate (company_id, year) pair", "CRITICAL")

    # DQ-03: FK integrity - company_id in child tables must exist in companies.id
    valid_ids = set(companies["id"])
    for tname, df in clean.items():
        if tname == "companies" or "company_id" not in df.columns:
            continue
        orphans = df[~df["company_id"].isin(valid_ids)]
        for _, row in orphans.iterrows():
            add("DQ-03", tname, row["company_id"], row.get("year"), "company_id",
                "Orphan row - no matching company", "CRITICAL")

    # DQ-04: Balance sheet balance check, |assets - liabilities| / assets < 1%
    for _, row in bs.iterrows():
        ta, tl = row.get("total_assets"), row.get("total_liabilities")
        if pd.notna(ta) and pd.notna(tl) and ta not in (0, None):
            if abs(ta - tl) / abs(ta) >= 0.01:
                add("DQ-04", "balancesheet", row["company_id"], row["year"],
                    "total_assets/total_liabilities", "Balance sheet does not balance (>1%)", "WARNING")

    # DQ-05: OPM cross-check
    for _, row in pl.iterrows():
        sales, op, opm = row.get("sales"), row.get("operating_profit"), row.get("opm_percentage")
        if pd.notna(sales) and sales not in (0, None) and pd.notna(op) and pd.notna(opm):
            computed = op / sales * 100
            if abs(opm - computed) >= 1.0:
                add("DQ-05", "profitandloss", row["company_id"], row["year"],
                    "opm_percentage", f"OPM mismatch: stated={opm}, computed={computed:.2f}", "WARNING")

    # DQ-06: Positive sales
    bad_sales = pl[pl["sales"] <= 0]
    for _, row in bad_sales.iterrows():
        add("DQ-06", "profitandloss", row["company_id"], row["year"], "sales",
            "Sales <= 0", "WARNING")

    # DQ-07/DQ-08 are enforced upstream during normalisation (year/ticker parse
    # failures are rejected before validation runs), logged separately as rejects.

    # DQ-09: Net cash check, |net_cash_flow - (CFO+CFI+CFF)| <= 10 Cr
    for _, row in cf.iterrows():
        cfo, cfi, cff, ncf = (row.get("operating_activity"), row.get("investing_activity"),
                               row.get("financing_activity"), row.get("net_cash_flow"))
        if all(pd.notna(x) for x in (cfo, cfi, cff, ncf)):
            if abs(ncf - (cfo + cfi + cff)) > 10:
                add("DQ-09", "cashflow", row["company_id"], row["year"], "net_cash_flow",
                    "net_cash_flow does not match CFO+CFI+CFF (>10 Cr tolerance)", "WARNING")

    # DQ-10: Non-negative fixed assets
    neg_fa = bs[bs["fixed_assets"] < 0]
    for _, row in neg_fa.iterrows():
        add("DQ-10", "balancesheet", row["company_id"], row["year"], "fixed_assets",
            "Negative fixed_assets", "WARNING")

    # DQ-11: Tax rate range 0-60%
    bad_tax = pl[(pl["tax_percentage"] < 0) | (pl["tax_percentage"] > 60)]
    for _, row in bad_tax.iterrows():
        add("DQ-11", "profitandloss", row["company_id"], row["year"], "tax_percentage",
            f"Tax rate out of range: {row['tax_percentage']}", "WARNING")

    # DQ-12: Dividend payout cap <= 200%
    bad_div = pl[pl["dividend_payout"] > 200]
    for _, row in bad_div.iterrows():
        add("DQ-12", "profitandloss", row["company_id"], row["year"], "dividend_payout",
            f"Dividend payout > 200%: {row['dividend_payout']}", "WARNING")

    # DQ-13: URL validity (documents) - structural check only (no live HTTP
    # calls in this offline pipeline); flags null/empty URLs.
    bad_urls = docs[docs["Annual_Report"].isna() | (docs["Annual_Report"].astype(str).str.strip() == "")]
    for _, row in bad_urls.iterrows():
        add("DQ-13", "documents", row["company_id"], row["Year"], "Annual_Report",
            "Missing/empty annual report URL", "WARNING")

    # DQ-14: EPS sign consistency (eps > 0 if net_profit > 0)
    bad_eps = pl[(pl["net_profit"] > 0) & (pl["eps"] <= 0)]
    for _, row in bad_eps.iterrows():
        add("DQ-14", "profitandloss", row["company_id"], row["year"], "eps",
            "EPS <= 0 while net_profit > 0", "WARNING")

    # DQ-15: Informational strict balance counter
    strict_ok = bs[bs["total_assets"] == bs["total_liabilities"]]
    add("DQ-15", "balancesheet", None, None, "total_assets/total_liabilities",
        f"{len(strict_ok)}/{len(bs)} rows balance exactly (informational)", "INFO")

    # DQ-16: Coverage check - each company needs >= 5 years across P&L/BS/CF
    for cid in companies["id"]:
        years = set(pl[pl["company_id"] == cid]["year"]) | \
                set(bs[bs["company_id"] == cid]["year"]) | \
                set(cf[cf["company_id"] == cid]["year"])
        if len(years) < 5:
            add("DQ-16", "companies", cid, None, "year_coverage",
                f"Only {len(years)} distinct fiscal years of history", "WARNING")

    return v
