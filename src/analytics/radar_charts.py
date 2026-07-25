"""Radar / polar chart generator (Sprint 3, Day 19).

One PNG per company: 8-axis radar showing the company's own values as a
filled polygon vs. its peer group average as a dashed overlay. Companies
with no peer group get a single-metric standalone chart vs the Nifty 100
average instead of raising an error.
"""
from __future__ import annotations
import sys
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.screener.engine import load_universe
from src.screener.composite import compute_sector_relative_score
from src.analytics.composite_score import winsorised_score

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "nifty100.db"
OUT_DIR = ROOT / "reports" / "radar_charts"

RADAR_AXES = [
    ("return_on_equity_pct", "ROE"),
    ("return_on_capital_employed_pct", "ROCE"),
    ("net_profit_margin_pct", "NPM"),
    ("debt_to_equity", "D/E"),          # inverted for scoring, lower is better
    ("free_cash_flow_cr", "FCF"),
    ("pat_cagr_5yr", "PAT CAGR 5yr"),
    ("revenue_cagr_5yr", "Rev CAGR 5yr"),
    ("composite_quality_score", "Composite"),
]
INVERT = {"debt_to_equity"}


def _axis_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Scale each of the 8 radar axes to 0-100 across the full universe so
    very different-unit metrics (D/E vs FCF in Crore) plot on one radar."""
    scores = pd.DataFrame(index=df.index)
    for col, _ in RADAR_AXES:
        vals = df[col].dropna()
        if len(vals) < 3:
            scores[col] = 50.0
            continue
        p10, p90 = vals.quantile(0.10), vals.quantile(0.90)
        scores[col] = df[col].apply(lambda v: winsorised_score(v, p10, p90, invert=col in INVERT))
        scores[col] = scores[col].fillna(0)
    return scores


def _draw_radar(ax, company_vals, peer_avg_vals, labels, title):
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    cv = company_vals + company_vals[:1]
    pv = peer_avg_vals + peer_avg_vals[:1]

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6)

    ax.plot(angles, cv, color="#1F4E78", linewidth=2, label="Company")
    ax.fill(angles, cv, color="#1F4E78", alpha=0.25)
    ax.plot(angles, pv, color="#C00000", linewidth=1.5, linestyle="--", label="Peer Avg")

    ax.set_title(title, fontsize=11, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=7)


def generate_all_radars():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    universe = load_universe(conn)
    universe["composite_quality_score"] = compute_sector_relative_score(universe)
    peer_groups = pd.read_sql("SELECT peer_group_name, company_id FROM peer_groups", conn)
    companies = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    conn.close()

    scores = _axis_scores(universe)
    scores["company_id"] = universe["company_id"].values
    labels = [lbl for _, lbl in RADAR_AXES]
    cols = [c for c, _ in RADAR_AXES]

    nifty_avg = scores[cols].mean().tolist()

    assigned_ids = set(peer_groups["company_id"])
    written = 0

    for _, row in universe.iterrows():
        cid = row["company_id"]
        srow = scores[scores["company_id"] == cid].iloc[0]
        company_vals = [float(srow[c]) for c in cols]

        group_members = peer_groups[peer_groups["company_id"] == cid]["peer_group_name"]
        if len(group_members) and cid in assigned_ids:
            group_name = group_members.iloc[0]
            peer_ids = peer_groups[peer_groups["peer_group_name"] == group_name]["company_id"]
            peer_scores = scores[scores["company_id"].isin(peer_ids)]
            peer_avg = [float(peer_scores[c].mean()) for c in cols]
            title = f"{cid} vs {group_name} peer avg"
        else:
            peer_avg = nifty_avg
            title = f"{cid} vs Nifty 100 avg (no peer group assigned)"

        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot(111, projection="polar")
        _draw_radar(ax, company_vals, peer_avg, labels, title)
        fig.tight_layout()
        fig.savefig(OUT_DIR / f"{cid}_radar.png", dpi=110)
        plt.close(fig)
        written += 1

    print(f"Radar charts written: {written} -> {OUT_DIR}")


if __name__ == "__main__":
    generate_all_radars()
