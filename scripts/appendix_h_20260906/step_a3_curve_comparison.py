"""Command #50 Step A3: gust curve-shape bake-off (quadratic / natural cubic
spline / U-shape-constrained hinge spline / softplus) on the C01+C02-C08
corrected final combined sample, using the paper's own design_train_valid()
and GroupKFold(date,5) CV protocol. Runs for both E0 (exposure) and R0c
(recovery, customers included as covariate).

Fairness: gust x pressure interaction is dropped from ALL four candidates in
this bake-off (see appendix_h_common.py docstring) -- this is a deliberate,
disclosed simplification; OOF numbers here are NOT the paper's main-text
numbers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import patsy

sys.path.insert(0, str(Path(__file__).parent))
from appendix_h_common import (  # noqa: E402
    RAW_DIR, get_data, build_folds, other_covariates, log_step,
    quad_gust_basis, spline_gust_design, ushape_hinge_design, search_ushape_knot,
    fit_ushape, softplus_col, fit_softplus, oof_metrics,
)

N_FOLDS = 5
CANDIDATES = ["quad", "spline4", "ushape", "softplus"]


def fit_ols(X: np.ndarray, y: np.ndarray):
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def run_target(v9, target_name: str, df: pd.DataFrame, target_col: str, use_customers: bool,
               back_transform: str, ushape_knot_grid: np.ndarray):
    log_step("A3", f"=== {target_name} : n={len(df)} ===")
    fold = build_folds(df)
    y_all = df[target_col].astype(float).to_numpy()
    gust_all = df["gust_0h"].astype(float).to_numpy()

    # ---------------- full-sample fit (for knot search, curves, complexity) ----------------
    Xtr_other_full, _, mu_full, sd_full = other_covariates(v9, df, df, use_customers)
    Xo_full = Xtr_other_full.to_numpy()

    ushape_knot, ushape_rss = search_ushape_knot(gust_all, y_all, Xo_full, ushape_knot_grid)
    log_step("A3", f"{target_name}: U-shape knot selected on full sample = {ushape_knot:.3f} m/s "
                    f"(grid RSS={ushape_rss:.2f})")

    softplus_best_full, softplus_coef_full, softplus_all_starts_full = fit_softplus(
        Xo_full, gust_all, y_all)
    log_step("A3", f"{target_name}: softplus full-sample fit b={softplus_best_full['b']:.4f}, "
                    f"c={softplus_best_full['c']:.4f}, converged_starts="
                    f"{sum(r['converged'] for r in softplus_all_starts_full)}/{len(softplus_all_starts_full)}")

    # full-sample coefficients per candidate (for plotting fitted curves + complexity)
    full_fits = {}
    quad_g = quad_gust_basis(df["gust_0h"], mu_full, sd_full)
    coef_quad = fit_ols(np.hstack([Xo_full, quad_g.to_numpy()]), y_all)
    full_fits["quad"] = {"coef": coef_quad, "n_other": Xo_full.shape[1], "n_gust_params": 2}

    spl_tr, _ = spline_gust_design(df["gust_0h"], df["gust_0h"], df=4)
    coef_spl = fit_ols(np.hstack([Xo_full, spl_tr.to_numpy()]), y_all)
    full_fits["spline4"] = {"coef": coef_spl, "n_other": Xo_full.shape[1], "n_gust_params": spl_tr.shape[1],
                             "design_info": spl_tr.design_info}

    ug_full = ushape_hinge_design(df["gust_0h"], ushape_knot)
    res_u = fit_ushape(Xo_full, ug_full.to_numpy(), y_all)
    full_fits["ushape"] = {"coef": res_u.x, "n_other": Xo_full.shape[1], "n_gust_params": 4,
                            "knot": ushape_knot}

    full_fits["softplus"] = {"coef": softplus_coef_full, "n_other": Xo_full.shape[1], "n_gust_params": 3,
                              "b": softplus_best_full["b"], "c": softplus_best_full["c"]}

    # ---------------- CV OOF ----------------
    oof_pred = {c: np.full(len(df), np.nan) for c in CANDIDATES}
    softplus_fold_diag = []

    for f in range(N_FOLDS):
        tr_mask = fold != f
        va_mask = fold == f
        train = df.loc[tr_mask]
        valid = df.loc[va_mask]
        y_tr = y_all[tr_mask]
        Xtr_o, Xva_o, mu, sd = other_covariates(v9, train, valid, use_customers)
        Xtr_o_np, Xva_o_np = Xtr_o.to_numpy(), Xva_o.to_numpy()

        # quad
        g_tr = quad_gust_basis(train["gust_0h"], mu, sd)
        g_va = quad_gust_basis(valid["gust_0h"], mu, sd)
        coef = fit_ols(np.hstack([Xtr_o_np, g_tr.to_numpy()]), y_tr)
        oof_pred["quad"][va_mask] = np.hstack([Xva_o_np, g_va.to_numpy()]) @ coef

        # spline4 (knots fit on train fold only)
        s_tr, s_va = spline_gust_design(train["gust_0h"], valid["gust_0h"], df=4)
        coef = fit_ols(np.hstack([Xtr_o_np, s_tr.to_numpy()]), y_tr)
        oof_pred["spline4"][va_mask] = np.hstack([Xva_o_np, s_va.to_numpy()]) @ coef

        # ushape (knot FIXED from full-sample search; coefficients refit on train fold)
        u_tr = ushape_hinge_design(train["gust_0h"], ushape_knot)
        u_va = ushape_hinge_design(valid["gust_0h"], ushape_knot)
        res = fit_ushape(Xtr_o_np, u_tr.to_numpy(), y_tr)
        oof_pred["ushape"][va_mask] = np.hstack([Xva_o_np, u_va.to_numpy()]) @ res.x

        # softplus (b,c refit fresh on train fold only, multi-start -- fewer
        # starts than the full-sample fit since full-sample already showed
        # complete robustness across starts in Step F diagnostics)
        fold_starts = [(b0, c0) for b0 in (0.1, 0.5, 1.0) for c0 in (8.0, 14.0, 20.0)]
        best, coef, all_starts = fit_softplus(Xtr_o_np, train["gust_0h"].to_numpy(), y_tr, starts=fold_starts)
        sp_va = softplus_col(valid["gust_0h"].to_numpy(), best["b"], best["c"]).reshape(-1, 1)
        oof_pred["softplus"][va_mask] = np.hstack([Xva_o_np, sp_va]) @ coef
        softplus_fold_diag.append({"fold": f, "b": best["b"], "c": best["c"],
                                    "n_converged_starts": sum(r["converged"] for r in all_starts),
                                    "n_starts": len(all_starts)})
        log_step("A3", f"{target_name} fold {f}: done (softplus b={best['b']:.4f}, c={best['c']:.4f})")

    assert all(np.isfinite(oof_pred[c]).all() for c in CANDIDATES)

    # ---------------- metrics ----------------
    metrics_full = {}
    for c in CANDIDATES:
        metrics_full[c] = oof_metrics(y_all, oof_pred[c], back_transform)

    gust_p90 = float(np.quantile(gust_all, 0.90))
    high_mask = gust_all > gust_p90
    metrics_high = {}
    for c in CANDIDATES:
        metrics_high[c] = oof_metrics(y_all[high_mask], oof_pred[c][high_mask], back_transform)
    log_step("A3", f"{target_name}: high-gust subset threshold (p90) = {gust_p90:.3f} m/s, n={high_mask.sum()}")

    # ---------------- paired date-block bootstrap CI (conditional on fixed OOF preds) ----------------
    rng = np.random.default_rng(20260906)
    dates = df["incident_date_utc"].dt.date.astype(str).to_numpy()
    unique_dates = np.unique(dates)
    by_date = {d: np.where(dates == d)[0] for d in unique_dates}
    resid_sq = {c: (y_all - oof_pred[c]) ** 2 for c in CANDIDATES}
    resid_abs = {c: np.abs(y_all - oof_pred[c]) for c in CANDIDATES}

    n_boot = 1000
    diffs_rmse = {c: [] for c in CANDIDATES if c != "quad"}
    diffs_mae = {c: [] for c in CANDIDATES if c != "quad"}
    for b in range(n_boot):
        sampled = rng.choice(unique_dates, size=len(unique_dates), replace=True)
        idx = np.concatenate([by_date[d] for d in sampled])
        base_rmse = np.sqrt(np.mean(resid_sq["quad"][idx]))
        base_mae = np.mean(resid_abs["quad"][idx])
        for c in CANDIDATES:
            if c == "quad":
                continue
            cand_rmse = np.sqrt(np.mean(resid_sq[c][idx]))
            cand_mae = np.mean(resid_abs[c][idx])
            diffs_rmse[c].append(cand_rmse - base_rmse)
            diffs_mae[c].append(cand_mae - base_mae)

    paired_ci = {}
    for c in CANDIDATES:
        if c == "quad":
            continue
        arr_r = np.array(diffs_rmse[c])
        arr_m = np.array(diffs_mae[c])
        paired_ci[c] = {
            "rmse_diff_point": float(metrics_full[c]["rmse_log"] - metrics_full["quad"]["rmse_log"]),
            "rmse_diff_ci95": [float(np.percentile(arr_r, 2.5)), float(np.percentile(arr_r, 97.5))],
            "mae_diff_point": float(metrics_full[c]["mae_log"] - metrics_full["quad"]["mae_log"]),
            "mae_diff_ci95": [float(np.percentile(arr_m, 2.5)), float(np.percentile(arr_m, 97.5))],
        }

    # ---------------- fitted curves over a gust grid (full-sample fit, other covars at their means) ----------------
    p1, p99 = np.quantile(gust_all, [0.01, 0.99])
    grid_ms = np.linspace(p1, p99, 200)
    means_other = Xo_full.mean(axis=0)
    curve_rows = []
    # quad
    zg = (grid_ms - mu_full) / sd_full
    Xg = np.column_stack([zg, zg ** 2])
    pred = np.column_stack([np.tile(means_other, (len(grid_ms), 1)), Xg]) @ full_fits["quad"]["coef"]
    for gm, p in zip(grid_ms, pred):
        curve_rows.append({"model": "quad", "gust_ms": gm, "pred_log": p})
    # spline4
    di = full_fits["spline4"]["design_info"]
    Xg = np.asarray(patsy.build_design_matrices([di], {"gust": grid_ms})[0])
    pred = np.column_stack([np.tile(means_other, (len(grid_ms), 1)), Xg]) @ full_fits["spline4"]["coef"]
    for gm, p in zip(grid_ms, pred):
        curve_rows.append({"model": "spline4", "gust_ms": gm, "pred_log": p})
    # ushape
    k = full_fits["ushape"]["knot"]
    left = np.maximum(k - grid_ms, 0.0)
    right = np.maximum(grid_ms - k, 0.0)
    Xg = np.column_stack([left, left ** 2, right, right ** 2])
    pred = np.column_stack([np.tile(means_other, (len(grid_ms), 1)), Xg]) @ full_fits["ushape"]["coef"]
    for gm, p in zip(grid_ms, pred):
        curve_rows.append({"model": "ushape", "gust_ms": gm, "pred_log": p})
    # softplus
    b_, c_ = full_fits["softplus"]["b"], full_fits["softplus"]["c"]
    sp = softplus_col(grid_ms, b_, c_).reshape(-1, 1)
    pred = np.column_stack([np.tile(means_other, (len(grid_ms), 1)), sp]) @ full_fits["softplus"]["coef"]
    for gm, p in zip(grid_ms, pred):
        curve_rows.append({"model": "softplus", "gust_ms": gm, "pred_log": p})

    curve_df = pd.DataFrame(curve_rows)
    curve_df.to_csv(RAW_DIR / f"a3_curves_{target_name}.csv", index=False)

    # ---------------- save everything ----------------
    complexity = {
        "quad": {"n_gust_params": 2, "n_hyperparams": 0, "note": "linear+quadratic, no tuning"},
        "spline4": {"n_gust_params": 4, "n_hyperparams": 1, "note": "df=4 fixed a priori (not tuned per fold)"},
        "ushape": {"n_gust_params": 4, "n_hyperparams": 1,
                   "note": f"knot={ushape_knot:.3f} m/s chosen by full-sample grid search, fixed across folds"},
        "softplus": {"n_gust_params": 3, "n_hyperparams": 2,
                     "note": "b,c refit per fold via 16-start Nelder-Mead (nonconvex)"},
    }

    result = {
        "target": target_name, "n": int(len(df)), "gust_p90": gust_p90,
        "ushape_knot": ushape_knot,
        "softplus_full_sample": {"b": softplus_best_full["b"], "c": softplus_best_full["c"],
                                  "n_converged_starts": sum(r["converged"] for r in softplus_all_starts_full),
                                  "n_starts": len(softplus_all_starts_full)},
        "softplus_fold_diagnostics": softplus_fold_diag,
        "metrics_full": metrics_full,
        "metrics_high_gust": metrics_high,
        "paired_ci_vs_quad": paired_ci,
        "complexity": complexity,
    }
    (RAW_DIR / f"a3_result_{target_name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log_step("A3", f"{target_name}: saved a3_result_{target_name}.json and a3_curves_{target_name}.csv")
    return result


def main():
    v9, combined_e0, combined_r0cb = get_data()

    knot_grid = np.arange(6.0, 16.0, 0.5)

    run_target(v9, "E0", combined_e0, "log1p_customers_v2", False, "expm1", knot_grid)
    run_target(v9, "R0c", combined_r0cb, "log_duration_B_full_span_hours", True, "exp", knot_grid)

    log_step("A3", "ALL DONE.")


if __name__ == "__main__":
    main()
