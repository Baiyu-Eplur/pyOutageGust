"""Command #53, Task 1 supplement: distfit's default 'score' (RSS on the
binned histogram density) is NOT comparable across variables with different
value ranges/densities -- it is only valid for ranking candidate
distributions WITHIN a single variable. This script adds the
Kolmogorov-Smirnov statistic (scipy.stats.kstest, comparing the empirical
CDF against each variable's best-fit distribution's CDF) as a
cross-variable-comparable goodness-of-fit measure, computed on the SAME
best-distribution/parameter choice already selected by task1 (no new
fitting, just a different diagnostic on the existing result)."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

RAW_DIR = result_path('distribution_gsa_20260907/raw')


def log_step(msg):
    print(f"[task1b] {msg}", flush=True)


def main():
    results = json.loads((read_input(RAW_DIR / "task1_distribution_fitting_results.json")).read_text(encoding="utf-8"))
    combined_wt, _, _, _ = build_corrected_combined_samples()

    ks_rows = []
    for col, r in results.items():
        full = combined_wt[col].astype(float).dropna().to_numpy()
        dist_obj = getattr(sstats, r["best_distribution"])
        params = tuple(r["best_params"])
        ks_stat, ks_p = sstats.kstest(full, dist_obj.cdf, args=params)
        log_step(f"{col}: best={r['best_distribution']}, KS stat={ks_stat:.4f}, KS p-value={ks_p:.3g} "
                  f"(n={len(full)}; with this large n, KS p-value is expected to reject even visually good fits -- "
                  f"the KS STATISTIC magnitude, not the p-value, is the practically informative number here)")
        ks_rows.append({"variable": col, "best_distribution": r["best_distribution"],
                          "ks_statistic": float(ks_stat), "ks_pvalue": float(ks_p)})

    df = pd.DataFrame(ks_rows).sort_values("ks_statistic")
    df.to_csv(RAW_DIR / "task1b_ks_supplement.csv", index=False)
    log_step("Ranked by KS statistic (lower = better cross-variable-comparable fit):\n" + df.to_string(index=False))
    log_step("Saved task1b_ks_supplement.csv")


if __name__ == "__main__":
    main()
