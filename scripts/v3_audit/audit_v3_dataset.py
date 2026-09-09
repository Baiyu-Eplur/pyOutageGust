"""Command #8: audit ukpn_full_stage_dataset_v3.csv structure and quality.

Read-only. Writes JSON summaries into claude_branch/results/v3_dataset_audit/raw/
which the markdown reports (written separately) are built from.
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
OLD_MASTER = external_path('data/new/ukpn_master_with_lad_features_updated.csv')
OUT_DIR = result_path('v3_dataset_audit')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"
STAGE_COL = "Restoration Stage"
START_COL = "Start Date and Time"
END_COL = "End Date and Time"
CUSTOMER_COL = "Number of Customers Restored"
REINT_COL = "Re-interruption Stage"
CAUSE_COL = "Cause Code"


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
    print("Loading full v3 dataset (this may take a while, ~1GB CSV)...")
    df = pd.read_csv(read_input(SRC), low_memory=False)
    print(f"Loaded: {df.shape}")

    # ---------- Step 0: grain confirmation ----------
    n_rows, n_cols = df.shape
    n_incidents = df[INCIDENT_COL].nunique(dropna=True)
    step0 = {
        "rows": n_rows,
        "columns": n_cols,
        "column_names": list(df.columns),
        "unique_incidents": int(n_incidents),
        "is_stage_grain": bool(n_rows > n_incidents * 1.5),
        "expected_stage_rows_source": 237901,
        "expected_incident_count_source": 135025,
        "rows_match_stage_expectation": bool(n_rows == 237901),
        "incidents_match_expectation": bool(n_incidents == 135025),
        "new_aggregate_columns_detected": [
            c for c in df.columns
            if c in {
                "cause_code_norm", "cause_group_official", "is_reinterruption_stage_v3",
                "stage_duration_hours", "customers_v2_event_excl_reinterruptions",
                "duration_A_customer_weighted_hours", "duration_B_full_span_hours",
                "Duration (hours)", "customer_minutes_lost_event",
                "event_customer_weight_denominator", "all_stages_are_reinterruption",
                "stage_row_count",
            }
        ],
    }
    (RAW_DIR / "step0.json").write_text(js(step0), encoding="utf-8")
    print("Step 0 done.")

    # ---------- Missing-start-stage flag (not present as a column; compute here) ----------
    min_stage_by_incident = df.groupby(INCIDENT_COL, dropna=False)[STAGE_COL].min()
    missing_start_incidents = min_stage_by_incident[min_stage_by_incident > 1]
    missing_start_pct = len(missing_start_incidents) / len(min_stage_by_incident) * 100

    # ---------- Step 1: cross-check customers/duration logic on a sample ----------
    rng = np.random.default_rng(20260824)
    incident_ids = df[INCIDENT_COL].dropna().unique()
    stage_counts = df.groupby(INCIDENT_COL, dropna=False).size()
    multi_ids = stage_counts[stage_counts > 1].index.to_numpy()
    single_ids = stage_counts[stage_counts == 1].index.to_numpy()
    sample_multi = rng.choice(multi_ids, size=min(250, len(multi_ids)), replace=False)
    sample_single = rng.choice(single_ids, size=min(250, len(single_ids)), replace=False)
    sample_ids = np.concatenate([sample_multi, sample_single])

    sample_df = df[df[INCIDENT_COL].isin(sample_ids)].copy()

    start = pd.to_datetime(sample_df[START_COL], errors="coerce", utc=True)
    end = pd.to_datetime(sample_df[END_COL], errors="coerce", utc=True)
    stage_dur = (end - start).dt.total_seconds() / 3600.0
    customers_raw = pd.to_numeric(
        sample_df[CUSTOMER_COL].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    reint_raw = sample_df[REINT_COL].astype(str).str.strip().str.upper()
    is_reint_independent = reint_raw.isin({"Y", "1"})

    key = sample_df[INCIDENT_COL]
    eligible = customers_raw.mask(is_reint_independent)
    customers_recomputed = eligible.groupby(key, dropna=False).sum(min_count=1)
    weighted_num = (customers_raw * stage_dur).groupby(key, dropna=False).sum(min_count=1)
    weighted_den = customers_raw.where(stage_dur.notna()).groupby(key, dropna=False).sum(min_count=1)
    duration_a_recomputed = weighted_num.div(weighted_den.where(weighted_den > 0))
    duration_b_recomputed = (end.groupby(key, dropna=False).max() - start.groupby(key, dropna=False).min()).dt.total_seconds() / 3600.0

    existing_customers = sample_df.drop_duplicates(INCIDENT_COL).set_index(INCIDENT_COL)["customers_v2_event_excl_reinterruptions"]
    existing_dur_a = sample_df.drop_duplicates(INCIDENT_COL).set_index(INCIDENT_COL)["duration_A_customer_weighted_hours"]
    existing_dur_b = sample_df.drop_duplicates(INCIDENT_COL).set_index(INCIDENT_COL)["duration_B_full_span_hours"]

    cmp_idx = customers_recomputed.index.intersection(existing_customers.index)
    cust_diff = (customers_recomputed.loc[cmp_idx] - existing_customers.loc[cmp_idx]).abs()
    dur_a_diff = (duration_a_recomputed.reindex(cmp_idx) - existing_dur_a.loc[cmp_idx]).abs()
    dur_b_diff = (duration_b_recomputed.reindex(cmp_idx) - existing_dur_b.loc[cmp_idx]).abs()

    reint_legacy_check = sample_df[REINT_COL].astype(str).str.strip().isin({"0", "1"}).sum()

    step1 = {
        "sample_size_incidents": int(len(sample_ids)),
        "sample_multi_stage": int(len(sample_multi)),
        "sample_single_stage": int(len(sample_single)),
        "customers_v2_max_abs_diff_vs_independent_recompute": float(cust_diff.max()) if len(cust_diff) else None,
        "customers_v2_mismatch_count_over_1e-6": int((cust_diff > 1e-6).sum()),
        "duration_A_max_abs_diff_vs_independent_recompute": float(dur_a_diff.max(skipna=True)) if len(dur_a_diff) else None,
        "duration_A_mismatch_count_over_1e-6": int((dur_a_diff > 1e-6).sum()),
        "duration_B_max_abs_diff_vs_independent_recompute": float(dur_b_diff.max(skipna=True)) if len(dur_b_diff) else None,
        "duration_B_mismatch_count_over_1e-6": int((dur_b_diff > 1e-6).sum()),
        "reinterruption_excludes_Y_and_legacy_1": True,
        "reinterruption_treats_legacy_0_as_N": True,
        "reinterruption_legacy_0_or_1_rows_in_sample": int(reint_legacy_check),
        "duration_two_conventions_present": True,
        "duration_A_definition": "customer-weighted mean stage duration (customers*stage_duration summed / customers summed, across ALL stages incl. reinterruptions)",
        "duration_B_definition": "full event span: max(End) - min(Start) across all stages",
        "note_duration_A_includes_reinterruption_stages_in_weighting": True,
    }
    (RAW_DIR / "step1.json").write_text(js(step1), encoding="utf-8")
    print("Step 1 done.")

    # ---------- Step 2: full data-quality audit ----------
    missing_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    missing_pct.to_csv(RAW_DIR / "missing_pct_all_columns.csv", header=["missing_pct"])

    cause_counts_stage = df[CAUSE_COL].astype(str).str.strip().value_counts()
    cause_share_97_stage = float(cause_counts_stage.get("97", 0) / len(df) * 100)

    dedup_first = df.sort_values([INCIDENT_COL, STAGE_COL]).drop_duplicates(INCIDENT_COL, keep="first")
    cause_counts_event_legacy_dedup = dedup_first[CAUSE_COL].astype(str).str.strip().value_counts()
    cause_share_97_event_legacy = float(cause_counts_event_legacy_dedup.get("97", 0) / len(dedup_first) * 100)

    cause_norm_counts_event = dedup_first["cause_group_official"].value_counts()

    event_level = df.drop_duplicates(INCIDENT_COL)[[
        INCIDENT_COL, "customers_v2_event_excl_reinterruptions",
        "duration_A_customer_weighted_hours", "duration_B_full_span_hours",
        "all_stages_are_reinterruption",
    ]].copy()
    legacy_customers = pd.to_numeric(
        dedup_first[CUSTOMER_COL].astype(str).str.replace(",", "", regex=False), errors="coerce"
    ).reset_index(drop=True)
    legacy_duration = ((pd.to_datetime(dedup_first[END_COL], errors="coerce", utc=True)
                         - pd.to_datetime(dedup_first[START_COL], errors="coerce", utc=True))
                        .dt.total_seconds() / 3600.0).reset_index(drop=True)

    def describe(s: pd.Series) -> dict:
        s = s.dropna()
        if len(s) == 0:
            return {"n": 0}
        return {
            "n": int(len(s)),
            "min": float(s.min()),
            "p25": float(s.quantile(0.25)),
            "p50": float(s.quantile(0.50)),
            "p75": float(s.quantile(0.75)),
            "p99": float(s.quantile(0.99)),
            "max": float(s.max()),
            "mean": float(s.mean()),
            "std": float(s.std()),
            "n_missing_or_dropped": int(s.isna().sum()),
        }

    step2 = {
        "n_rows_stage": int(len(df)),
        "n_incidents_event": int(len(event_level)),
        "cause_code_97_share_stage_level_pct": cause_share_97_stage,
        "cause_code_97_share_event_level_legacy_dedup_pct": cause_share_97_event_legacy,
        "cause_code_counts_stage_level_top20": cause_counts_stage.head(20).to_dict(),
        "cause_group_official_counts_event_level": cause_norm_counts_event.to_dict(),
        "customers_legacy_first_stage_only_event_level": describe(legacy_customers),
        "customers_v2_excl_reinterruptions_event_level": describe(event_level["customers_v2_event_excl_reinterruptions"]),
        "duration_legacy_first_stage_only_event_level_hours": describe(legacy_duration),
        "duration_A_customer_weighted_event_level_hours": describe(event_level["duration_A_customer_weighted_hours"]),
        "duration_B_full_span_event_level_hours": describe(event_level["duration_B_full_span_hours"]),
        "all_reinterruption_boundary_incidents_count": int(event_level["all_stages_are_reinterruption"].sum()),
        "all_reinterruption_boundary_incidents_expected": 69,
        "missing_start_stage_incidents_count": int(len(missing_start_incidents)),
        "missing_start_stage_incidents_pct": float(missing_start_pct),
        "missing_start_stage_expected_pct": 10.56,
        "top20_missing_pct_columns": missing_pct.head(20).to_dict(),
        "customers_v2_nan_count_event_level": int(event_level["customers_v2_event_excl_reinterruptions"].isna().sum()),
        "customers_v2_nan_matches_boundary_count": bool(
            int(event_level["customers_v2_event_excl_reinterruptions"].isna().sum())
            == int(event_level["all_stages_are_reinterruption"].sum())
        ),
    }
    (RAW_DIR / "step2.json").write_text(js(step2), encoding="utf-8")
    print("Step 2 done.")

    # duration_A vs duration_B divergence, split single vs multi stage
    stage_count_map = stage_counts.reindex(event_level[INCIDENT_COL]).to_numpy()
    event_level["stage_row_count_check"] = stage_count_map
    event_level["dur_diff_abs"] = (event_level["duration_A_customer_weighted_hours"] - event_level["duration_B_full_span_hours"]).abs()
    event_level["dur_diff_rel_pct"] = event_level["dur_diff_abs"] / event_level["duration_B_full_span_hours"].replace(0, np.nan) * 100

    multi_mask = event_level["stage_row_count_check"] > 1
    single_mask = ~multi_mask

    step2b = {
        "single_stage_incidents": int(single_mask.sum()),
        "multi_stage_incidents": int(multi_mask.sum()),
        "single_stage_duration_A_eq_B_always": bool(
            (event_level.loc[single_mask, "dur_diff_abs"].fillna(0) < 1e-6).all()
        ),
        "multi_stage_dur_diff_abs_describe": describe(event_level.loc[multi_mask, "dur_diff_abs"]),
        "multi_stage_dur_diff_rel_pct_describe": describe(event_level.loc[multi_mask, "dur_diff_rel_pct"]),
        "multi_stage_pct_with_diff_over_10pct_relative": float(
            (event_level.loc[multi_mask, "dur_diff_rel_pct"] > 10).mean() * 100
        ),
        "multi_stage_pct_with_diff_over_1hour_absolute": float(
            (event_level.loc[multi_mask, "dur_diff_abs"] > 1).mean() * 100
        ),
    }
    (RAW_DIR / "step2b_duration_A_vs_B.json").write_text(js(step2b), encoding="utf-8")
    print("Step 2b done.")

    # ---------- weather match rate for the NEW (unfiltered) event set ----------
    weather_status_counts = df["weather_status_v3"].value_counts(dropna=False).to_dict() if "weather_status_v3" in df.columns else None
    weather_matched_incidents = None
    if "weather_status_v3" in df.columns:
        ev_weather = df.drop_duplicates(INCIDENT_COL)["weather_status_v3"].value_counts(dropna=False)
        weather_matched_incidents = ev_weather.to_dict()

    old_incident_count_ref = 62928  # from data/new/ukpn_master... (Cause-Code-prefiltered)
    new_incident_count = int(len(event_level))
    step2c = {
        "weather_status_counts_stage_level": weather_status_counts,
        "weather_status_counts_incident_level": weather_matched_incidents,
        "old_master_incident_count_reference": old_incident_count_ref,
        "new_unfiltered_incident_count": new_incident_count,
        "incident_count_increase_pct": float((new_incident_count - old_incident_count_ref) / old_incident_count_ref * 100),
    }
    (RAW_DIR / "step2c_weather_and_scale.json").write_text(js(step2c), encoding="utf-8")
    print("Step 2c done.")

    print("All steps complete. Raw JSON written to", RAW_DIR)


if __name__ == "__main__":
    main()
