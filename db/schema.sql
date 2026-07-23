PRAGMA foreign_keys = ON;

CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

CREATE TABLE profitandloss (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales REAL, expenses REAL, operating_profit REAL, opm_percentage REAL,
    other_income REAL, interest REAL, depreciation REAL, profit_before_tax REAL,
    tax_percentage REAL, net_profit REAL, eps REAL, dividend_payout REAL,
    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE balancesheet (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL, reserves REAL, borrowings REAL, other_liabilities REAL,
    total_liabilities REAL, fixed_assets REAL, cwip REAL, investments REAL,
    other_asset REAL, total_assets REAL,
    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE cashflow (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL, investing_activity REAL, financing_activity REAL,
    net_cash_flow REAL,
    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE analysis (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE documents (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE prosandcons (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE sectors (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL UNIQUE,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE stock_prices (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL, high_price REAL, low_price REAL, close_price REAL,
    volume INTEGER, adjusted_close REAL,
    UNIQUE (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE market_cap (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    market_cap_crore REAL, enterprise_value_crore REAL, pe_ratio REAL,
    pb_ratio REAL, ev_ebitda REAL, dividend_yield_pct REAL,
    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE financial_ratios (
    row_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    net_profit_margin_pct REAL, operating_profit_margin_pct REAL,
    return_on_equity_pct REAL, debt_to_equity REAL, interest_coverage REAL,
    asset_turnover REAL, free_cash_flow_cr REAL, capex_cr REAL,
    earnings_per_share REAL, book_value_per_share REAL,
    dividend_payout_ratio_pct REAL, total_debt_cr REAL, cash_from_operations_cr REAL,
    UNIQUE (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE peer_groups (
    row_id INTEGER PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_pl_company ON profitandloss(company_id);
CREATE INDEX idx_bs_company ON balancesheet(company_id);
CREATE INDEX idx_cf_company ON cashflow(company_id);
CREATE INDEX idx_ratios_company ON financial_ratios(company_id);
CREATE INDEX idx_prices_company ON stock_prices(company_id);
CREATE INDEX idx_peer_group ON peer_groups(peer_group_name);
