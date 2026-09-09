"""A02: compute the Duan (1983) smearing factor on the C01-corrected E0/R0c
residuals, to quantify how much the naive exp(eta) predictions shown in
Figure 4/6 (command #45 versions, confirmed still using np.exp(eta) directly)
underestimate the true conditional expectation. Read-only diagnostic; does
not modify Figure 4/6 (option (a)/(b) decision is left to the web-side agent
per the command)."""
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

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = result_path('c09_final_cleanup_20260905/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[A02] {msg}", flush=True)


def main():
    v9, _, _ = _patch_v9()
    import statsmodels.api as sm
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    ye0 = combined_e0["log1p_customers_v2"].astype(float)
    res_e0 = sm.OLS(ye0, Xe0).fit()
    smear_e0 = float(np.mean(np.exp(res_e0.resid)))
    log_step(f"E0 (corrected) Duan smearing factor = {smear_e0:.6f}, "
              f"implied naive-exp underestimate = {(1-1/smear_e0)*100:.2f}%")

    s = combined_r0cb.copy()
    s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
    Xr, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    yr = s["log_duration_B_full_span_hours"].astype(float)
    res_r = sm.OLS(yr, Xr).fit()
    smear_r = float(np.mean(np.exp(res_r.resid)))
    log_step(f"R0c (corrected) Duan smearing factor = {smear_r:.6f}, "
              f"implied naive-exp underestimate = {(1-1/smear_r)*100:.2f}%")

    # illustrative concrete example: apply both factors to a couple of reference points
    result = {
        "E0_smearing_factor": smear_e0, "E0_pct_underestimate": (1 - 1 / smear_e0) * 100,
        "R0c_smearing_factor": smear_r, "R0c_pct_underestimate": (1 - 1 / smear_r) * 100,
        "E0_residual_std": float(res_e0.resid.std()),
        "R0c_residual_std": float(res_r.resid.std()),
    }
    (RAW_DIR / "a02_duan_smearing_corrected.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved a02_duan_smearing_corrected.json")


if __name__ == "__main__":
    main()
