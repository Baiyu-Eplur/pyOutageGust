"""Command #51, Question 2: verify the "development sample" row in Figure 10.
Confirms the current construction (inverse-variance pooling across 5
GroupKFold TRAINING-fold fits, each on an ~80%-overlapping subset of the dev
sample) and quantifies the option (a) [single full-sample fit] and option (b)
[day-block bootstrap on the full dev sample] alternatives for comparison.
Read-only w.r.t. all historical files; uses the C01+C02-C08 corrected dev-only
E0'/R0c'_B samples built via clean_sample_builder.build_clean_wt_samples().
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import _patch_v9  # noqa: E402

RAW_C0208 = result_path('c02_c08_repair_20260905/raw')
RAW_DIR = result_path('appendix_h_legacy_followup_20260906/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)

Z95 = 1.959963984540054
N_BOOTSTRAP = 500
RNG_SEED = 20260826
TERM = "z_gust_0h_sq"


def log_step(msg):
    print(f"[Q2] {msg}", flush=True)


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


def pooled_estimate(fold_csv, term):
    df = pd.read_csv(read_input(fold_csv))
    sub = df[df["term"] == term]
    w = 1.0 / (sub["std_error"].astype(float) ** 2)
    pooled = float((w * sub["coefficient"].astype(float)).sum() / w.sum())
    se = float(np.sqrt(1.0 / w.sum()))
    return pooled, se, sub[["fold", "coefficient", "std_error"]].to_dict("records")


def fold_overlap_check(sample_with_folds: pd.DataFrame):
    """Quantify how much the 5 GroupKFold TRAINING sets overlap with each other."""
    fold_idx = {f: set(sample_with_folds.index[sample_with_folds["cv_fold_v3"] == f]) for f in range(5)}
    n_total = len(sample_with_folds)
    train_sets = {f: set(sample_with_folds.index) - fold_idx[f] for f in range(5)}
    overlaps = []
    for i in range(5):
        for j in range(i + 1, 5):
            inter = len(train_sets[i] & train_sets[j])
            union = len(train_sets[i] | train_sets[j])
            overlaps.append({"fold_i": i, "fold_j": j, "n_shared": inter,
                              "pct_of_train_i_shared": inter / len(train_sets[i]) * 100,
                              "jaccard": inter / union * 100})
    return overlaps, n_total


def day_block_bootstrap_se(v9, df: pd.DataFrame, target_col: str, use_customers: bool, term: str):
    df = df.copy()
    df["incident_date_utc"] = pd.to_datetime(df["incident_date_utc"], errors="coerce")
    dates = df["incident_date_utc"].dt.date.astype(str)
    unique_dates = dates.unique()
    n_dates = len(unique_dates)
    by_date = {d: idx.to_numpy() for d, idx in df.groupby(dates).groups.items()}
    rng = np.random.default_rng(RNG_SEED)

    boot_coefs = []
    for b in range(N_BOOTSTRAP):
        sampled_dates = rng.choice(unique_dates, size=n_dates, replace=True)
        idx = np.concatenate([by_date[d] for d in sampled_dates])
        boot_df = df.loc[idx].copy()
        try:
            extra = None
            if use_customers:
                boot_df["customers_v2_log1p"] = np.log1p(
                    boot_df["customers_v2_event_excl_reinterruptions"].astype(float))
                extra = ["customers_v2_log1p"]
            Xb, _ = v9.design_train_valid(boot_df, boot_df, extra_scale_cols=extra)
            yb = boot_df[target_col].astype(float)
            resb = sm.OLS(yb, Xb.astype(float)).fit()
            boot_coefs.append(float(resb.params[term]))
        except Exception:
            boot_coefs.append(np.nan)
        if (b + 1) % 100 == 0:
            log_step(f"    bootstrap {b + 1}/{N_BOOTSTRAP}")
    arr = np.array(boot_coefs)
    valid = arr[~np.isnan(arr)]
    return valid


def main():
    v9, clean_sample_builder, build_holdout_sample = _patch_v9()

    # -------- option (a): genuine single full-sample fit on the dev-only corrected sample --------
    V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
    spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
    v11 = importlib.util.module_from_spec(spec11)
    spec11.loader.exec_module(v11)

    log_step("Building C01-corrected DEV-ONLY E0'/R0c'_B samples (clean_sample_builder)...")
    sample_wt, e0_sample, r0cb_sample, p99_b = clean_sample_builder.build_clean_wt_samples()
    log_step(f"dev-only E0' n={len(e0_sample)}, R0c'_B n={len(r0cb_sample)}")

    res_e0, cov_e0, _, _, d_e0 = v11.fit_full_sample(e0_sample, "log1p_customers_v2", use_customers_covariate=False)
    res_r0c, cov_r0c, _, _, d_r0c = v11.fit_full_sample(
        r0cb_sample, "log_duration_B_full_span_hours", use_customers_covariate=True)

    optA_e0 = {"coef": float(res_e0.params[TERM]), "se": float(np.sqrt(cov_e0.loc[TERM, TERM])), "n": int(len(d_e0))}
    optA_r0c = {"coef": float(res_r0c.params[TERM]), "se": float(np.sqrt(cov_r0c.loc[TERM, TERM])), "n": int(len(d_r0c))}
    log_step(f"Option (a) E0 single full-sample fit: coef={optA_e0['coef']:.6f}, se={optA_e0['se']:.6f} "
              f"(LAD-clustered), 95% CI=[{optA_e0['coef']-Z95*optA_e0['se']:.6f},"
              f"{optA_e0['coef']+Z95*optA_e0['se']:.6f}]")
    log_step(f"Option (a) R0c single full-sample fit: coef={optA_r0c['coef']:.6f}, se={optA_r0c['se']:.6f} "
              f"(LAD-clustered), 95% CI=[{optA_r0c['coef']-Z95*optA_r0c['se']:.6f},"
              f"{optA_r0c['coef']+Z95*optA_r0c['se']:.6f}]")

    # -------- current construction: inverse-variance pooling of 5 overlapping-training-fold fits --------
    e0_pooled, e0_pooled_se, e0_fold_rows = pooled_estimate(RAW_C0208 / "E0_dev_corrected_fold_coefs.csv", TERM)
    r0c_pooled, r0c_pooled_se, r0c_fold_rows = pooled_estimate(RAW_C0208 / "R0c_dev_corrected_fold_coefs.csv", TERM)
    log_step(f"Current pooled E0: coef={e0_pooled:.6f}, se={e0_pooled_se:.6f}, "
              f"95% CI=[{e0_pooled-Z95*e0_pooled_se:.6f},{e0_pooled+Z95*e0_pooled_se:.6f}]")
    log_step(f"Current pooled R0c: coef={r0c_pooled:.6f}, se={r0c_pooled_se:.6f}, "
              f"95% CI=[{r0c_pooled-Z95*r0c_pooled_se:.6f},{r0c_pooled+Z95*r0c_pooled_se:.6f}]")
    log_step(f"E0 per-fold coefficients/SEs: {e0_fold_rows}")
    log_step(f"R0c per-fold coefficients/SEs: {r0c_fold_rows}")

    # -------- quantify inter-fold TRAINING-set overlap (why independence assumption fails) --------
    # e0_sample already carries cv_fold_v3 from step2_build_folds() inside build_clean_wt_samples()
    if "cv_fold_v3" in e0_sample.columns:
        overlaps_e0, n_e0 = fold_overlap_check(e0_sample.reset_index(drop=True).assign(
            cv_fold_v3=e0_sample["cv_fold_v3"].to_numpy()))
    else:
        overlaps_e0, n_e0 = None, None
    log_step(f"E0' fold training-set overlap (pairwise): {overlaps_e0}")

    # -------- option (b): day-block bootstrap directly on the full dev-only sample --------
    log_step("Option (b): day-block bootstrap (500 reps) on the FULL E0' dev sample...")
    boot_e0 = day_block_bootstrap_se(v9, e0_sample, "log1p_customers_v2", False, TERM)
    log_step(f"Option (b) E0 bootstrap: n_valid={len(boot_e0)}, mean={boot_e0.mean():.6f}, "
              f"std={boot_e0.std(ddof=1):.6f}, 95% percentile CI=[{np.percentile(boot_e0,2.5):.6f},"
              f"{np.percentile(boot_e0,97.5):.6f}]")

    log_step("Option (b): day-block bootstrap (500 reps) on the FULL R0c'_B dev sample...")
    boot_r0c = day_block_bootstrap_se(v9, r0cb_sample, "log_duration_B_full_span_hours", True, TERM)
    log_step(f"Option (b) R0c bootstrap: n_valid={len(boot_r0c)}, mean={boot_r0c.mean():.6f}, "
              f"std={boot_r0c.std(ddof=1):.6f}, 95% percentile CI=[{np.percentile(boot_r0c,2.5):.6f},"
              f"{np.percentile(boot_r0c,97.5):.6f}]")

    pd.DataFrame({"boot_coef": boot_e0}).to_csv(RAW_DIR / "q2_bootstrap_E0_dev_gustsq.csv", index=False)
    pd.DataFrame({"boot_coef": boot_r0c}).to_csv(RAW_DIR / "q2_bootstrap_R0c_dev_gustsq.csv", index=False)

    result = {
        "term": TERM,
        "current_pooled_construction": {
            "E0": {"coef": e0_pooled, "se": e0_pooled_se, "ci95": [e0_pooled - Z95 * e0_pooled_se,
                                                                    e0_pooled + Z95 * e0_pooled_se],
                   "per_fold": e0_fold_rows},
            "R0c": {"coef": r0c_pooled, "se": r0c_pooled_se, "ci95": [r0c_pooled - Z95 * r0c_pooled_se,
                                                                        r0c_pooled + Z95 * r0c_pooled_se],
                    "per_fold": r0c_fold_rows},
        },
        "option_a_single_full_sample_fit": {"E0": optA_e0, "R0c": optA_r0c},
        "option_b_day_block_bootstrap": {
            "E0": {"mean": float(boot_e0.mean()), "std": float(boot_e0.std(ddof=1)),
                   "ci95": [float(np.percentile(boot_e0, 2.5)), float(np.percentile(boot_e0, 97.5))],
                   "n_valid": int(len(boot_e0))},
            "R0c": {"mean": float(boot_r0c.mean()), "std": float(boot_r0c.std(ddof=1)),
                    "ci95": [float(np.percentile(boot_r0c, 2.5)), float(np.percentile(boot_r0c, 97.5))],
                    "n_valid": int(len(boot_r0c))},
        },
        "fold_training_set_overlap_E0": overlaps_e0,
    }
    (RAW_DIR / "q2_result.json").write_text(js(result), encoding="utf-8")
    log_step("Saved q2_result.json")


if __name__ == "__main__":
    main()
