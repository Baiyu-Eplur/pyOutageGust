"""Command #22 Step 1-2: customers_v2 dose-response curve for R0c (gust and all
other covariates fixed at the SAME reference values command #21 Step3 used),
paired side-by-side with command #21's existing gust dose-response curve.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

V11_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\critical_wind_speed\critical_wind_speed_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)


def log_step(msg):
    print(f"[v22] {msg}", flush=True)


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
    _, _, combined_r0cb, _ = build_combined_samples()

    log_step("Fitting R0c final model (identical to command #21 Step1) for the customers_v2 curve...")
    sample = combined_r0cb.copy()
    sample["customers_v2_log1p"] = np.log1p(sample["customers_v2_event_excl_reinterruptions"].astype(float))
    res, cov, gust_mean, gust_sd, d = v11.fit_full_sample(
        sample, "log_duration_B_full_span_hours", use_customers_covariate=True)
    exog_names = list(res.model.exog_names)

    # SAME reference-value convention as command #21 Step3: every non-target
    # covariate (including gust terms this time) is fixed at its ACTUAL sample
    # mean as it appears in the fitted design matrix (Xtr_full.mean()), not an
    # artificially zeroed square term.
    Xtr_full, _ = v9.design_train_valid(sample, sample, extra_scale_cols=["customers_v2_log1p"])
    means = Xtr_full.mean(axis=0)

    cust_raw = d["customers_v2_event_excl_reinterruptions"]
    p1, p99 = cust_raw.quantile(0.01), cust_raw.quantile(0.99)
    grid_raw = np.linspace(p1, p99, 50)
    grid_log1p = np.log1p(grid_raw)
    cust_mean_log1p = sample["customers_v2_log1p"].mean()
    cust_sd_log1p = sample["customers_v2_log1p"].std(ddof=1)
    grid_z = (grid_log1p - cust_mean_log1p) / cust_sd_log1p

    X = pd.DataFrame(0.0, index=range(len(grid_z)), columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0
    for c in exog_names:
        if c in ("z_log1p_customers_v2", "z_log1p_customers_v2_sq", "Intercept"):
            continue
        if c in means.index:
            X[c] = means[c]
    X["z_log1p_customers_v2"] = grid_z
    X["z_log1p_customers_v2_sq"] = grid_z ** 2

    beta = res.params.loc[exog_names]
    eta = X[exog_names].astype(float) @ beta
    pred = np.exp(eta)

    curve = pd.DataFrame({
        "model": "R0c_customers_dose_response",
        "customers_v2_raw": grid_raw, "customers_v2_log1p": grid_log1p, "customers_v2_z": grid_z,
        "predicted_duration_B": pred.values,
    })
    curve.to_csv(OUT_DIR / "07_customers_v2剂量反应曲线.csv", index=False)

    ratio = float(pred.max() / pred.min())
    log_step(f"customers_v2 dose-response max/min ratio: {ratio:.4f}")

    # ---- cross-check against command #21 Step5's reported 5.99 ----
    expected = 5.99
    diff_pct = abs(ratio - expected) / expected * 100
    consistency_note = (
        f"Matches command #21 Step5's reported ratio (5.99) within {diff_pct:.2f}%."
        if diff_pct < 2 else
        f"⚠️ DIVERGES from command #21 Step5's reported ratio (5.99) by {diff_pct:.2f}% -- needs investigation."
    )
    log_step(consistency_note)

    summary = {
        "n": int(len(sample)), "p1_raw": float(p1), "p99_raw": float(p99),
        "pred_min": float(pred.min()), "pred_max": float(pred.max()),
        "max_min_ratio": ratio, "command21_step5_reported_ratio": expected,
        "consistency_check": consistency_note,
    }
    (RAW_DIR / "step7_customers_dose_response_summary.json").write_text(js(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # ---------------- Step 2: paired plot ----------------
    log_step("Loading command #21 Step3's gust dose-response curve for the paired plot...")
    gust_curve_all = pd.read_csv(OUT_DIR / "03_阵风剂量反应曲线.csv")
    gust_curve_r0c = gust_curve_all[gust_curve_all["model"] == "R0c_gust_dose_response"].copy()
    gust_ratio = float(gust_curve_r0c["predicted_level"].max() / gust_curve_r0c["predicted_level"].min())
    log_step(f"Gust (R0c) max/min ratio from command #21 Step3: {gust_ratio:.4f}")

    y_min = min(gust_curve_r0c["predicted_level"].min(), curve["predicted_duration_B"].min())
    y_max = max(gust_curve_r0c["predicted_level"].max(), curve["predicted_duration_B"].max())
    y_pad = (y_max - y_min) * 0.08

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    axes[0].plot(gust_curve_r0c["gust_ms"], gust_curve_r0c["predicted_level"], color="#d95f02", linewidth=2)
    axes[0].set_xlabel("Gust wind speed (m/s)")
    axes[0].set_ylabel("Predicted outage duration (hours)")
    axes[0].set_title(f"(a) Varying gust\n(max/min ratio = {gust_ratio:.2f}×)")
    axes[0].set_ylim(y_min - y_pad, y_max + y_pad)

    axes[1].plot(curve["customers_v2_raw"], curve["predicted_duration_B"], color="#1b9e77", linewidth=2)
    axes[1].set_xlabel("Affected customers (customers_v2)")
    axes[1].set_ylabel("Predicted outage duration (hours)")
    axes[1].set_title(f"(b) Varying customers_v2\n(max/min ratio = {ratio:.2f}×)")
    axes[1].set_ylim(y_min - y_pad, y_max + y_pad)

    fig.suptitle(
        "Predicted recovery duration's sensitivity to gust intensity vs. affected-customer scale\n"
        "(all other covariates fixed at their sample-mean reference values in both panels)",
        fontsize=11,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(OUT_DIR / "08_阵风vs客户规模剂量反应对比图.png", dpi=600, bbox_inches="tight")
    fig.savefig(OUT_DIR / "08_阵风vs客户规模剂量反应对比图.pdf", bbox_inches="tight")
    plt.close(fig)

    log_step("Done.")


if __name__ == "__main__":
    main()
