# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Three-segment (plateau) gust response for the exposure margin:
   f(g) = b0 * min(g, k1) + b1 * min(max(g - k1, 0), k2 - k1)
   -- free slope below k1, ramp between k1 and k2, CONSTANT beyond k2 (customers
   affected cannot fall with gust). Replaces the separate linear gust term.
Physically motivated (customers affected cannot decrease with gust). Compared with the
unconstrained two-hinge model by likelihood ratio (1 df: net slope beyond k2 = 0),
knots re-profiled for the ramp, district bootstrap, two-way SEs, nested CV.
Also fitted on the weather-attributed sample. Updates knots.json with a 'ramp' entry."""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from analysis_new.model_selection import design
from analysis_new.runtime import ROOT, DATA; OUT = ROOT / "results" / "model_selection"
KN = json.load(open(OUT / "knots.json"))

MARGIN = sys.argv[1] if len(sys.argv) > 1 else "E0"
CUST = MARGIN == "R0c"
def base(tr, va):
    Xtr, Xva = design(tr, va, "M5_+year_month_FE", CUST)
    drop = ["z_gust_sq", "z_gust_0h"] + (["z_gust_pressure"] if CUST else [])
    return Xtr.drop(columns=drop), Xva.drop(columns=drop)
def ramp(g, k1, k2): return np.column_stack([np.minimum(g, k1), np.minimum(np.maximum(g - k1, 0.0), k2 - k1)])
def add_temp(X, dd, tr):
    mu, sd = tr.temperature_0h.mean(), tr.temperature_0h.std(ddof=1); X["z_temperature_sq"] = ((dd.temperature_0h - mu) / sd) ** 2; return X

from analysis_new.basis_solver import Solver, profile
from analysis_new.runtime import PLATEAU_BOOTSTRAPS

res_all = {}
for label, wonly in [("all", False), ("weather", True)]:
    d = pd.read_csv(DATA / ("combined_R0c_final.csv" if CUST else "combined_E0_final.csv"))
    if wonly: d = d[d.cause_group_official == "weather_natural"]
    if CUST:
        d = d[d.customers_v2_event_excl_reinterruptions > 0].copy(); d["customers_v2_log1p"] = np.log1p(d.customers_v2_event_excl_reinterruptions.astype(float))
    d = d.reset_index(drop=True); y = d[("log_duration_B_full_span_hours" if CUST else "log1p_customers_v2")].astype(float).to_numpy(); g = d.gust_0h.to_numpy(); n = len(d)
    X0, _ = base(d, d); X0 = add_temp(X0, d, d); X0n = X0.to_numpy(); p0 = X0n.shape[1]
    k1r = np.arange(8, 21, 1.0); k2r = np.arange(18, 35, 1.0)
    (k1, k2, sse_r), tab = profile(X0n, g, y, k1r, k2r)
    # quadratic (with temperature^2) for reference
    Xq, _ = design(d, d, "M5_+year_month_FE", CUST); Xq = add_temp(Xq, d, d); sse_q = float(np.sum(sm.OLS(y, Xq).fit().resid ** 2))
    if CUST: Xq = Xq.drop(columns=["z_gust_pressure"]); sse_q = float(np.sum(sm.OLS(y, Xq).fit().resid ** 2))
    S = Solver(X0n, y, g)
    def sse_hinge(a, b):
        return S.at_knots(a, b, tail=True)
    bh = min(((a, b, sse_hinge(a, b)) for a in k1r for b in k2r if b - a >= 4), key=lambda t: t[2])
    bic = lambda s, p: n * np.log(s / n) + p * np.log(n)
    lr = n * np.log(sse_r / bh[2]); p_lr = float(stats.chi2.sf(lr, 1))
    lr_q = n * np.log(sse_q / bh[2])  # 2-hinge (3 slopes + 2 knots) vs quadratic (2 params): not nested; report BIC instead
    tab["lr"] = n * np.log(tab.sse / sse_r); reg = tab[tab.lr <= stats.chi2.ppf(0.95, 2)]
    # bootstrap knots for the ramp
    rng = np.random.default_rng(20260908); lad = pd.factorize(d.LAD21CD)[0]; L = lad.max() + 1; idx = [np.flatnonzero(lad == l) for l in range(L)]
    boot = []
    for b_ in range(PLATEAU_BOOTSTRAPS):
        ii = np.concatenate([idx[l] for l in rng.integers(0, L, L)])
        (a, b, _), _ = profile(X0n[ii], g[ii], y[ii], np.arange(max(8, k1 - 5), k1 + 6, 1.0), np.arange(max(18, k2 - 7), min(34, k2 + 7) + 1, 1.0)); boot.append((a, b))
    boot = np.array(boot)
    pd.DataFrame(boot, columns=["k1", "k2"]).to_csv(OUT / f"{MARGIN}_{label}_plateau_bootstrap.csv", index=False)
    tab.to_csv(OUT / f"{MARGIN}_{label}_plateau_profile.csv", index=False)
    # full fit with two-way SEs
    X = X0.copy(); R2 = ramp(g, k1, k2); X["gust_low"] = R2[:, 0]; X["gust_ramp"] = R2[:, 1]; r = sm.OLS(y, X).fit()
    gl = lad; gd = pd.factorize(pd.to_datetime(d.incident_date_utc).dt.date.astype(str))[0]; cov, _, _ = cov_cluster_2groups(r, gl, gd)
    se = np.sqrt(np.diag(cov)); i = list(X.columns).index("gust_ramp"); i0 = list(X.columns).index("gust_low")
    # nested CV: ramp vs two-hinge vs quadratic, knots reselected in-fold
    rng2 = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng2.shuffle(lads); fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy()
    pr, ph, pq = np.zeros(n), np.zeros(n), np.zeros(n)
    for k in range(5):
        m = fold == k; Xtr, Xva = base(d[~m], d[m]); Xtr = add_temp(Xtr, d[~m], d[~m]); Xva = add_temp(Xva, d[m], d[~m]); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        (a, b, _), _ = profile(Xtr.to_numpy(), g[~m], y[~m], k1r, k2r)
        bb = sm.OLS(y[~m], np.column_stack([Xtr.to_numpy(), ramp(g[~m], a, b)])).fit().params; pr[m] = np.column_stack([Xva.to_numpy(), ramp(g[m], a, b)]) @ bb
        Sf = Solver(Xtr.to_numpy(), y[~m], g[~m])
        def sh(a_, b_): return Sf.at_knots(a_, b_, tail=True)
        a2, b2, _ = min(((a_, b_, sh(a_, b_)) for a_ in k1r for b_ in k2r if b_ - a_ >= 4), key=lambda t: t[2])
        Hh = lambda gg: np.column_stack([np.minimum(gg, a2), np.minimum(np.maximum(gg - a2, 0), b2 - a2), np.maximum(gg - b2, 0)])
        bb = sm.OLS(y[~m], np.column_stack([Xtr.to_numpy(), Hh(g[~m])])).fit().params; ph[m] = np.column_stack([Xva.to_numpy(), Hh(g[m])]) @ bb
        Xq_tr, Xq_va = design(d[~m], d[m], "M5_+year_month_FE", CUST); Xq_tr = add_temp(Xq_tr, d[~m], d[~m]); Xq_va = add_temp(Xq_va, d[m], d[~m]).reindex(columns=Xq_tr.columns, fill_value=0.0)
        pq[m] = Xq_va.to_numpy() @ sm.OLS(y[~m], Xq_tr).fit().params.to_numpy()
    rm = lambda p: float(np.sqrt(np.mean((y - p) ** 2)))
    res_all[label] = dict(n=int(n), ramp=dict(k1=float(k1), k2=float(k2), slope=float(r.params["gust_ramp"]), se_twoway=float(se[i]), p=float(2 * stats.t.sf(abs(r.params["gust_ramp"] / se[i]), L - 1)),
        slope_below_k1=float(r.params["gust_low"]), se_below_k1=float(se[i0]),
        bic=bic(sse_r, p0 + 2), profile_region_95=dict(k1=[float(reg.k1.min()), float(reg.k1.max())], k2=[float(reg.k2.min()), float(reg.k2.max())]),
        bootstrap=dict(B=PLATEAU_BOOTSTRAPS, k1_pct=[float(v) for v in np.percentile(boot[:, 0], [2.5, 50, 97.5])], k2_pct=[float(v) for v in np.percentile(boot[:, 1], [2.5, 50, 97.5])]), adj_r2=float(r.rsquared_adj)),
        two_hinge=dict(k1=float(bh[0]), k2=float(bh[1]), bic=bic(bh[2], p0 + 3)), lr_hinge_vs_ramp=dict(stat=float(lr), p_1df=p_lr),
        nested_cv=dict(ramp=rm(pr), two_hinge=rm(ph), quadratic=rm(pq)))
    print(f"[{label} n={n}] ramp knots ({k1:.0f},{k2:.0f}) slope={r.params['gust_ramp']:.4f} (2way SE {se[i]:.4f})  BIC ramp={bic(sse_r,p0+2):.1f} vs 2-hinge({bh[0]:.0f},{bh[1]:.0f})={bic(bh[2],p0+3):.1f}  LR={lr:.2f} p={p_lr:.3f}")
    print(f"   region k1{res_all[label]['ramp']['profile_region_95']['k1']} k2{res_all[label]['ramp']['profile_region_95']['k2']}  boot k1 {np.percentile(boot[:,0],[2.5,50,97.5])} k2 {np.percentile(boot[:,1],[2.5,50,97.5])}")
    print(f"   nested CV: ramp {rm(pr):.4f}  two-hinge {rm(ph):.4f}  quadratic {rm(pq):.4f}")
(OUT / f"ramp_model{'' if MARGIN=='E0' else '_R0c'}.json").write_text(json.dumps(res_all, indent=2))
if MARGIN == "E0":
    KN["E0"]["ramp"] = res_all["all"]["ramp"]; KN["E0"]["ramp"]["lr_two_hinge_vs_ramp"] = res_all["all"]["lr_hinge_vs_ramp"]
    (OUT / "knots.json").write_text(json.dumps(KN, indent=2))
