"""
工作命令 #3：检验 log1p(customers) 与 log1p(duration) 的统计独立性。
数据来源：与工作命令 #2 完全相同、已交叉验证过的替代数据源
(analysis_step2/02_incident_analysis_master_v1_1.parquet 的
`Number of Customers Restored` / `Duration (hours)` 两列，62,928 行全量)。
不重新尝试传输 303MB 的 master CSV。

Steps 1-6（Step 7 综合结论在单独的 Markdown 中撰写）。
"""

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import gaussian_kde, spearmanr, kruskal
from sklearn.feature_selection import mutual_info_regression
import dcor

PARQUET = str(external_path('analysis_step2/02_incident_analysis_master_v1_1.parquet'))
OUT = str(result_path('test1b_independence_check'))
FIG = OUT + '/figures'
SEED = 20260823
N_PERM_DCOR = 500
N_PERM_MI = 500
rng_global = np.random.default_rng(SEED)

t_start = time.time()

# ---------------- Step 1: 数据准备 ----------------
cols = ['incident_reference_clean', 'Number of Customers Restored', 'Duration (hours)',
        'incident_date', 'substation', 'LAD21CD']
d = pd.read_parquet(read_input(PARQUET), columns=cols)
n0 = len(d)
d = d.dropna(subset=['Number of Customers Restored', 'Duration (hours)']).copy()
d = d[(d['Number of Customers Restored'] >= 0) & (d['Duration (hours)'] > 0)].copy()
n_full = len(d)

d['log1p_customers'] = np.log1p(d['Number of Customers Restored'].astype(float))
d['log1p_duration'] = np.log1p(d['Duration (hours)'].astype(float))

d_pos = d[d['Number of Customers Restored'] > 0].copy()
n_pos = len(d_pos)
n_zero = n_full - n_pos

step1_summary = {
    'n0_before_filter': int(n0),
    'n_full_sample': int(n_full),
    'n_customers_gt0_subset': int(n_pos),
    'n_customers_eq0_excluded': int(n_zero),
    'pct_customers_eq0': float(100 * n_zero / n_full),
    'full_sample': {
        'log1p_customers_mean': float(d.log1p_customers.mean()), 'log1p_customers_std': float(d.log1p_customers.std()),
        'log1p_duration_mean': float(d.log1p_duration.mean()), 'log1p_duration_std': float(d.log1p_duration.std()),
    },
    'customers_gt0_subset': {
        'log1p_customers_mean': float(d_pos.log1p_customers.mean()), 'log1p_customers_std': float(d_pos.log1p_customers.std()),
        'log1p_duration_mean': float(d_pos.log1p_duration.mean()), 'log1p_duration_std': float(d_pos.log1p_duration.std()),
    },
}
json.dump(step1_summary, open(OUT + '/00_step1_sample_summary.json', 'w'), indent=2)
print('Step1 done:', step1_summary)

datasets = {'full': d, 'customers_gt0': d_pos}

# ---------------- Step 2: Spearman ----------------
def spearman_benchmark(rho):
    a = abs(rho)
    if a < 0.1:
        return 'negligible'
    elif a < 0.3:
        return 'weak'
    elif a < 0.5:
        return 'moderate'
    else:
        return 'strong'

spearman_rows = []
for name, df_ in datasets.items():
    rho, p = spearmanr(df_['log1p_customers'], df_['log1p_duration'])
    spearman_rows.append({
        'sample': name, 'n': len(df_), 'spearman_rho': rho, 'p_value': p,
        'effect_size_label': spearman_benchmark(rho),
    })
spearman_df = pd.DataFrame(spearman_rows)
spearman_df.to_csv(OUT + '/01_spearman.csv', index=False)
print(spearman_df)

