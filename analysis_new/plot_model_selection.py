# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Figures and predicted-vs-observed tables for the specification search."""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_new.model_selection import design

from analysis_new.runtime import ROOT, DATA
FIG = ROOT / "results" / "figures"; FIG.mkdir(exist_ok=True, parents=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

MARGINS = [("E0", "combined_E0_final.csv", "log1p_customers_v2", False, "Exposure: log(1+customers)"),
           ("R0c", "combined_R0c_final.csv", "log_duration_B_full_span_hours", True, "Recovery: log(duration, h)")]
KNOTS = {m: [float(k) for k in v.get("unconstrained_selected", v["selected"])] for m, v in json.load(open(ROOT / "results/model_selection/knots.json")).items()}
HLAB = "Hinge E0 " + "/".join(f"{k:g}" for k in KNOTS["E0"]) + " · R0c " + "/".join(f"{k:g}" for k in KNOTS["R0c"])
SPECS = [("M1_weather_linear", "M1 linear"), ("M5_+year_month_FE", "M5 quadratic (paper)"),
         ("A1_gust_cubic", "Cubic"), ("A2_log_gust", "Log gust"), ("A4_gust_bins", "Gust bins"),
         ("HINGE", HLAB), ("A6_M5_+LAD_FE", "M5 + LAD FE")]


def make_X(d, tr, va, spec, cust, name):
    if spec == "HINGE":
        Xtr, Xva = design(tr, va, "M5_+year_month_FE", cust)
        for X, dd in ((Xtr, tr), (Xva, va)):
            X.drop(columns=["z_gust_sq"], inplace=True)
            for k in KNOTS[name]:
                X[f"hinge_{k:g}"] = np.maximum(dd["gust_0h"] - k, 0.0)
        return Xtr, Xva
    return design(tr, va, spec, cust)


def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))


results, calib_rows = {}, []
cmp = pd.read_csv(ROOT / "results/model_selection/all_model_comparison.csv")

for name, f, tgt, cust, ylab in MARGINS:
    d = pd.read_csv(DATA / f)
    if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
    y = d[tgt].astype(float).to_numpy()
    rng = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng.shuffle(lads)
    d["lad_fold"] = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5)))
    res = {}
    for spec, lab in SPECS:
        Xf, _ = make_X(d, d, d, spec, cust, name)
        fit = sm.OLS(y, Xf).fit()
        yhat_in = fit.fittedvalues.to_numpy()
        yhat_cv = np.full(len(d), np.nan)
        for k in range(5):
            m = (d.lad_fold == k).to_numpy()
            Xtr, Xva = make_X(d, d[~m], d[m], spec, cust, name)
            Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
            b = sm.OLS(y[~m], Xtr).fit().params.to_numpy()
            yhat_cv[m] = Xva.to_numpy() @ b
        res[lab] = dict(fit=fit, yin=yhat_in, ycv=yhat_cv, X=Xf)
        for kind, yh in (("in-sample", yhat_in), ("LAD-CV out-of-fold", yhat_cv)):
            r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2)
            calib_rows.append(dict(model=name, spec=lab, kind=kind, rmse=rmse(y, yh), r2=r2,
                                   corr=np.corrcoef(y, yh)[0, 1], slope=np.polyfit(yh, y, 1)[0]))
    results[name] = dict(d=d, y=y, res=res, ylab=ylab)

calib = pd.DataFrame(calib_rows)
calib.to_csv(ROOT / "results/model_selection/predicted_vs_observed_summary.csv", index=False)

