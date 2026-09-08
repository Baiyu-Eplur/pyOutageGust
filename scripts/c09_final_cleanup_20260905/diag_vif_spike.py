"""Diagnostic: why do log_population/income_deprivation_rate/deprivation_gap_pct/
morans_i show much higher VIF on the corrected sample (15.7/23.0/42.4/8.2) than
the original step26 check (1.34/2.58/3.75/2.51)? These are location-level
covariates untouched by the C01 date/weather fix, so investigate sample
composition (n distinct LAD, missingness/imputation, correlation structure)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402


def log_step(msg):
    print(f"[DIAG] {msg}", flush=True)


def main():
    v9, _, _ = _patch_v9()
    _, combined_e0, _, _ = build_corrected_combined_samples()

    cols = ["log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i", "urban_binary"]
    log_step(f"combined_e0 n={len(combined_e0)}")
    for c in cols:
        s = combined_e0[c]
        log_step(f"{c}: n_nonnull={s.notna().sum()}, n_null={s.isna().sum()}, n_unique={s.nunique()}, "
                  f"std={s.std():.4f}")

    if "LAD21CD" in combined_e0.columns:
        log_step(f"n_distinct_LAD21CD in combined_e0 = {combined_e0['LAD21CD'].nunique()}")

    corr = combined_e0[cols].astype(float).corr()
    log_step("Pairwise correlation matrix:\n" + corr.to_string())

    # check the actual z_-scaled columns used in design matrix, if scaling introduces near-duplicate cols
    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    zcols = [c for c in Xe0.columns if c in
             ("log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i", "urban_binary")]
    log_step(f"Design-matrix columns matching: {zcols}")
    log_step("Design-matrix pairwise correlation:\n" + Xe0[zcols].astype(float).corr().to_string())
    log_step("Design-matrix column stds:\n" + Xe0[zcols].astype(float).std().to_string())
    log_step("Design-matrix column describe:\n" + Xe0[zcols].astype(float).describe().to_string())


if __name__ == "__main__":
    main()
