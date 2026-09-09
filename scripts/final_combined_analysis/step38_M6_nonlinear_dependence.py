"""Command #38 M6: distance correlation + mutual information between
affected customers (customers_v2) and restoration duration (duration_B) on
the FINAL combined sample (command #21, n=59,834 R0c-usable), for direct
comparison against the legacy-era result in
claude_branch/results/test1b_independence_check/05_独立性检验综合结论.md
(distance correlation 0.375-0.519, MI 0.399/0.211 nats, computed on the old
customers/duration definitions, n=62,928/53,492).

Method choices (must match/mirror the legacy analysis for a fair comparison):
  - distance correlation: dcor.distance_correlation(x, y, method='avl'), the
    exact O(n log n) 1-D algorithm used in command #3 (NOT a naive O(n^2)
    pairwise-distance construction, which command #3 already found crashes
    at this sample size with ~30GB memory).
  - mutual information: sklearn.feature_selection.mutual_info_regression
    (k-NN / Kraskov-style estimator), same family of estimator as command #3.
  - permutation test: reduced from command #3's 500 permutations to 200 for
    runtime reasons at this sample size; explicitly disclosed below.
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
import dcor
from sklearn.feature_selection import mutual_info_regression

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RNG = np.random.default_rng(20260901)
N_PERM = 200


def log_step(msg):
    print(f"[M6] {msg}", flush=True)


def perm_test(x, y, stat_fn, n_perm=N_PERM):
    t0 = time.time()
    obs = stat_fn(x, y)
    null = np.empty(n_perm)
    for i in range(n_perm):
        yp = RNG.permutation(y)
        null[i] = stat_fn(x, yp)
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    elapsed = time.time() - t0
    return obs, null, p, elapsed


def dcorr_stat(x, y):
    return dcor.distance_correlation(x, y, method="avl")


def mi_stat(x, y):
    return float(mutual_info_regression(x.reshape(-1, 1), y, discrete_features=False,
                                          n_neighbors=3, random_state=0)[0])


def main():
    _, _, combined_r0cb, _ = build_combined_samples()
    n = len(combined_r0cb)
    log_step(f"Final R0c-usable sample n={n} (should match Table 1's 59,834)")

    customers = combined_r0cb["customers_v2_event_excl_reinterruptions"].astype(float).to_numpy()
    duration = combined_r0cb["duration_B_full_span_hours"].astype(float).to_numpy()
    log1p_customers = np.log1p(customers)
    log_duration = np.log(duration)

    log_step("Computing distance correlation (log1p_customers vs log_duration, exact AVL algorithm)...")
    dcorr_obs, dcorr_null, dcorr_p, dcorr_t = perm_test(log1p_customers, log_duration, dcorr_stat)
    log_step(f"distance correlation = {dcorr_obs:.4f}, perm p={dcorr_p:.4f} "
              f"(null mean={dcorr_null.mean():.4f}, null std={dcorr_null.std():.4f}), "
              f"{N_PERM} perms in {dcorr_t:.1f}s")

    log_step("Computing distance correlation on RAW scale (customers_v2 vs duration_B) for robustness...")
    dcorr_raw_obs = dcorr_stat(customers, duration)
    log_step(f"distance correlation (raw scale) = {dcorr_raw_obs:.4f}")

    log_step("Computing mutual information (k-NN estimator, log1p_customers vs log_duration)...")
    mi_obs, mi_null, mi_p, mi_t = perm_test(log1p_customers, log_duration, mi_stat)
    mi_z = (mi_obs - mi_null.mean()) / mi_null.std()
    log_step(f"MI = {mi_obs:.4f} nats, perm p={mi_p:.4f}, z={mi_z:.1f} "
              f"(null mean={mi_null.mean():.4f}, null std={mi_null.std():.4f}), "
              f"{N_PERM} perms in {mi_t:.1f}s")

    result = {
        "n": int(n),
        "distance_correlation_log1p_customers_vs_log_duration": float(dcorr_obs),
        "distance_correlation_perm_p": float(dcorr_p),
        "distance_correlation_null_mean": float(dcorr_null.mean()),
        "distance_correlation_null_std": float(dcorr_null.std()),
        "distance_correlation_raw_scale": float(dcorr_raw_obs),
        "mutual_information_nats": float(mi_obs),
        "mutual_information_perm_p": float(mi_p),
        "mutual_information_z": float(mi_z),
        "mutual_information_null_mean": float(mi_null.mean()),
        "mutual_information_null_std": float(mi_null.std()),
        "n_permutations": N_PERM,
        "legacy_reference_distance_correlation_full": 0.375,
        "legacy_reference_distance_correlation_subset_customers_gt0": 0.519,
        "legacy_reference_mi_full_nats": 0.399,
        "legacy_reference_mi_subset_customers_gt0_nats": 0.211,
        "legacy_reference_n_full": 62928,
        "legacy_reference_n_subset": 53492,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "step38_M6_nonlinear_dependence.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved raw/step38_M6_nonlinear_dependence.json")


if __name__ == "__main__":
    main()
