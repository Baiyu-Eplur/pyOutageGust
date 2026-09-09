"""C01 repair Step 4b: on the CORRECTED final combined sample, compute (a) 5-fold
GroupKFold coefficient stability for the gust linear+quadratic terms (matching
the project's standard v9.run_model/stability_summary method) and (b) the
out-of-sample variance decomposition (matching command #21's
step2_critical_wind_and_variance.py method exactly, v14.nested_r2_sequence).

Rebuilds the corrected sample via the same monkey-patch approach as
step3_4_corrected_sample_and_refit.py (kept self-contained here rather than
re-importing that script, to avoid re-running its bootstrap)."""
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

SRC = external_path('rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')
RAW_DIR = result_path('c01_repair_20260905/raw')

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


def log_step(msg):
    print(f"[C01-step4b] {msg}", flush=True)


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


def build_corrected_matched():
    df = pd.read_csv(read_input(SRC), usecols=V9_USECOLS, low_memory=False)
    old_event = df.drop_duplicates(INCIDENT_COL).copy().set_index(INCIDENT_COL, drop=False)

    comp = pd.read_csv(read_input(RAW_DIR / "step1_representative_row_comparison_full.csv"))
    comp["new_start_utc"] = pd.to_datetime(comp["new_start_utc"], utc=True)
    comp["new_incident_date_utc"] = comp["new_start_utc"].dt.date.astype(str)
    reext = pd.read_csv(read_input(RAW_DIR / "step2_weather_reextraction_full.csv")).set_index("Incident Reference")

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
    return matched


def main():
    log_step("Rebuilding corrected matched sample and combined E0/R0c samples...")
    corrected_matched = build_corrected_matched()
    step0_summary = {"n_weather_matched_events": int(len(corrected_matched))}

    sys.path.insert(0, str(project_path('scripts/v3_validation')))
    import v3_validation_pipeline as v9  # noqa: E402
    v9.step0_build_sample = lambda: (corrected_matched.copy(), step0_summary)

    spec = importlib.util.spec_from_file_location(
        "clean_sample_builder", str(project_path('scripts/dev_sample_decontamination/clean_sample_builder.py')))
    clean_sample_builder = importlib.util.module_from_spec(spec)
    sys.modules["clean_sample_builder"] = clean_sample_builder
    spec.loader.exec_module(clean_sample_builder)
    clean_sample_builder.v9.step0_build_sample = v9.step0_build_sample

    spec2 = importlib.util.spec_from_file_location(
        "build_holdout_sample", str(project_path('scripts/module_e_final_confirmation/build_holdout_sample.py')))
    build_holdout_sample = importlib.util.module_from_spec(spec2)
    sys.modules["build_holdout_sample"] = build_holdout_sample
    spec2.loader.exec_module(build_holdout_sample)
    build_holdout_sample.v9.step0_build_sample = v9.step0_build_sample

    from clean_sample_builder import build_clean_wt_samples
    from build_holdout_sample import build_holdout_wt_samples

    dev_wt, dev_e0, dev_r0cb, dev_p99 = build_clean_wt_samples()
    holdout_wt, holdout_e0, holdout_r0cb, holdout_p99 = build_holdout_wt_samples()

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
    log_step(f"Corrected combined E0 n={len(combined_e0)}, R0c n={len(combined_r0cb)}")

    # ---------------- fresh 5-fold GroupKFold + fold coefficient stability ----------------
    from sklearn.model_selection import GroupKFold

    def add_fresh_folds(df):
        d = df.copy()
        d["incident_date_utc"] = pd.to_datetime(d["incident_date_utc"], errors="coerce")
        gkf = GroupKFold(n_splits=5)
        d["cv_fold_v3"] = -1
        groups = d["incident_date_utc"].dt.date.astype(str)
        X_dummy = np.zeros(len(d))
        for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
            d.iloc[valid_idx, d.columns.get_loc("cv_fold_v3")] = fold_idx
        n_crossing = int((d.groupby(groups)["cv_fold_v3"].nunique() > 1).sum())
        assert n_crossing == 0
        return d

    log_step("Building fresh 5-fold GroupKFold splits...")
    combined_e0_folds = add_fresh_folds(combined_e0)
    combined_r0cb_folds = add_fresh_folds(combined_r0cb)

    log_step("Fitting per-fold coefficients (E0)...")
    e0_fold_df = v9.run_model(combined_e0_folds, "log1p_customers_v2", "E0_corrected",
                                ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=False)
    log_step("Fitting per-fold coefficients (R0c)...")
    r0c_fold_df = v9.run_model(combined_r0cb_folds, "log_duration_B_full_span_hours", "R0c_corrected",
                                 ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=True)

    e0_stability = v9.stability_summary(e0_fold_df)
    r0c_stability = v9.stability_summary(r0c_fold_df)
    e0_fold_df.to_csv(RAW_DIR / "step4b_E0_corrected_fold_coefs.csv", index=False)
    r0c_fold_df.to_csv(RAW_DIR / "step4b_R0c_corrected_fold_coefs.csv", index=False)
    e0_stability.to_csv(RAW_DIR / "step4b_E0_corrected_stability.csv", index=False)
    r0c_stability.to_csv(RAW_DIR / "step4b_R0c_corrected_stability.csv", index=False)
    log_step("E0 stability:\n" + e0_stability.to_string(index=False))
    log_step("R0c stability:\n" + r0c_stability.to_string(index=False))

    # ---------------- variance decomposition (matches command #21 method exactly) ----------------
    spec14 = importlib.util.spec_from_file_location(
        "variance_decomposition_pipeline",
        str(project_path('scripts/variance_decomposition/variance_decomposition_pipeline.py')))
    v14 = importlib.util.module_from_spec(spec14)
    spec14.loader.exec_module(v14)

    log_step("Running variance decomposition (E0)...")
    e0_var = v14.nested_r2_sequence(combined_e0_folds, "log1p_customers_v2", ["nongust_weather", "gust"],
                                      "E0_corrected")
    e0_var.to_csv(RAW_DIR / "step4b_E0_corrected_variance_decomposition.csv", index=False)
    log_step(e0_var.to_string(index=False))

    log_step("Running variance decomposition (R0c, gust-then-customers order)...")
    r0c_var = v14.nested_r2_sequence(combined_r0cb_folds, "log_duration_B_full_span_hours",
                                       ["nongust_weather", "gust", "customers"],
                                       "R0c_corrected_order_gust_then_customers")
    r0c_var.to_csv(RAW_DIR / "step4b_R0c_corrected_variance_decomposition_gust_first.csv", index=False)
    log_step(r0c_var.to_string(index=False))

    log_step("Running variance decomposition (R0c, customers-then-gust order)...")
    r0c_var2 = v14.nested_r2_sequence(combined_r0cb_folds, "log_duration_B_full_span_hours",
                                        ["nongust_weather", "customers", "gust"],
                                        "R0c_corrected_order_customers_then_gust")
    r0c_var2.to_csv(RAW_DIR / "step4b_R0c_corrected_variance_decomposition_customers_first.csv", index=False)
    log_step(r0c_var2.to_string(index=False))

    log_step("=== Step 4b complete ===")


if __name__ == "__main__":
    main()
