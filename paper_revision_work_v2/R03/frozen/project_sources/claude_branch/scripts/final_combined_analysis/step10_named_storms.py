"""Command #23: verify named storm events in the final combined
weather_natural+technical_asset sample (n=60,453), using officially documented
storm dates (UK Met Office) as the external, pre-registered reference -- never
inferring "this looks like storm X" from the data itself.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Officially documented UK Met Office storm dates, +/-1 day buffer for overnight events.
STORMS = {
    "Storm Arwen": ("2021-11-25", "2021-11-28"),
    "Storm Dudley": ("2022-02-15", "2022-02-17"),
    "Storm Eunice": ("2022-02-17", "2022-02-19"),
    "Storm Franklin": ("2022-02-19", "2022-02-22"),
    "Storm Babet": ("2023-10-17", "2023-10-22"),
    "Storm Ciaran": ("2023-10-31", "2023-11-03"),
    "Storm Henk": ("2024-01-01", "2024-01-03"),
}


def log_step(msg):
    print(f"[v23] {msg}", flush=True)


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


def main():
    combined_wt, combined_e0, combined_r0cb, verification = build_combined_samples()
    combined_wt = combined_wt.copy()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")

    log_step("Joining substation and LAD21NM (not in the base USECOLS) from the v3 dataset...")
    SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
    extra_cols = pd.read_csv(SRC, usecols=["Incident Reference", "substation", "LAD21NM"], low_memory=False)
    extra_cols = extra_cols.drop_duplicates("Incident Reference").set_index("Incident Reference")
    combined_wt["substation"] = combined_wt["Incident Reference"].map(extra_cols["substation"])
    combined_wt["LAD21NM"] = combined_wt["Incident Reference"].map(extra_cols["LAD21NM"])

    gust_all = combined_wt["gust_0h"].dropna()

    log_step(f"Full sample n={len(combined_wt)}; gust distribution: "
              f"p50={gust_all.quantile(0.5):.2f}, p95={gust_all.quantile(0.95):.2f}, "
              f"p99={gust_all.quantile(0.99):.2f}, max={gust_all.max():.2f} m/s")

    results = []
    for storm, (start, end) in STORMS.items():
        mask = (combined_wt["incident_date_utc"] >= start) & (combined_wt["incident_date_utc"] <= end)
        sub = combined_wt.loc[mask].copy()
        n = len(sub)
        if n == 0:
            results.append({
                "storm": storm, "window": f"{start} to {end}", "n_events": 0,
                "note": "No events found in this window in the final combined sample.",
            })
            log_step(f"{storm}: 0 events found.")
            continue

        gust_max_row = sub.loc[sub["gust_0h"].idxmax()] if sub["gust_0h"].notna().any() else None
        gust_max = float(sub["gust_0h"].max()) if sub["gust_0h"].notna().any() else np.nan
        gust_percentile = float((gust_all < gust_max).mean() * 100) if not np.isnan(gust_max) else np.nan

        cust_sum = float(sub["customers_v2_event_excl_reinterruptions"].sum(skipna=True))
        dur_mean = float(sub["duration_B_full_span_hours"].mean(skipna=True))
        dur_max = float(sub["duration_B_full_span_hours"].max(skipna=True))
        n_lads = int(sub["LAD21CD"].nunique())

        row = {
            "storm": storm, "window": f"{start} to {end}", "n_events": n,
            "gust_max_ms": gust_max, "gust_max_percentile_in_full_sample": gust_percentile,
            "gust_max_LAD21CD": str(gust_max_row["LAD21CD"]) if gust_max_row is not None else None,
            "gust_max_LAD21NM": str(gust_max_row["LAD21NM"]) if gust_max_row is not None else None,
            "gust_max_substation": str(gust_max_row["substation"]) if gust_max_row is not None else None,
            "gust_max_date": str(gust_max_row["incident_date_utc"].date()) if gust_max_row is not None else None,
            "customers_v2_sum": cust_sum, "duration_B_mean_hours": dur_mean, "duration_B_max_hours": dur_max,
            "n_unique_lads": n_lads,
            "cause_group_counts": sub["cause_group_official"].value_counts().to_dict(),
        }
        results.append(row)
        log_step(f"{storm}: n={n}, gust_max={gust_max:.2f} m/s (p{gust_percentile:.1f}), "
                  f"customers_v2_sum={cust_sum:.0f}, duration_B_max={dur_max:.2f}h, n_lads={n_lads}")

        sub.to_csv(RAW_DIR / f"step10_{storm.replace(' ', '_')}_events.csv", index=False)

    (RAW_DIR / "step10_storm_summary.json").write_text(js(results), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    log_step("Done.")


if __name__ == "__main__":
    main()
