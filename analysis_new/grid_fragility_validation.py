"""Paired old/grid panel evaluation; shared scientific MLE, identical held-out LADs."""
import numpy as np
import pandas as pd

from analysis_new.district_day_core import km, BW_KM, KMIN, lad_folds, lognormal_mle, predict_lognormal

TARGETS = [f'{kind}_gt{k}' for kind in ('any', 'wthr') for k in (0, 5, 100, 1000)]


def paired_stats(truth, estimate):
    truth, estimate = np.asarray(truth), np.asarray(estimate)
    delta = estimate - truth
    return dict(n=len(delta), mean_difference=float(delta.mean()), sd_difference=float(delta.std(ddof=1)),
                rmse=float(np.sqrt(np.mean(delta ** 2))),
                correlation=float(np.corrcoef(truth, estimate)[0, 1]) if np.std(truth) and np.std(estimate) else None,
                difference_quantiles=dict(zip(['p01', 'p05', 'p50', 'p95', 'p99'],
                                              np.quantile(delta, [.01, .05, .5, .95, .99]).tolist())))


def grid_loo(grid, centroids, exclude_shared_cells=False):
    """Hold each target LAD out before Gaussian/fallback weights are calculated.

    This diagnoses spatial reconstructability, not ERA5 measurement accuracy.
    Supplementary exclusion removes neighbours returned from the very same cell.
    """
    lads = centroids.LAD21CD.tolist()
    daily = grid.pivot(index='date', columns='LAD21CD', values='gust_grid')[lads]
    cells = grid.groupby('LAD21CD')[['grid_lat', 'grid_lon']].first().loc[lads]
    predictions = np.empty(daily.shape)
    for i, row in enumerate(centroids.itertuples(index=False)):
        allowed = np.arange(len(lads)) != i
        if exclude_shared_cells:
            allowed &= (cells.to_numpy() != cells.iloc[i].to_numpy()).any(axis=1)
        indices = np.flatnonzero(allowed)
        if not len(indices):
            raise ValueError('No distinct grid neighbours remain for spatial validation')
        distance = km(row.lat, row.lon, centroids.lat.to_numpy()[indices], centroids.lon.to_numpy()[indices])
        weights = np.exp(-.5 * (distance / BW_KM) ** 2)
        if (weights > 1e-3).sum() < KMIN:
            nearest = np.argsort(distance)[:KMIN]
            weights[:] = 0; weights[nearest] = 1 / (distance[nearest] + 1)
        weights /= weights.sum()
        predictions[:, i] = daily.to_numpy()[:, indices] @ weights
    result = daily.stack().rename('grid_truth').reset_index()
    result['grid_loo'] = pd.DataFrame(predictions, index=daily.index, columns=daily.columns).stack().to_numpy()
    return result


def paired_bootstrap(old_loss, new_loss, groups, repeats=1000, seed=20260909):
    """Resample whole LADs, paired across both versions and all eight endpoints.

    Conditional uncertainty in fixed OOF predictions; does not refit or resample storms.
    """
    unique = np.unique(groups)
    old = np.array([old_loss[groups == g].sum(axis=0) for g in unique])
    new = np.array([new_loss[groups == g].sum(axis=0) for g in unique])
    rng = np.random.default_rng(seed)
    gains = []
    for _ in range(repeats):
        take = rng.integers(0, len(unique), len(unique))
        a, b = old[take].sum(axis=0), new[take].sum(axis=0)
        gains.append((a-b) / np.maximum(a, 1e-15))
    gains = np.array(gains)
    return dict(mean_relative_gain_ci95=np.quantile(gains.mean(axis=1), [.025, .975]).tolist(),
                endpoint_relative_gain_ci95=np.quantile(gains, [.025, .975], axis=0).T.tolist(),
                repeats=repeats, unit='paired LAD, fixed OOF predictions')


def calibration_rows(y, old, new, target):
    # Common pooled-prediction quantiles resolve rare outcomes; no outcomes determine bins.
    edges = np.unique(np.r_[0., np.quantile(np.r_[old, new], np.linspace(0, 1, 11)), 1.])
    records = []
    for version, pred in [('proxy', old), ('era5_daily_max', new)]:
        bin_id = np.clip(np.searchsorted(edges, pred, side='right') - 1, 0, len(edges)-2)
        for b in np.unique(bin_id):
            m = bin_id == b
            records.append(dict(target=target, version=version, bin=int(b), lower=edges[b], upper=edges[b+1],
                                n=int(m.sum()), mean_probability=float(pred[m].mean()),
                                observed_frequency=float(y[m].mean()), events=int(y[m].sum())))
    return records


