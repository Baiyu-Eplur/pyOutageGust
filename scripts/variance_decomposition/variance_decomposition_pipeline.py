"""Command #14: nested-model variance decomposition (in-sample and 5-fold OOS R^2)
for E0' (exposure) and R0c'_B (recovery, both covariate orderings), restricted to
the weather_natural+technical_asset main-spec sample established by commands #12/13.

Read-only against rebuild_v3_full_stage/ and command #9's deterministic sample
construction (via importlib).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

V3_VALIDATION_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation\v3_validation_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\variance_decomposition")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

WT_GROUPS = {"weather_natural", "technical_asset"}

spec = importlib.util.spec_from_file_location("v3_validation_pipeline", V3_VALIDATION_SCRIPT)
v9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v9)


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
    print(f"[v14] {msg}", flush=True)


# ---------------- reconstruct WT samples (identical to command #12) ----------------

def build_wt_samples():
    log_step("Reconstructing base sample and restricting to weather_natural+technical_asset...")
    matched, _ = v9.step0_build_sample()
    matched, _ = v9.step1_lad_gapfill(matched)
    sample, _ = v9.step2_build_folds(matched)
    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()

    wt_mask = sample["cause_group_official"].isin(WT_GROUPS)
    sample_wt = sample.loc[wt_mask].copy()

    e0_sample = sample_wt.loc[sample_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    r0b_sample = sample_wt.loc[
        sample_wt["duration_B_full_span_hours"].notna() & (sample_wt["duration_B_full_span_hours"] > 0)
    ].copy()
    p99_b = r0b_sample["duration_B_full_span_hours"].quantile(0.99)
    r0b_sample = r0b_sample.loc[r0b_sample["duration_B_full_span_hours"] <= p99_b].copy()
    r0b_sample["log_duration_B_full_span_hours"] = np.log(r0b_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample = r0b_sample.loc[r0b_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    log_step(f"WT complete-predictor sample: n={len(sample_wt)}; "
              f"E0' n={len(e0_sample)}; R0c'_B n={len(r0cb_sample)} (p99 cap={p99_b:.2f}h).")
    return e0_sample, r0cb_sample


# ---------------- design-matrix builders for nested model blocks ----------------

REGION_SES_COLS = ["urban_binary", "log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
NONGUST_WEATHER_SCALE_COLS = ["precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]


def add_year_month_dummies(Xtr: pd.DataFrame, Xva: pd.DataFrame, tr: pd.DataFrame, va: pd.DataFrame):
    for c in ["incident_year", "incident_month"]:
        levels = sorted(pd.Series(tr[c].dropna().unique()).tolist())
        for level in levels[1:]:
            name = f"{c}[{level}]"
            Xtr[name] = (tr[c] == level).astype(float)
            Xva[name] = (va[c] == level).astype(float)


def build_block_baseline(tr: pd.DataFrame, va: pd.DataFrame):
    """Region SES controls + year/month FE. Closest available analogue to 'region
    fixed effects' in the already-established model spec — commands #9-#13 never
    used LAD dummy fixed effects in the mean model (LAD is only used for cluster-
    robust standard errors); introducing literal LAD FE now would be a new modeling
    choice inconsistent with all prior established specs, so this decomposition
    reuses the established region-level socioeconomic controls instead. Disclosed
    here rather than silently substituted."""
    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in REGION_SES_COLS:
        Xtr[c] = tr[c].astype(float)
        Xva[c] = va[c].astype(float)
    add_year_month_dummies(Xtr, Xva, tr, va)
    return Xtr, Xva


def add_block_nongust_weather(Xtr, Xva, tr, va):
    for c in NONGUST_WEATHER_SCALE_COLS:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        Xtr["z_" + c] = (tr[c] - mu) / sd
        Xva["z_" + c] = (va[c] - mu) / sd
    return Xtr, Xva


def add_block_gust(Xtr, Xva, tr, va):
    mu, sd = tr["gust_0h"].mean(), tr["gust_0h"].std(ddof=1)
    Xtr["z_gust_0h"] = (tr["gust_0h"] - mu) / sd
    Xva["z_gust_0h"] = (va["gust_0h"] - mu) / sd
    Xtr["z_gust_0h_sq"] = Xtr["z_gust_0h"] ** 2
    Xva["z_gust_0h_sq"] = Xva["z_gust_0h"] ** 2
    if "z_pressure_msl_0h" in Xtr.columns:
        Xtr["z_gust_pressure"] = Xtr["z_gust_0h"] * Xtr["z_pressure_msl_0h"]
        Xva["z_gust_pressure"] = Xva["z_gust_0h"] * Xva["z_pressure_msl_0h"]
    return Xtr, Xva


def add_block_customers(Xtr, Xva, tr, va):
    mu, sd = tr["log1p_customers_v2"].mean(), tr["log1p_customers_v2"].std(ddof=1)
    Xtr["z_log1p_customers_v2"] = (tr["log1p_customers_v2"] - mu) / sd
    Xva["z_log1p_customers_v2"] = (va["log1p_customers_v2"] - mu) / sd
    Xtr["z_log1p_customers_v2_sq"] = Xtr["z_log1p_customers_v2"] ** 2
    Xva["z_log1p_customers_v2_sq"] = Xva["z_log1p_customers_v2"] ** 2
    return Xtr, Xva


BLOCK_BUILDERS = {
    "nongust_weather": add_block_nongust_weather,
    "gust": add_block_gust,
    "customers": add_block_customers,
}


def fit_and_r2(Xtr, ytr, Xva, yva):
    res = sm.OLS(ytr.astype(float), Xtr.astype(float)).fit()
    fitted = res.predict(Xtr.astype(float))
    ss_res_in = float(((ytr - fitted) ** 2).sum())
    ss_tot_in = float(((ytr - ytr.mean()) ** 2).sum())
    r2_in = 1 - ss_res_in / ss_tot_in
    pred_va = res.predict(Xva.astype(float))
    return r2_in, pred_va


def nested_r2_sequence(df: pd.DataFrame, y_col: str, block_order: list[str], model_label: str):
    """Fit the baseline + each nested block addition, in-sample (full-sample fit)
    and 5-fold OOS (pooled out-of-fold predictions), reporting R^2 at each step."""
    results = []

    # ---- in-sample (full-sample standardization + full-sample fit) ----
    Xtr_full, _ = build_block_baseline(df, df)
    y = df[y_col].astype(float)
    cum_blocks = []
    r2_in_prev = None
    Xcur = Xtr_full.copy()
    res = sm.OLS(y, Xcur.astype(float)).fit()
    fitted = res.predict(Xcur.astype(float))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2_in = 1 - float(((y - fitted) ** 2).sum()) / ss_tot
    results.append({"model": model_label, "step": "baseline", "blocks_added": "region_SES+year_month_FE",
                     "r2_in_sample": r2_in, "r2_in_sample_increment": None})
    r2_in_prev = r2_in
    for block in block_order:
        Xcur, _ = BLOCK_BUILDERS[block](Xcur, Xcur.copy(), df, df)
        res = sm.OLS(y, Xcur.astype(float)).fit()
        fitted = res.predict(Xcur.astype(float))
        r2_in = 1 - float(((y - fitted) ** 2).sum()) / ss_tot
        results.append({"model": model_label, "step": block, "blocks_added": block,
                         "r2_in_sample": r2_in, "r2_in_sample_increment": r2_in - r2_in_prev})
        r2_in_prev = r2_in

    # ---- out-of-sample (5-fold, train-only standardization, pooled OOF predictions) ----
    def oof_predictions(blocks_included: list[str]):
        preds = pd.Series(index=df.index, dtype=float)
        for fold in range(5):
            va_mask = df["cv_fold_v3"].eq(fold)
            tr_mask = df["cv_fold_v3"].ne(fold) & df["cv_fold_v3"].ge(0)
            tr, va = df.loc[tr_mask], df.loc[va_mask]
            Xtr, Xva = build_block_baseline(tr, va)
            for block in blocks_included:
                Xtr, Xva = BLOCK_BUILDERS[block](Xtr, Xva, tr, va)
            ytr = tr[y_col].astype(float)
            res = sm.OLS(ytr, Xtr.astype(float)).fit()
            preds.loc[va.index] = res.predict(Xva.astype(float)).values
        return preds

    y_all = df[y_col].astype(float)
    ss_tot_oof = float(((y_all - y_all.mean()) ** 2).sum())

    cumulative = []
    r2_oos_prev = None
    preds0 = oof_predictions([])
    r2_oos = 1 - float(((y_all - preds0) ** 2).sum()) / ss_tot_oof
    results[0]["r2_oos_5fold"] = r2_oos
    results[0]["r2_oos_5fold_increment"] = None
    r2_oos_prev = r2_oos
    for i, block in enumerate(block_order):
        cumulative.append(block)
        preds = oof_predictions(cumulative)
        r2_oos = 1 - float(((y_all - preds) ** 2).sum()) / ss_tot_oof
        results[i + 1]["r2_oos_5fold"] = r2_oos
        results[i + 1]["r2_oos_5fold_increment"] = r2_oos - r2_oos_prev
        r2_oos_prev = r2_oos

    return pd.DataFrame(results)


def main():
    e0_sample, r0cb_sample = build_wt_samples()

    log_step("Step 1: E0' nested variance decomposition (baseline -> nongust_weather -> gust)...")
    e0_seq = nested_r2_sequence(e0_sample, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_prime_WT")
    e0_seq.to_csv(RAW_DIR / "E0_prime_WT_variance_decomposition.csv", index=False)
    print(e0_seq.to_string(index=False))

    log_step("Step 2a: R0c'_B nested variance decomposition, order 甲 (customers -> gust)...")
    r0cb_order_a = nested_r2_sequence(
        r0cb_sample, "log_duration_B_full_span_hours",
        ["nongust_weather", "customers", "gust"], "R0c_prime_B_WT_order_customers_then_gust")
    r0cb_order_a.to_csv(RAW_DIR / "R0c_prime_B_WT_order_customers_then_gust.csv", index=False)
    print(r0cb_order_a.to_string(index=False))

    log_step("Step 2b: R0c'_B nested variance decomposition, order 乙 (gust -> customers)...")
    r0cb_order_b = nested_r2_sequence(
        r0cb_sample, "log_duration_B_full_span_hours",
        ["nongust_weather", "gust", "customers"], "R0c_prime_B_WT_order_gust_then_customers")
    r0cb_order_b.to_csv(RAW_DIR / "R0c_prime_B_WT_order_gust_then_customers.csv", index=False)
    print(r0cb_order_b.to_string(index=False))

    sample_sizes = {"n_e0_prime_wt": int(len(e0_sample)), "n_r0c_prime_b_wt": int(len(r0cb_sample))}
    (RAW_DIR / "sample_sizes.json").write_text(js(sample_sizes), encoding="utf-8")

    log_step("All steps complete.")


if __name__ == "__main__":
    main()
