"""Command #37 Figure 7: simple horizontal bar chart comparing three
predicted-value magnitude ratios (max/min across the observed covariate
range, all other covariates held fixed). Numbers read from existing reports
(03_阵风剂量反应曲线说明.md, 07_customers_v2剂量反应曲线说明.md) -- no new
computation.

Design note: the command suggested either a bar chart or a dumbbell plot.
Each of the three quantities is a single ratio (not a before/after pair), so
a simple horizontal bar chart is the more natural fit -- a dumbbell plot is
built for showing two connected points per row, which does not apply here."""
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

sys.path.insert(0, str(Path(__file__).parent))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

OUT_DIR = result_path('final_combined_analysis/figures')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# source: 03_阵风剂量反应曲线说明.md, 07_customers_v2剂量反应曲线说明.md
LABELS = [
    "Gust \u2192 affected customers\n(E0, 1st\u201399th pct. of gust)",
    "Gust \u2192 restoration duration\n(R0c, customers fixed)",
    "Affected customers \u2192 restoration duration\n(R0c, gust fixed)",
]
RATIOS = [2.79, 2.37, 5.9903]
COLORS = ["#1b9e77", "#1b9e77", "#7570b3"]


def log_step(msg):
    print(f"[fig7] {msg}", flush=True)


def main():
    apply_style()
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
    log_step("Saved Figure_7_magnitude_comparison.")


if __name__ == "__main__":
    main()
