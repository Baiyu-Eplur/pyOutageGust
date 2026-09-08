"""Final regeneration of Figure 2 (distribution panels) on C01-corrected data.
No C02-C08 fix applies; regenerated for consistency with the corrected sample."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, DOUBLE_COL_MM  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig2-final] {msg}", flush=True)


def hist_with_kde(ax, data, color, bins, xlabel):
    from scipy.stats import gaussian_kde
    ax.hist(data, bins=bins, density=True, color=color, alpha=0.45, edgecolor="none")
    kde = gaussian_kde(data)
    xs = np.linspace(data.min(), data.max(), 400)
    ax.plot(xs, kde(xs), color=color, linewidth=1.3, alpha=0.95)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.tick_params(labelsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


def main():
    apply_style()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()
    customers = combined_e0["customers_v2_event_excl_reinterruptions"].astype(float)
    duration = combined_r0cb["duration_B_full_span_hours"].astype(float)
    log_step(f"customers n={len(customers)}, duration n={len(duration)}")

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(2, 2, figsize=(fig_w, fig_w * 0.78))
    COLOR_CUST, COLOR_DUR = "#1b9e77", "#d95f02"

    p99_c = customers.quantile(0.99)
    hist_with_kde(axes[0, 0], customers[customers <= p99_c], COLOR_CUST, bins=60, xlabel="Affected customers (customers_v2)")
    axes[0, 0].text(-0.18, 1.08, "(a)", transform=axes[0, 0].transAxes, fontsize=10, fontweight="bold")

    hist_with_kde(axes[0, 1], np.log1p(customers), COLOR_CUST, bins=60, xlabel="log(1 + affected customers)")
    axes[0, 1].text(-0.18, 1.08, "(b)", transform=axes[0, 1].transAxes, fontsize=10, fontweight="bold")

    p99_d = duration.quantile(0.99)
    hist_with_kde(axes[1, 0], duration[duration <= p99_d], COLOR_DUR, bins=60, xlabel="Restoration duration (hours)")
    axes[1, 0].text(-0.18, 1.08, "(c)", transform=axes[1, 0].transAxes, fontsize=10, fontweight="bold")

    hist_with_kde(axes[1, 1], np.log(duration), COLOR_DUR, bins=60, xlabel="log(restoration duration)")
    axes[1, 1].text(-0.18, 1.08, "(d)", transform=axes[1, 1].transAxes, fontsize=10, fontweight="bold")

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_2_distribution")
    plt.close(fig)
    log_step(f"Saved. p99_customers={p99_c:.1f}, p99_duration={p99_d:.2f}h")


if __name__ == "__main__":
    main()
