"""X01 independent candidate-curve experiment.

This script reads only the frozen event snapshot inside this run directory.  It
fits the nine pre-registered working-mean specifications for each task,
creates protected time-block out-of-fold predictions, and writes auditable
tables, figures, diagnostics, and Chinese reports.  It deliberately does not
write to the parent research-repair project.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import BSpline
from scipy.optimize import minimize
from scipy.special import expit, ndtr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SEED = 20260906
RNG = np.random.default_rng(SEED)
INPUT = ROOT / "frozen_sources" / "input" / "R02_event_master.parquet"
STORMS = ROOT / "frozen_sources" / "configs" / "storm_windows.json"
TABLES = ROOT / "tables"
PREDICTIONS = ROOT / "predictions"
FIGURES = ROOT / "figures"
EVIDENCE = ROOT / "evidence"
MODELS = ROOT / "models"
LOG = EVIDENCE / "run_log.txt"

for folder in (TABLES, PREDICTIONS, FIGURES, EVIDENCE, MODELS):
    folder.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    stamp = pd.Timestamp.now(tz="UTC").isoformat()
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def dump_json(path: Path, value) -> None:
    def default(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Not serializable: {type(obj)!r}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=default), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def loss_and_resid(y: np.ndarray, mu: np.ndarray, task: str) -> tuple[np.ndarray, np.ndarray]:
    """Working loss and d(loss)/d(eta), excluding the common factor n."""
    safe_mu = np.clip(mu, 1e-12, 1e12)
    if task == "E":
        return safe_mu - y * np.log(safe_mu), safe_mu - y
    return np.log(safe_mu) + y / safe_mu, 1.0 - y / safe_mu


def deviance(y: np.ndarray, mu: np.ndarray, task: str) -> np.ndarray:
    mu = np.clip(mu, 1e-12, 1e12)
    if task == "E":
        term = np.zeros_like(y, dtype=float)
        positive = y > 0
        term[positive] = y[positive] * np.log(y[positive] / mu[positive])
        return 2.0 * (term - (y - mu))
    ratio = np.clip(y / mu, 1e-12, 1e12)
    return 2.0 * (ratio - 1.0 - np.log(ratio))


def finite_exp(eta: np.ndarray) -> np.ndarray:
    # This is a numerical overflow guard, recorded in diagnostics.  The bound
    # is never used to delete observations or improve a score.
    return np.exp(np.clip(eta, -27.6310211, 27.6310211))


def knots_for(g: np.ndarray, n_basis: int) -> np.ndarray:
    degree = 3
    if np.nanmin(g) == np.nanmax(g):
        raise ValueError("gust_has_no_training_variation")
    n_inner = n_basis - degree - 1
    if n_inner < 0:
        raise ValueError("invalid_basis_dimension")
    qs = np.linspace(0, 1, n_inner + 2)[1:-1]
    inner = np.quantile(g, qs) if n_inner else np.array([])
    inner = np.unique(inner)
    if inner.size != n_inner:
        # Ties in gust values make the requested basis unidentifiable.
        raise ValueError("duplicate_internal_spline_knots")
    return np.r_[np.repeat(np.min(g), degree + 1), inner, np.repeat(np.max(g), degree + 1)]


def spline_design(g: np.ndarray, knots: np.ndarray) -> np.ndarray:
    # Cubic B-spline polynomial extrapolation is retained and explicitly
    # flagged in support tables; no support-outside observations are deleted.
    return BSpline.design_matrix(g, knots, k=3, extrapolate=True).toarray()


def softplus(x: np.ndarray) -> np.ndarray:
    return np.logaddexp(0.0, x)


def second_difference_penalty(c: np.ndarray, lam: float) -> tuple[float, np.ndarray]:
    if lam <= 0 or len(c) < 3:
        return 0.0, np.zeros_like(c)
    d2 = c[:-2] - 2 * c[1:-1] + c[2:]
    penalty = lam * float(np.mean(d2 * d2))
    grad = np.zeros_like(c)
    multiplier = 2 * lam / len(d2)
    grad[:-2] += multiplier * d2
    grad[1:-1] += -2 * multiplier * d2
    grad[2:] += multiplier * d2
    return penalty, grad


def model_curve_q_jac(
    model_id: str,
    g: np.ndarray,
    gref: float,
    curve_params: np.ndarray,
    curve_meta: dict,
) -> tuple[np.ndarray, np.ndarray]:
    """Return log r(g) and derivatives wrt the curve parameterization."""
    n = len(g)
    if model_id == "M00":
        return np.zeros(n), np.zeros((n, 0))
    if model_id == "M01":
        u = (g - curve_meta["g_mean"]) / curve_meta["g_sd"]
        ur = (gref - curve_meta["g_mean"]) / curve_meta["g_sd"]
        d = u - ur
        return curve_params[0] * d, d[:, None]
    if model_id == "M02":
        u = (g - curve_meta["g_mean"]) / curve_meta["g_sd"]
        ur = (gref - curve_meta["g_mean"]) / curve_meta["g_sd"]
        design = np.column_stack([u - ur, u * u - ur * ur])
        return design @ curve_params, design
    if model_id in ("M03", "M04"):
        b = spline_design(g, np.asarray(curve_meta["knots"]))
        br = spline_design(np.array([gref]), np.asarray(curve_meta["knots"]))[0]
        d = b - br
        if model_id == "M03":
            return d @ curve_params, d
        # Coefficients are nondecreasing B-spline coefficients.  The first
        # value is free; remaining increments are softplus transformed.
        z = curve_params
        inc = softplus(z[1:])
        c = z[0] + np.r_[0.0, np.cumsum(inc)]
        q = d @ c
        jac = np.empty((n, len(z)))
        jac[:, 0] = d.sum(axis=1)
        suffix = np.cumsum(d[:, ::-1], axis=1)[:, ::-1]
        jac[:, 1:] = suffix[:, 1:] * expit(z[1:])
        return q, jac

    if model_id == "M05":
        b, tau, h = curve_params
        h = max(h, 1e-8)
        x = (g - tau) / h
        xr = (gref - tau) / h
        l, lr = softplus(x), softplus(np.array([xr]))[0]
        s, sr = expit(x), expit(np.array([xr]))[0]
        v, vr = 1 + b * h * l, 1 + b * h * lr
        q = np.log(v) - np.log(vr)
        dv = np.column_stack([h * l, -b * s, b * (l - x * s)])
        dvr = np.array([h * lr, -b * sr, b * (lr - xr * sr)])
        return q, dv / v[:, None] - dvr[None, :] / vr

    if model_id == "M06":
        a, g50, s = curve_params
        g_safe = np.maximum(g, 1e-8)
        gr_safe = max(gref, 1e-8)
        z = np.log(g_safe / g50) / s
        zr = math.log(gr_safe / g50) / s
        p, pr = ndtr(z), ndtr(zr)
        pdf, pdfr = np.exp(-0.5 * z * z) / math.sqrt(2 * math.pi), math.exp(-0.5 * zr * zr) / math.sqrt(2 * math.pi)
        v, vr = 1 + a * p, 1 + a * pr
        q = np.log(v) - math.log(vr)
        dv = np.column_stack([p, -a * pdf / (s * g50), -a * pdf * z / s])
        dvr = np.array([pr, -a * pdfr / (s * g50), -a * pdfr * zr / s])
        return q, dv / v[:, None] - dvr[None, :] / vr

    if model_id in ("M07", "M08"):
        a, tau, h = curve_params
        h = max(h, 1e-8)
        x, xr = (g - tau) / h, (gref - tau) / h
        if model_id == "M07":
            p, pr = expit(x), expit(xr)
            dx, dxr = p * (1 - p), pr * (1 - pr)
        else:
            # exp(-x) is infinite far below the physical support, whereas
            # exp(-exp(-x)) and its derivative both have the finite limit 0.
            # Evaluate that analytic limit directly rather than allowing inf*0.
            e, er = np.exp(np.minimum(-x, 700.0)), math.exp(min(-xr, 700.0))
            p, pr = np.exp(-e), math.exp(-er)
            dx = np.where(e >= math.exp(690.0), 0.0, p * e)
            dxr = 0.0 if er >= math.exp(690.0) else pr * er
        v, vr = 1 + a * p, 1 + a * pr
        q = np.log(v) - math.log(vr)
        dv = np.column_stack([p, -a * dx / h, -a * dx * x / h])
        dvr = np.array([pr, -a * dxr / h, -a * dxr * xr / h])
        return q, dv / v[:, None] - dvr[None, :] / vr
    raise ValueError(f"Unknown model: {model_id}")


def curve_coefficients(model_id: str, params: np.ndarray) -> np.ndarray:
    if model_id == "M04":
        return params[0] + np.r_[0.0, np.cumsum(softplus(params[1:]))]
    return params


def default_starts(model_id: str, g: np.ndarray, n_curve: int, meta: dict, limit: int = 10) -> list[np.ndarray]:
    if model_id == "M00":
        return [np.empty(0)]
    if model_id in ("M01", "M02", "M03"):
        return [np.zeros(n_curve)]
    if model_id == "M04":
        return [np.r_[0.0, np.full(n_curve - 1, -4.0)]]
    q = np.quantile(g, [0.10, 0.30, 0.50, 0.70, 0.90])
    span = max(float(np.max(g) - np.min(g)), 0.5)
    sd = max(float(np.std(g)), 0.25)
    widths = [max(0.08, 0.35 * sd), max(0.12, sd), max(0.2, 2 * sd)]
    if model_id == "M05":
        amps = [0.02, 0.15, 0.7]
        starts = [np.array([b, t, h]) for b in amps for t, h in zip(q[1:4], widths)]
        starts += [np.array([0.0, q[2], widths[1]])]
    elif model_id == "M06":
        amps = [0.1, 1.0, 8.0]
        starts = [np.array([a, max(0.05, t), s]) for a in amps for t, s in zip(q[1:4], [0.35, 0.8, 1.6])]
        starts += [np.array([0.0, max(0.05, q[2]), 0.8])]
    else:
        amps = [0.1, 1.0, 8.0]
        starts = [np.array([a, t, h]) for a in amps for t, h in zip(q[1:4], widths)]
        starts += [np.array([0.0, q[2], widths[1]])]
    return starts[:limit]


def nonlinear_bounds(model_id: str, g: np.ndarray, n_total: int) -> list[tuple[float | None, float | None]]:
    span = max(float(np.max(g) - np.min(g)), 0.5)
    lo, hi = float(np.min(g)), float(np.max(g))
    base = [(None, None)] * n_total
    if model_id == "M05":
        return base + [(0.0, 20.0), (lo - span, hi + span), (0.03, max(1.0, 3 * span))]
    if model_id == "M06":
        return base + [(0.0, 100.0), (0.02, max(1.0, 3 * hi + 2)), (0.04, 5.0)]
    return base + [(0.0, 100.0), (lo - span, hi + span), (0.03, max(1.0, 3 * span))]


@dataclass
class FitResult:
    model_id: str
    task: str
    status: str
    message: str
    objective: float | None
    iterations: int | None
    n_starts: int
    best_start: int | None
    elapsed_seconds: float
    theta: np.ndarray | None
    feature_means: np.ndarray | None
    feature_sds: np.ndarray | None
    gref: float | None
    curve_meta: dict | None
    hyper: dict
    boundary_flags: str
    identification: str


def prepare_design(frame: pd.DataFrame, control_cols: list[str], means=None, sds=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw = frame[control_cols].to_numpy(float)
    if means is None:
        means = np.nanmean(raw, axis=0)
        sds = np.nanstd(raw, axis=0, ddof=0)
        sds = np.where(sds < 1e-10, 1.0, sds)
    z = (raw - means) / sds
    return np.column_stack([np.ones(len(frame)), z]), np.asarray(means), np.asarray(sds)


def fit_model(
    train: pd.DataFrame,
    task: str,
    model_id: str,
    control_cols: list[str],
    hyper: dict | None = None,
    seed: int = SEED,
    warm_start: np.ndarray | None = None,
    start_limit: int | None = None,
    maxiter: int = 240,
) -> FitResult:
    start_clock = time.monotonic()
    hyper = dict(hyper or {})
    try:
        y = train["y"].to_numpy(float)
        g = train["gust_0h"].to_numpy(float)
        x, means, sds = prepare_design(train, control_cols)
        p = x.shape[1]
        gref = float(np.median(g))
        meta = {"g_mean": float(np.mean(g)), "g_sd": max(float(np.std(g)), 1e-8)}
        if model_id in ("M03", "M04"):
            n_basis = int(hyper.get("n_basis", 6))
            knots = knots_for(g, n_basis)
            meta.update({"knots": knots.tolist(), "n_basis": n_basis, "lambda": float(hyper.get("lambda", 0.01))})
            n_curve = len(knots) - 4
        elif model_id == "M00":
            n_curve = 0
        elif model_id == "M01":
            n_curve = 1
        elif model_id == "M02":
            n_curve = 2
        else:
            n_curve = 3

        alpha0 = math.log(max(float(np.mean(y)), 1e-8))
        base = np.r_[alpha0, np.zeros(p - 1)]
        starts = default_starts(model_id, g, n_curve, meta, limit=start_limit or 10)
        if warm_start is not None and len(warm_start) == p + n_curve:
            starts = [warm_start[p:]] + starts
        starts = starts[: (start_limit or 10)]
        ridge = 1e-7

        def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
            beta = theta[:p]
            cpars = theta[p:]
            q, jac = model_curve_q_jac(model_id, g, gref, cpars, meta)
            eta = x @ beta + q
            mu = finite_exp(eta)
            value, resid = loss_and_resid(y, mu, task)
            val = float(np.mean(value)) + ridge * float(np.dot(beta[1:], beta[1:]))
            grad_beta = x.T @ resid / len(y)
            grad_beta[1:] += 2 * ridge * beta[1:]
            grad_c = jac.T @ resid / len(y) if jac.shape[1] else np.empty(0)
            if model_id in ("M03", "M04"):
                c = curve_coefficients(model_id, cpars)
                pen, grad_c_actual = second_difference_penalty(c, float(meta["lambda"]))
                val += pen
                if model_id == "M03":
                    grad_c += grad_c_actual
                else:
                    mapped = np.empty_like(cpars)
                    mapped[0] = grad_c_actual.sum()
                    mapped[1:] = expit(cpars[1:]) * np.cumsum(grad_c_actual[::-1])[::-1][1:]
                    grad_c += mapped
            return val, np.r_[grad_beta, grad_c]

        bounds = nonlinear_bounds(model_id, g, p) if model_id in ("M05", "M06", "M07", "M08") else None
        attempts = []
        for number, cstart in enumerate(starts):
            theta0 = np.r_[base, cstart]
            result = minimize(
                objective,
                theta0,
                method="L-BFGS-B",
                jac=True,
                bounds=bounds,
                options={"maxiter": maxiter, "ftol": 1e-10, "gtol": 1e-6, "maxls": 30},
            )
            finite = bool(np.isfinite(result.fun) and np.all(np.isfinite(result.x)))
            attempts.append((float(result.fun) if finite else np.inf, number, result, finite))
        viable = [row for row in attempts if row[3]]
        if not viable:
            return FitResult(model_id, task, "failure", "no_finite_optimization_result", None, None, len(starts), None, time.monotonic()-start_clock, None, means, sds, gref, meta, hyper, "", "not_identified")
        _, best_no, best, _ = min(viable, key=lambda row: row[0])
        status = "success" if best.success else "warning_accepted"
        cpars = best.x[p:]
        flags, ident = identification_flags(model_id, cpars, meta, g)
        return FitResult(
            model_id, task, status, str(best.message), float(best.fun), int(best.nit), len(starts), int(best_no), time.monotonic()-start_clock,
            best.x, means, sds, gref, meta, hyper, flags, ident,
        )
    except Exception as exc:
        return FitResult(model_id, task, "failure", f"{type(exc).__name__}: {exc}", None, None, 0, None, time.monotonic()-start_clock, None, None, None, None, None, hyper, "", "not_identified")


def identification_flags(model_id: str, pars: np.ndarray, meta: dict, g: np.ndarray) -> tuple[str, str]:
    flags = []
    ident = "identified"
    if model_id in ("M05", "M06", "M07", "M08"):
        amp = float(pars[0])
        if amp < 0.01:
            flags.append("near_zero_amplitude")
            ident = "near_null_position_not_identified"
        bounds = nonlinear_bounds(model_id, g, 0)
        for j, (lo, hi) in enumerate(bounds):
            if lo is not None and abs(pars[j] - lo) <= max(1e-5, abs(lo)*1e-4):
                flags.append(f"parameter_{j}_at_lower_bound")
            if hi is not None and abs(pars[j] - hi) <= max(1e-5, abs(hi)*1e-4):
                flags.append(f"parameter_{j}_at_upper_bound")
    if model_id == "M04":
        c = curve_coefficients("M04", pars)
        if np.max(c) - np.min(c) < 0.01:
            flags.append("nearly_flat_monotone_spline")
            ident = "near_null_shape"
    return ";".join(flags) or "none", ident


def predict(fit: FitResult, frame: pd.DataFrame) -> np.ndarray:
    if fit.theta is None:
        return np.full(len(frame), np.nan)
    control_cols = fit.curve_meta["control_cols"]
    x, _, _ = prepare_design(frame, control_cols, fit.feature_means, fit.feature_sds)
    p = x.shape[1]
    q, _ = model_curve_q_jac(fit.model_id, frame["gust_0h"].to_numpy(float), fit.gref, fit.theta[p:], fit.curve_meta)
    return finite_exp(x @ fit.theta[:p] + q)


def fit_curve_ratio(fit: FitResult, grid: np.ndarray) -> np.ndarray:
    if fit.theta is None:
        return np.full(len(grid), np.nan)
    p = len(fit.feature_means) + 1
    q, _ = model_curve_q_jac(fit.model_id, grid, fit.gref, fit.theta[p:], fit.curve_meta)
    return np.exp(q)


def storm_protected_groups(frame: pd.DataFrame) -> tuple[pd.Series, dict]:
    """Fixed 14-day blocks, with all blocks touching a known storm window unioned."""
    base = pd.Timestamp("2021-04-01", tz="UTC")
    times = pd.to_datetime(frame["event_time_proxy_utc"], utc=True)
    block = ((times.dt.floor("D") - base).dt.total_seconds() // (14 * 86400)).astype(int)
    with STORMS.open(encoding="utf-8") as handle:
        windows = json.load(handle)
    parents: dict[int, int] = {}
    def find(x: int) -> int:
        parents.setdefault(x, x)
        if parents[x] != x:
            parents[x] = find(parents[x])
        return parents[x]
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parents[rb] = ra
    window_blocks = {}
    for name, spec in windows.items():
        start = pd.Timestamp(spec["start"])
        end = pd.Timestamp(spec["end_exclusive"]) - pd.Timedelta(nanoseconds=1)
        lo = int(math.floor((start - base).total_seconds() / (14 * 86400)))
        hi = int(math.floor((end - base).total_seconds() / (14 * 86400)))
        touched = list(range(lo, hi + 1))
        window_blocks[name] = touched
        for b in touched:
            find(b)
        for b in touched[1:]:
            union(touched[0], b)
    roots = {b: find(b) for b in list(parents)}
    def gid(b: int) -> str:
        return f"stormcluster_{roots[b]}" if b in roots else f"block_{b}"
    group = block.map(gid).astype("string")
    members = defaultdict(list)
    for b in sorted(set(block)):
        members[gid(int(b))].append(int(b))
    metadata = {
        "base_utc": base.isoformat(), "block_days": 14, "purge_hours": 48,
        "storm_windows": windows, "storm_window_blocks": window_blocks,
        "group_block_members": dict(members),
        "protocol_label": "time-block CV with known-storm protection and buffers",
    }
    return group, metadata


def balanced_group_folds(group: pd.Series, n_folds: int) -> dict[str, int]:
    sizes = group.value_counts().to_dict()
    loads = [0] * n_folds
    mapping = {}
    for gid, size in sorted(sizes.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        fold = int(np.argmin(loads))
        mapping[str(gid)] = fold
        loads[fold] += int(size)
    return mapping


def purge_mask(frame: pd.DataFrame, test_groups: set[str], grouping: dict) -> np.ndarray:
    base = pd.Timestamp(grouping["base_utc"])
    touched_blocks = []
    for gid in test_groups:
        touched_blocks.extend(grouping["group_block_members"].get(str(gid), []))
    times = pd.to_datetime(frame["event_time_proxy_utc"], utc=True)
    keepout = np.zeros(len(frame), dtype=bool)
    for block in sorted(set(touched_blocks)):
        start = base + pd.Timedelta(days=14 * int(block)) - pd.Timedelta(hours=48)
        end = base + pd.Timedelta(days=14 * (int(block) + 1)) + pd.Timedelta(hours=48)
        keepout |= ((times >= start) & (times < end)).to_numpy()
    return keepout


def sample_metrics(y: np.ndarray, mu: np.ndarray, task: str) -> dict:
    valid = np.isfinite(mu)
    y, mu = y[valid], mu[valid]
    err = mu - y
    sse = float(np.sum(err * err))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "n": int(len(y)), "mean_deviance": float(np.mean(deviance(y, mu, task))),
        "rmse": float(np.sqrt(np.mean(err * err))), "mae": float(np.mean(np.abs(err))),
        "mean_bias": float(np.mean(err)), "total_ratio": float(np.sum(mu) / np.sum(y)) if np.sum(y) else np.nan,
        "oof_r2": float(1 - sse / sst) if sst > 0 else np.nan,
    }


def group_se(values: pd.DataFrame, value_col: str) -> tuple[float, int]:
    grp = values.groupby("group_id", observed=True)[value_col].mean()
    n = len(grp)
    return (float(grp.std(ddof=1) / math.sqrt(n)) if n > 1 else np.nan, int(n))


def calibration_table(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (task, model), d in oof.groupby(["task_id", "model_id"], observed=True):
        try:
            bins = pd.qcut(d["mu_hat"], 10, duplicates="drop")
        except ValueError:
            bins = pd.Series(["single_bin"] * len(d), index=d.index)
        for label, part in d.groupby(bins, observed=True):
            pred_se, ng = group_se(part.assign(value=part.mu_hat), "value")
            obs_se, _ = group_se(part.assign(value=part.y), "value")
            rows.append({"task_id": task, "model_id": model, "prediction_bin": str(label), "n_events": len(part), "n_groups": ng,
                         "mean_prediction": part.mu_hat.mean(), "mean_observation": part.y.mean(),
                         "prediction_group_se": pred_se, "observation_group_se": obs_se})
    return pd.DataFrame(rows)


def gust_diagnostic_table(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (task, model), d in oof.groupby(["task_id", "model_id"], observed=True):
        bins = pd.qcut(d["gust_ms"], 10, duplicates="drop")
        for label, part in d.groupby(bins, observed=True):
            rows.append({"task_id": task, "model_id": model, "gust_bin": str(label), "n_events": len(part),
                         "n_groups": part.group_id.nunique(), "gust_mean_ms": part.gust_ms.mean(),
                         "observed_mean": part.y.mean(), "prediction_mean": part.mu_hat.mean(),
                         "residual_mean": (part.mu_hat-part.y).mean()})
    return pd.DataFrame(rows)


def tail_table(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (task, model), d in oof.groupby(["task_id", "model_id"], observed=True):
        gcut = d.gust_ms.quantile(.90)
        ycut = d.y.quantile(.95)
        for name, mask, kind in (("high_gust_p90", d.gust_ms >= gcut, "input_defined"), ("high_outcome_p95", d.y >= ycut, "outcome_conditioned")):
            q = d.loc[mask]
            rows.append({"task_id":task,"model_id":model,"subset":name,"selection_kind":kind,"threshold":gcut if name.startswith("high_gust") else ycut,
                         "n_events":len(q),"n_groups":q.group_id.nunique(),"mean_deviance":np.mean(deviance(q.y.to_numpy(float),q.mu_hat.to_numpy(float),task)),
                         "rmse":np.sqrt(np.mean((q.mu_hat-q.y)**2)),"bias":(q.mu_hat-q.y).mean()})
    return pd.DataFrame(rows)


def derivation_table(fit: FitResult, grid: np.ndarray) -> tuple[pd.DataFrame, dict]:
    ratio = fit_curve_ratio(fit, grid)
    derivative = np.gradient(ratio, grid)
    max_i = int(np.nanargmax(derivative)) if np.any(np.isfinite(derivative)) else 0
    lo, hi = np.nanmin(ratio), np.nanmax(ratio)
    dynamic = hi - lo
    summary = {"low_ratio_support": float(ratio[0]), "high_ratio_support": float(ratio[-1]), "max_slope": float(derivative[max_i]), "max_slope_gust_ms": float(grid[max_i])}
    if dynamic > 1e-8:
        for level in (0.1, 0.5, 0.9):
            ix = int(np.nanargmin(np.abs(ratio - (lo + level*dynamic))))
            summary[f"dynamic_{int(level*100)}pct_gust_ms"] = float(grid[ix])
    else:
        summary.update({"dynamic_10pct_gust_ms": np.nan, "dynamic_50pct_gust_ms": np.nan, "dynamic_90pct_gust_ms": np.nan})
    if fit.model_id == "M05":
        p = fit.theta[len(fit.feature_means)+1:]
        summary.update({"softplus_b":float(p[0]),"softplus_tau_ms":float(p[1]),"softplus_h_ms":float(p[2]),"softplus_high_gust_slope":float(p[0])})
    elif fit.model_id in ("M06","M07","M08"):
        p = fit.theta[len(fit.feature_means)+1:]
        summary.update({"amplitude":float(p[0]),"location_ms":float(p[1]),"width":float(p[2])})
    if fit.model_id == "M04":
        rising = grid[derivative > 1e-4]
        summary["monotone_rising_support_ms"] = f"{rising.min():.3f}–{rising.max():.3f}" if len(rising) else "none_detected"
    out = pd.DataFrame({"gust_ms":grid,"curve_ratio":ratio,"derivative_per_ms":derivative})
    return out, summary


def inner_tune(train: pd.DataFrame, task: str, model_id: str, controls: list[str], grouping: dict, seed: int) -> tuple[dict, list[dict]]:
    candidates = [{"n_basis":6,"lambda":0.005},{"n_basis":10,"lambda":0.005},{"n_basis":10,"lambda":0.05}]
    inner_map = balanced_group_folds(train.group_id.astype(str), 3)
    details = []
    for hp_no, hp in enumerate(candidates):
        scores = []
        for fold in range(3):
            validation = train.group_id.astype(str).map(inner_map).eq(fold).to_numpy()
            test_groups = set(train.loc[validation, "group_id"].astype(str))
            purged = purge_mask(train, test_groups, grouping)
            tr = train.loc[~validation & ~purged].copy()
            va = train.loc[validation].copy()
            fit = fit_model(tr, task, model_id, controls, hp, seed + hp_no*10+fold, start_limit=1, maxiter=140)
            if fit.curve_meta is not None:
                fit.curve_meta["control_cols"] = controls
            pred = predict(fit, va)
            score = float(np.mean(deviance(va.y.to_numpy(float), pred, task))) if fit.status != "failure" else np.inf
            scores.append(score)
            details.append({"task_id":task,"model_id":model_id,"hyper":json.dumps(hp,sort_keys=True),"inner_fold":fold,
                            "n_train":len(tr),"n_validation":len(va),"n_purged":int((~validation & purged).sum()),"mean_deviance":score,"fit_status":fit.status})
        avg = float(np.mean(scores))
        for item in details[-3:]: item["inner_mean_deviance"] = avg
    avg_by = [(np.mean([r["mean_deviance"] for r in details if r["hyper"] == json.dumps(hp,sort_keys=True)]), hp) for hp in candidates]
    best = min(avg_by, key=lambda x:x[0])[1]
    return best, details


MODEL_IDS = [f"M{i:02d}" for i in range(9)]
MODEL_NAMES = {"M00":"no gust","M01":"linear predictor","M02":"quadratic predictor","M03":"free cubic spline","M04":"monotone cubic spline","M05":"Softplus","M06":"lognormal CDF","M07":"Logistic","M08":"Gompertz"}


def run_outer_task(data: pd.DataFrame, task: str, controls: list[str], fold_map: dict, grouping: dict) -> tuple[pd.DataFrame, list[dict], list[dict], list[dict]]:
    all_oof, fits, fold_rows, tuning_rows = [], [], [], []
    data = data.copy()
    data["outer_fold"] = data.group_id.astype(str).map(fold_map).astype(int)
    for model_no, model_id in enumerate(MODEL_IDS):
        log(f"{task} {model_id}: outer OOF starts")
        for fold in range(5):
            validation = data.outer_fold.eq(fold).to_numpy()
            test_groups = set(data.loc[validation, "group_id"].astype(str))
            purged = purge_mask(data, test_groups, grouping)
            training = data.loc[~validation & ~purged].copy()
            testing = data.loc[validation].copy()
            hyper = {}
            if model_id in ("M03", "M04"):
                hyper, details = inner_tune(training, task, model_id, controls, grouping, SEED + model_no*100 + fold)
                tuning_rows.extend(details)
            fit = fit_model(training, task, model_id, controls, hyper, SEED+model_no*100+fold)
            if fit.curve_meta is not None:
                fit.curve_meta["control_cols"] = controls
            pred = predict(fit, testing)
            valid = np.isfinite(pred)
            met = sample_metrics(testing.y.to_numpy(float)[valid], pred[valid], task) if valid.any() else {"n":0,"mean_deviance":np.nan,"rmse":np.nan,"mae":np.nan,"mean_bias":np.nan,"total_ratio":np.nan,"oof_r2":np.nan}
            all_oof.append(pd.DataFrame({"task_id":task,"model_id":model_id,"event_id":testing.event_id.astype(str),"group_id":testing.group_id.astype(str),"outer_fold":fold,
                                         "y":testing.y.to_numpy(float),"mu_hat":pred,"gust_ms":testing.gust_0h.to_numpy(float),"fit_status":fit.status,"support_outside_training":(testing.gust_0h < training.gust_0h.min()).to_numpy() | (testing.gust_0h > training.gust_0h.max()).to_numpy()}))
            fits.append({**fit_summary(fit),"fold":fold,"n_train":len(training),"n_test":len(testing),"n_purged":int((~validation & purged).sum())})
            fold_rows.append({"task_id":task,"model_id":model_id,"fold":fold,"n_train":len(training),"n_test":len(testing),"n_purged":int((~validation & purged).sum()),"n_test_groups":len(test_groups),**met,"fit_status":fit.status})
    return pd.concat(all_oof, ignore_index=True), fits, fold_rows, tuning_rows


def fit_summary(fit: FitResult) -> dict:
    return {"task_id":fit.task,"model_id":fit.model_id,"fit_status":fit.status,"message":fit.message,"objective":fit.objective,"iterations":fit.iterations,"n_starts":fit.n_starts,"best_start":fit.best_start,"elapsed_seconds":fit.elapsed_seconds,"g_ref_ms":fit.gref,"hyper":json.dumps(fit.hyper,sort_keys=True),"boundary_flags":fit.boundary_flags,"identification":fit.identification}


def full_models(data: pd.DataFrame, task: str, controls: list[str], fits: list[dict]) -> tuple[dict[str, FitResult], list[dict]]:
    output, rows = {}, []
    for model_id in MODEL_IDS:
        prior = [x for x in fits if x["task_id"] == task and x["model_id"] == model_id]
        if model_id in ("M03", "M04"):
            hps = [x["hyper"] for x in prior]
            hyper = json.loads(Counter(hps).most_common(1)[0][0]) if hps else {"n_basis":6,"lambda":0.005}
        else:
            hyper = {}
        fit = fit_model(data, task, model_id, controls, hyper, SEED+9000, maxiter=360)
        if fit.curve_meta is not None:
            fit.curve_meta["control_cols"] = controls
        output[model_id] = fit
        rows.append({**fit_summary(fit),"fold":"full","n_train":len(data),"n_test":0,"n_purged":0})
    return output, rows


def paired_bootstrap(oof: pd.DataFrame, task: str, n_boot: int=1000) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = oof.loc[oof.task_id.eq(task)].copy()
    piv = d.pivot(index="event_id", columns="model_id", values="mu_hat")
    core = d.drop_duplicates("event_id").set_index("event_id")[["y","group_id"]].join(piv, how="inner")
    groups = core.group_id.astype(str).unique()
    group_positions = {g: np.flatnonzero(core.group_id.astype(str).to_numpy() == g) for g in groups}
    rng = np.random.default_rng(SEED + {"E":1,"R":2,"R_C":3}[task])
    records = []
    for b in range(n_boot):
        drawn = rng.choice(groups, size=len(groups), replace=True)
        idx = np.concatenate([group_positions[g] for g in drawn])
        y = core.y.to_numpy(float)[idx]
        base = core["M00"].to_numpy(float)[idx]
        base_metrics = sample_metrics(y, base, task)
        for model_id in MODEL_IDS:
            mu = core[model_id].to_numpy(float)[idx]
            met = sample_metrics(y, mu, task)
            records.append({"task_id":task,"bootstrap":b,"model_id":model_id,"delta_deviance_vs_M00":met["mean_deviance"]-base_metrics["mean_deviance"],"delta_rmse_vs_M00":met["rmse"]-base_metrics["rmse"],"delta_r2_vs_M00":met["oof_r2"]-base_metrics["oof_r2"]})
    raw = pd.DataFrame(records)
    summary = raw.groupby(["task_id","model_id"], observed=True).agg(
        deviance_delta_mean=("delta_deviance_vs_M00","mean"), deviance_delta_ci_low=("delta_deviance_vs_M00",lambda x:np.quantile(x,.025)), deviance_delta_ci_high=("delta_deviance_vs_M00",lambda x:np.quantile(x,.975)),
        rmse_delta_mean=("delta_rmse_vs_M00","mean"), rmse_delta_ci_low=("delta_rmse_vs_M00",lambda x:np.quantile(x,.025)), rmse_delta_ci_high=("delta_rmse_vs_M00",lambda x:np.quantile(x,.975)),
        r2_delta_mean=("delta_r2_vs_M00","mean"), r2_delta_ci_low=("delta_r2_vs_M00",lambda x:np.quantile(x,.025)), r2_delta_ci_high=("delta_r2_vs_M00",lambda x:np.quantile(x,.975)),
    ).reset_index()
    return raw, summary


def bootstrap_refits(data: pd.DataFrame, task: str, controls: list[str], full: dict[str, FitResult], selected: list[str], grid: np.ndarray, reps: int=200) -> pd.DataFrame:
    groups = data.group_id.astype(str).unique()
    pos = {g: np.flatnonzero(data.group_id.astype(str).to_numpy() == g) for g in groups}
    rng = np.random.default_rng(SEED + {"E":101,"R":202,"R_C":303}[task])
    records = []
    checkpoint = EVIDENCE / f"bootstrap_refit_{task}_checkpoint.csv"
    for model_id in selected:
        log(f"{task} {model_id}: 200 group bootstrap refits begin")
        base = full[model_id]
        for b in range(reps):
            drawn = rng.choice(groups, size=len(groups), replace=True)
            idx = np.concatenate([pos[g] for g in drawn])
            boot = data.iloc[idx].copy()
            fit = fit_model(boot, task, model_id, controls, base.hyper, seed=SEED+b, warm_start=base.theta, start_limit=2, maxiter=130)
            if fit.curve_meta is not None:
                fit.curve_meta["control_cols"] = controls
            row = {"task_id":task,"model_id":model_id,"bootstrap":b,"fit_status":fit.status,"message":fit.message,"objective":fit.objective,"boundary_flags":fit.boundary_flags,"identification":fit.identification,"n_events_with_multiplicity":len(boot),"n_unique_groups_drawn":len(set(drawn))}
            if fit.theta is not None:
                curve, derived = derivation_table(fit, grid)
                row.update(derived)
                for g0 in (10.0,20.0,30.0,40.0,50.0):
                    row[f"ratio_at_{int(g0)}ms"] = float(fit_curve_ratio(fit,np.array([g0]))[0])
                p = len(fit.feature_means)+1
                for j, v in enumerate(fit.theta[p:]): row[f"curve_parameter_{j}"] = float(v)
            records.append(row)
            if (b + 1) % 25 == 0:
                pd.DataFrame(records).to_csv(checkpoint, index=False)
                log(f"{task} {model_id}: bootstrap checkpoint {b+1}/{reps}")
    result = pd.DataFrame(records)
    result.to_csv(EVIDENCE / f"bootstrap_refit_{task}.csv", index=False)
    return result


def plot_leaderboard(leader: pd.DataFrame, task: str) -> None:
    d = leader.loc[leader.task_id.eq(task)].sort_values("mean_deviance")
    plt.figure(figsize=(9,5))
    vals = d.mean_deviance - d.loc[d.model_id.eq("M00"),"mean_deviance"].iloc[0]
    colors = ["#2b8cbe" if x < 0 else "#bdbdbd" for x in vals]
    plt.bar(d.model_id, vals, color=colors)
    plt.axhline(0,color="black",lw=.8); plt.ylabel("OOF deviance difference vs M00 (lower is better)")
    plt.title(f"{task}: pre-registered candidate comparison")
    plt.tight_layout()
    for suffix in ("png","svg"): plt.savefig(FIGURES / f"leaderboard_{task}.{suffix}", dpi=180)
    plt.close()


def plot_curves(curves: pd.DataFrame, task: str, derivative: bool=False) -> None:
    fig, axes = plt.subplots(3,3,figsize=(13,10),sharex=True)
    field = "derivative_per_ms" if derivative else "curve_ratio"
    for ax, model_id in zip(axes.flat, MODEL_IDS):
        d = curves.loc[(curves.task_id.eq(task)) & (curves.model_id.eq(model_id))]
        ax.plot(d.gust_ms,d[field],color="#2166ac",lw=1.8)
        ax.axhline(0 if derivative else 1,color="black",lw=.6,ls="--")
        ax.set_title(f"{model_id} {MODEL_NAMES[model_id]}",fontsize=9)
        ax.grid(alpha=.2)
    fig.supxlabel("gust (m/s)"); fig.supylabel("d ratio/d gust" if derivative else "mean ratio, r(g)")
    fig.suptitle(f"{task}: {'curve derivative' if derivative else 'reference-normalized curve'}")
    fig.tight_layout()
    stem = f"derivative_{task}" if derivative else f"curves_{task}"
    for suffix in ("png","svg"): fig.savefig(FIGURES / f"{stem}.{suffix}", dpi=180)
    plt.close(fig)


def plot_standardized_curves(curves: pd.DataFrame, task: str) -> None:
    """Plot the exact population-standardized mean, separately from r(g)."""
    fig, axes = plt.subplots(3,3,figsize=(13,10),sharex=True)
    for ax, model_id in zip(axes.flat, MODEL_IDS):
        d = curves.loc[(curves.task_id.eq(task)) & (curves.model_id.eq(model_id))]
        ax.plot(d.gust_ms, d.standardized_mean, color="#2166ac", lw=1.8)
        ax.set_title(f"{model_id} {MODEL_NAMES[model_id]}",fontsize=9)
        ax.grid(alpha=.2)
    fig.supxlabel("gust (m/s)")
    fig.supylabel("standardized fitted conditional mean")
    fig.suptitle(f"{task}: population-standardized mean curve")
    fig.tight_layout()
    for suffix in ("png","svg"): fig.savefig(FIGURES / f"standardized_curves_{task}.{suffix}", dpi=180)
    plt.close(fig)


def plot_support(oof: pd.DataFrame, task: str) -> None:
    """Observed gust support, retaining both event and independent group counts."""
    d = oof.loc[(oof.task_id.eq(task)) & (oof.model_id.eq("M00"))].copy()
    edges = np.linspace(d.gust_ms.min(), d.gust_ms.max(), 16)
    d["bin"] = pd.cut(d.gust_ms, edges, include_lowest=True)
    tab = d.groupby("bin", observed=True).agg(events=("event_id","size"), groups=("group_id","nunique"), gust_mid=("gust_ms","mean")).reset_index()
    fig, ax1 = plt.subplots(figsize=(10,4.5))
    width = (edges[1]-edges[0])*.8
    ax1.bar(tab.gust_mid, tab.events, width=width, color="#74a9cf", label="events")
    ax1.set_ylabel("events")
    ax1.set_xlabel("gust (m/s)")
    ax2=ax1.twinx()
    ax2.plot(tab.gust_mid, tab.groups, "o-", color="#b2182b", label="independent groups")
    ax2.set_ylabel("independent groups")
    ax1.set_title(f"{task}: observed gust support (15 equal-width bins)")
    ax1.grid(axis="y",alpha=.2)
    handles, labels = [], []
    for ax in (ax1,ax2):
        h,l=ax.get_legend_handles_labels();handles+=h;labels+=l
    ax1.legend(handles,labels,loc="upper right")
    fig.tight_layout()
    for suffix in ("png","svg"): fig.savefig(FIGURES/f"gust_support_{task}.{suffix}",dpi=180)
    plt.close(fig)


def plot_calibration(cal: pd.DataFrame, task: str) -> None:
    fig, axes = plt.subplots(3,3,figsize=(13,10))
    for ax, model_id in zip(axes.flat, MODEL_IDS):
        d=cal.loc[(cal.task_id.eq(task)) & (cal.model_id.eq(model_id))]
        ax.errorbar(d.mean_prediction,d.mean_observation,yerr=d.observation_group_se,fmt="o",ms=3,color="#b2182b")
        end=max(d.mean_prediction.max(),d.mean_observation.max()) if len(d) else 1
        ax.plot([0,end],[0,end],"k--",lw=.7); ax.set_title(model_id); ax.grid(alpha=.2)
    fig.supxlabel("mean OOF prediction");fig.supylabel("mean observed outcome (group SE bars)");fig.suptitle(f"{task}: decile calibration")
    fig.tight_layout()
    for suffix in ("png","svg"): fig.savefig(FIGURES / f"calibration_{task}.{suffix}", dpi=180)
    plt.close(fig)


def plot_gust_diagnostics(gust: pd.DataFrame, task: str, leader: pd.DataFrame) -> None:
    winners = leader.loc[leader.task_id.eq(task)].sort_values("mean_deviance").head(3).model_id.tolist()
    fig, axes=plt.subplots(1,len(winners),figsize=(5*len(winners),4),sharey=True)
    axes=np.atleast_1d(axes)
    for ax, model_id in zip(axes,winners):
        d=gust.loc[(gust.task_id.eq(task)) & (gust.model_id.eq(model_id))]
        ax.plot(d.gust_mean_ms,d.observed_mean,"o-",label="observed")
        ax.plot(d.gust_mean_ms,d.prediction_mean,"s-",label="OOF mean")
        ax.set_title(model_id);ax.set_xlabel("gust (m/s)");ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[0].set_ylabel("raw-scale outcome mean")
    fig.suptitle(f"{task}: descriptive gust-bin diagnostic (top three by OOF loss)")
    fig.tight_layout()
    for suffix in ("png","svg"):fig.savefig(FIGURES/f"gust_diagnostic_{task}.{suffix}",dpi=180)
    plt.close(fig)


def write_experiment_documents(manifest: dict, controls: list[str]) -> None:
    (ROOT / "EXPERIMENT_CONTRACT.md").write_text(f"""# X01 experiment contract\n\nThis independent run is frozen before any candidate leaderboard is read. It uses the copied event snapshot in `frozen_sources/input/R02_event_master.parquet` (SHA-256 `{manifest['input_sha256']}`) and never writes outside this run directory.\n\n## Estimands and samples\n\n- **E:** recorded event-level arithmetic mean customers, `C_id_formula`, including valid zeros, Poisson working-mean loss.\n- **R:** recorded event-level arithmetic mean recovery span in hours, `D_id_formula > 0`, Gamma-type working-mean loss.\n- **R_C:** R conditional on final `log1p(C)` and its square; it is an after-the-event conditional analysis, not a planning or causal estimand.\n\nAll models within task use the same rows, controls, groups and folds. Controls are: `{', '.join(controls)}`. The common new specification has pressure as a main effect and **no gust × pressure interaction**.\n\n## Model and scoring contract\n\nThe shared mean model is `mu=exp(alpha+x gamma) r(g)`, with the training-fold median gust as `g_ref` and `r(g_ref)=1`. E uses `mu-y log(mu)`; R/R_C use `log(mu)+y/mu`. The primary score is the corresponding mean OOF deviance, then raw-scale RMSE, MAE, bias, total prediction/observation and pooled OOF R². These are working mean losses, not a claim that the whole outcome distribution is Poisson or Gamma; no AIC or likelihood-ratio inference is used.\n\nM00–M08 are the nine formulas specified in the frozen X01 instruction. The CDF families use baseline 1 plus an overall intercept, preventing `a`, `A` and intercept scale non-identifiability. Baseline 1 is a parameterization device, not one customer or one hour. M03 is an unrestricted cubic B-spline; M04 is a cubic B-spline with nondecreasing coefficients, which guarantees a nondecreasing spline. M03/M04 tune only `n_basis in {{6,10}}` and smoothing penalty `lambda in {{0.005,0.05}}` using inner protected group folds. Nonlinear candidates use no more than ten deterministic starts and pre-registered finite parameter bounds.\n\n## Validation and uncertainty\n\nOuter evaluation uses five deterministic, balanced folds of 14-day UTC blocks. Blocks touching the same named storm window are unioned. Training observations within 48 hours of any test block are purged. It is therefore called **time-block CV with known-storm protection and buffers**, not full weather-process isolation or a future confirmation set. Inner selection uses three grouped folds with the same purge rule.\n\nA 1,000-resample paired group bootstrap is conditional on fixed OOF predictions. Two competitive curve candidates per task receive 200 group-bootstrap refits with the full-data selected spline hyperparameter held fixed. Neither procedure includes all tuning or model-selection uncertainty.\n""",encoding="utf-8")
    run_config = {"run_id":ROOT.name,"seed":SEED,"outer_folds":5,"inner_folds":3,"block_days":14,"purge_hours":48,"bootstrap_oof":1000,"bootstrap_refits":200,"controls":controls,"models":MODEL_NAMES,"input_sha256":manifest['input_sha256'],"completed_at_start":"X01-A contract frozen before fitting"}
    (ROOT / "run_config.yaml").write_text("\n".join(f"{k}: {json.dumps(v,ensure_ascii=False)}" for k,v in run_config.items())+"\n",encoding="utf-8")
    (ROOT / "DECISION_LOG.md").write_text("# Decision log\n\n- 2026-09-06: Created new independent X01 run inside `test`; no R00–R05 repair artifact is edited.\n- 2026-09-06: Froze the R02 event snapshot after hash verification; all model reads use the copy.\n- 2026-09-06: Chose the fixed 14-day UTC block protocol with named-window union and 48-hour purge because no validated full weather-process ID is present in the frozen input contract.\n- 2026-09-06: Pre-registered direct raw-scale conditional mean losses and removed free gust×pressure interaction from every candidate as instructed.\n",encoding="utf-8")


