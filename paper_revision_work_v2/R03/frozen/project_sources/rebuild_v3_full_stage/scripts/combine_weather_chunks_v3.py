"""Combine completed weather shards, verify cardinality, and sort by source row."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage")
OUTPUT = ROOT / "outputs" / "02_ukpn_stage_weather_v3.csv"
QA = ROOT / "logs" / "02_weather_combined_qa.json"
SHARD_COUNT = 4
EXPECTED_ROWS = 237_901


def main():
    paths = [ROOT / "outputs" / f"02_weather_chunk_{i:02d}_of_{SHARD_COUNT:02d}.csv" for i in range(SHARD_COUNT)]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing weather shards: {missing}")
    frames = [pd.read_csv(path, low_memory=False) for path in paths]
    columns = frames[0].columns.tolist()
    if any(frame.columns.tolist() != columns for frame in frames[1:]):
        raise ValueError("Weather shard schemas do not match")
    df = pd.concat(frames, ignore_index=True)
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Combined rows {len(df):,} != {EXPECTED_ROWS:,}")
    if not df["source_row_number"].is_unique:
        raise ValueError("Duplicate source_row_number across weather shards")
    df = df.sort_values("source_row_number", kind="stable").reset_index(drop=True)
    if df["source_row_number"].tolist() != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("source_row_number sequence is incomplete")
    df.to_csv(OUTPUT, index=False)
    qa = {
        "rows": len(df),
        "columns": df.shape[1],
        "source_row_number_unique": True,
        "weather_status_counts": {
            str(k): int(v) for k, v in df["weather_status_v3"].value_counts(dropna=False).items()
        },
    }
    QA.write_text(json.dumps(qa, indent=2), encoding="utf-8")
    print(json.dumps(qa, indent=2))
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
