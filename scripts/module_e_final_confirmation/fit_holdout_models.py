"""Command #19 Steps 1-3: fit E0/R0c on the locked_temporal_test holdout (single
fit, no internal CV), estimate critical wind speed if sample size allows, run
n_stages stratification check for customers_v2, and run variance decomposition
if sample size allows. All using the exact locked-in specs from commands #9-18.
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

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\module_e_final_confirmation")))
from build_holdout_sample import build_holdout_wt_samples  # noqa: E402

V11_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
V14_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\module_e_final_confirmation")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260825

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)

spec14 = importlib.util.spec_from_file_location("variance_decomposition_pipeline", V14_SCRIPT)
v14 = importlib.util.module_from_spec(spec14)
spec14.loader.exec_module(v14)


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
    print(f"[v19-fit] {msg}", flush=True)


def single_fit_terms(df: pd.DataFrame, target_col: str, terms_of_interest, use_customers_covariate=False):
    """Single full-sample fit (no train/valid split), using the full-sample fit
    machinery from v11 (which already handles the use_customers_covariate case)."""
    res, cov, mean_gust, sd_gust, d = v11.fit_full_sample(df, target_col, use_customers_covariate)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    rows = []
    for term, coef, s, pv in zip(res.params.index, res.params, se, p):
        if term not in terms_of_interest:
            continue
        rows.append({"term": term, "coefficient": coef, "std_error": s,
                     "ci_low": coef - 1.96 * s, "ci_high": coef + 1.96 * s, "p_value": pv})
    return pd.DataFrame(rows), res, cov, mean_gust, sd_gust, d


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_holdout_wt_samples()

    # ================= Step 1: E0 =================
    log_step("Step 1: fitting E0 on holdout (single fit)...")
    e0_rows, res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = single_fit_terms(
        e0_sample, "log1p_customers_v2", v9.TERMS_OF_INTEREST, use_customers_covariate=False)
    e0_rows.to_csv(RAW_DIR / "step1_E0_holdout_coefs.csv", index=False)
    print(e0_rows.to_string(index=False))

    n_dates_e0 = e0_sample["incident_date_utc"].dt.date.nunique()
    log_step(f"E0 holdout n={len(e0_sample)}, unique dates={n_dates_e0}")

    b1_e0 = res_e0.params["z_gust_0h"]
    b2_e0 = res_e0.params["z_gust_0h_sq"]
    var1_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h"]
    var2_e0 = cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_e0 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_e0, se_x_e0, lo_e0, hi_e0 = v11.delta_method_ci(b1_e0, b2_e0, var1_e0, var2_e0, cov12_e0)
    log_step(f"E0 turning point z={x_e0:.4f}, delta CI(z)=[{lo_e0:.4f},{hi_e0:.4f}]")

    turning_point_result = {
        "beta1": float(b1_e0), "beta2": float(b2_e0), "turning_point_z": float(x_e0),
        "delta_se": float(se_x_e0), "delta_ci_95_z": [float(lo_e0), float(hi_e0)],
        "gust_mean": float(mean_gust_e0), "gust_sd": float(sd_gust_e0),
        "point_ms": float(mean_gust_e0 + x_e0 * sd_gust_e0),
        "delta_ci_95_ms": [float(mean_gust_e0 + lo_e0 * sd_gust_e0), float(mean_gust_e0 + hi_e0 * sd_gust_e0)],
        "n_unique_dates": int(n_dates_e0), "n_events": int(len(e0_sample)),
    }

    bootstrap_done = n_dates_e0 >= 100 and len(e0_sample) >= 3000
    if bootstrap_done:
        log_step(f"Sample size adequate (n={len(e0_sample)}, {n_dates_e0} unique dates) — running bootstrap...")
        boot_e0, e0_failed = v11.bootstrap_turning_point(
            e0_sample, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
        boot_lo, boot_hi = np.percentile(boot_e0, [2.5, 97.5])
        np.savetxt(RAW_DIR / "step1_E0_bootstrap_turning_points_z.csv", boot_e0, delimiter=",")
        turning_point_result.update({
            "bootstrap_performed": True, "bootstrap_n_success": int(len(boot_e0)), "bootstrap_n_failed": int(e0_failed),
            "bootstrap_mean": float(np.mean(boot_e0)), "bootstrap_std": float(np.std(boot_e0, ddof=1)),
            "bootstrap_ci_95_z": [float(boot_lo), float(boot_hi)],
            "bootstrap_ci_95_ms": [float(mean_gust_e0 + boot_lo * sd_gust_e0), float(mean_gust_e0 + boot_hi * sd_gust_e0)],
        })
        log_step(f"Bootstrap CI(z)=[{boot_lo:.4f},{boot_hi:.4f}]")
    else:
        turning_point_result["bootstrap_performed"] = False
        turning_point_result["bootstrap_skip_reason"] = (
            f"n={len(e0_sample)} events, {n_dates_e0} unique dates — below adequacy threshold "
            f"(n>=3000 and unique_dates>=100), skipped to avoid an unreliable bootstrap estimate."
        )
        log_step("Sample size inadequate for reliable bootstrap — skipped.")

    (RAW_DIR / "step1_E0_turning_point.json").write_text(js(turning_point_result), encoding="utf-8")

    # ================= Step 2: R0c =================
    log_step("Step 2: fitting R0c on holdout (single fit)...")
    r0c_rows, res_r0c, cov_r0c, mean_gust_r0c, sd_gust_r0c, d_r0c = single_fit_terms(
        r0cb_sample, "log_duration_B_full_span_hours",
        v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, use_customers_covariate=True)
    r0c_rows.to_csv(RAW_DIR / "step2_R0c_holdout_coefs.csv", index=False)
    print(r0c_rows.to_string(index=False))
    n_dates_r0c = r0cb_sample["incident_date_utc"].dt.date.nunique()
    log_step(f"R0c holdout n={len(r0cb_sample)}, unique dates={n_dates_r0c}, p99 cap={p99_b:.2f}h")

    # ---- n_stages stratification check for customers_v2 (command #18 replication) ----
    log_step("n_stages stratification check on holdout (replicating command #18)...")
    SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
    stage_counts = pd.read_csv(SRC, usecols=["Incident Reference", "stage_row_count"], low_memory=False)
    stage_counts = stage_counts.drop_duplicates("Incident Reference").set_index("Incident Reference")["stage_row_count"]
    r0cb_sample = r0cb_sample.copy()
    r0cb_sample["stage_row_count"] = r0cb_sample["Incident Reference"].map(stage_counts)
    n_single_stage = int((r0cb_sample["stage_row_count"] == 1).sum())
    log_step(f"holdout R0c sample: {n_single_stage} single-stage events out of {len(r0cb_sample)}.")

    n_stages_check = {"n_single_stage_holdout": n_single_stage, "n_total_holdout": int(len(r0cb_sample))}
    if n_single_stage >= 500:
        single = r0cb_sample[r0cb_sample["stage_row_count"] == 1].copy()
        d_ = single[["customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours"]].dropna()
        try:
            d_["decile"] = pd.qcut(d_["customers_v2_event_excl_reinterruptions"], q=5, duplicates="drop")
        except ValueError:
            d_["decile"] = pd.qcut(d_["customers_v2_event_excl_reinterruptions"], q=3, duplicates="drop")
        bin_report = d_.groupby("decile", observed=True)["duration_B_full_span_hours"].agg(["count", "mean", "median"])
        bin_report.to_csv(RAW_DIR / "step2_holdout_single_stage_bins.csv")
        print("=== holdout single-stage customers_v2 vs duration_B bins ===")
        print(bin_report.to_string())
        n_stages_check["single_stage_bins_performed"] = True
        n_stages_check["single_stage_bins"] = bin_report.reset_index().astype(str).to_dict("records")
    else:
        n_stages_check["single_stage_bins_performed"] = False
        n_stages_check["skip_reason"] = f"only {n_single_stage} single-stage events, below 500 threshold for reliable binning"
        log_step(f"Skipping n_stages binning check — only {n_single_stage} single-stage events (< 500 threshold).")

    (RAW_DIR / "step2_n_stages_check.json").write_text(js(n_stages_check), encoding="utf-8")

    # ================= Step 3: variance decomposition (in-sample only) =================
    log_step("Step 3: variance decomposition on holdout (in-sample R^2 only — the holdout itself "
              "is already an out-of-sample population relative to the dev-sample-established spec, "
              "so no internal CV split is needed within it, per command #19 Step3).")

    def in_sample_nested_r2(df: pd.DataFrame, y_col: str, block_order: list[str], model_label: str):
        y = df[y_col].astype(float)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        Xcur, _ = v14.build_block_baseline(df, df)
        rows = []
        res = sm.OLS(y, Xcur.astype(float)).fit()
        r2_prev = 1 - float(((y - res.predict(Xcur.astype(float))) ** 2).sum()) / ss_tot
        rows.append({"model": model_label, "step": "baseline", "blocks_added": "region_SES+year_month_FE",
                     "r2_in_sample": r2_prev, "r2_in_sample_increment": None})
        for block in block_order:
            Xcur, _ = v14.BLOCK_BUILDERS[block](Xcur, Xcur.copy(), df, df)
            res = sm.OLS(y, Xcur.astype(float)).fit()
            r2 = 1 - float(((y - res.predict(Xcur.astype(float))) ** 2).sum()) / ss_tot
            rows.append({"model": model_label, "step": block, "blocks_added": block,
                         "r2_in_sample": r2, "r2_in_sample_increment": r2 - r2_prev})
            r2_prev = r2
        return pd.DataFrame(rows)

    var_decomp_done = len(e0_sample) >= 2000 and len(r0cb_sample) >= 2000
    if var_decomp_done:
        e0_var = in_sample_nested_r2(e0_sample, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_holdout")
        e0_var.to_csv(RAW_DIR / "step3_E0_holdout_variance_decomposition.csv", index=False)
        print(e0_var.to_string(index=False))

        r0c_var_a = in_sample_nested_r2(
            r0cb_sample, "log_duration_B_full_span_hours",
            ["nongust_weather", "customers", "gust"], "R0c_holdout_order_customers_then_gust")
        r0c_var_a.to_csv(RAW_DIR / "step3_R0c_holdout_order_customers_then_gust.csv", index=False)
        print(r0c_var_a.to_string(index=False))

        r0c_var_b = in_sample_nested_r2(
            r0cb_sample, "log_duration_B_full_span_hours",
            ["nongust_weather", "gust", "customers"], "R0c_holdout_order_gust_then_customers")
        r0c_var_b.to_csv(RAW_DIR / "step3_R0c_holdout_order_gust_then_customers.csv", index=False)
        print(r0c_var_b.to_string(index=False))
    else:
        log_step(f"Skipping variance decomposition — E0 n={len(e0_sample)}, R0c n={len(r0cb_sample)}, "
                  f"below 2000 threshold for reliable nested-model R^2 estimation.")
        (RAW_DIR / "step3_skip_reason.json").write_text(
            js({"performed": False, "e0_n": len(e0_sample), "r0cb_n": len(r0cb_sample)}), encoding="utf-8")

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
