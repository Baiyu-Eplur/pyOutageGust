"""Command #21 Step 0: build the final combined analysis sample by concatenating
command #16's clean development sample with command #19's locked_temporal_test
holdout sample (both already restricted to weather_natural+technical_asset,
complete predictors, using identical construction pipelines).
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(project_path('scripts/dev_sample_decontamination')))
from clean_sample_builder import build_clean_wt_samples, v9  # noqa: E402

sys.path.insert(0, str(project_path('scripts/module_e_final_confirmation')))
from build_holdout_sample import build_holdout_wt_samples  # noqa: E402

INCIDENT_COL = "Incident Reference"


def log_step(msg):
    print(f"[v21-combined] {msg}", flush=True)


def build_combined_samples():
    log_step("Building command #16 clean development sample...")
    dev_wt, dev_e0, dev_r0cb, dev_p99 = build_clean_wt_samples()

    log_step("Building command #19 holdout sample...")
    holdout_wt, holdout_e0, holdout_r0cb, holdout_p99 = build_holdout_wt_samples()

    # ---- Step 0 verification ----
    dev_dates = pd.to_datetime(dev_wt["incident_date_utc"])
    holdout_dates = pd.to_datetime(holdout_wt["incident_date_utc"])
    date_overlap = set(dev_dates.dt.date) & set(holdout_dates.dt.date)

    dev_ids = set(dev_wt[INCIDENT_COL])
    holdout_ids = set(holdout_wt[INCIDENT_COL])
    id_overlap = dev_ids & holdout_ids

    combined_wt = pd.concat([dev_wt, holdout_wt], ignore_index=True)
    combined_e0 = pd.concat([dev_e0, holdout_e0], ignore_index=True)
    combined_r0cb_raw = pd.concat([dev_r0cb, holdout_r0cb], ignore_index=True)

    verification = {
        "dev_wt_n": len(dev_wt),
        "holdout_wt_n": len(holdout_wt),
        "combined_wt_n": len(combined_wt),
        "sum_check_passed": len(combined_wt) == len(dev_wt) + len(holdout_wt),
        "date_overlap_count": len(date_overlap),
        "id_overlap_count": len(id_overlap),
        "combined_unique_ids": combined_wt[INCIDENT_COL].nunique(),
        "combined_ids_match_rows": combined_wt[INCIDENT_COL].nunique() == len(combined_wt),
        "dev_e0_n": len(dev_e0), "holdout_e0_n": len(holdout_e0), "combined_e0_n": len(combined_e0),
        "dev_r0cb_n": len(dev_r0cb), "holdout_r0cb_n": len(holdout_r0cb),
    }

    # NOTE: dev_r0cb and holdout_r0cb each already applied their OWN p99 cap
    # (computed on their own respective duration_B distributions per commands
    # #16/#19). For the combined final sample, command #21 Step0 does not ask us
    # to recompute a fresh p99 cap on the pooled distribution -- but a fresh cap
    # is the methodologically correct choice for a genuine "final combined
    # sample" fit (matching how every prior command always recomputed its own
    # p99 on whatever sample it was fitting). We recompute it here and disclose
    # both numbers.
    combined_r0cb_base = pd.concat([
        dev_wt.loc[dev_wt["duration_B_full_span_hours"].notna() & (dev_wt["duration_B_full_span_hours"] > 0)],
        holdout_wt.loc[holdout_wt["duration_B_full_span_hours"].notna() & (holdout_wt["duration_B_full_span_hours"] > 0)],
    ], ignore_index=True)
    combined_p99 = combined_r0cb_base["duration_B_full_span_hours"].quantile(0.99)
    combined_r0cb = combined_r0cb_base.loc[combined_r0cb_base["duration_B_full_span_hours"] <= combined_p99].copy()
    combined_r0cb = combined_r0cb.loc[combined_r0cb["customers_v2_event_excl_reinterruptions"].notna()].copy()
    combined_r0cb["log_duration_B_full_span_hours"] = np.log(combined_r0cb["duration_B_full_span_hours"].astype(float))
    combined_r0cb["log1p_customers_v2"] = np.log1p(combined_r0cb["customers_v2_event_excl_reinterruptions"].astype(float))

    verification["combined_p99_cap_hours_recomputed"] = float(combined_p99)
    verification["dev_p99_cap_hours"] = float(dev_p99)
    verification["holdout_p99_cap_hours"] = float(holdout_p99)
    verification["combined_r0cb_n_recomputed_cap"] = len(combined_r0cb)

    return combined_wt, combined_e0, combined_r0cb, verification


if __name__ == "__main__":
    import json

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

    OUT_DIR = result_path('final_combined_analysis')
    RAW_DIR = OUT_DIR / "raw"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    combined_wt, combined_e0, combined_r0cb, verification = build_combined_samples()
    (RAW_DIR / "step0_verification.json").write_text(js(verification), encoding="utf-8")
    print(json.dumps(verification, indent=2, ensure_ascii=False))
