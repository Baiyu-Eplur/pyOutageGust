"""Command #31: rebuild the clean, decontaminated final combined sample WITHOUT
restricting to weather_natural+technical_asset (all six Cause Code groups kept),
reusing command #16/#19's exact date-decontamination logic, to redo the
"all six groups vs main-spec" R0c comparison on a fully clean, consistent basis.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

LOCKED_START = pd.Timestamp("2023-09-30")
LOCKED_END = pd.Timestamp("2024-03-31")


def log_step(msg):
    print(f"[v31] {msg}", flush=True)


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


def build_six_group_dev():
    log_step("Building SIX-GROUP clean development sample (date < 2023-09-30)...")
    matched, _ = v9.step0_build_sample()
    matched["_date_check"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    n_before = len(matched)
    matched = matched.loc[matched["_date_check"] < LOCKED_START].copy()
    matched = matched.drop(columns=["_date_check"])
    log_step(f"Weather-matched sample: {n_before} -> {len(matched)} after locked-window exclusion.")

    matched, _ = v9.step1_lad_gapfill(matched)
    matched["incident_date_utc"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    sample = v9.prep_predictors(matched)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"SIX-GROUP clean dev complete-predictor sample: n={len(sample)} (NO Cause Code filter).")
    return sample


def build_six_group_holdout():
    log_step("Building SIX-GROUP holdout sample ([2023-09-30, 2024-03-31])...")
    matched, _ = v9.step0_build_sample()
    matched["_date_check"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    matched = matched.loc[
        (matched["_date_check"] >= LOCKED_START) & (matched["_date_check"] <= LOCKED_END)
    ].copy()
    matched = matched.drop(columns=["_date_check"])
    log_step(f"Weather-matched sample in locked window: n={len(matched)}.")

    matched, _ = v9.step1_lad_gapfill(matched)
    matched["incident_date_utc"] = pd.to_datetime(matched["incident_date_utc"], errors="coerce")
    sample = v9.prep_predictors(matched)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"SIX-GROUP holdout complete-predictor sample: n={len(sample)} (NO Cause Code filter).")
    return sample


def main():
    dev = build_six_group_dev()
    holdout = build_six_group_holdout()

    # ---------------- Step 1: verification + comparison to WT main-spec ----------------
    dev_dates = pd.to_datetime(dev["incident_date_utc"])
    holdout_dates = pd.to_datetime(holdout["incident_date_utc"])
    date_overlap = set(dev_dates.dt.date) & set(holdout_dates.dt.date)
    id_overlap = set(dev["Incident Reference"]) & set(holdout["Incident Reference"])

    combined = pd.concat([dev, holdout], ignore_index=True)
    combined["incident_date_utc"] = pd.to_datetime(combined["incident_date_utc"], errors="coerce")

    verification = {
        "dev_n": int(len(dev)), "holdout_n": int(len(holdout)), "combined_n": int(len(combined)),
        "sum_check_passed": bool(len(combined) == len(dev) + len(holdout)),
        "date_overlap_count": len(date_overlap), "id_overlap_count": len(id_overlap),
        "combined_unique_ids": int(combined["Incident Reference"].nunique()),
        "wt_main_spec_r0c_n_command21": 59834,
    }
    log_step(f"Six-group combined n={len(combined)}, date overlap={len(date_overlap)}, id overlap={len(id_overlap)}")

    # R0c sample: duration_B non-missing & >0, customers_v2 non-missing, p99 cap recomputed on combined six-group sample
    r0b_base = combined.loc[
        combined["duration_B_full_span_hours"].notna() & (combined["duration_B_full_span_hours"] > 0)
    ].copy()
    p99 = r0b_base["duration_B_full_span_hours"].quantile(0.99)
    r0b_capped = r0b_base.loc[r0b_base["duration_B_full_span_hours"] <= p99].copy()
    r0cb_sample = r0b_capped.loc[r0b_capped["customers_v2_event_excl_reinterruptions"].notna()].copy()
    r0cb_sample["log_duration_B_full_span_hours"] = np.log(r0cb_sample["duration_B_full_span_hours"].astype(float))
    r0cb_sample["log1p_customers_v2"] = np.log1p(r0cb_sample["customers_v2_event_excl_reinterruptions"].astype(float))

    verification["six_group_r0c_n"] = int(len(r0cb_sample))
    verification["six_group_p99_cap_hours"] = float(p99)
    verification["ratio_six_group_to_wt_main_spec"] = len(r0cb_sample) / 59834

    (RAW_DIR / "step36_verification.json").write_text(js(verification), encoding="utf-8")
    print(json.dumps(verification, indent=2, ensure_ascii=False))

    # ---------------- Step 2: fresh 5-fold GroupKFold + R0c fit ----------------
    log_step("Building fresh 5-fold GroupKFold (by date) on the six-group R0c sample...")
    gkf = GroupKFold(n_splits=5)
    r0cb_sample["cv_fold_v3"] = -1
    groups = r0cb_sample["incident_date_utc"].dt.date.astype(str)
    X_dummy = np.zeros(len(r0cb_sample))
    for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
        r0cb_sample.iloc[valid_idx, r0cb_sample.columns.get_loc("cv_fold_v3")] = fold_idx
    date_fold_counts = r0cb_sample.groupby(groups)["cv_fold_v3"].nunique()
    n_crossing = int((date_fold_counts > 1).sum())
    log_step(f"Fold sizes: {r0cb_sample['cv_fold_v3'].value_counts().sort_index().to_dict()}, "
              f"dates crossing folds: {n_crossing} (expect 0)")
    assert n_crossing == 0

    rows = []
    for fold in range(5):
        va_mask = r0cb_sample["cv_fold_v3"].eq(fold)
        tr_mask = r0cb_sample["cv_fold_v3"].ne(fold)
        tr, va = r0cb_sample.loc[tr_mask], r0cb_sample.loc[va_mask]
        Xtr, Xva = v9.design_train_valid(tr, va, extra_scale_cols=["log1p_customers_v2"])
        ytr = tr["log_duration_B_full_span_hours"].astype(float)
        res = sm.OLS(ytr, Xtr.astype(float)).fit()
        groups_lad = pd.factorize(tr["LAD21CD"])[0]
        cov = cov_cluster(res, groups_lad)
        se = np.sqrt(np.maximum(np.diag(cov), 0))
        z = res.params.to_numpy() / se
        p = 2 * stats.norm.sf(np.abs(z))
        for term in ["z_gust_0h", "z_gust_0h_sq"]:
            idx = list(res.params.index).index(term)
            rows.append({"model": "R0c_six_group_clean", "fold": fold, "term": term,
                         "coefficient": res.params[term], "std_error": se[idx], "p_value": p[idx],
                         "n_train": len(tr), "n_valid": len(va)})

    fold_df = pd.DataFrame(rows)
    fold_df.to_csv(RAW_DIR / "step37_six_group_R0c_fold_coefs.csv", index=False)
    print(fold_df.to_string(index=False))

    stab_rows = []
    for term, g in fold_df.groupby("term"):
        n = len(g)
        n_pos, n_neg = (g["coefficient"] > 0).sum(), (g["coefficient"] < 0).sum()
        same = max(n_pos, n_neg)
        n_sig = (g["p_value"] < 0.05).sum()
        mean = g["coefficient"].mean()
        cv = float(g["coefficient"].std(ddof=1) / abs(mean) * 100) if mean != 0 else np.nan
        stab_rows.append({"term": term, "n_folds": n, "same_sign_folds": int(same),
                           "significant_folds": int(n_sig), "mean_coefficient": mean, "coef_cv_pct": cv})
    stab_df = pd.DataFrame(stab_rows)
    stab_df.to_csv(RAW_DIR / "step37_six_group_R0c_stability.csv", index=False)
    print(stab_df.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
