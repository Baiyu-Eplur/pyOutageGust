"""Command #50 Step D: plot the four gust-shape candidates' fitted curves
(full-sample fit, other covariates at their sample means) for E0 and R0c,
using the already-saved a3_curves_*.csv files."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = result_path('appendix_h_20260906/raw')
FIG_DIR = result_path('appendix_h_20260906/figures')

COLORS = {"quad": "#333333", "spline4": "#1b9e77", "ushape": "#d95f02", "softplus": "#7570b3"}
LABELS = {"quad": "Quadratic (baseline)", "spline4": "Free natural spline (df=4)",
          "ushape": "U-shape constrained hinge spline", "softplus": "Softplus (monotone)"}


def main():
    apply_style()
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.44))

    for ax, target, title, ylab in zip(
            axes, ["E0", "R0c"],
            ["Exposure margin (E0)", "Recovery margin (R0c)"],
            ["log(1 + affected customers)", "log(restoration duration)"]):
        df = pd.read_csv(read_input(RAW_DIR / f"a3_curves_{target}.csv"))
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
    print("Saved Figure_H1_curve_shape_comparison")


if __name__ == "__main__":
    main()