# ---------------- Step 3: 距离相关（快速 O(n log n) 一维算法 + 自定义置换检验） ----------------
# 说明：dcor.independence.distance_covariance_test 的内置置换检验即便对一维输入也会调用
# 朴素 O(n^2) 成对距离矩阵计算（在 n=62,928 时实测触发 29.5GB 内存分配错误，已验证并放弃）。
# 因此改为：用 dcor.distance_correlation(..., method='avl')（精确的 O(n log n) 一维快速算法，
# 不是近似、不是子采样）计算真实统计量，再对 y 做多次随机置换、每次仍用同一快速算法重新计算，
# 从而得到经验零分布和置换检验 p 值。这是命令允许的两种方案之一（"支持一维变量快速算法的实现"），
# 且在全量 n=62,928 上精确计算，不涉及子采样近似。
dcor_rows = []
for name, df_ in datasets.items():
    x = df_['log1p_customers'].to_numpy()
    y = df_['log1p_duration'].to_numpy()
    n = len(x)
    t0 = time.time()
    dc_obs = dcor.distance_correlation(x, y, method='avl')
    rng = np.random.default_rng(SEED)
    null_stats = np.empty(N_PERM_DCOR)
    for i in range(N_PERM_DCOR):
        yp = rng.permutation(y)
        null_stats[i] = dcor.distance_correlation(x, yp, method='avl')
    p_perm = (np.sum(null_stats >= dc_obs) + 1) / (N_PERM_DCOR + 1)
    elapsed = time.time() - t0
    dcor_rows.append({
        'sample': name, 'n': n, 'distance_correlation_avl_exact': float(dc_obs),
        'n_permutations': N_PERM_DCOR, 'perm_p_value': float(p_perm),
        'null_mean': float(null_stats.mean()), 'null_std': float(null_stats.std()),
        'null_max': float(null_stats.max()),
        'elapsed_sec': elapsed,
        'method_note': 'exact AVL O(n log n) algorithm on full n (no subsampling); custom permutation null since dcor built-in test uses naive O(n^2) distances',
    })
    print(f'[dcor] {name}: dc={dc_obs:.5f} perm_p={p_perm:.5f} elapsed={elapsed:.1f}s')

dcor_df = pd.DataFrame(dcor_rows)
dcor_df.to_csv(OUT + '/02_distance_correlation.csv', index=False)

# ---------------- Step 4: 互信息（k-NN 估计 + 置换检验） ----------------
mi_rows = []
for name, df_ in datasets.items():
    x = df_['log1p_customers'].to_numpy().reshape(-1, 1)
    y = df_['log1p_duration'].to_numpy()
    t0 = time.time()
    mi_obs = mutual_info_regression(x, y, n_neighbors=3, random_state=SEED)[0]
    rng = np.random.default_rng(SEED)
    null_mi = np.empty(N_PERM_MI)
    for i in range(N_PERM_MI):
        yp = rng.permutation(y)
        null_mi[i] = mutual_info_regression(x, yp, n_neighbors=3, random_state=SEED)[0]
    z = (mi_obs - null_mi.mean()) / (null_mi.std() if null_mi.std() > 0 else np.nan)
    p_perm = (np.sum(null_mi >= mi_obs) + 1) / (N_PERM_MI + 1)
    elapsed = time.time() - t0
    mi_rows.append({
        'sample': name, 'n': len(df_), 'mutual_info_knn': float(mi_obs),
        'n_permutations': N_PERM_MI, 'perm_p_value': float(p_perm), 'z_score_vs_null': float(z),
        'null_mean': float(null_mi.mean()), 'null_std': float(null_mi.std()),
        'elapsed_sec': elapsed,
    })
    print(f'[MI] {name}: mi={mi_obs:.5f} z={z:.2f} perm_p={p_perm:.5f} elapsed={elapsed:.1f}s')

mi_df = pd.DataFrame(mi_rows)
mi_df.to_csv(OUT + '/03_mutual_information.csv', index=False)

# ---------------- Step 5: 分层 / 分箱 Kruskal-Wallis（局部依赖检查，强制执行） ----------------
def make_customer_bins(df_, name):
    if name == 'full':
        # 0 单独一档，其余按分位数切分（1,2-3,4-10,11-50,51+ 采用固定业务分箱，便于跨样本可比）
        bins = [-0.5, 0.5, 1.5, 3.5, 10.5, 50.5, np.inf]
        labels = ['0', '1', '2-3', '4-10', '11-50', '51+']
    else:
        bins = [0.5, 1.5, 3.5, 10.5, 50.5, np.inf]
        labels = ['1', '2-3', '4-10', '11-50', '51+']
    cat = pd.cut(df_['Number of Customers Restored'], bins=bins, labels=labels)
    return cat

