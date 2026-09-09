"""Reusable C01-corrected final combined sample builder. Encapsulates the same
monkey-patch approach used in command #44 (patch v9.step0_build_sample() to
return the corrected event-level frame -- gust_0h/pressure_msl_0h/temperature_0h/
precipitation_24h_sum/incident_date_utc corrected for the 12,886 events whose
true earliest-start representative row differs from the old file-order row;
617 unrecoverable-weather events explicitly nulled, not backfilled with stale
values), so every downstream script in this command (tables, Figures 1/2/4/5/
6/7/8/9/10/D1) can import ONE building block and get identical, C01-corrected
data. All other pipeline logic (LAD gap-fill, GroupKFold, prep_predictors,
complete-predictor mask, dev/holdout split, weather_natural+technical_asset
filter, design_train_valid standardization, LAD-clustered SE) is untouched.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(r"D:\Pyprogramme\pyOutageGust\data\external\ukpn_full_stage_dataset_v3.csv")
C01_RAW_DIR = Path(r"D:\Pyprogramme\pyOutageGust\results\c01_repair_20260905\raw")

INCIDENT_COL = "Incident Reference"
V9_USECOLS = [
    INCIDENT_COL, "weather_status_v3", "cause_group_official",
    "gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h",
    "LAD21CD", "population", "income_deprivation_rate", "deprivation_gap_pct",
    "morans_i", "rural_urban_classification",
    "customers_v2_event_excl_reinterruptions",
    "duration_A_customer_weighted_hours", "duration_B_full_span_hours",
    "incident_date_utc", "lat", "lon",
]

_cached_matched = None


def log_step(msg):
    print(f"[corrected-sample] {msg}", flush=True)


def _build_corrected_matched():
    global _cached_matched
    if _cached_matched is not None:
        return _cached_matched.copy()

    log_step("Loading OLD-style event table and applying C01 corrections (Step1+Step2 outputs)...")
    df = pd.read_csv(SRC, usecols=V9_USECOLS, low_memory=False)
    old_event = df.drop_duplicates(INCIDENT_COL).copy().set_index(INCIDENT_COL, drop=False)

    comp = pd.read_csv(C01_RAW_DIR / "step1_representative_row_comparison_full.csv")
    comp["new_start_utc"] = pd.to_datetime(comp["new_start_utc"], utc=True)
    comp["new_incident_date_utc"] = comp["new_start_utc"].dt.date.astype(str)
    reext = pd.read_csv(C01_RAW_DIR / "step2_weather_reextraction_full.csv").set_index("Incident Reference")

    changed_ids = comp.loc[comp["representative_row_changed"], "Incident Reference"]
    comp_indexed = comp.set_index("Incident Reference")
    changed_in_corrected = pd.Index(changed_ids)[pd.Index(changed_ids).isin(old_event.index)]

    corrected = old_event.copy()
    date_updates = comp_indexed.loc[changed_in_corrected, "new_incident_date_utc"]
    corrected.loc[date_updates.index, "incident_date_utc"] = date_updates.values

    reext_changed = reext.reindex(changed_in_corrected)
    recovered_mask = reext_changed["cache_status"].astype(str).str.startswith("recovered")
    recovered_ids = reext_changed.index[recovered_mask.fillna(False)]
    nulled_ids = reext_changed.index[~recovered_mask.fillna(False)]
    weather_cols = ["gust_0h", "pressure_msl_0h", "temperature_0h", "precipitation_24h_sum"]
    recomputed_cols = ["recomputed_gust_0h", "recomputed_pressure_msl_0h",
                        "recomputed_temperature_0h", "recomputed_precip_24h_sum"]
    if len(recovered_ids):
        corrected.loc[recovered_ids, weather_cols] = reext_changed.loc[recovered_ids, recomputed_cols].to_numpy()
    if len(nulled_ids):
        corrected.loc[nulled_ids, weather_cols] = np.nan

    corrected = corrected.reset_index(drop=True)
    matched = corrected[corrected["weather_status_v3"] == "matched"].copy()
    log_step(f"Corrected matched sample: {len(matched)} events "
              f"({len(recovered_ids)} weather-corrected, {len(nulled_ids)} weather-nulled).")
    _cached_matched = matched
    return matched.copy()


def _patch_v9():
    """Patch v9.step0_build_sample everywhere it matters and return the patched
    clean_sample_builder / build_holdout_sample module objects."""
    matched = _build_corrected_matched()
    step0_summary = {"n_weather_matched_events": int(len(matched))}

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v3_validation"))
    import v3_validation_pipeline as v9  # noqa: E402
    v9.step0_build_sample = lambda: (matched.copy(), step0_summary)

    spec = importlib.util.spec_from_file_location(
        "clean_sample_builder",
        str(Path(__file__).resolve().parents[1] / "dev_sample_decontamination" / "clean_sample_builder.py"))
    clean_sample_builder = importlib.util.module_from_spec(spec)
    sys.modules["clean_sample_builder"] = clean_sample_builder
    spec.loader.exec_module(clean_sample_builder)
    clean_sample_builder.v9.step0_build_sample = v9.step0_build_sample

    spec2 = importlib.util.spec_from_file_location(
        "build_holdout_sample",
        str(Path(__file__).resolve().parents[1] / "module_e_final_confirmation" / "build_holdout_sample.py"))
    build_holdout_sample = importlib.util.module_from_spec(spec2)
    sys.modules["build_holdout_sample"] = build_holdout_sample
    spec2.loader.exec_module(build_holdout_sample)
    build_holdout_sample.v9.step0_build_sample = v9.step0_build_sample

    return v9, clean_sample_builder, build_holdout_sample


def build_corrected_combined_samples():
    """Drop-in, C01-corrected replacement for
    final_combined_analysis/combined_sample_builder.build_combined_samples().
    Returns (combined_wt, combined_e0, combined_r0cb, verification)."""
    v9, clean_sample_builder, build_holdout_sample = _patch_v9()

    dev_wt, dev_e0, dev_r0cb, dev_p99 = clean_sample_builder.build_clean_wt_samples()
    holdout_wt, holdout_e0, holdout_r0cb, holdout_p99 = build_holdout_sample.build_holdout_wt_samples()

    combined_wt = pd.concat([dev_wt, holdout_wt], ignore_index=True)
    combined_e0 = pd.concat([dev_e0, holdout_e0], ignore_index=True)
    combined_r0cb_base = pd.concat([
        dev_wt.loc[dev_wt["duration_B_full_span_hours"].notna() & (dev_wt["duration_B_full_span_hours"] > 0)],
        holdout_wt.loc[holdout_wt["duration_B_full_span_hours"].notna() & (holdout_wt["duration_B_full_span_hours"] > 0)],
    ], ignore_index=True)
    combined_p99 = combined_r0cb_base["duration_B_full_span_hours"].quantile(0.99)
    combined_r0cb = combined_r0cb_base.loc[combined_r0cb_base["duration_B_full_span_hours"] <= combined_p99].copy()
    combined_r0cb = combined_r0cb.loc[combined_r0cb["customers_v2_event_excl_reinterruptions"].notna()].copy()
    combined_r0cb["log_duration_B_full_span_hours"] = np.log(combined_r0cb["duration_B_full_span_hours"].astype(float))
    combined_r0cb["log1p_customers_v2"] = np.log1p(combined_r0cb["customers_v2_event_excl_reinterruptions"].astype(float))

    verification = {
        "dev_wt_n": len(dev_wt), "holdout_wt_n": len(holdout_wt), "combined_wt_n": len(combined_wt),
        "combined_e0_n": len(combined_e0), "combined_r0cb_n": len(combined_r0cb),
        "combined_p99_cap_hours_recomputed": float(combined_p99),
        "dev_p99_cap_hours": float(dev_p99), "holdout_p99_cap_hours": float(holdout_p99),
    }
    log_step(f"CORRECTED final combined sample: WT n={len(combined_wt)}, E0 n={len(combined_e0)}, "
              f"R0c n={len(combined_r0cb)} (p99 cap={combined_p99:.2f}h)")
    return combined_wt, combined_e0, combined_r0cb, verification


if __name__ == "__main__":
    build_corrected_combined_samples()
