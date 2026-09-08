"""
Test 1 - Step 0: 数据盘点。
只读来源说明：`data/new/ukpn_master_with_lad_features_updated.csv`（303MB）在设备桥两次
staging 均失败（upload failed，很可能是单文件体积超出传输预算），因此改用已在本地沙箱中的
`analysis_step2/02_incident_analysis_master_v1_1.parquet`（codex 自己的冻结 v1.1 主表，
62,928 行全量，非仅 screening_development 子集）里原样保留的 legacy 列
`Number of Customers Restored`（原始列名，未改名）与 `Duration (hours)`（与
`03_legacy_model_specification.md` 里记录的 master CSV 列名完全一致）。
这两列是否等于 master CSV 的对应列，用 codex 自己独立算的
`customers_affected_legacy` / `legacy_duration_hours` 做交叉核验（见下方一致性检查）。
"""
import pandas as pd
import numpy as np

PARQUET = '/mnt/user-data/uploads/STST2603/analysis_step2/02_incident_analysis_master_v1_1.parquet'

cols = ['incident_reference_clean', 'Number of Customers Restored', 'Duration (hours)',
        'incident_date', 'substation', 'LAD21CD', 'SiteFunctionalLocation',
        'customers_affected_legacy', 'legacy_duration_hours', 'split_role']
d = pd.read_parquet(PARQUET, columns=cols)
print('n rows total:', len(d))
print(d.dtypes)
print()
print('--- missingness ---')
print(d.isna().mean().sort_values(ascending=False))
print()
print('--- Number of Customers Restored describe ---')
print(d['Number of Customers Restored'].describe())
print('customers == 0 count/pct:', (d['Number of Customers Restored']==0).sum(), (d['Number of Customers Restored']==0).mean())
print('customers < 0 count:', (d['Number of Customers Restored']<0).sum())
print()
print('--- Duration (hours) describe ---')
print(d['Duration (hours)'].describe())
print('duration <= 0 count:', (d['Duration (hours)']<=0).sum())
print('duration missing count:', d['Duration (hours)'].isna().sum())
print()
print('--- cross-check master-style cols vs codex legacy reconstruction ---')
both = d.dropna(subset=['Number of Customers Restored','customers_affected_legacy'])
print('customers agree exactly:', (both['Number of Customers Restored']==both['customers_affected_legacy']).mean())
bothd = d.dropna(subset=['Duration (hours)','legacy_duration_hours'])
print('duration agree within 1e-6:', (np.abs(bothd['Duration (hours)']-bothd['legacy_duration_hours'])<1e-6).mean())
print('duration max abs diff:', np.abs(bothd['Duration (hours)']-bothd['legacy_duration_hours']).max())
print()
print('unique LAD21CD:', d['LAD21CD'].nunique())
print('unique substation:', d['substation'].nunique())
print('unique incident_date:', d['incident_date'].nunique())
print('date range:', d['incident_date'].min(), d['incident_date'].max())
print()
print(d[cols].head(3).to_string())
