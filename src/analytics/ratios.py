"""Profitability, leverage, and efficiency ratio formulas (Sprint 2, Day 8-9).

Every function takes plain numeric inputs (already extracted from the P&L /
Balance Sheet rows) and returns either a float or None for the documented
edge cases. Keeping these as pure functions makes them trivially unit
testable without touching the database.
"""
from __future__ import annotations


# ---------------------------------------------------------------- Day 8 ----

def net_profit_margin(net_profit: float, sales: float) -> float | None:
    """NPM = net_profit / sales x 100. None if sales = 0."""
    if sales in (0, None) or net_profit is None:
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit: float, sales: float) -> float | None:
    """OPM = operating_profit / sales x 100. None if sales = 0."""
    if sales in (0, None) or operating_profit is None:
        return None
    return operating_profit / sales * 100


def opm_cross_check(computed_opm: float | None, source_opm: float | None) -> bool:
    """True if computed OPM differs from the source opm_percentage field by >1pp."""
    if computed_opm is None or source_opm is None:
        return False
    return abs(computed_opm - source_opm) > 1.0


def return_on_equity(net_profit: float, equity_capital: float, reserves: float) -> float | None:
    """ROE = net_profit / (equity + reserves) x 100. None if equity+reserves <= 0."""
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    denom = equity_capital + reserves
    if denom <= 0:
        return None
    return net_profit / denom * 100


def return_on_capital_employed(ebit: float, equity_capital: float, reserves: float,
                                borrowings: float) -> float | None:
    """ROCE = EBIT / (equity + reserves + borrowings) x 100."""
    if any(v is None for v in (ebit, equity_capital, reserves, borrowings)):
        return None
    denom = equity_capital + reserves + borrowings
    if denom <= 0:
        return None
    return ebit / denom * 100


def return_on_assets(net_profit: float, total_assets: float) -> float | None:
    """ROA = net_profit / total_assets x 100. None if total_assets = 0."""
    if total_assets in (0, None) or net_profit is None:
        return None
    return net_profit / total_assets * 100


def ebit(operating_profit: float, depreciation: float) -> float | None:
    """EBIT = operating_profit - depreciation."""
    if operating_profit is None:
        return None
    return operating_profit - (depreciation or 0)


# ---------------------------------------------------------------- Day 9 ----

def debt_to_equity(borrowings: float, equity_capital: float, reserves: float) -> float | None:
    """D/E = borrowings / (equity + reserves). Returns 0 (not None) for debt-free."""
    if borrowings is None or equity_capital is None or reserves is None:
        return None
    if borrowings == 0:
        return 0.0
    denom = equity_capital + reserves
    if denom <= 0:
        return None
    return borrowings / denom


def high_leverage_flag(de_ratio: float | None, broad_sector: str | None) -> bool:
    """True if D/E > 5 and company is NOT in the Financials sector."""
    if de_ratio is None or broad_sector == "Financials":
        return False
    return de_ratio > 5


def interest_coverage(operating_profit: float, other_income: float, interest: float) -> float | None:
    """ICR = (operating_profit + other_income) / interest. None if interest = 0."""
    if operating_profit is None or interest in (0, None):
        return None
    return (operating_profit + (other_income or 0)) / interest


def icr_label(icr: float | None) -> str:
    """'Debt Free' when ICR is None (interest = 0), else numeric label."""
    return "Debt Free" if icr is None else "Interest Bearing"


def icr_risk_flag(icr: float | None) -> bool:
    """True if ICR < 1.5 (risk of not covering interest payments)."""
    if icr is None:
        return False
    return icr < 1.5


def net_debt(borrowings: float, investments: float) -> float | None:
    """Net Debt = borrowings - investments (investments used as liquid-asset proxy)."""
    if borrowings is None:
        return None
    return borrowings - (investments or 0)


def asset_turnover(sales: float, total_assets: float) -> float | None:
    """Asset Turnover = sales / total_assets. None if total_assets = 0."""
    if total_assets in (0, None) or sales is None:
        return None
    return sales / total_assets
