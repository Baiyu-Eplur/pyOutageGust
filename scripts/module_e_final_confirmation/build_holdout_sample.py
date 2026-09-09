"""Command #19 Step 0: build the genuine locked_temporal_test holdout sample
([2023-09-30, 2024-03-31]), applying the identical construction pipeline as
command #16's clean development sample (weather_natural+technical_asset,
weather-matched, complete predictors), just inverting the date filter.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dev_sample_decontamination"))
import clean_sample_builder as csb  # noqa: E402
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = result_path('module_e_final_confirmation')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

LOCKED_START = pd.Timestamp("2023-09-30")
LOCKED_END = pd.Timestamp("2024-03-31")
WT_GROUPS = {"weather_natural", "technical_asset"}


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
    print(f"[v19] {msg}", flush=True)


def build_holdout_wt_samples():
    log_step("Building weather-matched sample (command #9 Step0)...")
    matched, _ = v9.step0_build_sample()

    log_step("Restricting to the locked_temporal_test date block [2023-09-30, 2024-03-31]...")
    matched["_date_check"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    n_before = len(matched)
    matched = matched.loc[
        (matched["_date_check"] >= LOCKED_START) & (matched["_date_check"] <= LOCKED_END)
    ].copy()
    matched = matched.drop(columns=["_date_check"])
    n_after = len(matched)
    log_step(f"Weather-matched sample: {n_before} -> {n_after} in locked window.")

    matched, _ = v9.step1_lad_gapfill(matched)

    # Note: fold construction (GroupKFold) is NOT needed for a single-fit holdout
    # confirmation test (per command #19 Step1/2: "单次拟合，不做内部交叉验证切分").
    # We still run prep_predictors + complete_predictors_mask directly.
    matched["incident_date_utc"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    sample = v9.prep_predictors(matched)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"Holdout complete-predictor sample: n={len(sample)}.")

    min_date, max_date = sample["incident_date_utc"].min(), sample["incident_date_utc"].max()
    assert min_date >= LOCKED_START and max_date <= LOCKED_END, "date range check failed"
    log_step(f"Verified: holdout date range [{min_date}, {max_date}] within locked window.")

    wt_mask = sample["cause_group_official"].isin(WT_GROUPS)
    sample_wt = sample.loc[wt_mask].copy()
    log_step(f"Holdout weather_natural+technical_asset sample: n={len(sample_wt)}.")

    e0_sample = sample_wt.loc[sample_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    r0b_sample = sample_wt.loc[
        sample_wt["duration_B_full_span_hours"].notna() & (sample_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    p99_b = r0b_sample["duration_B_full_span_hours"].quantile(0.99)
    r0b_sample_capped = r0b_sample.loc[r0b_sample["duration_B_full_span_hours"] <= p99_b].copy()
    r0b_sample_capped["log_duration_B_full_span_hours"] = np.log(r0b_sample_capped["duration_B_full_span_hours"].astype(float))
    r0cb_sample = r0b_sample_capped.loc[r0b_sample_capped["customers_v2_event_excl_reinterruptions"].notna()].copy()
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    log_step(f"Holdout E0 n={len(e0_sample)}; holdout R0c n={len(r0cb_sample)} (p99 cap={p99_b:.2f}h).")
    return sample_wt, e0_sample, r0cb_sample, p99_b


def main():
    # ---- holdout sample ----
    sample_wt, e0_sample, r0cb_sample, p99_b = build_holdout_wt_samples()

    # ---- clean dev sample for comparison (command #16) ----
    log_step("Building clean development sample (command #16) for comparison...")
    dev_sample_wt, dev_e0_sample, dev_r0cb_sample, dev_p99_b = csb.build_clean_wt_samples()

    # ---- Cause Code composition comparison ----
    holdout_cause = sample_wt["cause_group_official"].value_counts(normalize=True) * 100
    dev_cause = dev_sample_wt["cause_group_official"].value_counts(normalize=True) * 100

    # ---- n_stages comparison ----
    SRC = project_path('data/external/ukpn_full_stage_dataset_v3.csv')
    stage_counts = pd.read_csv(read_input(SRC), usecols=["Incident Reference", "stage_row_count"], low_memory=False)
    stage_counts = stage_counts.drop_duplicates("Incident Reference").set_index("Incident Reference")["stage_row_count"]

    def n_stages_dist(df):
        s = df["Incident Reference"].map(stage_counts)
        bins = pd.cut(s, bins=[0, 1, 2, 4, 9, np.inf], labels=["1", "2", "3-4", "5-9", "10+"])
        return (bins.value_counts(normalize=True).sort_index() * 100)

    holdout_stages = n_stages_dist(sample_wt)
    dev_stages = n_stages_dist(dev_sample_wt)

    summary = {
        "holdout_wt_n": int(len(sample_wt)),
        "holdout_e0_n": int(len(e0_sample)),
        "holdout_r0cb_n": int(len(r0cb_sample)),
        "holdout_p99_cap_hours": float(p99_b),
        "dev_wt_n": int(len(dev_sample_wt)),
        "dev_e0_n": int(len(dev_e0_sample)),
        "dev_r0cb_n": int(len(dev_r0cb_sample)),
        "dev_p99_cap_hours": float(dev_p99_b),
        "holdout_cause_code_pct": holdout_cause.to_dict(),
        "dev_cause_code_pct": dev_cause.to_dict(),
        "holdout_n_stages_pct": {str(k): float(v) for k, v in holdout_stages.items()},
        "dev_n_stages_pct": {str(k): float(v) for k, v in dev_stages.items()},
    }
    (RAW_DIR / "step0_holdout_vs_dev_summary.json").write_text(js(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
