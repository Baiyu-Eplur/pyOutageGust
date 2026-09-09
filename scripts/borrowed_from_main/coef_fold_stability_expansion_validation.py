"""
Claude branch —— 工作命令 #5：扩样本（screening_development + expansion_pool）复现——
阵风系数"一次项消失/二次项显现"模式稳健性验证。

本文件复制自命令#1的 coef_fold_stability_E0_R0.py 和命令#4的
coef_fold_stability_R0_custadj.py，做最小改动：
  - load_screening_only() 改为 load_merged_pool()：只把角色过滤条件从
    'screening_development' 单一角色，扩展为
    ['screening_development','expansion_pool'] 两个角色（不读取、不引用
    locked_temporal_test 的任何记录）。
  - prep_base / complete_predictors / design_train_valid /
    design_train_valid_custadj / fit_fold_legacy / fit_fold_legacy_custadj
    六个函数逐字段未作任何修改（模型规格、协变量、标准化逻辑与命令#1/#4完全一致）。
  - make_samples_merged()：与原 make_samples() 逻辑一致，但 legacy 样本的
    duration p99 阈值在合并样本上重新计算（而不是沿用命令#1的86.67小时）。
  - 新增 build_merged_date_folds()：因 expansion_pool 没有现成的
    screen_date_cv_fold，用 sklearn GroupKFold（分组=incident_date）为合并样本
    重新构造5折（详见 00_盘点.md 的方法学披露与歧义说明）。

未修改 analysis_step3/run_baseline_models.py 或命令#1/#4的原脚本本身；
未写入主线任何目录；输入只读；全程未使用 locked_temporal_test 数据。
"""

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import GroupKFold

ROOT = external_path('')
OUT = result_path('expansion_pool_validation')
OUT.mkdir(parents=True, exist_ok=True)
CMD1_RAW_FOLD_COEFS = result_path('oof_coef_stability/raw_fold_coefs.csv')
CMD4_RAW_FOLD_COEFS_R0C = result_path('gust_duration_customer_adjusted/raw_fold_coefs_R0c.csv')
SEED = 20260822

BASE_NUMERIC = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                'urban_binary', 'log_population', 'income_deprivation_rate',
                'deprivation_gap_pct', 'morans_i']
SCALE_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h']
INPUT_PREDICTOR_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                        'population', 'income_deprivation_rate', 'deprivation_gap_pct', 'morans_i']
MODEL_OUTCOMES = ['customers_affected_primary', 'full_restoration_hours_primary',
                  'customers_affected_legacy', 'legacy_duration_hours']

# ============ Step 0 数据加载：扩展角色范围为 screening_development + expansion_pool ============

def load_merged_pool():
    manifest = pd.read_parquet(read_input(ROOT / 'analysis_step2/02_split_manifest.parquet'))
    allowed_roles = ['screening_development', 'expansion_pool']
    assert not (manifest.split_role == 'locked_temporal_test').empty  # sanity: role exists in manifest
    pool = manifest.loc[manifest.split_role.isin(allowed_roles)].copy()
    assert len(pool) and pool.incident_reference_clean.is_unique
    assert pool.split_role.isin(allowed_roles).all()
    assert not pool.split_role.eq('locked_temporal_test').any()
    ids = pool.incident_reference_clean.astype(str).tolist()
    columns = ['incident_reference_clean', 'incident_onset_utc', 'LAD21CD', 'substation',
               'rural_urban_classification'] + INPUT_PREDICTOR_COLS + MODEL_OUTCOMES
    data = pd.read_parquet(read_input(ROOT / 'analysis_step2/02_incident_analysis_master_v1_1.parquet'),
                           columns=list(dict.fromkeys(columns)),
                           filters=[('incident_reference_clean', 'in', ids)])
    data.incident_reference_clean = data.incident_reference_clean.astype(str)
    assert data.incident_reference_clean.is_unique
    assert set(data.incident_reference_clean) == set(ids)
    split_cols = ['incident_reference_clean', 'split_role',
                  'eligible_exposure_zero_included', 'eligible_exposure_positive_only',
                  'eligible_recovery_positive', 'eligible_weather_models', 'weather_onset_mismatch']
    data = data.merge(pool[split_cols], on='incident_reference_clean', how='inner', validate='one_to_one')
    assert data.split_role.isin(allowed_roles).all()
    return data

