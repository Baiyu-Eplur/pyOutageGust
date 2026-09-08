"""Command #37 Figure 4: gust dose-response curves for E0 (exposure) and R0c
(recovery), reusing command #21 Step3's existing 50-grid-point curve data
(03_阵风剂量反应曲线.csv) -- no new modeling, pure visualization."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from figure_style import apply_style, mm_to_in, save_fig, panel_label, DOUBLE_COL_MM  # noqa: E402

RESULTS_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
OUT_DIR = RESULTS_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# command #21 Step2 critical wind speed (E0): point 10.69 m/s, Bootstrap 95% CI [9.20, 12.06]
TURNING_POINT_MS = 10.693754982765721
BOOTSTRAP_CI_MS = (9.203112927593448, 12.059964209497657)
R0C_GUST_SQ_P = 2.7747599425673083e-36


def log_step(msg):
    print(f"[fig4] {msg}", flush=True)


def main():
    apply_style()
    df = pd.read_csv(RESULTS_DIR / "03_阵风剂量反应曲线.csv")
    e0 = df[df["model"] == "E0_gust_dose_response"].sort_values("gust_ms")
    r0c = df[df["model"] == "R0c_gust_dose_response"].sort_values("gust_ms")
    log_step(f"E0 grid points: {len(e0)}, R0c grid points: {len(r0c)}")

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.42))

    # ---- (a) E0: predicted customers_v2 vs gust, with critical wind speed ----
    ax = axes[0]
    ax.axvspan(BOOTSTRAP_CI_MS[0], BOOTSTRAP_CI_MS[1], color="#1b9e77", alpha=0.15,
               label="Bootstrap 95% CI")
    ax.axvline(TURNING_POINT_MS, color="#1b9e77", linewidth=1.0, linestyle="--")
    ax.plot(e0["gust_ms"], e0["predicted_level"], color="#333333", linewidth=1.4)
    ax.set_xlabel("Gust speed (m/s)")
    ax.set_ylabel("Predicted affected customers")
    ax.text(TURNING_POINT_MS + 0.6, ax.get_ylim()[1] * 0.05 + ax.get_ylim()[0],
             "critical wind\nspeed 10.69 m/s", fontsize=9, color="#1b9e77", va="bottom")
    panel_label(ax, "(a)")

    # ---- (b) R0c: predicted duration_B vs gust (customers_v2 fixed at mean) ----
    ax = axes[1]
    ax.plot(r0c["gust_ms"], r0c["predicted_level"], color="#333333", linewidth=1.4)
    ax.set_xlabel("Gust speed (m/s)")
    ax.set_ylabel("Predicted restoration duration (h)")
    ax.text(0.05, 0.92, f"quadratic term significant\n(p={R0C_GUST_SQ_P:.1e})",
             transform=ax.transAxes, fontsize=9, va="top", ha="left", color="#d95f02")
    panel_label(ax, "(b)")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_4_dose_response")
    plt.close(fig)
    log_step("Saved Figure_4_dose_response.")


if __name__ == "__main__":
    main()
