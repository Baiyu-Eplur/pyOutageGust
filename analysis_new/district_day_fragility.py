# Adapted from advisor review, 2026-09-09. See docs/NEW_ANALYSIS_GUIDE.md.
"""District-day exposure fragility.

Implements the recommendation that exposure fragility be defined at the
network/area level: P(at least one outage of size >= k in district l on day t | gust),
with the denominator being ALL district-days, not incidents.

The package has no weather for district-days without incidents, so daily gust is
interpolated to each district centroid from that day's incident-level gust
observations (every date has >= 15 incidents in >= 13 districts; within a
district-day the incident gusts have sd ~ 1.8 m/s). Interpolation is Gaussian-
kernel inverse-distance on lat/lon (bandwidth 40 km, min 5 neighbours) and is
validated by leaving each district's own incidents out. This is a documented
proxy; the project's gridded weather should replace it.

Fits: lognormal fragility Phi((ln g - ln theta_k)/beta_k) by binomial MLE for
k = any incident, >5, >100, >1000 customers; a probit version with log
population as covariate; and a gust x precipitation surface. Also fits the same
on the WEATHER-ATTRIBUTED occurrence (>= 1 weather-attributed incident of size
>= k), which is the cleaner vulnerability quantity.
Outputs: results/final_models/district_day_panel.csv, district_day_fragility.json,
         fig12_district_day_fragility.png
"""
import warnings; warnings.filterwarnings("ignore")
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats, optimize
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from analysis_new.runtime import ROOT, DATA
OUT = ROOT / "results" / "final_models"; FIG = ROOT / "results" / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
BW_KM = 40.0; KMIN = 5
THR = [0, 5, 100, 1000]; LAB = ["≥1 incident", ">5 cust.", ">100 cust.", ">1000 cust."]

d = pd.read_csv(DATA / "combined_E0_final.csv")
d["date"] = pd.to_datetime(d.incident_date_utc).dt.date
d["cust"] = d.customers_v2_event_excl_reinterruptions.astype(float)
d["weather"] = (d.cause_group_official == "weather_natural").astype(int)
lads = sorted(d.LAD21CD.unique()); dates = sorted(d.date.unique())
cent = d.groupby("LAD21CD")[["lat", "lon"]].mean().loc[lads]
static = d.groupby("LAD21CD")[["log_population", "urban_binary", "income_deprivation_rate"]].first().loc[lads]


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


# ---------------------------------------------------------------- build panel
CACHE = OUT / "district_day_panel.csv"
if CACHE.exists() and "--rebuild" not in __import__("sys").argv:
    panel = pd.read_csv(CACHE); interp_val = json.load(open(OUT / "interp_validation.json"))
else:
  rows, val = [], []
  by_date = {k: v for k, v in d.groupby("date")}
  for t in dates:
      obs = by_date[t]
      inc = obs.groupby("LAD21CD").agg(n=("cust", "size"), maxc=("cust", "max"), wmaxc=("cust", lambda s: s[obs.loc[s.index, "weather"] == 1].max() if (obs.loc[s.index, "weather"] == 1).any() else -1),
                                       g_obs=("gust_0h", "mean"))
      for l in lads:
          g, p = interp(obs, cent.loc[l, "lat"], cent.loc[l, "lon"])
          r = dict(LAD21CD=l, date=str(t), gust=g, precip=p, n_inc=0, maxc=-1.0, wmaxc=-1.0)
          if l in inc.index:
              r.update(n_inc=int(inc.loc[l, "n"]), maxc=float(inc.loc[l, "maxc"]), wmaxc=float(inc.loc[l, "wmaxc"]))
              g_loo, _ = interp(obs, cent.loc[l, "lat"], cent.loc[l, "lon"], exclude_lad=l)
              val.append((float(inc.loc[l, "g_obs"]), g_loo))
          rows.append(r)
  panel = pd.DataFrame(rows).merge(static, left_on="LAD21CD", right_index=True)
  panel["year"] = pd.to_datetime(panel.date).dt.year; panel["month"] = pd.to_datetime(panel.date).dt.month
  for k, lab in zip(THR, LAB):
      panel[f"any_gt{k}"] = (panel.maxc > k - (1 if k == 0 else 0)).astype(int) if k else (panel.n_inc > 0).astype(int)
      panel[f"wthr_gt{k}"] = (panel.wmaxc > k - (1 if k == 0 else 0)).astype(int) if k else (panel.wmaxc >= 0).astype(int)
  panel.to_csv(OUT / "district_day_panel.csv", index=False)
  val = np.array(val); vmask = np.isfinite(val[:, 1])
  interp_val = dict(n=int(vmask.sum()), rmse=float(np.sqrt(np.mean((val[vmask, 0] - val[vmask, 1]) ** 2))),
                    corr=float(np.corrcoef(val[vmask, 0], val[vmask, 1])[0, 1]), bias=float(np.mean(val[vmask, 1] - val[vmask, 0])))
  (OUT / "interp_validation.json").write_text(json.dumps(interp_val)); print(f"panel: {len(panel):,} district-days, {panel.any_gt0.mean():.1%} with an incident; interpolation LOO: rmse={interp_val['rmse']:.2f} m/s corr={interp_val['corr']:.3f} bias={interp_val['bias']:+.2f}")


