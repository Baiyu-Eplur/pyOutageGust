"""Command #28: storm weight share + counterfactual transportability analysis
(weather_natural gust coefficients applied to the full main-spec sample)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402

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

# weather_natural (command #25) full-sample fit coefficients, from raw/step17_full_fit.json
WN_E0_BETA1, WN_E0_BETA2 = 0.13432627915130949, 0.04189580887816403
WN_R0C_BETA1, WN_R0C_BETA2 = 0.2306849358527267, 0.08241130160446283

# main-spec (command #21) full-sample fit coefficients, from raw/step1_meta.json /
# step1_E0_final_full_coefs.csv / step1_R0c_final_full_coefs.csv
MAIN_E0_BETA1, MAIN_E0_BETA2 = -0.032326, 0.102762
MAIN_R0C_BETA1, MAIN_R0C_BETA2 = 0.000198, 0.079237

# naive/legacy-style full six-Cause-Code-group coefficients for the robustness
# check in Step 3, from command #10's raw_fold_coefs (R0_naive_large_sample,
# stability_summary_naive.csv mean_coefficient) and E0_naive equivalent
NAIVE_E0_BETA1, NAIVE_E0_BETA2 = -0.030349, 0.064642
NAIVE_R0C_BETA1, NAIVE_R0C_BETA2 = 0.031699, 0.043270


def log_step(msg):
    print(f"[v28] {msg}", flush=True)


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


def main():
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    # ================= Step 1: storm weight share =================
    log_step("Step 1: storm weight share...")
    total_customers = combined_e0["customers_v2_event_excl_reinterruptions"].sum()
    total_events = len(combined_wt)
    study_start = combined_wt["incident_date_utc"].min()
    study_end = combined_wt["incident_date_utc"].max()
    total_days = (study_end - study_start).days + 1

    storm_customers_sum = 0.0
    storm_events_sum = 0
    storm_days_sum = 0
    storm_rows = []
    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        sub = combined_wt.loc[mask]
        sub_e0 = sub.loc[sub["customers_v2_event_excl_reinterruptions"].notna()]
        c_sum = sub_e0["customers_v2_event_excl_reinterruptions"].sum()
        n_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
        storm_customers_sum += c_sum
        storm_events_sum += len(sub)
        storm_days_sum += n_days
        storm_rows.append({"storm": storm, "n_events": len(sub), "customers_v2_sum": float(c_sum), "n_days": n_days})

    step1 = {
        "total_customers_v2_full_sample": float(total_customers),
        "storm_customers_v2_sum": float(storm_customers_sum),
        "pct_customers_v2_from_storms": float(storm_customers_sum / total_customers * 100),
        "total_events_full_sample": int(total_events),
        "storm_events_sum": int(storm_events_sum),
        "pct_events_from_storms": float(storm_events_sum / total_events * 100),
        "total_study_days": int(total_days),
        "storm_days_sum": int(storm_days_sum),
        "pct_days_from_storms": float(storm_days_sum / total_days * 100),
        "per_storm": storm_rows,
    }
    (RAW_DIR / "step30_storm_weight.json").write_text(js(step1), encoding="utf-8")
    print(json.dumps(step1, indent=2, ensure_ascii=False))

    # ================= Step 2 & 3: counterfactual transportability =================
    log_step("Step 2-3: counterfactual transportability analysis...")

    def counterfactual_r2(sample, gust_mean_wn, gust_sd_wn, beta1, beta2, target_col):
        gust = sample["gust_0h"].astype(float)
        z = (gust - gust_mean_wn) / gust_sd_wn
        counterfactual = beta1 * z + beta2 * (z ** 2)
        var_counterfactual = counterfactual.var(ddof=1)
        y = np.log(sample[target_col].astype(float)) if "duration" in target_col else np.log1p(sample[target_col].astype(float))
        var_total = y.var(ddof=1)
        return float(var_counterfactual / var_total * 100), float(var_counterfactual), float(var_total)

    # weather_natural's OWN gust standardization (the scale its coefficients were estimated on)
    wn_mask = combined_e0["cause_group_official"] == "weather_natural"
    wn_e0 = combined_e0.loc[wn_mask]
    wn_gust_mean_e0, wn_gust_sd_e0 = wn_e0["gust_0h"].mean(), wn_e0["gust_0h"].std(ddof=1)

    wn_r0c_mask = combined_r0cb["cause_group_official"] == "weather_natural"
    wn_r0cb = combined_r0cb.loc[wn_r0c_mask]
    wn_gust_mean_r0c, wn_gust_sd_r0c = wn_r0cb["gust_0h"].mean(), wn_r0cb["gust_0h"].std(ddof=1)

    log_step(f"weather_natural gust stats: E0 mean={wn_gust_mean_e0:.3f} sd={wn_gust_sd_e0:.3f}, "
              f"R0c mean={wn_gust_mean_r0c:.3f} sd={wn_gust_sd_r0c:.3f}")

    # E0 counterfactual (applying weather_natural E0 coefficients to full E0 sample)
    e0_cf_pct, e0_cf_var, e0_total_var = counterfactual_r2(
        combined_e0, wn_gust_mean_e0, wn_gust_sd_e0, WN_E0_BETA1, WN_E0_BETA2, "customers_v2_event_excl_reinterruptions")
    # R0c counterfactual
    r0c_cf_pct, r0c_cf_var, r0c_total_var = counterfactual_r2(
        combined_r0cb, wn_gust_mean_r0c, wn_gust_sd_r0c, WN_R0C_BETA1, WN_R0C_BETA2, "duration_B_full_span_hours")

    # actual full-sample own gust marginal R^2 contribution, from command #21/#16 variance decomposition
    # (E0 ~1.02-1.83pp on a ~3.2-5.1% total R^2 base depending on in-sample/OOS; R0c ~0.62-0.96pp on ~11-12% total)
    ACTUAL_E0_MARGINAL_PCT = 1.83  # in-sample increment, pp of total variance explained (matches command #21 Step2 report)
    ACTUAL_R0C_MARGINAL_PCT_LOW, ACTUAL_R0C_MARGINAL_PCT_HIGH = 0.62, 0.96

    step2 = {
        "assumption_disclosure": (
            "This counterfactual assumes the weather_natural-estimated gust dose-response "
            "coefficients are TRANSPORTABLE to the full main-spec population (i.e., the same "
            "physical gust effect applies to technical_asset and other Cause Code groups, just "
            "masked there by other dominant factors). This is an UNTESTABLE assumption given the "
            "available data -- it is NOT established fact, only a counterfactual premise."
        ),
        "E0": {
            "wn_beta1": WN_E0_BETA1, "wn_beta2": WN_E0_BETA2,
            "wn_gust_mean": float(wn_gust_mean_e0), "wn_gust_sd": float(wn_gust_sd_e0),
            "counterfactual_gust_variance": e0_cf_var, "total_outcome_variance_log1p": e0_total_var,
            "counterfactual_pct_of_variance": e0_cf_pct,
            "actual_marginal_pct_main_spec": ACTUAL_E0_MARGINAL_PCT,
            "ratio_counterfactual_to_actual": e0_cf_pct / ACTUAL_E0_MARGINAL_PCT,
            "reliability_caveat": (
                "command #25 found the weather_natural E0 quadratic term statistically unreliable "
                "(CV=118%, only 1/5 folds significant) and its turning point falls at the 0.97th "
                "percentile of the observed gust distribution (extreme extrapolation, negative "
                "physically-impossible CI bounds). This counterfactual therefore inherits that "
                "unreliability: the E0 beta1/beta2 values used here are themselves poorly estimated, "
                "so this number should be treated as illustrative at best, not a credible estimate."
            ),
        },
        "R0c": {
            "wn_beta1": WN_R0C_BETA1, "wn_beta2": WN_R0C_BETA2,
            "wn_gust_mean": float(wn_gust_mean_r0c), "wn_gust_sd": float(wn_gust_sd_r0c),
            "counterfactual_gust_variance": r0c_cf_var, "total_outcome_variance_log": r0c_total_var,
            "counterfactual_pct_of_variance": r0c_cf_pct,
            "actual_marginal_pct_main_spec_range": [ACTUAL_R0C_MARGINAL_PCT_LOW, ACTUAL_R0C_MARGINAL_PCT_HIGH],
            "ratio_counterfactual_to_actual_range": [
                r0c_cf_pct / ACTUAL_R0C_MARGINAL_PCT_HIGH, r0c_cf_pct / ACTUAL_R0C_MARGINAL_PCT_LOW,
            ],
        },
    }
    (RAW_DIR / "step31_counterfactual.json").write_text(js(step2), encoding="utf-8")
    print(json.dumps(step2, indent=2, ensure_ascii=False))

    # ================= Step 3: robustness to which subsample's coefficients are used =================
    log_step("Step 3: robustness check using main-spec and naive/legacy coefficients instead...")

    def counterfactual_with_own_scale(sample, beta1, beta2, target_col, own_gust_mean, own_gust_sd):
        gust = sample["gust_0h"].astype(float)
        z = (gust - own_gust_mean) / own_gust_sd
        counterfactual = beta1 * z + beta2 * (z ** 2)
        var_counterfactual = counterfactual.var(ddof=1)
        y = np.log(sample[target_col].astype(float)) if "duration" in target_col else np.log1p(sample[target_col].astype(float))
        var_total = y.var(ddof=1)
        return float(var_counterfactual / var_total * 100)

    full_gust_mean_e0, full_gust_sd_e0 = combined_e0["gust_0h"].mean(), combined_e0["gust_0h"].std(ddof=1)
    full_gust_mean_r0c, full_gust_sd_r0c = combined_r0cb["gust_0h"].mean(), combined_r0cb["gust_0h"].std(ddof=1)

    robustness = {
        "E0": {
            "using_weather_natural_coefs_on_wn_scale": e0_cf_pct,
            "using_main_spec_own_coefs_on_full_scale": counterfactual_with_own_scale(
                combined_e0, MAIN_E0_BETA1, MAIN_E0_BETA2, "customers_v2_event_excl_reinterruptions",
                full_gust_mean_e0, full_gust_sd_e0),
            "using_naive_six_group_coefs_on_full_scale": counterfactual_with_own_scale(
                combined_e0, NAIVE_E0_BETA1, NAIVE_E0_BETA2, "customers_v2_event_excl_reinterruptions",
                full_gust_mean_e0, full_gust_sd_e0),
        },
        "R0c": {
            "using_weather_natural_coefs_on_wn_scale": r0c_cf_pct,
            "using_main_spec_own_coefs_on_full_scale": counterfactual_with_own_scale(
                combined_r0cb, MAIN_R0C_BETA1, MAIN_R0C_BETA2, "duration_B_full_span_hours",
                full_gust_mean_r0c, full_gust_sd_r0c),
            "using_naive_six_group_coefs_on_full_scale": counterfactual_with_own_scale(
                combined_r0cb, NAIVE_R0C_BETA1, NAIVE_R0C_BETA2, "duration_B_full_span_hours",
                full_gust_mean_r0c, full_gust_sd_r0c),
        },
    }
    (RAW_DIR / "step32_robustness.json").write_text(js(robustness), encoding="utf-8")
    print(json.dumps(robustness, indent=2, ensure_ascii=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
