"""Command #52: relabeled copy of appendix_h_20260906/make_curve_plot.py.
ONLY change: panel annotation text "Exposure margin (E0)" / "Recovery margin
(R0c)" -> "Exposure margin" / "Recovery margin" (no internal codenames).
Data unchanged (reuses the already-saved a3_curves_*.csv files)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\appendix_h_20260906\raw")
FIG_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\figure_relabel_20260906\figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {"quad": "#333333", "spline4": "#1b9e77", "ushape": "#d95f02", "softplus": "#7570b3"}
LABELS = {"quad": "Quadratic (baseline)", "spline4": "Free natural spline (df=4)",
          "ushape": "U-shape constrained hinge spline", "softplus": "Softplus (monotone)"}


def main():
    apply_style()
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.44))

    # RELABEL: "Exposure margin (E0)"/"Recovery margin (R0c)" -> drop the internal codename
    for ax, target, title, ylab in zip(
            axes, ["E0", "R0c"],
            ["Exposure margin", "Recovery margin"],
            ["log(1 + affected customers)", "log(restoration duration)"]):
        df = pd.read_csv(RAW_DIR / f"a3_curves_{target}.csv")
        for model in ["quad", "spline4", "ushape", "softplus"]:
            sub = df[df.model == model].sort_values("gust_ms")
            ax.plot(sub["gust_ms"], sub["pred_log"], color=COLORS[model], linewidth=1.3, label=LABELS[model])
        ax.set_xlabel("Gust speed (m/s)")
        ax.set_ylabel(ylab)
        ax.text(0.03, 0.95, title, transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#444444")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    panel_label(axes[0], "(a)")
    panel_label(axes[1], "(b)")
    axes[1].legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False, title="Gust-shape candidate")
    plt.tight_layout()
    save_fig(fig, FIG_DIR, "Figure_H1_curve_shape_comparison")
    plt.close(fig)
    print("Saved Figure_H1_curve_shape_comparison (relabeled)")


if __name__ == "__main__":
    main()
