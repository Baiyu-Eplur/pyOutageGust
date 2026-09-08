"""Shared infrastructure for command #50 (Appendix H): candidate gust-shape
comparison and distribution-assumption comparison, on the C01+C02-C08
corrected final combined sample, using the paper's real Section 3.3 design
(design_train_valid, GroupKFold(date,5), log-OLS targets).

Fairness rule applied throughout Step A3: the gust x pressure interaction
term is DROPPED from ALL four gust-shape candidates (including the quadratic
baseline used in this bake-off), because only the quadratic form admits a
trivial product interaction; this keeps the bake-off apples-to-apples. This
means the "quadratic" candidate reported here is a REDUCED version of the
paper's actual main-spec model (no interaction term) and its OOF numbers are
NOT directly comparable to the paper's main-text E0/R0c OOF R^2 figures --
this is a deliberate, disclosed simplification for Appendix H only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
from scipy.optimize import lsq_linear, minimize
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\appendix_h_20260906\raw")
FIG_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\appendix_h_20260906\figures")
RAW_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

N_FOLDS = 5
GUST_GRID_N = 200


def log_step(tag, msg):
    print(f"[{tag}] {msg}", flush=True)


def get_data():
    v9, _, _ = _patch_v9()
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()
    for df in (combined_e0, combined_r0cb):
        df["incident_date_utc"] = pd.to_datetime(df["incident_date_utc"], errors="coerce")
    return v9, combined_e0, combined_r0cb


def build_folds(df: pd.DataFrame) -> np.ndarray:
    dates = df["incident_date_utc"].dt.date.astype(str).to_numpy()
    gkf = GroupKFold(n_splits=N_FOLDS)
    fold = np.full(len(df), -1, dtype=int)
    X_dummy = np.zeros(len(df))
    for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=dates)):
        fold[valid_idx] = fold_idx
    assert (fold >= 0).all()
    return fold


def other_covariates(v9, train: pd.DataFrame, valid: pd.DataFrame, use_customers: bool):
    """Build the non-gust part of the design matrix using the project's own
    design_train_valid(), then strip the gust-related columns so the caller
    can attach whichever gust-shape basis is being tested. No gust x pressure
    interaction is included in the returned frame (dropped for fairness)."""
    tr = train.copy()
    va = valid.copy()
    extra = None
    if use_customers:
        tr["customers_v2_log1p"] = np.log1p(tr["customers_v2_event_excl_reinterruptions"].astype(float))
        va["customers_v2_log1p"] = np.log1p(va["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    Xtr, Xva = v9.design_train_valid(tr, va, extra_scale_cols=extra)
    drop_cols = ["z_gust_0h", "z_gust_0h_sq", "z_gust_pressure"]
    Xtr = Xtr.drop(columns=drop_cols)
    Xva = Xva.drop(columns=drop_cols)
    # also need the gust standardization mu/sd (fit on train) to convert grid m/s -> z later if needed
    mu, sd = tr["gust_0h"].mean(), tr["gust_0h"].std(ddof=1)
    return Xtr, Xva, mu, sd


# ---------------------------------------------------------------------------
# Candidate gust-shape bases
# ---------------------------------------------------------------------------

def quad_gust_basis(gust_ms: pd.Series, mu: float, sd: float) -> pd.DataFrame:
    z = (gust_ms - mu) / sd
    return pd.DataFrame({"gust_b1": z.values, "gust_b2": (z ** 2).values}, index=gust_ms.index)


def spline_gust_design(train_gust_ms: pd.Series, valid_gust_ms: pd.Series, df: int = 4):
    """Natural cubic spline (patsy cr()), knots fit on TRAIN only, applied to VALID
    via the same design_info (correct out-of-sample basis extension)."""
    tr_dm = patsy.dmatrix(f"cr(gust, df={df}) - 1", {"gust": train_gust_ms.values}, return_type="dataframe")
    tr_dm.index = train_gust_ms.index
    va_dm = patsy.build_design_matrices([tr_dm.design_info], {"gust": valid_gust_ms.values})[0]
    va_dm = pd.DataFrame(np.asarray(va_dm), columns=tr_dm.columns, index=valid_gust_ms.index)
    tr_dm.columns = [f"gust_spl{i}" for i in range(tr_dm.shape[1])]
    va_dm.columns = tr_dm.columns
    return tr_dm, va_dm


def ushape_hinge_design(gust_ms: pd.Series, knot: float) -> pd.DataFrame:
    left = np.maximum(knot - gust_ms.values, 0.0)
    right = np.maximum(gust_ms.values - knot, 0.0)
    return pd.DataFrame({
        "gust_u_left1": left, "gust_u_left2": left ** 2,
        "gust_u_right1": right, "gust_u_right2": right ** 2,
    }, index=gust_ms.index)


def search_ushape_knot(gust_ms: np.ndarray, y: np.ndarray, X_other: np.ndarray, candidates: np.ndarray):
    """Grid-search the U-shape knot location on the FULL sample once (not
    re-searched per CV fold -- disclosed as a fixed-hyperparameter choice,
    analogous to fixing the spline df a priori)."""
    best = None
    for k in candidates:
        Xg = ushape_hinge_design(pd.Series(gust_ms), k).values
        X = np.hstack([X_other, Xg])
        n_other = X_other.shape[1]
        lb = np.concatenate([np.full(n_other, -np.inf), np.zeros(4)])
        ub = np.full(X.shape[1], np.inf)
        res = lsq_linear(X, y, bounds=(lb, ub), method="bvls")
        rss = float(np.sum(res.fun ** 2))
        if best is None or rss < best[0]:
            best = (rss, k)
    return best[1], best[0]


def fit_ushape(X_other: np.ndarray, Xg: np.ndarray, y: np.ndarray):
    X = np.hstack([X_other, Xg])
    n_other = X_other.shape[1]
    lb = np.concatenate([np.full(n_other, -np.inf), np.zeros(Xg.shape[1])])
    ub = np.full(X.shape[1], np.inf)
    res = lsq_linear(X, y, bounds=(lb, ub), method="bvls")
    return res


def softplus_col(gust_ms: np.ndarray, b: float, c: float) -> np.ndarray:
    x = b * (gust_ms - c)
    # numerically stable softplus
    return np.where(x > 30, x, np.log1p(np.exp(np.clip(x, -30, 30))))


def fit_softplus(X_other: np.ndarray, gust_ms: np.ndarray, y: np.ndarray, starts=None,
                  b_bounds=(0.01, 5.0)):
    """Profile nonlinear least squares: outer search over (b, c), inner OLS
    for (a, beta_other). Multiple starting points tried; convergence status
    for each is returned for Step F reporting. `b` is bounded to keep the
    softplus a genuinely smooth ramp (b_bounds default 0.01-5.0 per m/s);
    without this bound, unconstrained Nelder-Mead can drift b to extreme
    values where softplus degenerates into a near-step function, which is a
    different (and unintended) functional family.

    Speed: the inner OLS is done via Frisch-Waugh-Lovell partialling-out of
    X_other (computed ONCE per call, not per (b,c) evaluation), reducing each
    outer-loop evaluation from an O(n*p^2) refit to an O(n*p) projection --
    this is what makes the 16-start x 5-fold search tractable at n=48k-60k."""
    gmin, gmax = float(np.min(gust_ms)), float(np.max(gust_ms))
    c_bounds = (gmin - 5.0, gmax + 5.0)
    if starts is None:
        starts = [(b0, c0) for b0 in (0.1, 0.3, 0.6, 1.0) for c0 in (5.0, 10.0, 15.0, 20.0)]

    # Precompute the FWL projector for X_other ONCE.
    Xo_pinv = np.linalg.pinv(X_other)  # (p x n)
    Hy = X_other @ (Xo_pinv @ y)
    y_resid = y - Hy
    yr_dot_yr = float(y_resid @ y_resid)

    def profile_rss_and_a(b, c):
        sp = softplus_col(gust_ms, b, c)
        sp_proj = X_other @ (Xo_pinv @ sp)
        sp_resid = sp - sp_proj
        denom = float(sp_resid @ sp_resid)
        if denom < 1e-10:
            return 1e18, 0.0, sp_resid
        a = float(sp_resid @ y_resid) / denom
        rss = yr_dot_yr - (a ** 2) * denom
        return rss, a, sp_resid

    def objective(params):
        b, c = params
        rss, _, _ = profile_rss_and_a(b, c)
        return rss

    results = []
    for b0, c0 in starts:
        opt = minimize(objective, x0=[b0, c0], method="Nelder-Mead",
                        bounds=[b_bounds, c_bounds],
                        options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 200})
        results.append({"b0": b0, "c0": c0, "b": float(opt.x[0]), "c": float(opt.x[1]),
                         "rss": float(opt.fun), "converged": bool(opt.success), "message": str(opt.message),
                         "at_b_bound": bool(opt.x[0] <= b_bounds[0] + 1e-6 or opt.x[0] >= b_bounds[1] - 1e-6)})
    best = min(results, key=lambda r: r["rss"])
    # Recover full coefficient vector (beta_other, a) at the winning (b, c).
    sp_best = softplus_col(gust_ms, best["b"], best["c"])
    X = np.hstack([X_other, sp_best.reshape(-1, 1)])
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    return best, coef, results


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def oof_metrics(y_true_log: np.ndarray, y_pred_log: np.ndarray, back_transform: str):
    resid = y_true_log - y_pred_log
    rmse_log = float(np.sqrt(np.mean(resid ** 2)))
    mae_log = float(np.mean(np.abs(resid)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y_true_log - y_true_log.mean()) ** 2))
    r2_log = 1 - ss_res / ss_tot
    if back_transform == "expm1":
        y_true_raw = np.expm1(y_true_log)
        y_pred_raw = np.expm1(y_pred_log)
    else:
        y_true_raw = np.exp(y_true_log)
        y_pred_raw = np.exp(y_pred_log)
    resid_raw = y_true_raw - y_pred_raw
    rmse_raw = float(np.sqrt(np.mean(resid_raw ** 2)))
    mae_raw = float(np.mean(np.abs(resid_raw)))
    return {
        "rmse_log": rmse_log, "mae_log": mae_log, "r2_log": r2_log,
        "rmse_raw_naive_exp": rmse_raw, "mae_raw_naive_exp": mae_raw,
        "n": int(len(y_true_log)),
    }