def evaluate(panel, folds, repeats=1000, progress=lambda text: None):
    """No held-out outcomes enter a fit; weather vectors are the only changed covariate."""
    parameters, diagnostics, scores, calibration, fold_scores = [], [], [], [], []
    oof = panel[['LAD21CD', 'date']].copy(); oof['fold'] = folds
    losses = {v: [] for v in ('proxy', 'era5_daily_max')}
    for target in TARGETS:
        y = panel[target].to_numpy(dtype=float)
        predictions = {}
        for version, column in [('proxy', 'gust_proxy'), ('era5_daily_max', 'gust')]:
            progress(f'fit {target} / {version}')
            g = panel[column].to_numpy()
            if len(np.unique(y)) != 2:
                raise ValueError(f'{target}: constant outcome, fragility parameters not identifiable')
            diag = []
            fit = lognormal_mle(g, y, diagnostics=diag)
            parameters.append(dict(target=target, version=version, n=len(y), events=int(y.sum()), **fit))
            diagnostics.append(dict(target=target, version=version, scope='full', **diag[-1]))
            pred = np.full(len(y), np.nan)
            for k in np.unique(folds):
                test = folds == k; train = ~test
                if set(panel.loc[test, 'LAD21CD']) & set(panel.loc[train, 'LAD21CD']):
                    raise ValueError('LAD leakage across train/test')
                if len(np.unique(y[train])) != 2:
                    raise ValueError(f'{target}, fold {k}: constant training outcome')
                diag = []; fit_fold = lognormal_mle(g[train], y[train], diagnostics=diag)
                diagnostics.append(dict(target=target, version=version, scope=f'fold_{k}', **diag[-1]))
                pred[test] = predict_lognormal(g[test], fit_fold)
                fold_scores.append(dict(target=target, version=version, fold=int(k), n=int(test.sum()),
                                        brier=float(np.mean((pred[test]-y[test])**2))))
            if not np.isfinite(pred).all():
                raise ValueError('Incomplete out-of-fold predictions')
            predictions[version] = pred
            losses[version].append((pred-y)**2)
            oof[f'{target}_y'] = y.astype(int); oof[f'{target}_{version}'] = pred
        old, new = (predictions[v] for v in ('proxy', 'era5_daily_max'))
        c = calibration_rows(y, old, new, target); calibration.extend(c)
        errors = {}
        for version in predictions:
            rows = [r for r in c if r['version'] == version]
            errors[version] = float(np.sqrt(sum(r['n']*(r['mean_probability']-r['observed_frequency'])**2 for r in rows)/len(y)))
        a, b = float(np.mean((old-y)**2)), float(np.mean((new-y)**2))
        scores.append(dict(target=target, n=len(y), event_rate=float(y.mean()), brier_proxy=a,
                           brier_grid=b, absolute_improvement=a-b, relative_improvement=(a-b)/max(a, 1e-15),
                           calibration_rmse_proxy=errors['proxy'], calibration_rmse_grid=errors['era5_daily_max']))
    ci = paired_bootstrap(np.array(losses['proxy']).T, np.array(losses['era5_daily_max']).T,
                          panel.LAD21CD.to_numpy(), repeats)
    for row, limits in zip(scores, ci['endpoint_relative_gain_ci95']):
        row.update(relative_gain_ci_low=limits[0], relative_gain_ci_high=limits[1])
    return dict(parameters=pd.DataFrame(parameters), scores=pd.DataFrame(scores),
                calibration=pd.DataFrame(calibration), fold_scores=pd.DataFrame(fold_scores),
                oof=oof, diagnostics=diagnostics, uncertainty=ci)


def decide(scores, uncertainty, quality_flags, diagnostics, minimum_gain=.05):
    """Predeclared screening rule; a visual calibration decision cannot be automated."""
    gain = float(scores.relative_improvement.mean())
    cal_gain = float((1-scores.calibration_rmse_grid/np.maximum(scores.calibration_rmse_proxy, 1e-15)).mean())
    metrics = dict(mean_relative_brier_gain=gain, mean_relative_calibration_rmse_gain=cal_gain,
                   brier_gain_ci95=uncertainty['mean_relative_gain_ci95'], candidate_min_gain=minimum_gain)
    if any(not d['success'] for d in diagnostics):
        return dict(status='intermediate', reason='存在未收敛拟合；不据此自动接受或宣称有效比较。', **metrics)
    if quality_flags:
        return dict(status='intermediate', reason='数据/空间诊断有待核查项：'+'；'.join(quality_flags), **metrics)
    if gain <= 0 or (scores.relative_gain_ci_high < -minimum_gain).any():
        return dict(status='rollback', reason='平均 Brier 未改善，或有阈值显示明确实质恶化；建议仅保留旧代理附录。', **metrics)
    if gain < .01:
        return dict(status='rollback', reason='平均相对 Brier 改善小于预设 1% 实质性下限；不支持正文转正。', **metrics)
    candidate = (gain >= minimum_gain and uncertainty['mean_relative_gain_ci95'][0] > 0
                 and (scores.relative_improvement >= -minimum_gain).all()
                 and cal_gain >= minimum_gain)
    return dict(status='intermediate', numerical_candidate=bool(candidate),
                reason=('达到候选数值门槛；仍需用户/设计方确认校准图明显改善及空间诊断后才可转正。'
                        if candidate else '改善或校准证据尚不明确；由用户/设计方共同判断。'), **metrics)


def plot_calibration(rows, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4, 2, figsize=(12, 17))
    for ax, target in zip(axes.flat, TARGETS):
        subset = rows[rows.target == target]
        high = max(subset.mean_probability.max(), subset.observed_frequency.max(), .01)*1.1
        ax.plot([0, high], [0, high], 'k--', lw=1)
        for version, label in [('proxy', 'Old incident proxy'), ('era5_daily_max', 'ERA5 daily maximum')]:
            d = subset[subset.version == version].sort_values('mean_probability')
            ax.plot(d.mean_probability, d.observed_frequency, 'o-', ms=4, label=label)
        ax.set(xlabel='Mean OOF probability', ylabel='Observed frequency', title=target, xlim=(0, high), ylim=(0, high))
        ax.legend(fontsize=8)
    fig.suptitle('Identical LAD-held-out folds; common pooled-probability bins')
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
