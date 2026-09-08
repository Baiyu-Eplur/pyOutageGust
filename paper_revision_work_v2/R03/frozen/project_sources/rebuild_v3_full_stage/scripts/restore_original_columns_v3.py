"""Atomically restore all 20 source columns to their exact original CSV values."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(r"D:\Pyprogramme\STST2603")
RAW = PROJECT_ROOT / "data" / "ukpn-iis.csv"
FINAL = PROJECT_ROOT / "rebuild_v3_full_stage" / "outputs" / "ukpn_full_stage_dataset_v3.csv"
TEMP = FINAL.with_suffix(".restoring.csv")


def main():
    original = pd.read_csv(RAW, dtype=str, keep_default_na=False, low_memory=False)
    final = pd.read_csv(FINAL, low_memory=False)
    if len(original) != len(final):
        raise ValueError("Cannot restore original columns because row counts differ")
    if final["source_row_number"].tolist() != list(range(1, len(final) + 1)):
        raise ValueError("Cannot restore original columns because source row order is not exact")
    for column in original.columns:
        final[column] = original[column]
    final.to_csv(TEMP, index=False)
    TEMP.replace(FINAL)
    print(f"Restored {len(original.columns)} original columns in {len(final):,} rows: {FINAL}")


if __name__ == "__main__":
    main()
