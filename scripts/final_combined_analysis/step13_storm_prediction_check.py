"""Command #24: fitted-vs-observed prediction check for the 7 named storms,
using command #21's final combined-sample E0/R0c models (refit deterministically,
not reloaded from a serialized object -- same code path guarantees identical
coefficients), compared against the full-sample baseline correlation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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


def log_step(msg):
    print(f"[v24] {msg}", flush=True)


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


def fit_model(train_sample, target_col, use_customers):
    s = train_sample.copy()
    extra = None
    if use_customers:
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    Xtr, _ = v9.design_train_valid(s, s, extra_scale_cols=extra)
    y = s[target_col].astype(float)
    res = sm.OLS(y, Xtr.astype(float)).fit()
    return res, s


def predict_for_subset(res, train_sample_for_scaling, subset, target_col, use_customers, obs_col):
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
    predicted_level = np.exp(eta)
    observed_level = s_sub[obs_col].astype(float)
    return predicted_level.values, observed_level.values, eta.values


def corr_stats(pred, obs, log_scale_pred, log_scale_obs):
    n = len(pred)
    if n < 3:
        return {"n": n, "pearson_r_level": np.nan, "pearson_r_log": np.nan,
                "mae_level": np.nan, "mae_log": np.nan, "note": "n<3, correlation not meaningful"}
    pear_level = stats.pearsonr(pred, obs)
    pear_log = stats.pearsonr(log_scale_pred, log_scale_obs)
    mae_level = float(np.mean(np.abs(pred - obs)))
    mae_log = float(np.mean(np.abs(log_scale_pred - log_scale_obs)))
    return {
        "n": n, "pearson_r_level": float(pear_level.statistic), "pearson_p_level": float(pear_level.pvalue),
        "pearson_r_log": float(pear_log.statistic), "pearson_p_log": float(pear_log.pvalue),
        "mae_level": mae_level, "mae_log": mae_log,
    }


def main():
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()

    log_step("Refitting E0 and R0c final models (deterministic, matches command #21 Step1 exactly)...")
    res_e0, e0_scaled = fit_model(combined_e0, "log1p_customers_v2", False)
    res_r0c, r0c_scaled = fit_model(combined_r0cb, "log_duration_B_full_span_hours", True)

    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    all_rows = []
    plot_data_e0 = []
    plot_data_r0c = []

    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        storm_events = combined_wt.loc[mask].copy()

        # --- E0: subset must have customers_v2 non-missing ---
        storm_e0 = storm_events.loc[storm_events["customers_v2_event_excl_reinterruptions"].notna()].copy()
        pred_e0, obs_e0, eta_e0 = predict_for_subset(
            res_e0, combined_e0, storm_e0, "log1p_customers_v2", False,
            "customers_v2_event_excl_reinterruptions")
        log_obs_e0 = np.log1p(obs_e0)
        log_pred_e0 = np.log1p(pred_e0)
        stats_e0 = corr_stats(pred_e0, obs_e0, log_pred_e0, log_obs_e0)
        stats_e0.update({"storm": storm, "model": "E0_customers_v2"})
        all_rows.append(stats_e0)
        for p, o in zip(pred_e0, obs_e0):
            plot_data_e0.append({"storm": storm, "predicted": p, "observed": o})

        # --- R0c: subset must have duration_B>0 and customers_v2 non-missing ---
        storm_r0c = storm_events.loc[
            storm_events["duration_B_full_span_hours"].notna() & (storm_events["duration_B_full_span_hours"] > 0)
            & storm_events["customers_v2_event_excl_reinterruptions"].notna()
        ].copy()
        pred_r0c, obs_r0c, eta_r0c = predict_for_subset(
            res_r0c, combined_r0cb, storm_r0c, "log_duration_B_full_span_hours", True,
            "duration_B_full_span_hours")
        log_obs_r0c = np.log(obs_r0c)
        log_pred_r0c = np.log(pred_r0c)
        stats_r0c = corr_stats(pred_r0c, obs_r0c, log_pred_r0c, log_obs_r0c)
        stats_r0c.update({"storm": storm, "model": "R0c_duration_B"})
        all_rows.append(stats_r0c)
        for p, o in zip(pred_r0c, obs_r0c):
            plot_data_r0c.append({"storm": storm, "predicted": p, "observed": o})

        log_step(f"{storm}: E0 n={stats_e0['n']} r_log={stats_e0.get('pearson_r_log', np.nan):.3f}; "
                  f"R0c n={stats_r0c['n']} r_log={stats_r0c.get('pearson_r_log', np.nan):.3f}")

    # --- full-sample baseline (Step 3) ---
    pred_e0_full, obs_e0_full, _ = predict_for_subset(
        res_e0, combined_e0, combined_e0, "log1p_customers_v2", False,
        "customers_v2_event_excl_reinterruptions")
    stats_e0_full = corr_stats(pred_e0_full, obs_e0_full, np.log1p(pred_e0_full), np.log1p(obs_e0_full))
    stats_e0_full.update({"storm": "FULL_SAMPLE", "model": "E0_customers_v2"})
    all_rows.append(stats_e0_full)

    pred_r0c_full, obs_r0c_full, _ = predict_for_subset(
        res_r0c, combined_r0cb, combined_r0cb, "log_duration_B_full_span_hours", True,
        "duration_B_full_span_hours")
    stats_r0c_full = corr_stats(pred_r0c_full, obs_r0c_full, np.log(pred_r0c_full), np.log(obs_r0c_full))
    stats_r0c_full.update({"storm": "FULL_SAMPLE", "model": "R0c_duration_B"})
    all_rows.append(stats_r0c_full)

    log_step(f"FULL SAMPLE: E0 n={stats_e0_full['n']} r_log={stats_e0_full['pearson_r_log']:.3f}; "
              f"R0c n={stats_r0c_full['n']} r_log={stats_r0c_full['pearson_r_log']:.3f}")

    result_df = pd.DataFrame(all_rows)
    result_df.to_csv(OUT_DIR / "13_风暴期预测检验.csv", index=False)
    print(result_df.to_string(index=False))

    # ---------------- scatter plots ----------------
    colors = plt.cm.tab10(np.linspace(0, 1, len(STORMS)))
    storm_color = dict(zip(STORMS.keys(), colors))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    df_e0 = pd.DataFrame(plot_data_e0)
    df_r0c = pd.DataFrame(plot_data_r0c)

    for storm in STORMS:
        sub = df_e0[df_e0["storm"] == storm]
        axes[0].scatter(np.log1p(sub["observed"]), np.log1p(sub["predicted"]),
                         s=14, alpha=0.6, color=storm_color[storm], label=storm)
    lims0 = [min(np.log1p(df_e0["observed"]).min(), np.log1p(df_e0["predicted"]).min()),
             max(np.log1p(df_e0["observed"]).max(), np.log1p(df_e0["predicted"]).max())]
    axes[0].plot(lims0, lims0, color="grey", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Observed log1p(customers_v2)")
    axes[0].set_ylabel("Predicted log1p(customers_v2)")
    axes[0].set_title("E0: fitted vs observed (storm events)")

    for storm in STORMS:
        sub = df_r0c[df_r0c["storm"] == storm]
        axes[1].scatter(np.log(sub["observed"]), np.log(sub["predicted"]),
                         s=14, alpha=0.6, color=storm_color[storm], label=storm)
    lims1 = [min(np.log(df_r0c["observed"]).min(), np.log(df_r0c["predicted"]).min()),
             max(np.log(df_r0c["observed"]).max(), np.log(df_r0c["predicted"]).max())]
    axes[1].plot(lims1, lims1, color="grey", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Observed log(duration_B)")
    axes[1].set_ylabel("Predicted log(duration_B)")
    axes[1].set_title("R0c: fitted vs observed (storm events)")
    axes[1].legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0))

    plt.tight_layout()
    fig.savefig(OUT_DIR / "13_风暴期预测检验散点图.png", dpi=600, bbox_inches="tight")
    fig.savefig(OUT_DIR / "13_风暴期预测检验散点图.pdf", bbox_inches="tight")
    plt.close(fig)

    (RAW_DIR / "step13_summary.json").write_text(js(all_rows), encoding="utf-8")
    log_step("Done.")


if __name__ == "__main__":
    main()
