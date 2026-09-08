"""C01 repair Step 2: for every event whose representative row changed (Step
1), re-extract gust_0h / pressure_msl_0h / temperature_0h / precipitation_24h_sum
at the NEW (correct, earliest-start) target time, using the EXISTING local
weather cache (data/weather_request_cache/*.pkl, keyed by rounded lat/lon and
a request date whose fetched window spans [date-3, date+1]) -- no new Open-Meteo
API calls are made. Events whose new target hour is not covered by any cached
window at that location are explicitly flagged as needing a new weather request.

Reuses the build_incident_features_from_hourly / summarize_window functions
extracted verbatim from main1.py into src/weather_features.py (imported, not
reimplemented) so the re-extraction logic is byte-identical to how the
original pipeline computed these fields.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.weather_features import build_incident_features_from_hourly  # noqa: E402

CACHE_DIR = Path(r"D:\Pyprogramme\STST2603\data\weather_request_cache")
RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905\raw")

FNAME_RE = re.compile(r"^(-?\d+\.\d)_(-?\d+\.\d)_(\d{4}-\d{2}-\d{2})\.pkl$")


def log_step(msg):
    print(f"[C01-step2] {msg}", flush=True)


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


def build_cache_index():
    log_step("Indexing cache filenames (no pickle loading yet)...")
    index = {}  # (lat_r, lon_r) -> list of (center_date, filepath)
    n_files = 0
    for p in CACHE_DIR.glob("*.pkl"):
        m = FNAME_RE.match(p.name)
        if not m:
            continue
        lat_r, lon_r, date_str = float(m.group(1)), float(m.group(2)), m.group(3)
        center_date = pd.Timestamp(date_str, tz="UTC")
        index.setdefault((lat_r, lon_r), []).append((center_date, p))
        n_files += 1
    log_step(f"Indexed {n_files} cache files across {len(index)} distinct (lat_r, lon_r) locations.")
    return index


def find_cache_file_for_target(index, lat_r, lon_r, target_time_utc):
    """Return the path of a cache file at (lat_r, lon_r) whose fetched window
    [center_date-3d, center_date+1d+23h] plausibly covers target_time_utc, or None."""
    candidates = index.get((lat_r, lon_r))
    if not candidates:
        return None
    for center_date, path in candidates:
        window_start = center_date - pd.Timedelta(days=3)
        window_end = center_date + pd.Timedelta(days=1) + pd.Timedelta(hours=23)
        if window_start <= target_time_utc <= window_end:
            return path
    return None


def main():
    changed = pd.read_csv(RAW_DIR / "step1_changed_events_only.csv")
    changed["new_start_utc"] = pd.to_datetime(changed["new_start_utc"], utc=True)
    log_step(f"Loaded {len(changed)} changed events from Step 1.")

    index = build_cache_index()

    results = []
    cache_load_memo = {}
    n_found = 0
    n_missing = 0
    missing_ids = []

    for i, row in changed.iterrows():
        lat, lon = row["lat"], row["lon"]
        if pd.isna(lat) or pd.isna(lon):
            results.append({**row.to_dict(), "cache_status": "no_coordinates"})
            n_missing += 1
            missing_ids.append(row["Incident Reference"])
            continue
        lat_r, lon_r = round(float(lat), 1), round(float(lon), 1)
        target = row["new_start_utc"]

        cache_path = find_cache_file_for_target(index, lat_r, lon_r, target)
        if cache_path is None:
            results.append({**row.to_dict(), "cache_status": "not_found_needs_new_request",
                             "lat_r": lat_r, "lon_r": lon_r})
            n_missing += 1
            missing_ids.append(row["Incident Reference"])
            continue

        key = str(cache_path)
        if key not in cache_load_memo:
            try:
                cache_load_memo[key] = pd.read_pickle(cache_path)
            except Exception:
                cache_load_memo[key] = None
        df_hourly = cache_load_memo[key]
        if df_hourly is None or df_hourly.empty:
            results.append({**row.to_dict(), "cache_status": "cache_file_unreadable",
                             "lat_r": lat_r, "lon_r": lon_r})
            n_missing += 1
            missing_ids.append(row["Incident Reference"])
            continue

        feat = build_incident_features_from_hourly(df_hourly, target)
        exact_hour_available = (df_hourly["time_utc"] == pd.Timestamp(target).floor("h")).any()
        results.append({
            **row.to_dict(),
            "cache_status": "recovered_exact_hour" if exact_hour_available else "recovered_nearest_hour",
            "lat_r": lat_r, "lon_r": lon_r,
            "recomputed_gust_0h": feat.get("gust_0h"),
            "recomputed_pressure_msl_0h": feat.get("pressure_msl_0h"),
            "recomputed_temperature_0h": feat.get("temperature_0h"),
            "recomputed_precip_24h_sum": feat.get("precipitation_24h_sum"),
        })
        n_found += 1

        if (i + 1) % 2000 == 0:
            log_step(f"  processed {i + 1}/{len(changed)}...")

    out_df = pd.DataFrame(results)
    out_df.to_csv(RAW_DIR / "step2_weather_reextraction_full.csv", index=False)
    log_step(f"Recovered from existing cache: {n_found} / {len(changed)} "
              f"({n_found/len(changed)*100:.2f}%)")
    log_step(f"NOT recoverable from existing cache (need new weather request): {n_missing} "
              f"({n_missing/len(changed)*100:.2f}%)")

    missing_df = out_df[out_df["cache_status"].isin(
        ["not_found_needs_new_request", "cache_file_unreadable", "no_coordinates"])]
    missing_df.to_csv(RAW_DIR / "step2_needs_new_weather_request.csv", index=False)
    log_step(f"Saved raw/step2_needs_new_weather_request.csv ({len(missing_df)} events, "
              f"full Incident Reference list included)")

    # gust diff on the recovered subset, comparing NEW recomputed gust vs OLD (v3-stored) gust
    recovered = out_df[out_df["cache_status"].str.startswith("recovered")].copy()
    recovered["recomputed_gust_diff_vs_old"] = recovered["recomputed_gust_0h"] - recovered["old_gust_0h"]

    summary = {
        "n_changed_events_total": len(changed),
        "n_recovered_from_existing_cache": n_found,
        "n_needs_new_weather_request": n_missing,
        "pct_recovered": n_found / len(changed) * 100,
        "cache_status_breakdown": out_df["cache_status"].value_counts().to_dict(),
        "recomputed_vs_old_gust_diff_on_recovered": {
            "n_valid": int(recovered["recomputed_gust_diff_vs_old"].notna().sum()),
            "mean": float(recovered["recomputed_gust_diff_vs_old"].mean()),
            "median": float(recovered["recomputed_gust_diff_vs_old"].median()),
            "std": float(recovered["recomputed_gust_diff_vs_old"].std()),
        },
    }
    (RAW_DIR / "step2_summary.json").write_text(js(summary), encoding="utf-8")
    log_step(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
