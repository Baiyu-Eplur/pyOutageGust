"""Final regeneration of Figure 9 (storm-period fitted vs observed), on
C01-corrected data, with C04 and C05 fixes:

C04: predict_for_subset now returns eta (the model's own fitted value in the
outcome's fitted scale -- log1p(customers_v2) for E0, log(duration_B) for
R0c) directly, instead of exp(eta) which was then re-transformed with
log1p()/log() for plotting. For R0c, log(exp(eta))=eta exactly so the old
code was accidentally correct there; for E0, log1p(exp(eta)) != eta in
general (the two only converge for large eta), which was distorting the
predicted-value axis, especially for events with a low predicted eta. Fixed
by removing the double transform entirely: plot eta directly.

C05: R0c's storm-period validation subset previously ignored the p99
duration cap used to build the R0c training sample, silently including
events whose duration_B exceeds the model's own training-sample truncation
point (i.e. events that model never had a chance to be fit on). These are
now explicitly split into "in_training_range" (duration_B <= p99 cap,
consistent with what the model was actually fit on) and
"excluded_by_p99_truncation" (duration_B > cap), with separate correlation/
MAE statistics for each -- not pooled into one homogeneous "validation set".
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

STORMS = {
    "Arwen": ("2021-11-25", "2021-11-28"), "Dudley": ("2022-02-15", "2022-02-17"),
    "Eunice": ("2022-02-17", "2022-02-19"), "Franklin": ("2022-02-19", "2022-02-22"),
    "Babet": ("2023-10-17", "2023-10-22"), "Ciaran": ("2023-10-31", "2023-11-03"),
    "Henk": ("2024-01-01", "2024-01-03"),
}
STORM_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]


def log_step(msg):
    print(f"[fig9-final] {msg}", flush=True)


def fit_model(v9, train_sample, target_col, use_customers):
    import statsmodels.api as sm
    s = train_sample.copy()
    extra = None
    if use_customers:
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    Xtr, _ = v9.design_train_valid(s, s, extra_scale_cols=extra)
    y = s[target_col].astype(float)
    res = sm.OLS(y, Xtr.astype(float)).fit()
    return res, s


def predict_for_subset(v9, res, train_sample_for_scaling, subset, use_customers, obs_col):
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
    # C04 fix: return eta directly (the fitted-scale prediction), not exp(eta)
    return eta.values, s_sub[obs_col].astype(float).values


def main():
    apply_style()
    v9, _, _ = _patch_v9()
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    r0c_p99_cap = combined_r0cb["duration_B_full_span_hours"].max()  # the training sample is already truncated at p99
    log_step(f"R0c training-sample p99 cap (max duration_B actually used in fitting): {r0c_p99_cap:.2f}h")

    log_step("Refitting E0/R0c final models (deterministic, on corrected data)...")
    res_e0, _ = fit_model(v9, combined_e0, "log1p_customers_v2", False)
    res_r0c, _ = fit_model(v9, combined_r0cb, "log_duration_B_full_span_hours", True)

    rows_e0, rows_r0c = [], []
    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        storm_events = combined_wt.loc[mask].copy()

        storm_e0 = storm_events.loc[storm_events["customers_v2_event_excl_reinterruptions"].notna()].copy()
        eta_e0, obs_e0 = predict_for_subset(v9, res_e0, combined_e0, storm_e0, False,
                                              "customers_v2_event_excl_reinterruptions")
        for e, o in zip(eta_e0, obs_e0):
            rows_e0.append({"storm": storm, "eta_pred": e, "observed": o})

        # C05: split by whether duration_B falls within the R0c training sample's own p99 cap
        storm_r0c_all = storm_events.loc[
            storm_events["duration_B_full_span_hours"].notna() & (storm_events["duration_B_full_span_hours"] > 0)
            & storm_events["customers_v2_event_excl_reinterruptions"].notna()
        ].copy()
        eta_r0c, obs_r0c = predict_for_subset(v9, res_r0c, combined_r0cb, storm_r0c_all, True,
                                                "duration_B_full_span_hours")
        in_range = obs_r0c <= r0c_p99_cap
        for e, o, ir in zip(eta_r0c, obs_r0c, in_range):
            rows_r0c.append({"storm": storm, "eta_pred": e, "observed": o, "in_training_range": bool(ir)})
        n_excluded = int((~in_range).sum())
        log_step(f"{storm}: E0 n={len(eta_e0)}, R0c n={len(eta_r0c)} "
                  f"({n_excluded} excluded by p99 truncation, i.e. duration_B > {r0c_p99_cap:.1f}h)")

    df_e0 = pd.DataFrame(rows_e0)
    df_r0c = pd.DataFrame(rows_r0c)
    df_e0.to_csv(RAW_DIR / "figure9_E0_data_corrected.csv", index=False)
    df_r0c.to_csv(RAW_DIR / "figure9_R0c_data_corrected.csv", index=False)

    # ---- C05: separate fit statistics for in-range vs p99-excluded R0c events ----
    def corr_row(sub_df):
        if len(sub_df) < 3:
            return {"n": len(sub_df), "pearson_r": np.nan, "mae": np.nan}
        r = stats.pearsonr(sub_df["eta_pred"], np.log(sub_df["observed"]))
        mae = float(np.mean(np.abs(sub_df["eta_pred"] - np.log(sub_df["observed"]))))
        return {"n": len(sub_df), "pearson_r": float(r.statistic), "pearson_p": float(r.pvalue), "mae": mae}

    r0c_summary_rows = []
    for storm in STORMS:
        sub = df_r0c[df_r0c["storm"] == storm]
        in_r = corr_row(sub[sub["in_training_range"]])
        ex_r = corr_row(sub[~sub["in_training_range"]])
        r0c_summary_rows.append({"storm": storm, "subset": "in_training_range", **in_r})
        r0c_summary_rows.append({"storm": storm, "subset": "excluded_by_p99_truncation", **ex_r})
    r0c_summary_rows.append({"storm": "FULL_SAMPLE", "subset": "in_training_range",
                               **corr_row(df_r0c[df_r0c["in_training_range"]])})
    r0c_summary_rows.append({"storm": "FULL_SAMPLE", "subset": "excluded_by_p99_truncation",
                               **corr_row(df_r0c[~df_r0c["in_training_range"]])})
    r0c_summary = pd.DataFrame(r0c_summary_rows)
    r0c_summary.to_csv(RAW_DIR / "figure9_R0c_c05_split_summary.csv", index=False)
    log_step("R0c fit statistics split by training-range status:\n" + r0c_summary.to_string(index=False))

    # ---------------- plot ----------------
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.46))
    storm_color = dict(zip(STORMS.keys(), STORM_COLORS))

    ax = axes[0]
    for storm in STORMS:
        sub = df_e0[df_e0["storm"] == storm]
        ax.scatter(np.log1p(sub["observed"]), sub["eta_pred"], s=8, alpha=0.55,
                   color=storm_color[storm], label=storm, linewidths=0)
    lims = [min(np.log1p(df_e0["observed"]).min(), df_e0["eta_pred"].min()),
            max(np.log1p(df_e0["observed"]).max(), df_e0["eta_pred"].max())]
    ax.plot(lims, lims, color="#888888", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Observed log(1 + affected customers)")
    ax.set_ylabel("Predicted log(1 + affected customers)")
    ax.text(0.05, 0.95, "E0 (exposure)", transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#444444")
    panel_label(ax, "(a)")

    ax = axes[1]
    for storm in STORMS:
        sub_in = df_r0c[(df_r0c["storm"] == storm) & (df_r0c["in_training_range"])]
        sub_ex = df_r0c[(df_r0c["storm"] == storm) & (~df_r0c["in_training_range"])]
        ax.scatter(np.log(sub_in["observed"]), sub_in["eta_pred"], s=8, alpha=0.55,
                   color=storm_color[storm], label=storm, linewidths=0)
        if len(sub_ex):
            ax.scatter(np.log(sub_ex["observed"]), sub_ex["eta_pred"], s=14, alpha=0.9,
                       facecolors="none", edgecolors=storm_color[storm], linewidths=0.9, marker="^")
    lims = [min(np.log(df_r0c["observed"]).min(), df_r0c["eta_pred"].min()),
            max(np.log(df_r0c["observed"]).max(), df_r0c["eta_pred"].max())]
    ax.plot(lims, lims, color="#888888", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Observed log(restoration duration)")
    ax.set_ylabel("Predicted log(restoration duration)")
    ax.text(0.05, 0.95, "R0c (recovery)\nopen triangles = excluded by p99 truncation", transform=ax.transAxes,
             fontsize=9, va="top", ha="left", color="#444444")
    panel_label(ax, "(b)")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
              markerscale=1.8, title="Storm")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_9_storm_validation")
    plt.close(fig)
    log_step("Saved Figure_9_storm_validation (final, C01+C04+C05 corrected).")


if __name__ == "__main__":
    main()
