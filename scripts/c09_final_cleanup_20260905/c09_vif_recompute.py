"""C09 item 2: recompute VIF on the FULL design matrix (including year/month
fixed-effect dummies, which the historical VIF check --
final_combined_analysis/raw/step26_E0_vif.csv / step26_R0c_vif.csv -- omitted
entirely) using the C01-corrected combined sample, to check whether "all
VIF<4"/"<5" still holds once the complete estimated design matrix is used."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
from pathlib import Path

import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = result_path('c09_final_cleanup_20260905/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[C09-VIF] {msg}", flush=True)


def compute_vif(X: pd.DataFrame, exclude_intercept=True) -> pd.DataFrame:
    cols = [c for c in X.columns if not (exclude_intercept and c == "Intercept")]
    Xv = X[cols].astype(float)
    vifs = []
    for i, c in enumerate(cols):
        vifs.append({"variable": c, "VIF": variance_inflation_factor(Xv.values, i)})
    return pd.DataFrame(vifs)


def main():
    v9, _, _ = _patch_v9()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    log_step("Building FULL E0 design matrix (incl. year/month FE) on corrected combined sample...")
    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    vif_e0_full = compute_vif(Xe0)
    vif_e0_full.to_csv(RAW_DIR / "c09_E0_vif_full_design_corrected.csv", index=False)
    log_step("E0 full-design VIF:\n" + vif_e0_full.to_string(index=False))
    log_step(f"E0 max VIF (full design) = {vif_e0_full['VIF'].max():.3f}")

    s = combined_r0cb.copy()
    s["customers_v2_log1p"] = pd.Series(
        __import__("numpy").log1p(s["customers_v2_event_excl_reinterruptions"].astype(float)), index=s.index)
    Xr0c, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    vif_r0c_full = compute_vif(Xr0c)
    vif_r0c_full.to_csv(RAW_DIR / "c09_R0c_vif_full_design_corrected.csv", index=False)
    log_step("R0c full-design VIF:\n" + vif_r0c_full.to_string(index=False))
    log_step(f"R0c max VIF (full design) = {vif_r0c_full['VIF'].max():.3f}")

    # also recompute the ORIGINAL restricted (no-FE) variable set for a direct before/after comparison
    restricted_cols_e0 = ["z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
                            "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
                            "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    vif_e0_restricted = compute_vif(Xe0[restricted_cols_e0])
    vif_e0_restricted.to_csv(RAW_DIR / "c09_E0_vif_restricted_corrected.csv", index=False)
    log_step("E0 restricted (no-FE, matches original methodology) VIF, corrected data:\n"
              + vif_e0_restricted.to_string(index=False))

    summary = {
        "E0_full_design_max_vif": float(vif_e0_full["VIF"].max()),
        "E0_full_design_n_vars_above_4": int((vif_e0_full["VIF"] > 4).sum()),
        "E0_full_design_n_vars_above_5": int((vif_e0_full["VIF"] > 5).sum()),
        "E0_full_design_n_vars_above_10": int((vif_e0_full["VIF"] > 10).sum()),
        "R0c_full_design_max_vif": float(vif_r0c_full["VIF"].max()),
        "R0c_full_design_n_vars_above_4": int((vif_r0c_full["VIF"] > 4).sum()),
        "R0c_full_design_n_vars_above_5": int((vif_r0c_full["VIF"] > 5).sum()),
        "R0c_full_design_n_vars_above_10": int((vif_r0c_full["VIF"] > 10).sum()),
        "E0_restricted_max_vif_corrected_data": float(vif_e0_restricted["VIF"].max()),
    }
    (RAW_DIR / "c09_vif_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_step(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
