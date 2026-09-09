"""Command #51, Question 2: regenerate Figure 10 with the "development
sample" row replaced by a genuine single full-sample fit (option a) instead
of the inverse-variance pooling of 5 overlapping GroupKFold training folds.
The other three rows (holdout, LAD single cluster, LAD x date two-way
cluster) are unchanged from command #45's corrected-data outputs."""
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

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

RAW_C0208 = result_path('c02_c08_repair_20260905/raw')
RAW_DIR = result_path('appendix_h_legacy_followup_20260906/raw')
FIG_DIR = result_path('appendix_h_legacy_followup_20260906/figures')
FIG_DIR.mkdir(parents=True, exist_ok=True)
Z95 = 1.959963984540054


def single_estimate(csv_path, term, coef_col="coef", se_col="se"):
    df = pd.read_csv(read_input(csv_path))
    row = df[df["term"] == term].iloc[0]
    return float(row[coef_col]), float(row[se_col])


def main():
    apply_style()
    term = "z_gust_0h_sq"

    # option (a) values, from q2_result.json (already computed)
    e0_dev, e0_dev_se = 0.08909100509038129, 0.00997972095015659
    r0c_dev, r0c_dev_se = 0.0739707557449553, 0.007465790992821263

    e0_hold, e0_hold_se = single_estimate(RAW_C0208 / "E0_holdout_corrected_coefs.csv", term)
    r0c_hold, r0c_hold_se = single_estimate(RAW_C0208 / "R0c_holdout_corrected_coefs.csv", term)
    e0_lad, e0_lad_se = single_estimate(RAW_C0208 / "E0_corrected_lad_cluster.csv", term)
    e0_2way, e0_2way_se = single_estimate(RAW_C0208 / "E0_corrected_twoway_cluster.csv", term)
    r0c_lad, r0c_lad_se = single_estimate(RAW_C0208 / "R0c_corrected_lad_cluster.csv", term)
    r0c_2way, r0c_2way_se = single_estimate(RAW_C0208 / "R0c_corrected_twoway_cluster.csv", term)

    rows = [
        ("E0 (exposure)", "LAD\u00d7date two-way cluster", e0_2way, e0_2way_se),
        ("E0 (exposure)", "LAD single cluster", e0_lad, e0_lad_se),
        ("E0 (exposure)", "Holdout (confirmation)", e0_hold, e0_hold_se),
        ("E0 (exposure)", "Development sample (single fit, revised)", e0_dev, e0_dev_se),
        ("R0c (recovery)", "LAD\u00d7date two-way cluster", r0c_2way, r0c_2way_se),
        ("R0c (recovery)", "LAD single cluster", r0c_lad, r0c_lad_se),
        ("R0c (recovery)", "Holdout (confirmation)", r0c_hold, r0c_hold_se),
        ("R0c (recovery)", "Development sample (single fit, revised)", r0c_dev, r0c_dev_se),
    ]
    for model, label, coef, se in rows:
        print(f"[fig10-revised] {model} / {label}: coef={coef:.4f}, 95% CI=[{coef-Z95*se:.4f},{coef+Z95*se:.4f}]")

    fig_w = mm_to_in(SINGLE_COL_MM) * 1.9
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.62))
    y_positions = np.arange(len(rows))[::-1]
    color_map = {"E0 (exposure)": "#1b9e77", "R0c (recovery)": "#d95f02"}
    for yi, (model, label, coef, se) in zip(y_positions, rows):
        lo, hi = coef - Z95 * se, coef + Z95 * se
        ax.plot([lo, hi], [yi, yi], color=color_map[model], linewidth=1.3)
        ax.plot(coef, yi, "o", color=color_map[model], markersize=5)
    ax.axvline(0, color="#888888", linewidth=0.7, linestyle="--")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{m} \u2013 {l}" for m, l in [(r[0], r[1]) for r in rows]])
    ax.set_xlabel("Gust quadratic-term coefficient (z_gust_0h_sq), 95% CI")
    ax.axhline(3.5, color="#cccccc", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    save_fig(fig, FIG_DIR, "Figure_10_robustness_forest_REVISED")
    plt.close(fig)
    print("[fig10-revised] Saved Figure_10_robustness_forest_REVISED")


if __name__ == "__main__":
    main()
