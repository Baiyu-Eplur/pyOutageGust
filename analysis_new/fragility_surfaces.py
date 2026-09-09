# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Proper fragility functions for the outage severity margins.

Why the earlier ordinal-logit curves were non-monotone: the sample is
conditional on an incident having occurred, and the mix of causes changes with
gust (7% weather-attributed at calm, 91% above 30 m/s). A fragility function
needs a sample in which the intensity measure is the cause, and a monotone
link. Here:

  * Sample: weather-attributed incidents only (cause_group_official ==
    'weather_natural'), n ~ 9.9k (E0).
  * Single-IM fragility: the standard lognormal form
        P(DS >= k | g) = Phi( (ln g - ln theta_k) / beta )
    fitted by binomial MLE (probit on ln g), one theta_k per damage state,
    common beta (parallel probit, the multinomial/ordinal analogue) and, as a
    check, free beta per state.  Sigma is shared with the seismic literature
    (Baker 2015; Shinozuka et al. 2000).
  * Fragility surfaces: two IMs, gust and 24-h precipitation,
        P(DS >= k | g, p) = Phi( a_k + b1 ln g + b2 ln(1+p) + b3 ln g * ln(1+p) )
    with monotonicity checked numerically over the observed IM domain.
  * The gradient is also evaluated for a gust x MSL-pressure-anomaly surface.
