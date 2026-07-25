import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.etl.validator import run_dq_rules
from tests.etl.test_validator import _base_frames


def test_dq02_duplicate_year_pair_triggers():
    frames = _base_frames()
    dup = frames["profitandloss"].iloc[[0]].copy()  # duplicate TCS/2023-03
    frames["profitandloss"] = pd.concat([frames["profitandloss"], dup], ignore_index=True)
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-02" and x["severity"] == "CRITICAL" for x in v)


def test_dq03_fk_orphan_triggers():
    frames = _base_frames()
    orphan = frames["profitandloss"].iloc[[0]].copy()
    orphan["company_id"] = "GHOSTCO"
    frames["profitandloss"] = pd.concat([frames["profitandloss"], orphan], ignore_index=True)
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-03" and x["company_id"] == "GHOSTCO" for x in v)


def test_dq05_opm_cross_check_mismatch():
    frames = _base_frames()
    # operating_profit/sales for TCS = 48534/225458*100 = 21.53; force stated far off
    frames["profitandloss"].loc[0, "opm_percentage"] = 10.0
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-05" for x in v)


def test_dq09_net_cash_mismatch():
    frames = _base_frames()
    frames["cashflow"].loc[0, "net_cash_flow"] = 999999  # way off from CFO+CFI+CFF
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-09" for x in v)


def test_dq10_negative_fixed_assets():
    frames = _base_frames()
    frames["balancesheet"].loc[0, "fixed_assets"] = -50
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-10" for x in v)


def test_dq13_missing_annual_report_url():
    frames = _base_frames()
    frames["documents"].loc[0, "Annual_Report"] = None
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-13" for x in v)


def test_dq15_informational_balance_counter_present():
    frames = _base_frames()
    v = run_dq_rules(frames)
    dq15 = [x for x in v if x["rule_id"] == "DQ-15"]
    assert len(dq15) == 1
    assert dq15[0]["severity"] == "INFO"


def test_dq16_coverage_flag_for_thin_history():
    frames = _base_frames()
    # TCS only has 1 year of history in the fixture -> < 5yr coverage
    v = run_dq_rules(frames)
    assert any(x["rule_id"] == "DQ-16" and x["company_id"] == "TCS" for x in v)
