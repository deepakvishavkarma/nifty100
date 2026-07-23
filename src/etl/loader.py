"""Excel ingestion layer for the Nifty 100 ETL pipeline.

Core files (7) use header=1 (row 0 is metadata, row 1 is the real header).
Supplementary files (5) use header=0.
"""
from pathlib import Path
import pandas as pd

from .normaliser import normalize_year, normalize_ticker

CORE_FILES = [
    "companies", "profitandloss", "balancesheet", "cashflow",
    "analysis", "documents", "prosandcons",
]
SUPPLEMENTARY_FILES = [
    "sectors", "stock_prices", "market_cap", "financial_ratios", "peer_groups",
]

# Tables keyed by (company_id, year) that need year normalisation
YEAR_TABLES = {
    "profitandloss": "year", "balancesheet": "year", "cashflow": "year",
    "documents": "Year", "market_cap": "year", "financial_ratios": "year",
}

# Every table (except companies, analysis, prosandcons master rows, peer_groups)
# carries a company_id FK that must be normalised
TICKER_TABLES = [
    "profitandloss", "balancesheet", "cashflow", "analysis", "documents",
    "prosandcons", "sectors", "stock_prices", "market_cap",
    "financial_ratios", "peer_groups",
]


def load_raw(raw_dir: Path, supporting_dir: Path) -> dict[str, pd.DataFrame]:
    """Load all 12 source Excel files into a dict of raw DataFrames."""
    frames = {}
    for name in CORE_FILES:
        frames[name] = pd.read_excel(raw_dir / f"{name}.xlsx", header=1)
    for name in SUPPLEMENTARY_FILES:
        frames[name] = pd.read_excel(supporting_dir / f"{name}.xlsx", header=0)
    return frames


def normalise(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply ticker + year normalisation, tracking rejected rows."""
    clean = {}
    rejects = {}

    for name, df in frames.items():
        df = df.copy()
        reject_mask = pd.Series(False, index=df.index)

        if name == "companies":
            df["id"] = df["id"].apply(normalize_ticker)
            reject_mask |= df["id"].isna()
        elif "company_id" in df.columns:
            df["company_id"] = df["company_id"].apply(normalize_ticker)
            reject_mask |= df["company_id"].isna()

        if name in YEAR_TABLES:
            col = YEAR_TABLES[name]
            df[col] = df[col].apply(normalize_year)
            reject_mask |= df[col].isna()

        clean[name] = df[~reject_mask].reset_index(drop=True)
        rejects[name] = df[reject_mask]

    return clean, rejects
