"""Command #52: relabeled copy of figure7_magnitude_comparison.py. ONLY
change: the three row labels no longer contain "E0"/"R0c" -- replaced with
"exposure margin"/"recovery margin". Data, ratios, and all other logic
unchanged (reuses the same existing corrected raw-data CSVs, no refitting
beyond what the original script already did for the third ratio)."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

RAW_DIR = result_path('c02_c08_repair_20260905/raw')
OUT_DIR = result_path('figure_relabel_20260906/figures')
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig7-relabel] {msg}", flush=True)


def main():
    apply_style()
    v9, _, _ = _patch_v9()
    import importlib.util
    spec11 = importlib.util.spec_from_file_location(
        "critical_wind_speed_pipeline",
        str(project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')))
    v11 = importlib.util.module_from_spec(spec11)
    spec11.loader.exec_module(v11)

    curves = pd.read_csv(read_input(RAW_DIR / "figure4_dose_response_curves_corrected.csv"))
    e0_curve = curves[curves["model"] == "E0_gust_dose_response"]
    r0c_curve = curves[curves["model"] == "R0c_gust_dose_response"]
    ratio_gust_e0 = e0_curve["predicted_level"].max() / e0_curve["predicted_level"].min()
    ratio_gust_r0c = r0c_curve["predicted_level"].max() / r0c_curve["predicted_level"].min()

    log_step("Building customers_v2 -> duration_B dose-response curve (corrected R0c sample)...")
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()
    res, cov, gust_mean, gust_sd, d = v11.fit_full_sample(
        combined_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)
    cust_raw = d["customers_v2_event_excl_reinterruptions"].astype(float)
    p1, p99 = cust_raw.quantile(0.01), cust_raw.quantile(0.99)
    grid_raw = np.linspace(p1, p99, 50)
    grid_log1p = np.log1p(grid_raw)

    s = combined_r0cb.copy()
    s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
    Xtr_full, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    mu_c, sd_c = s["customers_v2_log1p"].mean(), s["customers_v2_log1p"].std(ddof=1)
    grid_z = (grid_log1p - mu_c) / sd_c

    exog_names = list(res.model.exog_names)
    means = Xtr_full.mean(axis=0)
    X = pd.DataFrame(0.0, index=range(len(grid_z)), columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0
    for c in exog_names:
        if c in ("z_gust_0h", "z_gust_0h_sq", "z_gust_pressure", "Intercept",
                  "z_log1p_customers_v2", "z_log1p_customers_v2_sq"):
            continue
        if c in means.index:
            X[c] = means[c]
    X["z_gust_0h"] = 0.0
    X["z_gust_0h_sq"] = 0.0
    if "z_gust_pressure" in X.columns:
        X["z_gust_pressure"] = 0.0
    X["z_log1p_customers_v2"] = grid_z
    X["z_log1p_customers_v2_sq"] = grid_z ** 2
    beta = res.params.loc[exog_names]
    pred = np.exp(X[exog_names].astype(float) @ beta)
    ratio_customers = float(pred.max() / pred.min())

    log_step(f"Ratios (corrected): gust->exposure={ratio_gust_e0:.4f}, gust->recovery={ratio_gust_r0c:.4f}, "
              f"customers->recovery={ratio_customers:.4f}")

    # RELABEL: removed "(E0, ...)" / "(R0c, ...)" -- now "exposure margin" / "recovery margin"
    LABELS = [
        "Gust \u2192 affected customers\n(exposure margin, 1st\u201399th pct. of gust)",
        "Gust \u2192 restoration duration\n(recovery margin, customers fixed)",
        "Affected customers \u2192 restoration duration\n(recovery margin, gust fixed)",
    ]
    RATIOS = [ratio_gust_e0, ratio_gust_r0c, ratio_customers]
    COLORS = ["#1b9e77", "#1b9e77", "#7570b3"]

    fig_w = mm_to_in(SINGLE_COL_MM) * 1.75
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.45))
    y = np.arange(len(LABELS))[::-1]
    ax.barh(y, RATIOS, color=COLORS, height=0.5)
    for yi, v in zip(y, RATIOS):
        ax.text(v + 0.08, yi, f"{v:.2f}\u00d7", va="center", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted-value ratio (max/min over observed range)")
    ax.axvline(1.0, color="#888888", linewidth=0.6, linestyle="--")
    ax.set_xlim(0, max(RATIOS) * 1.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_7_magnitude_comparison")
    plt.close(fig)
    log_step("Saved Figure_7_magnitude_comparison (relabeled).")


if __name__ == "__main__":
    main()