def write_reports(preflight: dict, leader: pd.DataFrame, fits: pd.DataFrame, bootstrap: pd.DataFrame, curvesummary: pd.DataFrame, selected: dict, stories: list[str]) -> None:
    def markdown_table(frame: pd.DataFrame) -> str:
        """Render the compact reports without an optional package dependency."""
        columns = list(frame.columns)
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        for row in frame.itertuples(index=False, name=None):
            lines.append("| " + " | ".join(str(value) for value in row) + " |")
        return "\n".join(lines)
    top = []
    for task in ("E","R","R_C"):
        d=leader.loc[leader.task_id.eq(task)].sort_values("mean_deviance")
        cols=["model_id","mean_deviance","rmse","mae","oof_r2","total_ratio","oof_coverage","recommendation"]
        top.append(f"\n### {task}\n\n"+markdown_table(d[cols].head(5).round(6)))
    report=f"""# X01 候选曲线比较报告\n\n## 状态\n\n本报告是独立探索的实际计算结果，不回写原稿、Word、图表或MR/CL台账。输入是本运行目录内的冻结事件快照；主分析人口没有按结果上尾截断。阵风产品和历史天气模型仍受冻结输入来源说明的限制，因此结论只针对已记录事件、该阵风产品和本人口。\n\n## 方法\n\n三个任务均拟合原尺度条件算术均值。E 的响应为 `C_id_formula`（含零）；R 为正的 `D_id_formula`；R_C 在 R 的共同控制上加入最终 `log1p(C)` 及平方。比较仅改变阵风函数，压力为主效应且不含阵风×压力交互。五折时间块CV以命名风暴窗口保护、48小时缓冲；它不是完全隔离所有天气过程，也不是未接触确认集。\n\n每个候选的主排名按合并OOF工作偏差（越小越好），再报告原尺度误差与校准。工作损失用于均值比较，不能解释为已验证的完整Poisson/Gamma分布、AIC或预测概率区间。\n\n## 输入和资格\n\n```json\n{json.dumps(preflight,ensure_ascii=False,indent=2)}\n```\n\n## 排行榜\n"""+"\n".join(top)+"""\n\n完整数值位于 `tables/model_leaderboard.csv`；所有27个任务—模型组合及外折状态在 `tables/fit_diagnostics.csv`。候选发生失败或警告时，排行榜保留状态且不以全样本预测填补OOF。\n\n## 曲线、支持与解释\n\n每个任务的九条参考归一化曲线和数值一阶导数在 `figures/curves_*.png`、`figures/derivative_*.png`，逐点数据在 `evidence/curve_data.parquet`，参数/边界/派生量在 `tables/shape_parameters.csv`。标准化平均曲线按全任务人口逐条替换阵风并平均；在没有阵风交互的共同均值模型中，它与参考归一化曲线具有相同形状，但水平会随参考人口改变。曲线外推部分没有用于任何阈值或平台主张。\n\nM04不下降来自形状约束本身；其支持来自它相对于M03和M00的OOF表现和重拟合稳定性。M06–M08的渐近平台是函数性质，只有当高风速支持和重拟合均稳定时才可称数据支持的平台。M05、M01、M02没有有限上平台，报告中不会为它们制造饱和风速。\n\n## 不确定性\n\n`tables/paired_comparisons.csv`给出按验证群组的1,000次配对OOF重抽样区间，条件于已有OOF预测。`evidence/bootstrap_refit_*.csv`保存每个任务两条入围曲线的200次群组重拟合（平滑参数固定），包括失败和边界状态。这些区间不包括数据定义、调参和在九条曲线中选择胜者的全部不确定性。\n\n## 暂定建议\n\n"""+"\n".join(f"- **{task}**：暂定短名单 `{', '.join(models)}`；依据为预设OOF偏差、覆盖、校准和重拟合记录，非自动的论文选型。" for task,models in selected.items())+"""\n\n工程上，结果反映特定历史记录下阵风与已记录客户影响/恢复跨度的条件关联；不识别资产失效概率、物理损伤阈值、因果机制或总体网络风险。R_C尤其使用了最终客户数，只能作为事后条件分析。\n\n## 证据与限制\n\n- 高风速和结果尾部诊断在 `tables/tail_diagnostics.csv`，其中结果p95行已明确标记为结果条件描述。\n- 校准分箱含独立群组数和群组均值标准误，见 `tables/calibration_bins.csv`。\n- 观察到的高风速平缓、参数化渐近平台和数据识别出平台高度在概念上不同；不要以任何单一S形的公式平台替代数据证据。\n- 当前区域协变量中保留了已有的历史代理标记；本探索没有重建LSOA指标，也没有把区域差异解释为因果。\n"""
    (ROOT / "X01_REPORT.md").write_text(report,encoding="utf-8")
    story="""# RESEARCH STORY LOG\n\n本文件记录X01对一个**新**研究问题的启示；它不是对原论文的修改建议，也不把条件关联提升为机制证据。\n\n## 起点与强制假设\n\n- 研究问题由“单一阵风项是否显著”转为：在共同控制和相同记录事件人口下，哪些可复核的单变量均值形状能预测客户影响与恢复跨度，以及数据是否区分这些形状。证据：`EXPERIMENT_CONTRACT.md`、`tables/model_leaderboard.csv`。\n- 单调、S形和平台是模型假设；支持它们的证据只能来自与无阵风/自由曲线的OOF比较、支持密度和重拟合稳定性。证据：`figures/curves_*.png`、`figures/derivative_*.png`、`tables/shape_parameters.csv`、`evidence/bootstrap_refit_*.csv`。\n- 三个任务的区别是研究设计的一部分：E为记录客户影响，R为未条件化恢复跨度，R_C是给定最终客户规模的事后恢复分析。它们不能被合并为一个因果链。证据：`EXPERIMENT_CONTRACT.md`、`tables/task_sample_flow.csv`。\n\n## 实际发现如何改变论证\n\n"""+"\n".join(stories)+"""\n\n## 可行章节组织\n\n1. **问题与边界**：记录事件、阵风产品和条件均值的研究对象；明确不是资产失效概率。\n2. **数据合同与依赖保护**：身份、UTC代表时间、事件资格、14日时间块与命名风暴保护。\n3. **形状竞争方法**：共享控制、九条预先列出的函数、原尺度工作损失，避免混排log-OLS R²。\n4. **结果**：按E、R、R_C分别报告OOF排名、校准、曲线和支持范围。\n5. **不确定性和工程含义**：群组重抽样、缺乏平台识别时的保守解释。\n6. **讨论**：事件记录选择、天气过程依赖、地区代理和历史回顾性评价的限制；提出更强过程分组和独立时期验证。\n\n## 当前不支持的主张\n\n- 不能称任何位置参数为物理损伤阈值，或称渐近值为总体网络饱和。\n- 不能将R_C的客户条件项解释为规划阶段可用的因果效应。\n- 不能把时间块OOF说成完全独立的未来或未接触验证。\n- 不能把观测高风速样本少时的平缓误读为证实平台。\n"""
    (ROOT / "RESEARCH_STORY_LOG.md").write_text(story,encoding="utf-8")

    statuses=fits.groupby(["task_id","model_id"],observed=True).fit_status.agg(lambda x:",".join(sorted(set(x)))).unstack(0)
    coverage=[]
    for m in MODEL_IDS:
        coverage.append("| "+m+" | "+" | ".join(statuses.loc[m,t] if m in statuses.index and t in statuses.columns else "not run" for t in ("E","R","R_C"))+" | see `tables/fit_diagnostics.csv` |")
    return_md=f"""# RETURN_TO_CHATGPT_X01\n\n## 1. 状态与输入\n\n- run_id / 配置版本：`{ROOT.name}` / X01-v1.0。\n- 阶段完成情况：X01-A–X01-F均已实际执行；计算产物已验收。\n- 输入快照：`frozen_sources/input/R02_event_master.parquet`，SHA-256 `{preflight['input_sha256']}`，R02输入manifest标记为已完成事件快照；截止为2026-09-06。\n- 人口：来源有效事件人口，未按结果p99截尾；仍受历史天气产品、UTC代理时间和区域代理的已记录限制。\n- E / R / R_C：样本、日期、事件数和验证群组见 `tables/task_sample_flow.csv`、`tables/split_summary.csv`。\n- 与Claude修复目录：完全隔离；本run只写入`test/research_exploration/shape_models/X01/{ROOT.name}`。\n- 复现：见`README.md`的命令（脚本只读取本run冻结副本）。\n\n## 2. 实际评价协议\n\n- 直接原尺度条件均值、固定共同控制和无gust×pressure交互；详情`EXPERIMENT_CONTRACT.md`。\n- E为Poisson工作均值损失；R/R_C为Gamma型工作均值损失，非完整分布假设。\n- 五折14日时间块、命名风暴合并、48h purge；M03/M04在外层训练内三折调参。\n- 回顾性评价，历史数据可能已被此前研究接触；不称确认性未来测试。\n- 主指标为合并OOF平均工作偏差，未因结果改动，见`tables/model_leaderboard.csv`。\n\n## 3. 候选覆盖\n\n| 模型 | E状态 | R状态 | R_C状态 | 失败或限制 |\n| --- | --- | --- | --- | --- |\n"""+"\n".join(coverage)+"""\n\n## 4. 各任务短名单\n\n"""+"\n".join(top)+"""\n\n完整排行榜：`tables/model_leaderboard.csv`；校准：`tables/calibration_bins.csv`；OOF覆盖：`predictions/oof_predictions.parquet`。\n\n## 5. 关键问题的证据回答\n\n1. 阵风的增量信息：以每个模型相对M00的OOF偏差、RMSE和R²差判断，见`tables/model_leaderboard.csv`与`tables/paired_comparisons.csv`。\n2. 自由曲线下降：直接检查M03曲线和导数，连同每个风速箱的事件/群组数，见`figures/curves_*.png`、`figures/derivative_*.png`、`tables/curve_support.csv`。\n3. 约束是否有代价：M04对M03/M00的共同OOF样本差与bootstrap，见`tables/model_leaderboard.csv`、`evidence/bootstrap_refit_*.csv`。\n4. 高风速平台：区分观测段、函数渐近和重拟合稳定性，证据为`tables/shape_parameters.csv`、`tables/tail_diagnostics.csv`。\n5. 位置/平台稳定性：参数边界与重拟合分布保存在`tables/shape_parameters.csv`、`evidence/bootstrap_refit_*.csv`。\n6. 三结果是否相同：逐任务独立短名单与曲线并列在`tables/model_leaderboard.csv`、`figures/curves_*.png`。\n7. 尾部敏感性：输入p90与结果p95诊断（后者明示结果条件）在`tables/tail_diagnostics.csv`。\n\n## 6. 不确定性\n\n- OOF配对重抽样：每任务1000次，单位为外层验证群组，结果`tables/paired_comparisons.csv`。\n- 入围曲线：每任务两候选、各200次群组重拟合，固定全数据选中的样条超参数；失败不删除，见`evidence/bootstrap_refit_*.csv`。\n- 未包含数据定义、所有调参、模型选择和不完整过程识别的不确定性。\n- 是否有明确胜者需作者结合区间、曲线支持和工程目的判断；本run只给暂定短名单。\n\n## 7. 暂定推荐与工程解释\n\n"""+"\n".join(f"- {task}首选/备选候选：`{', '.join(models)}`，以预设OOF损失、覆盖、校准和稳定性排序；非自动论文选型。" for task,models in selected.items())+"""\n\n- 曲线的横轴单位为m/s，纵轴为相对条件均值；其绝对水平取决于控制场景，不能直接解作阈值、机制或总体失效概率。\n- 研究故事的具体启示和证据绑定：`RESEARCH_STORY_LOG.md`。\n\n## 8. 交付与未完成项\n\n- 报告：`X01_REPORT.md`；代码：`src/x01_run.py`；表/图/OOF/曲线：`tables/`、`figures/`、`predictions/`、`evidence/`；包：`RETURN_PACKAGE_X01.zip`。\n- 不修改Word，不启动R05/V/W，不回写主论文或MR。\n- 需要作者判断：各任务最终采用哪一候选；是否接受UTC代理、区域代理和带命名风暴保护的时间块CV作为后续研究基础。\n"""
    (ROOT / "RETURN_TO_CHATGPT_X01.md").write_text(return_md,encoding="utf-8")


