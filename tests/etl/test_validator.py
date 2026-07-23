import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.etl.validator import run_dq_rules


def _base_frames():
    """Minimal valid frame set the DQ engine can run against."""
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})
    pl = pd.DataFrame({
        "company_id": ["TCS", "INFY"], "year": ["2023-03", "2023-03"],
        "sales": [225458, 150000], "operating_profit": [48534, 30000],
        "opm_percentage": [21.5, 20.0], "net_profit": [34990, 20000],
        "eps": [95.3, 60.0], "tax_percentage": [25.0, 25.0],
        "dividend_payout": [45.0, 40.0],
    })
    bs = pd.DataFrame({
        "company_id": ["TCS", "INFY"], "year": ["2023-03", "2023-03"],
        "total_assets": [907, 800], "total_liabilities": [907, 800],
        "fixed_assets": [109, 50],
    })
    cf = pd.DataFrame({
        "company_id": ["TCS", "INFY"], "year": ["2023-03", "2023-03"],
        "operating_activity": [40000, 25000], "investing_activity": [-10000, -5000],
        "financing_activity": [-20000, -15000], "net_cash_flow": [10000, 5000],
    })
    docs = pd.DataFrame({
        "company_id": ["TCS"], "Year": [2023], "Annual_Report": ["https://x.com/a.pdf"],
    })
    return {"companies": companies, "profitandloss": pl, "balancesheet": bs,
            "cashflow": cf, "documents": docs}


def test_dq01_duplicate_pk_triggers():
    frames = _base_frames()
    frames["companies"] = pd.DataFrame({"id": ["TCS", "TCS"]})
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-01" and x["severity"] == "CRITICAL" for x in v)


def test_dq04_bs_balance_triggers():
    frames = _base_frames()
    frames["balancesheet"].loc[0, "total_liabilities"] = 950  # >1% off vs 907 assets
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-04" for x in v)


def test_dq06_zero_sales_triggers():
    frames = _base_frames()
    frames["profitandloss"].loc[0, "sales"] = 0
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-06" for x in v)


def test_no_findings_on_clean_data_for_bs_and_sales():
    frames = _base_frames()
    v = run_dq_rules(frames)
    assert not any(x["rule_id"] == "DQ-04" for x in v)
    assert not any(x["rule_id"] == "DQ-06" for x in v)


def test_dq11_tax_rate_out_of_range():
    frames = _base_frames()
    frames["profitandloss"].loc[0, "tax_percentage"] = 75
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-11" for x in v)


def test_dq12_dividend_payout_cap():
    frames = _base_frames()
    frames["profitandloss"].loc[0, "dividend_payout"] = 250
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-12" for x in v)


def test_dq14_eps_sign_mismatch():
    frames = _base_frames()
    frames["profitandloss"].loc[0, "eps"] = -5
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-14" for x in v)
