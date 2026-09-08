"""Command #37 Figure 5: grouped bar chart of marginal OOS R^2 contribution by
variable block, for E0 (exposure) and R0c (recovery), on the final combined
sample. Numbers read directly from command #21 Step2's existing CSVs
(raw/step2_E0_variance_decomposition.csv, raw/step2_R0c_order_gust_then_customers.csv)
-- no new computation. R0c uses the gust-before-customers ordering so gust's
marginal contribution is not first "used up" by customers_v2; the full
order-dependent range (0.62-0.75pp) is disclosed in the accompanying text."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig5] {msg}", flush=True)


def main():
    apply_style()
    e0 = pd.read_csv(RAW_DIR / "step2_E0_variance_decomposition.csv")
    r0c = pd.read_csv(RAW_DIR / "step2_R0c_order_gust_then_customers.csv")

    e0_vals = {
        "Baseline\n(region+FE)": e0.loc[e0["step"] == "baseline", "r2_oos_5fold"].iloc[0] * 100,
        "+ Non-gust\nweather": e0.loc[e0["step"] == "nongust_weather", "r2_oos_5fold_increment"].iloc[0] * 100,
        "+ Gust": e0.loc[e0["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100,
        "+ Customers": np.nan,
    }
    r0c_vals = {
        "Baseline\n(region+FE)": r0c.loc[r0c["step"] == "baseline", "r2_oos_5fold"].iloc[0] * 100,
        "+ Non-gust\nweather": r0c.loc[r0c["step"] == "nongust_weather", "r2_oos_5fold_increment"].iloc[0] * 100,
        "+ Gust": r0c.loc[r0c["step"] == "gust", "r2_oos_5fold_increment"].iloc[0] * 100,
        "+ Customers": r0c.loc[r0c["step"] == "customers", "r2_oos_5fold_increment"].iloc[0] * 100,
    }
    log_step(f"E0: {e0_vals}")
    log_step(f"R0c: {r0c_vals}")

    groups = list(e0_vals.keys())
    x = np.arange(len(groups))
    width = 0.36

    fig_w = mm_to_in(SINGLE_COL_MM) * 1.55
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.72))
    e0_bars = [e0_vals[g] for g in groups]
    r0c_bars = [r0c_vals[g] for g in groups]

    ax.bar(x - width / 2, e0_bars, width, label="E0 (exposure)", color="#1b9e77")
    ax.bar(x + width / 2, r0c_bars, width, label="R0c (recovery, gust-before-customers order)", color="#d95f02")

    for xi, v in zip(x - width / 2, e0_bars):
        if not np.isnan(v):
            ax.text(xi, v + 0.15, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    for xi, v in zip(x + width / 2, r0c_bars):
        if not np.isnan(v):
            ax.text(xi, v + 0.15, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel("Marginal out-of-sample R\u00b2 (percentage points)")
    ax.axhline(0, color="#888888", linewidth=0.6)
    ax.legend(frameon=False, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_5_variance_decomposition")
    plt.close(fig)
    log_step("Saved Figure_5_variance_decomposition.")


if __name__ == "__main__":
    main()
