"""6 preset screeners (Sprint 3, Day 16)."""
from __future__ import annotations
import pandas as pd

from src.screener.engine import apply_custom_filter


def run_preset(df: pd.DataFrame, preset_key: str, config: dict) -> pd.DataFrame:
    preset = config["presets"][preset_key]
    result = apply_custom_filter(df, preset["filters"], config)
    rank_col = preset["rank_by"]
    result = result.sort_values(rank_col, ascending=not preset["rank_desc"])
    return result


def run_all_presets(df: pd.DataFrame, config: dict) -> dict[str, pd.DataFrame]:
    return {key: run_preset(df, key, config) for key in config["presets"]}
