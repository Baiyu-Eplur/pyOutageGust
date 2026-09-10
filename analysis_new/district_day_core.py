"""Pure shared helpers extracted from the original district-day analysis.

The MLE starts, bounds, clipping and objective are unchanged. No input/output
or runtime context is accessed on import. Used by the legacy panel and P03/P04.
"""
import numpy as np
from scipy import stats, optimize

BW_KM = 40.0
KMIN = 5

def km(lat1, lon1, lat2, lon2):
    """Approximate planar distance in km (region spans ~2 deg)."""
    return np.sqrt(((lat1 - lat2) * 111.0) ** 2 + ((lon1 - lon2) * 111.0 * np.cos(np.radians(51.8))) ** 2)


def interp(obs, target_lat, target_lon, exclude_lad=None):
    """Gaussian-kernel IDW of gust and precip from one day's incidents to a point."""
    o = obs if exclude_lad is None else obs[obs.LAD21CD != exclude_lad]
    if len(o) == 0: return np.nan, np.nan
    dist = km(target_lat, target_lon, o.lat.to_numpy(), o.lon.to_numpy())
    w = np.exp(-0.5 * (dist / BW_KM) ** 2)
    if (w > 1e-3).sum() < KMIN:  # fall back to nearest KMIN
        idx = np.argsort(dist)[:KMIN]; w = np.zeros_like(w); w[idx] = 1.0 / (dist[idx] + 1.0)
    w /= w.sum()
    return float(w @ o.gust_0h.to_numpy()), float(w @ o.precipitation_24h_sum.to_numpy())


def lognormal_mle(g, y, floor=True, diagnostics=None):
    """P = p0 + (1-p0) * Phi((ln g - ln theta)/beta); p0 = gust-independent background rate."""
    lg = np.log(np.clip(g, 0.3, None))
    def nll(par):
        p0 = 1 / (1 + np.exp(-par[2])) if floor else 0.0
        p = np.clip(p0 + (1 - p0) * stats.norm.cdf((lg - np.log(par[0])) / par[1]), 1e-9, 1 - 1e-9)
        return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    best = None
    for th0 in (15, 20, 25, 30):
        x0 = [th0, 0.4, np.log(max(y.mean(), 1e-3) / (1 - y.mean()))] if floor else [th0, 0.4]
        bnds = [(2, 200), (0.05, 5)] + ([(-12, 5)] if floor else [])
        r = optimize.minimize(nll, x0, method="L-BFGS-B", bounds=bnds)
        if best is None or r.fun < best.fun: best = r
    if diagnostics is not None: diagnostics.append(dict(n=len(g), successes=float(y.sum()), success=bool(best.success), message=str(best.message), nll=float(best.fun), iterations=int(best.nit)))
    p0 = float(1 / (1 + np.exp(-best.x[2]))) if floor else 0.0
    return dict(theta=float(best.x[0]), beta=float(best.x[1]), p0=p0, nll=float(best.fun))


def predict_lognormal(g, fit):
    return np.clip(fit['p0'] + (1-fit['p0']) * stats.norm.cdf(
        (np.log(np.clip(g, 0.3, None))-np.log(fit['theta']))/fit['beta']), 1e-9, 1-1e-9)


def lad_folds(lads, seed=20260908, folds=5):
    """Same first-seen LAD order, shuffle seed and modulo allocation as plot_model_selection."""
    unique = np.array(list(dict.fromkeys(lads)))
    if len(unique) < folds:
        raise ValueError('Fewer LADs than CV folds')
    np.random.default_rng(seed).shuffle(unique)
    mapping = dict(zip(unique, np.arange(len(unique)) % folds))
    return np.array([mapping[x] for x in lads])
