"""Command #17 Step 3: refit R0c'_B_clean replacing the customers_v2 linear+quadratic
terms with decile dummy variables (a fully flexible, non-parametric-in-customers
functional form), holding all other established covariates (gust terms, non-gust
weather, region SES, year/month FE) unchanged, to see whether the inverted-U shape
survives without assuming a quadratic functional form.
"""
from __future__ import annotations

import importlib.util
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
    print(f"[v17-step3] {msg}", flush=True)


def build_design_with_customer_deciles(tr: pd.DataFrame, va: pd.DataFrame, decile_edges):
    """Same design as v9.design_train_valid (gust terms + non-gust weather + region
    SES + year/month FE), but with customers_v2 represented as decile dummies
    (reference = lowest decile) instead of a linear+quadratic term."""
    Xtr, Xva = v9.design_train_valid(tr, va, extra_scale_cols=None)
    tr_decile = pd.cut(tr["customers_v2_event_excl_reinterruptions"], bins=decile_edges, include_lowest=True, duplicates="drop")
    va_decile = pd.cut(va["customers_v2_event_excl_reinterruptions"], bins=decile_edges, include_lowest=True, duplicates="drop")
    categories = tr_decile.cat.categories
    for i, cat in enumerate(categories[1:], start=1):  # skip first = reference
        name = f"customers_decile_{i}"
        Xtr[name] = (tr_decile == cat).astype(float)
        Xva[name] = (va_decile == cat).astype(float)
    return Xtr.astype(float), Xva.astype(float), categories


def main():
    _, _, r0cb_sample, _ = build_clean_wt_samples()
    r0cb_sample = r0cb_sample.copy()
    r0cb_sample["log_duration_B"] = np.log(r0cb_sample["duration_B_full_span_hours"].astype(float))

    # decile edges from the full sample (fixed bin definition reused across the full-sample fit)
    _, edges = pd.qcut(r0cb_sample["customers_v2_event_excl_reinterruptions"], q=10, retbins=True, duplicates="drop")
    log_step(f"Decile edges: {edges}")

    Xtr, _, categories = build_design_with_customer_deciles(r0cb_sample, r0cb_sample, edges)
    y = r0cb_sample["log_duration_B"].astype(float)
    res = sm.OLS(y, Xtr).fit()
    groups_lad = pd.factorize(r0cb_sample["LAD21CD"])[0]
    cov = cov_cluster(res, groups_lad)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))

    rows = []
    for term, coef, s, pv in zip(res.params.index, res.params, se, p):
        if term.startswith("customers_decile_"):
            idx = int(term.split("_")[-1])
            rows.append({
                "decile_index": idx, "decile_range": str(categories[idx]), "term": term,
                "coefficient_vs_reference_decile1": coef, "std_error": s,
                "ci_low": coef - 1.96 * s, "ci_high": coef + 1.96 * s, "p_value": pv,
            })
    decile_df = pd.DataFrame(rows).sort_values("decile_index")
    decile_df.insert(0, "reference_decile", str(categories[0]))
    decile_df.to_csv(RAW_DIR / "03_customer_decile_dummy_coefficients.csv", index=False)
    print("=== customers_v2 decile-dummy coefficients (reference = decile 1, lowest) ===")
    print(f"Reference decile range: {categories[0]}")
    print(decile_df.to_string(index=False))

    # also report gust terms for internal consistency check
    gust_rows = []
    for term in ["z_gust_0h", "z_gust_0h_sq"]:
        idx = list(res.params.index).index(term)
        gust_rows.append({"term": term, "coefficient": res.params[term], "p_value": p[idx]})
    print("\n=== gust terms (should stay similar to R0c'_B_clean's established values) ===")
    print(pd.DataFrame(gust_rows).to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
