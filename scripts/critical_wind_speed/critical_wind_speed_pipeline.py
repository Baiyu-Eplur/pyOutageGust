"""Command #11: critical wind speed (quadratic turning point) for E0' (exposure) and
R0c'_B (recovery, customers_v2-adjusted, duration_B) using command #9/#10's already
validated 121,313-event sample, 5 folds, and model specs.

Read-only against rebuild_v3_full_stage/ and the command #9 script/results.
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
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

V3_VALIDATION_SCRIPT = project_path('scripts/v3_validation/v3_validation_pipeline.py')
V3_VALIDATION_RAW = result_path('v3_validation/raw')
OUT_DIR = result_path('critical_wind_speed')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

RNG_SEED = 20260825
N_BOOTSTRAP = 500

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
    print(f"[v11] {msg}", flush=True)


# ---------------- Step 0: reconstruct sample + reproduce fold coefficients ----------------

def reconstruct_and_reproduce():
    log_step("Reconstructing command #9's sample/folds and reproducing fold coefficients...")
    matched, _ = v9.step0_build_sample()
    matched, _ = v9.step1_lad_gapfill(matched)
    sample, _ = v9.step2_build_folds(matched)
    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()

    e0_sample = sample.loc[sample["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    r0b_sample = sample.loc[sample["duration_B_full_span_hours"].notna() & (sample["duration_B_full_span_hours"] > 0)].copy()
    p99_b = r0b_sample["duration_B_full_span_hours"].quantile(0.99)
    r0b_sample = r0b_sample.loc[r0b_sample["duration_B_full_span_hours"] <= p99_b].copy()
    r0b_sample["log_duration_B_full_span_hours"] = np.log(r0b_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample = r0b_sample.loc[r0b_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()

    e0_fold_reproduced = v9.run_model(e0_sample, "log1p_customers_v2", "E0_prime_customers_v2", v9.TERMS_OF_INTEREST)
    r0cb_fold_reproduced = v9.run_model(
        r0cb_sample, "log_duration_B_full_span_hours", "R0c_prime_B_custadj",
        v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, use_customers_covariate=True,
    )

    e0_hist = pd.read_csv(read_input(V3_VALIDATION_RAW / "E0_prime_fold_coefs.csv"))
    r0cb_hist = pd.read_csv(read_input(V3_VALIDATION_RAW / "R0c_prime_B_fold_coefs.csv"))

    def max_diff(new, hist, terms):
        m = new.merge(hist, on=["model", "fold", "term"], suffixes=("_new", "_hist"))
        return float((m["coefficient_new"] - m["coefficient_hist"]).abs().max())

    e0_diff = max_diff(e0_fold_reproduced, e0_hist, v9.TERMS_OF_INTEREST)
    r0cb_diff = max_diff(r0cb_fold_reproduced, r0cb_hist, v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST)

    repro = {
        "e0_prime_n": int(len(e0_sample)),
        "r0c_prime_b_n": int(len(r0cb_sample)),
        "e0_prime_max_abs_coef_diff_vs_command9": e0_diff,
        "r0c_prime_b_max_abs_coef_diff_vs_command9": r0cb_diff,
        "reproduction_passed": bool(e0_diff < 1e-8 and r0cb_diff < 1e-8),
    }
    (RAW_DIR / "step0_reproduction_check.json").write_text(js(repro), encoding="utf-8")
    log_step(f"Reproduction check: E0' max diff={e0_diff:.2e}, R0c'_B max diff={r0cb_diff:.2e}, "
              f"passed={repro['reproduction_passed']}.")
    assert repro["reproduction_passed"], "Reproduction check failed — aborting."

    return sample, e0_sample, r0cb_sample, e0_fold_reproduced, r0cb_fold_reproduced


# ---------------- turning point utilities ----------------

def turning_point(beta1, beta2):
    return -beta1 / (2 * beta2)


def turning_point_fold_table(fold_df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    rows = []
    for fold in sorted(fold_df["fold"].unique()):
        g = fold_df[fold_df["fold"] == fold]
        b1 = g.loc[g["term"] == "z_gust_0h", "coefficient"].iloc[0]
        b2 = g.loc[g["term"] == "z_gust_0h_sq", "coefficient"].iloc[0]
        rows.append({"model": model_name, "fold": int(fold), "beta1": b1, "beta2": b2,
                     "turning_point_z": turning_point(b1, b2)})
    return pd.DataFrame(rows)


# ---------------- full-sample fit (no train/valid split) ----------------

def fit_full_sample(df: pd.DataFrame, target_col: str, use_customers_covariate: bool):
    d = df.copy()
    extra_scale_cols = None
    if use_customers_covariate:
        d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
        extra_scale_cols = ["customers_v2_log1p"]
    # design_train_valid(train, valid) standardizes using train's mean/sd; passing the
    # same full sample as both train and valid yields full-sample standardization and
    # an identical design matrix for both (Xtr is what we use).
    Xfull, _ = v9.design_train_valid(d, d, extra_scale_cols=extra_scale_cols)
    y = d[target_col].astype(float)
    res = sm.OLS(y, Xfull).fit()
    groups_lad = pd.factorize(d["LAD21CD"])[0]
    cov = cov_cluster(res, groups_lad)
    cov_df = pd.DataFrame(cov, index=res.params.index, columns=res.params.index)
    gust_mean = d["gust_0h"].mean()
    gust_sd = d["gust_0h"].std(ddof=1)
    return res, cov_df, gust_mean, gust_sd, d


def delta_method_ci(beta1, beta2, var1, var2, cov12):
    x_star = turning_point(beta1, beta2)
    d_dbeta1 = -1.0 / (2 * beta2)
    d_dbeta2 = beta1 / (2 * beta2 ** 2)
    var_x = (d_dbeta1 ** 2) * var1 + (d_dbeta2 ** 2) * var2 + 2 * d_dbeta1 * d_dbeta2 * cov12
    se_x = np.sqrt(max(var_x, 0))
    return x_star, se_x, x_star - 1.96 * se_x, x_star + 1.96 * se_x


def bootstrap_turning_point(df: pd.DataFrame, target_col: str, use_customers_covariate: bool,
                             n_boot: int, seed: int):
    rng = np.random.default_rng(seed)
    dates = df["incident_date_utc"].dt.date.astype(str)
    unique_dates = dates.unique()
    n_dates = len(unique_dates)
    by_date = {d: idx.to_numpy() for d, idx in df.groupby(dates).groups.items()}

    results = []
    for b in range(n_boot):
        sampled_dates = rng.choice(unique_dates, size=n_dates, replace=True)
        idx = np.concatenate([by_date[d] for d in sampled_dates])
        boot_df = df.loc[idx].copy()
        d = boot_df.copy()
        extra_scale_cols = None
        if use_customers_covariate:
            d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
            extra_scale_cols = ["customers_v2_log1p"]
        try:
            Xb, _ = v9.design_train_valid(d, d, extra_scale_cols=extra_scale_cols)
            y = d[target_col].astype(float)
            res = sm.OLS(y, Xb).fit()
            b1 = res.params["z_gust_0h"]
            b2 = res.params["z_gust_0h_sq"]
            results.append(turning_point(b1, b2))
        except Exception as exc:  # noqa: BLE001
            results.append(np.nan)
        if (b + 1) % 100 == 0:
            log_step(f"  bootstrap {b + 1}/{n_boot} done")
    arr = np.array(results)
    n_failed = int(np.isnan(arr).sum())
    arr_valid = arr[~np.isnan(arr)]
    return arr_valid, n_failed


def main():
    sample, e0_sample, r0cb_sample, e0_fold, r0cb_fold = reconstruct_and_reproduce()

    # ---------------- Step 1: per-fold turning points ----------------
    log_step("Step 1: per-fold turning points...")
    e0_tp = turning_point_fold_table(e0_fold, "E0_prime")
    r0cb_tp = turning_point_fold_table(r0cb_fold, "R0c_prime_B")
    e0_tp.to_csv(RAW_DIR / "E0_prime_fold_turning_points.csv", index=False)
    r0cb_tp.to_csv(RAW_DIR / "R0c_prime_B_fold_turning_points.csv", index=False)

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

    step1_summary = {"E0_prime": fold_tp_summary(e0_tp), "R0c_prime_B": fold_tp_summary(r0cb_tp)}
    (RAW_DIR / "step1_fold_turning_point_summary.json").write_text(js(step1_summary), encoding="utf-8")
    log_step(f"E0' fold turning points: {e0_tp['turning_point_z'].tolist()}")
    log_step(f"R0c'_B fold turning points: {r0cb_tp['turning_point_z'].tolist()}")

    # ---------------- Step 2: full-sample fit + delta method + bootstrap ----------------
    log_step("Step 2: full-sample fit (E0')...")
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = fit_full_sample(
        e0_sample, "log1p_customers_v2", use_customers_covariate=False)
    b1_e0, b2_e0 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1_e0, var2_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_e0, se_e0, lo_e0, hi_e0 = delta_method_ci(b1_e0, b2_e0, var1_e0, var2_e0, cov12_e0)
    log_step(f"E0' full-sample: beta1={b1_e0:.4f}, beta2={b2_e0:.4f}, turning point z={x_e0:.4f} "
              f"delta-CI=[{lo_e0:.4f}, {hi_e0:.4f}]")

    log_step("Step 2: full-sample fit (R0c'_B)...")
    res_r0cb, cov_r0cb, mean_gust_r0cb, sd_gust_r0cb, d_r0cb = fit_full_sample(
        r0cb_sample, "log_duration_B_full_span_hours", use_customers_covariate=True)
    b1_r, b2_r = res_r0cb.params["z_gust_0h"], res_r0cb.params["z_gust_0h_sq"]
    var1_r, var2_r = cov_r0cb.loc["z_gust_0h", "z_gust_0h"], cov_r0cb.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_r = cov_r0cb.loc["z_gust_0h", "z_gust_0h_sq"]
    x_r, se_r, lo_r, hi_r = delta_method_ci(b1_r, b2_r, var1_r, var2_r, cov12_r)
    log_step(f"R0c'_B full-sample: beta1={b1_r:.4f}, beta2={b2_r:.4f}, turning point z={x_r:.4f} "
              f"delta-CI=[{lo_r:.4f}, {hi_r:.4f}]")

    log_step(f"Bootstrap E0' ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_e0, e0_failed = bootstrap_turning_point(
        e0_sample, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
    boot_e0_lo, boot_e0_hi = np.percentile(boot_e0, [2.5, 97.5])

    log_step(f"Bootstrap R0c'_B ({N_BOOTSTRAP} draws, date-clustered)...")
    boot_r0cb, r0cb_failed = bootstrap_turning_point(
        r0cb_sample, "log_duration_B_full_span_hours", True, N_BOOTSTRAP, RNG_SEED + 1)
    boot_r0cb_lo, boot_r0cb_hi = np.percentile(boot_r0cb, [2.5, 97.5])

    np.savetxt(RAW_DIR / "E0_prime_bootstrap_turning_points_z.csv", boot_e0, delimiter=",")
    np.savetxt(RAW_DIR / "R0c_prime_B_bootstrap_turning_points_z.csv", boot_r0cb, delimiter=",")

    step2_summary = {
        "E0_prime": {
            "n": int(len(e0_sample)), "beta1": float(b1_e0), "beta2": float(b2_e0),
            "turning_point_z": float(x_e0), "delta_se": float(se_e0),
            "delta_ci_95": [float(lo_e0), float(hi_e0)],
            "bootstrap_n_success": int(len(boot_e0)), "bootstrap_n_failed": int(e0_failed),
            "bootstrap_mean": float(np.mean(boot_e0)), "bootstrap_std": float(np.std(boot_e0, ddof=1)),
            "bootstrap_ci_95": [float(boot_e0_lo), float(boot_e0_hi)],
            "gust_mean_full_sample": float(mean_gust_e0), "gust_sd_full_sample": float(sd_gust_e0),
        },
        "R0c_prime_B": {
            "n": int(len(r0cb_sample)), "beta1": float(b1_r), "beta2": float(b2_r),
            "turning_point_z": float(x_r), "delta_se": float(se_r),
            "delta_ci_95": [float(lo_r), float(hi_r)],
            "bootstrap_n_success": int(len(boot_r0cb)), "bootstrap_n_failed": int(r0cb_failed),
            "bootstrap_mean": float(np.mean(boot_r0cb)), "bootstrap_std": float(np.std(boot_r0cb, ddof=1)),
            "bootstrap_ci_95": [float(boot_r0cb_lo), float(boot_r0cb_hi)],
            "gust_mean_full_sample": float(mean_gust_r0cb), "gust_sd_full_sample": float(sd_gust_r0cb),
        },
    }
    (RAW_DIR / "step2_turning_point_estimates.json").write_text(js(step2_summary), encoding="utf-8")

    # ---------------- Step 3: convert to physical units (m/s) ----------------
    log_step("Step 3: converting to physical units (gust_0h is in m/s, wind_speed_unit='ms')...")

    def to_physical(z_val, mean_g, sd_g):
        return mean_g + z_val * sd_g

    step3 = {
        "gust_unit": "m/s (Open-Meteo API called with wind_speed_unit='ms', verified in main1_v3.py line 337)",
        "E0_prime": {
            "point_ms": to_physical(x_e0, mean_gust_e0, sd_gust_e0),
            "delta_ci_95_ms": [to_physical(lo_e0, mean_gust_e0, sd_gust_e0), to_physical(hi_e0, mean_gust_e0, sd_gust_e0)],
            "bootstrap_ci_95_ms": [to_physical(boot_e0_lo, mean_gust_e0, sd_gust_e0), to_physical(boot_e0_hi, mean_gust_e0, sd_gust_e0)],
        },
        "R0c_prime_B": {
            "point_ms": to_physical(x_r, mean_gust_r0cb, sd_gust_r0cb),
            "delta_ci_95_ms": [to_physical(lo_r, mean_gust_r0cb, sd_gust_r0cb), to_physical(hi_r, mean_gust_r0cb, sd_gust_r0cb)],
            "bootstrap_ci_95_ms": [to_physical(boot_r0cb_lo, mean_gust_r0cb, sd_gust_r0cb), to_physical(boot_r0cb_hi, mean_gust_r0cb, sd_gust_r0cb)],
        },
    }
    (RAW_DIR / "step3_physical_units.json").write_text(js(step3), encoding="utf-8")

    # ---------------- Step 4: observed distribution + percentile position ----------------
    log_step("Step 4: observed gust distribution + percentile position of turning points...")

    def dist_summary(g: pd.Series):
        return {
            "min": float(g.min()), "p1": float(g.quantile(0.01)), "p5": float(g.quantile(0.05)),
            "p50": float(g.quantile(0.50)), "p95": float(g.quantile(0.95)), "p99": float(g.quantile(0.99)),
            "max": float(g.max()), "n": int(g.notna().sum()),
        }

    def percentile_of(value, g: pd.Series):
        return float((g < value).mean() * 100)

    step4 = {
        "E0_prime_gust_distribution_ms": dist_summary(d_e0["gust_0h"]),
        "R0c_prime_B_gust_distribution_ms": dist_summary(d_r0cb["gust_0h"]),
        "E0_prime_turning_point_percentile": percentile_of(step3["E0_prime"]["point_ms"], d_e0["gust_0h"]),
        "R0c_prime_B_turning_point_percentile": percentile_of(step3["R0c_prime_B"]["point_ms"], d_r0cb["gust_0h"]),
    }
    (RAW_DIR / "step4_distribution_and_percentile.json").write_text(js(step4), encoding="utf-8")
    log_step(f"E0' turning point percentile: {step4['E0_prime_turning_point_percentile']:.2f}")
    log_step(f"R0c'_B turning point percentile: {step4['R0c_prime_B_turning_point_percentile']:.2f}")

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
