"""C02-C08 repair: final unified regeneration of all core coefficient/CI/
variance-decomposition numbers on the C01-corrected data, needed to complete
Figure 10 (dev-only fold coefs, holdout-only single fit, LAD+2-way cluster on
combined) and the weather_natural subsample comparison (Figure 8 + text).

Run once; every other final-generation script in this command reads its
outputs rather than recomputing them independently.
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
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import _patch_v9, build_corrected_combined_samples  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

WT_GROUPS = {"weather_natural", "technical_asset"}


def log_step(msg):
    print(f"[final-core] {msg}", flush=True)


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


def load_v11():
    spec = importlib.util.spec_from_file_location(
        "critical_wind_speed_pipeline",
        r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
    v11 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v11)
    return v11


def coef_table(res, cov):
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    return pd.DataFrame({"term": res.params.index, "coef": res.params.values, "se": se, "p": p})


def main():
    v9, clean_sample_builder, build_holdout_sample = _patch_v9()
    v11 = load_v11()

    log_step("=== Building corrected dev / holdout / combined samples ===")
    dev_wt, dev_e0, dev_r0cb, dev_p99 = clean_sample_builder.build_clean_wt_samples()
    holdout_wt, holdout_e0, holdout_r0cb, holdout_p99 = build_holdout_sample.build_holdout_wt_samples()
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()

    # ================= 1. Combined-sample LAD single + LAD*date two-way cluster =================
    log_step("=== Combined sample: LAD single + two-way cluster (E0 & R0c) ===")
    res_e0, cov_e0_lad, gust_mean_e0, gust_sd_e0, d_e0 = v11.fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False)
    res_r0c, cov_r0c_lad, gust_mean_r0c, gust_sd_r0c, d_r0c = v11.fit_full_sample(
        combined_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)

    groups_lad_e0 = pd.factorize(d_e0["LAD21CD"])[0]
    groups_date_e0 = pd.factorize(pd.to_datetime(d_e0["incident_date_utc"]).dt.date.astype(str))[0]
    cov_both_e0, _, _ = cov_cluster_2groups(res_e0, groups_lad_e0, groups_date_e0)

    groups_lad_r0c = pd.factorize(d_r0c["LAD21CD"])[0]
    groups_date_r0c = pd.factorize(pd.to_datetime(d_r0c["incident_date_utc"]).dt.date.astype(str))[0]
    cov_both_r0c, _, _ = cov_cluster_2groups(res_r0c, groups_lad_r0c, groups_date_r0c)

    e0_lad_table = coef_table(res_e0, cov_e0_lad)
    e0_2way_table = coef_table(res_e0, cov_both_e0)
    r0c_lad_table = coef_table(res_r0c, cov_r0c_lad)
    r0c_2way_table = coef_table(res_r0c, cov_both_r0c)
    e0_lad_table.to_csv(RAW_DIR / "E0_corrected_lad_cluster.csv", index=False)
    e0_2way_table.to_csv(RAW_DIR / "E0_corrected_twoway_cluster.csv", index=False)
    r0c_lad_table.to_csv(RAW_DIR / "R0c_corrected_lad_cluster.csv", index=False)
    r0c_2way_table.to_csv(RAW_DIR / "R0c_corrected_twoway_cluster.csv", index=False)
    log_step(f"E0 gust_sq: LAD se={e0_lad_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}, "
              f"2way se={e0_2way_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}")
    log_step(f"R0c gust_sq: LAD se={r0c_lad_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}, "
              f"2way se={r0c_2way_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}")

    # ================= 2. Dev-only 5-fold coefficients (for Figure 10 "development sample") =================
    log_step("=== Dev-only 5-fold coefficient stability (E0 & R0c) ===")
    e0_dev_fold = v9.run_model(dev_e0, "log1p_customers_v2", "E0_dev_corrected",
                                 ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=False)
    r0c_dev_fold = v9.run_model(dev_r0cb, "log_duration_B_full_span_hours", "R0c_dev_corrected",
                                  ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=True)
    e0_dev_fold.to_csv(RAW_DIR / "E0_dev_corrected_fold_coefs.csv", index=False)
    r0c_dev_fold.to_csv(RAW_DIR / "R0c_dev_corrected_fold_coefs.csv", index=False)

    def pooled(fold_df, term):
        sub = fold_df[fold_df["term"] == term]
        w = 1.0 / (sub["std_error"].astype(float) ** 2)
        pooled_est = float((w * sub["coefficient"].astype(float)).sum() / w.sum())
        se = float(np.sqrt(1.0 / w.sum()))
        return pooled_est, se

    e0_dev_pooled, e0_dev_pooled_se = pooled(e0_dev_fold, "z_gust_0h_sq")
    r0c_dev_pooled, r0c_dev_pooled_se = pooled(r0c_dev_fold, "z_gust_0h_sq")
    log_step(f"Dev pooled gust_sq: E0={e0_dev_pooled:.4f}+/-{e0_dev_pooled_se:.4f}, "
              f"R0c={r0c_dev_pooled:.4f}+/-{r0c_dev_pooled_se:.4f}")

    # ================= 3. Holdout-only single fit (for Figure 10 "holdout/confirmation") =================
    log_step("=== Holdout-only single-fit coefficients (E0 & R0c) ===")
    res_e0_hold, cov_e0_hold, _, _, _ = v11.fit_full_sample(holdout_e0, "log1p_customers_v2", use_customers_covariate=False)
    res_r0c_hold, cov_r0c_hold, _, _, _ = v11.fit_full_sample(holdout_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)
    e0_hold_table = coef_table(res_e0_hold, cov_e0_hold)
    r0c_hold_table = coef_table(res_r0c_hold, cov_r0c_hold)
    e0_hold_table.to_csv(RAW_DIR / "E0_holdout_corrected_coefs.csv", index=False)
    r0c_hold_table.to_csv(RAW_DIR / "R0c_holdout_corrected_coefs.csv", index=False)
    log_step(f"Holdout gust_sq: E0={e0_hold_table.set_index('term').loc['z_gust_0h_sq','coef']:.4f}, "
              f"R0c={r0c_hold_table.set_index('term').loc['z_gust_0h_sq','coef']:.4f}")

    # ================= 4. weather_natural subsample rebuild + critical wind speed + variance decomp =================
    log_step("=== weather_natural subsample (corrected) ===")
    wn_e0 = combined_e0.loc[combined_e0["cause_group_official"] == "weather_natural"].copy()
    wn_r0cb_pre = combined_wt.loc[
        (combined_wt["cause_group_official"] == "weather_natural")
        & combined_wt["duration_B_full_span_hours"].notna() & (combined_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    wn_p99 = wn_r0cb_pre["duration_B_full_span_hours"].quantile(0.99)
    wn_r0cb = wn_r0cb_pre.loc[wn_r0cb_pre["duration_B_full_span_hours"] <= wn_p99].copy()
    wn_r0cb = wn_r0cb.loc[wn_r0cb["customers_v2_event_excl_reinterruptions"].notna()].copy()
    wn_r0cb["log_duration_B_full_span_hours"] = np.log(wn_r0cb["duration_B_full_span_hours"].astype(float))
    wn_r0cb["log1p_customers_v2"] = np.log1p(wn_r0cb["customers_v2_event_excl_reinterruptions"].astype(float))
    log_step(f"weather_natural (corrected): E0 n={len(wn_e0)}, R0c n={len(wn_r0cb)} (p99={wn_p99:.2f}h)")

    # fresh 5-fold GroupKFold within each subsample for run_model/variance decomposition
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

    wn_e0_folds = add_fresh_folds(wn_e0)
    wn_r0cb_folds = add_fresh_folds(wn_r0cb)

    spec14 = importlib.util.spec_from_file_location(
        "variance_decomposition_pipeline",
        r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
    v14 = importlib.util.module_from_spec(spec14)
    spec14.loader.exec_module(v14)

    wn_e0_var = v14.nested_r2_sequence(wn_e0_folds, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_wn_corrected")
    wn_r0c_var_gust_first = v14.nested_r2_sequence(wn_r0cb_folds, "log_duration_B_full_span_hours",
                                                     ["nongust_weather", "gust", "customers"], "R0c_wn_corrected_gust_first")
    wn_e0_var.to_csv(RAW_DIR / "E0_wn_corrected_variance_decomposition.csv", index=False)
    wn_r0c_var_gust_first.to_csv(RAW_DIR / "R0c_wn_corrected_variance_decomposition_gust_first.csv", index=False)
    log_step("weather_natural E0 variance decomposition:\n" + wn_e0_var.to_string(index=False))
    log_step("weather_natural R0c variance decomposition (gust first):\n" + wn_r0c_var_gust_first.to_string(index=False))

    # weather_natural E0 critical wind speed (point estimate + Delta CI only; bootstrap optional/expensive)
    res_e0_wn, cov_e0_wn, gust_mean_wn, gust_sd_wn, _ = v11.fit_full_sample(wn_e0, "log1p_customers_v2", use_customers_covariate=False)
    b1_wn, b2_wn = res_e0_wn.params["z_gust_0h"], res_e0_wn.params["z_gust_0h_sq"]
    var1_wn, var2_wn = cov_e0_wn.loc["z_gust_0h", "z_gust_0h"], cov_e0_wn.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12_wn = cov_e0_wn.loc["z_gust_0h", "z_gust_0h_sq"]
    x_wn, se_wn, lo_wn, hi_wn = v11.delta_method_ci(b1_wn, b2_wn, var1_wn, var2_wn, cov12_wn)
    tp_ms_wn = gust_mean_wn + x_wn * gust_sd_wn
    log_step(f"weather_natural E0 (corrected): beta1={b1_wn:.4f}, beta2={b2_wn:.4f}, "
              f"turning point z={x_wn:.4f} ({tp_ms_wn:.4f} m/s), Delta CI(z)=[{lo_wn:.4f},{hi_wn:.4f}]")

    summary = {
        "corrected_sample_sizes": {"dev_e0": len(dev_e0), "dev_r0cb": len(dev_r0cb),
                                     "holdout_e0": len(holdout_e0), "holdout_r0cb": len(holdout_r0cb),
                                     "combined_e0": len(combined_e0), "combined_r0cb": len(combined_r0cb),
                                     "wn_e0": len(wn_e0), "wn_r0cb": len(wn_r0cb), "wn_p99_cap": float(wn_p99)},
        "dev_pooled_gust_sq": {"E0": [e0_dev_pooled, e0_dev_pooled_se], "R0c": [r0c_dev_pooled, r0c_dev_pooled_se]},
        "holdout_gust_sq": {
            "E0": [float(e0_hold_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                    float(e0_hold_table.set_index("term").loc["z_gust_0h_sq", "se"])],
            "R0c": [float(r0c_hold_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                     float(r0c_hold_table.set_index("term").loc["z_gust_0h_sq", "se"])],
        },
        "combined_lad_gust_sq": {
            "E0": [float(e0_lad_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                    float(e0_lad_table.set_index("term").loc["z_gust_0h_sq", "se"])],
            "R0c": [float(r0c_lad_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                     float(r0c_lad_table.set_index("term").loc["z_gust_0h_sq", "se"])],
        },
        "combined_2way_gust_sq": {
            "E0": [float(e0_2way_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                    float(e0_2way_table.set_index("term").loc["z_gust_0h_sq", "se"])],
            "R0c": [float(r0c_2way_table.set_index("term").loc["z_gust_0h_sq", "coef"]),
                     float(r0c_2way_table.set_index("term").loc["z_gust_0h_sq", "se"])],
        },
        "weather_natural_E0_turning_point": {
            "beta1": float(b1_wn), "beta2": float(b2_wn), "z_star": float(x_wn), "ms": float(tp_ms_wn),
            "delta_ci_z": [float(lo_wn), float(hi_wn)],
        },
    }
    (RAW_DIR / "final_core_summary.json").write_text(js(summary), encoding="utf-8")
    log_step("Saved final_core_summary.json and all component CSVs.")
    log_step("=== final_core_tables.py complete ===")


if __name__ == "__main__":
    main()
