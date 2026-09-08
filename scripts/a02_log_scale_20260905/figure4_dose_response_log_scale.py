"""Command #47: A02 resolution -- Figure 4 redrawn on the log scale directly,
removing the final exponentiation step entirely (no Duan smearing, no new
bootstrap). This is a pure display change on top of the command #45 final
(C01+C07+C08 corrected) pipeline: build_curve() below is identical to
figure4_dose_response.py's version except `pred = eta` replaces
`pred = np.exp(eta)`. Gust-axis shape, turning point (10.81 m/s) and
bootstrap CI are computed exactly as before (they never depended on the
exponentiation step) and are read out fresh here, not hardcoded or reused
from a prior JSON, to confirm they are unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\a02_log_scale_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\a02_log_scale_20260905\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig4-logscale] {msg}", flush=True)


def build_curve(v9, v11, sample, target_col, use_customers, model_label):
    res, cov, gust_mean, gust_sd, d = v11.fit_full_sample(sample, target_col, use_customers_covariate=use_customers)

    gust_raw = d["gust_0h"]
    p1, p99 = gust_raw.quantile(0.01), gust_raw.quantile(0.99)
    grid_ms = np.linspace(p1, p99, 50)
    grid_z = (grid_ms - gust_mean) / gust_sd

    exog_names = list(res.model.exog_names)
    X = pd.DataFrame(0.0, index=range(len(grid_z)), columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0

    if use_customers:
        s = sample.copy()
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        Xtr_full, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    else:
        Xtr_full, _ = v9.design_train_valid(sample, sample, extra_scale_cols=None)

    means = Xtr_full.mean(axis=0)
    for c in exog_names:
        if c in ("z_gust_0h", "z_gust_0h_sq", "z_gust_pressure", "Intercept"):
            continue
        if c in ("z_log1p_customers_v2", "z_log1p_customers_v2_sq"):
            X[c] = 0.0
            continue
        if c in means.index:
            X[c] = means[c]

    X["z_gust_0h"] = grid_z
    X["z_gust_0h_sq"] = grid_z ** 2
    if "z_gust_pressure" in X.columns:
        X["z_gust_pressure"] = grid_z * means.get("z_pressure_msl_0h", 0.0)

    beta = res.params.loc[exog_names]
    eta = X[exog_names].astype(float) @ beta
    # Command #47: no exponentiation -- plot the model's own log-scale fitted
    # value (eta) directly. This is the entire fix for A02.
    pred_log = eta

    curve = pd.DataFrame({"model": model_label, "gust_ms": grid_ms, "gust_z": grid_z,
                           "predicted_log_scale": pred_log.values})
    return curve, res, cov, gust_mean, gust_sd, d


def main():
    apply_style()
    v9, clean_sample_builder, build_holdout_sample = _patch_v9()
    import importlib.util
    spec11 = importlib.util.spec_from_file_location(
        "critical_wind_speed_pipeline",
        r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
    v11 = importlib.util.module_from_spec(spec11)
    spec11.loader.exec_module(v11)

    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    log_step("Building E0 dose-response curve (log scale, customers held at z=0 -- E0 has no customers term)...")
    curve_e0, res_e0, cov_e0, gust_mean_e0, gust_sd_e0, _ = build_curve(
        v9, v11, combined_e0, "log1p_customers_v2", False, "E0_gust_dose_response")

    log_step("Building R0c dose-response curve (log scale, customers fixed at z=0)...")
    curve_r0c, res_r0c, cov_r0c, gust_mean_r0c, gust_sd_r0c, _ = build_curve(
        v9, v11, combined_r0cb, "log_duration_B_full_span_hours", True, "R0c_gust_dose_response")

    pd.concat([curve_e0, curve_r0c], ignore_index=True).to_csv(
        RAW_DIR / "figure4_dose_response_curves_log_scale.csv", index=False)

    # ---- turning point + CI, dynamically computed exactly as command #45 (unaffected by this change) ----
    b1, b2 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1, var2 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_star, se_x, lo_z, hi_z = v11.delta_method_ci(b1, b2, var1, var2, cov12)
    tp_ms = gust_mean_e0 + x_star * gust_sd_e0

    log_step("Bootstrap (500 draws, seed 20260826) for the E0 turning point (identical to command #45)...")
    boot, n_failed = v11.bootstrap_turning_point(combined_e0, "log1p_customers_v2", False, 500, 20260826)
    boot_lo_z, boot_hi_z = np.percentile(boot, [2.5, 97.5])
    boot_lo_ms = gust_mean_e0 + boot_lo_z * gust_sd_e0
    boot_hi_ms = gust_mean_e0 + boot_hi_z * gust_sd_e0
    log_step(f"Turning point z*={x_star:.4f} ({tp_ms:.4f} m/s), Bootstrap CI(ms)=[{boot_lo_ms:.4f},{boot_hi_ms:.4f}]")
    log_step("(For comparison against command #45's Figure 4: turning_point_ms and bootstrap CI "
              "must match exactly, since this change is display-only.)")

    from scipy import stats as sstats
    r0c_gust_sq_z = res_r0c.params["z_gust_0h_sq"] / (cov_r0c.loc["z_gust_0h_sq", "z_gust_0h_sq"] ** 0.5)
    r0c_gust_sq_p = 2 * sstats.norm.sf(abs(r0c_gust_sq_z))

    import json
    turning_point_summary = {
        "turning_point_z": float(x_star), "turning_point_ms": float(tp_ms),
        "bootstrap_ci_z": [float(boot_lo_z), float(boot_hi_z)],
        "bootstrap_ci_ms": [float(boot_lo_ms), float(boot_hi_ms)],
        "r0c_gust_sq_p": float(r0c_gust_sq_p),
    }
    (RAW_DIR / "figure4_turning_point_summary_log_scale.json").write_text(
        json.dumps(turning_point_summary, indent=2), encoding="utf-8")

    # ---------------- plot ----------------
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.42))

    ax = axes[0]
    ax.axvspan(boot_lo_ms, boot_hi_ms, color="#1b9e77", alpha=0.15, label="Bootstrap 95% CI")
    ax.axvline(tp_ms, color="#1b9e77", linewidth=1.0, linestyle="--")
    ax.plot(curve_e0["gust_ms"], curve_e0["predicted_log_scale"], color="#333333", linewidth=1.4)
    ax.set_xlabel("Gust speed (m/s)")
    ax.set_ylabel("log(1 + affected customers)")
    ax.text(tp_ms + 0.6, ax.get_ylim()[1] * 0.05 + ax.get_ylim()[0],
             f"turning point\n{tp_ms:.2f} m/s", fontsize=9, color="#1b9e77", va="bottom")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(curve_r0c["gust_ms"], curve_r0c["predicted_log_scale"], color="#333333", linewidth=1.4)
    ax.set_xlabel("Gust speed (m/s)")
    ax.set_ylabel("log(restoration duration)")
    ax.text(0.05, 0.92, f"quadratic term significant\n(p={r0c_gust_sq_p:.1e})",
             transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#d95f02")
    panel_label(ax, "(b)")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_4_dose_response_log_scale")
    plt.close(fig)
    log_step("Saved Figure_4_dose_response_log_scale (command #47, no exponentiation).")


if __name__ == "__main__":
    main()
