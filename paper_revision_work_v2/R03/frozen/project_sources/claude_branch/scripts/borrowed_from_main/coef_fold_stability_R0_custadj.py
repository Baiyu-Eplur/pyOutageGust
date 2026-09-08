"""
Claude branch —— 工作命令 #4：控制 customers（调度优先级代理变量）后，
重新检验阵风—恢复时长（R0_legacy_log_OLS）系数的样本外稳定性。

本文件是 `claude_branch/scripts/borrowed_from_main/coef_fold_stability_E0_R0.py`
（工作命令 #1 产出）的复制件，最小化改动：
  - load_screening_only / prep_base / complete_predictors / make_samples /
    design_train_valid / fit_fold_legacy 四个数据加载与原始 R0 拟合函数
    **逐字段未作任何修改**（仅 ROOT 路径不变，仍指向本地只读镜像）。
  - 新增 design_train_valid_custadj()：在原 design_train_valid() 返回的设计矩阵基础上，
    追加 log1p(customers_affected_legacy) 的一次项与二次项，标准化方式
    （用训练折均值/标准差做 z-score，再取平方）与阵风项（z_gust_0h / z_gust_0h_sq）
    完全一致的处理逻辑。
  - 新增 fit_fold_legacy_custadj()：在新设计矩阵上重新拟合 R0c_legacy_log_OLS_custadj，
    导出阵风两项 + customers 两项的系数/LAD聚类稳健SE/95% CI/p值。
  - 新增 collinearity 诊断（相关系数 + VIF）。
  - Step 1 会先用未改动的 fit_fold_legacy() 重跑一次原始 R0_legacy_log_OLS，
    与命令#1的 raw_fold_coefs.csv 做逐折数值核对，确认可复现后才继续。

未修改 analysis_step3/run_baseline_models.py 或命令#1的原脚本本身；
未写入主线任何目录；输入只读。
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path('/mnt/user-data/uploads/STST2603')
OUT = Path('/tmp/branch_work4/results/gust_duration_customer_adjusted')
OUT.mkdir(parents=True, exist_ok=True)
CMD1_RAW_FOLD_COEFS = Path('/tmp/branch_work/results/oof_coef_stability/raw_fold_coefs.csv')

BASE_NUMERIC = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                'urban_binary', 'log_population', 'income_deprivation_rate',
                'deprivation_gap_pct', 'morans_i']
SCALE_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h']
INPUT_PREDICTOR_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                        'population', 'income_deprivation_rate', 'deprivation_gap_pct', 'morans_i']
MODEL_OUTCOMES = ['customers_affected_primary', 'full_restoration_hours_primary',
                  'customers_affected_legacy', 'legacy_duration_hours']

# ============ 以下四个函数 + fit_fold_legacy：与命令#1脚本逐字段一致，未作任何修改 ============

def load_screening_only():
    manifest = pd.read_parquet(ROOT / 'analysis_step2/02_split_manifest.parquet')
    screen = manifest.loc[manifest.split_role.eq('screening_development')].copy()
    assert len(screen) and screen.incident_reference_clean.is_unique
    ids = screen.incident_reference_clean.astype(str).tolist()
    columns = ['incident_reference_clean', 'incident_onset_utc', 'LAD21CD',
               'rural_urban_classification'] + INPUT_PREDICTOR_COLS + MODEL_OUTCOMES
    data = pd.read_parquet(ROOT / 'analysis_step2/02_incident_analysis_master_v1_1.parquet',
                           columns=list(dict.fromkeys(columns)),
                           filters=[('incident_reference_clean', 'in', ids)])
    data.incident_reference_clean = data.incident_reference_clean.astype(str)
    assert data.incident_reference_clean.is_unique
    assert set(data.incident_reference_clean) == set(ids)
    split_cols = ['incident_reference_clean','split_role','screen_date_cv_fold',
                  'eligible_exposure_zero_included','eligible_exposure_positive_only',
                  'eligible_recovery_positive','eligible_weather_models','weather_onset_mismatch']
    data = data.merge(screen[split_cols], on='incident_reference_clean', how='inner', validate='one_to_one')
    assert data.split_role.eq('screening_development').all()
    assert data.screen_date_cv_fold.notna().all()
    return data

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

def make_samples(d):
    comp = complete_predictors(d)
    allmask = pd.Series(True, index=d.index)
    ex = allmask.copy()
    ex &= d.eligible_exposure_zero_included.fillna(False)
    ex &= d.eligible_weather_models.fillna(False)
    ex &= d.customers_affected_primary.notna()
    ex &= comp
    exp_pos = ex & d.customers_affected_primary.gt(0)

    rec = allmask.copy()
    rec &= d.eligible_recovery_positive.fillna(False)
    rec &= d.eligible_weather_models.fillna(False)
    rec &= d.full_restoration_hours_primary.gt(0)
    rec &= comp

    legacy_joint_raw = d.customers_affected_legacy.ge(1) & d.legacy_duration_hours.ge(1)
    p99 = d.loc[legacy_joint_raw, 'legacy_duration_hours'].quantile(.99)
    legacy_joint = legacy_joint_raw & d.legacy_duration_hours.le(p99)
    legacy = legacy_joint & comp
    return {'exposure': d.loc[ex].copy(), 'exposure_positive': d.loc[exp_pos].copy(),
            'recovery': d.loc[rec].copy(), 'legacy': d.loc[legacy].copy()}, p99

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

TERMS_OF_INTEREST = ['z_gust_0h', 'z_gust_0h_sq']

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

# ============ 以下为工作命令 #4 新增逻辑 ============

TERMS_OF_INTEREST_CUSTADJ = ['z_gust_0h', 'z_gust_0h_sq', 'z_log1p_customers', 'z_log1p_customers_sq']

def design_train_valid_custadj(train, valid):
    """在原 design_train_valid() 的设计矩阵基础上追加 log1p(customers) 一次/二次项。
    标准化方式与阵风项完全一致：用训练折的均值/标准差对 log1p(customers) 做 z-score，
    再对该 z 分数取平方作为二次项（与 z_gust_0h -> z_gust_0h_sq 的处理逻辑相同）。
    customers 变量取自 customers_affected_legacy（本样本定义要求 customers>=1，
    与 legacy 联合样本的构造条件一致，不存在 log1p(0) 的退化情况）。
    """
    Xtr, Xva = design_train_valid(train, valid)  # 原函数，未修改，直接调用
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

    # ---- 共线性诊断：相关系数 + VIF（Step 3）----
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
            except Exception as e:
                v = np.nan
            vif_rows.append({'term': c, 'vif_in_train_fold': v})

    return rows, len(train), len(valid), corr_pairs, vif_rows

def run_model_custadj(samples_legacy, outcome_col, model_name, outcome_family):
    all_rows = []
    all_corr = []
    all_vif = []
    for fold in range(5):
        va = samples_legacy.screen_date_cv_fold.astype(int).eq(fold)
        tr = ~va
        assert va.any() and tr.any()
        rows, n_train, n_valid, corr_pairs, vif_rows = fit_fold_legacy_custadj(
            samples_legacy.loc[tr], samples_legacy.loc[va], outcome_col)
        for r in rows:
            r.update({'model': model_name, 'outcome_family': outcome_family, 'fold': fold,
                      'n_obs_in_fold_train': n_train, 'n_obs_in_fold_valid': n_valid,
                      'inference': 'LAD_cluster'})
            all_rows.append(r)
        for c in corr_pairs:
            c.update({'fold': fold})
            all_corr.append(c)
        for v in vif_rows:
            v.update({'fold': fold})
            all_vif.append(v)
    return pd.DataFrame(all_rows), pd.DataFrame(all_corr), pd.DataFrame(all_vif)

def run_model_original(samples_legacy, outcome_col, model_name, outcome_family):
    """用未修改的 fit_fold_legacy() 重跑原始 R0，用于 Step 1 复现校验。"""
    all_rows = []
    for fold in range(5):
        va = samples_legacy.screen_date_cv_fold.astype(int).eq(fold)
        tr = ~va
        assert va.any() and tr.any()
        rows, n_train, n_valid = fit_fold_legacy(samples_legacy.loc[tr], samples_legacy.loc[va], outcome_col)
        for r in rows:
            r.update({'model': model_name, 'outcome_family': outcome_family, 'fold': fold,
                      'n_obs_in_fold_train': n_train, 'n_obs_in_fold_valid': n_valid,
                      'inference': 'LAD_cluster'})
            all_rows.append(r)
    return pd.DataFrame(all_rows)

def main():
    data = prep_base(load_screening_only())
    samples, legacy_p99 = make_samples(data)
    legacy = samples['legacy']
    assert legacy.screen_date_cv_fold.notna().all()
    print(f'legacy sample n={len(legacy)}; screening p99 duration cutoff={legacy_p99:.6g}')

    # ---- Step 1: 复现校验（未改动函数重跑原始 R0_legacy_log_OLS）----
    r0_repro = run_model_original(legacy, 'legacy_duration_hours', 'R0_legacy_log_OLS', 'recovery')
    cmd1_raw = pd.read_csv(CMD1_RAW_FOLD_COEFS)
    cmd1_r0 = cmd1_raw[cmd1_raw.model == 'R0_legacy_log_OLS'].copy()

    merged = r0_repro.merge(cmd1_r0, on=['model', 'outcome_family', 'fold', 'term'],
                             suffixes=('_repro', '_cmd1'))
    merged['abs_diff_coefficient'] = (merged['coefficient_repro'] - merged['coefficient_cmd1']).abs()
    merged['abs_diff_std_error'] = (merged['std_error_repro'] - merged['std_error_cmd1']).abs()
    merged['abs_diff_p_value'] = (merged['p_value_repro'] - merged['p_value_cmd1']).abs()
    max_diff_coef = merged['abs_diff_coefficient'].max()
    max_diff_se = merged['abs_diff_std_error'].max()
    max_diff_p = merged['abs_diff_p_value'].max()
    repro_n = r0_repro.drop_duplicates('fold').set_index('fold').sort_index()
    cmd1_n = cmd1_r0.drop_duplicates('fold').set_index('fold').sort_index()
    n_train_match = (repro_n['n_obs_in_fold_train'].to_numpy() == cmd1_n['n_obs_in_fold_train'].to_numpy()).all()
    n_valid_match = (repro_n['n_obs_in_fold_valid'].to_numpy() == cmd1_n['n_obs_in_fold_valid'].to_numpy()).all()

    repro_ok = (max_diff_coef < 1e-8) and (max_diff_se < 1e-8) and (max_diff_p < 1e-6) and n_train_match and n_valid_match
    merged.to_csv(OUT / '00_step1_repro_check.csv', index=False)
    print('=== Step 1 复现校验 ===')
    print(f'max abs diff coefficient={max_diff_coef:.3e}, std_error={max_diff_se:.3e}, p_value={max_diff_p:.3e}')
    print(f'n_train match={n_train_match}, n_valid match={n_valid_match}')
    print(f'REPRO_OK={repro_ok}')
    if not repro_ok:
        raise SystemExit('Step 1 复现校验未通过，停止执行，需先排查（见 00_step1_repro_check.csv）。')

    # ---- Step 2: 新增 customers 协变量，重新逐折拟合 R0c_legacy_log_OLS_custadj ----
    r0c_coefs, r0c_corr, r0c_vif = run_model_custadj(
        legacy, 'legacy_duration_hours', 'R0c_legacy_log_OLS_custadj', 'recovery')
    cols = ['model','outcome_family','fold','term','coefficient','std_error','ci_low','ci_high',
            'p_value','inference','n_obs_in_fold_train','n_obs_in_fold_valid']
    r0c_coefs = r0c_coefs[cols]
    r0c_coefs.to_csv(OUT / 'raw_fold_coefs_R0c.csv', index=False)
    print('=== Step 2 raw_fold_coefs_R0c.csv ===')
    print(r0c_coefs.to_string(index=False))

    # ---- Step 3: 共线性诊断 ----
    vif_df = r0c_corr.merge(r0c_vif.rename(columns={'term': 'term_a'}), on='fold', how='outer')
    # 更清晰的输出：相关系数表与 VIF 表分别保存，再拼一张宽表方便阅读
    r0c_corr.to_csv(OUT / '02a_gust_customers_correlation.csv', index=False)
    r0c_vif.to_csv(OUT / '02_共线性诊断_VIF.csv', index=False)
    print('=== Step 3 相关系数 ===')
    print(r0c_corr.to_string(index=False))
    print('=== Step 3 VIF ===')
    print(r0c_vif.to_string(index=False))

    # ---- Step 4: 新旧结果并排对比 ----
    orig = cmd1_r0[cmd1_r0.term.isin(['z_gust_0h', 'z_gust_0h_sq'])].copy()
    adj = r0c_coefs[r0c_coefs.term.isin(['z_gust_0h', 'z_gust_0h_sq'])].copy()
    rows = []
    for fold in range(5):
        row = {'fold': fold}
        for term, prefix in [('z_gust_0h', 'gust_linear'), ('z_gust_0h_sq', 'gust_quad')]:
            o = orig[(orig.fold == fold) & (orig.term == term)].iloc[0]
            a = adj[(adj.fold == fold) & (adj.term == term)].iloc[0]
            row[f'{prefix}_coef_orig'] = o.coefficient
            row[f'{prefix}_coef_custadj'] = a.coefficient
            row[f'{prefix}_p_orig'] = o.p_value
            row[f'{prefix}_p_custadj'] = a.p_value
        rows.append(row)
    comp_df = pd.DataFrame(rows)

    def stability_stats(coefs, pvals):
        signs = np.sign(coefs)
        sign_consistent_n = int((signs == signs[0]).sum())
        sig_n = int((pvals < 0.05).sum())
        cv = float(np.std(coefs, ddof=1) / np.mean(coefs)) if np.mean(coefs) != 0 else np.nan
        return sign_consistent_n, sig_n, cv

    summary_rows = []
    for term, prefix in [('z_gust_0h', 'gust_linear'), ('z_gust_0h_sq', 'gust_quad')]:
        for tag in ['orig', 'custadj']:
            coefs = comp_df[f'{prefix}_coef_{tag}'].to_numpy()
            pvals = comp_df[f'{prefix}_p_{tag}'].to_numpy()
            sign_n, sig_n, cv = stability_stats(coefs, pvals)
            summary_rows.append({'term': term, 'spec': tag, 'n_folds_same_sign': sign_n,
                                  'n_folds_p_lt_0.05': sig_n, 'coefficient_cv': cv})
    summary_df = pd.DataFrame(summary_rows)

    comp_df.to_csv(OUT / '03_控制前后对比表.csv', index=False)
    summary_df.to_csv(OUT / '03b_控制前后稳定性汇总.csv', index=False)
    print('=== Step 4 对比表 ===')
    print(comp_df.to_string(index=False))
    print('=== Step 4/5 稳定性汇总 ===')
    print(summary_df.to_string(index=False))

    print('DONE')

if __name__ == '__main__':
    main()
