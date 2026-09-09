"""Command #16 Step 1: rebuild a clean development sample with the
locked_temporal_test date block (>= 2023-09-30) excluded, using whole-date-block
exclusion (not row-level random exclusion), consistent with the project's
GroupKFold-by-date discipline.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
from pathlib import Path

import numpy as np
import pandas as pd

SRC = external_path('rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')
OUT_DIR = result_path('dev_sample_decontamination')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"
LOCKED_START = pd.Timestamp("2023-09-30")


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
    print(f"[v16-step1] {msg}", flush=True)


def main():
    log_step("Loading v3 stage-level dataset...")
    df = pd.read_csv(
        read_input(SRC),
        usecols=[
            INCIDENT_COL, "incident_date_utc", "clean_start", "Start Date and Time", "End Date and Time",
            "cause_group_official", "weather_status_v3",
            "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
            "duration_A_customer_weighted_hours",
        ],
        low_memory=False,
    )
    n_stage_total = len(df)
    event = df.drop_duplicates(INCIDENT_COL).copy()
    n_event_total = len(event)
    event["incident_date_utc_dt"] = pd.to_datetime(event["incident_date_utc"], errors="coerce")

    # ---------------- boundary edge-case check ----------------
    log_step("Checking boundary edge cases (events starting before the locked window "
              "but with End Date and Time extending into or past it)...")
    end_all = pd.to_datetime(df["End Date and Time"], errors="coerce", utc=True).dt.tz_localize(None)
    df["_end_dt"] = end_all
    max_end_by_incident = df.groupby(INCIDENT_COL)["_end_dt"].max()
    event = event.set_index(INCIDENT_COL, drop=False)
    event["max_stage_end"] = max_end_by_incident

    pre_locked = event["incident_date_utc_dt"] < LOCKED_START
    straddling = pre_locked & (event["max_stage_end"] >= LOCKED_START)
    n_straddling = int(straddling.sum())

    boundary_report = {
        "n_events_starting_before_locked_window": int(pre_locked.sum()),
        "n_straddling_events_end_extends_into_or_past_locked_window": n_straddling,
        "straddling_event_ids_sample": event.loc[straddling, INCIDENT_COL].head(20).tolist(),
    }
    (RAW_DIR / "step1_boundary_edge_cases.json").write_text(js(boundary_report), encoding="utf-8")
    log_step(f"Boundary check: {n_straddling} straddling events found "
              f"(out of {int(pre_locked.sum())} events starting before the locked window).")

    # ---------------- apply whole-date-block exclusion ----------------
    log_step("Applying whole-date-block exclusion (incident_date_utc >= 2023-09-30 removed)...")
    clean_mask = event["incident_date_utc_dt"] < LOCKED_START
    clean_event = event.loc[clean_mask].copy()
    excluded_event = event.loc[~clean_mask].copy()

    n_event_clean = len(clean_event)
    n_event_excluded = len(excluded_event)

    # verify zero date overlap
    clean_dates = set(clean_event["incident_date_utc_dt"].dt.date.dropna())
    locked_dates = set(excluded_event["incident_date_utc_dt"].dt.date.dropna())
    overlap_dates = clean_dates & locked_dates
    max_clean_date = clean_event["incident_date_utc_dt"].max()
    min_excluded_date = excluded_event["incident_date_utc_dt"].min()

    # cause-code + weather-matched + complete-predictor funnel (WT main spec), on clean sample
    wt_mask = clean_event["cause_group_official"].isin({"weather_natural", "technical_asset"})
    n_wt = int(wt_mask.sum())
    wt_matched_mask = wt_mask & clean_event["weather_status_v3"].eq("matched")
    n_wt_matched = int(wt_matched_mask.sum())

    summary = {
        "n_stage_rows_total_v3": int(n_stage_total),
        "n_event_total_v3": int(n_event_total),
        "n_event_clean_dev_sample": n_event_clean,
        "n_event_excluded_locked_window": n_event_excluded,
        "excluded_pct_of_total": float(n_event_excluded / n_event_total * 100),
        "overlap_dates_check": len(overlap_dates),
        "max_date_in_clean_sample": str(max_clean_date),
        "min_date_in_excluded_sample": str(min_excluded_date),
        "n_wt_cause_code_clean": n_wt,
        "n_wt_weather_matched_clean": n_wt_matched,
    }
    (RAW_DIR / "step1_clean_sample_summary.json").write_text(js(summary), encoding="utf-8")
    log_step(f"Clean dev sample: n={n_event_clean} events ({n_event_excluded} excluded, "
              f"{n_event_excluded / n_event_total * 100:.2f}%). Overlap dates: {len(overlap_dates)}.")
    log_step(f"Max date in clean sample: {max_clean_date}; min date in excluded sample: {min_excluded_date}.")
    log_step(f"WT cause-code clean n={n_wt}; WT weather-matched clean n={n_wt_matched}.")

    # persist the clean event-id list for reuse in Step 2-4
    clean_event[[INCIDENT_COL]].to_csv(RAW_DIR / "clean_dev_sample_incident_ids.csv", index=False)

    log_step("Done.")


if __name__ == "__main__":
    main()
