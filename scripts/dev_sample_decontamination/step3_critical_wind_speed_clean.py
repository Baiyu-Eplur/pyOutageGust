"""Command #16 Step 3: re-estimate the critical wind speed (E0' turning point only,
per command scope) on the clean (decontaminated) weather_natural+technical_asset
sample, replicating command #11's full method (per-fold turning points, delta
method + bootstrap CIs, physical units, observed-range percentile).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from clean_sample_builder import build_clean_wt_samples, v9  # noqa: E402

V11_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\dev_sample_decontamination")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260825

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
    print(f"[v16-step3] {msg}", flush=True)


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_clean_wt_samples()

    # ---------------- per-fold turning points ----------------
    log_step("Fitting per-fold E0'_clean and R0c'_B_clean for turning points...")
    e0_fold = v9.run_model(e0_sample, "log1p_customers_v2", "E0_prime_clean", v9.TERMS_OF_INTEREST)
    r0cb_fold = v9.run_model(
        r0cb_sample, "log_duration_B_full_span_hours", "R0c_prime_B_clean",
        v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, use_customers_covariate=True,
    )

    e0_tp = v11.turning_point_fold_table(e0_fold, "E0_prime_clean")
    r0cb_tp = v11.turning_point_fold_table(r0cb_fold, "R0c_prime_B_clean")
    e0_tp.to_csv(RAW_DIR / "E0_prime_clean_fold_turning_points.csv", index=False)
    r0cb_tp.to_csv(RAW_DIR / "R0c_prime_B_clean_fold_turning_points.csv", index=False)

    def fold_tp_summary(tp_df):
        return {
            "n_folds": int(len(tp_df)), "mean": float(tp_df["turning_point_z"].mean()),
            "std": float(tp_df["turning_point_z"].std(ddof=1)),
            "cv_pct": float(tp_df["turning_point_z"].std(ddof=1) / abs(tp_df["turning_point_z"].mean()) * 100),
            "min": float(tp_df["turning_point_z"].min()), "max": float(tp_df["turning_point_z"].max()),
            "values": tp_df["turning_point_z"].tolist(),
        }

    step1_summary = {"E0_prime_clean": fold_tp_summary(e0_tp), "R0c_prime_B_clean": fold_tp_summary(r0cb_tp)}
    (RAW_DIR / "step3_fold_turning_point_summary_clean.json").write_text(js(step1_summary), encoding="utf-8")
    log_step(f"E0'_clean fold turning points: {e0_tp['turning_point_z'].tolist()}")
    log_step(f"R0c'_B_clean fold turning points: {r0cb_tp['turning_point_z'].tolist()}")

    # ---------------- full-sample fit + delta method ----------------
    log_step("Full-sample fit E0'_clean...")
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = v11.fit_full_sample(
        e0_sample, "log1p_customers_v2", use_customers_covariate=False)
    b1_e0, b2_e0 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1_e0, var2_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_e0, se_e0, lo_e0, hi_e0 = v11.delta_method_ci(b1_e0, b2_e0, var1_e0, var2_e0, cov12_e0)
    log_step(f"E0'_clean: beta1={b1_e0:.4f}, beta2={b2_e0:.4f}, x*={x_e0:.4f}, delta-CI=[{lo_e0:.4f},{hi_e0:.4f}]")

    log_step("Full-sample fit R0c'_B_clean...")
    res_r, cov_r, mean_gust_r, sd_gust_r, d_r = v11.fit_full_sample(
        r0cb_sample, "log_duration_B_full_span_hours", use_customers_covariate=True)
    b1_r, b2_r = res_r.params["z_gust_0h"], res_r.params["z_gust_0h_sq"]
    var1_r, var2_r = cov_r.loc["z_gust_0h", "z_gust_0h"], cov_r.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_r = cov_r.loc["z_gust_0h", "z_gust_0h_sq"]
    x_r, se_r, lo_r, hi_r = v11.delta_method_ci(b1_r, b2_r, var1_r, var2_r, cov12_r)
    log_step(f"R0c'_B_clean: beta1={b1_r:.4f}, beta2={b2_r:.4f}, x*={x_r:.4f}, delta-CI=[{lo_r:.4f},{hi_r:.4f}]")

    # ---------------- bootstrap ----------------
    log_step(f"Bootstrap E0'_clean ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_e0, e0_failed = v11.bootstrap_turning_point(
        e0_sample, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
    boot_e0_lo, boot_e0_hi = np.percentile(boot_e0, [2.5, 97.5])

    log_step(f"Bootstrap R0c'_B_clean ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_r, r_failed = v11.bootstrap_turning_point(
        r0cb_sample, "log_duration_B_full_span_hours", True, N_BOOTSTRAP, RNG_SEED + 1)
    boot_r_lo, boot_r_hi = np.percentile(boot_r, [2.5, 97.5])

    np.savetxt(RAW_DIR / "E0_prime_clean_bootstrap_turning_points_z.csv", boot_e0, delimiter=",")
    np.savetxt(RAW_DIR / "R0c_prime_B_clean_bootstrap_turning_points_z.csv", boot_r, delimiter=",")

    step2_summary = {
        "E0_prime_clean": {
            "n": int(len(e0_sample)), "beta1": float(b1_e0), "beta2": float(b2_e0),
            "turning_point_z": float(x_e0), "delta_se": float(se_e0),
            "delta_ci_95": [float(lo_e0), float(hi_e0)],
            "bootstrap_n_success": int(len(boot_e0)), "bootstrap_n_failed": int(e0_failed),
            "bootstrap_mean": float(np.mean(boot_e0)), "bootstrap_std": float(np.std(boot_e0, ddof=1)),
            "bootstrap_ci_95": [float(boot_e0_lo), float(boot_e0_hi)],
            "gust_mean_full_sample": float(mean_gust_e0), "gust_sd_full_sample": float(sd_gust_e0),
        },
        "R0c_prime_B_clean": {
            "n": int(len(r0cb_sample)), "beta1": float(b1_r), "beta2": float(b2_r),
            "turning_point_z": float(x_r), "delta_se": float(se_r),
            "delta_ci_95": [float(lo_r), float(hi_r)],
            "bootstrap_n_success": int(len(boot_r)), "bootstrap_n_failed": int(r_failed),
            "bootstrap_mean": float(np.mean(boot_r)), "bootstrap_std": float(np.std(boot_r, ddof=1)),
            "bootstrap_ci_95": [float(boot_r_lo), float(boot_r_hi)],
            "gust_mean_full_sample": float(mean_gust_r), "gust_sd_full_sample": float(sd_gust_r),
        },
    }
    (RAW_DIR / "step3_turning_point_estimates_clean.json").write_text(js(step2_summary), encoding="utf-8")

    def to_physical(z_val, mean_g, sd_g):
        return mean_g + z_val * sd_g

    step3 = {
        "E0_prime_clean": {
            "point_ms": to_physical(x_e0, mean_gust_e0, sd_gust_e0),
            "delta_ci_95_ms": [to_physical(lo_e0, mean_gust_e0, sd_gust_e0), to_physical(hi_e0, mean_gust_e0, sd_gust_e0)],
            "bootstrap_ci_95_ms": [to_physical(boot_e0_lo, mean_gust_e0, sd_gust_e0), to_physical(boot_e0_hi, mean_gust_e0, sd_gust_e0)],
        },
        "R0c_prime_B_clean": {
            "point_ms": to_physical(x_r, mean_gust_r, sd_gust_r),
            "delta_ci_95_ms": [to_physical(lo_r, mean_gust_r, sd_gust_r), to_physical(hi_r, mean_gust_r, sd_gust_r)],
            "bootstrap_ci_95_ms": [to_physical(boot_r_lo, mean_gust_r, sd_gust_r), to_physical(boot_r_hi, mean_gust_r, sd_gust_r)],
        },
    }
    (RAW_DIR / "step3_physical_units_clean.json").write_text(js(step3), encoding="utf-8")

    def dist_summary(g: pd.Series):
        return {
            "min": float(g.min()), "p1": float(g.quantile(0.01)), "p5": float(g.quantile(0.05)),
            "p50": float(g.quantile(0.50)), "p95": float(g.quantile(0.95)), "p99": float(g.quantile(0.99)),
            "max": float(g.max()), "n": int(g.notna().sum()),
        }

    def percentile_of(value, g: pd.Series):
        return float((g < value).mean() * 100)

    step4 = {
        "E0_prime_clean_gust_distribution_ms": dist_summary(d_e0["gust_0h"]),
        "R0c_prime_B_clean_gust_distribution_ms": dist_summary(d_r["gust_0h"]),
        "E0_prime_clean_turning_point_percentile": percentile_of(step3["E0_prime_clean"]["point_ms"], d_e0["gust_0h"]),
        "R0c_prime_B_clean_turning_point_percentile": percentile_of(step3["R0c_prime_B_clean"]["point_ms"], d_r["gust_0h"]),
    }
    (RAW_DIR / "step3_distribution_and_percentile_clean.json").write_text(js(step4), encoding="utf-8")
    log_step(f"E0'_clean turning point percentile: {step4['E0_prime_clean_turning_point_percentile']:.2f}")
    log_step(f"R0c'_B_clean turning point percentile: {step4['R0c_prime_B_clean_turning_point_percentile']:.2f}")

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