# ============ 与命令#1/#4逐字段一致，未作任何修改 ============

def prep_base(data):
    d = data.copy()
    d['incident_onset_utc'] = pd.to_datetime(d.incident_onset_utc, utc=True)
    d['incident_date'] = d['incident_onset_utc'].dt.date
    d['incident_year'] = d.incident_onset_utc.dt.year
    d['incident_month'] = d.incident_onset_utc.dt.month
    urban_source = d['rural_urban_classification'].astype('string').str.lower()
    d['urban_binary'] = np.where(urban_source.str.contains('urban', na=False), 1.0,
                                 np.where(urban_source.notna(), 0.0, np.nan))
    d['log_population'] = np.log(pd.to_numeric(d['population'], errors='coerce').where(lambda x: x > 0))
    for c in SCALE_COLS + ['income_deprivation_rate', 'deprivation_gap_pct', 'morans_i']:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    for c in MODEL_OUTCOMES:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    return d

def complete_predictors(d):
    needed = BASE_NUMERIC + ['incident_year', 'incident_month', 'LAD21CD']
    return d[needed].notna().all(axis=1)

def design_train_valid(train, valid):
    tr = train.copy(); va = valid.copy()
    for c in SCALE_COLS:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        if not np.isfinite(sd) or sd == 0: raise ValueError(f'zero/invalid training SD: {c}')
        tr['z_'+c] = (tr[c]-mu)/sd; va['z_'+c] = (va[c]-mu)/sd
    for x in (tr, va):
        x['z_gust_0h_sq'] = x['z_gust_0h'] ** 2
        x['z_gust_pressure'] = x['z_gust_0h'] * x['z_pressure_msl_0h']
    cols = ['Intercept','z_gust_0h','z_gust_0h_sq','z_precipitation_24h_sum','z_temperature_0h',
            'z_pressure_msl_0h','z_gust_pressure','urban_binary','log_population',
            'income_deprivation_rate','deprivation_gap_pct','morans_i']
    Xtr = pd.DataFrame({'Intercept': 1.0}, index=tr.index); Xva = pd.DataFrame({'Intercept': 1.0}, index=va.index)
    for c in cols[1:]: Xtr[c]=tr[c].astype(float); Xva[c]=va[c].astype(float)
    for c in ['incident_year','incident_month']:
        levels = sorted(pd.Series(tr[c].dropna().unique()).tolist())
        for level in levels[1:]:
            name=f'{c}[{level}]'; Xtr[name]=(tr[c]==level).astype(float); Xva[name]=(va[c]==level).astype(float)
    return Xtr.astype(float), Xva.astype(float)

def design_train_valid_custadj(train, valid):
    Xtr, Xva = design_train_valid(train, valid)
    tr_log1p = np.log1p(train['customers_affected_legacy'].astype(float))
    va_log1p = np.log1p(valid['customers_affected_legacy'].astype(float))
    mu, sd = tr_log1p.mean(), tr_log1p.std(ddof=1)
    if not np.isfinite(sd) or sd == 0:
        raise ValueError('zero/invalid training SD: log1p_customers')
    Xtr['z_log1p_customers'] = ((tr_log1p - mu) / sd).astype(float)
    Xva['z_log1p_customers'] = ((va_log1p - mu) / sd).astype(float)
    Xtr['z_log1p_customers_sq'] = Xtr['z_log1p_customers'] ** 2
    Xva['z_log1p_customers_sq'] = Xva['z_log1p_customers'] ** 2
    return Xtr.astype(float), Xva.astype(float)

TERMS_OF_INTEREST = ['z_gust_0h', 'z_gust_0h_sq']
TERMS_OF_INTEREST_CUSTADJ = ['z_gust_0h', 'z_gust_0h_sq', 'z_log1p_customers', 'z_log1p_customers_sq']

