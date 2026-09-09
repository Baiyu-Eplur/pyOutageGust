"""Shared clean-sample builder for command #16: reuses command #9's deterministic
functions unchanged, but filters out the locked_temporal_test date block
(incident_date_utc >= 2023-09-30) BEFORE LAD gap-fill and fold construction, so
the rebuilt 5-fold GroupKFold never sees a locked-window date.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

V3_VALIDATION_SCRIPT = Path(__file__).resolve().parents[1] / "v3_validation" / "v3_validation_pipeline.py"
LOCKED_START = pd.Timestamp("2023-09-30")
WT_GROUPS = {"weather_natural", "technical_asset"}

spec = importlib.util.spec_from_file_location("v3_validation_pipeline", V3_VALIDATION_SCRIPT)
v9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v9)


def log_step(msg):
    print(f"[v16-clean] {msg}", flush=True)


def build_clean_wt_samples():
    log_step("Building weather-matched sample (command #9 Step0)...")
    matched, _ = v9.step0_build_sample()

    log_step("Excluding locked_temporal_test date block (>= 2023-09-30) BEFORE fold construction...")
    matched["_date_check"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    n_before = len(matched)
    matched = matched.loc[matched["_date_check"] < LOCKED_START].copy()
    matched = matched.drop(columns=["_date_check"])
    n_after = len(matched)
    log_step(f"Weather-matched sample: {n_before} -> {n_after} after locked-window exclusion "
              f"({n_before - n_after} removed, {(n_before - n_after) / n_before * 100:.2f}%).")

    matched, _ = v9.step1_lad_gapfill(matched)
    sample, fold_check = v9.step2_build_folds(matched)
    assert fold_check["n_dates_crossing_folds"] == 0

    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"Clean complete-predictor sample: n={len(sample)}.")

    # verify zero overlap with locked window
    max_date = pd.to_datetime(sample["incident_date_utc"]).max()
    assert max_date < LOCKED_START, f"Contamination check failed: max date {max_date} >= {LOCKED_START}"
    log_step(f"Verified: max date in clean sample = {max_date} (< {LOCKED_START}).")

    wt_mask = sample["cause_group_official"].isin(WT_GROUPS)
    sample_wt = sample.loc[wt_mask].copy()
    log_step(f"Clean weather_natural+technical_asset sample: n={len(sample_wt)}.")

    e0_sample = sample_wt.loc[sample_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    r0b_sample = sample_wt.loc[
        sample_wt["duration_B_full_span_hours"].notna() & (sample_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    p99_b = r0b_sample["duration_B_full_span_hours"].quantile(0.99)
    r0b_sample = r0b_sample.loc[r0b_sample["duration_B_full_span_hours"] <= p99_b].copy()
    r0b_sample["log_duration_B_full_span_hours"] = np.log(r0b_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample = r0b_sample.loc[r0b_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    log_step(f"Clean E0' n={len(e0_sample)}; clean R0c'_B n={len(r0cb_sample)} (p99 cap={p99_b:.2f}h).")
    return sample_wt, e0_sample, r0cb_sample, p99_b
