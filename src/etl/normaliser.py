"""Field normalisation utilities for the Nifty 100 ETL pipeline.

Handles two recurring dirty-data problems in the source files:
  1. Inconsistent financial-year labels ("Mar-23", "FY24", "2023", "Dec-22" ...)
  2. Inconsistent company tickers (whitespace, casing)
"""
import re

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "march": "03", "apr": "04",
    "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
    "aug": "08", "sep": "09", "sept": "09", "oct": "10", "nov": "11", "dec": "12",
}

YEAR_RE = re.compile(r"^\d{4}-\d{2}$")


def normalize_year(raw) -> str | None:
    """Convert a raw financial-year label into standard 'YYYY-MM' form.

    Examples
    --------
    'Mar-23'    -> '2023-03'
    'Mar 23'    -> '2023-03'
    'March-2023'-> '2023-03'
    'FY24'      -> '2024-03'
    '2023'      -> '2023-03'   (bare year assumed March FY close)
    'Dec-22'    -> '2022-12'
    '2023-03'   -> '2023-03'   (already normalised, pass through)
    'garbage'   -> None        (unparseable -> caller rejects row)
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None

    # Already normalised
    if YEAR_RE.match(s):
        return s

    # Bare 4-digit year -> assume March FY close
    if re.fullmatch(r"\d{4}", s):
        return f"{s}-03"

    # FY prefix, e.g. FY24, FY2024
    m = re.fullmatch(r"FY\s*(\d{2,4})", s, flags=re.IGNORECASE)
    if m:
        yr = m.group(1)
        yr = f"20{yr}" if len(yr) == 2 else yr
        return f"{yr}-03"

    # Month-Year or Month Year (hyphen or space separated), 2 or 4 digit year
    m = re.fullmatch(
        r"([A-Za-z]+)[\s\-]+(\d{2,4})", s
    )
    if m:
        month_raw, yr = m.group(1).lower(), m.group(2)
        month = _MONTH_MAP.get(month_raw)
        if month is None:
            return None
        yr = f"20{yr}" if len(yr) == 2 else yr
        return f"{yr}-{month}"

    return None  # PARSE_ERROR


def normalize_ticker(raw) -> str | None:
    """Strip whitespace and upper-case a company ticker.

    Preserves valid NSE ticker characters such as '-' (BAJAJ-AUTO) and
    '&' (M&M). Returns None for empty/missing values so the caller can
    reject the row (no FK match possible).
    """
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s or s in {"MISSING", "NAN", "NONE"}:
        return None
    if not (2 <= len(s) <= 12):
        return None
    return s
