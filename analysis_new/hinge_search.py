"""Reconstruct the missing exploratory hinge-grid producer from documented specs.

Same M5 controls, train-scaled five LAD folds, LAD normal-based p-values.
These fixed exploratory candidates are separate from formal knot estimation.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster
from analysis_new.model_selection import design
from analysis_new.runtime import ROOT, DATA


def matrix(tr, va, cust, knots):
    a, b = design(tr, va, 'M5_+year_month_FE', cust)
    if knots:
        for X, d in ((a, tr), (b, va)):
            X.drop(columns=['z_gust_sq'], inplace=True)
            for k in knots:
                X[f'hinge_{k:g}'] = np.maximum(d.gust_0h-k, 0.)
    return a, b.reindex(columns=a.columns, fill_value=0.)


def main():
    rows = []
    for name, target, cust in [('E0', 'log1p_customers_v2', False), ('R0c', 'log_duration_B_full_span_hours', True)]:
        d = pd.read_csv(DATA/f'combined_{name}_final.csv')
        if cust:
            d['customers_v2_log1p'] = np.log1p(d.customers_v2_event_excl_reinterruptions)
        y = d[target].to_numpy(); lads = d.LAD21CD.unique()
        np.random.default_rng(20260908).shuffle(lads)
        folds = d.LAD21CD.map(dict(zip(lads, np.arange(len(lads)) % 5))).to_numpy()
        for knots in [[], [10.8], [14], [16], [18], [16, 26], [14, 20, 26]]:
            X, _ = matrix(d, d, cust, knots)
            fit = sm.OLS(y, X).fit()
            se = np.sqrt(np.diag(cov_cluster(fit, pd.factorize(d.LAD21CD)[0])))
            pvals = pd.Series(2*stats.norm.sf(np.abs(fit.params.to_numpy()/se)), index=X.columns)
            pred = np.zeros(len(d))
            for k in range(5):
                mask = folds == k
                tr, va = matrix(d[~mask], d[mask], cust, knots)
                pred[mask] = va.to_numpy() @ sm.OLS(y[~mask], tr).fit().params.to_numpy()
            terms = {f'hinge_{k:g}': f'{fit.params[f"hinge_{k:g}"]:.3f}(p={pvals[f"hinge_{k:g}"]:.2g})' for k in knots}
            rows.append(dict(model=name, spec='hinge@'+'+@'.join(f'{k:g}' for k in knots) if knots else 'quadratic (M5)',
                             k=int(fit.df_model+1), aic=fit.aic, bic=fit.bic, adj_r2=fit.rsquared_adj,
                             cv_lad=float(np.sqrt(np.mean((y-pred)**2))), hinge_coefs=str(terms)))
    pd.DataFrame(rows).to_csv(ROOT/'results/model_selection/hinge_knot_search.csv', index=False)