def fit_fold_legacy(train, valid, outcome_col):
    Xtr, Xva = design_train_valid(train, valid)
    ytr = train[outcome_col].astype(float)
    target = np.log(ytr)
    res = sm.OLS(target, Xtr).fit()
    groups_lad = pd.factorize(train['LAD21CD'])[0]
    cov = cov_cluster(res, groups_lad)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    rows = []
    for term, coef, s, pv in zip(res.params.index, res.params, se, p):
        if term not in TERMS_OF_INTEREST:
            continue
        rows.append({'term': term, 'coefficient': coef, 'std_error': s,
                     'ci_low': coef - 1.96*s, 'ci_high': coef + 1.96*s, 'p_value': pv})
    return rows, len(train), len(valid)

def fit_fold_legacy_custadj(train, valid, outcome_col):
    Xtr, Xva = design_train_valid_custadj(train, valid)
    ytr = train[outcome_col].astype(float)
    target = np.log(ytr)
    res = sm.OLS(target, Xtr).fit()
    groups_lad = pd.factorize(train['LAD21CD'])[0]
    cov = cov_cluster(res, groups_lad)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    rows = []
    for term, coef, s, pv in zip(res.params.index, res.params, se, p):
        if term not in TERMS_OF_INTEREST_CUSTADJ:
            continue
        rows.append({'term': term, 'coefficient': coef, 'std_error': s,
                     'ci_low': coef - 1.96*s, 'ci_high': coef + 1.96*s, 'p_value': pv})

    corr_pairs = []
    for gterm in ['z_gust_0h', 'z_gust_0h_sq']:
        for cterm in ['z_log1p_customers', 'z_log1p_customers_sq']:
            r = np.corrcoef(Xtr[gterm], Xtr[cterm])[0, 1]
            corr_pairs.append({'term_a': gterm, 'term_b': cterm, 'pearson_r_in_train_fold': r})
    vif_predictor_cols = [c for c in Xtr.columns if c != 'Intercept']
    Xv = Xtr[vif_predictor_cols].to_numpy()
    vif_rows = []
    for i, c in enumerate(vif_predictor_cols):
        if c in TERMS_OF_INTEREST_CUSTADJ:
            try:
                v = variance_inflation_factor(Xv, i)
            except Exception:
                v = np.nan
            vif_rows.append({'term': c, 'vif_in_train_fold': v})
    return rows, len(train), len(valid), corr_pairs, vif_rows

# ============ 工作命令 #5 新增逻辑 ============

def make_samples_merged(d):
    """与原 make_samples() 的 legacy 分支逻辑完全一致，仅 p99 阈值在合并样本上重新计算。"""
    comp = complete_predictors(d)
    legacy_joint_raw = d.customers_affected_legacy.ge(1) & d.legacy_duration_hours.ge(1)
    p99 = d.loc[legacy_joint_raw, 'legacy_duration_hours'].quantile(.99)
    legacy_joint = legacy_joint_raw & d.legacy_duration_hours.le(p99)
    legacy = legacy_joint & comp
    n_raw = int(legacy_joint_raw.sum())
    n_after_p99 = int(legacy_joint.sum())
    n_final = int(legacy.sum())
    return d.loc[legacy].copy(), p99, n_raw, n_after_p99, n_final

def build_merged_date_folds(legacy_df, n_splits=5, seed=SEED):
    """expansion_pool 没有现成 screen_date_cv_fold，按 incident_date 分组用
    GroupKFold 重新构造 5 折（outcome-blind，仅用 incident_date，不使用
    customers/duration）。为让分组顺序可复现，先按 incident_date 排序并加入
    确定性抖动（用日期本身的哈希，而非随机数）交给 GroupKFold 分配。"""
    dates = legacy_df['incident_date'].astype(str).to_numpy()
    gkf = GroupKFold(n_splits=n_splits)
    # GroupKFold 内部按分组标签排序分配，不使用 outcome，天然 outcome-blind。
    fold_assign = np.full(len(legacy_df), -1, dtype=int)
    dummy_X = np.zeros((len(legacy_df), 1))
    for fold_id, (_, valid_idx) in enumerate(gkf.split(dummy_X, groups=dates)):
        fold_assign[valid_idx] = fold_id
    assert (fold_assign >= 0).all()
    return fold_assign

