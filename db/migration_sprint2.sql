-- Sprint 2 migration: extend financial_ratios with ratio-engine outputs.
-- Run once, before populate_ratios.py inserts computed rows.

DROP TABLE IF EXISTS financial_ratios;

CREATE TABLE financial_ratios (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    -- Profitability
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    opm_cross_check_flag INTEGER,
    return_on_equity_pct REAL,
    return_on_capital_employed_pct REAL,
    return_on_assets_pct REAL,

    -- Leverage
    debt_to_equity REAL,
    high_leverage_flag INTEGER,
    interest_coverage REAL,
    icr_label TEXT,
    icr_risk_flag INTEGER,
    net_debt_cr REAL,

    -- Efficiency
    asset_turnover REAL,

    -- Cash flow quality
    free_cash_flow_cr REAL,
    capex_cr REAL,
    capex_intensity_pct REAL,
    capex_category TEXT,
    fcf_conversion_pct REAL,
    cfo_quality_score REAL,
    cfo_quality_label TEXT,

    -- Direct source pass-throughs
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    -- Growth (CAGR) - 3/5/10yr for revenue, PAT, EPS
    revenue_cagr_3yr REAL, revenue_cagr_3yr_flag TEXT,
    revenue_cagr_5yr REAL, revenue_cagr_5yr_flag TEXT,
    revenue_cagr_10yr REAL, revenue_cagr_10yr_flag TEXT,
    pat_cagr_3yr REAL, pat_cagr_3yr_flag TEXT,
    pat_cagr_5yr REAL, pat_cagr_5yr_flag TEXT,
    pat_cagr_10yr REAL, pat_cagr_10yr_flag TEXT,
    eps_cagr_3yr REAL, eps_cagr_3yr_flag TEXT,
    eps_cagr_5yr REAL, eps_cagr_5yr_flag TEXT,
    eps_cagr_10yr REAL, eps_cagr_10yr_flag TEXT,

    -- Composite
    composite_quality_score REAL,

    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_ratios2_company ON financial_ratios(company_id);
CREATE INDEX idx_ratios2_year ON financial_ratios(year);
