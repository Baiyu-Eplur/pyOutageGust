# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Fragility-curve demonstration: ordinal (proportional-odds) logit on outage
severity classes, plus a negative-binomial GLM on the raw customer count.

Fragility curve here = P(severity >= class k | gust, covariates at reference),
in direct analogy with seismic fragility P(DS >= ds_k | IM). The gust enters
through the piecewise-linear basis whose knots were estimated in
knot_estimation.py (results/model_selection/knots.json).
"""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from analysis_new.model_selection import design

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "model_selection"; FIG = ROOT / "results" / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
KN = json.load(open(OUT / "knots.json"))

SPEC = {  # margin: (file, severity variable, class edges, labels, customers covariate)
    "E0": ("combined_E0_final.csv", "customers_v2_event_excl_reinterruptions",
           [-0.5, 0.5, 5.5, 100.5, 1000.5, np.inf], ["0", "1-5", "6-100", "101-1000", ">1000"], False),
    "R0c": ("combined_R0c_final.csv", "duration_B_full_span_hours",
            [0, 3, 12, 48, np.inf], ["<3 h", "3-12 h", "12-48 h", ">48 h"], True)}

summary = {}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (name, (f, sev, edges, labels, cust)) in zip(axes, SPEC.items()):
    d = pd.read_csv(DATA / f)
    if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    knots = KN[name].get("unconstrained_selected", KN[name]["selected"])
    X, _ = design(d, d, "M5_+year_month_FE", cust); X = X.drop(columns=["z_gust_sq", "Intercept"])
    for k in knots: X[f"hinge_{k:g}"] = np.maximum(d.gust_0h - k, 0.0)
    cls = pd.cut(d[sev], edges, labels=labels, right=True).astype(str)
    yord = pd.Categorical(cls, categories=labels, ordered=True)
    # ---------------- proportional-odds ordinal logit
    mod = OrderedModel(yord.codes, X, distr="logit")
    res = mod.fit(method="bfgs", maxiter=300, disp=False)
    # ---------------- fragility curves at the reference covariate vector (sample means)
    gg = np.linspace(0.5, 40, 200)
    Xref = pd.DataFrame(np.tile(X.mean().to_numpy(), (len(gg), 1)), columns=X.columns)
    mu, sd = d.gust_0h.mean(), d.gust_0h.std(ddof=1)
    Xref["z_gust_0h"] = (gg - mu) / sd; Xref["z_gust_pressure"] = 0.0  # mean pressure
    for k in knots: Xref[f"hinge_{k:g}"] = np.maximum(gg - k, 0.0)
    probs = res.model.predict(res.params, exog=Xref.to_numpy())  # n x K class probabilities
    exceed = 1 - np.cumsum(probs, axis=1)[:, :-1]                 # P(class >= k), k = 1..K-1
    colors = plt.cm.viridis(np.linspace(0.15, 0.9, len(labels) - 1))
    bins = [0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 26, 30, 45]; mids = [(a + b) / 2 for a, b in zip(bins[:-1], bins[1:])]
    gb = pd.cut(d.gust_0h, bins)
    for j in range(len(labels) - 1):
        emp = (yord.codes >= j + 1)
        e = pd.DataFrame({"g": gb, "e": emp}).groupby("g", observed=True).e.agg(["mean", "count"])
        ax.plot(gg, exceed[:, j], color=colors[j], lw=1.8, label=f"P(severity ≥ {labels[j+1]})")
        ax.errorbar(mids, e["mean"], yerr=1.96 * np.sqrt(e["mean"] * (1 - e["mean"]) / e["count"]), fmt="o", color=colors[j], ms=3, capsize=2, alpha=0.8)
    for k in knots: ax.axvline(k, color="0.6", lw=0.7, ls=":")
    ax.set_ylim(0, 1); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel("Exceedance probability")
    ax.set_title(f"{name}: fragility curves (ordinal logit, covariates at sample mean)")
    ax.legend(fontsize=7, loc="upper left")
    # ---------------- gust coefficients & parallel-lines diagnostic: separate binary logits per threshold
    coefs = {"z_gust_0h": float(res.params["z_gust_0h"]), **{f"hinge_{k:g}": float(res.params[f"hinge_{k:g}"]) for k in knots}}
    per_thr = {}
    Xc = sm.add_constant(X)
    for j in range(len(labels) - 1):
        b = sm.Logit((yord.codes >= j + 1).astype(int), Xc).fit(disp=False, maxiter=200)
        per_thr[f">= {labels[j+1]}"] = {c: float(b.params[c]) for c in coefs}
    # ---------------- negative-binomial GLM on the raw count (E0 only: customers)
    nb = None
    if name == "E0":
        Xc2 = sm.add_constant(X); y = d[sev].astype(float)
        pois = sm.GLM(y, Xc2, family=sm.families.Poisson()).fit()
        alpha = max(((y - pois.mu) ** 2 - pois.mu).sum() / (pois.mu ** 2).sum(), 1e-3)  # moment estimate
        nbres = sm.GLM(y, Xc2, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
        nb = {"alpha": float(alpha), "z_gust_0h": float(nbres.params["z_gust_0h"]),
              **{f"hinge_{k:g}": float(nbres.params[f"hinge_{k:g}"]) for k in knots},
              "deviance_explained": float(1 - nbres.deviance / nbres.null_deviance)}
    summary[name] = {"classes": labels, "class_shares": [float(v) for v in pd.Series(yord.codes).value_counts(normalize=True).sort_index()],
                     "knots": knots, "ordinal_llf": float(res.llf), "ordinal_pseudoR2_McFadden": float(1 - res.llf / OrderedModel(yord.codes, X.iloc[:, :0].assign(z=0.0), distr="logit").fit(disp=False).llf) if False else None,
                     "ordinal_converged": bool(res.mle_retvals.get("converged", False)), "ordinal_gust_coefs": coefs, "per_threshold_binary_logit_gust_coefs": per_thr, "negbin_glm": nb}
    print(f"[{name}] ordinal logit gust coefs {coefs}")
    print(f"[{name}] per-threshold logits: {json.dumps(per_thr, indent=1)}")
    if nb: print(f"[{name}] NB GLM: {nb}")
fig.tight_layout(); fig.savefig(FIG / "fig8_fragility_curves.png", dpi=170); plt.close(fig)
(OUT / "fragility_summary.json").write_text(json.dumps(summary, indent=2))
