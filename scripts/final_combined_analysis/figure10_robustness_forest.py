"""Command #37 Figure 10: robustness forest plot for the gust quadratic term
(z_gust_0h_sq), comparing four existing analyses per outcome:
  1. Development sample (command #16): inverse-variance-weighted pooled
     estimate across the 5 already-reported GroupKFold coefficients (a
     visualization-only aggregation of existing numbers -- no new model fit).
  2. Independent holdout/confirmation sample (command #19): existing
     single full-sample coefficient + LAD-clustered SE.
  3. Full combined sample, LAD-clustered SE (command #21/#27).
  4. Full combined sample, LAD*date two-way-clustered SE (command #27).
Groups 3-4 share the identical point estimate (same model, only the SE
estimator differs) -- this is expected and is the whole point of the
clustering-robustness check.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

DEV_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\dev_sample_decontamination\raw")
HOLDOUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\module_e_final_confirmation\raw")
COMBINED_RAW = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

Z95 = 1.959963984540054


def log_step(msg):
    print(f"[fig10] {msg}", flush=True)


def pooled_estimate(fold_csv: Path, term: str):
    df = pd.read_csv(fold_csv)
    sub = df[df["term"] == term]
    w = 1.0 / (sub["std_error"].astype(float) ** 2)
    pooled = float((w * sub["coefficient"].astype(float)).sum() / w.sum())
    se = float(np.sqrt(1.0 / w.sum()))
    return pooled, se, len(sub)


def single_estimate(csv_path: Path, term: str, coef_col="coefficient", se_col="std_error"):
    df = pd.read_csv(csv_path)
    row = df[df["term"] == term].iloc[0]
    return float(row[coef_col]), float(row[se_col])


def main():
    apply_style()
    term = "z_gust_0h_sq"

    e0_dev, e0_dev_se, e0_dev_nfold = pooled_estimate(DEV_DIR / "E0_prime_clean_fold_coefs.csv", term)
    r0c_dev, r0c_dev_se, r0c_dev_nfold = pooled_estimate(DEV_DIR / "R0c_prime_B_clean_fold_coefs.csv", term)
    log_step(f"Dev pooled (n_folds={e0_dev_nfold}): E0={e0_dev:.4f}\u00b1{e0_dev_se:.4f}, "
              f"R0c={r0c_dev:.4f}\u00b1{r0c_dev_se:.4f}")

    e0_hold, e0_hold_se = single_estimate(HOLDOUT_DIR / "step1_E0_holdout_coefs.csv", term)
    r0c_hold, r0c_hold_se = single_estimate(HOLDOUT_DIR / "step2_R0c_holdout_coefs.csv", term)

    e0_lad, e0_lad_se = single_estimate(COMBINED_RAW / "step28_E0_lad_cluster.csv", term, "coef", "se")
    e0_2way, e0_2way_se = single_estimate(COMBINED_RAW / "step28_E0_twoway_cluster.csv", term, "coef", "se")
    r0c_lad, r0c_lad_se = single_estimate(COMBINED_RAW / "step28_R0c_lad_cluster.csv", term, "coef", "se")
    r0c_2way, r0c_2way_se = single_estimate(COMBINED_RAW / "step28_R0c_twoway_cluster.csv", term, "coef", "se")

    rows = [
        ("E0 (exposure)", "LAD\u00d7date two-way cluster", e0_2way, e0_2way_se),
        ("E0 (exposure)", "LAD single cluster", e0_lad, e0_lad_se),
        ("E0 (exposure)", "Holdout (confirmation)", e0_hold, e0_hold_se),
        ("E0 (exposure)", "Development sample (pooled)", e0_dev, e0_dev_se),
        ("R0c (recovery)", "LAD\u00d7date two-way cluster", r0c_2way, r0c_2way_se),
        ("R0c (recovery)", "LAD single cluster", r0c_lad, r0c_lad_se),
        ("R0c (recovery)", "Holdout (confirmation)", r0c_hold, r0c_hold_se),
        ("R0c (recovery)", "Development sample (pooled)", r0c_dev, r0c_dev_se),
    ]
    for model, label, coef, se in rows:
        log_step(f"{model} / {label}: coef={coef:.4f}, 95% CI=[{coef - Z95*se:.4f}, {coef + Z95*se:.4f}]")

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

    # separator between E0 block and R0c block
    ax.axhline(3.5, color="#cccccc", linewidth=0.6)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_10_robustness_forest")
    plt.close(fig)
    log_step("Saved Figure_10_robustness_forest.")


if __name__ == "__main__":
    main()
