"""Command #52: relabeled copy of figure9_storm_validation.py. Changes:
"E0 (exposure)" -> "Exposure margin"; "R0c (recovery)\nopen triangles..." ->
"Recovery margin\nopen triangles..."; "excluded by p99 truncation" ->
"excluded by 99th-percentile truncation" (matches the paper's own prose,
which never abbreviates this as "p99"). No data, model, or statistics
changed -- this is the same deterministic refit as the original script."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = result_path('c02_c08_repair_20260905/raw')
OUT_DIR = result_path('figure_relabel_20260906/figures')
OUT_DIR.mkdir(parents=True, exist_ok=True)

STORMS = {
    "Arwen": ("2021-11-25", "2021-11-28"), "Dudley": ("2022-02-15", "2022-02-17"),
    "Eunice": ("2022-02-17", "2022-02-19"), "Franklin": ("2022-02-19", "2022-02-22"),
    "Babet": ("2023-10-17", "2023-10-22"), "Ciaran": ("2023-10-31", "2023-11-03"),
    "Henk": ("2024-01-01", "2024-01-03"),
}
STORM_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]


def log_step(msg):
    print(f"[fig9-relabel] {msg}", flush=True)


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
    return eta.values, s_sub[obs_col].astype(float).values


def main():
    apply_style()
    v9, _, _ = _patch_v9()
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    r0c_p99_cap = combined_r0cb["duration_B_full_span_hours"].max()
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
                  f"({n_excluded} excluded by 99th-percentile truncation, i.e. duration_B > {r0c_p99_cap:.1f}h)")

    df_e0 = pd.DataFrame(rows_e0)
    df_r0c = pd.DataFrame(rows_r0c)

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
        r0c_summary_rows.append({"storm": storm, "subset": "excluded_by_99th_percentile_truncation", **ex_r})
    r0c_summary_rows.append({"storm": "FULL_SAMPLE", "subset": "in_training_range",
                               **corr_row(df_r0c[df_r0c["in_training_range"]])})
    r0c_summary_rows.append({"storm": "FULL_SAMPLE", "subset": "excluded_by_99th_percentile_truncation",
                               **corr_row(df_r0c[~df_r0c["in_training_range"]])})
    r0c_summary = pd.DataFrame(r0c_summary_rows)
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
    # RELABEL: "E0 (exposure)" -> "Exposure margin"
    ax.text(0.05, 0.95, "Exposure margin", transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#444444")
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
    # RELABEL: "R0c (recovery)" -> "Recovery margin"; "p99 truncation" -> "99th-percentile truncation"
    ax.text(0.05, 0.95, "Recovery margin\nopen triangles = excluded by 99th-percentile truncation",
             transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#444444")
    panel_label(ax, "(b)")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
              markerscale=1.8, title="Storm")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_9_storm_validation")
    plt.close(fig)
    log_step("Saved Figure_9_storm_validation (relabeled).")


if __name__ == "__main__":
    main()
