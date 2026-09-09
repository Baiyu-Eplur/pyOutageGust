"""3a independent verification: placeholder ratio + coefficient sign flip.

Runs entirely against pyOutageGust's own combined_R0c_final.csv (identical
by SHA256 to the advisor package's copy, confirmed separately), using the
exact same design/fit logic as pyOutageGust/review_package/code/run_main_regression.py
(z-scored covariates, log1p(customers) + its square, LAD-clustered SE),
just run once on the full R0c sample and once after excluding the
zero-customer/placeholder rows.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

SCALE_COLS = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]


def design(d, extra_scale_cols):
    tr = d.copy()
    for c in SCALE_COLS + extra_scale_cols:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        tr["z_" + c] = (tr[c] - mu) / sd
    tr["z_gust_0h_sq"] = tr["z_gust_0h"] ** 2
    tr["z_gust_pressure"] = tr["z_gust_0h"] * tr["z_pressure_msl_0h"]
    tr["z_log1p_customers_v2_sq"] = tr["z_customers_v2_log1p"] ** 2
    cols = ["Intercept", "z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
            "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
            "income_deprivation_rate", "deprivation_gap_pct", "morans_i",
            "z_customers_v2_log1p", "z_log1p_customers_v2_sq"]
    X = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    for c in cols[1:]:
        X[c] = tr[c].astype(float)
    for f in ["incident_year", "incident_month"]:
        levels = sorted(tr[f].dropna().unique())
        for lv in levels[1:]:
            X[f"{f}[{lv}]"] = (tr[f] == lv).astype(float)
    return X.astype(float)


def fit(d, label):
    d = d.copy()
    d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    X = design(d, ["customers_v2_log1p"])
    y = d["log_duration_B_full_span_hours"].astype(float)
    res = sm.OLS(y, X).fit()
    groups = pd.factorize(d["LAD21CD"])[0]
    cov = cov_cluster(res, groups)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    idx = list(res.params.index)
    out = {}
    for term in ["z_customers_v2_log1p", "z_log1p_customers_v2_sq", "z_gust_0h", "z_gust_0h_sq"]:
        i = idx.index(term)
        z = res.params[term] / se[i]
        out[term] = {"coef": float(res.params[term]), "se_lad": float(se[i]), "p": float(2 * stats.norm.sf(abs(z)))}
    print(f"--- {label}: n={len(d)} ---")
    for k, v in out.items():
        print(f"  {k}: coef={v['coef']:.4f}  se={v['se_lad']:.4f}  p={v['p']:.3g}")
    return {"n": int(len(d)), "terms": out, "adj_r2": float(res.rsquared_adj), "bic": float(res.bic)}


def main():
    d = pd.read_csv(r"D:\Pyprogramme\pyOutageGust\review_package\data\combined_R0c_final.csv")

    print("=== Placeholder check ===")
    zero = d["customers_v2_event_excl_reinterruptions"] == 0
    n_zero = int(zero.sum())
    dur_zero = d.loc[zero, "duration_B_full_span_hours"]
    dur_nonzero = d.loc[~zero, "duration_B_full_span_hours"]
    placeholder = {
        "n_total": int(len(d)),
        "n_zero_customer": n_zero,
        "pct_zero_customer_with_1h": float((dur_zero == 1.0).mean()),
        "pct_nonzero_customer_with_1h": float((dur_nonzero == 1.0).mean()),
    }
    print(json.dumps(placeholder, indent=2))

    print("\n=== Coefficient sign-flip check (full sample vs. placeholder-excluded) ===")
    full = fit(d, "FULL sample (incl. zero-customer placeholders)")
    clean = fit(d[~zero].reset_index(drop=True), "CLEANED sample (zero-customer excluded)")

    result = {"placeholder": placeholder, "full_sample_fit": full, "cleaned_sample_fit": clean}
    out_path = r"D:\Pyprogramme\pyOutageGust\results\advisor_review_20260908\verification\3a_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
