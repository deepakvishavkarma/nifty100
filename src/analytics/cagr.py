"""CAGR growth engine (Sprint 2, Day 10).

Computes N-year CAGR for a metric given a chronologically sorted series of
(year, value) pairs, handling all 6 documented edge cases. Each result is a
(value, flag) tuple - value is None whenever flag is not None.
"""
from __future__ import annotations

FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


def cagr(base_value: float | None, end_value: float | None, n_years: int) -> tuple[float | None, str | None]:
    """Compound Annual Growth Rate with edge-case flags.

    Returns (cagr_pct, flag). flag is None for a normally computed value.
    """
    if base_value is None or end_value is None:
        return None, FLAG_INSUFFICIENT
    if base_value == 0:
        return None, FLAG_ZERO_BASE
    if base_value > 0 and end_value < 0:
        return None, FLAG_DECLINE_TO_LOSS
    if base_value < 0 and end_value > 0:
        return None, FLAG_TURNAROUND
    if base_value < 0 and end_value < 0:
        return None, FLAG_BOTH_NEGATIVE
    # base_value > 0 and end_value >= 0 -> compute normally
    value = ((end_value / base_value) ** (1 / n_years) - 1) * 100
    return value, None


def cagr_over_window(series: list[tuple[str, float | None]], n_years: int) -> tuple[float | None, str | None]:
    """Compute CAGR over an N-period window using a chronologically sorted
    [(year_label, value), ...] series (annual cadence, one row per company-year).

    Uses positional index-back (not calendar subtraction) since some
    companies close their FY in a different month than others.
    """
    if len(series) <= n_years:
        return None, FLAG_INSUFFICIENT
    base_value = series[-1 - n_years][1]
    end_value = series[-1][1]
    return cagr(base_value, end_value, n_years)


def compute_all_windows(series: list[tuple[str, float | None]]) -> dict:
    """Returns a flat dict with 3yr/5yr/10yr CAGR + flag for a metric series."""
    out = {}
    for window in (3, 5, 10):
        value, flag = cagr_over_window(series, window)
        out[f"cagr_{window}yr"] = value
        out[f"cagr_{window}yr_flag"] = flag
    return out
