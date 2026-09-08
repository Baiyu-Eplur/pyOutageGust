"""Command #33 Figure 2: 2x2 distribution panels for affected customers and
restoration duration, raw and log scale, on the final combined sample."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402
from figure_style import apply_style, mm_to_in, save_fig, DOUBLE_COL_MM  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig2] {msg}", flush=True)


def hist_with_kde(ax, data, color, bins, xlabel, log_x=False):
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
    _, combined_e0, combined_r0cb, _ = build_combined_samples()

    customers = combined_e0["customers_v2_event_excl_reinterruptions"].astype(float)
    duration = combined_r0cb["duration_B_full_span_hours"].astype(float)

    log_step(f"customers n={len(customers)}, duration n={len(duration)}")

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(2, 2, figsize=(fig_w, fig_w * 0.78))

    COLOR_CUST = "#1b9e77"
    COLOR_DUR = "#d95f02"

    # (a) affected customers, raw, p99-capped view for readability (full range noted in caption)
    p99_c = customers.quantile(0.99)
    hist_with_kde(axes[0, 0], customers[customers <= p99_c], COLOR_CUST, bins=60,
                  xlabel="Affected customers (customers_v2)")
    axes[0, 0].text(-0.18, 1.08, "(a)", transform=axes[0, 0].transAxes, fontsize=10, fontweight="bold")

    # (b) log1p(customers)
    hist_with_kde(axes[0, 1], np.log1p(customers), COLOR_CUST, bins=60,
                  xlabel="log(1 + affected customers)")
    axes[0, 1].text(-0.18, 1.08, "(b)", transform=axes[0, 1].transAxes, fontsize=10, fontweight="bold")

    # (c) duration raw
    p99_d = duration.quantile(0.99)
    hist_with_kde(axes[1, 0], duration[duration <= p99_d], COLOR_DUR, bins=60,
                  xlabel="Restoration duration (hours)")
    axes[1, 0].text(-0.18, 1.08, "(c)", transform=axes[1, 0].transAxes, fontsize=10, fontweight="bold")

    # (d) log duration
    hist_with_kde(axes[1, 1], np.log(duration), COLOR_DUR, bins=60,
                  xlabel="log(restoration duration)")
    axes[1, 1].text(-0.18, 1.08, "(d)", transform=axes[1, 1].transAxes, fontsize=10, fontweight="bold")

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_2_distribution")
    plt.close(fig)

    log_step(f"Saved. Note: panels (a)/(c) display the 0-99th percentile range for "
              f"readability (p99_customers={p99_c:.1f}, p99_duration={p99_d:.2f}h); "
              f"full range and n reported in caption text separately.")


if __name__ == "__main__":
    main()
