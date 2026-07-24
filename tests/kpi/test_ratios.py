import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.analytics import ratios as R
from src.analytics import cagr as C
from src.analytics import cashflow_kpis as CF


# ---- Profitability / leverage / efficiency (10 tests) ----

def test_roe_positive():
    assert R.return_on_equity(net_profit=100, equity_capital=100, reserves=400) == 20.0

def test_roe_negative_equity_returns_none():
    assert R.return_on_equity(net_profit=100, equity_capital=100, reserves=-150) is None

def test_npm_zero_sales_returns_none():
    assert R.net_profit_margin(net_profit=100, sales=0) is None

def test_opm_cross_check_flags_mismatch():
    assert R.opm_cross_check(computed_opm=21.5, source_opm=19.0) is True

def test_opm_cross_check_within_tolerance():
    assert R.opm_cross_check(computed_opm=21.5, source_opm=21.0) is False

def test_de_debtfree_returns_zero():
    assert R.debt_to_equity(borrowings=0, equity_capital=100, reserves=400) == 0

def test_icr_interest_zero_returns_none():
    assert R.interest_coverage(operating_profit=1000, other_income=100, interest=0) is None

def test_icr_label_debt_free():
    assert R.icr_label(None) == "Debt Free"

def test_high_leverage_flag_true_for_nonfinancial():
    assert R.high_leverage_flag(de_ratio=6.0, broad_sector="Industrials") is True

def test_high_leverage_flag_suppressed_for_financials():
    assert R.high_leverage_flag(de_ratio=6.0, broad_sector="Financials") is False

def test_asset_turnover_zero_assets_returns_none():
    assert R.asset_turnover(sales=1000, total_assets=0) is None

def test_roce_normal():
    eb = R.ebit(operating_profit=500, depreciation=100)
    assert eb == 400
    roce = R.return_on_capital_employed(eb, equity_capital=100, reserves=400, borrowings=500)
    assert round(roce, 2) == 40.0


# ---- CAGR engine (6 edge cases + 2 normal) ----

def test_cagr_normal():
    value, flag = C.cagr(base_value=100, end_value=161.05, n_years=5)
    assert flag is None
    assert round(value, 1) == 10.0

def test_cagr_turnaround():
    value, flag = C.cagr(base_value=-100, end_value=200, n_years=3)
    assert value is None
    assert flag == C.FLAG_TURNAROUND

def test_cagr_decline_to_loss():
    value, flag = C.cagr(base_value=100, end_value=-50, n_years=3)
    assert value is None
    assert flag == C.FLAG_DECLINE_TO_LOSS

def test_cagr_both_negative():
    value, flag = C.cagr(base_value=-100, end_value=-50, n_years=3)
    assert value is None
    assert flag == C.FLAG_BOTH_NEGATIVE

def test_cagr_zero_base():
    value, flag = C.cagr(base_value=0, end_value=100, n_years=3)
    assert value is None
    assert flag == C.FLAG_ZERO_BASE

def test_cagr_insufficient_data():
    series = [("2022-03", 100), ("2023-03", 110)]
    value, flag = C.cagr_over_window(series, n_years=5)
    assert value is None
    assert flag == C.FLAG_INSUFFICIENT


# ---- Cash flow KPIs (2 tests) ----

def test_capex_intensity_asset_light():
    intensity = CF.capex_intensity(investing_activity=-200, sales=10000)
    assert CF.capex_category(intensity) == "Asset Light"

def test_capital_allocation_reinvestor_pattern():
    cfo_s, cfi_s, cff_s, label = CF.capital_allocation_pattern(cfo=500, cfi=-200, cff=-100, cfo_pat_ratio=0.7)
    assert (cfo_s, cfi_s, cff_s) == (1, -1, -1)
    assert label == "Reinvestor"