# ---------------------------------------------------------------- lognormal fragility fits
OPTIMIZER_DIAGNOSTICS = []

def lognormal_mle(g, y, floor=True):
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
    OPTIMIZER_DIAGNOSTICS.append(dict(n=len(g), successes=float(y.sum()), success=bool(best.success), message=str(best.message), nll=float(best.fun), iterations=int(best.nit)))
    p0 = float(1 / (1 + np.exp(-best.x[2]))) if floor else 0.0
    return dict(theta=float(best.x[0]), beta=float(best.x[1]), p0=p0, nll=float(best.fun))


BINS = [0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 23, 26, 30, 45]; MIDS = [(a + b) / 2 for a, b in zip(BINS[:-1], BINS[1:])]
out = {"interpolation_validation": interp_val, "n_district_days": int(len(panel)), "bandwidth_km": BW_KM, "fits": {}}
fig, axes = plt.subplots(1, 3, figsize=(14, 4.3)); gg = np.linspace(1, 40, 300)
colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(THR)))
for ax, (kind, title) in zip(axes[:2], [("any", "any incident of size ≥ k"), ("wthr", "weather-attributed incident of size ≥ k")]):
    for k, lab, c in zip(THR, LAB, colors):
        y = panel[f"{kind}_gt{k}"].to_numpy(); f = lognormal_mle(panel.gust.to_numpy(), y)
        # probit with log population (per-district exposure) at the median district
        X = sm.add_constant(np.column_stack([np.log(np.clip(panel.gust, 0.3, None)), panel.log_population]))
        pr = sm.GLM(y, X, family=sm.families.Binomial(sm.families.links.Probit())).fit()
        out["fits"][f"{kind}_gt{k}"] = dict(label=lab, base_rate=float(y.mean()), lognormal=f,
                                           probit_with_logpop=dict(params=[float(v) for v in pr.params], se=[float(v) for v in pr.bse]))
        e = pd.DataFrame({"g": pd.cut(panel.gust, BINS), "y": y}).groupby("g", observed=False).y.agg(["mean", "count"])
        ax.errorbar(MIDS, e["mean"], yerr=1.96 * np.sqrt(e["mean"] * (1 - e["mean"]) / e["count"]), fmt="o", ms=3, capsize=2, color=c)
        ax.plot(gg, f["p0"] + (1 - f["p0"]) * stats.norm.cdf((np.log(gg) - np.log(f["theta"])) / f["beta"]), color=c, lw=1.8,
                label=f"{lab}: p₀={f['p0']:.3f}, θ={f['theta']:.1f} m/s, β={f['beta']:.2f}")
    ax.set_ylim(0, 1); ax.set_xlabel("District-day gust (m/s, interpolated)"); ax.set_ylabel("P per district-day")
    ax.set_title(f"District-day exposure fragility: {title}", fontsize=9); ax.legend(fontsize=7, loc="upper left")
# surface: P(>100 customers, any) on gust x precip
ax = axes[2]; y = panel["any_gt100"].to_numpy()
lg = np.log(np.clip(panel.gust, 0.3, None)); lp = np.log1p(np.clip(panel.precip, 0, None))
X = sm.add_constant(np.column_stack([lg, lp, lg * lp, panel.log_population]))
m = sm.GLM(y, X, family=sm.families.Binomial(sm.families.links.Probit())).fit()
G, P = np.meshgrid(np.linspace(2, 38, 80), np.linspace(0, 30, 80)); lpop = panel.log_population.median()
Z = stats.norm.cdf(m.params[0] + m.params[1] * np.log(G) + m.params[2] * np.log1p(P) + m.params[3] * np.log(G) * np.log1p(P) + m.params[4] * lpop)
cs = ax.contourf(G, P, Z, levels=np.linspace(0, 1, 11), cmap="magma"); plt.colorbar(cs, ax=ax, label="P")
ax.contour(G, P, Z, levels=[0.1, 0.25, 0.5], colors="white", linewidths=0.8)
ax.set_xlabel("District-day gust (m/s)"); ax.set_ylabel("24-h precipitation (mm)"); ax.set_ylim(0, 30)
ax.set_title(f"P(≥1 outage >100 customers | gust, precip), median district\nb_g={m.params[1]:.2f}, b_p={m.params[2]:.2f}, b_gp={m.params[3]:.2f}", fontsize=8)
dZdg = m.params[1] + m.params[3] * np.log1p(P)
out["surface_gt100"] = dict(params=[float(v) for v in m.params], se=[float(v) for v in m.bse], frac_domain_monotone_gust=float((dZdg >= 0).mean()))
fig.tight_layout(); fig.savefig(FIG / "fig12_district_day_fragility.png", dpi=170); plt.close(fig)
(OUT / "district_day_fragility.json").write_text(json.dumps(out, indent=2))
for k, v in out["fits"].items(): print(f"  {k:12s} base={v['base_rate']:.3f}  p0={v['lognormal']['p0']:.3f}  theta={v['lognormal']['theta']:.1f}  beta={v['lognormal']['beta']:.2f}")
print("surface >100:", np.round(out["surface_gt100"]["params"], 3), "monotone in gust over", out["surface_gt100"]["frac_domain_monotone_gust"])

(OUT / "district_day_optimizer_diagnostics.json").write_text(json.dumps(OPTIMIZER_DIAGNOSTICS, indent=2))
