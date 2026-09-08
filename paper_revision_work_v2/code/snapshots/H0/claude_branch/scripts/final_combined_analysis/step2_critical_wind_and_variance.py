"""Command #21 Step 2: re-estimate E0's critical wind speed (with bootstrap CI)
and re-run variance decomposition (E0 + R0c both orderings), on the final
combined sample."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

V11_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
V14_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500
RNG_SEED = 20260826

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)

spec14 = importlib.util.spec_from_file_location("variance_decomposition_pipeline", V14_SCRIPT)
v14 = importlib.util.module_from_spec(spec14)
spec14.loader.exec_module(v14)


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


def log_step(msg):
    print(f"[v21-step2] {msg}", flush=True)


def main():
    combined_wt, combined_e0, combined_r0cb, verification = build_combined_samples()

    # ---------------- critical wind speed (E0 only) ----------------
    log_step("Full-sample fit E0 for turning point...")
    res_e0, cov_e0, mean_gust_e0, sd_gust_e0, d_e0 = v11.fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False)
    b1, b2 = res_e0.params["z_gust_0h"], res_e0.params["z_gust_0h_sq"]
    var1, var2 = cov_e0.loc["z_gust_0h", "z_gust_0h"], cov_e0.loc["z_gust_0h_sq", "z_gust_0h_sq"]
    cov12 = cov_e0.loc["z_gust_0h", "z_gust_0h_sq"]
    x_star, se_x, lo, hi = v11.delta_method_ci(b1, b2, var1, var2, cov12)
    log_step(f"beta1={b1:.4f}, beta2={b2:.4f}, x*={x_star:.4f}, delta-CI=[{lo:.4f},{hi:.4f}]")

    log_step(f"Bootstrap E0 ({N_BOOTSTRAP} draws, date-clustered)...")
    boot, n_failed = v11.bootstrap_turning_point(
        combined_e0, "log1p_customers_v2", False, N_BOOTSTRAP, RNG_SEED)
    boot_lo, boot_hi = np.percentile(boot, [2.5, 97.5])
    np.savetxt(RAW_DIR / "step2_E0_bootstrap_turning_points_z.csv", boot, delimiter=",")
    log_step(f"Bootstrap CI(z)=[{boot_lo:.4f},{boot_hi:.4f}]")

    def to_ms(z):
        return mean_gust_e0 + z * sd_gust_e0

    result = {
        "n": int(len(combined_e0)), "beta1": float(b1), "beta2": float(b2),
        "turning_point_z": float(x_star), "delta_se": float(se_x),
        "delta_ci_95_z": [float(lo), float(hi)],
        "bootstrap_n_success": int(len(boot)), "bootstrap_n_failed": int(n_failed),
        "bootstrap_mean_z": float(np.mean(boot)), "bootstrap_std_z": float(np.std(boot, ddof=1)),
        "bootstrap_ci_95_z": [float(boot_lo), float(boot_hi)],
        "gust_mean": float(mean_gust_e0), "gust_sd": float(sd_gust_e0),
        "point_ms": float(to_ms(x_star)),
        "delta_ci_95_ms": [float(to_ms(lo)), float(to_ms(hi))],
        "bootstrap_ci_95_ms": [float(to_ms(boot_lo)), float(to_ms(boot_hi))],
    }

    gust_dist = d_e0["gust_0h"]
    result["gust_distribution"] = {
        "min": float(gust_dist.min()), "p1": float(gust_dist.quantile(0.01)), "p50": float(gust_dist.quantile(0.50)),
        "p95": float(gust_dist.quantile(0.95)), "p99": float(gust_dist.quantile(0.99)), "max": float(gust_dist.max()),
    }
    result["turning_point_percentile"] = float((gust_dist < result["point_ms"]).mean() * 100)

    (RAW_DIR / "step2_critical_wind_speed.json").write_text(js(result), encoding="utf-8")
    print(json.dumps(result, indent=2))

    # ---------------- variance decomposition: fresh 5-fold GroupKFold on the ----
    # ---------------- combined sample, reusing command #14/#16's OOS method ----
    from sklearn.model_selection import GroupKFold

    log_step("Building fresh 5-fold GroupKFold (by date) on the combined sample "
              "for out-of-sample variance decomposition (matches command #14/#16 method)...")

    def add_fresh_folds(df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        d["incident_date_utc"] = pd.to_datetime(d["incident_date_utc"], errors="coerce")
        gkf = GroupKFold(n_splits=5)
        d["cv_fold_v3"] = -1
        groups = d["incident_date_utc"].dt.date.astype(str)
        X_dummy = np.zeros(len(d))
        for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
            d.iloc[valid_idx, d.columns.get_loc("cv_fold_v3")] = fold_idx
        date_fold_counts = d.groupby(groups)["cv_fold_v3"].nunique()
        n_crossing = int((date_fold_counts > 1).sum())
        log_step(f"  fold sizes: {d['cv_fold_v3'].value_counts().sort_index().to_dict()}, "
                  f"dates crossing folds: {n_crossing} (expect 0)")
        assert n_crossing == 0
        return d

    combined_e0_folds = add_fresh_folds(combined_e0)
    combined_r0cb_folds = add_fresh_folds(combined_r0cb)

    e0_var = v14.nested_r2_sequence(combined_e0_folds, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_final_combined")
    e0_var.to_csv(RAW_DIR / "step2_E0_variance_decomposition.csv", index=False)
    print(e0_var.to_string(index=False))

    r0c_var_a = v14.nested_r2_sequence(
        combined_r0cb_folds, "log_duration_B_full_span_hours",
        ["nongust_weather", "customers", "gust"], "R0c_final_combined_order_customers_then_gust")
    r0c_var_a.to_csv(RAW_DIR / "step2_R0c_order_customers_then_gust.csv", index=False)
    print(r0c_var_a.to_string(index=False))

    r0c_var_b = v14.nested_r2_sequence(
        combined_r0cb_folds, "log_duration_B_full_span_hours",
        ["nongust_weather", "gust", "customers"], "R0c_final_combined_order_gust_then_customers")
    r0c_var_b.to_csv(RAW_DIR / "step2_R0c_order_gust_then_customers.csv", index=False)
    print(r0c_var_b.to_string(index=False))

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
