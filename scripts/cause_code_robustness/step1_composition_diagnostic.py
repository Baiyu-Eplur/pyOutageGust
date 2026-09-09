"""Command #12 Step 1: Cause Code composition diagnostic across gust bins.

Read-only against rebuild_v3_full_stage/. Reuses command #9's deterministic
sample-construction functions (via importlib) to get the exact same
117,298-event complete-predictor sample used by commands #9-#11.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

V3_VALIDATION_SCRIPT = project_path('scripts/v3_validation/v3_validation_pipeline.py')
OUT_DIR = result_path('cause_code_robustness')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

WT_GROUPS = {"weather_natural", "technical_asset"}

spec = importlib.util.spec_from_file_location("v3_validation_pipeline", V3_VALIDATION_SCRIPT)
v9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v9)


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


def log_step(msg):
    print(f"[v12-step1] {msg}", flush=True)


def build_base_sample():
    log_step("Reconstructing command #9's base complete-predictor sample...")
    matched, _ = v9.step0_build_sample()
    matched, _ = v9.step1_lad_gapfill(matched)
    sample, _ = v9.step2_build_folds(matched)
    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"Base sample: n={len(sample)}.")
    return sample


def bin_and_report(sample: pd.DataFrame, binning: str, n_bins: int = 10):
    d = sample.copy()
    if binning == "equal_width":
        d["gust_bin"] = pd.cut(d["gust_0h"], bins=n_bins)
    elif binning == "equal_freq":
        d["gust_bin"] = pd.qcut(d["gust_0h"], q=n_bins, duplicates="drop")
    else:
        raise ValueError(binning)

    rows = []
    for bin_label, g in d.groupby("gust_bin", observed=True):
        n = len(g)
        gust_min, gust_max = g["gust_0h"].min(), g["gust_0h"].max()
        cause_counts = g["cause_group_official"].value_counts(normalize=True) * 100
        wt_mask = g["cause_group_official"].isin(WT_GROUPS)
        g_wt = g.loc[wt_mask]
        row = {
            "binning": binning,
            "bin": str(bin_label),
            "gust_min": float(gust_min),
            "gust_max": float(gust_max),
            "n_total": int(n),
            "n_weather_technical": int(len(g_wt)),
            "pct_weather_technical": float(len(g_wt) / n * 100),
            "customers_v2_mean_all6": float(g["customers_v2_event_excl_reinterruptions"].mean()),
            "customers_v2_mean_wt_only": float(g_wt["customers_v2_event_excl_reinterruptions"].mean()) if len(g_wt) else np.nan,
            "duration_B_mean_all6": float(g["duration_B_full_span_hours"].mean()),
            "duration_B_mean_wt_only": float(g_wt["duration_B_full_span_hours"].mean()) if len(g_wt) else np.nan,
        }
        for grp in ["technical_asset", "non_fault_or_unknown", "weather_natural", "third_party", "external_or_customer", "human_error"]:
            row[f"pct_{grp}"] = float(cause_counts.get(grp, 0.0))
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    sample = build_base_sample()

    ew = bin_and_report(sample, "equal_width", 10)
    ef = bin_and_report(sample, "equal_freq", 10)
    ew.to_csv(RAW_DIR / "composition_equal_width_bins.csv", index=False)
    ef.to_csv(RAW_DIR / "composition_equal_freq_bins.csv", index=False)

    print("=== Equal-width bins ===")
    print(ew.to_string(index=False))
    print("=== Equal-frequency bins ===")
    print(ef.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
