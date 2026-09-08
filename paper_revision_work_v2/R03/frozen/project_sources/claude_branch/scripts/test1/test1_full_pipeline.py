"""
Test 1 快速摸底：(duration, customers) 二维结果空间聚类有效性检验。
Steps 1-5. 数据来源见 test1_step0_inventory.py 顶部注释（同一份 62,928 行全量数据）。
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import gaussian_kde
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler
import diptest

PARQUET = '/mnt/user-data/uploads/STST2603/analysis_step2/02_incident_analysis_master_v1_1.parquet'
OUT = '/tmp/branch_work2/results/test1_cluster_screening'
FIG = OUT + '/figures'
SEED = 20260822

cols = ['incident_reference_clean', 'Number of Customers Restored', 'Duration (hours)',
        'incident_date', 'substation', 'LAD21CD']
d = pd.read_parquet(PARQUET, columns=cols)

# ---------------- Step 1: 数据准备 ----------------
n0 = len(d)
d = d.dropna(subset=['Number of Customers Restored', 'Duration (hours)']).copy()
d = d[(d['Number of Customers Restored'] >= 0) & (d['Duration (hours)'] > 0)].copy()
n1 = len(d)
dropped_pct = 100 * (n0 - n1) / n0
print(f'n0={n0} n1={n1} dropped_pct={dropped_pct:.4f}%')

d['log1p_customers'] = np.log1p(d['Number of Customers Restored'].astype(float))
d['log1p_duration'] = np.log1p(d['Duration (hours)'].astype(float))

X_raw = d[['log1p_customers', 'log1p_duration']].to_numpy()
scaler = StandardScaler()
X = scaler.fit_transform(X_raw)

step1_summary = {
    'n0_before_filter': int(n0), 'n1_after_filter': int(n1),
    'dropped_pct': float(dropped_pct),
    'log1p_customers_mean': float(d.log1p_customers.mean()), 'log1p_customers_std': float(d.log1p_customers.std()),
    'log1p_duration_mean': float(d.log1p_duration.mean()), 'log1p_duration_std': float(d.log1p_duration.std()),
}
json.dump(step1_summary, open(OUT + '/00b_step1_sample_summary.json', 'w'), indent=2)

# ---------------- Step 2: 双峰性/多峰性检验 ----------------
dip_rows = []
for name, col in [('log1p_customers', 'log1p_customers'), ('log1p_duration', 'log1p_duration')]:
    vals = d[col].to_numpy()
    dip_stat, pval = diptest.diptest(vals)
    dip_rows.append({'variable': name, 'method': 'hartigan_dip_test', 'statistic': dip_stat,
                      'p_value': pval, 'n': len(vals), 'note': 'diptest package available; no fallback needed'})

# 2D KDE peak counting on standardized log1p space
kde = gaussian_kde(X.T)
grid_n = 150
xg = np.linspace(X[:, 0].min(), X[:, 0].max(), grid_n)
yg = np.linspace(X[:, 1].min(), X[:, 1].max(), grid_n)
XX, YY = np.meshgrid(xg, yg)
ZZ = kde(np.vstack([XX.ravel(), YY.ravel()])).reshape(XX.shape)

# count local maxima via simple 3x3 neighborhood comparison
from scipy.ndimage import maximum_filter
local_max = (maximum_filter(ZZ, size=5) == ZZ)
# ignore boundary and very low density peaks (noise)
thresh = ZZ.max() * 0.02
peak_mask = local_max & (ZZ > thresh)
peak_mask[0, :] = peak_mask[-1, :] = peak_mask[:, 0] = peak_mask[:, -1] = False
peak_idx = np.argwhere(peak_mask)
peaks = [{'x_log1p_customers_std': float(XX[i, j]), 'y_log1p_duration_std': float(YY[i, j]), 'density': float(ZZ[i, j])} for i, j in peak_idx]
peaks = sorted(peaks, key=lambda p: -p['density'])
n_peaks_2d = len(peaks)

pd.DataFrame(dip_rows).to_csv(OUT + '/01_双峰性检验结果.csv', index=False)
json.dump({'n_2d_kde_local_maxima_above_2pct_threshold': n_peaks_2d, 'peaks': peaks[:10]},
           open(OUT + '/01b_2d_kde_peaks.json', 'w'), indent=2)

fig, ax = plt.subplots(figsize=(6, 5))
cf = ax.contourf(XX, YY, ZZ, levels=25, cmap='viridis')
ax.scatter(*zip(*[(p['x_log1p_customers_std'], p['y_log1p_duration_std']) for p in peaks]), color='red', marker='x', s=60, label='local maxima')
ax.set_xlabel('standardized log1p(customers)')
ax.set_ylabel('standardized log1p(duration)')
ax.set_title(f'2D KDE, n_peaks={n_peaks_2d} (threshold=2% of max density)')
plt.colorbar(cf, ax=ax)
ax.legend()
fig.tight_layout()
fig.savefig(FIG + '/01_2d_kde.png', dpi=160)
plt.close(fig)

print('dip test:', dip_rows)
print('n_peaks_2d:', n_peaks_2d)

# ---------------- Step 3: GMM k=2..6 ----------------
gmm_rows = []
gmm_models = {}
n = X.shape[0]
for k in range(2, 7):
    gm = GaussianMixture(n_components=k, covariance_type='full', random_state=SEED, n_init=5)
    gm.fit(X)
    bic = gm.bic(X)
    resp = gm.predict_proba(X)
    resp_clipped = np.clip(resp, 1e-12, 1)
    entropy = -np.sum(resp_clipped * np.log(resp_clipped))
    icl = bic + 2 * entropy  # ICL = BIC + 2*entropy penalty (higher entropy = worse separation); lower ICL better, consistent with BIC's "lower is better" sign convention here since BIC in sklearn is already "lower is better"
    gmm_rows.append({'k': k, 'bic': bic, 'icl': icl, 'entropy': entropy, 'converged': gm.converged_})
    gmm_models[k] = gm

gmm_df = pd.DataFrame(gmm_rows)
gmm_df.to_csv(OUT + '/02_gmm_bic_icl.csv', index=False)
best_k_bic = int(gmm_df.loc[gmm_df.bic.idxmin(), 'k'])
best_k_icl = int(gmm_df.loc[gmm_df.icl.idxmin(), 'k'])
print(gmm_df)
print('best_k_bic', best_k_bic, 'best_k_icl', best_k_icl)

# ---------------- Step 4: K-means 对照（ARI） ----------------
ari_rows = []
for k in sorted(set([best_k_bic, best_k_icl])):
    gm_labels = gmm_models[k].predict(X)
    km = KMeans(n_clusters=k, random_state=SEED, n_init=10)
    km_labels = km.fit_predict(X)
    ari = adjusted_rand_score(gm_labels, km_labels)
    ari_rows.append({'k': k, 'source': 'best_bic' if k == best_k_bic else '', 'ari_gmm_vs_kmeans': ari})
ari_df = pd.DataFrame(ari_rows)
ari_df.to_csv(OUT + '/03_kmeans_ari_对照.csv', index=False)
print(ari_df)

# ---------------- Step 5: 样本量门槛检查（对 best_k_bic 的 GMM 划分） ----------------
d['cluster_bic'] = gmm_models[best_k_bic].predict(X)
rows = []
for c, g in d.groupby('cluster_bic'):
    n_c = len(g)
    n_dates = g['incident_date'].nunique()
    n_lad = g['LAD21CD'].nunique()
    formal = (n_c >= 1000) and (n_dates >= 100) and (n_lad >= 30)
    rows.append({'cluster': int(c), 'n': n_c, 'pct_of_total': 100*n_c/len(d), 'n_dates': n_dates, 'n_lad': n_lad,
                 'mean_log1p_customers': float(g.log1p_customers.mean()), 'mean_log1p_duration': float(g.log1p_duration.mean()),
                 'formal_supported_n>=1000_dates>=100_lad>=30': formal})
sample_check_df = pd.DataFrame(rows).sort_values('cluster')
sample_check_df.to_csv(OUT + '/04_类别样本量检查.csv', index=False)
print(sample_check_df)

# scatter plot colored by cluster for visual reference
fig, ax = plt.subplots(figsize=(6, 5))
sc = ax.scatter(d['log1p_customers'], d['log1p_duration'], c=d['cluster_bic'], cmap='tab10', s=4, alpha=0.4)
ax.set_xlabel('log1p(customers)')
ax.set_ylabel('log1p(duration)')
ax.set_title(f'GMM k={best_k_bic} (BIC-optimal) cluster assignment')
plt.colorbar(sc, ax=ax, label='cluster')
fig.tight_layout()
fig.savefig(FIG + '/02_gmm_clusters_scatter.png', dpi=160)
plt.close(fig)

summary = {
    'best_k_bic': best_k_bic, 'best_k_icl': best_k_icl,
    'dip_test': dip_rows, 'n_peaks_2d_kde': n_peaks_2d,
    'ari': ari_rows, 'sample_check': rows,
}
json.dump(summary, open(OUT + '/99_all_steps_summary.json', 'w'), indent=2, default=str)
print('DONE')
