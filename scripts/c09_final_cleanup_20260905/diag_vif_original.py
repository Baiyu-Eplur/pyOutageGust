"""Diagnostic: reproduce the restricted-variable VIF check on the ORIGINAL
(uncorrected, pre-C01) sample pipeline, to check whether the historical
step26_E0_vif.csv numbers (max ~3.75) are still reproducible today with the
CURRENT codebase's sample-building logic, or whether they were already stale
even before C01 (i.e. isolate whether the VIF spike is caused by the C01 fix
specifically, or by some other unrelated change in the combined-sample
pipeline since command #26/27 was originally run)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation")))


def log_step(msg):
    print(f"[DIAG-ORIG] {msg}", flush=True)


def compute_vif(X: pd.DataFrame, cols) -> pd.DataFrame:
    Xv = X[cols].astype(float)
    vifs = [{"variable": c, "VIF": variance_inflation_factor(Xv.values, i)} for i, c in enumerate(cols)]
    return pd.DataFrame(vifs)


def main():
    import combined_sample_builder as csb
    combined_wt, combined_e0, combined_r0cb, verification = csb.build_combined_samples()
    log_step(f"ORIGINAL (uncorrected) combined_wt n={len(combined_wt)}, combined_e0 n={len(combined_e0)}, "
              f"combined_r0cb n={len(combined_r0cb)}")

    import v3_validation_pipeline as v9
    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)

    restricted_cols = ["z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
                        "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
                        "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    vif_orig = compute_vif(Xe0, restricted_cols)
    log_step("E0 restricted VIF on ORIGINAL (uncorrected) sample, current codebase:\n"
              + vif_orig.to_string(index=False))

    cols = ["log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i", "urban_binary"]
    for c in cols:
        s = combined_e0[c]
        log_step(f"{c}: n_nonnull={s.notna().sum()}, n_null={s.isna().sum()}, n_unique={s.nunique()}, "
                  f"std={s.std():.4f}")
    if "LAD21CD" in combined_e0.columns:
        log_step(f"n_distinct_LAD21CD in ORIGINAL combined_e0 = {combined_e0['LAD21CD'].nunique()}")
    log_step("Pairwise correlation (ORIGINAL):\n" + combined_e0[cols].astype(float).corr().to_string())


if __name__ == "__main__":
    main()