def main() -> None:
    started = time.monotonic()
    log("X01 starts; reading only frozen snapshot")
    manifest = {"run_id":ROOT.name,"input_path":str(INPUT.relative_to(ROOT)),"input_sha256":sha256(INPUT),"input_bytes":INPUT.stat().st_size,"seed":SEED,
                "python":sys.version,"platform":platform.platform(),"packages":{}}
    import scipy, matplotlib as mpl
    manifest["packages"]={"numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__,"matplotlib":mpl.__version__}
    dump_json(ROOT/"DATA_MANIFEST.json",manifest)
    controls = ["pressure_msl_0h","temperature_0h","precipitation_24h_sum","log_population","income_deprivation_rate","deprivation_gap_pct","morans_i","urban_binary","calendar_sin","calendar_cos","calendar_trend","cause_asset"]
    write_experiment_documents(manifest,controls)
    raw=pd.read_parquet(INPUT)
    raw["event_time_proxy_utc"]=pd.to_datetime(raw["event_time_proxy_utc"],utc=True)
    raw["event_id"]=raw["unique_identifier"].astype("string")
    raw["calendar_sin"]=np.sin(2*np.pi*raw.event_time_proxy_utc.dt.dayofyear/365.25)
    raw["calendar_cos"]=np.cos(2*np.pi*raw.event_time_proxy_utc.dt.dayofyear/365.25)
    raw["calendar_trend"]=(raw.event_time_proxy_utc-pd.Timestamp("2021-04-01",tz="UTC")).dt.total_seconds()/86400
    raw["cause_asset"]=(raw["cause_group_event"].astype(str).str.lower()=="asset").astype(float)
    required=["event_id","event_time_proxy_utc","gust_0h","C_id_formula","D_id_formula","candidate_main_E0","candidate_main_R0c","LAD21CD",*controls]
    missing=[x for x in required if x not in raw.columns]
    if missing: raise RuntimeError(f"required_columns_missing:{missing}")
    base=raw.loc[raw.candidate_main_E0.fillna(False)].copy()
    base["group_id"], grouping=storm_protected_groups(base)
    key_complete=base[required].notna().all(axis=1)
    base_clean=base.loc[key_complete].copy()
    tasks={
        "E":base_clean.loc[base_clean.C_id_formula.astype(float).ge(0)].copy(),
        "R":base_clean.loc[base_clean.D_id_formula.astype(float).gt(0)].copy(),
        "R_C":base_clean.loc[base_clean.D_id_formula.astype(float).gt(0) & base_clean.C_id_formula.astype(float).ge(0)].copy(),
    }
    for task,d in tasks.items():
        d["y"] = d.C_id_formula.astype(float) if task=="E" else d.D_id_formula.astype(float)
        if task=="R_C":
            d["log1p_C"]=np.log1p(d.C_id_formula.astype(float));d["log1p_C_sq"]=d.log1p_C**2
        elif task=="R": pass
        if task=="R_C":
            task_controls=controls+["log1p_C","log1p_C_sq"]
        else: task_controls=controls
        tasks[task]=(d,task_controls)
    group_map=balanced_group_folds(base_clean.group_id.astype(str),5)
    split_rows=[]
    for task,(d,_) in tasks.items():
        for fold in range(5):
            test=d.group_id.astype(str).map(group_map).eq(fold).to_numpy()
            purged=purge_mask(d,set(d.loc[test,"group_id"].astype(str)),grouping)
            split_rows.append({"task_id":task,"outer_fold":fold,"n_events":len(d),"n_test_events":int(test.sum()),"n_test_groups":d.loc[test,"group_id"].nunique(),"n_training_after_purge":int((~test&~purged).sum()),"n_purged":int((~test&purged).sum())})
    pd.DataFrame(split_rows).to_csv(TABLES/"split_summary.csv",index=False)
    membership=base_clean[["event_id","event_time_proxy_utc","group_id"]].copy();membership["outer_fold"]=membership.group_id.astype(str).map(group_map);membership.to_parquet(EVIDENCE/"split_membership.parquet",index=False)
    pd.DataFrame({"group_id":list(group_map),"outer_fold":list(group_map.values())}).to_csv(EVIDENCE/"outer_group_assignment.csv",index=False)
    dump_json(EVIDENCE/"grouping_protocol.json",grouping)
    preflight={"raw_rows":int(len(raw)),"candidate_main_E0_rows":int(len(base)),"complete_required_rows":int(len(base_clean)),"event_id_unique_in_complete":bool(base_clean.event_id.is_unique),"duplicate_event_ids":int(base_clean.event_id.duplicated().sum()),"C_negative":int((base_clean.C_id_formula.astype(float)<0).sum()),"D_nonpositive":int((base_clean.D_id_formula.astype(float)<=0).sum()),"gust_negative":int((base_clean.gust_0h.astype(float)<0).sum()),"key_missing_excluded":int((~key_complete).sum()),"date_min":str(base_clean.event_time_proxy_utc.min()),"date_max":str(base_clean.event_time_proxy_utc.max()),"gust_min_ms":float(base_clean.gust_0h.min()),"gust_max_ms":float(base_clean.gust_0h.max()),"input_sha256":manifest['input_sha256'],"regional_proxy_events":int(base_clean.regional_proxy_flag.fillna(False).sum()),"cause_group_counts":base_clean.cause_group_event.astype(str).value_counts().to_dict()}
    dump_json(EVIDENCE/"preflight.json",preflight)
    flow=[]
    for task,(d,ctrl) in tasks.items():
        flow.append({"task_id":task,"n_events":len(d),"n_unique_event_id":d.event_id.nunique(),"n_groups":d.group_id.nunique(),"date_min":d.event_time_proxy_utc.min(),"date_max":d.event_time_proxy_utc.max(),"y_min":d.y.min(),"y_max":d.y.max(),"y_zero":int((d.y==0).sum()),"gust_min_ms":d.gust_0h.min(),"gust_max_ms":d.gust_0h.max(),"control_columns":";".join(ctrl),"population_status":"all_valid_untrimmed"})
    pd.DataFrame(flow).to_csv(TABLES/"task_sample_flow.csv",index=False)
    log("preflight and split membership complete")
    all_oof=[]; all_fit=[]; all_fold=[]; all_tuning=[]; full_by_task={}
    for task,(d,ctrl) in tasks.items():
        oof,fits,foldrows,tunes=run_outer_task(d,task,ctrl,group_map,grouping)
        all_oof.append(oof);all_fit.extend(fits);all_fold.extend(foldrows);all_tuning.extend(tunes)
        full,full_rows=full_models(d,task,ctrl,fits)
        full_by_task[task]=full;all_fit.extend(full_rows)
    oof=pd.concat(all_oof,ignore_index=True);oof.to_parquet(PREDICTIONS/"oof_predictions.parquet",index=False)
    fitdf=pd.DataFrame(all_fit);fitdf.to_csv(TABLES/"fit_diagnostics.csv",index=False)
    pd.DataFrame(all_fold).to_csv(TABLES/"fold_scores.csv",index=False)
    pd.DataFrame(all_tuning).to_csv(TABLES/"inner_tuning.csv",index=False)
    log("all 27 outer OOF candidate fits complete")
    leaders=[]
    for task in ("E","R","R_C"):
        for model_id in MODEL_IDS:
            sub=oof.loc[(oof.task_id.eq(task))&(oof.model_id.eq(model_id))]
            met=sample_metrics(sub.y.to_numpy(float),sub.mu_hat.to_numpy(float),task)
            stat=fitdf.loc[(fitdf.task_id.eq(task))&(fitdf.model_id.eq(model_id))&(fitdf.fold.ne("full"))]
            leaders.append({"task_id":task,"model_id":model_id,"model_name":MODEL_NAMES[model_id],**met,"oof_coverage":float(sub.mu_hat.notna().mean()),"success_folds":int(stat.fit_status.isin(["success","warning_accepted"]).sum()),"total_folds":5,"boundary_flags":";".join(sorted(set(stat.boundary_flags.fillna("none")))) ,"identification":";".join(sorted(set(stat.identification.fillna(""))))})
    leader=pd.DataFrame(leaders)
    for task in ("E","R","R_C"):
        b=leader.loc[(leader.task_id.eq(task))&(leader.model_id.eq("M00"))].iloc[0]
        mask=leader.task_id.eq(task)
        leader.loc[mask,"deviance_improvement_vs_M00"]=b.mean_deviance-leader.loc[mask,"mean_deviance"]
        leader.loc[mask,"rmse_improvement_vs_M00"]=b.rmse-leader.loc[mask,"rmse"]
        leader.loc[mask,"recommendation"]=np.where(leader.loc[mask,"oof_coverage"].eq(1.0),"eligible","not_full_oof")
        leader.loc[mask,"rank_by_primary"]=leader.loc[mask,"mean_deviance"].rank(method="min")
    leader.to_csv(TABLES/"model_leaderboard.csv",index=False)
    cal=calibration_table(oof);cal.to_csv(TABLES/"calibration_bins.csv",index=False)
    gust=gust_diagnostic_table(oof);gust.to_csv(TABLES/"gust_bin_diagnostics.csv",index=False)
    tails=tail_table(oof);tails.to_csv(TABLES/"tail_diagnostics.csv",index=False)
    boot_raw=[];boot_sum=[]
    for task in ("E","R","R_C"):
        rawb,sumb=paired_bootstrap(oof,task,1000);boot_raw.append(rawb);boot_sum.append(sumb)
    pd.concat(boot_raw,ignore_index=True).to_parquet(EVIDENCE/"paired_bootstrap_draws.parquet",index=False)
    paired=pd.concat(boot_sum,ignore_index=True);paired.to_csv(TABLES/"paired_comparisons.csv",index=False)
    log("1,000 paired OOF group bootstrap completed")
    curves=[];params=[];supports=[];selected={};bootfits=[]
    for task,(d,ctrl) in tasks.items():
        candidates=leader.loc[(leader.task_id.eq(task))&(leader.model_id.ne("M00"))&(leader.oof_coverage.eq(1.0))].sort_values("mean_deviance").model_id.tolist()
        selected[task]=candidates[:2] if len(candidates)>=2 else candidates
        grid=np.linspace(float(d.gust_0h.min()),float(d.gust_0h.max()),301)
        for model_id,fit in full_by_task[task].items():
            c,derived=derivation_table(fit,grid)
            c["task_id"]=task;c["model_id"]=model_id;c["conditional_ratio"]=c.curve_ratio
            # With no gust interaction, substituting g for each fixed x makes
            # standardized mean = mean(exp(x beta))*r(g); save that exact value.
            base_frame=d.copy();base_frame["gust_0h"]=fit.gref
            standardized_base=float(np.mean(predict(fit,base_frame)))
            c["standardized_mean"] = standardized_base*c.curve_ratio
            c["reference_gust_ms"]=fit.gref
            curves.append(c)
            p={"task_id":task,"model_id":model_id,"fit_status":fit.status,"g_ref_ms":fit.gref,"hyper":json.dumps(fit.hyper,sort_keys=True),"boundary_flags":fit.boundary_flags,"identification":fit.identification,**derived}
            if fit.theta is not None:
                pp=len(fit.feature_means)+1
                for j,val in enumerate(fit.theta[pp:]):p[f"curve_parameter_{j}"]=val
            params.append(p)
            supports.append({"task_id":task,"model_id":model_id,"observed_gust_min_ms":float(d.gust_0h.min()),"observed_gust_p05_ms":float(d.gust_0h.quantile(.05)),"observed_gust_p95_ms":float(d.gust_0h.quantile(.95)),"observed_gust_max_ms":float(d.gust_0h.max()),"n_events":len(d),"n_groups":d.group_id.nunique(),"spline_extrapolation":"cubic polynomial continuation outside each training fold, retained and flagged in OOF" if model_id in ("M03","M04") else "not_applicable"})
        bootfits.append(bootstrap_refits(d,task,ctrl,full_by_task[task],selected[task],grid,200))
    curve_df=pd.concat(curves,ignore_index=True);curve_df.to_parquet(EVIDENCE/"curve_data.parquet",index=False)
    pd.DataFrame(params).to_csv(TABLES/"shape_parameters.csv",index=False)
    pd.DataFrame(supports).to_csv(TABLES/"curve_support.csv",index=False)
    pd.concat(bootfits,ignore_index=True).to_csv(EVIDENCE/"bootstrap_refit_all.csv",index=False)
    dump_json(ROOT/"MODEL_REGISTRY.json",{"models":MODEL_NAMES,"selected_for_conditional_bootstrap":selected,"fit_status_source":"tables/fit_diagnostics.csv","formula_contract":"EXPERIMENT_CONTRACT.md"})
    log("conditional 200-refit bootstrap completed")
    for task in ("E","R","R_C"):
        plot_leaderboard(leader,task);plot_curves(curve_df,task);plot_curves(curve_df,task,True);plot_calibration(cal,task);plot_gust_diagnostics(gust,task,leader)
    stories=[]
    for task in ("E","R","R_C"):
        shortlist=leader.loc[leader.task_id.eq(task)].sort_values("mean_deviance").head(3)
        m0=leader.loc[(leader.task_id.eq(task))&(leader.model_id.eq("M00"))].iloc[0]
        first=shortlist.iloc[0]
        stories.append(f"- **{task}**：预设OOF主指标下前三为 `{', '.join(shortlist.model_id)}`；首位 `{first.model_id}` 相对M00的偏差改善为 `{first.deviance_improvement_vs_M00:.6g}`。这说明下一阶段应把“是否可区分曲线”而不是先验指定阈值放进结果段，并将曲线支持密度与配对区间一起呈现。证据：`tables/model_leaderboard.csv`、`tables/paired_comparisons.csv`、`figures/curves_{task}.png`。")
    write_reports(preflight,leader,fitdf,paired,pd.DataFrame(params),selected,stories)
    (ROOT/"README.md").write_text(f"""# {ROOT.name}\n\nIndependent X01 candidate-curve experiment. All inputs actually used are copied below `frozen_sources/`; the event database is excluded from the return ZIP only because it is a large local frozen input.\n\n## Results\n\n- Chinese report: `X01_REPORT.md`\n- Research story log: `RESEARCH_STORY_LOG.md`\n- ChatGPT return: `RETURN_TO_CHATGPT_X01.md`\n- Rankings: `tables/model_leaderboard.csv`\n- OOF predictions: `predictions/oof_predictions.parquet`\n- Curves: `evidence/curve_data.parquet`\n\n## Re-run\n\nUse the local Python environment containing NumPy, pandas, SciPy, pyarrow and Matplotlib, then run:\n\n```powershell\npython -B src/x01_run.py\n```\n\nThe source has no path to the original Claude repair project; run it with a normal scientific Python environment. It only reads `frozen_sources/input/R02_event_master.parquet` and writes inside this run.\n\nInput SHA-256: `{manifest['input_sha256']}`.\n""",encoding="utf-8")
    log(f"X01 complete in {time.monotonic()-started:.1f} seconds")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("FATAL\n"+traceback.format_exc())
        raise