kw_rows = []
strat_detail_rows = []
for name, df_ in datasets.items():
    df2 = df_.copy()
    df2['cust_bin'] = make_customer_bins(df2, name)
    groups = [g['log1p_duration'].to_numpy() for _, g in df2.groupby('cust_bin', observed=True) if len(g) >= 30]
    group_labels = [lbl for lbl, g in df2.groupby('cust_bin', observed=True) if len(g) >= 30]
    if len(groups) >= 2:
        h_stat, p_kw = kruskal(*groups)
    else:
        h_stat, p_kw = np.nan, np.nan
    # effect size: epsilon-squared = (H - k + 1) / (n - k)
    k = len(groups)
    n_tot = sum(len(g) for g in groups)
    eps_sq = (h_stat - k + 1) / (n_tot - k) if n_tot > k else np.nan
    kw_rows.append({'sample': name, 'n_groups': k, 'n_total': n_tot, 'H_statistic': h_stat,
                     'p_value': p_kw, 'epsilon_squared_effect_size': eps_sq})
    for lbl, g in df2.groupby('cust_bin', observed=True):
        if len(g) < 30:
            continue
        strat_detail_rows.append({
            'sample': name, 'customer_bin': str(lbl), 'n': len(g),
            'log1p_duration_median': float(g.log1p_duration.median()),
            'log1p_duration_mean': float(g.log1p_duration.mean()),
            'log1p_duration_p25': float(g.log1p_duration.quantile(0.25)),
            'log1p_duration_p75': float(g.log1p_duration.quantile(0.75)),
        })

kw_df = pd.DataFrame(kw_rows)
kw_df.to_csv(OUT + '/04_kruskal_wallis_stratified.csv', index=False)
strat_df = pd.DataFrame(strat_detail_rows)
strat_df.to_csv(OUT + '/04b_stratified_duration_by_customer_bin_detail.csv', index=False)
print(kw_df)
print(strat_df)

# ---------------- Step 6: 可视化 ----------------
# 6a. 2D hexbin (全样本)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, (name, df_) in zip(axes, datasets.items()):
    hb = ax.hexbin(df_['log1p_customers'], df_['log1p_duration'], gridsize=45, cmap='viridis', mincnt=1, bins='log')
    ax.set_xlabel('log1p(customers)')
    ax.set_ylabel('log1p(duration)')
    ax.set_title(f'{name} (n={len(df_)})')
    plt.colorbar(hb, ax=ax, label='log10(count)')
fig.suptitle('2D hexbin: log1p(customers) vs log1p(duration)')
fig.tight_layout()
fig.savefig(FIG + '/01_hexbin_full_vs_subset.png', dpi=160)
plt.close(fig)

# 6b. boxplot/violin by customer bin (full sample)
df_full_binned = d.copy()
df_full_binned['cust_bin'] = make_customer_bins(df_full_binned, 'full')
order = ['0', '1', '2-3', '4-10', '11-50', '51+']
data_by_bin = [df_full_binned[df_full_binned['cust_bin'] == b]['log1p_duration'].to_numpy() for b in order
               if (df_full_binned['cust_bin'] == b).sum() >= 30]
labels_present = [b for b in order if (df_full_binned['cust_bin'] == b).sum() >= 30]

fig, ax = plt.subplots(figsize=(7, 5))
vp = ax.violinplot(data_by_bin, showmedians=True)
ax.set_xticks(range(1, len(labels_present) + 1))
ax.set_xticklabels(labels_present)
ax.set_xlabel('customer count bin')
ax.set_ylabel('log1p(duration)')
ax.set_title('log1p(duration) distribution by customer-count bin (full sample)')
fig.tight_layout()
fig.savefig(FIG + '/02_violin_duration_by_customer_bin.png', dpi=160)
plt.close(fig)

total_elapsed = time.time() - t_start
summary = {
    'step1_sample_summary': step1_summary,
    'spearman': spearman_rows,
    'distance_correlation': dcor_rows,
    'mutual_information': mi_rows,
    'kruskal_wallis': kw_rows,
    'total_elapsed_sec': total_elapsed,
}
json.dump(summary, open(OUT + '/99_all_steps_summary.json', 'w'), indent=2, default=str)
print('TOTAL ELAPSED (sec):', total_elapsed)
print('DONE')
