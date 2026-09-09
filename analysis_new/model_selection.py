# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Specification search for the E0 (exposure) and R0c (recovery) models.

Fits a ladder of nested specifications plus alternative gust functional forms,
and compares them on in-sample criteria (AIC, BIC, adj. R2) and out-of-sample
RMSE under three cross-validation schemes:
  - random 5-fold (cv_fold_v3 as supplied; rows without a fold are excluded)
  - LAD-grouped 5-fold (whole LADs held out -> spatial generalisation)
  - leave-one-year-out (temporal generalisation)
All specifications use the same in-fold standardisation as the original
design_train_valid (train mean/sd applied to the validation fold).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "model_selection"
OUT.mkdir(parents=True, exist_ok=True)
SCALE = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]
SOCIO = ["urban_binary", "log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]


# ---------------------------------------------------------------- design ----
def design(train, valid, spec, customers):
    """Return X_train, X_valid for a named specification, train-scaled."""
    tr, va = train.copy(), valid.copy()
    scale = SCALE + (["customers_v2_log1p"] if customers else [])
    for c in scale:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        tr["z_" + c], va["z_" + c] = (tr[c] - mu) / sd, (va[c] - mu) / sd
    # gust transforms evaluated on raw gust, scaled with train stats
    for x in (tr, va):
        x["z_gust_sq"] = x["z_gust_0h"] ** 2
        x["z_gust_cu"] = x["z_gust_0h"] ** 3
        x["z_gust_pressure"] = x["z_gust_0h"] * x["z_pressure_msl_0h"]
        x["z_gust_precip"] = x["z_gust_0h"] * x["z_precipitation_24h_sum"]
        x["z_temp_sq"] = x["z_temperature_0h"] ** 2
        x["z_precip_sq"] = x["z_precipitation_24h_sum"] ** 2
        x["log_gust"] = np.log1p(x["gust_0h"])
        if customers:
            x["z_cust_sq"] = x["z_customers_v2_log1p"] ** 2
    for k in ("hinge",):  # hinge at the E0 turning point ~10.8 m/s
        for x in (tr, va):
            x["gust_hinge"] = np.maximum(x["gust_0h"] - 10.8, 0.0)
    # thresholds for a step/bin form (train-based quantiles keeps it honest)
    q = tr["gust_0h"].quantile([0.5, 0.75, 0.9, 0.97]).to_numpy()
    for x in (tr, va):
        for i, t in enumerate(q):
            x[f"gust_ge_q{i}"] = (x["gust_0h"] >= t).astype(float)

    weather_lin = ["z_gust_0h", "z_precipitation_24h_sum", "z_temperature_0h", "z_pressure_msl_0h"]
    cust = ["z_customers_v2_log1p", "z_cust_sq"] if customers else []
    S = {
        "M1_weather_linear":       weather_lin,
        "M2_+gust_sq":             weather_lin + ["z_gust_sq"],
        "M3_+gust_x_pressure":     weather_lin + ["z_gust_sq", "z_gust_pressure"],
        "M4_+socio":               weather_lin + ["z_gust_sq", "z_gust_pressure"] + SOCIO,
        "M5_+year_month_FE":       weather_lin + ["z_gust_sq", "z_gust_pressure"] + SOCIO + ["FE"],
        "A1_gust_cubic":           weather_lin + ["z_gust_sq", "z_gust_cu", "z_gust_pressure"] + SOCIO + ["FE"],
        "A2_log_gust":             ["log_gust", "z_precipitation_24h_sum", "z_temperature_0h", "z_pressure_msl_0h", "z_gust_pressure"] + SOCIO + ["FE"],
        "A3_hinge_10.8":           weather_lin + ["gust_hinge", "z_gust_pressure"] + SOCIO + ["FE"],
        "A4_gust_bins":            ["z_precipitation_24h_sum", "z_temperature_0h", "z_pressure_msl_0h", "z_gust_pressure"] + [f"gust_ge_q{i}" for i in range(4)] + SOCIO + ["FE"],
        "A5_full_quad_weather":    weather_lin + ["z_gust_sq", "z_temp_sq", "z_precip_sq", "z_gust_pressure", "z_gust_precip"] + SOCIO + ["FE"],
        "A6_M5_+LAD_FE":           weather_lin + ["z_gust_sq", "z_gust_pressure"] + SOCIO + ["FE", "LADFE"],
        "A7_M5_no_socio":          weather_lin + ["z_gust_sq", "z_gust_pressure"] + ["FE"],
    }
    cols = S[spec]
    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in cols:
        if c == "FE":
            for f in ("incident_year", "incident_month"):
                lv = sorted(tr[f].dropna().unique())
                for l in lv[1:]:
                    Xtr[f"{f}[{l}]"] = (tr[f] == l).astype(float)
                    Xva[f"{f}[{l}]"] = (va[f] == l).astype(float)
        elif c == "LADFE":
            lv = sorted(tr["LAD21CD"].unique())
            for l in lv[1:]:
                Xtr[f"LAD[{l}]"] = (tr["LAD21CD"] == l).astype(float)
                Xva[f"LAD[{l}]"] = (va["LAD21CD"] == l).astype(float)
        else:
            Xtr[c], Xva[c] = tr[c].astype(float), va[c].astype(float)
    for c in cust:
        Xtr[c], Xva[c] = tr[c].astype(float), va[c].astype(float)
    return Xtr, Xva


SPECS = ["M1_weather_linear", "M2_+gust_sq", "M3_+gust_x_pressure", "M4_+socio", "M5_+year_month_FE",
         "A1_gust_cubic", "A2_log_gust", "A3_hinge_10.8", "A4_gust_bins", "A5_full_quad_weather",
         "A6_M5_+LAD_FE", "A7_M5_no_socio"]


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def run_margin(name, df, target, customers):
    d = df.copy()
    if customers:
        d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    y = d[target].astype(float)
    groups_lad = pd.factorize(d["LAD21CD"])[0]
    rng = np.random.default_rng(20260908)
    lads = d["LAD21CD"].unique(); rng.shuffle(lads)
    lad_fold = dict(zip(lads, np.arange(len(lads)) % 5))
    d["lad_fold"] = d["LAD21CD"].map(lad_fold)
    years = sorted(d["incident_year"].unique())
    rows, coefs = [], {}
    tss = float(((y - y.mean()) ** 2).sum())
    for spec in SPECS:
        Xf, _ = design(d, d, spec, customers)
        res = sm.OLS(y, Xf).fit()
        cov = cov_cluster(res, groups_lad)
        se = np.sqrt(np.diag(cov)); z = res.params.to_numpy() / se
        coefs[spec] = pd.DataFrame({"term": res.params.index, "coef": res.params.values,
                                    "se_lad": se, "p_lad": 2 * stats.norm.sf(np.abs(z))})
        # cross-validation
        cv = {}
        for label, foldcol, folds in [("cv_random", "cv_fold_v3", [0, 1, 2, 3, 4]),
                                      ("cv_lad", "lad_fold", [0, 1, 2, 3, 4]),
                                      ("cv_year", "incident_year", years)]:
            preds, obs = [], []
            for k in folds:
                m = d[foldcol] == k
                tr_idx = d[foldcol].notna() & ~m if label == "cv_random" else ~m
                Xtr, Xva = design(d[tr_idx], d[m], spec, customers)
                Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
                b = sm.OLS(y[tr_idx], Xtr).fit().params
                preds.append(Xva.to_numpy() @ b.to_numpy()); obs.append(y[m].to_numpy())
            cv[label] = rmse(np.concatenate(preds), np.concatenate(obs))
        rows.append({"model": name, "spec": spec, "k": int(res.df_model + 1), "aic": res.aic, "bic": res.bic,
                     "r2": res.rsquared, "adj_r2": res.rsquared_adj, "rmse_in": rmse(res.fittedvalues, y), **cv})
        print(f"[{name}] {spec:24s} k={int(res.df_model+1):4d} AIC={res.aic:12.1f} BIC={res.bic:12.1f} "
              f"adjR2={res.rsquared_adj:.4f} cv_rand={cv['cv_random']:.4f} cv_lad={cv['cv_lad']:.4f} cv_year={cv['cv_year']:.4f}", flush=True)
    tab = pd.DataFrame(rows)
    best = tab.loc[tab["bic"].idxmin(), "bic"]
    tab["dAIC"] = tab["aic"] - tab["aic"].min(); tab["dBIC"] = tab["bic"] - tab["bic"].min()
    tab.to_csv(OUT / f"{name}_model_comparison.csv", index=False)
    with pd.ExcelWriter(OUT / f"{name}_coefficients.xlsx") as xw:
        for s, c in coefs.items():
            c.to_excel(xw, sheet_name=s[:31], index=False)
    return tab, coefs


def main():
    e0 = pd.read_csv(DATA / "combined_E0_final.csv")
    r0 = pd.read_csv(DATA / "combined_R0c_final.csv")
    t_e0, c_e0 = run_margin("E0", e0, "log1p_customers_v2", False)
    t_r0, c_r0 = run_margin("R0c", r0, "log_duration_B_full_span_hours", True)
    pd.concat([t_e0, t_r0]).to_csv(OUT / "all_model_comparison.csv", index=False)


if __name__ == "__main__":
    main()
