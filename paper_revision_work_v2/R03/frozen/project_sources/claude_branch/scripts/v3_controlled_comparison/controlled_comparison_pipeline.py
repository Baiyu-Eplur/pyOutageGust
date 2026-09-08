"""Command #10: separate the "sample-size effect" from the "variable-redefinition
effect" in command #9's E0'/R0'_A/R0'_B/R0c' findings, using a naive/legacy-style
customers/duration construction on the exact same 121,313-event sample and 5 folds.

Read-only against rebuild_v3_full_stage/ and claude_branch/results/v3_validation/
(re-executes command #9's deterministic Step0-2 to reconstruct the identical sample+
folds, rather than depending on unsaved intermediate state).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
V3_VALIDATION_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation\v3_validation_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\v3_controlled_comparison")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"
TERMS_OF_INTEREST = ["z_gust_0h", "z_gust_0h_sq"]
CUST_TERMS_OF_INTEREST = ["z_log1p_customers_naive", "z_log1p_customers_naive_sq"]

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
    print(f"[v10] {msg}", flush=True)


# ---------------- reconstruct command #9's exact sample + folds ----------------

def reconstruct_v9_sample():
    log_step("Reconstructing command #9's Step0-2 sample + folds (identical code path)...")
    matched, _ = v9.step0_build_sample()
    matched, _ = v9.step1_lad_gapfill(matched)
    sample, s2 = v9.step2_build_folds(matched)
    sample = v9.prep_predictors(sample)
    comp_mask = v9.complete_predictors_mask(sample)
    sample = sample.loc[comp_mask].copy()
    log_step(f"Reconstructed sample: n={len(sample)} (expect 117,298, matching command #9).")
    return sample, s2


# ---------------- Step 1: naive customers/duration (legacy filter.py dedup logic) ----------------

def build_naive_variables(event_ids: pd.Index):
    log_step("Step 1: building customers_naive / duration_naive via legacy filter.py dedup logic...")
    stage = pd.read_csv(
        SRC,
        usecols=[INCIDENT_COL, "Start Date and Time", "Number of Customers Restored", "stage_duration_hours"],
        low_memory=False,
    )
    stage["_sort_time"] = pd.to_datetime(stage["Start Date and Time"], errors="coerce", utc=True)
    stage = stage.sort_values([INCIDENT_COL, "_sort_time"], kind="stable")
    earliest = stage.drop_duplicates(subset=[INCIDENT_COL], keep="first").copy()
    earliest["customers_naive"] = pd.to_numeric(
        earliest["Number of Customers Restored"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    earliest["duration_naive"] = earliest["stage_duration_hours"]
    naive = earliest.set_index(INCIDENT_COL)[["customers_naive", "duration_naive"]]
    naive = naive.reindex(event_ids)
    log_step(f"Naive variables built for {naive.index.isin(event_ids).sum()} / {len(event_ids)} target events "
              f"({naive['customers_naive'].notna().sum()} customers_naive non-null, "
              f"{naive['duration_naive'].notna().sum()} duration_naive non-null).")
    return naive


# ---------------- Step 2: fit E0_naive / R0_naive / R0c_naive ----------------

def main():
    sample, s2 = reconstruct_v9_sample()
    naive = build_naive_variables(sample[INCIDENT_COL].unique())
    sample = sample.set_index(INCIDENT_COL, drop=False).join(naive, how="left").reset_index(drop=True)

    # E0_naive: mirrors E0' construction (customers notna, log1p, no cap)
    e0_sample = sample.loc[sample["customers_naive"].notna()].copy()
    e0_sample["log1p_customers_naive"] = np.log1p(e0_sample["customers_naive"].astype(float))
    e0_naive = v9.run_model(e0_sample, "log1p_customers_naive", "E0_naive_large_sample", TERMS_OF_INTEREST)
    e0_naive.to_csv(RAW_DIR / "E0_naive_fold_coefs.csv", index=False)
    log_step(f"E0_naive done, n={len(e0_sample)}.")

    # R0_naive: mirrors R0'_A construction (duration>0, p99 cap, log)
    r0_sample = sample.loc[sample["duration_naive"].notna() & (sample["duration_naive"] > 0)].copy()
    p99 = r0_sample["duration_naive"].quantile(0.99)
    r0_sample = r0_sample.loc[r0_sample["duration_naive"] <= p99].copy()
    r0_sample["log_duration_naive"] = np.log(r0_sample["duration_naive"].astype(float))
    r0_naive = v9.run_model(r0_sample, "log_duration_naive", "R0_naive_large_sample", TERMS_OF_INTEREST)
    r0_naive.to_csv(RAW_DIR / "R0_naive_fold_coefs.csv", index=False)
    log_step(f"R0_naive done, n={len(r0_sample)} (p99 cap={p99:.2f}h).")

    # R0c_naive: control for customers_naive (mirrors R0c'_A construction)
    r0c_sample = r0_sample.loc[r0_sample["customers_naive"].notna()].copy()

    # NOTE: v9.fit_fold_terms(use_customers_covariate=True) hardcodes reading the
    # REAL "customers_v2_event_excl_reinterruptions" column (which still has 69 NaN
    # boundary cases in this sample) rather than any column we hand it, so it cannot
    # be reused as-is for the naive covariate. design_train_valid's special-casing is
    # keyed only on the literal string "customers_v2_log1p" appearing in
    # extra_scale_cols, so we call it directly with a column of that name holding the
    # naive (not real) log1p(customers) values, then run the identical
    # OLS + LAD-cluster-robust-SE fit that fit_fold_terms uses internally.
    def fit_fold_terms_naive(train, valid, target_col, terms_of_interest):
        import statsmodels.api as sm
        from scipy import stats
        from statsmodels.stats.sandwich_covariance import cov_cluster

        tr = train.copy()
        va = valid.copy()
        tr["customers_v2_log1p"] = np.log1p(tr["customers_naive"].astype(float))
        va["customers_v2_log1p"] = np.log1p(va["customers_naive"].astype(float))
        Xtr, Xva = v9.design_train_valid(tr, va, extra_scale_cols=["customers_v2_log1p"])
        ytr = tr[target_col].astype(float)
        res = sm.OLS(ytr, Xtr).fit()
        groups_lad = pd.factorize(tr["LAD21CD"])[0]
        cov = cov_cluster(res, groups_lad)
        se = np.sqrt(np.maximum(np.diag(cov), 0))
        z = res.params.to_numpy() / se
        p = 2 * stats.norm.sf(np.abs(z))
        rows = []
        for term, coef, s, pv in zip(res.params.index, res.params, se, p):
            if term not in terms_of_interest:
                continue
            rows.append({"term": term, "coefficient": coef, "std_error": s,
                         "ci_low": coef - 1.96 * s, "ci_high": coef + 1.96 * s, "p_value": pv})
        return rows, len(tr), len(va)

    all_rows = []
    for fold in range(5):
        va_mask = r0c_sample["cv_fold_v3"].eq(fold)
        tr_mask = r0c_sample["cv_fold_v3"].ne(fold) & r0c_sample["cv_fold_v3"].ge(0)
        rows, n_train, n_valid = fit_fold_terms_naive(
            r0c_sample.loc[tr_mask], r0c_sample.loc[va_mask],
            "log_duration_naive", TERMS_OF_INTEREST + ["z_log1p_customers_v2", "z_log1p_customers_v2_sq"],
        )
        for r in rows:
            r.update({"model": "R0c_naive_large_sample", "fold": fold, "n_obs_in_fold_train": n_train,
                      "n_obs_in_fold_valid": n_valid, "inference": "LAD_cluster"})
            all_rows.append(r)
    r0c_naive = pd.DataFrame(all_rows)
    # rename customers_v2 terms -> customers_naive terms for clarity in output
    r0c_naive["term"] = r0c_naive["term"].replace({
        "z_log1p_customers_v2": "z_log1p_customers_naive",
        "z_log1p_customers_v2_sq": "z_log1p_customers_naive_sq",
    })
    r0c_naive.to_csv(RAW_DIR / "R0c_naive_fold_coefs.csv", index=False)
    log_step(f"R0c_naive done, n={len(r0c_sample)}.")

    step_summary = {
        "e0_naive_n": int(len(e0_sample)),
        "r0_naive_n": int(len(r0_sample)),
        "r0_naive_p99_cap_hours": float(p99),
        "r0c_naive_n": int(len(r0c_sample)),
    }
    (RAW_DIR / "step2_naive_samples.json").write_text(js(step_summary), encoding="utf-8")

    all_fold_coefs = pd.concat([e0_naive, r0_naive, r0c_naive], ignore_index=True)
    all_fold_coefs.to_csv(RAW_DIR / "all_naive_fold_coefs.csv", index=False)
    stab = v9.stability_summary(all_fold_coefs)
    stab.to_csv(RAW_DIR / "stability_summary_naive.csv", index=False)
    print(stab.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
