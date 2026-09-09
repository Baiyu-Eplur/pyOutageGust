# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Final recommended specifications, implementing the review recommendations.

E0 (exposure):  M5 covariates; gust as linear + ramp between the two estimated knots
                (14, 26 m/s; constant beyond 26 -- customers affected cannot fall with
                gust); gust x pressure kept; temperature^2 added.
R0c (recovery): M5 covariates; gust quadratic kept; gust x pressure dropped;
                temperature^2 and gust x precipitation added; zero-customer
                incidents EXCLUDED (66.5% carry a placeholder duration of exactly
                1.000 h; restoration time is undefined when nobody was interrupted).
                The paper's M5 is refitted on the same subsample for comparison.
Both:           LAD-clustered and LAD x date two-way clustered SEs; p-values from
                t with G-1 df (G = number of LAD clusters) as well as normal;
                LAD-grouped and year-grouped CV against the paper's M5.
Outputs: results/final_models/{E0,R0c}_final_{lad,twoway}.csv, final_summary.json,
         table2_replacement.csv, fig11_final_models.png
"""
import warnings; warnings.filterwarnings("ignore")
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from analysis_new.model_selection import design, SOCIO

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "final_models"; OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "results" / "figures"
KN = json.load(open(ROOT / "results/model_selection/knots.json"))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def final_design(tr, va, name, cust):
    """Paper's M5 design (train-scaled) modified per the recommendations."""
    Xtr, Xva = design(tr, va, "M5_+year_month_FE", cust)
    mu_t, sd_t = tr.temperature_0h.mean(), tr.temperature_0h.std(ddof=1)
    mu_p, sd_p = tr.precipitation_24h_sum.mean(), tr.precipitation_24h_sum.std(ddof=1)
    for X, dd in ((Xtr, tr), (Xva, va)):
        X["z_temperature_sq"] = ((dd.temperature_0h - mu_t) / sd_t) ** 2
        if name == "E0":
            X.drop(columns=["z_gust_sq", "z_gust_0h"], inplace=True)
            k1, k2 = KN["E0"]["selected"]
            X["gust_low"] = np.minimum(dd.gust_0h, k1)                                   # slope below onset
            X["gust_ramp"] = np.minimum(np.maximum(dd.gust_0h - k1, 0.0), k2 - k1)      # ramp; constant above k2
        else:
            X.drop(columns=["z_gust_pressure"], inplace=True)
            X["z_gust_precip"] = X["z_gust_0h"] * ((dd.precipitation_24h_sum - mu_p) / sd_p)
    return Xtr, Xva


def table(res, cov, G):
    se = np.sqrt(np.maximum(np.diag(cov), 0)); t = res.params.to_numpy() / se
    return pd.DataFrame({"term": res.params.index, "coef": res.params.values, "se": se,
                         "p_normal": 2 * stats.norm.sf(np.abs(t)), "p_t_G1": 2 * stats.t.sf(np.abs(t), G - 1)})


def cv(d, y, name, cust, groups, build):
    pred = np.zeros(len(d))
    for k in np.unique(groups):
        m = groups == k
        Xtr, Xva = build(d[~m], d[m]); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
        pred[m] = Xva.to_numpy() @ sm.OLS(y[~m], Xtr).fit().params.to_numpy()
    return float(np.sqrt(np.mean((y - pred) ** 2))), pred


