"""Sprint 1 orchestrator: Excel -> normalise -> validate -> SQLite -> audit."""
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.etl.loader import load_raw, normalise, CORE_FILES, SUPPLEMENTARY_FILES
from src.etl.validator import run_dq_rules

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SUP_DIR = ROOT / "data" / "supporting"
DB_PATH = ROOT / "data" / "nifty100.db"
OUT_DIR = ROOT / "output"

TABLE_MAP = {  # source frame name -> sql table name, plus column renames
    "companies": ("companies", {}),
    "profitandloss": ("profitandloss", {}),
    "balancesheet": ("balancesheet", {}),
    "cashflow": ("cashflow", {}),
    "analysis": ("analysis", {}),
    "documents": ("documents", {"Year": "year", "Annual_Report": "annual_report"}),
    "prosandcons": ("prosandcons", {}),
    "sectors": ("sectors", {}),
    "stock_prices": ("stock_prices", {}),
    "market_cap": ("market_cap", {}),
    "financial_ratios": ("financial_ratios", {}),
    "peer_groups": ("peer_groups", {}),
}

DROP_COLS = {"profitandloss": ["id"], "balancesheet": ["id"],
             "cashflow": ["id"], "analysis": ["id"], "documents": ["id"],
             "prosandcons": ["id"], "sectors": ["id"], "stock_prices": ["id"],
             "market_cap": ["id"], "financial_ratios": ["id"], "peer_groups": ["id"]}


def main():
    t0 = time.time()
    OUT_DIR.mkdir(exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    print("[1/5] Loading 12 source files ...")
    raw = load_raw(RAW_DIR, SUP_DIR)
    for name, df in raw.items():
        print(f"   {name:<18} rows_in={len(df)}")

    print("[2/5] Normalising tickers + years ...")
    clean, rejects = normalise(raw)

    print("[3/5] Running 16 DQ rules ...")
    violations = run_dq_rules(clean)
    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    print(f"   {len(violations)} total findings ({len(critical)} CRITICAL)")

    print("[4/5] Building SQLite database ...")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript((Path(__file__).parent / "schema.sql").read_text())

    # DQ-03 action: reject orphan rows (company_id with no match in companies)
    # before insert; already logged as CRITICAL findings above.
    valid_ids = set(clean["companies"]["id"])
    for name, df in clean.items():
        if name != "companies" and "company_id" in df.columns:
            clean[name] = df[df["company_id"].isin(valid_ids)].reset_index(drop=True)

    audit_rows = []
    for name in CORE_FILES + SUPPLEMENTARY_FILES:
        table, renames = TABLE_MAP[name]
        df = clean[name].copy()
        if name in DROP_COLS:

            df = df.drop(columns=[c for c in DROP_COLS[name] if c in df.columns])
        if renames:
            df = df.rename(columns=renames)
        # Deduplicate on natural key before insert, keep last occurrence (DQ-02 action)
        if {"company_id", "year"}.issubset(df.columns):
            df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
        elif {"company_id", "date"}.issubset(df.columns):
            df = df.drop_duplicates(subset=["company_id", "date"], keep="last")
        if name == "companies":
            df = df.drop_duplicates(subset=["id"], keep="last")

        rows_before = len(raw[name])
        df.to_sql(table, conn, if_exists="append", index=False)
        rows_after = len(df)
        audit_rows.append({
            "table": table, "rows_in": rows_before, "rows_out": rows_after,
            "rejected": rows_before - len(clean[name]), "timestamp": pd.Timestamp.now().isoformat(),
        })

    conn.commit()

    print("[5/5] Verifying FK integrity + writing audit files ...")
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    runtime = time.time() - t0
    for row in audit_rows:
        row["runtime_s"] = round(runtime, 2)
    pd.DataFrame(audit_rows).to_csv(OUT_DIR / "load_audit.csv", index=False)
    pd.DataFrame(violations).to_csv(OUT_DIR / "validation_failures.csv", index=False)

    all_rejects = []
    for name, rdf in rejects.items():
        if len(rdf):
            r = rdf.copy()
            r.insert(0, "source_table", name)
            all_rejects.append(r)
    if all_rejects:
        pd.concat(all_rejects, ignore_index=True).to_csv(OUT_DIR / "parse_failures.csv", index=False)

    print(f"\nDone in {runtime:.2f}s")
    print(f"DB: {DB_PATH}")
    print(f"FK check violations: {len(fk_check)}")
    print(f"CRITICAL DQ findings: {len(critical)}")
    n_companies = conn2 = sqlite3.connect(DB_PATH)
    count = conn2.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    conn2.close()
    print(f"companies row count: {count}")

    # DQ-03 (orphan FK rows) and DQ-02 (duplicates) are auto-remediated by the
    # loader (rows rejected / deduped before insert) - logged for audit but
    # don't block the build. Only an unresolved PK collision (DQ-01) would
    # indicate a broken master file and should halt the load.
    blocking = [v for v in critical if v["rule_id"] == "DQ-01"]
    if blocking:
        print("\n*** BLOCKING DQ-01 FAILURE - duplicate company PK - review validation_failures.csv ***")
        sys.exit(1)
    print(f"({len(critical)} CRITICAL findings auto-remediated: orphan rows rejected / dupes deduped - see validation_failures.csv)")



if __name__ == "__main__":
    main()
