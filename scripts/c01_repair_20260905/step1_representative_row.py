"""C01 repair Step 1: recompute the correct event-representative row (earliest
UTC start time, tie-broken by source_row_number) for every unique Incident
Reference in the v3 stage-level dataset, and compare it against the OLD
representative row (drop_duplicates(keep='first') on file order, equivalent
to min source_row_number, which is what v3_validation_pipeline.py's
step0_build_sample() actually uses).

Read-only against ukpn_full_stage_dataset_v3.csv. Writes only under
claude_branch/results/c01_repair_20260905/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"
STAGE_COL = "Restoration Stage"
START_COL = "Start Date and Time"

USECOLS = [
    "source_row_number", INCIDENT_COL, STAGE_COL, START_COL,
    "lat", "lon", "weather_status_v3", "cause_group_official",
    "gust_0h", "pressure_msl_0h",
]


def log_step(msg):
    print(f"[C01-step1] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, pd.Timestamp):
            return str(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def main():
    log_step("Loading v3 stage-level dataset (selected columns only)...")
    df = pd.read_csv(SRC, usecols=USECOLS, low_memory=False)
    log_step(f"Loaded {len(df)} stage rows, {df[INCIDENT_COL].nunique()} unique incidents.")

    df["start_utc"] = pd.to_datetime(df[START_COL], errors="coerce", utc=True)
    n_unparseable = df["start_utc"].isna().sum()
    log_step(f"Rows with unparseable start time: {n_unparseable}")

    # ---- OLD representative row: file order first = min source_row_number ----
    old_rep = (
        df.sort_values("source_row_number")
        .drop_duplicates(INCIDENT_COL, keep="first")
        .set_index(INCIDENT_COL)
    )

    # ---- NEW representative row: earliest start_utc, tie-break by source_row_number ----
    df_valid = df.dropna(subset=["start_utc"]).copy()
    df_sorted = df_valid.sort_values(["start_utc", "source_row_number"])
    new_rep = df_sorted.drop_duplicates(INCIDENT_COL, keep="first").set_index(INCIDENT_COL)

    # events where ALL stages have unparseable start time (cannot determine a new rep row)
    all_ids = set(df[INCIDENT_COL].unique())
    resolvable_ids = set(new_rep.index)
    unresolvable_ids = all_ids - resolvable_ids
    log_step(f"Incidents with at least one parseable start time (resolvable): {len(resolvable_ids)}")
    log_step(f"Incidents with NO parseable start time at all (unresolvable): {len(unresolvable_ids)}")

    # ---- ties in the new selection: count incidents with >1 row sharing the min start_utc ----
    min_time_per_incident = df_valid.groupby(INCIDENT_COL)["start_utc"].transform("min")
    is_tied_min = df_valid["start_utc"] == min_time_per_incident
    tie_counts = is_tied_min.groupby(df_valid[INCIDENT_COL]).sum()
    n_incidents_with_ties = int((tie_counts > 1).sum())
    log_step(f"Incidents with a tie at the minimum start time (>1 stage sharing the earliest "
              f"start_utc, resolved via source_row_number): {n_incidents_with_ties}")

    # ---- build the full comparison table (only for resolvable incidents) ----
    comparison_rows = []
    for inc_id in resolvable_ids:
        new_row = new_rep.loc[inc_id]
        old_row = old_rep.loc[inc_id] if inc_id in old_rep.index else None
        if old_row is None:
            continue
        new_src_row = int(new_row["source_row_number"])
        old_src_row = int(old_row["source_row_number"])
        changed = new_src_row != old_src_row
        new_start = new_row["start_utc"]
        old_start = old_row["start_utc"]
        time_diff_h = (
            (old_start - new_start).total_seconds() / 3600.0
            if pd.notna(old_start) and pd.notna(new_start) else np.nan
        )
        comparison_rows.append({
            "Incident Reference": inc_id,
            "new_source_row": new_src_row,
            "new_start_utc": new_start,
            "new_stage": new_row[STAGE_COL],
            "old_source_row": old_src_row,
            "old_start_utc": old_start,
            "old_stage": old_row[STAGE_COL],
            "representative_row_changed": changed,
            "time_diff_hours_old_minus_new": time_diff_h,
            "new_gust_0h": new_row["gust_0h"],
            "old_gust_0h": old_row["gust_0h"],
            "gust_0h_diff": (
                new_row["gust_0h"] - old_row["gust_0h"]
                if pd.notna(new_row["gust_0h"]) and pd.notna(old_row["gust_0h"]) else np.nan
            ),
            "lat": new_row["lat"], "lon": new_row["lon"],
            "weather_status_v3": new_row["weather_status_v3"],
            "cause_group_official": new_row["cause_group_official"],
        })

    comp_df = pd.DataFrame(comparison_rows)
    log_step(f"Comparison table built: {len(comp_df)} incidents.")

    n_changed = int(comp_df["representative_row_changed"].sum())
    pct_changed = n_changed / len(comp_df) * 100
    log_step(f"Representative row changed: {n_changed} / {len(comp_df)} ({pct_changed:.2f}%)")

    comp_df.to_csv(RAW_DIR / "step1_representative_row_comparison_full.csv", index=False)
    log_step(f"Saved full event-level comparison table: "
              f"raw/step1_representative_row_comparison_full.csv ({len(comp_df)} rows)")

    changed_df = comp_df[comp_df["representative_row_changed"]].copy()
    changed_df.to_csv(RAW_DIR / "step1_changed_events_only.csv", index=False)
    log_step(f"Saved changed-only subset: raw/step1_changed_events_only.csv ({len(changed_df)} rows)")

    summary = {
        "n_total_incidents_v3": int(df[INCIDENT_COL].nunique()),
        "n_stage_rows_unparseable_start_time": int(n_unparseable),
        "n_incidents_unresolvable_no_parseable_start": len(unresolvable_ids),
        "unresolvable_incident_ids": sorted(unresolvable_ids)[:200],
        "n_incidents_with_tie_at_min_start_time": n_incidents_with_ties,
        "n_incidents_compared": len(comp_df),
        "n_representative_row_changed": n_changed,
        "pct_representative_row_changed": pct_changed,
        "time_diff_hours_stats_changed_only": {
            "mean": float(changed_df["time_diff_hours_old_minus_new"].mean()),
            "median": float(changed_df["time_diff_hours_old_minus_new"].median()),
            "std": float(changed_df["time_diff_hours_old_minus_new"].std()),
            "min": float(changed_df["time_diff_hours_old_minus_new"].min()),
            "max": float(changed_df["time_diff_hours_old_minus_new"].max()),
        },
        "gust_0h_diff_stats_changed_only": {
            "n_valid": int(changed_df["gust_0h_diff"].notna().sum()),
            "mean": float(changed_df["gust_0h_diff"].mean()),
            "median": float(changed_df["gust_0h_diff"].median()),
            "std": float(changed_df["gust_0h_diff"].std()),
            "n_abs_gt_1ms": int((changed_df["gust_0h_diff"].abs() > 1.0).sum()),
        },
    }
    (RAW_DIR / "step1_summary.json").write_text(js(summary), encoding="utf-8")
    log_step("Saved raw/step1_summary.json")
    log_step(json.dumps({k: v for k, v in summary.items() if k != "unresolvable_incident_ids"}, indent=2, default=str))


if __name__ == "__main__":
    main()
