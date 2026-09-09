"""Command #26: pure descriptive diagnostic -- does Cause Code classification
(weather_natural vs technical_asset) itself correlate with gust level, and does
this create a low-gust anchor-point shortage specifically within the
weather_natural subsample? No model fitting.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from combined_sample_builder import build_combined_samples  # noqa: E402

OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

E0_TURNING_POINT_MS = 10.69  # command #21's main-spec E0 turning point


def log_step(msg):
    print(f"[v26] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def main():
    _, combined_e0, _, _ = build_combined_samples()
    log_step(f"Main-spec E0 sample: n={len(combined_e0)}")

    wn = combined_e0[combined_e0["cause_group_official"] == "weather_natural"].copy()
    ta = combined_e0[combined_e0["cause_group_official"] == "technical_asset"].copy()
    log_step(f"weather_natural n={len(wn)}, technical_asset n={len(ta)}")

    # ---------------- Step 1: quantile distributions ----------------
    quantiles = [0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.0]
    qlabels = ["min", "p1", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "max"]

    def qdist(s):
        return {lab: float(s.quantile(q)) for lab, q in zip(qlabels, quantiles)}

    step1 = {
        "all": qdist(combined_e0["gust_0h"]),
        "weather_natural": qdist(wn["gust_0h"]),
        "technical_asset": qdist(ta["gust_0h"]),
    }
    (RAW_DIR / "step21_gust_distributions.json").write_text(js(step1), encoding="utf-8")
    log_step("Step1 quantile distributions computed.")

    # ---------------- Step 2: weather_natural share by gust decile ----------------
    d = combined_e0.copy()
    d["gust_decile"] = pd.qcut(d["gust_0h"], q=10, duplicates="drop")
    rows = []
    for decile, g in d.groupby("gust_decile", observed=True):
        n = len(g)
        n_wn = (g["cause_group_official"] == "weather_natural").sum()
        rows.append({
            "decile": str(decile), "n": n, "n_weather_natural": int(n_wn),
            "pct_weather_natural": float(n_wn / n * 100),
            "gust_min": float(g["gust_0h"].min()), "gust_max": float(g["gust_0h"].max()),
        })
    step2_df = pd.DataFrame(rows)
    step2_df.to_csv(RAW_DIR / "step22_wn_share_by_decile.csv", index=False)
    print(step2_df.to_string(index=False))

    # monotonicity check
    shares = step2_df["pct_weather_natural"].values
    is_monotonic = bool(np.all(np.diff(shares) >= -1e-9))
    n_increases = int(np.sum(np.diff(shares) > 0))
    n_total_steps = len(shares) - 1

    # ---------------- Step 3: anchor-point density below turning point ----------------
    below_all = combined_e0[combined_e0["gust_0h"] < E0_TURNING_POINT_MS]
    below_wn = wn[wn["gust_0h"] < E0_TURNING_POINT_MS]

    step3 = {
        "turning_point_ms": E0_TURNING_POINT_MS,
        "n_below_turning_all": int(len(below_all)),
        "pct_below_turning_all": float(len(below_all) / len(combined_e0) * 100),
        "n_below_turning_wn": int(len(below_wn)),
        "pct_below_turning_wn": float(len(below_wn) / len(wn) * 100),
        "n_wn_total": int(len(wn)),
        "n_all_total": int(len(combined_e0)),
    }
    (RAW_DIR / "step23_anchor_density.json").write_text(js(step3), encoding="utf-8")

    summary = {
        "step1_distributions": step1,
        "step2_monotonic": is_monotonic,
        "step2_n_increasing_steps_of_9": f"{n_increases}/{n_total_steps}",
        "step2_first_decile_pct_wn": float(shares[0]),
        "step2_last_decile_pct_wn": float(shares[-1]),
        "step3": step3,
    }
    (RAW_DIR / "step26_full_summary.json").write_text(js(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    log_step("Done.")


if __name__ == "__main__":
    main()
