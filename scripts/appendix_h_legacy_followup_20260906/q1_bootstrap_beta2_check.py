"""Command #51, Question 1: re-run command #43's M05 bootstrap diagnostic
(capturing beta1/beta2, not just the turning-point ratio) on the C01+C02-C08
CORRECTED final E0 sample, using the EXACT same deterministic procedure as
figure4_dose_response.py / critical_wind_speed_pipeline.py's
bootstrap_turning_point (seed 20260826, n_boot=500, date-block resampling
with replacement, v9.design_train_valid on each resample). Read-only
diagnostic; does not touch any historical result file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\appendix_h_legacy_followup_20260906\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260826


def log_step(msg):
    print(f"[Q1] {msg}", flush=True)


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
    v9, _, _ = _patch_v9()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()
    combined_e0["incident_date_utc"] = pd.to_datetime(combined_e0["incident_date_utc"], errors="coerce")

    Xfull, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    y = combined_e0["log1p_customers_v2"].astype(float)
    res = sm.OLS(y, Xfull.astype(float)).fit()
    b1 = float(res.params["z_gust_0h"])
    b2 = float(res.params["z_gust_0h_sq"])
    z_star = -b1 / (2 * b2)
    gust_mean = float(combined_e0["gust_0h"].mean())
    gust_sd = float(combined_e0["gust_0h"].std(ddof=1))
    log_step(f"Corrected full-sample fit: beta1={b1!r}, beta2={b2!r}, z*={z_star!r}, "
              f"turning_point_ms={gust_mean + z_star * gust_sd:.4f}")

    rng = np.random.default_rng(RNG_SEED)
    df = combined_e0
    dates = df["incident_date_utc"].dt.date.astype(str)
    unique_dates = dates.unique()
    n_dates = len(unique_dates)
    by_date = {d: idx.to_numpy() for d, idx in df.groupby(dates).groups.items()}

    boot_rows = []
    for b in range(N_BOOTSTRAP):
        sampled_dates = rng.choice(unique_dates, size=n_dates, replace=True)
        idx = np.concatenate([by_date[d] for d in sampled_dates])
        boot_df = df.loc[idx].copy()
        try:
            Xb, _ = v9.design_train_valid(boot_df, boot_df, extra_scale_cols=None)
            yb = boot_df["log1p_customers_v2"].astype(float)
            resb = sm.OLS(yb, Xb.astype(float)).fit()
            bb1 = float(resb.params["z_gust_0h"])
            bb2 = float(resb.params["z_gust_0h_sq"])
            boot_gust_mean = float(boot_df["gust_0h"].mean())
            boot_gust_sd = float(boot_df["gust_0h"].std(ddof=1))
            tp = -bb1 / (2 * bb2)
            boot_rows.append({"b": b, "beta1": bb1, "beta2": bb2, "turning_point_z": tp,
                               "boot_gust_mean": boot_gust_mean, "boot_gust_sd": boot_gust_sd,
                               "turning_point_ms": boot_gust_mean + tp * boot_gust_sd})
        except Exception as exc:  # noqa: BLE001
            boot_rows.append({"b": b, "beta1": np.nan, "beta2": np.nan, "turning_point_z": np.nan,
                               "boot_gust_mean": np.nan, "boot_gust_sd": np.nan, "turning_point_ms": np.nan})
        if (b + 1) % 100 == 0:
            log_step(f"  bootstrap {b + 1}/{N_BOOTSTRAP} done")

    boot_df_out = pd.DataFrame(boot_rows)
    boot_df_out.to_csv(RAW_DIR / "q1_bootstrap_full_corrected.csv", index=False)

    valid = boot_df_out.dropna(subset=["beta2"])
    log_step(f"Valid bootstrap replicates: {len(valid)} / {N_BOOTSTRAP}")

    # cross-check against the officially-reported (percentile-only) bootstrap CI
    boot_lo_z, boot_hi_z = np.percentile(valid["turning_point_z"], [2.5, 97.5])
    boot_lo_ms = gust_mean + boot_lo_z * gust_sd
    boot_hi_ms = gust_mean + boot_hi_z * gust_sd
    log_step(f"Reproduced bootstrap CI (z): [{boot_lo_z:.4f},{boot_hi_z:.4f}], "
              f"(ms, using ORIGINAL full-sample mean/sd): [{boot_lo_ms:.4f},{boot_hi_ms:.4f}]")

    beta2_near_zero_1pct = (valid["beta2"].abs() < 0.01 * valid["beta2"].abs().median()).mean() * 100
    beta2_near_zero_10pct = (valid["beta2"].abs() < 0.10 * abs(b2)).mean() * 100
    beta2_sign_negative = (valid["beta2"] < 0).mean() * 100
    beta2_sign_nonpositive = (valid["beta2"] <= 0).mean() * 100
    beta2_stats = {
        "point_estimate_full_sample": b2,
        "mean": float(valid["beta2"].mean()), "std": float(valid["beta2"].std(ddof=1)),
        "min": float(valid["beta2"].min()), "max": float(valid["beta2"].max()),
        "n_negative": int((valid["beta2"] < 0).sum()), "n_nonpositive": int((valid["beta2"] <= 0).sum()),
        "pct_negative": float(beta2_sign_negative), "pct_nonpositive": float(beta2_sign_nonpositive),
        "pct_within_1pct_of_median": float(beta2_near_zero_1pct),
        "pct_within_10pct_of_point_estimate": float(beta2_near_zero_10pct),
        "percentiles": {str(p): float(np.percentile(valid["beta2"], p)) for p in [1, 5, 25, 50, 75, 95, 99]},
        "min_as_pct_of_point_estimate": float(valid["beta2"].min() / b2 * 100),
    }
    log_step(f"beta2 bootstrap distribution (corrected data): {json.dumps(beta2_stats, indent=2, default=float)}")

    beta1_stats = {
        "point_estimate_full_sample": b1,
        "mean": float(valid["beta1"].mean()), "std": float(valid["beta1"].std(ddof=1)),
        "min": float(valid["beta1"].min()), "max": float(valid["beta1"].max()),
        "n_positive": int((valid["beta1"] > 0).sum()),
        "pct_positive": float((valid["beta1"] > 0).mean() * 100),
    }
    log_step(f"beta1 bootstrap distribution (corrected data): {beta1_stats}")

    tp_stats = {
        "mean": float(valid["turning_point_z"].mean()), "std": float(valid["turning_point_z"].std(ddof=1)),
        "skew": float(pd.Series(valid["turning_point_z"]).skew()),
        "kurtosis_excess": float(pd.Series(valid["turning_point_z"]).kurt()),
        "percentiles": {str(p): float(np.percentile(valid["turning_point_z"], p))
                         for p in [1, 2.5, 5, 25, 50, 75, 95, 97.5, 99]},
    }
    log_step(f"turning_point_z bootstrap distribution shape (corrected): {tp_stats}")

    result = {
        "full_sample": {"beta1": b1, "beta2": b2, "z_star": z_star,
                         "turning_point_ms": gust_mean + z_star * gust_sd,
                         "gust_mean": gust_mean, "gust_sd": gust_sd},
        "n_valid": int(len(valid)),
        "beta1_distribution": beta1_stats,
        "beta2_distribution": beta2_stats,
        "turning_point_z_distribution": tp_stats,
        "reproduced_bootstrap_ci_z": [float(boot_lo_z), float(boot_hi_z)],
        "reproduced_bootstrap_ci_ms_using_full_sample_scale": [float(boot_lo_ms), float(boot_hi_ms)],
    }
    (RAW_DIR / "q1_result.json").write_text(js(result), encoding="utf-8")
    log_step("Saved q1_result.json and q1_bootstrap_full_corrected.csv")


if __name__ == "__main__":
    main()
