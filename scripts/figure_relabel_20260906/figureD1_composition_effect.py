"""Command #52: relabeled copy of figureD1_composition_effect.py. ONLY
change: legend labels "n_stages = 1" / "n_stages = 2" / "n_stages = 3-4" /
"n_stages >= 5" (the raw variable name rendered into the legend) replaced
with formal English ("1 restoration stage" / "2 restoration stages" /
"3-4 restoration stages" / "5+ restoration stages"), matching the paper's own
prose ("the number of restoration stages"), which never uses "n_stages"
literally. GROUP_ORDER/GROUP_COLORS/GROUP_MARKERS dict KEYS are internal
lookup keys, not rendered text, and are left unchanged. Data unchanged."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\figure_relabel_20260906\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_ORDER = ["n_stages=1", "n_stages=2", "n_stages=3-4", "n_stages>=5"]
# RELABEL: dict VALUES (the rendered legend text) no longer use the raw "n_stages" variable name
GROUP_LABELS = {"n_stages=1": "1 restoration stage", "n_stages=2": "2 restoration stages",
                "n_stages=3-4": "3\u20134 restoration stages", "n_stages>=5": "5+ restoration stages"}
GROUP_COLORS = {"n_stages=1": "#0072B2", "n_stages=2": "#E69F00",
                "n_stages=3-4": "#009E73", "n_stages>=5": "#CC79A7"}
GROUP_MARKERS = {"n_stages=1": "o", "n_stages=2": "s", "n_stages=3-4": "^", "n_stages>=5": "D"}


def log_step(msg):
    print(f"[figD1-relabel] {msg}", flush=True)


def main():
    apply_style()
    _, _, combined_r0cb, _ = build_corrected_combined_samples()
    ids = combined_r0cb["Incident Reference"].astype(str).unique().tolist()
    stage_lookup = pd.read_csv(SRC, usecols=["Incident Reference", "stage_row_count"], low_memory=False)
    stage_lookup["Incident Reference"] = stage_lookup["Incident Reference"].astype(str)
    stage_lookup = stage_lookup[stage_lookup["Incident Reference"].isin(ids)].drop_duplicates("Incident Reference")

    df = combined_r0cb.copy()
    df["Incident Reference"] = df["Incident Reference"].astype(str)
    df = df.merge(stage_lookup, on="Incident Reference", how="left")

    def stage_group(x):
        if x == 1:
            return "n_stages=1"
        if x == 2:
            return "n_stages=2"
        if 3 <= x <= 4:
            return "n_stages=3-4"
        return "n_stages>=5"

    df["n_stages_group"] = df["stage_row_count"].apply(stage_group)
    customers = df["customers_v2_event_excl_reinterruptions"].astype(float)
    edges = customers.quantile([0, 0.25, 0.5, 0.75, 1.0]).to_numpy().copy()
    edges[0] -= 1e-9
    bin_labels = [f"Q1 [{edges[0]+1e-9:.0f}-{edges[1]:.0f}]", f"Q2 ({edges[1]:.0f}-{edges[2]:.0f}]",
                  f"Q3 ({edges[2]:.0f}-{edges[3]:.0f}]", f"Q4 ({edges[3]:.0f}-{edges[4]:.0f}]"]
    df["customers_bin"] = pd.cut(customers, bins=edges, labels=bin_labels, include_lowest=True)

    cross = df.groupby(["n_stages_group", "customers_bin"], observed=True)["duration_B_full_span_hours"].mean()
    cross_mean = cross.unstack("customers_bin").reindex(GROUP_ORDER)[bin_labels]
    pooled = df.groupby("customers_bin", observed=True)["duration_B_full_span_hours"].mean().reindex(bin_labels)
    log_step("Cross-tab (corrected):\n" + cross_mean.round(2).to_string())
    log_step("Pooled (corrected):\n" + pooled.round(2).to_string())

    x = range(len(bin_labels))
    y_max = max(cross_mean.to_numpy().max(), pooled.max()) * 1.08
    y_min = min(cross_mean.to_numpy().min(), pooled.min()) * 0.9
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.42))

    ax = axes[0]
    for grp in GROUP_ORDER:
        ax.plot(x, cross_mean.loc[grp].to_numpy(), marker=GROUP_MARKERS[grp], color=GROUP_COLORS[grp],
                 linewidth=1.4, markersize=5, label=GROUP_LABELS[grp])
    ax.set_xticks(list(x))
    ax.set_xticklabels(bin_labels, rotation=15, ha="right")
    ax.set_xlabel("Affected customers (quartile bin)")
    ax.set_ylabel("Mean restoration duration (h)")
    ax.set_ylim(y_min, y_max)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(x, pooled.to_numpy(), marker="o", color="#333333", linewidth=1.6, markersize=6)
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
    log_step("Saved Figure_D1_composition_effect (relabeled).")


if __name__ == "__main__":
    main()