# ---------------------------------------------------------------- Figure 1: comparison
fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))
for i, (name, *_ ) in enumerate(MARGINS):
    t = cmp[cmp.model == name].copy(); t["lab"] = t.spec.str.replace("_", " ")
    ax = axes[i, 0]; ax.barh(t.lab, t.dBIC, color=["#c0392b" if v == 0 else "#7f8c8d" for v in t.dBIC])
    ax.set_xlabel("ΔBIC (0 = best)"); ax.set_title(f"{name}: in-sample penalised fit"); ax.invert_yaxis()
    ax = axes[i, 1]
    w = 0.27; idx = np.arange(len(t))
    for j, (col, lab, c) in enumerate([("cv_random", "random 5-fold", "#95a5a6"), ("cv_lad", "LAD-grouped", "#2980b9"), ("cv_year", "leave-one-year-out", "#e67e22")]):
        ax.barh(idx + (j - 1) * w, t[col], height=w, label=lab, color=c)
    ax.set_yticks(idx); ax.set_yticklabels(t.lab); ax.invert_yaxis()
    lo = t[["cv_random", "cv_lad", "cv_year"]].min().min(); hi = t[["cv_random", "cv_lad", "cv_year"]].max().max()
    ax.set_xlim(lo - 0.02, hi + 0.02); ax.set_xlabel("Out-of-sample RMSE"); ax.set_title(f"{name}: cross-validated error")
    if i == 0: ax.legend(fontsize=7, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "fig1_model_comparison.png", dpi=170); plt.close(fig)

# ---------------------------------------------------------------- Figure 2: gust response curves
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
bins = [0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 26, 30, 45]
for ax, (name, f, tgt, cust, ylab) in zip(axes, MARGINS):
    R = results[name]; d, y = R["d"], R["y"]
    X5 = R["res"]["M5 quadratic (paper)"]["X"]
    resid = sm.OLS(y, X5.drop(columns=["z_gust_0h", "z_gust_sq", "z_gust_pressure"])).fit().resid
    g = pd.cut(d.gust_0h, bins); s = pd.DataFrame({"g": g, "r": resid}).groupby("g", observed=True).r.agg(["mean", "sem"])
    mids = [(a + b) / 2 for a, b in zip(bins[:-1], bins[1:])]
    ax.errorbar(mids, s["mean"], yerr=1.96 * s["sem"], fmt="o", color="k", ms=4, capsize=2, label="binned partial residual ±95% CI", zorder=5)
    gg = np.linspace(0.5, 40, 300); mu, sd = d.gust_0h.mean(), d.gust_0h.std(ddof=1); z = (gg - mu) / sd
    for lab, c, ls in [("M5 quadratic (paper)", "#c0392b", "-"), ("Cubic", "#2980b9", "--"), (HLAB, "#27ae60", "-"), ("Log gust", "#8e44ad", ":")]:
        p = R["res"][lab]["fit"].params
        if lab.startswith("M5"): curve = p["z_gust_0h"] * z + p["z_gust_sq"] * z ** 2
        elif lab == "Cubic": curve = p["z_gust_0h"] * z + p["z_gust_sq"] * z ** 2 + p["z_gust_cu"] * z ** 3
        elif lab == "Log gust": curve = p["log_gust"] * np.log1p(gg)
        else: curve = p["z_gust_0h"] * z + sum(p[f"hinge_{k:g}"] * np.maximum(gg - k, 0) for k in KNOTS[name])
        # centre curve on the binned residuals (both are defined up to a constant)
        w = np.interp(mids, gg, curve); curve -= np.average(w - s["mean"].to_numpy(), weights=1 / s["sem"].to_numpy() ** 2)
        ax.plot(gg, curve, color=c, ls=ls, lw=1.8, label=lab)
    ax.axhline(0, color="0.7", lw=0.6); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel("Effect on " + ylab.split(":")[1].strip())
    ax.set_title(f"{name} — {ylab.split(':')[0]}: fitted gust response vs data")
    if name == "E0":
        tp = json.load(open(ROOT/'results/run_summary.json'))['E0_turning_point_ms']
        ax.axvline(tp, color="#c0392b", lw=0.8, ls="--"); ax.text(tp + 0.4, 2.0, f"paper turning\npoint {tp:.1f} m/s", fontsize=7, color="#c0392b")
    for k in KNOTS[name]: ax.axvline(k, color="#27ae60", lw=0.8, ls=":")
    ax.text(KNOTS[name][0] + 0.4, 2.6, "estimated knot(s)\n" + " / ".join(f"{k:g}" for k in KNOTS[name]) + " m/s", fontsize=7, color="#27ae60")