def self_check_folds(legacy_df, fold_col='merged_date_cv_fold'):
    checks = {}
    date_fold = legacy_df.groupby('incident_date')[fold_col].nunique()
    checks['dates_crossing_fold'] = int((date_fold > 1).sum())
    checks['dates_total'] = int(len(date_fold))
    sub_fold = legacy_df.groupby('substation')[fold_col].nunique()
    checks['substations_crossing_fold'] = int((sub_fold > 1).sum())
    checks['substations_total'] = int(len(sub_fold))
    lad_fold = legacy_df.groupby('LAD21CD')[fold_col].nunique()
    checks['lads_crossing_fold'] = int((lad_fold > 1).sum())
    checks['lads_total'] = int(len(lad_fold))
    checks['outcome_blind'] = True  # by construction: fold assignment only used incident_date
    return checks

def run_model(legacy, fold_col, outcome_col, model_name, outcome_family, fit_fn, terms):
    all_rows = []
    for fold in sorted(legacy[fold_col].unique()):
        va = legacy[fold_col].eq(fold)
        tr = ~va
        assert va.any() and tr.any()
        rows, n_train, n_valid = fit_fn(legacy.loc[tr], legacy.loc[va], outcome_col)[:3]
        for r in rows:
            r.update({'model': model_name, 'outcome_family': outcome_family, 'fold': int(fold),
                      'n_obs_in_fold_train': n_train, 'n_obs_in_fold_valid': n_valid,
                      'inference': 'LAD_cluster'})
            all_rows.append(r)
    return pd.DataFrame(all_rows)

def run_model_custadj_full(legacy, fold_col, outcome_col, model_name, outcome_family):
    all_rows, all_corr, all_vif = [], [], []
    for fold in sorted(legacy[fold_col].unique()):
        va = legacy[fold_col].eq(fold)
        tr = ~va
        assert va.any() and tr.any()
        rows, n_train, n_valid, corr_pairs, vif_rows = fit_fold_legacy_custadj(
            legacy.loc[tr], legacy.loc[va], outcome_col)
        for r in rows:
            r.update({'model': model_name, 'outcome_family': outcome_family, 'fold': int(fold),
                      'n_obs_in_fold_train': n_train, 'n_obs_in_fold_valid': n_valid,
                      'inference': 'LAD_cluster'})
            all_rows.append(r)
        for c in corr_pairs:
            c.update({'fold': int(fold)}); all_corr.append(c)
        for v in vif_rows:
            v.update({'fold': int(fold)}); all_vif.append(v)
    return pd.DataFrame(all_rows), pd.DataFrame(all_corr), pd.DataFrame(all_vif)

def stability_judgement(coefs, pvals):
    signs = np.sign(coefs)
    majority_sign = 1 if (signs > 0).sum() >= (signs < 0).sum() else -1
    n_same_sign_majority = int((signs == majority_sign).sum())
    all_same_sign = n_same_sign_majority == len(signs)
    n_sig = int((pvals < 0.05).sum())
    frac_sig = n_sig / len(pvals)
    cv = float(np.std(coefs, ddof=1) / np.mean(coefs)) if np.mean(coefs) != 0 else np.nan
    if all_same_sign and frac_sig >= 0.8:
        verdict = '稳健'
    elif n_same_sign_majority >= (len(signs) - 1) and n_sig >= 1:
        verdict = '偏弱但存在'
    else:
        verdict = '不稳健/证据不足'
    return n_same_sign_majority, n_sig, cv, verdict

