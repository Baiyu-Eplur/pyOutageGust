"""C09 item 2, corrected computation: the first pass (run_all_c09.py) computed
VIF by dropping the Intercept column entirely before calling
variance_inflation_factor -- for non-centered, always-positive covariates
(log_population, income_deprivation_rate, deprivation_gap_pct, morans_i) this
spuriously inflates VIF, because statsmodels' variance_inflation_factor does
NOT add its own constant; omitting it forces the auxiliary regression through
the origin. Correct usage: sm.add_constant(X), then only report VIF for the
non-constant columns. This script recomputes both the restricted (original
step26 scope, no FE) and full (incl. year/month FE) design matrices with the
constant properly included, on the SAME C01-corrected sample, to determine
whether the earlier 15.7/23.0/42.4/8.2 spike was a real finding or a bug in
the diagnostic itself."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c09_final_cleanup_20260905\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[C09-VIF-FIXED] {msg}", flush=True)


def compute_vif_with_const(X: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in X.columns if c != "Intercept"]
    Xv = X[cols].astype(float)
    Xc = sm.add_constant(Xv, has_constant="add")
    const_pos = list(Xc.columns).index("const")
    vifs = []
    for c in cols:
        i = list(Xc.columns).index(c)
        vifs.append({"variable": c, "VIF": variance_inflation_factor(Xc.values, i)})
    return pd.DataFrame(vifs)


def main():
    v9, _, _ = _patch_v9()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    s = combined_r0cb.copy()
    s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
    Xr0c, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])

    restricted_cols_e0 = ["z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
                           "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
                           "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    restricted_cols_r0c = restricted_cols_e0 + ["z_log1p_customers_v2", "z_log1p_customers_v2_sq"]

    vif_e0_restricted = compute_vif_with_const(Xe0[restricted_cols_e0])
    vif_e0_restricted.to_csv(RAW_DIR / "c09_E0_vif_restricted_FIXED.csv", index=False)
    log_step("E0 restricted VIF (constant included, corrected data):\n" + vif_e0_restricted.to_string(index=False))

    vif_r0c_restricted = compute_vif_with_const(Xr0c[restricted_cols_r0c])
    vif_r0c_restricted.to_csv(RAW_DIR / "c09_R0c_vif_restricted_FIXED.csv", index=False)
    log_step("R0c restricted VIF (constant included, corrected data):\n" + vif_r0c_restricted.to_string(index=False))

    vif_e0_full = compute_vif_with_const(Xe0)
    vif_e0_full.to_csv(RAW_DIR / "c09_E0_vif_full_design_FIXED.csv", index=False)
    log_step("E0 FULL design VIF (incl. year/month FE, constant included, corrected data):\n"
              + vif_e0_full.to_string(index=False))

    vif_r0c_full = compute_vif_with_const(Xr0c)
    vif_r0c_full.to_csv(RAW_DIR / "c09_R0c_vif_full_design_FIXED.csv", index=False)
    log_step("R0c FULL design VIF (incl. year/month FE, constant included, corrected data):\n"
              + vif_r0c_full.to_string(index=False))

    summary = {
        "E0_restricted_max_vif_FIXED": float(vif_e0_restricted["VIF"].max()),
        "R0c_restricted_max_vif_FIXED": float(vif_r0c_restricted["VIF"].max()),
        "E0_full_design_max_vif_FIXED": float(vif_e0_full["VIF"].max()),
        "E0_full_design_n_above_4_FIXED": int((vif_e0_full["VIF"] > 4).sum()),
        "E0_full_design_vars_above_4_FIXED": vif_e0_full.loc[vif_e0_full["VIF"] > 4, "variable"].tolist(),
        "R0c_full_design_max_vif_FIXED": float(vif_r0c_full["VIF"].max()),
        "R0c_full_design_n_above_4_FIXED": int((vif_r0c_full["VIF"] > 4).sum()),
        "R0c_full_design_vars_above_4_FIXED": vif_r0c_full.loc[vif_r0c_full["VIF"] > 4, "variable"].tolist(),
    }
    (RAW_DIR / "c09_vif_summary_FIXED.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_step(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
