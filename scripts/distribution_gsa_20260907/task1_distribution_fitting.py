"""Command #53, Task 1: descriptive distribution fitting for the continuous
covariates listed in Table 2, on the C01+C02-C08 corrected final combined
(weather_natural+technical_asset) sample. Uses distfit (distr='full', ~89
scipy.stats continuous candidates) rather than fitter's default common-
distribution set (~10), per the instruction to prefer whichever tool covers
more candidate distributions. Read-only w.r.t. all model results; purely
descriptive, does not touch any regression coefficient.

Practical note (disclosed, not hidden): fitting ~89 distributions via MLE on
the full sample (n up to ~60,000) is prohibitively slow (~65s per variable at
n=5,000 already; scales worse with n). Each variable is fit on a random
subsample of 5,000 observations (fixed seed for reproducibility) -- standard
practice for descriptive shape-fitting, where the qualitative ranking of
candidate distributions is not expected to be sensitive to subsampling at
this size.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from distfit import distfit

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\distribution_gsa_20260907\raw")
FIG_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\distribution_gsa_20260907\figures")
RAW_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SUBSAMPLE_N = 5000
SEED = 20260907

# Table 2 continuous covariates -> (column name, display name for plots)
VARIABLES = {
    "gust_0h": "Gust speed (m/s)",
    "precipitation_24h_sum": "24h cumulative precipitation (mm)",
    "temperature_0h": "Temperature (\u00b0C)",
    "pressure_msl_0h": "Mean sea level pressure (hPa)",
    "log_population": "log population",
    "income_deprivation_rate": "Income deprivation rate",
    "deprivation_gap_pct": "Deprivation gap (percentage points)",
    "morans_i": "Moran's I",
}


def log_step(msg):
    print(f"[task1] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return str(o)
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def main():
    apply_style()
    combined_wt, _, _, _ = build_corrected_combined_samples()
    log_step(f"combined_wt n={len(combined_wt)}")

    rng = np.random.default_rng(SEED)
    results = {}

    for col, disp in VARIABLES.items():
        full = combined_wt[col].astype(float).dropna().to_numpy()
        n_full = len(full)
        if n_full > SUBSAMPLE_N:
            idx = rng.choice(n_full, size=SUBSAMPLE_N, replace=False)
            data = full[idx]
        else:
            data = full
        log_step(f"--- {col} ({disp}): n_full={n_full}, n_fit_subsample={len(data)} ---")
        log_step(f"    full-sample mean={full.mean():.5f}, std={full.std(ddof=1):.5f}, "
                  f"min={full.min():.5f}, max={full.max():.5f}, skew={pd.Series(full).skew():.4f}")

        dfit = distfit(distr="full", todf=True, verbose=0)
        dfit.fit_transform(data, verbose=0)
        top3 = dfit.summary.head(3)[["name", "score", "loc", "scale", "arg"]].copy()
        log_step(f"    Top 3 (score = distfit RSS on binned histogram, lower is better):\n"
                  + top3.to_string(index=False))

        best_name = dfit.model["name"]
        best_params = dfit.model["params"]
        best_score = float(dfit.model["score"])
        log_step(f"    BEST: {best_name}, params={best_params}, score={best_score:.6f}")

        # goodness-of-fit figure: histogram + best-fit pdf overlay
        fig_w = mm_to_in(SINGLE_COL_MM) * 1.5
        fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.72))
        ax.hist(full, bins=60, density=True, color="#1b9e77", alpha=0.45, edgecolor="none", label="Observed")
        xs = np.linspace(full.min(), full.max(), 400)
        from scipy import stats as sstats
        dist_obj = getattr(sstats, best_name)
        pdf = dist_obj.pdf(xs, *best_params)
        ax.plot(xs, pdf, color="#d95f02", linewidth=1.6, label=f"Best fit: {best_name}")
        ax.set_xlabel(disp)
        ax.set_ylabel("Density")
        ax.legend(frameon=False, fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        save_fig(fig, FIG_DIR, f"FigureA_dist_{col}")
        plt.close(fig)

        results[col] = {
            "display_name": disp,
            "n_full": int(n_full), "n_fit_subsample": int(len(data)),
            "full_sample_mean": float(full.mean()), "full_sample_std": float(full.std(ddof=1)),
            "full_sample_min": float(full.min()), "full_sample_max": float(full.max()),
            "full_sample_skew": float(pd.Series(full).skew()),
            "top3_candidates": top3.to_dict("records"),
            "best_distribution": best_name,
            "best_params": [float(p) for p in best_params],
            "best_score_rss": best_score,
        }

    (RAW_DIR / "task1_distribution_fitting_results.json").write_text(js(results), encoding="utf-8")
    log_step("Saved task1_distribution_fitting_results.json")

    # summary table
    rows = []
    for col, r in results.items():
        rows.append({
            "variable": col, "display_name": r["display_name"],
            "best_distribution": r["best_distribution"], "score_rss": r["best_score_rss"],
            "mean": r["full_sample_mean"], "std": r["full_sample_std"], "skew": r["full_sample_skew"],
        })
    pd.DataFrame(rows).to_csv(RAW_DIR / "task1_summary_table.csv", index=False)
    log_step("Saved task1_summary_table.csv")


if __name__ == "__main__":
    main()