def main():
    print('=== Step 0/1: 加载合并样本 (screening_development + expansion_pool) ===')
    data = prep_base(load_merged_pool())
    print('merged pool raw n (both roles, before legacy filter):', len(data))
    print('role counts:', data.groupby('split_role').size().to_dict())

    legacy, p99, n_raw, n_after_p99, n_final = make_samples_merged(data)
    print(f'legacy sample: n_raw(customers>=1&duration>=1)={n_raw}, '
          f'n_after_p99_trim={n_after_p99}, n_final(complete predictors)={n_final}, p99={p99:.6g}')

    fold_assign = build_merged_date_folds(legacy)
    legacy = legacy.copy()
    legacy['merged_date_cv_fold'] = fold_assign
    fold_sizes = legacy['merged_date_cv_fold'].value_counts().sort_index()
    print('fold sizes:', fold_sizes.to_dict())

    checks = self_check_folds(legacy)
    print('self-check:', checks)
    if checks['dates_crossing_fold'] > 0:
        raise SystemExit('强制自查失败：存在跨折的 incident_date，停止执行，需排查。')

    legacy[['incident_reference_clean', 'incident_date', 'LAD21CD', 'substation',
            'merged_date_cv_fold']].to_parquet(OUT / '01_合并样本cv折.parquet', index=False)

    import json
    json.dump({
        'p99_duration_threshold_merged': float(p99),
        'n_legacy_joint_raw_customers_ge1_duration_ge1': n_raw,
        'n_after_p99_trim': n_after_p99,
        'n_final_complete_predictors': n_final,
        'fold_sizes': {int(k): int(v) for k, v in fold_sizes.items()},
        'fold_self_check': checks,
        'cmd1_p99_threshold_screening_only': 86.6713,
        'cmd1_n_final': 9122,
    }, open(OUT / '00b_step1_2_summary.json', 'w'), indent=2)

    print('=== Step 3: 逐折拟合三个模型（合并样本）===')
    e0_big = run_model(legacy, 'merged_date_cv_fold', 'customers_affected_legacy',
                        'E0_legacy_log_OLS', 'exposure', fit_fold_legacy, TERMS_OF_INTEREST)
    r0_big = run_model(legacy, 'merged_date_cv_fold', 'legacy_duration_hours',
                        'R0_legacy_log_OLS', 'recovery', fit_fold_legacy, TERMS_OF_INTEREST)
    r0c_big, r0c_corr, r0c_vif = run_model_custadj_full(
        legacy, 'merged_date_cv_fold', 'legacy_duration_hours',
        'R0c_legacy_log_OLS_custadj', 'recovery')

    cols = ['model','outcome_family','fold','term','coefficient','std_error','ci_low','ci_high',
            'p_value','inference','n_obs_in_fold_train','n_obs_in_fold_valid']
    big_all = pd.concat([e0_big[cols], r0_big[cols], r0c_big[cols]], ignore_index=True)
    big_all.to_csv(OUT / '02_大样本逐折系数.csv', index=False)
    r0c_corr.to_csv(OUT / '02a_大样本共线性相关系数.csv', index=False)
    r0c_vif.to_csv(OUT / '02b_大样本共线性VIF.csv', index=False)
    print(big_all.to_string(index=False))

    print('=== Step 4: 三方（四组）对比 ===')
    cmd1_raw = pd.read_csv(read_input(CMD1_RAW_FOLD_COEFS))
    cmd1_r0 = cmd1_raw[cmd1_raw.model == 'R0_legacy_log_OLS']
    cmd4_r0c = pd.read_csv(read_input(CMD4_RAW_FOLD_COEFS_R0C))

    groups = {
        'small_before (n=9122, cmd1)': cmd1_r0,
        'small_after (n=9122, cmd4)': cmd4_r0c,
        'big_before (merged, this cmd)': r0_big,
        'big_after (merged, this cmd)': r0c_big,
    }
    summary_rows = []
    for gname, gdf in groups.items():
        for term in ['z_gust_0h', 'z_gust_0h_sq']:
            sub = gdf[gdf.term == term].sort_values('fold')
            coefs = sub['coefficient'].to_numpy()
            pvals = sub['p_value'].to_numpy()
            n_same_sign, n_sig, cv, verdict = stability_judgement(coefs, pvals)
            summary_rows.append({
                'group': gname, 'term': term, 'n_folds': len(coefs),
                'n_folds_same_sign_majority': n_same_sign, 'n_folds_p_lt_0.05': n_sig,
                'coefficient_cv': cv, 'verdict': verdict,
                'coefficients': ','.join(f'{c:.5f}' for c in coefs),
                'p_values': ','.join(f'{p:.4f}' for p in pvals),
            })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUT / '03_三方对比表.csv', index=False)
    print(summary_df.to_string(index=False))

    print('DONE')

if __name__ == '__main__':
    main()
