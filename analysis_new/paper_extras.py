# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Extras for the paper: (1) development/confirmation split with the final hinge
specification; (2) marginal out-of-sample R2 by variable group under district-grouped
CV, final specifications, both samples; (3) outcome distributions with placeholder
annotation. Outputs results/paper/ and figures figP1_r2_decomposition.png, figP2_distributions.png"""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from analysis_new.model_selection import design, SOCIO
from analysis_new.final_models import final_design
from analysis_new.runtime import ROOT, DATA; OUT = ROOT / "results" / "paper"; OUT.mkdir(exist_ok=True); FIG = ROOT / "results" / "figures"
KN = json.load(open(ROOT / "results/model_selection/knots.json"))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

def load(name, weather_only):
    f = "combined_E0_final.csv" if name == "E0" else "combined_R0c_final.csv"; d = pd.read_csv(DATA / f)
    if weather_only: d = d[d.cause_group_official == "weather_natural"]
    if name == "R0c":
        d = d[d.customers_v2_event_excl_reinterruptions > 0].copy(); d["customers_v2_log1p"] = np.log1p(d.customers_v2_event_excl_reinterruptions.astype(float))
    return d.reset_index(drop=True)

out = {}
# ---- (1) development / confirmation split
split = pd.Timestamp("2023-09-30")
for name, tgt, cust in [("E0", "log1p_customers_v2", False), ("R0c", "log_duration_B_full_span_hours", True)]:
    d = load(name, False); dt = pd.to_datetime(d.incident_date_utc)
    res = {}
    for lab, m in [("development", dt < split), ("confirmation", dt >= split), ("combined", np.ones(len(d), bool))]:
        dd = d[m].reset_index(drop=True); y = dd[tgt].astype(float).to_numpy()
        X, _ = final_design(dd, dd, name, cust); r = sm.OLS(y, X).fit()
        gl = pd.factorize(dd.LAD21CD)[0]; gd = pd.factorize(pd.to_datetime(dd.incident_date_utc).dt.date.astype(str))[0]
        cov, _, _ = cov_cluster_2groups(r, gl, gd); se = np.sqrt(np.diag(cov)); G = gl.max() + 1
        terms = [c for c in X.columns if "gust" in c]
        res[lab] = {"n": int(len(dd)), "gust_mean": float(dd.gust_0h.mean()), **{t: dict(coef=float(r.params[t]), se=float(se[list(X.columns).index(t)]), p=float(2 * stats.t.sf(abs(r.params[t] / se[list(X.columns).index(t)]), G - 1))) for t in terms}}
    out[f"{name}_dev_conf"] = res
    print(name, {k: {t: (round(v[t]["coef"], 3), round(v[t]["se"], 3)) for t in v if isinstance(v[t], dict)} for k, v in res.items()})

# ---- (2) marginal out-of-sample R2 by group, district-grouped CV, final specs, both samples
def groups_design(tr, va, name, cust, level):
    """level 0: regional + FE; 1: + non-gust weather; 2: + gust terms; 3 (R0c): + customers."""
    Xtr, Xva = final_design(tr, va, name, cust)
    gust = [c for c in Xtr.columns if "gust" in c]; weather = ["z_precipitation_24h_sum", "z_temperature_0h", "z_pressure_msl_0h", "z_temperature_sq"]
    custc = [c for c in Xtr.columns if "cust" in c]
    drop = []
    if level < 3: drop += custc
    if level < 2: drop += gust
    if level < 1: drop += weather
    drop = [c for c in drop if c in Xtr.columns]
    return Xtr.drop(columns=drop), Xva.drop(columns=drop)

def cv_r2(d, y, mk):
    rng = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng.shuffle(lads)
    fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy(); pred = np.zeros(len(d))
    for k in range(5):
        m = fold == k; Xtr, Xva = mk(d[~m], d[m]); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        pred[m] = Xva.to_numpy() @ sm.OLS(y[~m], Xtr).fit().params.to_numpy()
    return float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))

dec = []
for sample, wo in [("all", False), ("weather", True)]:
    for name, tgt, cust in [("E0", "log1p_customers_v2", False), ("R0c", "log_duration_B_full_span_hours", True)]:
        d = load(name, wo); y = d[tgt].astype(float).to_numpy(); levels = [0, 1, 2] + ([3] if cust else [])
        r2 = [cv_r2(d, y, lambda tr, va, l=l: groups_design(tr, va, name, cust, l)) for l in levels]
        names = ["Regional + calendar", "Non-gust weather", "Gust"] + (["Affected customers"] if cust else [])
        for i, (nm, v) in enumerate(zip(names, r2)):
            dec.append(dict(sample=sample, margin=name, group=nm, cum_r2=v, marginal=v - (r2[i - 1] if i else 0), n=len(d)))
        print(sample, name, [round(v * 100, 2) for v in r2])
dec = pd.DataFrame(dec); dec.to_csv(OUT / "r2_decomposition.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=False)
for ax, name in zip(axes, ["E0", "R0c"]):
    t = dec[dec.margin == name]; groups = t.group.unique(); x = np.arange(len(groups)); w = 0.36
    for j, (sample, c, lab) in enumerate([("all", "#7f8c8d", "all incidents"), ("weather", "#2980b9", "weather-attributed only")]):
        v = [t[(t["sample"] == sample) & (t.group == g)].marginal.iloc[0] * 100 for g in groups]
        ax.bar(x + (j - 0.5) * w, v, w, color=c, label=f"{lab} (n={int(t[t['sample']==sample].n.iloc[0]):,})")
        for xi, vi in zip(x + (j - 0.5) * w, v): ax.text(xi, vi + 0.15, f"{vi:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=8); ax.set_ylabel("marginal out-of-sample R² (pp)"); ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.set_title(f"{'Exposure' if name=='E0' else 'Recovery'} margin"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "figP1_r2_decomposition.png", dpi=170); plt.close(fig)

# ---- (3) outcome distributions with annotations
e = pd.read_csv(DATA / "combined_E0_final.csv"); r = pd.read_csv(DATA / "combined_R0c_final.csv")
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
ax = axes[0]; ax.hist(e.log1p_customers_v2, bins=80, color="#2980b9"); ax.set_xlabel("log(1 + affected customers)"); ax.set_ylabel("incidents"); ax.set_title("(a) Exposure, all incidents (n=60,437)")
for v, l, yy in [(0, "0", 0.55), (np.log(2), "1", 0.97), (np.log(3), "2", 0.28)]: ax.annotate(f"{l} cust.", (v, ax.get_ylim()[1] * yy), fontsize=7, ha="left", xytext=(v + 0.6, ax.get_ylim()[1] * yy), arrowprops=dict(arrowstyle="->", lw=0.6))
ax = axes[1]; ax.hist(r.log_duration_B_full_span_hours, bins=80, color="#c0392b"); ax.set_xlabel("log(restoration duration, h)"); ax.set_title("(b) Recovery, before exclusion (n=59,834)")
ax.annotate("1.000 h placeholder\n(zero-customer incidents)", (0, ax.get_ylim()[1] * 0.8), fontsize=7, ha="left", xytext=(0.4, ax.get_ylim()[1] * 0.8), arrowprops=dict(arrowstyle="->", lw=0.6))
rc = r[r.customers_v2_event_excl_reinterruptions > 0]
ax = axes[2]; ax.hist(rc.log_duration_B_full_span_hours, bins=80, color="#27ae60"); ax.set_xlabel("log(restoration duration, h)"); ax.set_title(f"(c) Recovery, after exclusion (n={len(rc):,})")
ax.annotate("auto-reclosure\nmode (~0.5 h)", (np.log(0.52), 520), fontsize=7, ha="left", xytext=(-2.9, ax.get_ylim()[1] * 0.7), arrowprops=dict(arrowstyle="->", lw=0.6))
fig.tight_layout(); fig.savefig(FIG / "figP2_distributions.png", dpi=170); plt.close(fig)
(OUT / "paper_extras.json").write_text(json.dumps(out, indent=2))
