"""Command #25 Steps 2-4: build the weather_natural-only subsample (from command
#21's final combined sample), refit E0/R0c, run variance decomposition, and
re-estimate the critical wind speed -- all compared against the main
weather_natural+technical_asset specification.
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
import statsmodels.api as sm
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(project_path('scripts/dev_sample_decontamination')))
from clean_sample_builder import v9  # noqa: E402

V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
V14_SCRIPT = project_path('scripts/variance_decomposition/variance_decomposition_pipeline.py')
OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260827

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)

spec14 = importlib.util.spec_from_file_location("variance_decomposition_pipeline", V14_SCRIPT)
v14 = importlib.util.module_from_spec(spec14)
spec14.loader.exec_module(v14)


def log_step(msg):
    print(f"[v25-wn] {msg}", flush=True)


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


def add_fresh_folds(df: pd.DataFrame, n_splits: int) -> pd.DataFrame:
    d = df.copy()
    d["incident_date_utc"] = pd.to_datetime(d["incident_date_utc"], errors="coerce")
    gkf = GroupKFold(n_splits=n_splits)
    d["cv_fold_v3"] = -1
    groups = d["incident_date_utc"].dt.date.astype(str)
    X_dummy = np.zeros(len(d))
    for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
        d.iloc[valid_idx, d.columns.get_loc("cv_fold_v3")] = fold_idx
    n_crossing = int((d.groupby(groups)["cv_fold_v3"].nunique() > 1).sum())
    log_step(f"  {n_splits}-fold: sizes={d['cv_fold_v3'].value_counts().sort_index().to_dict()}, "
              f"dates crossing folds={n_crossing}")
    assert n_crossing == 0
    return d


def main():
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()

    # ---------------- Step 2: weather_natural subsample ----------------
    log_step("Building weather_natural-only subsample...")
    wn_wt = combined_wt.loc[combined_wt["cause_group_official"] == "weather_natural"].copy()
    wn_e0 = wn_wt.loc[wn_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    wn_e0["log1p_customers_v2"] = np.log1p(wn_e0["customers_v2_event_excl_reinterruptions"].astype(float))

    wn_r0_base = wn_wt.loc[
        wn_wt["duration_B_full_span_hours"].notna() & (wn_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    wn_p99 = wn_r0_base["duration_B_full_span_hours"].quantile(0.99)
    wn_r0cb = wn_r0_base.loc[wn_r0_base["duration_B_full_span_hours"] <= wn_p99].copy()
    wn_r0cb = wn_r0cb.loc[wn_r0cb["customers_v2_event_excl_reinterruptions"].notna()].copy()
    wn_r0cb["log_duration_B_full_span_hours"] = np.log(wn_r0cb["duration_B_full_span_hours"].astype(float))
    wn_r0cb["log1p_customers_v2"] = np.log1p(wn_r0cb["customers_v2_event_excl_reinterruptions"].astype(float))

    n_unique_dates_e0 = pd.to_datetime(wn_e0["incident_date_utc"]).dt.date.nunique()
    n_unique_dates_r0c = pd.to_datetime(wn_r0cb["incident_date_utc"]).dt.date.nunique()

    sizes = {
        "wn_wt_n": int(len(wn_wt)), "wn_e0_n": int(len(wn_e0)), "wn_r0cb_n": int(len(wn_r0cb)),
        "wn_p99_cap_hours": float(wn_p99),
        "main_e0_n": int(len(combined_e0)), "main_r0cb_n": int(len(combined_r0cb)),
        "wn_e0_pct_of_main": float(len(wn_e0) / len(combined_e0) * 100),
        "wn_r0cb_pct_of_main": float(len(wn_r0cb) / len(combined_r0cb) * 100),
        "n_unique_dates_e0": int(n_unique_dates_e0), "n_unique_dates_r0c": int(n_unique_dates_r0c),
    }
    log_step(f"weather_natural: E0 n={len(wn_e0)} ({sizes['wn_e0_pct_of_main']:.1f}% of main), "
              f"R0c n={len(wn_r0cb)} ({sizes['wn_r0cb_pct_of_main']:.1f}% of main), "
              f"unique dates E0={n_unique_dates_e0}, R0c={n_unique_dates_r0c}")

    # decide fold count: 5-fold needs each fold to have enough unique dates;
    # with ~1000+ unique dates in a 3-year span this is not the limiting factor,
    # sample SIZE per fold is what matters (want >=500 events per fold as a rule
    # of thumb, consistent with project practice).
    use_n_splits = 5
    if len(wn_e0) / 5 < 500 or len(wn_r0cb) / 5 < 500:
        use_n_splits = 3
        log_step(f"Sample size per fold would be <500 events at 5-fold; using {use_n_splits}-fold instead.")
    sizes["n_folds_used"] = use_n_splits
    (RAW_DIR / "step17_sample_sizes.json").write_text(js(sizes), encoding="utf-8")

    wn_e0_folds = add_fresh_folds(wn_e0, use_n_splits)
    wn_r0cb_folds = add_fresh_folds(wn_r0cb, use_n_splits)

    # ---------------- Step 3: refit E0/R0c on weather_natural, per-fold ----------------
    log_step("Fitting E0/R0c per-fold on weather_natural subsample...")

    def run_model_nsplits(sample_with_folds, target_col, model_label, terms, use_customers, n_splits):
        rows = []
        for fold in range(n_splits):
            va = sample_with_folds["cv_fold_v3"].eq(fold)
            tr = sample_with_folds["cv_fold_v3"].ne(fold) & sample_with_folds["cv_fold_v3"].ge(0)
            fold_rows, n_train, n_valid = v9.fit_fold_terms(
                sample_with_folds.loc[tr], sample_with_folds.loc[va], target_col, terms, use_customers)
            for r in fold_rows:
                r.update({"model": model_label, "fold": fold, "n_obs_in_fold_train": n_train,
                          "n_obs_in_fold_valid": n_valid, "inference": "LAD_cluster"})
                rows.append(r)
        return pd.DataFrame(rows)

    e0_fold = run_model_nsplits(wn_e0_folds, "log1p_customers_v2", "E0_weather_natural",
                                  v9.TERMS_OF_INTEREST, False, use_n_splits)
    r0c_fold = run_model_nsplits(wn_r0cb_folds, "log_duration_B_full_span_hours", "R0c_weather_natural",
                                   v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, True, use_n_splits)
    e0_fold.to_csv(RAW_DIR / "step17_E0_weather_natural_fold_coefs.csv", index=False)
    r0c_fold.to_csv(RAW_DIR / "step17_R0c_weather_natural_fold_coefs.csv", index=False)

    def stability(fold_df):
        rows = []
        for (model, term), g in fold_df.groupby(["model", "term"]):
            n = len(g)
            n_pos, n_neg = (g["coefficient"] > 0).sum(), (g["coefficient"] < 0).sum()
            same = max(n_pos, n_neg)
            n_sig = (g["p_value"] < 0.05).sum()
            mean = g["coefficient"].mean()
            cv = float(g["coefficient"].std(ddof=1) / abs(mean) * 100) if mean != 0 else np.nan
            rows.append({"model": model, "term": term, "n_folds": n, "same_sign_folds": int(same),
                         "significant_folds": int(n_sig), "mean_coefficient": mean, "coef_cv_pct": cv})
        return pd.DataFrame(rows)

    stab = pd.concat([stability(e0_fold), stability(r0c_fold)], ignore_index=True)
    stab.to_csv(RAW_DIR / "step17_stability_summary.csv", index=False)
    print(stab.to_string(index=False))

    # full-sample fit too (for critical wind speed + point estimates)
    log_step("Full-sample fit E0/R0c on weather_natural (for point estimates + critical wind speed)...")
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = v11.fit_full_sample(
        wn_e0, "log1p_customers_v2", use_customers_covariate=False)
    res_r0c, cov_r0c, mean_gust_r0c, sd_gust_r0c, d_r0c = v11.fit_full_sample(
        wn_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)

    full_fit = {
        "E0": {"beta1": float(res_e0.params["z_gust_0h"]), "beta2": float(res_e0.params["z_gust_0h_sq"]),
               "r2": float(res_e0.rsquared)},
        "R0c": {"beta1": float(res_r0c.params["z_gust_0h"]), "beta2": float(res_r0c.params["z_gust_0h_sq"]),
                "cust1": float(res_r0c.params["z_log1p_customers_v2"]),
                "cust2": float(res_r0c.params["z_log1p_customers_v2_sq"]), "r2": float(res_r0c.rsquared)},
    }
    (RAW_DIR / "step17_full_fit.json").write_text(js(full_fit), encoding="utf-8")
    print(json.dumps(full_fit, indent=2))

    # ---------------- Step 4a: critical wind speed (E0) ----------------
    log_step("Critical wind speed on weather_natural E0...")
    b1, b2 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1, var2 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_star, se_x, lo, hi = v11.delta_method_ci(b1, b2, var1, var2, cov12)
    log_step(f"beta1={b1:.4f}, beta2={b2:.4f}, x*={x_star:.4f}, delta-CI=[{lo:.4f},{hi:.4f}]")

    boot, n_failed = v11.bootstrap_turning_point(wn_e0, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
    boot_lo, boot_hi = np.percentile(boot, [2.5, 97.5])
    np.savetxt(RAW_DIR / "step17_E0_wn_bootstrap_turning_points_z.csv", boot, delimiter=",")

    def to_ms(z):
        return mean_gust_e0 + z * sd_gust_e0

    tp_result = {
        "n": int(len(wn_e0)), "beta1": float(b1), "beta2": float(b2), "turning_point_z": float(x_star),
        "delta_ci_95_z": [float(lo), float(hi)],
        "bootstrap_n_success": int(len(boot)), "bootstrap_ci_95_z": [float(boot_lo), float(boot_hi)],
        "gust_mean": float(mean_gust_e0), "gust_sd": float(sd_gust_e0),
        "point_ms": float(to_ms(x_star)),
        "delta_ci_95_ms": [float(to_ms(lo)), float(to_ms(hi))],
        "bootstrap_ci_95_ms": [float(to_ms(boot_lo)), float(to_ms(boot_hi))],
    }
    gust_dist = d_e0["gust_0h"]
    tp_result["turning_point_percentile"] = float((gust_dist < tp_result["point_ms"]).mean() * 100)
    (RAW_DIR / "step17_critical_wind_speed.json").write_text(js(tp_result), encoding="utf-8")
    print(json.dumps(tp_result, indent=2))

    # ---------------- Step 4b: variance decomposition ----------------
    log_step("Variance decomposition on weather_natural subsample...")
    e0_var = v14.nested_r2_sequence(wn_e0_folds, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_wn")
    e0_var.to_csv(RAW_DIR / "step17_E0_variance_decomposition.csv", index=False)
    print(e0_var.to_string(index=False))

    r0c_var_a = v14.nested_r2_sequence(
        wn_r0cb_folds, "log_duration_B_full_span_hours",
        ["nongust_weather", "customers", "gust"], "R0c_wn_order_customers_then_gust")
    r0c_var_a.to_csv(RAW_DIR / "step17_R0c_order_customers_then_gust.csv", index=False)
    print(r0c_var_a.to_string(index=False))

    r0c_var_b = v14.nested_r2_sequence(
        wn_r0cb_folds, "log_duration_B_full_span_hours",
        ["nongust_weather", "gust", "customers"], "R0c_wn_order_gust_then_customers")
    r0c_var_b.to_csv(RAW_DIR / "step17_R0c_order_gust_then_customers.csv", index=False)
    print(r0c_var_b.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
