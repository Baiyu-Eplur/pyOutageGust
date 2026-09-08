"""Final regeneration of Figure 8 on C01-corrected data (main-spec variance
decomposition from c01_repair's step4b outputs; weather_natural subsample
variance decomposition from this command's final_core_tables.py output)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

C01_RAW = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905\raw")
RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\figures")


def log_step(msg):
    print(f"[fig8-final] {msg}", flush=True)


def main():
    apply_style()
    e0_main = pd.read_csv(C01_RAW / "step4b_E0_corrected_variance_decomposition.csv")
    e0_wn = pd.read_csv(RAW_DIR / "E0_wn_corrected_variance_decomposition.csv")
    r0c_main = pd.read_csv(C01_RAW / "step4b_R0c_corrected_variance_decomposition_gust_first.csv")
    r0c_wn = pd.read_csv(RAW_DIR / "R0c_wn_corrected_variance_decomposition_gust_first.csv")

    e0_main_gust = e0_main.loc[e0_main["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100
    e0_wn_gust = e0_wn.loc[e0_wn["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100
    r0c_main_gust = r0c_main.loc[r0c_main["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100
    r0c_wn_gust = r0c_wn.loc[r0c_wn["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100
    r0c_main_cust = r0c_main.loc[r0c_main["step"] == "customers", "r2_oos_5fold_increment"].iloc[0] * 100
    r0c_wn_cust = r0c_wn.loc[r0c_wn["step"] == "customers", "r2_oos_5fold_increment"].iloc[0] * 100
    log_step(f"E0 gust: main={e0_main_gust:.4f}, wn={e0_wn_gust:.4f}")
    log_step(f"R0c gust: main={r0c_main_gust:.4f}, wn={r0c_wn_gust:.4f}; "
              f"customers: main={r0c_main_cust:.4f}, wn={r0c_wn_cust:.4f}")

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.45))

    ax = axes[0]
    labels_a = ["Main spec.\n(corrected)", "weather_natural\n(corrected)"]
    vals_a = [e0_main_gust, e0_wn_gust]
    bars = ax.bar(labels_a, vals_a, color=["#1b9e77", "#66c2a5"], width=0.5)
    y_lo = min(0, min(vals_a)) - 0.35
    y_hi = max(vals_a) * 1.25 + 0.1
    for b, v in zip(bars, vals_a):
        va = "bottom" if v >= 0 else "top"
        offset = 0.05 if v >= 0 else -0.05
        ax.text(b.get_x() + b.get_width() / 2, v + offset, f"{v:.2f}pp", ha="center", va=va, fontsize=9)
    ax.axhline(0, color="#888888", linewidth=0.6)
    ax.set_ylim(y_lo, y_hi)
    ax.set_ylabel("Gust marginal OOS R\u00b2 (pp)")
    ax.text(0.95, 0.95, "E0 (exposure)", transform=ax.transAxes, fontsize=9, va="top", ha="right", color="#444444")
    panel_label(ax, "(a)")

    ax = axes[1]
    x = np.arange(2)
    width = 0.36
    gust_bars = [r0c_main_gust, r0c_wn_gust]
    cust_bars = [r0c_main_cust, r0c_wn_cust]
    ax.bar(x - width / 2, gust_bars, width, label="Gust", color="#1b9e77")
    ax.bar(x + width / 2, cust_bars, width, label="Affected customers", color="#7570b3")
    for xi, v in zip(x - width / 2, gust_bars):
        ax.text(xi, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    for xi, v in zip(x + width / 2, cust_bars):
        ax.text(xi, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(["Main spec.\n(corrected)", "weather_natural\n(corrected)"])
    ax.set_ylabel("Marginal OOS R\u00b2 (pp)")
    ax.legend(frameon=False, loc="upper left")
    ax.text(0.95, 0.95, "R0c (recovery)", transform=ax.transAxes, fontsize=9, va="top", ha="right", color="#444444")
    panel_label(ax, "(b)")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_8_weather_subsample_comparison")
    plt.close(fig)
    log_step("Saved Figure_8_weather_subsample_comparison (final).")


if __name__ == "__main__":
    main()
