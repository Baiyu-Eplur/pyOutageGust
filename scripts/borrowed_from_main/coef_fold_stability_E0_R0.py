"""
Claude branch — 借用自 analysis_step3/run_baseline_models.py 的只读函数
（load_screening_only / prep_base / make_samples / design_train_valid，逻辑未作任何修改，
仅调整了 ROOT 路径以指向本地只读镜像），在此基础上新增：对 E0_legacy_log_OLS /
R0_legacy_log_OLS（即与 v6 论文口径一致的 legacy 规格）做逐折（screen_date_cv_fold 0-4）
拟合，并对每一折的 z_gust_0h / z_gust_0h_sq 系数计算 LAD 聚类稳健标准误、95% CI、p 值，
导出为 raw_fold_coefs.csv。

未修改 analysis_step3/run_baseline_models.py 本身；未写入主线任何目录；输入只读。
对应执行指令：作命令 #1（检验阵风系数在样本外交叉验证中的稳定性），Step 2 路径 B。
"""

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster

# 只读镜像根目录（本地云端沙箱内的 STST2603 只读快照，非用户设备原路径）
ROOT = external_path('')
OUT = result_path('oof_coef_stability')
OUT.mkdir(parents=True, exist_ok=True)

BASE_NUMERIC = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                'urban_binary', 'log_population', 'income_deprivation_rate',
                'deprivation_gap_pct', 'morans_i']
SCALE_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h']
INPUT_PREDICTOR_COLS = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h',
                        'population', 'income_deprivation_rate', 'deprivation_gap_pct', 'morans_i']
MODEL_OUTCOMES = ['customers_affected_primary', 'full_restoration_hours_primary',
                  'customers_affected_legacy', 'legacy_duration_hours']

# ---- 以下四个函数逐字段对应 analysis_step3/run_baseline_models.py 的同名函数，
# ---- 未改变任何拟合/筛选/标准化逻辑，仅把 ROOT 指向本地只读镜像。 ----

def load_screening_only():
    manifest = pd.read_parquet(read_input(ROOT / 'analysis_step2/02_split_manifest.parquet'))
    screen = manifest.loc[manifest.split_role.eq('screening_development')].copy()
    assert len(screen) and screen.incident_reference_clean.is_unique
    ids = screen.incident_reference_clean.astype(str).tolist()
    columns = ['incident_reference_clean', 'incident_onset_utc', 'LAD21CD',
               'rural_urban_classification'] + INPUT_PREDICTOR_COLS + MODEL_OUTCOMES
    data = pd.read_parquet(read_input(ROOT / 'analysis_step2/02_incident_analysis_master_v1_1.parquet'),
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

# ---- 以下为本次新增逻辑：对 E0/R0 legacy 规格逐折拟合并导出 z_gust_0h / z_gust_0h_sq 的
# ---- 系数、LAD 聚类稳健标准误、95% CI 与 p 值。拟合逻辑（OLS on log(y)，标准化仅用训练折）
# ---- 与 run_baseline_models.py 的 fit_ols + coefficient_rows 完全一致，只是把二者合并，
# ---- 并按折（而不是按全样本单次拟合）输出。 ----

TERMS_OF_INTEREST = ['z_gust_0h', 'z_gust_0h_sq']

def fit_fold_legacy(train, valid, outcome_col):
    Xtr, Xva = design_train_valid(train, valid)
    ytr = train[outcome_col].astype(float)
    target = np.log(ytr)  # E0/R0 均为 is_log1p=False -> log(y)，与 run_baseline_models.cv_models 一致
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

def run_model(samples_legacy, outcome_col, model_name, outcome_family):
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

    e0 = run_model(legacy, 'customers_affected_legacy', 'E0_legacy_log_OLS', 'exposure')
    r0 = run_model(legacy, 'legacy_duration_hours', 'R0_legacy_log_OLS', 'recovery')
    out = pd.concat([e0, r0], ignore_index=True)
    cols = ['model','outcome_family','fold','term','coefficient','std_error','ci_low','ci_high',
            'p_value','inference','n_obs_in_fold_train','n_obs_in_fold_valid']
    out = out[cols]
    out.to_csv(OUT / 'raw_fold_coefs.csv', index=False)
    print(out.to_string(index=False))
    print('legacy_p99', legacy_p99, 'legacy_n', len(legacy))

if __name__ == '__main__':
    main()
