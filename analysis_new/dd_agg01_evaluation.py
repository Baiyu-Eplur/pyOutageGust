"""Fixed-fold probability evaluation for the five DD-AGG01 aggregations."""
import numpy as np
import pandas as pd

from analysis_new.daily_aggregations import CANDIDATES, LABELS
from analysis_new.grid_fragility_validation import TARGETS, paired_bootstrap
from analysis_new.fragility_optimizer import probabilities


def calibration(y, predictions, target, edges=None):
    """Shared probability-only edges; ties stay together and empty bins survive."""
    if edges is None:
        pooled = np.concatenate(list(predictions.values()))
        edges = np.unique(np.r_[0., np.quantile(pooled, np.linspace(0, 1, 11)), 1.])
    else:
        edges = np.asarray(edges, dtype=float)
        if len(edges)<2 or edges[0]!=0 or edges[-1]!=1 or not np.isfinite(edges).all() or (np.diff(edges)<=0).any():
            raise ValueError('Frozen probability edges must strictly increase from 0 to 1')
    rows = []
    for candidate, p in predictions.items():
        ids = np.clip(np.searchsorted(edges, p, side='right')-1, 0, len(edges)-2)
        for b in range(len(edges)-1):
            m = ids == b; n = int(m.sum())
            rows.append(dict(target=target, candidate=candidate, bin=b, lower=edges[b], upper=edges[b+1],
                             n=n, events=int(y[m].sum()), mean_probability=float(p[m].mean()) if n else np.nan,
                             observed_frequency=float(y[m].mean()) if n else np.nan, sparse=n < 100))
    return rows, edges.tolist()


def evaluate(oof, fits, candidates=CANDIDATES):
    scores, folds, bins, edges = [], [], [], {}
    for target in TARGETS:
        y = oof[target].to_numpy(); const = oof[target+'_constant'].to_numpy()
        base = oof[target+'__'+candidates[0]].to_numpy()
        bs0 = np.mean((base-y)**2); bsc = np.mean((const-y)**2)
        valid_predictions = {}
        for candidate in candidates:
            p = oof[target+'__'+candidate].to_numpy()
            status = fits[(fits.target == target) & (fits.candidate == candidate) & (fits.scope != 'full')]
            valid = bool(len(status) == 5 and status.valid.all() and np.isfinite(p).all())
            bs = np.mean((p-y)**2)
            scores.append(dict(target=target, candidate=candidate, n=len(y), events=int(y.sum()), valid_cv=valid,
                               brier=bs, brier_a01=bs0, absolute_gain=bs0-bs, relative_gain=(bs0-bs)/bs0,
                               constant_brier=bsc, brier_skill=1-bs/bsc))
            if valid: valid_predictions[candidate] = p
            for fold in sorted(oof.fold.unique()):
                m = oof.fold.to_numpy() == fold
                a = np.mean((base[m]-y[m])**2); b = np.mean((p[m]-y[m])**2)
                folds.append(dict(target=target, candidate=candidate, fold=int(fold), n=int(m.sum()),
                                  valid=bool(status.loc[status.scope == f'fold_{fold}', 'valid'].all()),
                                  brier=b, brier_a01=a, absolute_gain=a-b, relative_gain=(a-b)/a,
                                  constant_brier=np.mean((const[m]-y[m])**2)))
        if valid_predictions:
            records, edges[target] = calibration(y, valid_predictions, target); bins.extend(records)
    scores = pd.DataFrame(scores); bins = pd.DataFrame(bins)
    for i, r in scores.iterrows():
        rows = bins[(bins.target == r.target) & (bins.candidate == r.candidate) & (bins.n > 0)]
        scores.loc[i, 'calibration_rmse'] = (np.sqrt(np.sum(rows.n*(rows.mean_probability-rows.observed_frequency)**2)/rows.n.sum())
                                            if len(rows) else np.nan)
    for target in TARGETS:
        a = scores[(scores.target == target) & (scores.candidate == candidates[0])].calibration_rmse.iloc[0]
        m = scores.target == target
        scores.loc[m, 'calibration_absolute_gain'] = a-scores.loc[m, 'calibration_rmse']
        scores.loc[m, 'calibration_relative_gain'] = (a-scores.loc[m, 'calibration_rmse'])/a
    return scores, pd.DataFrame(folds), bins, edges


