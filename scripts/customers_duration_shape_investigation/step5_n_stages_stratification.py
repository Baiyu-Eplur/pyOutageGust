"""Command #18: check whether the customers_v2/duration_B inverted-U is a
mechanical byproduct of n_stages (both variables are stage-count-dependent by
construction: duration_B = full multi-stage span, customers_v2 = cross-stage sum).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import build_clean_wt_samples, v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\customers_duration_shape_investigation")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[v18] {msg}", flush=True)


def decile_bin_report(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> pd.DataFrame:
    d = df[[x_col, y_col]].dropna().copy()
    try:
        d["decile"] = pd.qcut(d[x_col], q=10, duplicates="drop")
    except ValueError:
        d["decile"] = pd.qcut(d[x_col], q=5, duplicates="drop")
    rows = []
    for decile, g in d.groupby("decile", observed=True):
        rows.append({
            "label": label, "decile": str(decile), "n": len(g),
            "x_min": float(g[x_col].min()), "x_max": float(g[x_col].max()), "x_median": float(g[x_col].median()),
            "y_mean": float(g[y_col].mean()), "y_median": float(g[y_col].median()),
        })
    return pd.DataFrame(rows)


def main():
    _, _, r0cb_sample, _ = build_clean_wt_samples()
    r0cb_sample = r0cb_sample.copy()
    r0cb_sample["log_duration_B"] = np.log(r0cb_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    log_step("Joining stage_row_count (n_stages) from v3 dataset...")
    SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
    stage_counts = pd.read_csv(SRC, usecols=["Incident Reference", "stage_row_count"], low_memory=False)
    stage_counts = stage_counts.drop_duplicates("Incident Reference").set_index("Incident Reference")["stage_row_count"]
    r0cb_sample["stage_row_count"] = r0cb_sample["Incident Reference"].map(stage_counts)
    assert r0cb_sample["stage_row_count"].notna().all(), "some events missing stage_row_count after join"

    # ---------------- Step 1: n_stages distribution ----------------
    log_step("Step 1: n_stages distribution...")
    n_stages = r0cb_sample["stage_row_count"]
    bins = [1, 2, 3, 5, 10, np.inf]
    labels = ["1", "2", "3-4", "5-9", "10+"]
    r0cb_sample["n_stages_bucket"] = pd.cut(n_stages, bins=[0, 1, 2, 4, 9, np.inf], labels=labels)
    dist = r0cb_sample["n_stages_bucket"].value_counts().sort_index()
    dist_pct = (dist / len(r0cb_sample) * 100).round(2)
    dist_df = pd.DataFrame({"n_stages_bucket": dist.index, "n": dist.values, "pct": dist_pct.values})
    dist_df.to_csv(RAW_DIR / "05_n_stages_distribution.csv", index=False)
    print(dist_df.to_string(index=False))

    # ---------------- Step 2: single-stage subset ----------------
    log_step("Step 2: single-stage (n_stages=1) subset relationship...")
    single = r0cb_sample[n_stages == 1].copy()
    log_step(f"single-stage n={len(single)}")
    single_raw = decile_bin_report(single, "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
                                    "single_stage_raw")
    single_raw.to_csv(RAW_DIR / "05_single_stage_bins.csv", index=False)
    print("=== single-stage (n_stages=1) ===")
    print(single_raw.to_string(index=False))

    # ---------------- Step 3: multi-stage subsets ----------------
    log_step("Step 3: multi-stage subsets...")
    multi_all = r0cb_sample[n_stages >= 2].copy()
    log_step(f"multi-stage (>=2) n={len(multi_all)}")
    multi_raw = decile_bin_report(multi_all, "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
                                   "multi_stage_all_raw")
    multi_raw.to_csv(RAW_DIR / "05_multi_stage_all_bins.csv", index=False)
    print("=== multi-stage (n_stages>=2), all ===")
    print(multi_raw.to_string(index=False))

    for label, mask in [
        ("n_stages=2", n_stages == 2),
        ("n_stages=3-4", (n_stages >= 3) & (n_stages <= 4)),
        ("n_stages>=5", n_stages >= 5),
    ]:
        sub = r0cb_sample[mask].copy()
        log_step(f"{label}: n={len(sub)}")
        if len(sub) < 200:
            log_step(f"  skipped (too small for reliable decile bins)")
            continue
        b = decile_bin_report(sub, "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours", label)
        b.to_csv(RAW_DIR / f"05_{label.replace('=','').replace('>','gte').replace('-','_')}_bins.csv", index=False)
        print(f"=== {label} ===")
        print(b.to_string(index=False))

    # ---------------- Step 4: regression controlling for n_stages ----------------
    log_step("Step 4: regression with/without n_stages control...")
    r0cb_sample["log_n_stages"] = np.log(r0cb_sample["stage_row_count"].astype(float))

    def fit_with_terms(df, extra_cols):
        Xtr, _ = v9.design_train_valid(df, df, extra_scale_cols=["customers_v2_log1p"])
        for c in extra_cols:
            Xtr[c] = df[c].astype(float)
        y = df["log_duration_B"].astype(float)
        # design_train_valid needs the raw column 'customers_v2_log1p' present under that exact name
        res = sm.OLS(y, Xtr.astype(float)).fit()
        groups_lad = pd.factorize(df["LAD21CD"])[0]
        cov = cov_cluster(res, groups_lad)
        se = np.sqrt(np.maximum(np.diag(cov), 0))
        z = res.params.to_numpy() / se
        p = 2 * stats.norm.sf(np.abs(z))
        return res, se, p

    d = r0cb_sample.copy()
    d["customers_v2_log1p"] = d["log1p_customers_v2"]

    log_step("Fitting WITHOUT n_stages control (baseline, matches established R0c'_B_clean)...")
    res0, se0, p0 = fit_with_terms(d, [])
    terms_of_interest = ["z_gust_0h", "z_gust_0h_sq", "z_log1p_customers_v2", "z_log1p_customers_v2_sq"]
    rows = []
    for t in terms_of_interest:
        idx = list(res0.params.index).index(t)
        rows.append({"spec": "without_n_stages_control", "term": t, "coefficient": res0.params[t], "p_value": p0[idx]})

    log_step("Fitting WITH log(n_stages) control...")
    res1, se1, p1 = fit_with_terms(d, ["log_n_stages"])
    for t in terms_of_interest + ["log_n_stages"]:
        idx = list(res1.params.index).index(t)
        rows.append({"spec": "with_n_stages_control", "term": t, "coefficient": res1.params[t], "p_value": p1[idx]})

    reg_df = pd.DataFrame(rows)
    reg_df.to_csv(RAW_DIR / "05_regression_with_without_n_stages.csv", index=False)
    print(reg_df.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
