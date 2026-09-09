"""Command #38 M6 (extra): decompose whether the drop in customers-duration
nonlinear dependence (final sample dcorr=0.199 vs legacy dcorr=0.375-0.519)
is driven by the SAMPLE restriction (weather-matched + complete-covariate
final sample, n=59,834, vs the full 62,928/135,025-event legacy population)
or by the VARIABLE REDEFINITION (customers_v2/duration_B vs legacy
first-stage-only customers/duration).

Method: compute distance correlation + MI using the LEGACY variable
definitions (first-stage-only customers, first-stage start/end duration),
but restricted to the SAME final-sample incident IDs (n=59,834) used in the
new-definition calculation. This isolates the sample-restriction effect
while holding the variable definition fixed at 'legacy'.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import dcor
from sklearn.feature_selection import mutual_info_regression

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

SRC = external_path('rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')
INCIDENT_COL = "Incident Reference"
STAGE_COL = "Restoration Stage"
CUSTOMER_COL = "Number of Customers Restored"
START_COL = "Start Date and Time"
END_COL = "End Date and Time"

OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RNG = np.random.default_rng(20260901)
N_PERM = 200


def log_step(msg):
    print(f"[M6-decompose] {msg}", flush=True)


def dcorr_stat(x, y):
    return dcor.distance_correlation(x, y, method="avl")


def mi_stat(x, y):
    return float(mutual_info_regression(x.reshape(-1, 1), y, discrete_features=False,
                                          n_neighbors=3, random_state=0)[0])


def perm_test(x, y, stat_fn, n_perm=N_PERM):
    t0 = time.time()
    obs = stat_fn(x, y)
    null = np.empty(n_perm)
    for i in range(n_perm):
        yp = RNG.permutation(y)
        null[i] = stat_fn(x, yp)
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    return obs, null, p, time.time() - t0


def main():
    _, _, combined_r0cb, _ = build_combined_samples()
    final_ids = set(combined_r0cb["Incident Reference"].astype(str))
    n_final = len(final_ids)
    log_step(f"Final R0c-usable sample n={n_final} (same IDs as the new-definition M6 run)")

    log_step("Loading stage-level v3 data for these incidents (legacy customers + legacy duration)...")
    usecols = [INCIDENT_COL, STAGE_COL, CUSTOMER_COL, START_COL, END_COL]
    chunks = []
    for chunk in pd.read_csv(read_input(SRC), usecols=usecols, low_memory=False, chunksize=500_000):
        chunk = chunk[chunk[INCIDENT_COL].astype(str).isin(final_ids)]
        if len(chunk):
            chunks.append(chunk)
    stage_subset = pd.concat(chunks, ignore_index=True)

    dedup_first = stage_subset.sort_values([INCIDENT_COL, STAGE_COL]).drop_duplicates(INCIDENT_COL, keep="first")
    log_step(f"After earliest-stage dedup: {len(dedup_first)} incidents (expect {n_final})")

    legacy_customers = pd.to_numeric(
        dedup_first[CUSTOMER_COL].astype(str).str.replace(",", "", regex=False), errors="coerce")
    legacy_duration = ((pd.to_datetime(dedup_first[END_COL], errors="coerce", utc=True)
                         - pd.to_datetime(dedup_first[START_COL], errors="coerce", utc=True))
                        .dt.total_seconds() / 3600.0)

    valid = legacy_customers.notna() & legacy_duration.notna() & (legacy_duration > 0)
    log_step(f"Valid legacy customers+duration pairs on final-sample IDs: {valid.sum()} / {len(dedup_first)}")
    lc = legacy_customers[valid].to_numpy()
    ld = legacy_duration[valid].to_numpy()

    log1p_lc = np.log1p(lc)
    log1p_ld = np.log1p(ld)  # matches command #3's log1p/log1p transform exactly

    log_step("Computing distance correlation (legacy definitions, final-sample IDs)...")
    dcorr_obs, dcorr_null, dcorr_p, dcorr_t = perm_test(log1p_lc, log1p_ld, dcorr_stat)
    log_step(f"distance correlation = {dcorr_obs:.4f}, perm p={dcorr_p:.4f} "
              f"(null mean={dcorr_null.mean():.4f}), {N_PERM} perms in {dcorr_t:.1f}s")

    log_step("Computing mutual information (legacy definitions, final-sample IDs)...")
    mi_obs, mi_null, mi_p, mi_t = perm_test(log1p_lc, log1p_ld, mi_stat)
    mi_z = (mi_obs - mi_null.mean()) / mi_null.std()
    log_step(f"MI = {mi_obs:.4f} nats, perm p={mi_p:.4f}, z={mi_z:.1f}, {N_PERM} perms in {mi_t:.1f}s")

    result = {
        "n_valid": int(valid.sum()),
        "distance_correlation_legacy_def_final_sample": float(dcorr_obs),
        "distance_correlation_perm_p": float(dcorr_p),
        "mutual_information_legacy_def_final_sample_nats": float(mi_obs),
        "mutual_information_perm_p": float(mi_p),
        "mutual_information_z": float(mi_z),
        "n_permutations": N_PERM,
    }
    (RAW_DIR / "step38_M6_decompose_sample_vs_definition.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved raw/step38_M6_decompose_sample_vs_definition.json")


if __name__ == "__main__":
    main()