def main():
    summary, t2 = {}, []
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    for i, (name, f, tgt, cust, ylab) in enumerate([("E0", "combined_E0_final.csv", "log1p_customers_v2", False, "log(1+customers)"),
                                                     ("R0c", "combined_R0c_final.csv", "log_duration_B_full_span_hours", True, "log(duration, h)")]):
        d = pd.read_csv(DATA / f)
        if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
        n_full = len(d)
        if name == "R0c":
            zero = d.customers_v2_event_excl_reinterruptions == 0
            placeholder_share = float((d.loc[zero, "duration_B_full_span_hours"] == 1.0).mean())
            d = d[~zero].reset_index(drop=True)
        y = d[tgt].astype(float).to_numpy()
        X, _ = final_design(d, d, name, cust); res = sm.OLS(y, X).fit()
        Xp, _ = design(d, d, "M5_+year_month_FE", cust); resp = sm.OLS(y, Xp).fit()
        g_lad = pd.factorize(d.LAD21CD)[0]; g_date = pd.factorize(pd.to_datetime(d.incident_date_utc).dt.date.astype(str))[0]
        G = g_lad.max() + 1
        cov_lad = cov_cluster(res, g_lad); cov_2w, _, _ = cov_cluster_2groups(res, g_lad, g_date)
        t_lad, t_2w = table(res, cov_lad, G), table(res, cov_2w, G)
        t_lad.to_csv(OUT / f"{name}_final_lad.csv", index=False); t_2w.to_csv(OUT / f"{name}_final_twoway.csv", index=False)
        # ---- CV: LAD-grouped and year-grouped, final vs paper
        rng = np.random.default_rng(20260908); lads = d.LAD21CD.unique(); rng.shuffle(lads)
        lad_fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy(); yr = d.incident_year.to_numpy()
        bF = lambda tr, va: final_design(tr, va, name, cust); bP = lambda tr, va: design(tr, va, "M5_+year_month_FE", cust)
        cv_res = {"final_cv_lad": cv(d, y, name, cust, lad_fold, bF)[0], "paper_cv_lad": cv(d, y, name, cust, lad_fold, bP)[0],
                  "final_cv_year": cv(d, y, name, cust, yr, bF)[0], "paper_cv_year": cv(d, y, name, cust, yr, bP)[0]}
        _, pred_final = cv(d, y, name, cust, lad_fold, bF); _, pred_paper = cv(d, y, name, cust, lad_fold, bP)
        # ---- gust-related terms for the Table 2 replacement (two-way SEs, t(G-1) p-values)
        keep = [c for c in X.columns if "gust" in c or "temperature" in c or c.startswith("z_customers") or c.startswith("z_cust") or c.startswith("z_log1p")]
        for c in keep:
            r = t_2w.set_index("term").loc[c]; rl = t_lad.set_index("term").loc[c]
            t2.append(dict(margin=name, term=c, coef=r.coef, se_lad=rl.se, se_twoway=r.se, p_twoway_tG1=r.p_t_G1))
        summary[name] = dict(n=int(len(d)), n_full_sample=int(n_full),
                             **({"zero_customer_excluded": int(n_full - len(d)), "zero_customer_placeholder_1h_share": placeholder_share} if name == "R0c" else {}), G_lad=int(G), G_date=int(g_date.max() + 1), r2=float(res.rsquared), adj_r2=float(res.rsquared_adj),
                             bic=float(res.bic), paper_bic=float(resp.bic), paper_adj_r2=float(resp.rsquared_adj), **cv_res,
                             knots=KN[name]["selected"] if name == "E0" else None)
        print(f"[{name}] final: adjR2={res.rsquared_adj:.4f} (paper {resp.rsquared_adj:.4f})  BIC {res.bic:.1f} vs {resp.bic:.1f}  "
              f"CV-LAD {cv_res['final_cv_lad']:.4f} vs {cv_res['paper_cv_lad']:.4f}  CV-year {cv_res['final_cv_year']:.4f} vs {cv_res['paper_cv_year']:.4f}")
        print(t_2w[t_2w.term.isin(keep)].round(4).to_string(index=False))
        # ---- figure: gust response with two-way 95% band (left), calibration final vs paper (right)
        ax = axes[i, 0]; gg = np.linspace(0.5, 40, 300); mu, sd = d.gust_0h.mean(), d.gust_0h.std(ddof=1); z = (gg - mu) / sd
        if name == "E0":
            k1, k2 = KN["E0"]["selected"]; cols = ["gust_low", "gust_ramp"]
            Bm = np.column_stack([np.minimum(gg, k1), np.minimum(np.maximum(gg - k1, 0), k2 - k1)])
        else:
            cols = ["z_gust_0h", "z_gust_sq"]; Bm = np.column_stack([z, z ** 2])
        idx = [list(res.params.index).index(c) for c in cols]
        curve = Bm @ res.params[cols].to_numpy(); curve -= curve[np.argmin(np.abs(gg - mu))]
        V = cov_2w[np.ix_(idx, idx)]; se_c = np.sqrt(np.einsum("ij,jk,ik->i", Bm, V, Bm))
        ax.fill_between(gg, curve - 1.96 * se_c, curve + 1.96 * se_c, color="#27ae60", alpha=0.2, label="95% band (LAD×date clustered)")
        ax.plot(gg, curve, color="#27ae60", lw=2, label="final model")
        zp = z; cp = resp.params["z_gust_0h"] * zp + resp.params["z_gust_sq"] * zp ** 2; cp -= cp[np.argmin(np.abs(gg - mu))]
        ax.plot(gg, cp, color="#c0392b", ls="--", lw=1.5, label="paper (quadratic)")
        ax.axhline(0, color="0.7", lw=0.6); ax.set_xlabel("Gust at event (m/s)"); ax.set_ylabel(f"effect on {ylab}, rel. to mean gust")
        ax.set_title(f"{name}: final gust response at mean covariates"); ax.legend(fontsize=7)
        ax = axes[i, 1]
        for lab, pr, c in [("paper M5", pred_paper, "#c0392b"), ("final", pred_final, "#27ae60")]:
            q = pd.qcut(pr, 20, duplicates="drop"); bm = pd.DataFrame({"q": q, "p": pr, "y": y}).groupby("q", observed=True).mean()
            ax.plot(bm.p, bm.y, "o-", ms=3, lw=1.2, color=c, label=lab)
        lim = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]; ax.plot(lim, lim, "k--", lw=0.7)
        ax.set_xlabel("mean predicted (LAD-grouped CV, out-of-fold)"); ax.set_ylabel("mean observed"); ax.set_title(f"{name}: calibration by predicted ventile"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "fig11_final_models.png", dpi=170); plt.close(fig)
    pd.DataFrame(t2).to_csv(OUT / "table2_replacement.csv", index=False)
    (OUT / "final_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
