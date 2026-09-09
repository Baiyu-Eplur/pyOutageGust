"""IR04 diagnostic: quantify the difference between the CURRENT bootstrap-CI
conversion method used by figure4_dose_response.py (take percentiles on the
z-scale bootstrap distribution, then apply ONE fixed full-sample gust
mean/SD to convert the two percentile endpoints to m/s) versus the more
rigorous alternative (convert EACH resample's own z* to m/s using THAT
resample's own gust mean/SD, then take percentiles of the m/s values).

This is diagnostic-only: it does not change any existing model result or
figure. Uses the C01-corrected E0 sample and reproduces the exact same
500-draw, seed=20260826 date-block bootstrap as figure4_dose_response.py,
except it additionally records each resample's own gust mean/SD so both
conversion orders can be compared on identical resamples.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = result_path('independent_review_ir_20260905/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[IR04] {msg}", flush=True)


def turning_point(b1, b2):
    if b2 == 0:
        return np.nan
    return -b1 / (2 * b2)


def main():
    v9, _, _ = _patch_v9()
    _, combined_e0, _, _ = build_corrected_combined_samples()

    df = combined_e0.copy()
    df["incident_date_utc"] = pd.to_datetime(df["incident_date_utc"], errors="coerce")

    # full-sample gust mean/SD, exactly as figure4_dose_response.py's build_curve() obtains
    # via v11.fit_full_sample -> design_train_valid(sample, sample, ...) fit on the FULL sample
    gust_mean_full = df["gust_0h"].mean()
    gust_sd_full = df["gust_0h"].std(ddof=1)
    log_step(f"Full-sample gust mean={gust_mean_full:.4f}, sd={gust_sd_full:.4f}")

    rng = np.random.default_rng(20260826)
    dates = df["incident_date_utc"].dt.date.astype(str)
    unique_dates = dates.unique()
    n_dates = len(unique_dates)
    by_date = {d: idx.to_numpy() for d, idx in df.groupby(dates).groups.items()}

    z_star_list = []
    ms_star_per_resample_list = []
    resample_gust_mean_list = []
    resample_gust_sd_list = []
    n_failed = 0

    for b in range(500):
        sampled_dates = rng.choice(unique_dates, size=n_dates, replace=True)
        idx = np.concatenate([by_date[d] for d in sampled_dates])
        boot_df = df.loc[idx].copy()
        try:
            Xb, _ = v9.design_train_valid(boot_df, boot_df, extra_scale_cols=None)
            y = boot_df["log1p_customers_v2"].astype(float)
            res = sm.OLS(y, Xb.astype(float)).fit()
            b1 = res.params["z_gust_0h"]
            b2 = res.params["z_gust_0h_sq"]
            z_star = turning_point(b1, b2)
            # this resample's OWN gust mean/SD (what design_train_valid actually used internally)
            resample_mean = boot_df["gust_0h"].mean()
            resample_sd = boot_df["gust_0h"].std(ddof=1)
            ms_star_this_resample = resample_mean + z_star * resample_sd

            z_star_list.append(z_star)
            ms_star_per_resample_list.append(ms_star_this_resample)
            resample_gust_mean_list.append(resample_mean)
            resample_gust_sd_list.append(resample_sd)
        except Exception as exc:  # noqa: BLE001
            n_failed += 1
        if (b + 1) % 100 == 0:
            log_step(f"  bootstrap {b + 1}/500 done")

    z_arr = np.array(z_star_list)
    ms_per_resample_arr = np.array(ms_star_per_resample_list)
    mean_arr = np.array(resample_gust_mean_list)
    sd_arr = np.array(resample_gust_sd_list)

    log_step(f"n_valid={len(z_arr)}, n_failed={n_failed}")
    log_step(f"Per-resample gust mean: range=[{mean_arr.min():.4f},{mean_arr.max():.4f}], "
              f"std of means across resamples={mean_arr.std():.4f}")
    log_step(f"Per-resample gust sd: range=[{sd_arr.min():.4f},{sd_arr.max():.4f}], "
              f"std of sds across resamples={sd_arr.std():.4f}")

    # ---- Method (b): CURRENT method -- percentile on z-scale first, then ONE fixed conversion ----
    boot_lo_z, boot_hi_z = np.percentile(z_arr, [2.5, 97.5])
    current_lo_ms = gust_mean_full + boot_lo_z * gust_sd_full
    current_hi_ms = gust_mean_full + boot_hi_z * gust_sd_full

    # ---- Method (a): per-resample conversion FIRST, then percentile on the m/s values ----
    strict_lo_ms, strict_hi_ms = np.percentile(ms_per_resample_arr, [2.5, 97.5])

    log_step("=" * 70)
    log_step(f"CURRENT method (percentile-on-z, then fixed full-sample conversion): "
              f"[{current_lo_ms:.4f}, {current_hi_ms:.4f}] m/s")
    log_step(f"STRICTER method (per-resample own mean/SD conversion, then percentile): "
              f"[{strict_lo_ms:.4f}, {strict_hi_ms:.4f}] m/s")
    log_step(f"Difference in lower bound: {strict_lo_ms - current_lo_ms:+.4f} m/s")
    log_step(f"Difference in upper bound: {strict_hi_ms - current_hi_ms:+.4f} m/s")
    log_step(f"Difference in CI width: {(strict_hi_ms - strict_lo_ms) - (current_hi_ms - current_lo_ms):+.4f} m/s")

    result = {
        "n_valid": int(len(z_arr)), "n_failed": int(n_failed),
        "full_sample_gust_mean": float(gust_mean_full), "full_sample_gust_sd": float(gust_sd_full),
        "resample_gust_mean_range": [float(mean_arr.min()), float(mean_arr.max())],
        "resample_gust_mean_std_across_resamples": float(mean_arr.std()),
        "resample_gust_sd_range": [float(sd_arr.min()), float(sd_arr.max())],
        "resample_gust_sd_std_across_resamples": float(sd_arr.std()),
        "current_method_ci_ms": [float(current_lo_ms), float(current_hi_ms)],
        "stricter_method_ci_ms": [float(strict_lo_ms), float(strict_hi_ms)],
        "lower_bound_diff_ms": float(strict_lo_ms - current_lo_ms),
        "upper_bound_diff_ms": float(strict_hi_ms - current_hi_ms),
        "width_diff_ms": float((strict_hi_ms - strict_lo_ms) - (current_hi_ms - current_lo_ms)),
    }
    (RAW_DIR / "ir04_bootstrap_conversion_comparison.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved ir04_bootstrap_conversion_comparison.json")


if __name__ == "__main__":
    main()
