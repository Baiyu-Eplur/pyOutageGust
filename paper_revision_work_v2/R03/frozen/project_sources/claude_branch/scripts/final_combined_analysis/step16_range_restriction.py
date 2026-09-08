"""Command #25 Step 1: range-restriction diagnostic for command #24's storm-window
fitted-vs-observed correlation attenuation, using the classic Thorndike Case 2
direct range-restriction formula.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

import statsmodels.api as sm

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

STORMS = {
    "Storm Arwen": ("2021-11-25", "2021-11-28"),
    "Storm Dudley": ("2022-02-15", "2022-02-17"),
    "Storm Eunice": ("2022-02-17", "2022-02-19"),
    "Storm Franklin": ("2022-02-19", "2022-02-22"),
    "Storm Babet": ("2023-10-17", "2023-10-22"),
    "Storm Ciaran": ("2023-10-31", "2023-11-03"),
    "Storm Henk": ("2024-01-01", "2024-01-03"),
}

# Actual observed fitted-vs-observed log-scale Pearson r from command #24
OBSERVED_R_E0 = {
    "Storm Arwen": 0.115527, "Storm Dudley": 0.294155, "Storm Eunice": 0.153248,
    "Storm Franklin": 0.123756, "Storm Babet": 0.185069, "Storm Ciaran": 0.341333,
    "Storm Henk": 0.331641,
}
OBSERVED_R_R0C = {
    "Storm Arwen": 0.249159, "Storm Dudley": 0.084079, "Storm Eunice": 0.203612,
    "Storm Franklin": 0.211295, "Storm Babet": 0.261894, "Storm Ciaran": 0.317174,
    "Storm Henk": 0.135522,
}
FULL_R_E0 = 0.179336
FULL_R_R0C = 0.342938


def log_step(msg):
    print(f"[v25-step1] {msg}", flush=True)


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


def thorndike_case2(rho_full, u):
    """Direct range restriction: given the unrestricted correlation rho_full and
    the restriction ratio u = SD_restricted / SD_unrestricted (applied to the
    predictor/selection variable), return the theoretically expected correlation
    in the restricted sample. Derivation (bivariate-normal, linear Y|X):
        rho_restricted = (u * rho_full) / sqrt(1 - rho_full^2 + u^2 * rho_full^2)
    """
    num = u * rho_full
    den = np.sqrt(max(1 - rho_full ** 2 + (u ** 2) * (rho_full ** 2), 1e-12))
    return num / den


def fit_model(train_sample, target_col, use_customers):
    s = train_sample.copy()
    extra = None
    if use_customers:
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    Xtr, _ = v9.design_train_valid(s, s, extra_scale_cols=extra)
    y = s[target_col].astype(float)
    res = sm.OLS(y, Xtr.astype(float)).fit()
    return res


def predict_for_subset(res, train_sample_for_scaling, subset, use_customers):
    s_train = train_sample_for_scaling.copy()
    s_sub = subset.copy()
    extra = None
    if use_customers:
        s_train["customers_v2_log1p"] = np.log1p(s_train["customers_v2_event_excl_reinterruptions"].astype(float))
        s_sub["customers_v2_log1p"] = np.log1p(s_sub["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    _, Xva = v9.design_train_valid(s_train, s_sub, extra_scale_cols=extra)
    exog_names = list(res.model.exog_names)
    Xva = Xva.reindex(columns=exog_names, fill_value=0.0)
    eta = Xva[exog_names].astype(float) @ res.params.loc[exog_names]
    return eta.values  # linear predictor (log scale), used directly for SD-ratio diagnostics


def main():
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    log_step("Refitting E0/R0c final models (deterministic)...")
    res_e0 = fit_model(combined_e0, "log1p_customers_v2", False)
    res_r0c = fit_model(combined_r0cb, "log_duration_B_full_span_hours", True)

    # full-sample SDs
    gust_sd_full = combined_wt["gust_0h"].std(ddof=1)
    log1p_cust_sd_full = np.log1p(combined_e0["customers_v2_event_excl_reinterruptions"].astype(float)).std(ddof=1)
    eta_e0_full = predict_for_subset(res_e0, combined_e0, combined_e0, False)
    eta_r0c_full = predict_for_subset(res_r0c, combined_r0cb, combined_r0cb, True)
    pred_e0_sd_full = np.std(eta_e0_full, ddof=1)
    pred_r0c_sd_full = np.std(eta_r0c_full, ddof=1)

    log_step(f"Full sample: SD(gust)={gust_sd_full:.3f}, SD(log1p customers_v2)={log1p_cust_sd_full:.3f}, "
              f"SD(predicted eta, E0)={pred_e0_sd_full:.3f}, SD(predicted eta, R0c)={pred_r0c_sd_full:.3f}")

    rows = []
    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        storm_events = combined_wt.loc[mask].copy()

        gust_sd_storm = storm_events["gust_0h"].std(ddof=1)
        u_gust = gust_sd_storm / gust_sd_full

        storm_e0 = storm_events.loc[storm_events["customers_v2_event_excl_reinterruptions"].notna()].copy()
        log1p_cust_sd_storm = np.log1p(storm_e0["customers_v2_event_excl_reinterruptions"].astype(float)).std(ddof=1)
        u_log1p_cust = log1p_cust_sd_storm / log1p_cust_sd_full

        eta_e0_storm = predict_for_subset(res_e0, combined_e0, storm_e0, False)
        pred_e0_sd_storm = np.std(eta_e0_storm, ddof=1)
        u_pred_e0 = pred_e0_sd_storm / pred_e0_sd_full

        storm_r0c = storm_events.loc[
            storm_events["duration_B_full_span_hours"].notna() & (storm_events["duration_B_full_span_hours"] > 0)
            & storm_events["customers_v2_event_excl_reinterruptions"].notna()
        ].copy()
        eta_r0c_storm = predict_for_subset(res_r0c, combined_r0cb, storm_r0c, True)
        pred_r0c_sd_storm = np.std(eta_r0c_storm, ddof=1)
        u_pred_r0c = pred_r0c_sd_storm / pred_r0c_sd_full

        theo_r_e0_gust = thorndike_case2(FULL_R_E0, u_gust)
        theo_r_e0_pred = thorndike_case2(FULL_R_E0, u_pred_e0)
        theo_r_r0c_gust = thorndike_case2(FULL_R_R0C, u_gust)
        theo_r_r0c_pred = thorndike_case2(FULL_R_R0C, u_pred_r0c)

        obs_r_e0 = OBSERVED_R_E0[storm]
        obs_r_r0c = OBSERVED_R_R0C[storm]

        # % of the observed drop "explained" by the theoretical (predicted-eta-based) attenuation
        full_minus_obs_e0 = FULL_R_E0 - obs_r_e0
        full_minus_theo_e0 = FULL_R_E0 - theo_r_e0_pred
        pct_explained_e0 = (full_minus_theo_e0 / full_minus_obs_e0 * 100) if full_minus_obs_e0 != 0 else np.nan

        full_minus_obs_r0c = FULL_R_R0C - obs_r_r0c
        full_minus_theo_r0c = FULL_R_R0C - theo_r_r0c_pred
        pct_explained_r0c = (full_minus_theo_r0c / full_minus_obs_r0c * 100) if full_minus_obs_r0c != 0 else np.nan

        rows.append({
            "storm": storm, "n": len(storm_events),
            "gust_sd_storm": gust_sd_storm, "gust_sd_full": gust_sd_full, "u_gust": u_gust,
            "log1p_cust_sd_storm": log1p_cust_sd_storm, "log1p_cust_sd_full": log1p_cust_sd_full,
            "u_log1p_cust": u_log1p_cust,
            "pred_eta_sd_storm_E0": pred_e0_sd_storm, "pred_eta_sd_full_E0": pred_e0_sd_full, "u_pred_E0": u_pred_e0,
            "pred_eta_sd_storm_R0c": pred_r0c_sd_storm, "pred_eta_sd_full_R0c": pred_r0c_sd_full, "u_pred_R0c": u_pred_r0c,
            "full_r_E0": FULL_R_E0, "theoretical_r_E0_using_gust_u": theo_r_e0_gust,
            "theoretical_r_E0_using_pred_u": theo_r_e0_pred, "observed_r_E0": obs_r_e0,
            "pct_of_E0_drop_explained_by_range_restriction": pct_explained_e0,
            "full_r_R0c": FULL_R_R0C, "theoretical_r_R0c_using_gust_u": theo_r_r0c_gust,
            "theoretical_r_R0c_using_pred_u": theo_r_r0c_pred, "observed_r_R0c": obs_r_r0c,
            "pct_of_R0c_drop_explained_by_range_restriction": pct_explained_r0c,
        })
        log_step(f"{storm}: u_gust={u_gust:.3f}, u_pred_E0={u_pred_e0:.3f}, u_pred_R0c={u_pred_r0c:.3f}, "
                  f"theo_r_E0={theo_r_e0_pred:.3f} (obs={obs_r_e0:.3f}), "
                  f"theo_r_R0c={theo_r_r0c_pred:.3f} (obs={obs_r_r0c:.3f})")

    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "step16_range_restriction.csv", index=False)
    print(df.to_string(index=False))
    log_step("Done.")


if __name__ == "__main__":
    main()
