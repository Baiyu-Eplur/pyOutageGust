# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""Formal estimation of the piecewise-linear gust knots.

1. Profile likelihood: exhaustive grid over knot locations (1 m/s steps),
   minimising residual sum of squares of the full M5 covariate set with
   gust entering as linear + hinge(s). Reports BIC surface and a
   likelihood-ratio-based joint confidence region.
2. LAD cluster bootstrap: districts resampled with replacement (B reps),
   knots re-estimated on a 1 m/s grid each time -> percentile intervals.
3. Nested cross-validation: knots re-selected by BIC inside each LAD-grouped
   training fold, so the held-out error is not contaminated by knot choice.
Writes results/model_selection/knots.json consumed by the other scripts.
"""
import warnings; warnings.filterwarnings("ignore")
import sys, json, itertools, time
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from analysis_new.model_selection import design

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "model_selection"; OUT.mkdir(parents=True, exist_ok=True)
from analysis_new.runtime import KNOT_BOOTSTRAPS as B_BOOT
SEED = 20260908

MARGINS = [("E0", "combined_E0_final.csv", "log1p_customers_v2", False, 2),
           ("R0c", "combined_R0c_final.csv", "log_duration_B_full_span_hours", True, 2)]


def base_matrix(tr, va, cust):
    """M5 design minus gust^2 (keeps linear z_gust and gust x pressure)."""
    Xtr, Xva = design(tr, va, "M5_+year_month_FE", cust)
    return Xtr.drop(columns=["z_gust_sq"]), Xva.drop(columns=["z_gust_sq"])


def hinge_cols(g, knots):
    return np.column_stack([np.maximum(g - k, 0.0) for k in knots])


class KnotSolver:
    """Frisch-Waugh + Gram matrix: project out the fixed covariates once,
    residualise every candidate hinge column once, then the SSE for any set of
    knots is ry'ry - c_S' G_SS^{-1} c_S with a tiny solve."""
    def __init__(self, X0, g, y, kgrid):
        Q, _ = np.linalg.qr(X0)
        self.ry = y - Q @ (Q.T @ y); self.yy = float(self.ry @ self.ry)
        H = hinge_cols(g, kgrid); rH = H - Q @ (Q.T @ H)
        self.G = rH.T @ rH; self.c = rH.T @ self.ry
        self.pos = {float(k): i for i, k in enumerate(kgrid)}
    def sse(self, knots):
        i = [self.pos[float(k)] for k in knots]
        Gs = self.G[np.ix_(i, i)]; cs = self.c[i]
        return float(self.yy - cs @ np.linalg.solve(Gs, cs))


KGRID = np.arange(8, 35, 1.0)


def grid_search(X0, g, y, n_knots, k1_range, k2_range=None, min_gap=4, solver=None):
    S = solver or KnotSolver(X0, g, y, KGRID)
    best, table = None, []
    if n_knots == 1:
        combos = [(k,) for k in k1_range]
    else:
        combos = [(a, b) for a in k1_range for b in k2_range if b - a >= min_gap]
    n = len(y); p0 = X0.shape[1]
    for ks in combos:
        s = S.sse(ks)
        bic = n * np.log(s / n) + (p0 + len(ks)) * np.log(n)
        table.append((*ks, s, bic))
        if best is None or s < best[1]: best = (ks, s)
    cols = ["k1", "sse", "bic"] if n_knots == 1 else ["k1", "k2", "sse", "bic"]
    return best[0], best[1], pd.DataFrame(table, columns=cols)


def main():
    results = {}
    for name, f, tgt, cust, nk in MARGINS:
        t0 = time.time()
        d = pd.read_csv(DATA / f)
        if cust: d["customers_v2_log1p"] = np.log1p(d["customers_v2_event_excl_reinterruptions"].astype(float))
        y = d[tgt].astype(float).to_numpy(); g = d["gust_0h"].to_numpy(); n = len(y)
        X0df, _ = base_matrix(d, d, cust); X0 = X0df.to_numpy()
        k1r = np.arange(8, 21, 1.0); k2r = np.arange(18, 35, 1.0)
        out = {"n": int(n)}

        # ---- profile likelihood, one and two knots
        k1_1, sse1, tab1 = grid_search(X0, g, y, 1, np.arange(8, 31, 1.0))
        k_2, sse2, tab2 = grid_search(X0, g, y, 2, k1r, k2r)
        # quadratic (paper) SSE for reference
        Xq, _ = design(d, d, "M5_+year_month_FE", cust)
        sseq = float(np.sum(sm.OLS(y, Xq).fit().resid ** 2))
        bic = lambda s, p: n * np.log(s / n) + p * np.log(n)
        p0 = X0.shape[1]
        out["quadratic"] = {"sse": sseq, "bic": bic(sseq, p0 + 1)}
        out["one_knot"] = {"k1": float(k1_1[0]), "sse": sse1, "bic": bic(sse1, p0 + 1)}
        out["two_knot"] = {"k1": float(k_2[0]), "k2": float(k_2[1]), "sse": sse2, "bic": bic(sse2, p0 + 2)}
        # LR test two vs one knot (1 extra slope + 1 knot ~ 2 df, conservative)
        lr = n * np.log(sse1 / sse2)
        out["two_vs_one_LR"] = {"stat": float(lr), "p_2df": float(stats.chi2.sf(lr, 2))}
        # joint 95% confidence region for (k1,k2): profile LR within chi2(2) 0.95 of the minimum
        tab2["lr"] = n * np.log(tab2.sse / sse2)
        region = tab2[tab2.lr <= stats.chi2.ppf(0.95, 2)]
        out["two_knot"]["profile_region_95"] = {"k1": [float(region.k1.min()), float(region.k1.max())],
                                                 "k2": [float(region.k2.min()), float(region.k2.max())],
                                                 "n_cells": int(len(region))}
        tab1.to_csv(OUT / f"{name}_knot_profile_1.csv", index=False)
        tab2.to_csv(OUT / f"{name}_knot_profile_2.csv", index=False)
        print(f"[{name}] profile: 1-knot k={k1_1[0]:.0f}  2-knot k=({k_2[0]:.0f},{k_2[1]:.0f})  "
              f"BIC quad={out['quadratic']['bic']:.1f} 1k={out['one_knot']['bic']:.1f} 2k={out['two_knot']['bic']:.1f}  "
              f"LR(2v1)={lr:.1f} p={out['two_vs_one_LR']['p_2df']:.2g}  region k1{out['two_knot']['profile_region_95']['k1']} k2{out['two_knot']['profile_region_95']['k2']}", flush=True)

        # ---- LAD cluster bootstrap on the two-knot model (coarser 1 m/s grid, narrowed window)
        rng = np.random.default_rng(SEED)
        lad_codes = pd.factorize(d.LAD21CD)[0]; L = lad_codes.max() + 1
        idx_by_lad = [np.flatnonzero(lad_codes == l) for l in range(L)]
        k1w = np.arange(max(8, k_2[0] - 6), k_2[0] + 7, 1.0); k2w = np.arange(max(18, k_2[1] - 8), min(34, k_2[1] + 8) + 1, 1.0)
        boot = []
        for b in range(B_BOOT):
            pick = rng.integers(0, L, L)
            ii = np.concatenate([idx_by_lad[l] for l in pick])
            kb, _, _ = grid_search(X0[ii], g[ii], y[ii], 2, k1w, k2w, solver=KnotSolver(X0[ii], g[ii], y[ii], KGRID))
            boot.append(kb)
        boot = np.array(boot)
        out["two_knot"]["bootstrap"] = {"B": B_BOOT,
                                        "k1_pct_2.5_50_97.5": [float(v) for v in np.percentile(boot[:, 0], [2.5, 50, 97.5])],
                                        "k2_pct_2.5_50_97.5": [float(v) for v in np.percentile(boot[:, 1], [2.5, 50, 97.5])],
                                        "k1_sd": float(boot[:, 0].std()), "k2_sd": float(boot[:, 1].std())}
        pd.DataFrame(boot, columns=["k1", "k2"]).to_csv(OUT / f"{name}_knot_bootstrap.csv", index=False)
        print(f"[{name}] bootstrap B={B_BOOT}: k1 {np.percentile(boot[:,0],[2.5,50,97.5])}  k2 {np.percentile(boot[:,1],[2.5,50,97.5])}", flush=True)

        # ---- nested CV: reselect knots (2-knot, BIC on train) inside each LAD fold; compare with quadratic
        rng2 = np.random.default_rng(SEED); lads = d.LAD21CD.unique(); rng2.shuffle(lads)
        fold = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy()
        pred_h, pred_q, pred_h1, fold_knots = np.zeros(n), np.zeros(n), np.zeros(n), []
        for k in range(5):
            m = fold == k
            Xtr, Xva = base_matrix(d[~m], d[m], cust); Xva = Xva.reindex(columns=Xtr.columns, fill_value=0.0)
            kf, _, _ = grid_search(Xtr.to_numpy(), g[~m], y[~m], 2, k1r, k2r); fold_knots.append([float(kf[0]), float(kf[1])])
            Xh_tr = np.hstack([Xtr.to_numpy(), hinge_cols(g[~m], kf)]); Xh_va = np.hstack([Xva.to_numpy(), hinge_cols(g[m], kf)])
            b, *_ = np.linalg.lstsq(Xh_tr, y[~m], rcond=None); pred_h[m] = Xh_va @ b
            kf1, _, _ = grid_search(Xtr.to_numpy(), g[~m], y[~m], 1, np.arange(8, 31, 1.0))
            b, *_ = np.linalg.lstsq(np.hstack([Xtr.to_numpy(), hinge_cols(g[~m], kf1)]), y[~m], rcond=None)
            pred_h1[m] = np.hstack([Xva.to_numpy(), hinge_cols(g[m], kf1)]) @ b
            Xq_tr, Xq_va = design(d[~m], d[m], "M5_+year_month_FE", cust); Xq_va = Xq_va.reindex(columns=Xq_tr.columns, fill_value=0.0)
            b = sm.OLS(y[~m], Xq_tr).fit().params.to_numpy(); pred_q[m] = Xq_va.to_numpy() @ b
        rm = lambda p: float(np.sqrt(np.mean((y - p) ** 2)))
        out["nested_cv"] = {"fold_knots_2": fold_knots, "rmse_two_knot": rm(pred_h), "rmse_one_knot": rm(pred_h1), "rmse_quadratic": rm(pred_q)}
        print(f"[{name}] nested CV: quad={rm(pred_q):.4f} 1-knot={rm(pred_h1):.4f} 2-knot={rm(pred_h):.4f}  fold knots={fold_knots}  ({time.time()-t0:.0f}s)", flush=True)
        results[name] = out

    # final knots to carry forward: two knots only if the LR test supports the second
    # knot AND both knots are identified (bootstrap 95% interval width <= 6 m/s);
    # otherwise the single profile-likelihood knot.
    for name in results:
        r = results[name]; bs = r["two_knot"]["bootstrap"]
        w1 = bs["k1_pct_2.5_50_97.5"][2] - bs["k1_pct_2.5_50_97.5"][0]
        w2 = bs["k2_pct_2.5_50_97.5"][2] - bs["k2_pct_2.5_50_97.5"][0]
        two = r["two_vs_one_LR"]["p_2df"] < 0.01 and w1 <= 6 and w2 <= 6
        r["selected"] = [r["two_knot"]["k1"], r["two_knot"]["k2"]] if two else [r["one_knot"]["k1"]]
        r["selection_rule"] = "LR p<0.01 and both bootstrap 95% widths <= 6 m/s"
        print(f"[{name}] selected knots: {r['selected']}  (bootstrap widths k1={w1:.1f}, k2={w2:.1f})")
    (OUT / "knots.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
