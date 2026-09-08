"""C01 repair Step 4c: compute the SAME fold-stability + variance-decomposition
diagnostics as step4b, but on the ORIGINAL (uncorrected, pre-C01-fix) final
combined sample, using the identical methodology (fresh 5-fold GroupKFold +
v9.run_model/stability_summary + v14.nested_r2_sequence). This gives a true
apples-to-apples 'before' baseline for Step 4's comparison, since command #21
itself never computed a fold-level coefficient stability table for the final
combined sample (it only reported a single full-sample fit + bootstrap)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905\raw")


def log_step(msg):
    print(f"[C01-step4c] {msg}", flush=True)


def main():
    log_step("Building the ORIGINAL (uncorrected) final combined sample...")
    _, combined_e0, combined_r0cb, _ = build_combined_samples()
    log_step(f"Original combined E0 n={len(combined_e0)}, R0c n={len(combined_r0cb)}")

    sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation")))
    import v3_validation_pipeline as v9  # noqa: E402

    from sklearn.model_selection import GroupKFold

    def add_fresh_folds(df):
        d = df.copy()
        d["incident_date_utc"] = pd.to_datetime(d["incident_date_utc"], errors="coerce")
        gkf = GroupKFold(n_splits=5)
        d["cv_fold_v3"] = -1
        groups = d["incident_date_utc"].dt.date.astype(str)
        X_dummy = np.zeros(len(d))
        for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
            d.iloc[valid_idx, d.columns.get_loc("cv_fold_v3")] = fold_idx
        n_crossing = int((d.groupby(groups)["cv_fold_v3"].nunique() > 1).sum())
        assert n_crossing == 0
        return d

    log_step("Building fresh 5-fold GroupKFold splits (original sample)...")
    combined_e0_folds = add_fresh_folds(combined_e0)
    combined_r0cb_folds = add_fresh_folds(combined_r0cb)

    log_step("Fitting per-fold coefficients (original E0)...")
    e0_fold_df = v9.run_model(combined_e0_folds, "log1p_customers_v2", "E0_original",
                                ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=False)
    log_step("Fitting per-fold coefficients (original R0c)...")
    r0c_fold_df = v9.run_model(combined_r0cb_folds, "log_duration_B_full_span_hours", "R0c_original",
                                 ["z_gust_0h", "z_gust_0h_sq"], use_customers_covariate=True)

    e0_stability = v9.stability_summary(e0_fold_df)
    r0c_stability = v9.stability_summary(r0c_fold_df)
    e0_fold_df.to_csv(RAW_DIR / "step4c_E0_original_fold_coefs.csv", index=False)
    r0c_fold_df.to_csv(RAW_DIR / "step4c_R0c_original_fold_coefs.csv", index=False)
    e0_stability.to_csv(RAW_DIR / "step4c_E0_original_stability.csv", index=False)
    r0c_stability.to_csv(RAW_DIR / "step4c_R0c_original_stability.csv", index=False)
    log_step("E0 (original) stability:\n" + e0_stability.to_string(index=False))
    log_step("R0c (original) stability:\n" + r0c_stability.to_string(index=False))

    spec14 = importlib.util.spec_from_file_location(
        "variance_decomposition_pipeline",
        r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
    v14 = importlib.util.module_from_spec(spec14)
    spec14.loader.exec_module(v14)

    log_step("Variance decomposition (original E0)...")
    e0_var = v14.nested_r2_sequence(combined_e0_folds, "log1p_customers_v2", ["nongust_weather", "gust"],
                                      "E0_original")
    e0_var.to_csv(RAW_DIR / "step4c_E0_original_variance_decomposition.csv", index=False)
    log_step(e0_var.to_string(index=False))

    log_step("Variance decomposition (original R0c, gust-first)...")
    r0c_var = v14.nested_r2_sequence(combined_r0cb_folds, "log_duration_B_full_span_hours",
                                       ["nongust_weather", "gust", "customers"],
                                       "R0c_original_order_gust_then_customers")
    r0c_var.to_csv(RAW_DIR / "step4c_R0c_original_variance_decomposition_gust_first.csv", index=False)
    log_step(r0c_var.to_string(index=False))

    log_step("Variance decomposition (original R0c, customers-first)...")
    r0c_var2 = v14.nested_r2_sequence(combined_r0cb_folds, "log_duration_B_full_span_hours",
                                        ["nongust_weather", "customers", "gust"],
                                        "R0c_original_order_customers_then_gust")
    r0c_var2.to_csv(RAW_DIR / "step4c_R0c_original_variance_decomposition_customers_first.csv", index=False)
    log_step(r0c_var2.to_string(index=False))

    log_step("=== Step 4c complete ===")


if __name__ == "__main__":
    main()
