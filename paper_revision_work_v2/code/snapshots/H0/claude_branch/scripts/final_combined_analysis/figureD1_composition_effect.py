"""Command #42 Figure D1 (Appendix figure, not part of the main Figure 1-10
series): n_stages x affected-customers composition-effect figure. Panel (a)
shows duration_B vs customers_v2 quartile stratified by n_stages (each line
should be roughly monotonic decreasing); panel (b) shows the same x-axis
pooled across n_stages (rises then falls). Data from step42's cross-tab
(descriptive means only, no new modelling), reusing figure_style.py."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_ORDER = ["n_stages=1", "n_stages=2", "n_stages=3-4", "n_stages>=5"]
GROUP_LABELS = {"n_stages=1": "n_stages = 1", "n_stages=2": "n_stages = 2",
                "n_stages=3-4": "n_stages = 3-4", "n_stages>=5": "n_stages \u2265 5"}
# Wong (2011) colorblind-safe qualitative colours, no red-green pair
GROUP_COLORS = {"n_stages=1": "#0072B2", "n_stages=2": "#E69F00",
                "n_stages=3-4": "#009E73", "n_stages>=5": "#CC79A7"}
GROUP_MARKERS = {"n_stages=1": "o", "n_stages=2": "s", "n_stages=3-4": "^", "n_stages>=5": "D"}


def log_step(msg):
    print(f"[figD1] {msg}", flush=True)


def main():
    apply_style()
    cross = pd.read_csv(RAW_DIR / "step42_crosstab_mean_duration.csv", index_col=0)
    pooled = pd.read_csv(RAW_DIR / "step42_pooled_mean_duration.csv", index_col=0)
    bin_labels = list(cross.columns)
    x = range(len(bin_labels))

    y_max = max(cross.to_numpy().max(), pooled["mean"].max()) * 1.08
    y_min = min(cross.to_numpy().min(), pooled["mean"].min()) * 0.9

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.42))

    ax = axes[0]
    for grp in GROUP_ORDER:
        ax.plot(x, cross.loc[grp].to_numpy(), marker=GROUP_MARKERS[grp], color=GROUP_COLORS[grp],
                 linewidth=1.4, markersize=5, label=GROUP_LABELS[grp])
    ax.set_xticks(list(x))
    ax.set_xticklabels(bin_labels, rotation=15, ha="right")
    ax.set_xlabel("Affected customers (quartile bin)")
    ax.set_ylabel("Mean restoration duration (h)")
    ax.set_ylim(y_min, y_max)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(x, pooled["mean"].to_numpy(), marker="o", color="#333333", linewidth=1.6, markersize=6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(bin_labels, rotation=15, ha="right")
    ax.set_xlabel("Affected customers (quartile bin)")
    ax.set_ylabel("Mean restoration duration (h)")
    ax.set_ylim(y_min, y_max)
    panel_label(ax, "(b)")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_D1_composition_effect")
    plt.close(fig)
    log_step("Saved Figure_D1_composition_effect.")


if __name__ == "__main__":
    main()
