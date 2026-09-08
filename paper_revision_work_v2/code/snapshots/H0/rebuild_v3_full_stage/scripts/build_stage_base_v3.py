"""Build the unfiltered, stage-grain v3 UKPN base dataset.

The output preserves every row and every original column from ukpn-iis.csv.
Incident-level outcomes are calculated once per Incident Reference and mapped
back to every restoration-stage row. No cause-code, coordinate, time, or LAD
filter is applied in this step.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(r"D:\Pyprogramme\STST2603")
RUN_ROOT = PROJECT_ROOT / "rebuild_v3_full_stage"
INPUT_CSV = PROJECT_ROOT / "data" / "ukpn-iis.csv"
OUTPUT_CSV = RUN_ROOT / "outputs" / "01_ukpn_stage_base_v3.csv"
QA_JSON = RUN_ROOT / "logs" / "01_stage_base_qa.json"
BOUNDARY_CSV = RUN_ROOT / "logs" / "01_all_reinterruption_incidents.csv"
CAUSE_INCONSISTENCY_CSV = RUN_ROOT / "logs" / "01_cause_inconsistent_incidents.csv"

INCIDENT_COL = "Incident Reference"
START_COL = "Start Date and Time"
END_COL = "End Date and Time"
CUSTOMER_COL = "Number of Customers Restored"
REINTERRUPTION_COL = "Re-interruption Stage"
CAUSE_COL = "Cause Code"

# Legacy binary coding follows the observed N/Y mapping: 0=N and 1=Y.
REINTERRUPTION_TRUE_VALUES = frozenset({"Y", "1"})


def normalize_cause_code(value):
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    if text in {"D", "X", "A1", "A2"}:
        return text
    try:
        number = float(text)
        if number.is_integer():
            return f"{int(number):02d}"
    except (TypeError, ValueError):
        pass
    if text.isdigit():
        return f"{int(text):02d}"
    return text


def classify_cause_code(code):
    groups = {
        "weather_natural": {
            "01", "02", "03", "04", "05", "06", "07", "10", "18",
            "21", "23", "24", "25", "30", "32", "33",
        },
        "technical_asset": {
            "14", "15", "16", "17", "19", "22", "26", "64", "67",
            "70", "71", "72", "73", "76", "77", "78", "90", "A1", "A2",
        },
        "third_party": {
            "39", "40", "41", "42", "43", "44", "45", "48", "49", "50",
            "53", "54", "55", "56", "57", "58",
        },
        "human_error": {
            "60", "61", "62", "63", "65", "66", "68", "69", "81", "82",
            "83", "84",
        },
        "external_or_customer": {"74", "80", "85", "86", "87", "88", "89"},
        "non_fault_or_unknown": {"75", "97", "98", "99", "D", "X"},
    }
    for group_name, values in groups.items():
        if code in values:
            return group_name
    return "unmapped"


def build_stage_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict, pd.DataFrame, pd.DataFrame]:
    required = {
        INCIDENT_COL,
        START_COL,
        END_COL,
        CUSTOMER_COL,
        REINTERRUPTION_COL,
        CAUSE_COL,
    }
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise KeyError(f"Missing required source columns: {missing}")

    df = raw.copy()
    df.insert(0, "source_row_number", np.arange(1, len(df) + 1, dtype=np.int64))
    df[INCIDENT_COL] = df[INCIDENT_COL].astype("string").str.strip()

    start = pd.to_datetime(df[START_COL], errors="coerce", utc=True)
    end = pd.to_datetime(df[END_COL], errors="coerce", utc=True)
    stage_duration = (end - start).dt.total_seconds() / 3600.0
    stage_duration = stage_duration.mask(stage_duration < 0)
    customers = pd.to_numeric(
        df[CUSTOMER_COL].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
    reinterruption = df[REINTERRUPTION_COL].astype("string").str.strip().str.upper()
    is_reinterruption = reinterruption.isin(REINTERRUPTION_TRUE_VALUES)

    df["cause_code_norm"] = df[CAUSE_COL].map(normalize_cause_code)
    df["cause_group_official"] = df["cause_code_norm"].map(classify_cause_code)
    df["is_reinterruption_stage_v3"] = is_reinterruption
    df["stage_duration_hours"] = stage_duration

    key = df[INCIDENT_COL]
    eligible_customers = customers.mask(is_reinterruption)
    customers_by_incident = eligible_customers.groupby(key, dropna=False).sum(min_count=1)
    all_reinterruption = is_reinterruption.groupby(key, dropna=False).all()
    stage_count = key.groupby(key, dropna=False).size()

    weighted_numerator = (customers * stage_duration).groupby(key, dropna=False).sum(min_count=1)
    weighted_denominator = customers.where(stage_duration.notna()).groupby(key, dropna=False).sum(min_count=1)
    duration_a = weighted_numerator.div(weighted_denominator.where(weighted_denominator > 0))
    duration_b = (
        end.groupby(key, dropna=False).max() - start.groupby(key, dropna=False).min()
    ).dt.total_seconds() / 3600.0

    df["customers_v2_event_excl_reinterruptions"] = key.map(customers_by_incident)
    df["duration_A_customer_weighted_hours"] = key.map(duration_a)
    df["duration_B_full_span_hours"] = key.map(duration_b)
    # Canonical compatibility field for downstream code; both candidates remain available.
    df["Duration (hours)"] = df["duration_A_customer_weighted_hours"]
    df["customer_minutes_lost_event"] = key.map(weighted_numerator * 60.0)
    df["event_customer_weight_denominator"] = key.map(weighted_denominator)
    df["all_stages_are_reinterruption"] = key.map(all_reinterruption).fillna(False)
    df["stage_row_count"] = key.map(stage_count)

    cause_nunique = df.groupby(INCIDENT_COL, dropna=False)["cause_code_norm"].nunique(dropna=False)
    inconsistent_ids = cause_nunique[cause_nunique > 1].index
    cause_inconsistent = (
        df.loc[df[INCIDENT_COL].isin(inconsistent_ids), [INCIDENT_COL, CAUSE_COL, "cause_code_norm"]]
        .drop_duplicates()
        .sort_values([INCIDENT_COL, "cause_code_norm"])
    )
    boundary = (
        df.loc[df["all_stages_are_reinterruption"], [INCIDENT_COL]]
        .drop_duplicates()
        .sort_values(INCIDENT_COL)
    )

    qa = {
        "source_rows": int(len(raw)),
        "output_rows": int(len(df)),
        "source_columns": int(raw.shape[1]),
        "output_columns": int(df.shape[1]),
        "unique_incidents": int(df[INCIDENT_COL].nunique(dropna=True)),
        "multi_stage_incidents": int((stage_count > 1).sum()),
        "reinterruption_value_counts": {
            str(k): int(v) for k, v in reinterruption.value_counts(dropna=False).items()
        },
        "all_reinterruption_incidents": int(len(boundary)),
        "cause_inconsistent_incidents": int(len(inconsistent_ids)),
        "invalid_start_rows": int(start.isna().sum()),
        "invalid_end_rows": int(end.isna().sum()),
        "negative_stage_duration_rows": int(((end - start).dt.total_seconds() < 0).sum()),
        "non_numeric_customer_rows": int(customers.isna().sum()),
        "rows_preserved_exactly": bool(len(raw) == len(df)),
        "source_row_number_unique": bool(df["source_row_number"].is_unique),
        "canonical_duration": "duration_A_customer_weighted_hours",
        "reinterruption_true_values": sorted(REINTERRUPTION_TRUE_VALUES),
    }
    return df, qa, boundary, cause_inconsistent


def main():
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    QA_JSON.parent.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(
        INPUT_CSV,
        dtype={"Continued Cause Code": "string"},
        low_memory=False,
    )
    result, qa, boundary, cause_inconsistent = build_stage_dataset(raw)
    result.to_csv(OUTPUT_CSV, index=False)
    boundary.to_csv(BOUNDARY_CSV, index=False)
    cause_inconsistent.to_csv(CAUSE_INCONSISTENCY_CSV, index=False)
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    print(f"Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
