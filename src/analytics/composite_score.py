"""Composite Quality Score (Sprint 2, Day 12).

0.30 x ROE_score + 0.25 x FCF_score + 0.25 x ROCE_score + 0.20 x DE_score
Each sub-score is normalised 0-100 using P10/P90 winsorisation across the
full company universe for the latest year, per the KPI reference (Section 13).
"""
from __future__ import annotations


def winsorised_score(value: float | None, p10: float, p90: float, invert: bool = False) -> float | None:
    """Scale a raw metric to 0-100 using P10/P90 winsorisation.

    invert=True for metrics where lower is better (e.g. D/E) so the score
    still runs 0 (worst) -> 100 (best).
    """
    if value is None:
        return None
    if p90 == p10:
        return 50.0
    clipped = max(p10, min(p90, value))
    score = (clipped - p10) / (p90 - p10) * 100
    return 100 - score if invert else score


def composite_quality_score(roe_score: float | None, fcf_score: float | None,
                             roce_score: float | None, de_score: float | None) -> float | None:
    parts = [(roe_score, 0.30), (fcf_score, 0.25), (roce_score, 0.25), (de_score, 0.20)]
    if any(p[0] is None for p in parts):
        # Re-weight across available components rather than failing outright
        available = [(v, w) for v, w in parts if v is not None]
        if not available:
            return None
        total_w = sum(w for _, w in available)
        return sum(v * w for v, w in available) / total_w
    return sum(v * w for v, w in parts)
