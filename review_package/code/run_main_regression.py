"""Fit the E0 exposure and R0c recovery models on the corrected analysis samples.

Outputs include coefficient tables with LAD and LAD-by-date clustered standard
errors, and the E0 gust turning point. Source references and package adaptations
are documented in PROVENANCE.md.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups

DATA_DIR = result_path("review_package/data")
RESULTS_DIR = result_path("review_package/regression")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SCALE_COLS = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]


def log_step(msg):
    print(f"[main-regression] {msg}", flush=True)


# Build training and validation matrices using training-sample scaling.
def design_train_valid(train: pd.DataFrame, valid: pd.DataFrame, extra_scale_cols=None):
    tr = train.copy()
    va = valid.copy()
    extra_scale_cols = extra_scale_cols or []
    for c in SCALE_COLS + extra_scale_cols:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        if not np.isfinite(sd) or sd == 0:
            raise ValueError(f"zero/invalid training SD: {c}")
        tr["z_" + c] = (tr[c] - mu) / sd
        va["z_" + c] = (va[c] - mu) / sd
    for x in (tr, va):
        x["z_gust_0h_sq"] = x["z_gust_0h"] ** 2
        x["z_gust_pressure"] = x["z_gust_0h"] * x["z_pressure_msl_0h"]
        if "customers_v2_log1p" in extra_scale_cols:
            x["z_log1p_customers_v2_sq"] = x["z_customers_v2_log1p"] ** 2

    cols = ["Intercept", "z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
            "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
            "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    if "customers_v2_log1p" in extra_scale_cols:
        cols += ["z_customers_v2_log1p", "z_log1p_customers_v2_sq"]

    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in cols[1:]:
        Xtr[c] = tr[c].astype(float)
        Xva[c] = va[c].astype(float)
    for c in ["incident_year", "incident_month"]:
        levels = sorted(pd.Series(tr[c].dropna().unique()).tolist())
        for level in levels[1:]:
            name = f"{c}[{level}]"
            Xtr[name] = (tr[c] == level).astype(float)
            Xva[name] = (va[c] == level).astype(float)

    # rename z_customers_v2_log1p -> the term-of-interest name used for reporting
    rename_map = {"z_customers_v2_log1p": "z_log1p_customers_v2"}
    Xtr = Xtr.rename(columns=rename_map)
    Xva = Xva.rename(columns=rename_map)
    return Xtr.astype(float), Xva.astype(float)


# Fit OLS with full-sample scaling and LAD-clustered covariance.
def fit_full_sample(df: pd.DataFrame, target_col: str, use_customers_covariate: bool):
    d = df.copy()
    extra_scale_cols = None
    if use_customers_covariate:
        d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
        extra_scale_cols = ["customers_v2_log1p"]
    Xfull, _ = design_train_valid(d, d, extra_scale_cols=extra_scale_cols)
    y = d[target_col].astype(float)
    res = sm.OLS(y, Xfull).fit()
    groups_lad = pd.factorize(d["LAD21CD"])[0]
    cov = cov_cluster(res, groups_lad)
    cov_df = pd.DataFrame(cov, index=res.params.index, columns=res.params.index)
    gust_mean = d["gust_0h"].mean()
    gust_sd = d["gust_0h"].std(ddof=1)
    return res, cov_df, gust_mean, gust_sd, d


# Report coefficients, clustered standard errors and normal-based p-values.
def coef_table(res, cov):
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    return pd.DataFrame({"term": res.params.index, "coef": res.params.values, "se": se, "p": p})


def main():
    log_step("Loading final analysis samples via the pretest input resolver ...")
    combined_e0 = pd.read_csv(read_input(DATA_DIR / "combined_E0_final.csv"))
    combined_r0cb = pd.read_csv(read_input(DATA_DIR / "combined_R0c_final.csv"))
    log_step(f"combined_E0_final.csv: n={len(combined_e0)}")
    log_step(f"combined_R0c_final.csv: n={len(combined_r0cb)}")

    # Fit both models and calculate LAD-by-date clustered covariance.
    log_step("=== Combined sample: LAD single + two-way cluster (E0 & R0c) ===")
    res_e0, cov_e0_lad, gust_mean_e0, gust_sd_e0, d_e0 = fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False)
    res_r0c, cov_r0c_lad, gust_mean_r0c, gust_sd_r0c, d_r0c = fit_full_sample(
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
    e0_lad_table.to_csv(RESULTS_DIR / "E0_corrected_lad_cluster.csv", index=False)
    e0_2way_table.to_csv(RESULTS_DIR / "E0_corrected_twoway_cluster.csv", index=False)
    r0c_lad_table.to_csv(RESULTS_DIR / "R0c_corrected_lad_cluster.csv", index=False)
    r0c_2way_table.to_csv(RESULTS_DIR / "R0c_corrected_twoway_cluster.csv", index=False)
    log_step(f"E0 gust_sq: LAD se={e0_lad_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}, "
              f"2way se={e0_2way_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}")
    log_step(f"R0c gust_sq: LAD se={r0c_lad_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}, "
              f"2way se={r0c_2way_table.set_index('term').loc['z_gust_0h_sq','se']:.4f}")

    # E0 gust turning point at mean pressure, converted from z units to m/s.
    b1 = res_e0.params["z_gust_0h"]
    b2 = res_e0.params["z_gust_0h_sq"]
    x_star = -b1 / (2 * b2)
    tp_ms = gust_mean_e0 + x_star * gust_sd_e0
    log_step(f"E0 turning point: z*={x_star:.6f}, {tp_ms:.4f} m/s "
              f"(gust_mean={gust_mean_e0:.4f}, gust_sd={gust_sd_e0:.4f})")

    summary = {
        "n_E0": int(len(combined_e0)), "n_R0c": int(len(combined_r0cb)),
        "E0_turning_point_ms": float(tp_ms), "E0_turning_point_z": float(x_star),
        "E0_beta1": float(b1), "E0_beta2": float(b2),
    }
    (RESULTS_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_step(f"Saved run_summary.json and all coefficient tables to {RESULTS_DIR}")
    log_step("=== Done ===")


if __name__ == "__main__":
    main()
