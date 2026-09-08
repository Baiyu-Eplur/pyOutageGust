"""Command #40 Test 1: add a cubic gust term (z_gust_0h^3) to E0 and R0c on
command #21's final combined sample, checking 5-fold GroupKFold(date)
stability (not just a single full-sample fit), and comparing pooled
out-of-fold R^2 with vs without the cubic term."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.model_selection import GroupKFold
from statsmodels.stats.sandwich_covariance import cov_cluster

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import v9  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[step40-1] {msg}", flush=True)


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


def make_folds(df, n_splits=5):
    dates = df["incident_date_utc"].dt.floor("D")
    gkf = GroupKFold(n_splits=n_splits)
    fold_of = pd.Series(index=df.index, dtype=int)
    for i, (_, va_idx) in enumerate(gkf.split(df, groups=dates)):
        fold_of.iloc[va_idx] = i
    # verify 0 dates crossing folds
    date_to_folds = dates.groupby(dates).apply(lambda s: fold_of.loc[s.index].nunique())
    n_crossing = int((date_to_folds > 1).sum())
    return fold_of, n_crossing


def add_cubic(X):
    X = X.copy()
    X["z_gust_0h_cubed"] = X["z_gust_0h"] ** 3
    return X


def fit_with_cluster(y, X, lad_series):
    res = sm.OLS(y, X.astype(float)).fit()
    groups = pd.factorize(lad_series)[0]
    cov = cov_cluster(res, groups)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    return res, pd.Series(se, index=res.params.index), pd.Series(p, index=res.params.index)


def run_model(df, target_col, use_customers, label):
    log_step(f"=== {label} (n={len(df)}) ===")
    extra = ["customers_v2_log1p"] if use_customers else None
    d = df.copy()
    if use_customers:
        d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))

    fold_of, n_crossing = make_folds(d)
    log_step(f"{label}: dates crossing folds = {n_crossing} (expect 0)")

    terms_lin_quad = ["z_gust_0h", "z_gust_0h_sq"]
    fold_rows_nocubic = []
    fold_rows_cubic = []
    oof_pred_nocubic = pd.Series(index=d.index, dtype=float)
    oof_pred_cubic = pd.Series(index=d.index, dtype=float)

    for fold in range(5):
        va_mask = fold_of == fold
        tr_mask = ~va_mask
        tr, va = d.loc[tr_mask], d.loc[va_mask]
        Xtr, Xva = v9.design_train_valid(tr, va, extra_scale_cols=extra)
        ytr = tr[target_col].astype(float)
        yva = va[target_col].astype(float)

        # ---- without cubic ----
        res_no, se_no, p_no = fit_with_cluster(ytr, Xtr, tr["LAD21CD"])
        oof_pred_nocubic.loc[va.index] = res_no.predict(Xva.astype(float)).values
        for term in terms_lin_quad:
            fold_rows_nocubic.append({
                "fold": fold, "term": term, "coefficient": res_no.params[term],
                "std_error": se_no[term], "p_value": p_no[term],
            })

        # ---- with cubic ----
        Xtr_c, Xva_c = add_cubic(Xtr), add_cubic(Xva)
        res_c, se_c, p_c = fit_with_cluster(ytr, Xtr_c, tr["LAD21CD"])
        oof_pred_cubic.loc[va.index] = res_c.predict(Xva_c.astype(float)).values
        for term in terms_lin_quad + ["z_gust_0h_cubed"]:
            fold_rows_cubic.append({
                "fold": fold, "term": term, "coefficient": res_c.params[term],
                "std_error": se_c[term], "p_value": p_c[term],
            })

    df_no = pd.DataFrame(fold_rows_nocubic)
    df_c = pd.DataFrame(fold_rows_cubic)

    y_all = d[target_col].astype(float)
    ss_tot = float(((y_all - y_all.mean()) ** 2).sum())
    r2_oos_no = 1 - float(((y_all - oof_pred_nocubic) ** 2).sum()) / ss_tot
    r2_oos_c = 1 - float(((y_all - oof_pred_cubic) ** 2).sum()) / ss_tot
    log_step(f"{label}: OOS R^2 without cubic = {r2_oos_no:.6f}, with cubic = {r2_oos_c:.6f}, "
              f"delta = {r2_oos_c - r2_oos_no:.6f}")

    def stability(df_terms, term):
        sub = df_terms[df_terms["term"] == term]
        same_sign = (np.sign(sub["coefficient"]) == np.sign(sub["coefficient"].iloc[0])).all()
        n_same_sign = int((np.sign(sub["coefficient"]) == np.sign(sub["coefficient"]).mode()[0]).sum())
        n_sig = int((sub["p_value"] < 0.05).sum())
        mean_coef = float(sub["coefficient"].mean())
        cv = float(sub["coefficient"].std() / abs(mean_coef) * 100) if mean_coef != 0 else np.nan
        return {"mean_coef": mean_coef, "cv_pct": cv, "n_same_sign": n_same_sign, "n_sig": n_sig,
                "fold_detail": sub[["fold", "coefficient", "std_error", "p_value"]].to_dict("records")}

    summary = {
        "label": label, "n": int(len(d)), "n_dates_crossing_folds": n_crossing,
        "r2_oos_5fold_no_cubic": r2_oos_no, "r2_oos_5fold_with_cubic": r2_oos_c,
        "r2_oos_delta": r2_oos_c - r2_oos_no,
        "no_cubic": {t: stability(df_no, t) for t in terms_lin_quad},
        "with_cubic": {t: stability(df_c, t) for t in terms_lin_quad + ["z_gust_0h_cubed"]},
    }

    # also a single full-sample fit (all data, no CV split) for a headline number
    Xfull, _ = v9.design_train_valid(d, d, extra_scale_cols=extra)
    Xfull_c = add_cubic(Xfull)
    yfull = d[target_col].astype(float)
    res_full_no, se_full_no, p_full_no = fit_with_cluster(yfull, Xfull, d["LAD21CD"])
    res_full_c, se_full_c, p_full_c = fit_with_cluster(yfull, Xfull_c, d["LAD21CD"])
    summary["full_sample_no_cubic"] = {
        t: {"coef": float(res_full_no.params[t]), "se": float(se_full_no[t]), "p": float(p_full_no[t])}
        for t in terms_lin_quad
    }
    summary["full_sample_with_cubic"] = {
        t: {"coef": float(res_full_c.params[t]), "se": float(se_full_c[t]), "p": float(p_full_c[t])}
        for t in terms_lin_quad + ["z_gust_0h_cubed"]
    }

    for t in terms_lin_quad:
        log_step(f"{label} full-sample {t}: no-cubic coef={res_full_no.params[t]:.4f} p={p_full_no[t]:.2e} "
                  f"-> with-cubic coef={res_full_c.params[t]:.4f} p={p_full_c[t]:.2e}")
    log_step(f"{label} full-sample z_gust_0h_cubed: coef={res_full_c.params['z_gust_0h_cubed']:.4f} "
              f"se={se_full_c['z_gust_0h_cubed']:.4f} p={p_full_c['z_gust_0h_cubed']:.2e}")

    return summary


def main():
    _, combined_e0, combined_r0cb, _ = build_combined_samples()
    combined_e0 = combined_e0.copy()
    combined_r0cb = combined_r0cb.copy()
    combined_e0["incident_date_utc"] = pd.to_datetime(combined_e0["incident_date_utc"], errors="coerce")
    combined_r0cb["incident_date_utc"] = pd.to_datetime(combined_r0cb["incident_date_utc"], errors="coerce")

    e0_summary = run_model(combined_e0, "log1p_customers_v2", False, "E0 (exposure)")
    r0c_summary = run_model(combined_r0cb, "log_duration_B_full_span_hours", True, "R0c (recovery)")

    (RAW_DIR / "step40_1_cubic_E0.json").write_text(js(e0_summary), encoding="utf-8")
    (RAW_DIR / "step40_1_cubic_R0c.json").write_text(js(r0c_summary), encoding="utf-8")
    log_step("Saved raw/step40_1_cubic_E0.json, raw/step40_1_cubic_R0c.json")


if __name__ == "__main__":
    main()
