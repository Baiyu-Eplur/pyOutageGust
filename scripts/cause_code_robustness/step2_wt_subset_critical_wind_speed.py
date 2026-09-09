"""Command #12 Step 2: full critical-wind-speed re-estimation restricted to the
weather_natural + technical_asset Cause Code subset, replicating command #11's
entire pipeline (per-fold turning points, delta method + bootstrap CIs, physical
unit conversion, observed-range percentile check) unchanged except for the
sample filter.
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
V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
OUT_DIR = result_path('cause_code_robustness')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

WT_GROUPS = {"weather_natural", "technical_asset"}
N_BOOTSTRAP = 500
RNG_SEED = 20260825

spec9 = importlib.util.spec_from_file_location("v3_validation_pipeline", V3_VALIDATION_SCRIPT)
v9 = importlib.util.module_from_spec(spec9)
spec9.loader.exec_module(v9)

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)


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
    print(f"[v12-step2] {msg}", flush=True)


def build_wt_samples():
    log_step("Reconstructing base sample and restricting to weather_natural+technical_asset...")
    matched, _ = v9.step0_build_sample()
    matched, _ = v9.step1_lad_gapfill(matched)
    sample, _ = v9.step2_build_folds(matched)
    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()

    wt_mask = sample["cause_group_official"].isin(WT_GROUPS)
    sample_wt = sample.loc[wt_mask].copy()
    log_step(f"Base complete-predictor sample: n={len(sample)}; "
              f"weather_natural+technical_asset subset: n={len(sample_wt)} "
              f"({len(sample_wt) / len(sample) * 100:.2f}%).")

    e0_sample = sample_wt.loc[sample_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    r0b_sample = sample_wt.loc[
        sample_wt["duration_B_full_span_hours"].notna() & (sample_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    p99_b = r0b_sample["duration_B_full_span_hours"].quantile(0.99)
    r0b_sample = r0b_sample.loc[r0b_sample["duration_B_full_span_hours"] <= p99_b].copy()
    r0b_sample["log_duration_B_full_span_hours"] = np.log(r0b_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample = r0b_sample.loc[r0b_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()

    log_step(f"E0' (WT subset) n={len(e0_sample)}; R0c'_B (WT subset) n={len(r0cb_sample)} (p99 cap={p99_b:.2f}h).")
    return sample_wt, e0_sample, r0cb_sample, p99_b


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_wt_samples()

    sample_sizes = {
        "n_wt_complete_predictors": int(len(sample_wt)),
        "n_e0_prime_wt": int(len(e0_sample)),
        "n_r0c_prime_b_wt": int(len(r0cb_sample)),
        "duration_B_p99_cap_hours_wt": float(p99_b),
    }
    (RAW_DIR / "step2_sample_sizes.json").write_text(js(sample_sizes), encoding="utf-8")

    # ---------------- per-fold turning points (reuse folds already on sample_wt) ----------------
    log_step("Fitting per-fold E0'_WT and R0c'_B_WT (reusing original date-based fold labels)...")
    e0_fold = v9.run_model(e0_sample, "log1p_customers_v2", "E0_prime_WT", v9.TERMS_OF_INTEREST)
    r0cb_fold = v9.run_model(
        r0cb_sample, "log_duration_B_full_span_hours", "R0c_prime_B_WT",
        v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, use_customers_covariate=True,
    )
    e0_fold.to_csv(RAW_DIR / "E0_prime_WT_fold_coefs.csv", index=False)
    r0cb_fold.to_csv(RAW_DIR / "R0c_prime_B_WT_fold_coefs.csv", index=False)

    e0_tp = v11.turning_point_fold_table(e0_fold, "E0_prime_WT")
    r0cb_tp = v11.turning_point_fold_table(r0cb_fold, "R0c_prime_B_WT")
    e0_tp.to_csv(RAW_DIR / "E0_prime_WT_fold_turning_points.csv", index=False)
    r0cb_tp.to_csv(RAW_DIR / "R0c_prime_B_WT_fold_turning_points.csv", index=False)

    def fold_tp_summary(tp_df):
        return {
            "n_folds": int(len(tp_df)),
            "mean": float(tp_df["turning_point_z"].mean()),
            "std": float(tp_df["turning_point_z"].std(ddof=1)),
            "cv_pct": float(tp_df["turning_point_z"].std(ddof=1) / abs(tp_df["turning_point_z"].mean()) * 100),
            "min": float(tp_df["turning_point_z"].min()),
            "max": float(tp_df["turning_point_z"].max()),
            "values": tp_df["turning_point_z"].tolist(),
        }

    step1_summary = {"E0_prime_WT": fold_tp_summary(e0_tp), "R0c_prime_B_WT": fold_tp_summary(r0cb_tp)}
    (RAW_DIR / "step1_fold_turning_point_summary_WT.json").write_text(js(step1_summary), encoding="utf-8")
    log_step(f"E0'_WT fold turning points: {e0_tp['turning_point_z'].tolist()}")
    log_step(f"R0c'_B_WT fold turning points: {r0cb_tp['turning_point_z'].tolist()}")

    # ---------------- full-sample fit + delta method ----------------
    log_step("Full-sample fit E0'_WT...")
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = v11.fit_full_sample(
        e0_sample, "log1p_customers_v2", use_customers_covariate=False)
    b1_e0, b2_e0 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1_e0, var2_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_e0, se_e0, lo_e0, hi_e0 = v11.delta_method_ci(b1_e0, b2_e0, var1_e0, var2_e0, cov12_e0)
    log_step(f"E0'_WT: beta1={b1_e0:.4f}, beta2={b2_e0:.4f}, x*={x_e0:.4f}, delta-CI=[{lo_e0:.4f},{hi_e0:.4f}]")

    log_step("Full-sample fit R0c'_B_WT...")
    res_r, cov_r, mean_gust_r, sd_gust_r, d_r = v11.fit_full_sample(
        r0cb_sample, "log_duration_B_full_span_hours", use_customers_covariate=True)
    b1_r, b2_r = res_r.params["z_gust_0h"], res_r.params["z_gust_0h_sq"]
    var1_r, var2_r = cov_r.loc["z_gust_0h", "z_gust_0h"], cov_r.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_r = cov_r.loc["z_gust_0h", "z_gust_0h_sq"]
    x_r, se_r, lo_r, hi_r = v11.delta_method_ci(b1_r, b2_r, var1_r, var2_r, cov12_r)
    log_step(f"R0c'_B_WT: beta1={b1_r:.4f}, beta2={b2_r:.4f}, x*={x_r:.4f}, delta-CI=[{lo_r:.4f},{hi_r:.4f}]")

    # ---------------- bootstrap ----------------
    log_step(f"Bootstrap E0'_WT ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_e0, e0_failed = v11.bootstrap_turning_point(
        e0_sample, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
    boot_e0_lo, boot_e0_hi = np.percentile(boot_e0, [2.5, 97.5])

    log_step(f"Bootstrap R0c'_B_WT ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_r, r_failed = v11.bootstrap_turning_point(
        r0cb_sample, "log_duration_B_full_span_hours", True, N_BOOTSTRAP, RNG_SEED + 1)
    boot_r_lo, boot_r_hi = np.percentile(boot_r, [2.5, 97.5])

    np.savetxt(RAW_DIR / "E0_prime_WT_bootstrap_turning_points_z.csv", boot_e0, delimiter=",")
    np.savetxt(RAW_DIR / "R0c_prime_B_WT_bootstrap_turning_points_z.csv", boot_r, delimiter=",")

    step2_summary = {
        "E0_prime_WT": {
            "n": int(len(e0_sample)), "beta1": float(b1_e0), "beta2": float(b2_e0),
            "turning_point_z": float(x_e0), "delta_se": float(se_e0),
            "delta_ci_95": [float(lo_e0), float(hi_e0)],
            "bootstrap_n_success": int(len(boot_e0)), "bootstrap_n_failed": int(e0_failed),
            "bootstrap_mean": float(np.mean(boot_e0)), "bootstrap_std": float(np.std(boot_e0, ddof=1)),
            "bootstrap_ci_95": [float(boot_e0_lo), float(boot_e0_hi)],
            "gust_mean_full_sample": float(mean_gust_e0), "gust_sd_full_sample": float(sd_gust_e0),
        },
        "R0c_prime_B_WT": {
            "n": int(len(r0cb_sample)), "beta1": float(b1_r), "beta2": float(b2_r),
            "turning_point_z": float(x_r), "delta_se": float(se_r),
            "delta_ci_95": [float(lo_r), float(hi_r)],
            "bootstrap_n_success": int(len(boot_r)), "bootstrap_n_failed": int(r_failed),
            "bootstrap_mean": float(np.mean(boot_r)), "bootstrap_std": float(np.std(boot_r, ddof=1)),
            "bootstrap_ci_95": [float(boot_r_lo), float(boot_r_hi)],
            "gust_mean_full_sample": float(mean_gust_r), "gust_sd_full_sample": float(sd_gust_r),
        },
    }
    (RAW_DIR / "step2_turning_point_estimates_WT.json").write_text(js(step2_summary), encoding="utf-8")

    # ---------------- physical units ----------------
    def to_physical(z_val, mean_g, sd_g):
        return mean_g + z_val * sd_g

    step3 = {
        "E0_prime_WT": {
            "point_ms": to_physical(x_e0, mean_gust_e0, sd_gust_e0),
            "delta_ci_95_ms": [to_physical(lo_e0, mean_gust_e0, sd_gust_e0), to_physical(hi_e0, mean_gust_e0, sd_gust_e0)],
            "bootstrap_ci_95_ms": [to_physical(boot_e0_lo, mean_gust_e0, sd_gust_e0), to_physical(boot_e0_hi, mean_gust_e0, sd_gust_e0)],
        },
        "R0c_prime_B_WT": {
            "point_ms": to_physical(x_r, mean_gust_r, sd_gust_r),
            "delta_ci_95_ms": [to_physical(lo_r, mean_gust_r, sd_gust_r), to_physical(hi_r, mean_gust_r, sd_gust_r)],
            "bootstrap_ci_95_ms": [to_physical(boot_r_lo, mean_gust_r, sd_gust_r), to_physical(boot_r_hi, mean_gust_r, sd_gust_r)],
        },
    }
    (RAW_DIR / "step3_physical_units_WT.json").write_text(js(step3), encoding="utf-8")

    # ---------------- observed range check ----------------
    def dist_summary(g: pd.Series):
        return {
            "min": float(g.min()), "p1": float(g.quantile(0.01)), "p5": float(g.quantile(0.05)),
            "p50": float(g.quantile(0.50)), "p95": float(g.quantile(0.95)), "p99": float(g.quantile(0.99)),
            "max": float(g.max()), "n": int(g.notna().sum()),
        }

    def percentile_of(value, g: pd.Series):
        return float((g < value).mean() * 100)

    step4 = {
        "E0_prime_WT_gust_distribution_ms": dist_summary(d_e0["gust_0h"]),
        "R0c_prime_B_WT_gust_distribution_ms": dist_summary(d_r["gust_0h"]),
        "E0_prime_WT_turning_point_percentile": percentile_of(step3["E0_prime_WT"]["point_ms"], d_e0["gust_0h"]),
        "R0c_prime_B_WT_turning_point_percentile": percentile_of(step3["R0c_prime_B_WT"]["point_ms"], d_r["gust_0h"]),
    }
    (RAW_DIR / "step4_distribution_and_percentile_WT.json").write_text(js(step4), encoding="utf-8")
    log_step(f"E0'_WT turning point percentile: {step4['E0_prime_WT_turning_point_percentile']:.2f}")
    log_step(f"R0c'_B_WT turning point percentile: {step4['R0c_prime_B_WT_turning_point_percentile']:.2f}")

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