axes[0].legend(fontsize=7, loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "fig2_gust_response.png", dpi=170); plt.close(fig)

# ---------------------------------------------------------------- Figure 3/4: predicted vs observed (hexbin) per model
for name, f, tgt, cust, ylab in MARGINS:
    R = results[name]; y = R["y"]
    for kind, key, fn in (("in-sample", "yin", "fig3"), ("LAD-grouped CV out-of-fold", "ycv", "fig4")):
        fig, axes = plt.subplots(2, 4, figsize=(12, 6)); axes = axes.ravel()
        for ax, (spec, lab) in zip(axes, SPECS):
            yh = R["res"][lab][key]
            ax.hexbin(yh, y, gridsize=45, bins="log", cmap="Blues", mincnt=1)
            lo, hi = np.percentile(y, [0.2, 99.8]); ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
            # binned means of observed by predicted decile
            q = pd.qcut(yh, 10, duplicates="drop"); bm = pd.DataFrame({"q": q, "yh": yh, "y": y}).groupby("q", observed=True).mean()
            ax.plot(bm.yh, bm.y, "o-", color="#c0392b", ms=3, lw=1)
            r = calib[(calib.model == name) & (calib.spec == lab) & (calib.kind.str.startswith(kind[:3]))].iloc[0]
            ax.set_title(lab, fontsize=8); ax.text(0.03, 0.95, f"RMSE {r.rmse:.3f}\nR² {r.r2:.3f}\ncal. slope {r.slope:.2f}", transform=ax.transAxes, va="top", fontsize=7)
            ax.set_xlim(np.percentile(yh, [0.5, 99.5])); ax.set_ylim(lo, hi)
            ax.set_xlabel("predicted"); ax.set_ylabel("observed")
        axes[-1].axis("off"); axes[-1].text(0, 0.8, "Hexbin: log density of incidents\nRed: mean observed within\npredicted-value deciles\nDashed: 45° line\ncal. slope: OLS slope of\nobserved on predicted (1 = calibrated)", fontsize=8, va="top")
        fig.suptitle(f"{name} ({ylab}) — predicted vs observed, {kind}", fontsize=10)
        fig.tight_layout(); fig.savefig(FIG / f"{fn}_{name}_pred_vs_obs.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Figure 5: calibration overlay + residuals vs gust
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for i, (name, f, tgt, cust, ylab) in enumerate(MARGINS):
    R = results[name]; d, y = R["d"], R["y"]
    ax = axes[i, 0]
    for lab, c in [("M1 linear", "0.6"), ("M5 quadratic (paper)", "#c0392b"), ("Cubic", "#2980b9"), (HLAB, "#27ae60"), ("M5 + LAD FE", "#e67e22")]:
        yh = R["res"][lab]["ycv"]; q = pd.qcut(yh, 20, duplicates="drop")
        bm = pd.DataFrame({"q": q, "yh": yh, "y": y}).groupby("q", observed=True).mean()
        ax.plot(bm.yh, bm.y, "o-", ms=3, lw=1.2, color=c, label=lab)
    lim = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lim, lim, "k--", lw=0.7); ax.set_xlabel("mean predicted (out-of-fold, LAD-grouped CV)"); ax.set_ylabel("mean observed")
    ax.set_title(f"{name}: calibration by predicted ventile"); ax.legend(fontsize=7)
    ax = axes[i, 1]
    g = pd.cut(d.gust_0h, bins); mids = [(a + b) / 2 for a, b in zip(bins[:-1], bins[1:])]
    for lab, c in [("M5 quadratic (paper)", "#c0392b"), ("Cubic", "#2980b9"), (HLAB, "#27ae60")]:
        r = y - R["res"][lab]["ycv"]; s = pd.DataFrame({"g": g, "r": r}).groupby("g", observed=True).r.agg(["mean", "sem"])
        ax.errorbar(mids, s["mean"], yerr=1.96 * s["sem"], fmt="o-", ms=3, lw=1, capsize=2, color=c, label=lab)
    ax.axhline(0, color="k", lw=0.7); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel("mean out-of-fold residual")
    ax.set_title(f"{name}: residual bias by gust band (0 = no misfit)"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "fig5_calibration_residuals.png", dpi=170); plt.close(fig)
