"""3b independent verification -- the key test: does a free natural cubic
spline with MORE degrees of freedom than our own Appendix H (df=4) actually
reproduce the "floor - rise - plateau" shape the advisor's binned partial
residuals show, or does it keep looking like a smooth, quadratic-like dip?

Runs entirely on pyOutageGust's own combined_E0_final.csv (SHA256-identical
to the advisor package's copy). Design: same M5 covariate set as our own
run_main_regression.py / the advisor's model_selection.py (weather block,
socio block, year/month FE), gust represented by a patsy natural cubic
spline cr(gust, df=k) with NO other gust term, fit once in-sample (for
shape) and once under the same LAD-grouped 5-fold CV used throughout this
review (for an honest RMSE comparison against the quadratic and against
each other).
"""
import json
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm

SCALE_COLS = ["precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]
SOCIO = ["urban_binary", "log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]


def other_covariates(tr, va):
    """Non-gust part of the M5 design: weather (minus gust), socio, year/month FE."""
    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in SCALE_COLS:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        Xtr[f"z_{c}"] = (tr[c] - mu) / sd
        Xva[f"z_{c}"] = (va[c] - mu) / sd
    for c in SOCIO:
        Xtr[c] = tr[c].astype(float)
        Xva[c] = va[c].astype(float)
    for f in ["incident_year", "incident_month"]:
        levels = sorted(tr[f].dropna().unique())
        for lv in levels[1:]:
            Xtr[f"{f}[{lv}]"] = (tr[f] == lv).astype(float)
            Xva[f"{f}[{lv}]"] = (va[f] == lv).astype(float)
    return Xtr, Xva


def spline_basis(train_gust, target_gust, df):
    tr_dm = patsy.dmatrix(f"cr(gust, df={df}) - 1", {"gust": train_gust.values}, return_type="dataframe")
    tr_dm.index = train_gust.index
    out_dm = patsy.build_design_matrices([tr_dm.design_info], {"gust": target_gust.values})[0]
    out = pd.DataFrame(np.asarray(out_dm), columns=[f"spl{i}" for i in range(tr_dm.shape[1])], index=target_gust.index)
    tr_dm.columns = out.columns
    return tr_dm, out


def quad_basis(train_gust, target_gust):
    mu, sd = train_gust.mean(), train_gust.std(ddof=1)
    zt = (train_gust - mu) / sd
    zv = (target_gust - mu) / sd
    tr = pd.DataFrame({"z": zt, "z2": zt ** 2}, index=train_gust.index)
    va = pd.DataFrame({"z": zv, "z2": zv ** 2}, index=target_gust.index)
    return tr, va


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def lad_cv_rmse(d, y, gust_col, basis_fn, seed=20260908):
    rng = np.random.default_rng(seed)
    lads = d["LAD21CD"].unique()
    rng.shuffle(lads)
    fold = d["LAD21CD"].map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy()
    pred = np.zeros(len(d))
    for k in range(5):
        m = fold == k
        Xo_tr, Xo_va = other_covariates(d[~m], d[m])
        Xg_tr, Xg_va = basis_fn(d.loc[~m, gust_col], d.loc[m, gust_col])
        Xtr = pd.concat([Xo_tr, Xg_tr], axis=1)
        Xva = pd.concat([Xo_va, Xg_va], axis=1).reindex(columns=Xtr.columns, fill_value=0.0)
        b = sm.OLS(y[~m], Xtr).fit().params.to_numpy()
        pred[m] = Xva.to_numpy() @ b
    return rmse(y, pred)


def main():
    d = pd.read_csv(r"D:\Pyprogramme\pyOutageGust\review_package\data\combined_E0_final.csv")
    y = d["log1p_customers_v2"].astype(float).to_numpy()
    gust = d["gust_0h"]
    n = len(d)

    # ---- in-sample shape: fit each candidate on the FULL sample, extract the
    # fitted gust-effect curve on a grid, after partialling out the other covariates
    # (so the curve is comparable to a "binned partial residual" plot).
    Xo, _ = other_covariates(d, d)
    Xo_pinv = np.linalg.pinv(Xo.to_numpy())

    def partial_curve(basis_tr_full, grid_basis):
        """Residualize y and the gust basis against Xo (FWL), fit, then predict
        on `grid_basis` (already expressed in the same TRAIN design_info)."""
        Xg = basis_tr_full.to_numpy()
        Hy = Xo.to_numpy() @ (Xo_pinv @ y)
        y_resid = y - Hy
        Hg = Xo.to_numpy() @ (Xo_pinv @ Xg)
        Xg_resid = Xg - Hg
        beta, *_ = np.linalg.lstsq(Xg_resid, y_resid, rcond=None)
        return grid_basis.to_numpy() @ beta

    grid = pd.Series(np.linspace(0.5, 40, 300), name="gust")

    results = {"n": int(n), "curves": {"grid_gust": grid.tolist()}, "cv_rmse": {}, "turning_points": {}}

    # quadratic baseline (for reference, matches the paper / our own review_package spec)
    tr_q, grid_q = quad_basis(gust, grid)
    curve_q = partial_curve(tr_q, grid_q)
    results["curves"]["quadratic"] = curve_q.tolist()
    results["turning_points"]["quadratic"] = float(grid[np.argmin(curve_q)])

    for df in (4, 6, 8, 10):
        tr_s, grid_s = spline_basis(gust, grid, df)
        curve_s = partial_curve(tr_s, grid_s)
        results["curves"][f"spline_df{df}"] = curve_s.tolist()
        argmin_g = float(grid[np.argmin(curve_s)])
        results["turning_points"][f"spline_df{df}"] = argmin_g
        # crude "does it plateau above 26?" check: slope of a linear fit on [26,40] band
        hi = grid >= 26
        slope_hi = float(np.polyfit(grid[hi], curve_s[hi], 1)[0])
        # crude "floor" check: is the curve roughly flat (near its max value) below 8 m/s?
        lo = grid <= 8
        slope_lo = float(np.polyfit(grid[lo], curve_s[lo], 1)[0])
        results.setdefault("shape_diagnostics", {})[f"spline_df{df}"] = {
            "argmin_gust_ms": argmin_g,
            "slope_above_26ms": slope_hi,
            "slope_below_8ms": slope_lo,
            "value_at_min": float(curve_s.min()),
            "value_at_0.5": float(curve_s[0]),
            "value_at_40": float(curve_s[-1]),
        }
        print(f"df={df:2d}: argmin={argmin_g:.2f} m/s   slope[26-40]={slope_hi:+.4f}/m/s   slope[0-8]={slope_lo:+.4f}/m/s")

    # ---- LAD-grouped CV RMSE, quadratic vs each spline df (honest out-of-fold comparison)
    print("\n=== LAD-grouped 5-fold CV RMSE ===")
    rm_q = lad_cv_rmse(d, y, "gust_0h", quad_basis)
    results["cv_rmse"]["quadratic"] = rm_q
    print(f"quadratic: {rm_q:.4f}")
    for df in (4, 6, 8, 10):
        rm = lad_cv_rmse(d, y, "gust_0h", lambda tr, va, df=df: spline_basis(tr, va, df))
        results["cv_rmse"][f"spline_df{df}"] = rm
        print(f"spline df={df}: {rm:.4f}")

    out_path = r"D:\Pyprogramme\pyOutageGust\results\advisor_review_20260908\verification\3b_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
