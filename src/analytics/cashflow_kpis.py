"""Cash flow quality KPIs + capital allocation classifier (Sprint 2, Day 11)."""
from __future__ import annotations
import statistics


def free_cash_flow(operating_activity: float, investing_activity: float) -> float | None:
    """FCF = CFO + CFI. Negative allowed."""
    if operating_activity is None or investing_activity is None:
        return None
    return operating_activity + investing_activity


def cfo_quality_score(cfo_series: list[float], pat_series: list[float]) -> float | None:
    """CFO/PAT ratio averaged over up to 5 most recent years. None if PAT sum is 0
    or the series are empty/misaligned."""
    pairs = [(c, p) for c, p in zip(cfo_series[-5:], pat_series[-5:])
             if c is not None and p is not None and p != 0]
    if not pairs:
        return None
    ratios = [c / p for c, p in pairs]
    return statistics.mean(ratios)


def cfo_quality_label(score: float | None) -> str | None:
    if score is None:
        return None
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_intensity(investing_activity: float, sales: float) -> float | None:
    """CapEx Intensity = abs(investing_activity) / sales x 100."""
    if sales in (0, None) or investing_activity is None:
        return None
    return abs(investing_activity) / sales * 100


def capex_category(intensity_pct: float | None) -> str | None:
    if intensity_pct is None:
        return None
    if intensity_pct < 3:
        return "Asset Light"
    if intensity_pct <= 8:
        return "Moderate"
    return "Capital Intensive"


def fcf_conversion_rate(fcf: float, operating_profit: float) -> float | None:
    """FCF Conversion = FCF / operating_profit x 100. None if operating_profit = 0."""
    if operating_profit in (0, None) or fcf is None:
        return None
    return fcf / operating_profit * 100


# ------------------------------------------------ Capital allocation (8 patterns) ---

_PATTERN_LABELS = {
    (1, -1, -1): "Reinvestor",
    (1, -1, 1): "Cash Accumulator",
    (1, 1, -1): "Liquidating Assets",
    (1, 1, 1): "Cash Accumulator",
    (-1, 1, 1): "Distress Signal",
    (-1, -1, 1): "Growth Funded by Debt",
    (-1, -1, -1): "Pre-Revenue",
    (-1, 1, -1): "Mixed",
}


def _sign(value: float | None) -> int:
    if value is None or value == 0:
        return 1  # treat exact zero as non-negative for classification purposes
    return 1 if value > 0 else -1


def capital_allocation_pattern(cfo: float | None, cfi: float | None, cff: float | None,
                                cfo_pat_ratio: float | None = None) -> tuple[int, int, int, str]:
    """Classify capital allocation into one of 8 sign-pattern labels.

    (+,-,-) further splits into 'Reinvestor' vs 'Shareholder Returns' using the
    CFO/PAT quality ratio as the day-11 spec requires (high CFO/PAT among the
    (+,-,-) pattern implies mature dividend/buyback behaviour rather than pure
    reinvestment).
    """
    cfo_s, cfi_s, cff_s = _sign(cfo), _sign(cfi), _sign(cff)
    label = _PATTERN_LABELS.get((cfo_s, cfi_s, cff_s), "Mixed")
    if (cfo_s, cfi_s, cff_s) == (1, -1, -1) and cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
        label = "Shareholder Returns"
    return cfo_s, cfi_s, cff_s, label
