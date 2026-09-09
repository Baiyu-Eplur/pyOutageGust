"""3c independent verification: LAD fixed-effects "trap".

Claim: adding 110 LAD dummies to M5 wins every in-sample criterion but is the
worst model under LAD-grouped (spatial) cross-validation, because held-out
districts get no intercept. Reproduced independently on pyOutageGust's own
combined_E0_final.csv / combined_R0c_final.csv.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

SCALE_COLS = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]
SOCIO = ["urban_binary", "log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]


def design(tr, va, cust, lad_fe):
    scale = SCALE_COLS + (["customers_v2_log1p"] if cust else [])
    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in scale:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        Xtr[f"z_{c}"] = (tr[c] - mu) / sd
        Xva[f"z_{c}"] = (va[c] - mu) / sd
    Xtr["z_gust_sq"] = Xtr["z_gust_0h"] ** 2
    Xva["z_gust_sq"] = Xva["z_gust_0h"] ** 2
    Xtr["z_gust_pressure"] = Xtr["z_gust_0h"] * Xtr["z_pressure_msl_0h"]
    Xva["z_gust_pressure"] = Xva["z_gust_0h"] * Xva["z_pressure_msl_0h"]
    if cust:
        Xtr["z_cust_sq"] = Xtr["z_customers_v2_log1p"] ** 2
        Xva["z_cust_sq"] = Xva["z_customers_v2_log1p"] ** 2
    for c in SOCIO:
        Xtr[c] = tr[c].astype(float)
        Xva[c] = va[c].astype(float)
    for f in ["incident_year", "incident_month"]:
        levels = sorted(tr[f].dropna().unique())
        for lv in levels[1:]:
            Xtr[f"{f}[{lv}]"] = (tr[f] == lv).astype(float)
            Xva[f"{f}[{lv}]"] = (va[f] == lv).astype(float)
    if lad_fe:
        levels = sorted(tr["LAD21CD"].unique())
        for lv in levels[1:]:
            Xtr[f"LAD[{lv}]"] = (tr["LAD21CD"] == lv).astype(float)
            Xva[f"LAD[{lv}]"] = (va["LAD21CD"] == lv).astype(float)
    return Xtr, Xva


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def lad_cv(d, y, cust, lad_fe, seed=20260908):
    rng = np.random.default_rng(seed)
    lads = d["LAD21CD"].unique()
    rng.shuffle(lads)
    fold = d["LAD21CD"].map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy()
    pred = np.zeros(len(d))
    for k in range(5):
        m = fold == k
        Xtr, Xva = design(d[~m], d[m], cust, lad_fe)
        Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        b = sm.OLS(y[~m], Xtr).fit().params.to_numpy()
        pred[m] = Xva.to_numpy() @ b
    return rmse(y, pred), pred


def run_margin(name, path, tgt, cust):
    d = pd.read_csv(path)
    if cust:
        d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    y = d[tgt].astype(float).to_numpy()

    out = {}
    for lad_fe, label in [(False, "M5"), (True, "M5_LAD_FE")]:
        X, _ = design(d, d, cust, lad_fe)
        res = sm.OLS(y, X).fit()
        cv_rmse, pred = lad_cv(d, y, cust, lad_fe)
        cal_slope = float(np.polyfit(pred, y, 1)[0])
        out[label] = {
            "k_params": int(res.df_model + 1),
            "aic": float(res.aic), "bic": float(res.bic),
            "adj_r2": float(res.rsquared_adj),
            "rmse_in_sample": rmse(res.fittedvalues.to_numpy(), y),
            "cv_lad_rmse": cv_rmse,
            "cv_lad_calibration_slope": cal_slope,
        }
        print(f"[{name}] {label}: k={out[label]['k_params']} AIC={out[label]['aic']:.1f} BIC={out[label]['bic']:.1f} "
              f"adjR2={out[label]['adj_r2']:.4f} | RMSE_in={out[label]['rmse_in_sample']:.4f} "
              f"CV_LAD={cv_rmse:.4f} cal_slope={cal_slope:.3f}")
    return out


def main():
    results = {}
    results["E0"] = run_margin("E0", r"D:\Pyprogramme\pyOutageGust\review_package\data\combined_E0_final.csv",
                                "log1p_customers_v2", False)
    results["R0c"] = run_margin("R0c", r"D:\Pyprogramme\pyOutageGust\review_package\data\combined_R0c_final.csv",
                                 "log_duration_B_full_span_hours", True)
    out_path = r"D:\Pyprogramme\pyOutageGust\results\advisor_review_20260908\verification\3c_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
