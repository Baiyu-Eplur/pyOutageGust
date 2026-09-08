"""Command #37 Figure 9: restyled storm-period fitted-vs-observed scatter.

Command #24's original file (13_风暴期预测检验散点图.png) has an in-figure
title, 7-8pt default fonts, and a default (non-colorblind-checked) tab10
palette -- all of which violate the unified figure_style.py spec established
in commands #33/#34. This script therefore regenerates the plot rather than
reusing the file as-is. The underlying numbers are NOT new: it reuses the
exact same deterministic refit-and-predict logic as command #24's
step13_storm_prediction_check.py (same final combined-sample E0/R0c models,
same storm date windows), which is guaranteed to reproduce identical
predicted/observed values -- this is a restyle, not a new analysis."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

STORMS = {
    "Arwen": ("2021-11-25", "2021-11-28"),
    "Dudley": ("2022-02-15", "2022-02-17"),
    "Eunice": ("2022-02-17", "2022-02-19"),
    "Franklin": ("2022-02-19", "2022-02-22"),
    "Babet": ("2023-10-17", "2023-10-22"),
    "Ciaran": ("2023-10-31", "2023-11-03"),
    "Henk": ("2024-01-01", "2024-01-03"),
}
# Wong (2011) colorblind-safe qualitative palette (7 colours, no red-green pair)
STORM_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]


def log_step(msg):
    print(f"[fig9] {msg}", flush=True)


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


def predict_for_subset(res, train_sample_for_scaling, subset, use_customers, obs_col):
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
    return np.exp(eta).values, s_sub[obs_col].astype(float).values


def main():
    apply_style()
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    log_step("Refitting E0/R0c final models (deterministic, identical to command #21/#24)...")
    res_e0, _ = fit_model(combined_e0, "log1p_customers_v2", False)
    res_r0c, _ = fit_model(combined_r0cb, "log_duration_B_full_span_hours", True)

    rows_e0, rows_r0c = [], []
    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        storm_events = combined_wt.loc[mask].copy()

        storm_e0 = storm_events.loc[storm_events["customers_v2_event_excl_reinterruptions"].notna()].copy()
        pred_e0, obs_e0 = predict_for_subset(res_e0, combined_e0, storm_e0, False,
                                              "customers_v2_event_excl_reinterruptions")
        for p, o in zip(pred_e0, obs_e0):
            rows_e0.append({"storm": storm, "predicted": p, "observed": o})

        storm_r0c = storm_events.loc[
            storm_events["duration_B_full_span_hours"].notna() & (storm_events["duration_B_full_span_hours"] > 0)
            & storm_events["customers_v2_event_excl_reinterruptions"].notna()
        ].copy()
        pred_r0c, obs_r0c = predict_for_subset(res_r0c, combined_r0cb, storm_r0c, True,
                                                "duration_B_full_span_hours")
        for p, o in zip(pred_r0c, obs_r0c):
            rows_r0c.append({"storm": storm, "predicted": p, "observed": o})
        log_step(f"{storm}: E0 n={len(pred_e0)}, R0c n={len(pred_r0c)}")

    df_e0 = pd.DataFrame(rows_e0)
    df_r0c = pd.DataFrame(rows_r0c)

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.46))

    storm_color = dict(zip(STORMS.keys(), STORM_COLORS))

    ax = axes[0]
    for storm in STORMS:
        sub = df_e0[df_e0["storm"] == storm]
        ax.scatter(np.log1p(sub["observed"]), np.log1p(sub["predicted"]), s=8, alpha=0.55,
                   color=storm_color[storm], label=storm, linewidths=0)
    lims = [min(np.log1p(df_e0["observed"]).min(), np.log1p(df_e0["predicted"]).min()),
            max(np.log1p(df_e0["observed"]).max(), np.log1p(df_e0["predicted"]).max())]
    ax.plot(lims, lims, color="#888888", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Observed log(1 + affected customers)")
    ax.set_ylabel("Predicted log(1 + affected customers)")
    ax.text(0.05, 0.95, "E0 (exposure)", transform=ax.transAxes, fontsize=9,
             va="top", ha="left", color="#444444")
    panel_label(ax, "(a)")

    ax = axes[1]
    for storm in STORMS:
        sub = df_r0c[df_r0c["storm"] == storm]
        ax.scatter(np.log(sub["observed"]), np.log(sub["predicted"]), s=8, alpha=0.55,
                   color=storm_color[storm], label=storm, linewidths=0)
    lims = [min(np.log(df_r0c["observed"]).min(), np.log(df_r0c["predicted"]).min()),
            max(np.log(df_r0c["observed"]).max(), np.log(df_r0c["predicted"]).max())]
    ax.plot(lims, lims, color="#888888", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Observed log(restoration duration)")
    ax.set_ylabel("Predicted log(restoration duration)")
    ax.text(0.05, 0.95, "R0c (recovery)", transform=ax.transAxes, fontsize=9,
             va="top", ha="left", color="#444444")
    panel_label(ax, "(b)")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
              markerscale=1.8, title="Storm")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_9_storm_validation")
    plt.close(fig)
    log_step("Saved Figure_9_storm_validation.")


if __name__ == "__main__":
    main()
