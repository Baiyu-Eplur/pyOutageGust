"""Read-only source audit and isolated replication of the existing analysis.

Run with bundled CPython 3.12 and -B. Reuse installed project packages without
repairing its broken venv launcher. No historical project module is imported:
only explicitly reviewed, pure function definitions are loaded through AST.
All outputs are confined to results/code_audit_20260905.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parent
sys.path.insert(0, str(PROJECT / '.venv/Lib/site-packages'))
import numpy as np
import pandas as pd
import scipy
import statsmodels.api as sm
import sklearn
from scipy import stats
from sklearn.model_selection import GroupKFold
from statsmodels.stats.sandwich_covariance import cov_cluster

OUT = ROOT / 'results/code_audit_20260905'
OUT.mkdir(parents=True, exist_ok=True)
assert OUT.resolve().is_relative_to(ROOT.resolve())
SRC = PROJECT / 'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv'
C = 'customers_v2_event_excl_reinterruptions'
D = 'duration_B_full_span_hours'
ID = 'Incident Reference'
WEATHER = ['gust_0h', 'precipitation_24h_sum', 'temperature_0h', 'pressure_msl_0h']
REGION = ['urban_binary', 'log_population', 'income_deprivation_rate', 'deprivation_gap_pct', 'morans_i']


def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_pure(path, names, env):
    """Execute named definitions only, excluding imports and all top-level I/O."""
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), env)
    return env


def inventory():
    print('Inventory and historical-file baseline', flush=True)
    files = list((ROOT / 'scripts').rglob('*.py')) + list((PROJECT / 'rebuild_v3_full_stage').rglob('*.py'))
    files = [p for p in files if 'code_audit_20260905' not in p.parts]
    items = []
    for p in sorted(files):
        source = p.read_text(encoding='utf-8-sig')
        try:
            tree = ast.parse(source)
            funcs = [{'name': n.name, 'line': n.lineno, 'end': n.end_lineno} for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            refs = [{'line': n.lineno, 'value': n.value} for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and ('STST2603' in n.value or n.value.endswith(('.csv', '.json', '.parquet', '.py', '.png', '.pdf', '.pkl')))]
            io = [{'line': n.lineno, 'call': ast.unparse(n.func)} for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {'write_text','to_csv','to_parquet','savefig','mkdir','save','savetxt','to_pickle'}]
            items.append({'path': str(p), 'sha256': sha(p), 'lines': len(source.splitlines()), 'functions': funcs, 'file_references': refs, 'potential_writes': io, 'parse_error': None})
        except SyntaxError as e:
            items.append({'path': str(p), 'sha256': sha(p), 'parse_error': str(e)})
    write_json('script_inventory.json', items)
    pd.DataFrame([{'path': i['path'], 'lines': i.get('lines'), 'sha256': i['sha256'], 'parse_error': i['parse_error'], 'potential_write_count': len(i.get('potential_writes', []))} for i in items]).to_csv(OUT / 'script_inventory.csv', index=False, encoding='utf-8-sig')
    watched = [p for p in ROOT.rglob('*') if p.is_file() and 'code_audit_20260905' not in p.parts and p.suffix.lower() in {'.md','.py','.docx','.csv','.json','.png','.pdf'} and p.stat().st_size < 5_000_000]
    baseline = {str(p): sha(p) for p in watched}
    write_json('historical_files_before.json', baseline)
    write_json('runtime.json', {'executable': sys.executable, 'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'statsmodels': sm.__version__, 'sklearn': sklearn.__version__, 'project_package_path': sys.path[0]})
    return baseline


def source_and_samples():
    print('Reading raw stages and selected v3 columns', flush=True)
    raw = pd.read_csv(PROJECT / 'data/ukpn-iis.csv', dtype=str, keep_default_na=False)
    extras = [C, D, 'duration_A_customer_weighted_hours', 'weather_status_v3', 'cause_group_official', 'LAD21CD', 'population', 'income_deprivation_rate', 'deprivation_gap_pct', 'morans_i', 'rural_urban_classification', 'incident_date_utc', 'clean_start', 'wx_time_used_utc', 'incident_hour_in_window_24h', 'stage_row_count', 'source_row_number'] + WEATHER
    cols = list(dict.fromkeys(list(raw.columns) + extras))
    stage = pd.read_csv(SRC, usecols=cols, dtype={c: str for c in raw.columns}, keep_default_na=False, low_memory=False)
    source_equal = {c: bool(raw[c].equals(stage[c])) for c in raw.columns}
    for c in extras:
        if c not in {'weather_status_v3','cause_group_official','LAD21CD','rural_urban_classification','incident_date_utc','clean_start','wx_time_used_utc'}:
            stage[c] = pd.to_numeric(stage[c], errors='coerce')
    for c in ['LAD21CD','rural_urban_classification']:
        stage[c] = stage[c].replace('', np.nan)
    key = stage[ID].str.strip()
    starts = pd.to_datetime(stage['Start Date and Time'], utc=True, errors='coerce')
    ends = pd.to_datetime(stage['End Date and Time'], utc=True, errors='coerce')
    cust = pd.to_numeric(stage['Number of Customers Restored'].str.replace(',', '', regex=False), errors='coerce')
    repeat = stage['Re-interruption Stage'].str.strip().str.upper().isin(['Y', '1'])
    c_calc = cust.mask(repeat).groupby(key, dropna=False).sum(min_count=1)
    d_calc = (ends.groupby(key).max() - starts.groupby(key).min()).dt.total_seconds() / 3600
    durations = ((ends-starts).dt.total_seconds()/3600).mask(lambda x:x<0)
    a_calc = (cust*durations).groupby(key).sum(min_count=1) / cust.where(durations.notna()).groupby(key).sum(min_count=1).where(lambda x:x>0)
    evt = stage.drop_duplicates(ID).copy()
    comparisons = {}
    for name, calc in [(C,c_calc),(D,d_calc),('duration_A_customer_weighted_hours',a_calc)]:
        actual = stage[name]
        expected = key.map(calc)
        ok = np.isclose(actual, expected, rtol=1e-12, atol=1e-10, equal_nan=True)
        comparisons[name] = {'stage_rows_compared':len(ok),'mismatch_rows':int((~ok).sum()),'max_abs_difference':float(np.nanmax(np.abs(actual-expected)))}
    first_start = pd.to_datetime(evt['Start Date and Time'], utc=True, errors='coerce')
    min_start = evt[ID].map(starts.groupby(key).min())
    onset_diff = (first_start-min_start).dt.total_seconds()/3600
    cause_inconsistent = stage.groupby(ID)['Cause Code'].nunique()
    evt['incident_date_utc'] = pd.to_datetime(evt['incident_date_utc'], errors='coerce')
    matched = evt[evt['weather_status_v3'].eq('matched')].copy()
    matched['urban_binary'] = np.where(matched['rural_urban_classification'].astype('string').str.lower().str.contains('urban', na=False),1.0,np.where(matched['rural_urban_classification'].notna(),0.0,np.nan))
    matched['log_population'] = np.log(matched['population'].where(matched['population']>0))
    matched['incident_year'] = matched['incident_date_utc'].dt.year
    matched['incident_month'] = matched['incident_date_utc'].dt.month
    needed = WEATHER+REGION+['LAD21CD','incident_year','incident_month']
    complete = matched.loc[matched[needed].notna().all(axis=1)].copy()
    complete = complete[complete['incident_date_utc'].le('2024-03-31')].copy()
    wt = complete[complete['cause_group_official'].isin(['weather_natural','technical_asset'])].copy()
    # Match combined_sample_builder's earlier-period then later-period concatenation.
    wt = pd.concat([wt[wt['incident_date_utc'].lt('2023-09-30')],wt[wt['incident_date_utc'].ge('2023-09-30')]],ignore_index=True)
    def make(d):
        e = d[d[C].notna()].copy()
        e['log1p_customers_v2'] = np.log1p(e[C])
        rbase=d[d[D].notna() & d[D].gt(0)].copy()
        cap=rbase[D].quantile(.99)
        r=rbase[rbase[D].le(cap)&rbase[C].notna()].copy()
        r['log1p_customers_v2']=np.log1p(r[C]);r['log_duration_B_full_span_hours']=np.log(r[D])
        return e.reset_index(drop=True),r.reset_index(drop=True),float(cap)
    e,r,cap=make(wt)
    we,wr,wcap=make(wt[wt['cause_group_official'].eq('weather_natural')])
    masks={'main_E0':e,'main_R0c':r,'weather_E0':we,'weather_R0c':wr}
    flow={'raw_rows':len(raw),'v3_selected_rows':len(stage),'unique_incidents':len(evt),'weather_matched_events':len(matched),'complete_predictor_events_to_end':len(complete),'main_base':len(wt),'main_E0':len(e),'main_R0c':len(r),'weather_E0':len(we),'weather_R0c':len(wr),'main_duration_p99':cap,'weather_duration_p99':wcap,'weather_events_in_main_R0c':int(r['cause_group_official'].eq('weather_natural').sum()),'weather_only_additional_tail_exclusions':len(set(r.loc[r['cause_group_official'].eq('weather_natural'),ID])-set(wr[ID]))}
    for label,subset in [('development',wt[wt['incident_date_utc'].lt('2023-09-30')]),('later',wt[wt['incident_date_utc'].ge('2023-09-30')])]:
        a,b,k=make(subset);flow[label]={'base':len(subset),'E0':len(a),'R0c':len(b),'p99':k}
    stages_min = pd.to_numeric(stage['Restoration Stage'],errors='coerce').groupby(key).min()
    wx = pd.to_datetime(evt['wx_time_used_utc'],utc=True,errors='coerce')
    sample_features=[]
    for label,dd in masks.items():
        ids=set(dd[ID]);ef=evt[evt[ID].isin(ids)]
        idx=ef.index
        sample_features.append({'sample':label,'n':len(dd),'zero_customers':int(dd[C].eq(0).sum()),'minimum_stage_ge2':int(dd[ID].map(stages_min).ge(2).sum()),'first_source_row_not_earliest_start':int(onset_diff.loc[idx].fillna(0).ne(0).sum()),'weather_hour_not_first_source_hour':int((wx.loc[idx]-first_start.loc[idx].dt.floor('h')).dt.total_seconds().fillna(0).ne(0).sum()),'24h_window_not_24_rows':int(ef['incident_hour_in_window_24h'].ne(24).sum())})
        dd[[ID,'incident_date_utc','cause_group_official',C,D]].to_csv(OUT/f'{label}_sample_membership.csv',index=False)
    write_json('source_and_sample_checks.json',{'raw_source_columns_exact':source_equal,'aggregate_checks':comparisons,'first_source_not_earliest_events':int(onset_diff.fillna(0).ne(0).sum()),'cause_inconsistent_incidents':int(cause_inconsistent.gt(1).sum()),'sample_flow':flow,'sample_quality':sample_features,'input_sha256':{'raw':sha(PROJECT/'data/ukpn-iis.csv'),'v3':sha(SRC)}})
    print(json.dumps(flow),flush=True)
    return masks


def replicate(samples):
    env={'np':np,'pd':pd,'SCALE_COLS':WEATHER}
    load_pure(ROOT/'scripts/v3_validation/v3_validation_pipeline.py',['design_train_valid'],env)
    design=env['design_train_valid']
    all_fit=[];all_metrics=[];fold_rows=[];group_mapping={};comparisons=[]
    archives=ROOT/'results/final_combined_analysis/raw'
    for label,d in samples.items():
        print('Replicating '+label,flush=True)
        recovery='R0c' in label
        target='log_duration_B_full_span_hours' if recovery else 'log1p_customers_v2'
        if recovery:d['customers_v2_log1p']=d['log1p_customers_v2']
        extra=['customers_v2_log1p'] if recovery else None
        X,_=design(d,d,extra_scale_cols=extra)
        fit=sm.OLS(d[target],X).fit()
        cov=cov_cluster(fit,pd.factorize(d['LAD21CD'])[0]);se=np.sqrt(np.maximum(np.diag(cov),0))
        tab=pd.DataFrame({'term':X.columns,'coefficient':fit.params.values,'std_error':se,'p_value':2*stats.norm.sf(np.abs(fit.params.values/se))})
        tab.to_csv(OUT/f'{label}_full_coefficients.csv',index=False)
        old=archives/f"step1_{'R0c' if recovery else 'E0'}_final_full_coefs.csv"
        if label.startswith('main'):
            baseline=pd.read_csv(old).set_index('term');now=tab.set_index('term')
            comparisons.append({'sample':label,'archive':str(old),'max_abs_coef_diff':float((now['coefficient']-baseline['coefficient']).abs().max()),'max_abs_se_diff':float((now['std_error']-baseline['std_error']).abs().max())})
        all_fit.append({'sample':label,'n':len(d),'columns':X.shape[1],'rank':int(np.linalg.matrix_rank(X)),'r2_in_sample':float(fit.rsquared),'gust_mean':float(d['gust_0h'].mean()),'gust_sd':float(d['gust_0h'].std()),'physical_minimum_at_mean_pressure':float(d['gust_0h'].mean()-d['gust_0h'].std()*fit.params['z_gust_0h']/(2*fit.params['z_gust_0h_sq']))})
        # Verify gap is not an affine copy of the deprivation rate in model inputs.
        gap=np.linalg.lstsq(np.column_stack([np.ones(len(d)),d['income_deprivation_rate']]),d['deprivation_gap_pct'],rcond=None)[0]
        all_fit[-1]['gap_affine_residual_max']=float(np.abs(d['deprivation_gap_pct']-gap[0]-gap[1]*d['income_deprivation_rate']).max())
        groups=d['incident_date_utc'].dt.date.astype(str);folds=np.full(len(d),-1,dtype=int)
        for k,(_,ix) in enumerate(GroupKFold(5).split(d,groups=groups)):folds[ix]=k
        mapping=pd.DataFrame({'date':groups,'fold':folds}).drop_duplicates()
        assert not mapping['date'].duplicated().any()
        group_mapping[label]=dict(zip(mapping['date'],mapping['fold']))
        pd.DataFrame({ID:d[ID],'date':groups,'fold':folds}).to_csv(OUT/f'{label}_folds.csv',index=False)
        gcols=['z_gust_0h','z_gust_0h_sq','z_gust_pressure']
        ccols=['z_log1p_customers_v2','z_log1p_customers_v2_sq'] if recovery else []
        wxcols=['z_precipitation_24h_sum','z_temperature_0h','z_pressure_msl_0h']
        blocks={'regional_time':[c for c in X if c not in gcols+ccols+wxcols],'B':[c for c in X if c not in gcols+ccols],'BG':[c for c in X if c not in ccols]}
        if recovery:blocks.update({'BC':[c for c in X if c not in gcols],'BGC':list(X.columns)})
        preds={b:np.full(len(d),np.nan) for b in blocks}
        for k in range(5):
            tr=d.loc[folds!=k];va=d.loc[folds==k]
            Xt,Xv=design(tr,va,extra_scale_cols=extra)
            for b,cols in blocks.items():
                assert set(cols)<=set(Xt.columns), 'Unexpected absent calendar dummy'
                fitted=sm.OLS(tr[target],Xt[cols]).fit()
                pr=fitted.predict(Xv[cols]).to_numpy();preds[b][folds==k]=pr
                y=va[target].to_numpy();r2=1-np.sum((y-pr)**2)/np.sum((y-y.mean())**2)
                fold_rows.append({'sample':label,'block':b,'fold':k,'n':len(y),'r2':float(r2)})
        y=d[target].to_numpy()
        predframe=pd.DataFrame({ID:d[ID],'fold':folds,'observed':y})
        for b,pr in preds.items():
            assert np.isfinite(pr).all()
            pooled=1-np.sum((y-pr)**2)/np.sum((y-y.mean())**2)
            fr=[z['r2'] for z in fold_rows if z['sample']==label and z['block']==b]
            all_metrics.append({'sample':label,'block':b,'pooled_oof_r2':float(pooled),'mean_fold_r2':float(np.mean(fr)),'difference':float(pooled-np.mean(fr))})
            predframe[b]=pr
        predframe.to_csv(OUT/f'{label}_oof_predictions.csv',index=False)
    pd.DataFrame(all_fit).to_csv(OUT/'full_fit_summary.csv',index=False)
    pd.DataFrame(all_metrics).to_csv(OUT/'oof_metric_comparison.csv',index=False)
    pd.DataFrame(fold_rows).to_csv(OUT/'per_fold_r2.csv',index=False)
    write_json('coefficient_archive_comparison.json',comparisons)
    # Compare pooled scores directly with archived nested sequences.
    rows=[]
    for label,prefix in [('main_E0','step2_E0_variance_decomposition.csv'),('weather_E0','step17_E0_variance_decomposition.csv'),('main_R0c','step2_R0c_order_gust_then_customers.csv'),('weather_R0c','step17_R0c_order_gust_then_customers.csv')]:
        old=pd.read_csv(archives/prefix)
        lookup={'baseline':'regional_time','nongust_weather':'B','gust':'BG','customers':'BGC'}
        for _,row in old.iterrows():
            b=lookup[row['step']];new=next(z for z in all_metrics if z['sample']==label and z['block']==b)
            rows.append({'sample':label,'block':b,'archived':row['r2_oos_5fold'],'replicated_pooled':new['pooled_oof_r2'],'abs_diff':abs(row['r2_oos_5fold']-new['pooled_oof_r2']),'mean_fold_r2':new['mean_fold_r2']})
    pd.DataFrame(rows).to_csv(OUT/'oof_archive_comparison.csv',index=False)
    alignment={}
    for a,b in [('main_E0','weather_E0'),('main_R0c','weather_R0c'),('main_E0','main_R0c')]:
        common=set(group_mapping[a])&set(group_mapping[b])
        contingency=pd.crosstab(pd.Series([group_mapping[a][dt] for dt in sorted(common)],name=a),pd.Series([group_mapping[b][dt] for dt in sorted(common)],name=b))
        # Labels can be permuted; contingency, rather than equality alone, diagnoses different partitions.
        alignment[a+'__'+b]={'shared_dates':len(common),'contingency':contingency.to_dict(),'identical_partition_up_to_labels':bool((contingency.gt(0).sum(axis=0)<=1).all() and (contingency.gt(0).sum(axis=1)<=1).all())}
    write_json('fold_alignment.json',alignment)
    print(pd.DataFrame(all_metrics).to_string(index=False),flush=True)


def main():
    before=inventory()
    samples=source_and_samples()
    replicate(samples)
    changed=[p for p,h in before.items() if not Path(p).exists() or sha(Path(p))!=h]
    write_json('historical_preservation_check.json',{'watched_files':len(before),'changed_files':changed,'scope':'Existing relevant files under 5 MB; raw and v3 read-only opens separately recorded. Audit directory excluded.'})
    assert not changed, changed
    print('Complete; historical files unchanged.',flush=True)


if __name__=='__main__':
    main()
