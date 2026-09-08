"""Independent integrity checks for the completed v3 CSV."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(r"D:\Pyprogramme\STST2603")
RUN_ROOT = PROJECT_ROOT / "rebuild_v3_full_stage"
RAW = PROJECT_ROOT / "data" / "ukpn-iis.csv"
FINAL = RUN_ROOT / "outputs" / "ukpn_full_stage_dataset_v3.csv"
REPORT = RUN_ROOT / "logs" / "04_final_validation.json"
EXPECTED_ROWS = 237_901


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    raw_columns = pd.read_csv(RAW, nrows=0).columns.tolist()
    raw = pd.read_csv(RAW, usecols=raw_columns, dtype=str, keep_default_na=False)
    final_original = pd.read_csv(FINAL, usecols=raw_columns, dtype=str, keep_default_na=False, low_memory=False)
    original_equal = raw.equals(final_original)
    mismatch_cells = int((raw != final_original).to_numpy().sum())

    required = [
        "source_row_number",
        "Incident Reference",
        "Re-interruption Stage",
        "customers_v2_event_excl_reinterruptions",
        "duration_A_customer_weighted_hours",
        "duration_B_full_span_hours",
        "Duration (hours)",
        "all_stages_are_reinterruption",
        "stage_row_count",
        "weather_status_v3",
        "LAD21CD",
        "population",
        "income_deprivation_rate",
        "gva_pc",
    ]
    df = pd.read_csv(FINAL, usecols=required, low_memory=False)
    header = pd.read_csv(FINAL, nrows=0).columns.tolist()

    event_cols = [
        "customers_v2_event_excl_reinterruptions",
        "duration_A_customer_weighted_hours",
        "duration_B_full_span_hours",
        "all_stages_are_reinterruption",
        "stage_row_count",
    ]
    event_inconsistencies = int(
        (df.groupby("Incident Reference", dropna=False)[event_cols].nunique(dropna=False) > 1)
        .any(axis=1)
        .sum()
    )
    numeric = df[
        [
            "customers_v2_event_excl_reinterruptions",
            "duration_A_customer_weighted_hours",
            "duration_B_full_span_hours",
            "Duration (hours)",
        ]
    ].apply(pd.to_numeric, errors="coerce")

    legacy_expected = {
        "FREP-290743-G": 136.0,
        "FREP-307113-J": 3.0,
    }
    legacy_actual = {
        incident: float(
            df.loc[df["Incident Reference"].eq(incident), "customers_v2_event_excl_reinterruptions"].iloc[0]
        )
        for incident in legacy_expected
    }

    report = {
        "final_path": str(FINAL),
        "file_size_bytes": FINAL.stat().st_size,
        "sha256": sha256(FINAL),
        "rows": int(len(df)),
        "columns": len(header),
        "column_names_unique": len(header) == len(set(header)),
        "source_row_number_unique": bool(df["source_row_number"].is_unique),
        "source_row_number_complete_sequence": bool(
            df["source_row_number"].tolist() == list(range(1, EXPECTED_ROWS + 1))
        ),
        "all_original_columns_present": set(raw_columns).issubset(header),
        "original_values_and_order_preserved_exactly": bool(original_equal),
        "original_cell_mismatch_count": mismatch_cells,
        "unique_incidents": int(df["Incident Reference"].nunique()),
        "event_aggregate_inconsistent_incidents": event_inconsistencies,
        "canonical_duration_matches_duration_A": bool(
            np.allclose(numeric["Duration (hours)"], numeric["duration_A_customer_weighted_hours"], equal_nan=True)
        ),
        "all_reinterruption_incidents": int(
            df.loc[df["all_stages_are_reinterruption"].eq(True), "Incident Reference"].nunique()
        ),
        "legacy_one_exclusion_expected": legacy_expected,
        "legacy_one_exclusion_actual": legacy_actual,
        "legacy_one_exclusion_pass": legacy_actual == legacy_expected,
        "infinite_derived_numeric_values": int(np.isinf(numeric.to_numpy()).sum()),
        "weather_status_counts": {
            str(k): int(v) for k, v in df["weather_status_v3"].value_counts(dropna=False).items()
        },
        "match_rates": {
            "lad": float(df["LAD21CD"].notna().mean()),
            "population": float(df["population"].notna().mean()),
            "imd": float(df["income_deprivation_rate"].notna().mean()),
            "gva": float(df["gva_pc"].notna().mean()),
        },
    }
    hard_checks = [
        report["rows"] == EXPECTED_ROWS,
        report["column_names_unique"],
        report["source_row_number_unique"],
        report["source_row_number_complete_sequence"],
        report["all_original_columns_present"],
        report["original_values_and_order_preserved_exactly"],
        report["event_aggregate_inconsistent_incidents"] == 0,
        report["canonical_duration_matches_duration_A"],
        report["legacy_one_exclusion_pass"],
        report["infinite_derived_numeric_values"] == 0,
    ]
    report["hard_checks_pass"] = bool(all(hard_checks))
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["hard_checks_pass"]:
        raise SystemExit("Final validation failed")


if __name__ == "__main__":
    main()