def uncertainty(oof, scores, candidates=CANDIDATES):
    """Reuse the P03 paired-LAD method; absolute intervals use the same draws."""
    groups = oof.LAD21CD.to_numpy(); unique = np.unique(groups)
    y = oof[TARGETS].to_numpy()
    old = (oof[[t+'__'+candidates[0] for t in TARGETS]].to_numpy()-y)**2
    counts = np.array([(groups == g).sum() for g in unique]); rows = []
    for c in candidates:
        loss = (oof[[t+'__'+c for t in TARGETS]].to_numpy()-y)**2
        relative = paired_bootstrap(old, loss, groups, repeats=1000, seed=20260909)
        delta = np.array([(old[groups == g]-loss[groups == g]).sum(axis=0) for g in unique])
        rng = np.random.default_rng(20260909); values = []
        for _ in range(1000):
            take = rng.integers(0, len(unique), len(unique))
            values.append(delta[take].sum(axis=0)/counts[take].sum())
        absolute = np.quantile(values, [.025, .975], axis=0).T
        for j, target in enumerate(TARGETS):
            valid = scores.loc[(scores.target == target) & scores.candidate.isin([c, candidates[0]]), 'valid_cv'].all()
            rows.append(dict(candidate=c, target=target, valid_comparison=bool(valid),
                             absolute_gain_lo=absolute[j, 0], absolute_gain_hi=absolute[j, 1],
                             relative_gain_lo=relative['endpoint_relative_gain_ci95'][j][0],
                             relative_gain_hi=relative['endpoint_relative_gain_ci95'][j][1], repeats=1000, seed=20260909))
    return pd.DataFrame(rows)


def plot_results(out, daily, fits, bins):
    import matplotlib.pyplot as plt
    figdir = out/'figures'; figdir.mkdir(exist_ok=True)
    curve_rows = []
    colors = plt.get_cmap('tab10').colors
    for target in TARGETS:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        rows = bins[bins.target == target]
        nonempty = rows[rows.n > 0]
        zoom = min(1., max(.015, float(nonempty[['mean_probability', 'observed_frequency']].max().max())*1.1)) if len(nonempty) else 1.
        for ax, limit in zip(axes, [1., zoom]):
            ax.plot([0, limit], [0, limit], 'k--', lw=1)
            for j, c in enumerate(CANDIDATES):
                b = rows[rows.candidate == c]
                # NaNs break lines at sparse/empty bins instead of bridging over them.
                x = b.mean_probability.where(b.n >= 100); y = b.observed_frequency.where(b.n >= 100)
                ax.plot(x, y, '-o', color=colors[j], markersize=3, label=c)
                sparse = b[(b.n > 0) & (b.n < 100)]
                ax.scatter(sparse.mean_probability, sparse.observed_frequency, marker='x', color=colors[j], s=40)
            ax.set(xlim=(0, limit), ylim=(0, limit), xlabel='Mean OOF probability', ylabel='Observed frequency')
            ax.set_aspect('equal', adjustable='box'); ax.grid(alpha=.2)
        axes[0].set_title('Full range (all nonempty bins)'); axes[1].set_title('Common zoom (all nonempty bins)')
        axes[1].legend(fontsize=7, loc='best')
        fig.suptitle(f'{target}: shared bins; crosses n<100; empty bins in CSV')
        fig.tight_layout(); fig.savefig(figdir/f'calibration_{target}.png', dpi=160); plt.close(fig)
        fig, axes = plt.subplots(1, 5, figsize=(20, 4), sharey=True)
        for j, (c, label) in enumerate(zip(CANDIDATES, LABELS)):
            ax = axes[j]; g = daily[c].to_numpy(); y = daily[target].to_numpy()
            f = fits[(fits.candidate == c) & (fits.target == target) & (fits.scope == 'full')].iloc[0]
            x = np.linspace(g.min(), g.max(), 201)
            if f.valid:
                p = probabilities(x, **{k: f[k] for k in ['theta', 'beta', 'p0']})
                ax.plot(x, p, color=colors[j], label='Full fit (descriptive)')
                curve_rows.extend(dict(target=target, candidate=c, kind='fit', aggregate=a, probability=b, n=0, events=0) for a, b in zip(x, p))
            else: ax.text(.1, .8, 'INVALID full fit', transform=ax.transAxes)
            be = np.unique(np.quantile(g, np.linspace(0, 1, 16)))
            ids = np.clip(np.searchsorted(be, g, side='right')-1, 0, len(be)-2)
            for b in np.unique(ids):
                m = ids == b; n = int(m.sum()); mx=float(g[m].mean()); my=float(y[m].mean())
                ax.scatter(mx, my, color='black', s=20, marker='x' if n < 100 else 'o')
                curve_rows.append(dict(target=target, candidate=c, kind='observed', aggregate=mx, probability=my, n=n, events=int(y[m].sum())))
            ax.set_title(label, fontsize=9); ax.set_xlabel('Own aggregate (m/s)'); ax.set_ylim(0, 1); ax.grid(alpha=.2)
        axes[0].set_ylabel('Event probability / frequency')
        fig.suptitle(f'{target}: full-sample description, not calibration; horizontal quantities differ')
        fig.tight_layout(); fig.savefig(figdir/f'occurrence_{target}.png', dpi=150); plt.close(fig)
    pd.DataFrame(curve_rows).to_csv(out/'occurrence_curve_data.csv', index=False)
