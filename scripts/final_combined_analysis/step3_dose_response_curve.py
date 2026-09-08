"""Command #21 Step 3: gust dose-response curve (region held fixed at sample
mean, only gust varies), using Step 1's final combined-sample model."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

V11_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)


def log_step(msg):
    print(f"[v21-step3] {msg}", flush=True)


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


def build_curve(sample, target_col, use_customers, model_label):
    res, cov, gust_mean, gust_sd, d = v11.fit_full_sample(sample, target_col, use_customers_covariate=use_customers)

    gust_raw = d["gust_0h"]
    p1, p99 = gust_raw.quantile(0.01), gust_raw.quantile(0.99)
    grid_ms = np.linspace(p1, p99, 50)
    grid_z = (grid_ms - gust_mean) / gust_sd

    # Build a design matrix matching the fitted model's exog, with all non-gust
    # covariates fixed at the ESTIMATION SAMPLE's mean (for customers: fixed at
    # the sample mean of log1p(customers_v2), representing "region/customers held
    # fixed"; year/month FE: use the average predicted effect by setting all
    # year/month dummies to their sample-mean incidence rate, so the curve
    # reflects an "average calendar" reference rather than an arbitrary single
    # year/month choice).
    exog_names = list(res.model.exog_names)
    X = pd.DataFrame(0.0, index=range(len(grid_z)), columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0

    # non-gust continuous covariates: fixed at sample mean of their z-scored /
    # raw form as already present in the training design (mean of a z-scored
    # variable is ~0 by construction, but we take the ACTUAL column mean used
    # in fitting for exactness, e.g. urban_binary, log_population, etc.)
    if use_customers:
        s = sample.copy()
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        Xtr_full, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    else:
        Xtr_full, _ = v9.design_train_valid(sample, sample, extra_scale_cols=None)

    means = Xtr_full.mean(axis=0)
    for c in exog_names:
        if c in ("z_gust_0h", "z_gust_0h_sq", "z_gust_pressure", "Intercept"):
            continue
        if c in means.index:
            X[c] = means[c]

    X["z_gust_0h"] = grid_z
    X["z_gust_0h_sq"] = grid_z ** 2
    if "z_gust_pressure" in X.columns:
        X["z_gust_pressure"] = grid_z * means.get("z_pressure_msl_0h", 0.0)

    beta = res.params.loc[exog_names]
    eta = X[exog_names].astype(float) @ beta
    pred = np.exp(eta)

    curve = pd.DataFrame({
        "model": model_label, "gust_ms": grid_ms, "gust_z": grid_z, "predicted_level": pred.values,
    })
    ratio = float(curve["predicted_level"].max() / curve["predicted_level"].min())
    return curve, ratio, {"p1_ms": float(p1), "p99_ms": float(p99), "max_min_ratio": ratio}


def main():
    _, combined_e0, combined_r0cb, _ = build_combined_samples()

    log_step("Building E0 dose-response curve (customers_v2 as outcome)...")
    curve_e0, ratio_e0, meta_e0 = build_curve(combined_e0, "log1p_customers_v2", False, "E0_gust_dose_response")
    log_step(f"E0 max/min ratio across observed gust range: {ratio_e0:.3f}")

    log_step("Building R0c dose-response curve (duration_B as outcome, customers_v2 fixed at sample mean)...")
    curve_r0c, ratio_r0c, meta_r0c = build_curve(
        combined_r0cb, "log_duration_B_full_span_hours", True, "R0c_gust_dose_response")
    log_step(f"R0c max/min ratio across observed gust range: {ratio_r0c:.3f}")

    combined_curve = pd.concat([curve_e0, curve_r0c], ignore_index=True)
    combined_curve.to_csv(OUT_DIR / "03_阵风剂量反应曲线.csv", index=False)

    summary = {"E0": meta_e0, "R0c": meta_r0c}
    (RAW_DIR / "step3_dose_response_summary.json").write_text(js(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    log_step("Done.")


if __name__ == "__main__":
    main()
