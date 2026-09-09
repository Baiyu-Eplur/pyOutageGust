"""Command #54 preparatory step (run in the main project, NOT part of the
review package itself): materialize the actual final E0/R0c analysis-ready
DataFrames -- the exact objects final_core_tables.py fits its main regression
on -- to static CSV files, for inclusion in the isolated review package.
This does not touch any historical result file; it only reads."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "c02_c08_repair_20260905"))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

OUT_DIR = result_path('review_package/data')
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[materialize] {msg}", flush=True)


def main():
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()
    log_step(f"combined_e0: n={len(combined_e0)}, columns={len(combined_e0.columns)}")
    log_step(f"combined_r0cb: n={len(combined_r0cb)}, columns={len(combined_r0cb.columns)}")

    combined_e0.to_csv(OUT_DIR / "combined_E0_final.csv", index=False)
    combined_r0cb.to_csv(OUT_DIR / "combined_R0c_final.csv", index=False)
    log_step(f"Saved {OUT_DIR / 'combined_E0_final.csv'}")
    log_step(f"Saved {OUT_DIR / 'combined_R0c_final.csv'}")

    # sanity: key columns present
    needed_e0 = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h",
                 "urban_binary", "log_population", "income_deprivation_rate", "deprivation_gap_pct",
                 "morans_i", "incident_year", "incident_month", "LAD21CD", "incident_date_utc",
                 "log1p_customers_v2"]
    needed_r0c = needed_e0 + ["customers_v2_event_excl_reinterruptions", "log_duration_B_full_span_hours"]
    missing_e0 = [c for c in needed_e0 if c not in combined_e0.columns]
    missing_r0c = [c for c in needed_r0c if c not in combined_r0cb.columns]
    log_step(f"Missing required columns -- E0: {missing_e0}, R0c: {missing_r0c}")
    assert not missing_e0 and not missing_r0c, "materialized data missing required columns"
    log_step("All required columns present. Done.")


if __name__ == "__main__":
    main()
