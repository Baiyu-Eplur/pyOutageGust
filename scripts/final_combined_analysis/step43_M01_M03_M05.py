"""Command #43: M01 (z=0 vs turning-point centering, algebraic proof), M03
(pressure-conditional turning points, full precision), M05 (bootstrap
resampling diagnostics -- beta1/beta2 distributions, not just the ratio).

M05 reuses the EXACT same deterministic bootstrap procedure as
critical_wind_speed_pipeline.py's bootstrap_turning_point (same seed
20260826, same n_boot=500, same date-block resampling with replacement,
same v9.design_train_valid call), only additionally capturing beta1/beta2
per replicate (the original function discarded them, keeping only the
ratio) -- this is a deterministic reproduction, not a new analytical choice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260826  # identical to step2_critical_wind_and_variance.py


def log_step(msg):
    print(f"[step43] {msg}", flush=True)


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
    combined_wt, combined_e0, combined_r0cb, _ = build_combined_samples()

    # ---------------- shared: full-sample E0 fit (exact same as command #21 step1) ----------------
    Xfull, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    y = combined_e0["log1p_customers_v2"].astype(float)
    res = sm.OLS(y, Xfull).fit()
    b1 = res.params["z_gust_0h"]
    b2 = res.params["z_gust_0h_sq"]
    b_gp = res.params["z_gust_pressure"]
    log_step(f"E0 full-sample (exact precision): beta1={b1!r}, beta2={b2!r}, beta_gust_pressure={b_gp!r}")
    z_star = -b1 / (2 * b2)
    log_step(f"Turning point z* = {z_star!r}")

    gust_mean = combined_e0["gust_0h"].mean()
    gust_sd = combined_e0["gust_0h"].std(ddof=1)
    log_step(f"gust_mean={gust_mean!r}, gust_sd={gust_sd!r}")

    def eta(z):
        return b1 * z + b2 * z ** 2

    # =============== M01: z=0-centered vs turning-point-centered asymmetry ===============
    log_step("=== M01 ===")
    m01 = {"centered_on_zero": {}, "centered_on_turning_point": {}}
    for k in (1, 2, 3):
        eta_plus = eta(k)
        eta_minus = eta(-k)
        ratio = eta_plus / eta_minus
        pct_diff = (1 - ratio) * 100
        m01["centered_on_zero"][k] = {
            "eta(+k)": eta_plus, "eta(-k)": eta_minus, "ratio": ratio, "pct_diff_1_minus_ratio": pct_diff,
        }
        log_step(f"z=0-centered, k={k}: eta(+k)={eta_plus:.6f}, eta(-k)={eta_minus:.6f}, "
                  f"ratio={ratio:.6f}, (1-ratio)={pct_diff:.2f}%")

    for k in (1, 2, 3):
        eta_plus = eta(z_star + k)
        eta_minus = eta(z_star - k)
        diff = eta_plus - eta_minus
        m01["centered_on_turning_point"][k] = {
            "eta(z*+k)": eta_plus, "eta(z*-k)": eta_minus, "diff": diff,
        }
        log_step(f"turning-point-centered, k={k}: eta(z*+k)={eta_plus:.10f}, eta(z*-k)={eta_minus:.10f}, "
                  f"diff={diff:.2e} (algebraic identity predicts exactly 0)")

    # algebraic proof: eta(z*+d) - eta(z*-d) = 2d*(b1 + 2*b2*z*) = 2d*0 = 0
    algebraic_check = b1 + 2 * b2 * z_star
    log_step(f"Algebraic check b1 + 2*b2*z* (should be ~0 by definition of z*): {algebraic_check!r}")
    m01["algebraic_identity_b1_plus_2b2_zstar"] = float(algebraic_check)

    # =============== M03: pressure-conditional turning points ===============
    log_step("=== M03 ===")
    m03 = {}
    for label, p in [("mean-1SD", -1.0), ("mean", 0.0), ("mean+1SD", 1.0)]:
        eff_b1 = b1 + b_gp * p
        z_p = -eff_b1 / (2 * b2)
        ms_p = gust_mean + z_p * gust_sd
        m03[label] = {"pressure_z": p, "effective_beta1": eff_b1, "turning_point_z": z_p, "turning_point_ms": ms_p}
        log_step(f"pressure={label} (z_pressure={p}): effective_beta1={eff_b1:.6f}, "
                  f"turning_point_z={z_p:.6f}, turning_point_ms={ms_p:.4f}")

    # =============== M05: bootstrap resampling diagnostics (capture beta1/beta2) ===============
    log_step("=== M05: deterministic reproduction of the E0 bootstrap, capturing beta1/beta2 ===")
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
            resb = sm.OLS(yb, Xb).fit()
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
    boot_df_out.to_csv(RAW_DIR / "step43_M05_bootstrap_full.csv", index=False)

    valid = boot_df_out.dropna(subset=["beta2"])
    log_step(f"Valid bootstrap replicates: {len(valid)} / {N_BOOTSTRAP}")

    # sanity check: does this reproduce the original saved turning_point_z distribution?
    orig = pd.read_csv(RAW_DIR / "step2_E0_bootstrap_turning_points_z.csv", header=None)[0].to_numpy()
    reproduced = valid["turning_point_z"].to_numpy()
    log_step(f"Reproduction check: original n={len(orig)}, reproduced n={len(reproduced)}; "
              f"max abs diff (sorted, positional) = {np.max(np.abs(np.sort(orig)-np.sort(reproduced))):.2e}")

    beta2_near_zero_1pct = (valid["beta2"].abs() < 0.01 * valid["beta2"].abs().median()).mean() * 100
    beta2_sign_negative = (valid["beta2"] < 0).mean() * 100
    beta2_stats = {
        "mean": float(valid["beta2"].mean()), "std": float(valid["beta2"].std(ddof=1)),
        "min": float(valid["beta2"].min()), "max": float(valid["beta2"].max()),
        "pct_negative": float(beta2_sign_negative),
        "pct_within_1pct_of_median_of_zero": float(beta2_near_zero_1pct),
        "percentiles": {str(p): float(np.percentile(valid["beta2"], p)) for p in [1, 5, 25, 50, 75, 95, 99]},
    }
    log_step(f"beta2 bootstrap distribution: {beta2_stats}")

    tp_stats = {
        "mean": float(valid["turning_point_z"].mean()), "std": float(valid["turning_point_z"].std(ddof=1)),
        "skew": float(pd.Series(valid["turning_point_z"]).skew()),
        "kurtosis_excess": float(pd.Series(valid["turning_point_z"]).kurt()),
        "percentiles": {str(p): float(np.percentile(valid["turning_point_z"], p)) for p in [1, 2.5, 5, 25, 50, 75, 95, 97.5, 99]},
    }
    log_step(f"turning_point_z bootstrap distribution shape: {tp_stats}")

    gust_mean_stats = {
        "boot_gust_mean_std_across_replicates": float(valid["boot_gust_mean"].std(ddof=1)),
        "boot_gust_sd_std_across_replicates": float(valid["boot_gust_sd"].std(ddof=1)),
        "original_gust_mean": float(gust_mean), "original_gust_sd": float(gust_sd),
    }
    log_step(f"Standardization re-estimation check: {gust_mean_stats}")

    result = {
        "M01": m01,
        "M03": m03,
        "M05": {
            "n_valid": int(len(valid)),
            "beta2_distribution": beta2_stats,
            "turning_point_z_distribution": tp_stats,
            "standardization_reestimated_per_replicate": True,
            "standardization_check": gust_mean_stats,
            "reproduction_matches_original_file": bool(np.max(np.abs(np.sort(orig) - np.sort(reproduced))) < 1e-6),
        },
    }
    (RAW_DIR / "step43_M01_M03_M05.json").write_text(js(result), encoding="utf-8")
    log_step("Saved raw/step43_M01_M03_M05.json and raw/step43_M05_bootstrap_full.csv")


if __name__ == "__main__":
    main()
