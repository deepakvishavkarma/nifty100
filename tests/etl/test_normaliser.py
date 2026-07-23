import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.etl.normaliser import normalize_year, normalize_ticker

# ---- normalize_year: 20 cases ----

def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"

def test_year_mar_space23():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_march_full():
    assert normalize_year("March-2023") == "2023-03"

def test_year_bare_int():
    assert normalize_year(2023) == "2023-03"

def test_year_bare_str():
    assert normalize_year("2023") == "2023-03"

def test_year_fy_short():
    assert normalize_year("FY23") == "2023-03"

def test_year_fy_long():
    assert normalize_year("FY2024") == "2024-03"

def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"

def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"

def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"

def test_year_lowercase_month():
    assert normalize_year("mar-23") == "2023-03"

def test_year_garbage():
    assert normalize_year("garbage") is None

def test_year_none():
    assert normalize_year(None) is None

def test_year_empty():
    assert normalize_year("") is None

def test_year_nan_float():
    import math
    assert normalize_year(float("nan")) is None

def test_year_sept_abbrev():
    assert normalize_year("Sept-21") == "2021-09"

def test_year_july_full():
    assert normalize_year("July-2020") == "2020-07"

def test_year_two_digit_low():
    assert normalize_year("Jan-05") == "2005-01"

def test_year_whitespace_padded():
    assert normalize_year("  Mar-23  ") == "2023-03"

def test_year_invalid_month():
    assert normalize_year("Xyz-23") is None


# ---- normalize_ticker: 15 cases ----

def test_ticker_strip():
    assert normalize_ticker(" TCS ") == "TCS"

def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"

def test_ticker_mixed_case():
    assert normalize_ticker("TcS") == "TCS"

def test_ticker_hyphen_preserved():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"

def test_ticker_ampersand_preserved():
    assert normalize_ticker("m&m") == "M&M"

def test_ticker_missing_literal():
    assert normalize_ticker("MISSING") is None

def test_ticker_none():
    assert normalize_ticker(None) is None

def test_ticker_empty():
    assert normalize_ticker("") is None

def test_ticker_whitespace_only():
    assert normalize_ticker("   ") is None

def test_ticker_too_short():
    assert normalize_ticker("A") is None

def test_ticker_too_long():
    assert normalize_ticker("A" * 13) is None

def test_ticker_min_length_ok():
    assert normalize_ticker("AB") == "AB"

def test_ticker_max_length_ok():
    assert normalize_ticker("A" * 12) == "A" * 12

def test_ticker_leading_trailing_tabs():
    assert normalize_ticker("\tTCS\n") == "TCS"

def test_ticker_nan_string():
    assert normalize_ticker("nan") is None
