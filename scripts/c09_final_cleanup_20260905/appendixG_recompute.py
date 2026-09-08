"""Appendix G recomputation on C01-corrected data:
1. weather_natural share of the weather_natural+technical_asset sample, by
   gust decile (command #26's Table G1, originally 6.89%-56.10%).
2. Share of events below the (corrected) turning point 10.81 m/s, in the
   full WT sample vs the weather_natural subsample (command #26 Step3,
   originally 63.70% vs 36.83%).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c09_final_cleanup_20260905\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

TURNING_POINT_MS = 10.80715790164296  # command #45 final corrected E0 turning point


def log_step(msg):
    print(f"[AppendixG] {msg}", flush=True)


def main():
    combined_wt, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()
    log_step(f"Combined WT sample (corrected): n={len(combined_wt)}")

    # ---------------- Table G1: weather_natural share by gust decile ----------------
    df = combined_wt.copy()
    df["gust_decile"] = pd.qcut(df["gust_0h"], 10, labels=False, duplicates="drop")
    decile_stats = df.groupby("gust_decile").apply(
        lambda g: pd.Series({
            "n": len(g),
            "gust_min": g["gust_0h"].min(), "gust_max": g["gust_0h"].max(),
            "pct_weather_natural": (g["cause_group_official"] == "weather_natural").mean() * 100,
        }), include_groups=False
    )
    decile_stats.to_csv(RAW_DIR / "appendixG_table_G1_corrected.csv")
    log_step("Table G1 (corrected):\n" + decile_stats.to_string())

    first_decile_pct = decile_stats["pct_weather_natural"].iloc[0]
    last_decile_pct = decile_stats["pct_weather_natural"].iloc[-1]
    is_monotonic = decile_stats["pct_weather_natural"].is_monotonic_increasing
    log_step(f"First decile: {first_decile_pct:.2f}%, last decile: {last_decile_pct:.2f}%, "
              f"monotonic increasing across all deciles: {is_monotonic}")

    # ---------------- Step3: share below turning point ----------------
    combined_e0_local = combined_wt.loc[combined_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    wn_e0 = combined_e0_local.loc[combined_e0_local["cause_group_official"] == "weather_natural"].copy()

    pct_below_full = (combined_e0_local["gust_0h"] < TURNING_POINT_MS).mean() * 100
    pct_below_wn = (wn_e0["gust_0h"] < TURNING_POINT_MS).mean() * 100
    log_step(f"Share of events with gust < {TURNING_POINT_MS:.2f} m/s: "
              f"full WT E0 sample = {pct_below_full:.2f}% (n={len(combined_e0_local)}), "
              f"weather_natural subsample = {pct_below_wn:.2f}% (n={len(wn_e0)})")

    result = {
        "table_G1_first_decile_pct_weather_natural": float(first_decile_pct),
        "table_G1_last_decile_pct_weather_natural": float(last_decile_pct),
        "table_G1_monotonic_increasing": bool(is_monotonic),
        "table_G1_original_command26": {"first_decile": 6.89, "last_decile": 56.10},
        "turning_point_ms_used": TURNING_POINT_MS,
        "pct_below_turning_point_full_WT_E0": float(pct_below_full),
        "pct_below_turning_point_weather_natural": float(pct_below_wn),
        "original_command26_step3": {"full_sample": 63.70, "weather_natural": 36.83},
    }
    (RAW_DIR / "appendixG_summary_corrected.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved appendixG_summary_corrected.json")


if __name__ == "__main__":
    main()