print(calib.round(4).to_string(index=False))

# ---------------------------------------------------------------- Figure 6: knot estimation
KJ = json.load(open(ROOT / "results/model_selection/knots.json"))
fig, axes = plt.subplots(2, 3, figsize=(12, 6.5))
for i, name in enumerate(["E0", "R0c"]):
    prof2 = pd.read_csv(ROOT / f"results/model_selection/{name}_knot_profile_2.csv")
    prof1 = pd.read_csv(ROOT / f"results/model_selection/{name}_knot_profile_1.csv")
    boot = pd.read_csv(ROOT / f"results/model_selection/{name}_knot_bootstrap.csv")
    kj = KJ[name]; n = kj["n"]
    ax = axes[i, 0]
    ax.plot(prof1.k1, prof1.bic - prof1.bic.min(), "o-", ms=3, color="#2980b9")
    ax.axhline(kj["quadratic"]["bic"] - prof1.bic.min(), color="#c0392b", ls="--", lw=1, label="quadratic (paper)")
    ax.set_xlabel("single knot k (m/s)"); ax.set_ylabel("ΔBIC vs best single knot"); ax.set_title(f"{name}: one-knot profile"); ax.legend(fontsize=7)
    ax = axes[i, 1]
    piv = prof2.pivot(index="k2", columns="k1", values="lr")
    im = ax.imshow(np.minimum(piv.values, 40), origin="lower", aspect="auto", cmap="viridis_r",
                   extent=[piv.columns.min() - .5, piv.columns.max() + .5, piv.index.min() - .5, piv.index.max() + .5])
    from scipy import stats as st
    ax.contour(piv.columns, piv.index, piv.values, levels=[st.chi2.ppf(0.95, 2)], colors="white", linewidths=1.2)
    ax.plot(kj["two_knot"]["k1"], kj["two_knot"]["k2"], "r*", ms=10)
    ax.set_xlabel("k1 (m/s)"); ax.set_ylabel("k2 (m/s)"); ax.set_title(f"{name}: two-knot profile LR (white = 95% region)")
    plt.colorbar(im, ax=ax, label="LR stat (capped at 40)")
    ax = axes[i, 2]
    ax.hist(boot.k1, bins=np.arange(7.5, 21.5, 1), alpha=0.7, color="#27ae60", label="k1")
    ax.hist(boot.k2, bins=np.arange(17.5, 35.5, 1), alpha=0.7, color="#8e44ad", label="k2")
    b = kj["two_knot"]["bootstrap"]
    ax.set_title(f"{name}: LAD cluster bootstrap (B={b['B']})\nk1 95% [{b['k1_pct_2.5_50_97.5'][0]:.0f}, {b['k1_pct_2.5_50_97.5'][2]:.0f}]  k2 95% [{b['k2_pct_2.5_50_97.5'][0]:.0f}, {b['k2_pct_2.5_50_97.5'][2]:.1f}]", fontsize=8)
    ax.set_xlabel("knot (m/s)"); ax.set_ylabel("count"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "fig6_knot_estimation.png", dpi=170); plt.close(fig)
