"""Command #38 F4: recompute the legacy 'first-stage-only' customers mean on
the EXACT final combined E0 sample (n=60,437, command #21), using the same
sort+dedup logic as command #8's audit_v3_dataset.py, so it is directly
comparable to Table 1's customers_v2 mean (93.02)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
INCIDENT_COL = "Incident Reference"
STAGE_COL = "Restoration Stage"
CUSTOMER_COL = "Number of Customers Restored"

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"


def log_step(msg):
    print(f"[F4] {msg}", flush=True)


def main():
    _, combined_e0, _, _ = build_combined_samples()
    final_ids = set(combined_e0["Incident Reference"].astype(str))
    log_step(f"Final E0 sample n={len(combined_e0)}, unique incident IDs={len(final_ids)}")
    log_step(f"customers_v2 mean on final sample (should match Table 1's 93.02): "
              f"{combined_e0['customers_v2_event_excl_reinterruptions'].astype(float).mean():.5f}")

    log_step("Loading full v3 stage-level dataset (subset to the final sample's incidents only)...")
    usecols = [INCIDENT_COL, STAGE_COL, CUSTOMER_COL]
    chunks = []
    for chunk in pd.read_csv(SRC, usecols=usecols, low_memory=False, chunksize=500_000):
        chunk = chunk[chunk[INCIDENT_COL].astype(str).isin(final_ids)]
        if len(chunk):
            chunks.append(chunk)
    stage_subset = pd.concat(chunks, ignore_index=True)
    log_step(f"Stage-level rows for final-sample incidents: {len(stage_subset)}")

    # exact same sort+dedup logic as command #8's audit_v3_dataset.py line 149
    dedup_first = stage_subset.sort_values([INCIDENT_COL, STAGE_COL]).drop_duplicates(INCIDENT_COL, keep="first")
    log_step(f"After earliest-stage dedup: {len(dedup_first)} incidents "
              f"(expect {len(final_ids)})")
    missing = final_ids - set(dedup_first[INCIDENT_COL].astype(str))
    if missing:
        log_step(f"WARNING: {len(missing)} final-sample incidents not found in stage-level file: "
                  f"{list(missing)[:5]}")

    legacy_customers = pd.to_numeric(
        dedup_first[CUSTOMER_COL].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    n_legacy_valid = legacy_customers.notna().sum()
    legacy_mean = float(legacy_customers.mean())
    log_step(f"Legacy first-stage-only customers: n_valid={n_legacy_valid}, mean={legacy_mean:.5f}, "
              f"median={legacy_customers.median():.2f}, std={legacy_customers.std():.2f}")

    v2_mean = float(combined_e0["customers_v2_event_excl_reinterruptions"].astype(float).mean())
    ratio = v2_mean / legacy_mean
    log_step(f"customers_v2 mean = {v2_mean:.5f}")
    log_step(f"Ratio (customers_v2 / legacy first-stage-only) = {ratio:.4f}")

    result = {
        "n_final_sample": int(len(combined_e0)),
        "n_legacy_valid": int(n_legacy_valid),
        "legacy_first_stage_only_mean": legacy_mean,
        "customers_v2_mean": v2_mean,
        "ratio_v2_over_legacy": ratio,
    }
    import json
    (RAW_DIR / "step38_F4_customers_mean_ratio.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved raw/step38_F4_customers_mean_ratio.json")


if __name__ == "__main__":
    main()
