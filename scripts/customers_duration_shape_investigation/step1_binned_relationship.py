"""Command #17 Step 1: raw decile-binned customers_v2 vs duration_B relationship
(no quadratic functional-form assumption), on command #16's clean weather_natural+
technical_asset sample. Also builds naive/legacy-style customers+duration (same
construction as command #10) on the SAME set of incidents for comparison.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(project_path('scripts/dev_sample_decontamination')))
from clean_sample_builder import build_clean_wt_samples  # noqa: E402

SRC = external_path('rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')
OUT_DIR = result_path('customers_duration_shape_investigation')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"


def log_step(msg):
    print(f"[v17-step1] {msg}", flush=True)


def decile_bin_report(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> pd.DataFrame:
    d = df[[x_col, y_col]].dropna().copy()
    d["decile"] = pd.qcut(d[x_col], q=10, duplicates="drop")
    rows = []
    for decile, g in d.groupby("decile", observed=True):
        rows.append({
            "label": label, "decile": str(decile), "n": len(g),
            "x_min": float(g[x_col].min()), "x_max": float(g[x_col].max()), "x_median": float(g[x_col].median()),
            "y_mean": float(g[y_col].mean()), "y_median": float(g[y_col].median()), "y_std": float(g[y_col].std(ddof=1)),
        })
    return pd.DataFrame(rows)


def build_naive_variables(event_ids: pd.Index) -> pd.DataFrame:
    log_step("Building naive customers/duration via legacy filter.py dedup logic (same as command #10)...")
    stage = pd.read_csv(
        read_input(SRC),
        usecols=[INCIDENT_COL, "Start Date and Time", "Number of Customers Restored", "stage_duration_hours"],
        low_memory=False,
    )
    stage["_sort_time"] = pd.to_datetime(stage["Start Date and Time"], errors="coerce", utc=True)
    stage = stage.sort_values([INCIDENT_COL, "_sort_time"], kind="stable")
    earliest = stage.drop_duplicates(subset=[INCIDENT_COL], keep="first").copy()
    earliest["customers_naive"] = pd.to_numeric(
        earliest["Number of Customers Restored"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    earliest["duration_naive"] = earliest["stage_duration_hours"]
    naive = earliest.set_index(INCIDENT_COL)[["customers_naive", "duration_naive"]]
    naive = naive.reindex(event_ids)
    return naive


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_clean_wt_samples()

    log_step(f"R0c'_B_clean sample (customers_v2 vs duration_B): n={len(r0cb_sample)}")
    r0cb_sample = r0cb_sample.copy()
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))
    r0cb_sample["log_duration_B"] = np.log(r0cb_sample["duration_B_full_span_hours"].astype(float))

    # ---------------- new-definition binning (raw scale and log scale) ----------------
    new_raw = decile_bin_report(r0cb_sample, "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
                                 "customers_v2_vs_duration_B_raw_scale")
    new_log = decile_bin_report(r0cb_sample, "log1p_customers_v2", "log_duration_B",
                                 "customers_v2_vs_duration_B_log_scale")
    new_raw.to_csv(RAW_DIR / "01_new_definition_raw_scale_bins.csv", index=False)
    new_log.to_csv(RAW_DIR / "01_new_definition_log_scale_bins.csv", index=False)
    print("=== New definition, raw scale ===")
    print(new_raw.to_string(index=False))
    print("=== New definition, log scale ===")
    print(new_log.to_string(index=False))

    # ---------------- naive/legacy definition binning, SAME incident set ----------------
    naive = build_naive_variables(r0cb_sample[INCIDENT_COL].unique())
    naive_joined = r0cb_sample.set_index(INCIDENT_COL, drop=False).join(naive, how="left")
    naive_valid = naive_joined.loc[
        naive_joined["customers_naive"].notna() & naive_joined["duration_naive"].notna()
        & (naive_joined["duration_naive"] > 0)
    ].copy()
    log_step(f"Naive-definition valid subset (same incidents, naive customers/duration both non-missing/positive): "
              f"n={len(naive_valid)} out of {len(r0cb_sample)}")

    naive_raw = decile_bin_report(naive_valid, "customers_naive", "duration_naive", "naive_customers_vs_naive_duration_raw_scale")
    naive_valid["log1p_customers_naive"] = np.log1p(naive_valid["customers_naive"])
    naive_valid["log_duration_naive"] = np.log(naive_valid["duration_naive"])
    naive_log = decile_bin_report(naive_valid, "log1p_customers_naive", "log_duration_naive", "naive_customers_vs_naive_duration_log_scale")
    naive_raw.to_csv(RAW_DIR / "01_naive_definition_raw_scale_bins.csv", index=False)
    naive_log.to_csv(RAW_DIR / "01_naive_definition_log_scale_bins.csv", index=False)
    print("=== Naive/legacy definition, raw scale ===")
    print(naive_raw.to_string(index=False))
    print("=== Naive/legacy definition, log scale ===")
    print(naive_log.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
