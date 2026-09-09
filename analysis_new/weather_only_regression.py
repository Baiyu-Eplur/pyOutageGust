# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Regressions on weather-attributed incidents only (cause_group_official == 'weather_natural').

For each margin fits, on the weather subsample:
  * the paper's M5 quadratic specification;
  * a piecewise-linear gust specification with knots RE-ESTIMATED on the subsample
    (profile likelihood over 1 m/s grids; one and two knots; LR test);
  * the final specification from final_models.py (temperature^2 etc.; R0c drops
    zero-customer placeholder rows and gust x pressure).
LAD- and LAD x date-clustered SEs, LAD-grouped CV, and a gust-response figure with
binned partial residuals, full-sample curve overlaid for comparison.
Outputs: results/weather_only/{E0,R0c}_weather_{paper,hinge,final}_twoway.csv,
         weather_only_summary.json, fig13_weather_only.png
"""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from analysis_new.model_selection import design
from analysis_new.knot_estimation import KnotSolver, KGRID, hinge_cols

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "weather_only"; OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "results" / "figures"
KN_FULL = json.load(open(ROOT / "results/model_selection/knots.json"))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
BINS = [0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 26, 30, 45]; MIDS = [(a + b) / 2 for a, b in zip(BINS[:-1], BINS[1:])]


def base(tr, va, cust):
    Xtr, Xva = design(tr, va, "M5_+year_month_FE", cust)
    return Xtr.drop(columns=["z_gust_sq"]), Xva.drop(columns=["z_gust_sq"])


def build(tr, va, name, cust, spec, knots):
    if spec == "paper":
        return design(tr, va, "M5_+year_month_FE", cust)
    Xtr, Xva = base(tr, va, cust)
    mu_t, sd_t = tr.temperature_0h.mean(), tr.temperature_0h.std(ddof=1)
    mu_p, sd_p = tr.precipitation_24h_sum.mean(), tr.precipitation_24h_sum.std(ddof=1)
    for X, dd in ((Xtr, tr), (Xva, va)):
        if len(knots) == 2:
            X.drop(columns=["z_gust_0h"], inplace=True); X["gust_low"] = np.minimum(dd.gust_0h, knots[0]); X["gust_ramp"] = np.minimum(np.maximum(dd.gust_0h - knots[0], 0.0), knots[1] - knots[0])
        else:
            for k in knots: X[f"gust_hinge_{k:g}"] = np.maximum(dd.gust_0h - k, 0.0)
        if spec == "final":
            X["z_temperature_sq"] = ((dd.temperature_0h - mu_t) / sd_t) ** 2
            if name == "R0c":
                X.drop(columns=["z_gust_pressure"], inplace=True)
                X["z_gust_precip"] = X["z_gust_0h"] * ((dd.precipitation_24h_sum - mu_p) / sd_p)
    return Xtr, Xva


def table(res, cov, G):
    se = np.sqrt(np.maximum(np.diag(cov), 0)); t = res.params.to_numpy() / se
    return pd.DataFrame({"term": res.params.index, "coef": res.params.values, "se": se, "p_t_G1": 2 * stats.t.sf(np.abs(t), G - 1)})


def cv_lad(d, y, mk):
    rng = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng.shuffle(lads)
    fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy(); pred = np.zeros(len(d))
    for k in range(5):
        m = fold == k; Xtr, Xva = mk(d[~m], d[m]); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        pred[m] = Xva.to_numpy() @ sm.OLS(y[~m], Xtr).fit().params.to_numpy()
    return float(np.sqrt(np.mean((y - pred) ** 2)))


summary = {}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for ax, (name, f, tgt, cust, ylab) in zip(axes, [("E0", "combined_E0_final.csv", "log1p_customers_v2", False, "log(1+customers)"),
                                                ("R0c", "combined_R0c_final.csv", "log_duration_B_full_span_hours", True, "log(duration, h)")]):
    d0 = pd.read_csv(DATA / f)
    d = d0[d0.cause_group_official == "weather_natural"].copy()
    if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    n_w = len(d)
    if name == "R0c": d = d[d.customers_v2_event_excl_reinterruptions > 0]
    d = d.reset_index(drop=True); y = d[tgt].astype(float).to_numpy(); n = len(d)
    g_lad = pd.factorize(d.LAD21CD)[0]; g_date = pd.factorize(pd.to_datetime(d.incident_date_utc).dt.date.astype(str))[0]; G = g_lad.max() + 1
    # ---- knots re-estimated on the subsample
    X0, _ = base(d, d, cust); S = KnotSolver(X0.to_numpy(), d.gust_0h.to_numpy(), y, KGRID)
    k1r = np.arange(8, 31, 1.0)
    one = min([((k,), S.sse((k,))) for k in k1r], key=lambda t: t[1])
    two = min([((a, b), S.sse((a, b))) for a in np.arange(8, 21, 1.0) for b in np.arange(18, 35, 1.0) if b - a >= 4], key=lambda t: t[1])
    p0 = X0.shape[1]; bic = lambda s, p: n * np.log(s / n) + p * np.log(n)
    lr = n * np.log(one[1] / two[1]); p_lr = float(stats.chi2.sf(lr, 2))
    knots = list(two[0]) if p_lr < 0.01 else list(one[0])
    if len(knots) == 2 and name == "E0":  # ramp knots re-profiled on the subsample
        RJ = json.load(open(OUT / ".." / "model_selection" / "ramp_model.json"))["weather"]["ramp"]; knots = [RJ["k1"], RJ["k2"]]
    Xq, _ = design(d, d, "M5_+year_month_FE", cust); sse_q = float(np.sum(sm.OLS(y, Xq).fit().resid ** 2))
    knot_info = dict(one_knot=float(one[0][0]), one_bic=bic(one[1], p0 + 1), two_knot=[float(v) for v in two[0]], two_bic=bic(two[1], p0 + 2),
                     quad_bic=bic(sse_q, p0 + 1), lr_two_vs_one=float(lr), p=p_lr, selected=knots, full_sample_knots=KN_FULL[name]["selected"])
    # ---- fits
    fits = {}
    for spec in ["paper", "hinge", "final"]:
        mk = lambda tr, va, spec=spec: build(tr, va, name, cust, spec, knots)
        X, _ = mk(d, d); res = sm.OLS(y, X).fit()
        cov_l = cov_cluster(res, g_lad); cov_2, _, _ = cov_cluster_2groups(res, g_lad, g_date)
        t2 = table(res, cov_2, G); t2["se_lad"] = np.sqrt(np.maximum(np.diag(cov_l), 0))
        t2.to_csv(OUT / f"{name}_weather_{spec}_twoway.csv", index=False)
        gt = t2[t2.term.str.contains("gust|temperature|cust")].set_index("term")
        fits[spec] = dict(adj_r2=float(res.rsquared_adj), bic=float(res.bic), cv_lad=cv_lad(d, y, mk),
                          gust_terms={t: dict(coef=float(r.coef), se_twoway=float(r.se), p=float(r.p_t_G1)) for t, r in gt.iterrows()})
        if spec != "paper": fits[spec]["_res"] = (res, cov_2, X)
        print(f"[{name} weather-only n={n}] {spec:6s} adjR2={res.rsquared_adj:.4f} BIC={res.bic:.1f} CV-LAD={fits[spec]['cv_lad']:.4f}")
        print(gt[["coef", "se", "p_t_G1"]].round(4).to_string())
    # ---- figure: partial residuals + fitted curves (weather-only) + full-sample final curve
    Xnog = base(d, d, cust)[0].drop(columns=["z_gust_0h", "z_gust_pressure"]); resid = sm.OLS(y, Xnog).fit().resid
    e = pd.DataFrame({"g": pd.cut(d.gust_0h, BINS), "r": resid}).groupby("g", observed=False).r.agg(["mean", "sem"])
    ax.errorbar(MIDS, e["mean"], yerr=1.96 * e["sem"], fmt="o", color="k", ms=4, capsize=2, label="weather-only binned partial residual", zorder=5)
    gg = np.linspace(0.5, 40, 300); mu, sd = d.gust_0h.mean(), d.gust_0h.std(ddof=1); z = (gg - mu) / sd
    rq = sm.OLS(y, Xq).fit(); cq = rq.params["z_gust_0h"] * z + rq.params["z_gust_sq"] * z ** 2
    res_h, cov_h, Xh = fits["hinge"]["_res"]
    if len(knots) == 2: cols = ["gust_low", "gust_ramp"]; Bm = np.column_stack([np.minimum(gg, knots[0]), np.minimum(np.maximum(gg - knots[0], 0), knots[1] - knots[0])])
    else: cols = ["z_gust_0h"] + [f"gust_hinge_{k:g}" for k in knots]; Bm = np.column_stack([z] + [np.maximum(gg - k, 0) for k in knots])
    ch = Bm @ res_h.params[cols].to_numpy()
    idx = [list(res_h.params.index).index(c) for c in cols]; se_h = np.sqrt(np.einsum("ij,jk,ik->i", Bm, cov_h[np.ix_(idx, idx)], Bm))
    # full-sample final curve, on the same partial-residual scale
    dfull = d0.copy()
    if cust: dfull["customers_v2_log1p"] = np.log1p(dfull.customers_v2_event_excl_reinterruptions.astype(float))
    if name == "R0c": dfull = dfull[dfull.customers_v2_event_excl_reinterruptions > 0]
    yf = dfull[tgt].astype(float).to_numpy(); kf = KN_FULL[name]["selected"] if name == "E0" else []
    Xf, _ = build(dfull, dfull, name, cust, "final" if name == "E0" else "paper", kf); rf = sm.OLS(yf, Xf).fit()
    muf, sdf = dfull.gust_0h.mean(), dfull.gust_0h.std(ddof=1); zf = (gg - muf) / sdf
    cf = (rf.params["gust_low"] * np.minimum(gg, kf[0]) + rf.params["gust_ramp"] * np.minimum(np.maximum(gg - kf[0], 0), kf[1] - kf[0])) if kf else (rf.params["z_gust_0h"] * zf + rf.params["z_gust_sq"] * zf ** 2)
    def centre(c):  # align curves with the binned residuals (weighted)
        w = np.interp(MIDS, gg, c); ok = np.isfinite(e["mean"].to_numpy()); return c - np.average((w - e["mean"].to_numpy())[ok], weights=1 / e["sem"].to_numpy()[ok] ** 2)
    ax.fill_between(gg, centre(ch) - 1.96 * se_h, centre(ch) + 1.96 * se_h, color="#27ae60", alpha=0.18)
    ax.plot(gg, centre(ch), color="#27ae60", lw=2, label=f"weather-only {'ramp' if len(knots)==2 else 'hinge'} ({'/'.join(f'{k:g}' for k in knots)} m/s)")
    ax.plot(gg, centre(cq), color="#c0392b", ls="--", lw=1.5, label="weather-only quadratic (paper spec)")
    ax.plot(gg, centre(cf), color="0.4", ls=":", lw=1.8, label="full-sample final model")
    for k in knots: ax.axvline(k, color="#27ae60", lw=0.7, ls=":")
    ax.axhline(0, color="0.7", lw=0.6); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel(f"effect on {ylab}")
    ax.set_title(f"{name}, weather-attributed incidents only (n={n:,})"); ax.legend(fontsize=7, loc="upper left")
    for s_ in fits.values(): s_.pop("_res", None)
    summary[name] = dict(n_weather=int(n_w), n_used=int(n), share_of_full=float(n_w / len(d0)), G_lad=int(G), knots=knot_info, fits=fits)
fig.tight_layout(); fig.savefig(FIG / "fig13_weather_only.png", dpi=170); plt.close(fig)
(OUT / "weather_only_summary.json").write_text(json.dumps(summary, indent=2))
for name in summary: print(name, "knots:", summary[name]["knots"])


# ---------------------------------------------------------------- Figure 14: predicted vs observed (out-of-fold), weather-only
def cv_pred(d, y, mk):
    rng = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng.shuffle(lads)
    fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy(); pred = np.zeros(len(d))
    for k in range(5):
        m = fold == k; Xtr, Xva = mk(d[~m], d[m]); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        pred[m] = Xva.to_numpy() @ sm.OLS(y[~m], Xtr).fit().params.to_numpy()
    return pred


fig, axes = plt.subplots(2, 3, figsize=(12, 7.2))
pvo_rows = []
for i, (name, f, tgt, cust, ylab) in enumerate([("E0", "combined_E0_final.csv", "log1p_customers_v2", False, "log(1+customers)"),
                                                 ("R0c", "combined_R0c_final.csv", "log_duration_B_full_span_hours", True, "log(duration, h)")]):
    d0 = pd.read_csv(DATA / f); d = d0[d0.cause_group_official == "weather_natural"].copy()
    if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    if name == "R0c": d = d[d.customers_v2_event_excl_reinterruptions > 0]
    d = d.reset_index(drop=True); y = d[tgt].astype(float).to_numpy()
    knots = [float(k) for k in summary[name]["knots"]["selected"]]
    for j, (spec, lab) in enumerate([("paper", "paper quadratic"), ("hinge", f"{'ramp' if len(knots)==2 else 'hinge'} ({'/'.join(f'{k:g}' for k in knots)} m/s)"), ("final", "final specification")]):
        yh = cv_pred(d, y, lambda tr, va, spec=spec: build(tr, va, name, cust, spec, knots))
        r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2); rm = float(np.sqrt(np.mean((y - yh) ** 2)))
        slope = np.polyfit(yh, y, 1)[0]; pvo_rows.append(dict(model=name, spec=lab, rmse_cv=rm, r2_cv=r2, cal_slope=slope, n=len(y)))
        ax = axes[i, j]
        ax.hexbin(yh, y, gridsize=40, bins="log", cmap="Blues", mincnt=1)
        lo, hi = np.percentile(y, [0.2, 99.8]); ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
        q = pd.qcut(yh, 10, duplicates="drop"); bm = pd.DataFrame({"q": q, "yh": yh, "y": y}).groupby("q", observed=True).mean()
        ax.plot(bm.yh, bm.y, "o-", color="#c0392b", ms=3, lw=1)
        ax.text(0.03, 0.95, f"RMSE {rm:.3f}\nR² {r2:.3f}\ncal. slope {slope:.2f}", transform=ax.transAxes, va="top", fontsize=7)
        ax.set_xlim(np.percentile(yh, [0.5, 99.5])); ax.set_ylim(lo, hi)
        ax.set_title(f"{name} weather-only (n={len(y):,}): {lab}", fontsize=8.5); ax.set_xlabel("predicted (LAD-grouped CV, out-of-fold)"); ax.set_ylabel(f"observed {ylab}")
fig.suptitle("Weather-attributed incidents only — predicted vs observed, out-of-fold. Hexbin: log density; red: mean observed by predicted decile; dashed: 45°", fontsize=9)
fig.tight_layout(); fig.savefig(FIG / "fig14_weather_only_pred_vs_obs.png", dpi=150); plt.close(fig)
pd.DataFrame(pvo_rows).to_csv(OUT / "weather_only_pred_vs_obs.csv", index=False)
print(pd.DataFrame(pvo_rows).round(4).to_string(index=False))
