"""Command #52: relabeled copy of figure10_robustness_forest.py. ONLY
change: row labels "E0 (exposure)" / "R0c (recovery)" replaced with
"Exposure margin" / "Recovery margin". The CI construction (inverse-variance
pooling of the 5 development-sample fold coefficients) is UNCHANGED here --
command #51 separately identified a statistical concern with that pooling
and offered alternatives, which is a distinct, not-yet-decided question left
to the web-side agent; this command only fixes the label text on the
currently-published construction, matching the "no statistical content
changed" scope of command #52."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\figure_relabel_20260906\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
Z95 = 1.959963984540054


def log_step(msg):
    print(f"[fig10-relabel] {msg}", flush=True)


def pooled_estimate(fold_csv, term):
    df = pd.read_csv(fold_csv)
    sub = df[df["term"] == term]
    w = 1.0 / (sub["std_error"].astype(float) ** 2)
    pooled = float((w * sub["coefficient"].astype(float)).sum() / w.sum())
    se = float(np.sqrt(1.0 / w.sum()))
    return pooled, se


def single_estimate(csv_path, term, coef_col="coef", se_col="se"):
    df = pd.read_csv(csv_path)
    row = df[df["term"] == term].iloc[0]
    return float(row[coef_col]), float(row[se_col])


def main():
    apply_style()
    term = "z_gust_0h_sq"

    e0_dev, e0_dev_se = pooled_estimate(RAW_DIR / "E0_dev_corrected_fold_coefs.csv", term)
    r0c_dev, r0c_dev_se = pooled_estimate(RAW_DIR / "R0c_dev_corrected_fold_coefs.csv", term)
    e0_hold, e0_hold_se = single_estimate(RAW_DIR / "E0_holdout_corrected_coefs.csv", term)
    r0c_hold, r0c_hold_se = single_estimate(RAW_DIR / "R0c_holdout_corrected_coefs.csv", term)
    e0_lad, e0_lad_se = single_estimate(RAW_DIR / "E0_corrected_lad_cluster.csv", term)
    e0_2way, e0_2way_se = single_estimate(RAW_DIR / "E0_corrected_twoway_cluster.csv", term)
    r0c_lad, r0c_lad_se = single_estimate(RAW_DIR / "R0c_corrected_lad_cluster.csv", term)
    r0c_2way, r0c_2way_se = single_estimate(RAW_DIR / "R0c_corrected_twoway_cluster.csv", term)

    # RELABEL: "E0 (exposure)" -> "Exposure margin"; "R0c (recovery)" -> "Recovery margin"
    rows = [
        ("Exposure margin", "LAD\u00d7date two-way cluster", e0_2way, e0_2way_se),
        ("Exposure margin", "LAD single cluster", e0_lad, e0_lad_se),
        ("Exposure margin", "Holdout (confirmation)", e0_hold, e0_hold_se),
        ("Exposure margin", "Development sample (pooled)", e0_dev, e0_dev_se),
        ("Recovery margin", "LAD\u00d7date two-way cluster", r0c_2way, r0c_2way_se),
        ("Recovery margin", "LAD single cluster", r0c_lad, r0c_lad_se),
        ("Recovery margin", "Holdout (confirmation)", r0c_hold, r0c_hold_se),
        ("Recovery margin", "Development sample (pooled)", r0c_dev, r0c_dev_se),
    ]
    for model, label, coef, se in rows:
        log_step(f"{model} / {label}: coef={coef:.4f}, 95% CI=[{coef - Z95*se:.4f}, {coef + Z95*se:.4f}]")

    fig_w = mm_to_in(SINGLE_COL_MM) * 1.9
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.62))
    y_positions = np.arange(len(rows))[::-1]
    color_map = {"Exposure margin": "#1b9e77", "Recovery margin": "#d95f02"}
    for yi, (model, label, coef, se) in zip(y_positions, rows):
        lo, hi = coef - Z95 * se, coef + Z95 * se
        ax.plot([lo, hi], [yi, yi], color=color_map[model], linewidth=1.3)
        ax.plot(coef, yi, "o", color=color_map[model], markersize=5)
    ax.axvline(0, color="#888888", linewidth=0.7, linestyle="--")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{m} \u2013 {l}" for m, l in [(r[0], r[1]) for r in rows]])
    # RELABEL: dropped the internal variable name "(z_gust_0h_sq)" from the axis label
    ax.set_xlabel("Gust quadratic-term coefficient, 95% CI")
    ax.axhline(3.5, color="#cccccc", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_10_robustness_forest")
    plt.close(fig)
    log_step("Saved Figure_10_robustness_forest (relabeled).")


if __name__ == "__main__":
    main()