Outputs: fig9_fragility_lognormal.png, fig10_fragility_surfaces.png,
fragility_lognormal.json
"""
import warnings; warnings.filterwarnings("ignore")
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats, optimize
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "model_selection"; FIG = ROOT / "results" / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

SPEC = {"E0": ("combined_E0_final.csv", "customers_v2_event_excl_reinterruptions",
               [5.5, 100.5, 1000.5], [">5", ">100", ">1000"], "customers affected"),
        "R0c": ("combined_R0c_final.csv", "duration_B_full_span_hours",
                [3, 12, 48], [">3 h", ">12 h", ">48 h"], "restoration time")}
BINS = [0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 26, 30, 45]
MIDS = [(a + b) / 2 for a, b in zip(BINS[:-1], BINS[1:])]


OPTIMIZER_DIAGNOSTICS = []

def lognormal_mle(g, exceed_matrix, common_beta=True):
    """Parallel-probit MLE: P(DS>=k|g)=Phi(a_k + b ln g); theta_k=exp(-a_k/b), beta=1/b."""
    lg = np.log(g); K = exceed_matrix.shape[1]
    def nll(par):
        if common_beta:
            a = par[:K]; b = np.full(K, par[K])
        else:
            a = par[:K]; b = par[K:]
        ll = 0.0
        for k in range(K):
            p = np.clip(stats.norm.cdf(a[k] + b[k] * lg), 1e-9, 1 - 1e-9)
            y = exceed_matrix[:, k]
            ll += np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
        return -ll
    x0 = np.r_[np.linspace(0, -2, K), 1.0] if common_beta else np.r_[np.linspace(0, -2, K), np.ones(K)]
    r = optimize.minimize(nll, x0, method="L-BFGS-B")
    OPTIMIZER_DIAGNOSTICS.append(dict(n=len(g), common_beta=common_beta, success=bool(r.success), message=str(r.message), nll=float(r.fun), iterations=int(r.nit)))
    a = r.x[:K]; b = np.full(K, r.x[K]) if common_beta else r.x[K:]
    return dict(a=a, b=b, theta=np.exp(-a / b), beta=1 / b, nll=r.fun, k=len(r.x))


def empirical(g, y):
    e = pd.DataFrame({"g": pd.cut(g, BINS), "y": y}).groupby("g", observed=True).y.agg(["mean", "count"])
    return e["mean"].to_numpy(), 1.96 * np.sqrt(e["mean"] * (1 - e["mean"]) / e["count"]).to_numpy()


summary = {}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
figS, axesS = plt.subplots(2, 3, figsize=(13, 7.5))
for col, (name, (f, sev, thr, labels, what)) in enumerate(SPEC.items()):
    d = pd.read_csv(DATA / f)
    w = d[d.cause_group_official == "weather_natural"].copy()
    g_all, g_w = d.gust_0h.to_numpy(), w.gust_0h.to_numpy()
    E_all = np.column_stack([(d[sev] > t).astype(float) for t in thr])
    E_w = np.column_stack([(w[sev] > t).astype(float) for t in thr])
    fit_w = lognormal_mle(g_w, E_w, True); fit_w_free = lognormal_mle(g_w, E_w, False)
    fit_all = lognormal_mle(g_all, E_all, True)
    lr_beta = 2 * (fit_w["nll"] - fit_w_free["nll"]); p_beta = stats.chi2.sf(lr_beta, len(thr) - 1)
    ax = axes[col]; gg = np.linspace(1, 40, 300); colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(thr)))
    use = fit_w_free if p_beta < 0.01 else fit_w
    for k, (lab, c) in enumerate(zip(labels, colors)):
        m, ci = empirical(g_w, E_w[:, k]); ax.errorbar(MIDS, m, yerr=ci, fmt="o", ms=3, capsize=2, color=c, alpha=0.9)
        m2, _ = empirical(g_all, E_all[:, k]); ax.plot(MIDS, m2, "x", ms=4, color=c, alpha=0.5)
        th, be = use["theta"][k], use["beta"][k]
        txt = f"θ={th:.1f} m/s, β={be:.2f}" if 0.2 < be < 5 and 1 < th < 200 else f"β̂={be:.0f} → no monotone dependence"
        ax.plot(gg, stats.norm.cdf((np.log(gg) - np.log(th)) / be), color=c, lw=1.8, label=f"P({what} {lab}): {txt}")
    ax.set_ylim(0, 1); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel("Exceedance probability")
    ax.set_title(f"{name}: lognormal fragility, weather-attributed incidents (n={len(w):,})\n"
                 f"● weather-attributed  × all incidents (for reference)", fontsize=9)
    ax.legend(fontsize=7, loc="upper left")

    # ------------------------------------------------------------- surfaces
    lg = np.log(w.gust_0h.to_numpy()); lp = np.log1p(w.precipitation_24h_sum.to_numpy())
    pa = (w.pressure_msl_0h - 1013.25).to_numpy() / 10.0  # pressure anomaly in 10 hPa
    surf = {}
    for k, lab in enumerate(labels):
        X = sm.add_constant(np.column_stack([lg, lp, lg * lp]))
        m = sm.GLM(E_w[:, k], X, family=sm.families.Binomial(sm.families.links.Probit())).fit()
        a, b1, b2, b3 = m.params
        G, P = np.meshgrid(np.linspace(2, 38, 80), np.linspace(0, 30, 80))
        Z = stats.norm.cdf(a + b1 * np.log(G) + b2 * np.log1p(P) + b3 * np.log(G) * np.log1p(P))
        dZdg = b1 + b3 * np.log1p(P); dZdp = b2 + b3 * np.log(G)   # signs of partial derivatives of the linear index
        mono = dict(gust_min_slope=float(dZdg.min()), precip_min_slope=float(dZdp.min()),
                    frac_domain_monotone_gust=float((dZdg >= 0).mean()), frac_domain_monotone_precip=float((dZdp >= 0).mean()))
        # pressure surface (gust x pressure anomaly), no interaction
        X2 = sm.add_constant(np.column_stack([lg, pa]))
        m2 = sm.GLM(E_w[:, k], X2, family=sm.families.Binomial(sm.families.links.Probit())).fit()
        surf[lab] = dict(gust_precip=dict(params=[float(v) for v in m.params], se=[float(v) for v in m.bse], **mono),
                         gust_pressure=dict(params=[float(v) for v in m2.params], se=[float(v) for v in m2.bse]))
        ax2 = axesS[col, k]
        cs = ax2.contourf(G, P, Z, levels=np.linspace(0, 1, 11), cmap="magma"); plt.colorbar(cs, ax=ax2, label="P")
        ax2.contour(G, P, Z, levels=[0.25, 0.5, 0.75], colors="white", linewidths=0.8)
        ax2.scatter(w.gust_0h, w.precipitation_24h_sum, s=1, color="cyan", alpha=0.12)
        ax2.set_xlabel("Gust (m/s)"); ax2.set_ylabel("24-h precipitation (mm)"); ax2.set_ylim(0, 30)
        ax2.set_title(f"{name}: P({what} {lab} | gust, precip)\nb_g={b1:.2f}, b_p={b2:.2f}, b_gp={b3:.2f}", fontsize=8)
    summary[name] = dict(n_weather=int(len(w)), n_all=int(len(d)), states=labels,
                         lognormal_weather_common_beta=dict(theta=[float(v) for v in fit_w["theta"]], beta=float(fit_w["beta"][0])),
                         lognormal_weather_free_beta=dict(theta=[float(v) for v in fit_w_free["theta"]], beta=[float(v) for v in fit_w_free["beta"]]),
                         lr_common_vs_free_beta=dict(stat=float(lr_beta), p=float(p_beta)),
                         lognormal_all_incidents=dict(theta=[float(v) for v in fit_all["theta"]], beta=float(fit_all["beta"][0])),
                         surfaces=surf)
    print(f"[{name}] weather subset n={len(w)}  theta={np.round(fit_w['theta'],1)} beta={fit_w['beta'][0]:.2f}  "
          f"free-beta={np.round(fit_w_free['beta'],2)} LR p={p_beta:.2g}")
    for lab in labels: print(f"   {lab}: gust×precip {np.round(surf[lab]['gust_precip']['params'],3)} mono_g={surf[lab]['gust_precip']['frac_domain_monotone_gust']:.2f} mono_p={surf[lab]['gust_precip']['frac_domain_monotone_precip']:.2f} | gust×pressure {np.round(surf[lab]['gust_pressure']['params'],3)}")
fig.tight_layout(); fig.savefig(FIG / "fig9_fragility_lognormal.png", dpi=170); plt.close(fig)
figS.tight_layout(); figS.savefig(FIG / "fig10_fragility_surfaces.png", dpi=150); plt.close(figS)
(OUT / "fragility_lognormal.json").write_text(json.dumps(summary, indent=2))

(OUT / "fragility_optimizer_diagnostics.json").write_text(json.dumps(OPTIMIZER_DIAGNOSTICS, indent=2))
