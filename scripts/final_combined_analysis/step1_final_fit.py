"""Command #21 Step 1: full-sample E0/R0c fit on the final combined sample,
reporting the COMPLETE coefficient table (not just gust terms)."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def log_step(msg):
    print(f"[v21-step1] {msg}", flush=True)


def full_coef_table(res, cov):
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    return pd.DataFrame({
        "term": res.params.index, "coefficient": res.params.values, "std_error": se,
        "ci_low": res.params.values - 1.96 * se, "ci_high": res.params.values + 1.96 * se, "p_value": p,
    })


def main():
    combined_wt, combined_e0, combined_r0cb, verification = build_combined_samples()

    log_step("Fitting E0 (final, full-sample, combined n=%d)..." % len(combined_e0))
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = v11.fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False)
    e0_table = full_coef_table(res_e0, cov_e0)
    e0_table.to_csv(RAW_DIR / "step1_E0_final_full_coefs.csv", index=False)
    print("=== E0 full coefficient table ===")
    print(e0_table.to_string(index=False))

    log_step("Fitting R0c (final, full-sample, combined n=%d)..." % len(combined_r0cb))
    res_r0c, cov_r0c, mean_gust_r0c, sd_gust_r0c, d_r0c = v11.fit_full_sample(
        combined_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True)
    r0c_table = full_coef_table(res_r0c, cov_r0c)
    r0c_table.to_csv(RAW_DIR / "step1_R0c_final_full_coefs.csv", index=False)
    print("=== R0c full coefficient table ===")
    print(r0c_table.to_string(index=False))

    meta = {
        "e0_n": int(len(combined_e0)), "r0c_n": int(len(combined_r0cb)),
        "e0_r2": float(res_e0.rsquared), "r0c_r2": float(res_r0c.rsquared),
        "gust_mean_e0": float(mean_gust_e0), "gust_sd_e0": float(sd_gust_e0),
        "gust_mean_r0c": float(mean_gust_r0c), "gust_sd_r0c": float(sd_gust_r0c),
    }
    (RAW_DIR / "step1_meta.json").write_text(js(meta), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    log_step("Done.")


if __name__ == "__main__":
    main()
