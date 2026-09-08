"""C01 repair Steps 3-4: build the corrected event-level weather-matched
sample (patching ONLY the fields that actually depend on which stage row is
the event's representative row -- gust_0h, pressure_msl_0h, temperature_0h,
precipitation_24h_sum, incident_date_utc -- everything else, e.g. LAD21CD,
population, customers_v2, duration_B, is an event-level broadcast value
identical across all of an incident's stage rows and does not need
correction), then reuse the EXISTING, UNCHANGED downstream pipeline
(v9.step1_lad_gapfill, GroupKFold construction, prep_predictors,
complete_predictors_mask, the dev/holdout split logic, the
weather_natural+technical_asset filter, and v9.design_train_valid + OLS
+ LAD-clustered SE) via monkey-patching v9.step0_build_sample so that ONLY
the input data changes and NOT one line of modelling logic.

Read-only against all original data files and all pre-existing results
directories. Writes only under claude_branch/results/c01_repair_20260905/.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905")

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

STORMS = {
    "Arwen": ("2021-11-25", "2021-11-28"), "Dudley": ("2022-02-15", "2022-02-17"),
    "Eunice": ("2022-02-17", "2022-02-19"), "Franklin": ("2022-02-19", "2022-02-22"),
    "Babet": ("2023-10-17", "2023-10-22"), "Ciaran": ("2023-10-31", "2023-11-03"),
    "Henk": ("2024-01-01", "2024-01-03"),
}
LOCKED_START, LOCKED_END = "2023-09-30", "2024-03-31"


def log_step(msg):
    print(f"[C01-step3/4] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, pd.Timestamp):
            return str(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def storm_for_date(date_str):
    d = pd.Timestamp(date_str)
    for name, (start, end) in STORMS.items():
        if pd.Timestamp(start) <= d <= pd.Timestamp(end):
            return name
    return None


def build_corrected_matched():
    log_step("Loading OLD-style event table (df.drop_duplicates, matches v9.step0_build_sample exactly)...")
    df = pd.read_csv(SRC, usecols=V9_USECOLS, low_memory=False)
    old_event = df.drop_duplicates(INCIDENT_COL).copy().set_index(INCIDENT_COL, drop=False)

    log_step("Loading Step1 (representative row) and Step2 (weather re-extraction) outputs...")
    comp = pd.read_csv(RAW_DIR / "step1_representative_row_comparison_full.csv")
    comp["new_start_utc"] = pd.to_datetime(comp["new_start_utc"], utc=True)
    comp["new_incident_date_utc"] = comp["new_start_utc"].dt.date.astype(str)

    reext = pd.read_csv(RAW_DIR / "step2_weather_reextraction_full.csv")
    reext = reext.set_index("Incident Reference")

    changed_ids = comp.loc[comp["representative_row_changed"], "Incident Reference"]
    comp_indexed = comp.set_index("Incident Reference")
    changed_in_corrected = pd.Index(changed_ids)[pd.Index(changed_ids).isin(old_event.index)]

    corrected = old_event.copy()

    # ---- vectorized date correction (all changed events) ----
    date_updates = comp_indexed.loc[changed_in_corrected, "new_incident_date_utc"]
    corrected.loc[date_updates.index, "incident_date_utc"] = date_updates.values
    n_date_corrected = len(date_updates)

    # ---- vectorized weather correction / nulling ----
    reext_changed = reext.reindex(changed_in_corrected)
    recovered_mask = reext_changed["cache_status"].astype(str).str.startswith("recovered")
    recovered_ids = reext_changed.index[recovered_mask.fillna(False)]
    nulled_ids = reext_changed.index[~recovered_mask.fillna(False)]

    weather_cols = ["gust_0h", "pressure_msl_0h", "temperature_0h", "precipitation_24h_sum"]
    recomputed_cols = ["recomputed_gust_0h", "recomputed_pressure_msl_0h",
                        "recomputed_temperature_0h", "recomputed_precip_24h_sum"]

    if len(recovered_ids):
        vals = reext_changed.loc[recovered_ids, recomputed_cols].to_numpy()
        corrected.loc[recovered_ids, weather_cols] = vals
    if len(nulled_ids):
        corrected.loc[nulled_ids, weather_cols] = np.nan

    n_weather_corrected = len(recovered_ids)
    n_weather_nulled = len(nulled_ids)

    corrected = corrected.reset_index(drop=True)
    log_step(f"Date corrected for {n_date_corrected} incidents; weather corrected for "
              f"{n_weather_corrected}; weather nulled (unrecoverable) for {n_weather_nulled}.")

    matched = corrected[corrected["weather_status_v3"] == "matched"].copy()
    step0_summary = {
        "n_total_events_v3": int(len(corrected)),
        "n_weather_matched_events": int(len(matched)),
        "weather_matched_pct": float(len(matched) / len(corrected) * 100),
    }
    log_step(f"Corrected matched sample: {len(matched)} events (was {len(matched)} before too -- "
              f"row selection changes do not change which incidents are 'matched').")
    return matched, step0_summary, comp


def main():
    log_step("=== Building corrected matched sample ===")
    corrected_matched, step0_summary, comp = build_corrected_matched()

    # ---------------- monkey-patch v9.step0_build_sample ----------------
    sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation")))
    import v3_validation_pipeline as v9  # noqa: E402

    def patched_step0_build_sample():
        return corrected_matched.copy(), step0_summary

    v9.step0_build_sample = patched_step0_build_sample

    # also patch it in already-imported dependent modules (clean_sample_builder / build_holdout_sample
    # import v9 by reference, so patching the v9 module object itself propagates automatically as long
    # as they call v9.step0_build_sample() rather than a bound copy)
    spec = importlib.util.spec_from_file_location(
        "clean_sample_builder", r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination\clean_sample_builder.py")
    clean_sample_builder = importlib.util.module_from_spec(spec)
    sys.modules["clean_sample_builder"] = clean_sample_builder
    # ensure clean_sample_builder's own "from ... import v9" binds to our already-patched module object
    sys.modules["v3_validation_pipeline"] = v9
    spec.loader.exec_module(clean_sample_builder)
    clean_sample_builder.v9.step0_build_sample = patched_step0_build_sample  # belt-and-braces

    spec2 = importlib.util.spec_from_file_location(
        "build_holdout_sample", r"D:\Pyprogramme\STST2603\claude_branch\scripts\module_e_final_confirmation\build_holdout_sample.py")
    build_holdout_sample = importlib.util.module_from_spec(spec2)
    sys.modules["build_holdout_sample"] = build_holdout_sample
    spec2.loader.exec_module(build_holdout_sample)
    build_holdout_sample.v9.step0_build_sample = patched_step0_build_sample

    log_step("=== Step 3: dev/holdout and storm reassignment diagnostics (on corrected dates) ===")
    # recompute using the OLD event-level table too, for a like-for-like before/after comparison
    old_matched = pd.read_csv(SRC, usecols=V9_USECOLS, low_memory=False).drop_duplicates(INCIDENT_COL).copy()
    old_matched = old_matched[old_matched["weather_status_v3"] == "matched"].copy()

    def assign_role(date_str):
        d = pd.Timestamp(date_str)
        if d >= pd.Timestamp(LOCKED_START) and d <= pd.Timestamp(LOCKED_END):
            return "holdout"
        return "dev"

    changed_ids = set(comp.loc[comp["representative_row_changed"], "Incident Reference"])
    old_sub = old_matched[old_matched[INCIDENT_COL].isin(changed_ids)].copy()
    new_sub = corrected_matched[corrected_matched[INCIDENT_COL].isin(changed_ids)].copy()
    old_sub = old_sub.set_index(INCIDENT_COL)
    new_sub = new_sub.set_index(INCIDENT_COL)
    common_ids = old_sub.index.intersection(new_sub.index)

    old_role = old_sub.loc[common_ids, "incident_date_utc"].apply(assign_role)
    new_role = new_sub.loc[common_ids, "incident_date_utc"].apply(assign_role)
    role_changed = (old_role != new_role)
    n_role_changed = int(role_changed.sum())

    old_storm = old_sub.loc[common_ids, "incident_date_utc"].apply(storm_for_date)
    new_storm = new_sub.loc[common_ids, "incident_date_utc"].apply(storm_for_date)
    storm_changed = (old_storm != new_storm)
    n_storm_changed = int(storm_changed.sum())

    log_step(f"Among {len(common_ids)} weather-matched incidents with a changed representative row: "
              f"dev/holdout role changed for {n_role_changed}, storm-window membership changed for {n_storm_changed}.")

    step3_summary = {
        "n_weather_matched_events_with_changed_rep_row": int(len(common_ids)),
        "n_dev_holdout_role_changed": n_role_changed,
        "n_storm_membership_changed": n_storm_changed,
        "role_changed_incident_ids": common_ids[role_changed].tolist(),
        "storm_changed_detail": [
            {"Incident Reference": iid, "old_storm": old_storm[iid], "new_storm": new_storm[iid]}
            for iid in common_ids[storm_changed]
        ],
    }
    (RAW_DIR / "step3_role_storm_reassignment.json").write_text(js(step3_summary), encoding="utf-8")

    log_step("=== Step 4: rebuild final combined sample (corrected) and refit E0/R0c ===")
    from clean_sample_builder import build_clean_wt_samples
    from build_holdout_sample import build_holdout_wt_samples

    dev_wt, dev_e0, dev_r0cb, dev_p99 = build_clean_wt_samples()
    holdout_wt, holdout_e0, holdout_r0cb, holdout_p99 = build_holdout_wt_samples()

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

    log_step(f"CORRECTED final combined sample: WT n={len(combined_wt)}, E0 n={len(combined_e0)}, "
              f"R0c n={len(combined_r0cb)} (p99 cap={combined_p99:.2f}h)")

    # --- A07/A08-style E0/R0c sample-specific changed-row rate (matches the audit's 13.57%/13.56%) ---
    e0_changed = combined_e0[INCIDENT_COL].isin(changed_ids).sum()
    r0c_changed = combined_r0cb[INCIDENT_COL].isin(changed_ids).sum()
    sample_specific_rates = {
        "combined_e0_n": len(combined_e0), "combined_e0_changed": int(e0_changed),
        "combined_e0_changed_pct": float(e0_changed / len(combined_e0) * 100),
        "combined_r0c_n": len(combined_r0cb), "combined_r0c_changed": int(r0c_changed),
        "combined_r0c_changed_pct": float(r0c_changed / len(combined_r0cb) * 100),
    }
    log_step(f"Sample-specific changed-row rates (cf. audit's 13.57%/13.56%): {sample_specific_rates}")

    # ---------------- refit E0 and R0c on the CORRECTED combined sample ----------------
    sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed")))
    spec11 = importlib.util.spec_from_file_location(
        "critical_wind_speed_pipeline", r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
    v11 = importlib.util.module_from_spec(spec11)
    spec11.loader.exec_module(v11)

    log_step("Fitting corrected E0...")
    res_e0, cov_e0, gust_mean_e0, gust_sd_e0, _ = v11.fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False)
    log_step("Fitting corrected R0c...")
    res_r0c, cov_r0c, gust_mean_r0c, gust_sd_r0c, _ = v11.fit_full_sample(
        combined_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)

    def coef_table(res, cov):
        se = np.sqrt(np.maximum(np.diag(cov), 0))
        z = res.params.to_numpy() / se
        p = 2 * stats.norm.sf(np.abs(z))
        return pd.DataFrame({"term": res.params.index, "coefficient": res.params.values, "std_error": se,
                              "p_value": p})

    e0_table = coef_table(res_e0, cov_e0)
    r0c_table = coef_table(res_r0c, cov_r0c)
    e0_table.to_csv(RAW_DIR / "step4_E0_corrected_full_coefs.csv", index=False)
    r0c_table.to_csv(RAW_DIR / "step4_R0c_corrected_full_coefs.csv", index=False)

    b1_e0, b2_e0 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1_e0, var2_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_e0, se_e0, lo_e0, hi_e0 = v11.delta_method_ci(b1_e0, b2_e0, var1_e0, var2_e0, cov12_e0)
    tp_ms_e0 = gust_mean_e0 + x_e0 * gust_sd_e0
    tp_ms_lo = gust_mean_e0 + lo_e0 * gust_sd_e0
    tp_ms_hi = gust_mean_e0 + hi_e0 * gust_sd_e0

    log_step(f"CORRECTED E0: beta1={b1_e0:.6f}, beta2={b2_e0:.6f}, turning point z={x_e0:.6f} "
              f"({tp_ms_e0:.4f} m/s), Delta CI(ms)=[{tp_ms_lo:.4f},{tp_ms_hi:.4f}]")

    log_step("Bootstrap (500 draws, same seed 20260826) for corrected E0 turning point...")
    boot, n_failed = v11.bootstrap_turning_point(combined_e0, "log1p_customers_v2", False, 500, 20260826)
    boot_lo_z, boot_hi_z = np.percentile(boot, [2.5, 97.5])
    boot_lo_ms, boot_hi_ms = gust_mean_e0 + boot_lo_z * gust_sd_e0, gust_mean_e0 + boot_hi_z * gust_sd_e0
    np.savetxt(RAW_DIR / "step4_E0_corrected_bootstrap_turning_points_z.csv", boot, delimiter=",")
    log_step(f"CORRECTED E0 Bootstrap CI(z)=[{boot_lo_z:.4f},{boot_hi_z:.4f}], "
              f"CI(ms)=[{boot_lo_ms:.4f},{boot_hi_ms:.4f}], n_failed={n_failed}")

    result = {
        "step0_summary": step0_summary,
        "step3_role_storm_summary": {k: v for k, v in step3_summary.items()
                                       if k not in ("role_changed_incident_ids", "storm_changed_detail")},
        "sample_specific_changed_rates": sample_specific_rates,
        "corrected_sample_sizes": {"wt": len(combined_wt), "e0": len(combined_e0), "r0c": len(combined_r0cb),
                                     "p99_cap": float(combined_p99)},
        "corrected_E0": {
            "beta1": float(b1_e0), "beta2": float(b2_e0),
            "turning_point_z": float(x_e0), "turning_point_ms": float(tp_ms_e0),
            "delta_ci_ms": [float(tp_ms_lo), float(tp_ms_hi)],
            "bootstrap_ci_z": [float(boot_lo_z), float(boot_hi_z)],
            "bootstrap_ci_ms": [float(boot_lo_ms), float(boot_hi_ms)],
            "gust_mean": float(gust_mean_e0), "gust_sd": float(gust_sd_e0),
        },
        "corrected_R0c": {
            "beta1": float(res_r0c.params["z_gust_0h"]), "beta2": float(res_r0c.params["z_gust_0h_sq"]),
        },
    }
    (RAW_DIR / "step4_corrected_model_summary.json").write_text(js(result), encoding="utf-8")
    log_step("Saved raw/step4_corrected_model_summary.json, step4_E0/R0c_corrected_full_coefs.csv")
    log_step("=== Steps 3-4 complete ===")


if __name__ == "__main__":
    main()
