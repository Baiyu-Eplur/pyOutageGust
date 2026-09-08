"""Parallel cache-only weather worker for one deterministic request-key shard."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(r"D:\Pyprogramme\STST2603")
RUN_ROOT = PROJECT_ROOT / "rebuild_v3_full_stage"
INPUT = RUN_ROOT / "outputs" / "01_ukpn_stage_base_v3.csv"
CACHE = PROJECT_ROOT / "data" / "weather_request_cache"

MAIN1 = Path(__file__).with_name("main1_v3.py")
spec = importlib.util.spec_from_file_location("main1_v3_helpers", MAIN1)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def shard_for_key(key: str, shard_count: int) -> int:
    return int.from_bytes(hashlib.md5(key.encode("utf-8")).digest()[:4], "little") % shard_count


def append_batch(rows, output_path, columns):
    if not rows:
        return
    frame = pd.DataFrame(rows).reindex(columns=columns)
    frame.to_csv(output_path, mode="a", index=False, header=not output_path.exists())


def empty_record(row, empty_features, status):
    return {**row.to_dict(), **empty_features, "weather_status_v3": status}


def main(shard_index: int, shard_count: int):
    output = RUN_ROOT / "outputs" / f"02_weather_chunk_{shard_index:02d}_of_{shard_count:02d}.csv"
    log = RUN_ROOT / "logs" / f"02_weather_chunk_{shard_index:02d}_qa.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing shard: {output}")

    df = pd.read_csv(INPUT, low_memory=False)
    df = helpers.prepare_incident_time(df, "Start Date and Time", assume_local_london_time=False)
    df["lat"], df["lon"] = helpers.parse_spatial_coordinates(df["Spatial Coordinates"])
    df = helpers.round_coordinates(df, lat_col="lat", lon_col="lon", decimals=1)
    df["weather_eligible_v3"] = (
        df["clean_start"].notna()
        & df["lat"].between(49, 61)
        & df["lon"].between(-9, 3)
    )
    df["incident_date_utc"] = df["clean_start"].dt.date.astype("string")
    keys = (
        df["lat_r"].astype(str)
        + "_"
        + df["lon_r"].astype(str)
        + "_"
        + df["incident_date_utc"].astype(str)
    )
    df["request_key"] = keys.where(df["weather_eligible_v3"], pd.NA)

    eligible_shard = df["request_key"].fillna("").map(
        lambda key: shard_for_key(key, shard_count) if key else -1
    )
    selected = df[eligible_shard.eq(shard_index)].copy()
    if shard_index == 0:
        selected = pd.concat([df[~df["weather_eligible_v3"]], selected], ignore_index=True)

    empty_features = helpers.make_empty_feature_series().to_dict()
    output_columns = selected.columns.tolist() + list(empty_features) + ["weather_status_v3"]
    cached_keys = {p.stem for p in CACHE.glob("*.pkl")}

    records = []
    matched = 0
    unavailable = 0
    invalid = 0

    invalid_rows = selected[~selected["weather_eligible_v3"]]
    for _, row in invalid_rows.iterrows():
        records.append(empty_record(row, empty_features, "invalid_time_or_coordinate"))
        invalid += 1
        if len(records) >= 2000:
            append_batch(records, output, output_columns)
            records = []

    eligible = selected[selected["weather_eligible_v3"]]
    for request_key, group in eligible.groupby("request_key", sort=False):
        if request_key not in cached_keys:
            for _, row in group.iterrows():
                records.append(empty_record(row, empty_features, "weather_request_unavailable"))
                unavailable += 1
        else:
            try:
                hourly = pd.read_pickle(CACHE / f"{request_key}.pkl")
            except Exception:
                hourly = None
            if hourly is None:
                for _, row in group.iterrows():
                    records.append(empty_record(row, empty_features, "weather_cache_unreadable"))
                    unavailable += 1
            else:
                per_hour = {}
                for _, row in group.iterrows():
                    target_hour = pd.Timestamp(row["clean_start"]).floor("h")
                    feature = per_hour.get(target_hour)
                    if feature is None:
                        feature = helpers.build_incident_features_from_hourly(hourly, target_hour).to_dict()
                        per_hour[target_hour] = feature
                    records.append({**row.to_dict(), **feature, "weather_status_v3": "matched"})
                    matched += 1
        if len(records) >= 2000:
            append_batch(records, output, output_columns)
            records = []

    append_batch(records, output, output_columns)
    qa = {
        "shard_index": shard_index,
        "shard_count": shard_count,
        "rows": int(len(selected)),
        "matched": matched,
        "unavailable": unavailable,
        "invalid": invalid,
        "output": str(output),
    }
    log.write_text(json.dumps(qa, indent=2), encoding="utf-8")
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=4)
    args = parser.parse_args()
    main(args.shard_index, args.shard_count)
