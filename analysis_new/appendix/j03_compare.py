"""APP-J03-COMPARE: fixed-source, fixed-fold comparison through main_appendix.

No weather requests or historical output writes. Fit budgets come unchanged from
DD-AGG01. Full fits are descriptive; only held-out fold fits supply OOF scores.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from analysis_new.fragility_optimizer import RULES, Objective, fit, probabilities
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.dd_agg01_evaluation import evaluate, uncertainty
from .catalog import ROOT, MAIN, AGG, P03, J03_PLAN, J03_SOURCES, REQUIREMENTS
from .mapping import digest, write_json, expected
from .exporters import table

VERSIONS = ['PROXY', 'GRID_MAX']
SCOPES = ['full'] + [f'fold_{i}' for i in range(5)]
R = next(r for r in REQUIREMENTS if r['requirement_id']=='J03')
OWN = 'J03'


def now(): return datetime.now().astimezone().isoformat(timespec='seconds')


def read(path): return pd.read_csv(path, float_precision='round_trip')


def clean(value):
    if isinstance(value, dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, np.generic): return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value): return None
    return value


def js(path, value): write_json(path, clean(value))


def csv(path, frame):
    path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False,float_format='%.17g',compression={'method':'gzip','mtime':0} if path.suffix=='.gz' else None)


def frame_hash(frame):
    return hashlib.sha256(frame.to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()).hexdigest()


def matched_inputs():
    proxy=read(ROOT/MAIN/'final_models/district_day_panel.csv')
    grid=read(ROOT/AGG/'daily_aggregations.csv.gz')
    folds=read(ROOT/P03/'lad_folds.csv')
    keys=['LAD21CD','date']
    for label,d in [('PROXY',proxy),('GRID_MAX',grid)]:
        if len(d)!=121656 or d.LAD21CD.nunique()!=111 or d.duplicated(keys).any():
            raise ValueError(label+': invalid/duplicate panel keys; no intersection or filling permitted')
        actual=pd.MultiIndex.from_frame(d[keys])
        wanted=pd.MultiIndex.from_product([sorted(d.LAD21CD.unique()),pd.date_range('2021-04-01','2024-03-31').strftime('%Y-%m-%d')])
        if set(actual)!=set(wanted): raise ValueError(label+': incomplete LAD/date product')
    if set(map(tuple,proxy[keys].to_numpy()))!=set(map(tuple,grid[keys].to_numpy())):
        raise ValueError('Weather schemes have different keys')
    # Explicit bijection, never an intersection. Retain source PROXY ordering.
    grid=grid.set_index(keys).loc[pd.MultiIndex.from_frame(proxy[keys])].reset_index()
    if not np.array_equal(proxy[TARGETS],grid[TARGETS]): raise ValueError('Source labels differ')
    if not np.isin(proxy[TARGETS].to_numpy(),[0,1]).all(): raise ValueError('Non-binary source labels')
    if folds.LAD21CD.duplicated().any() or len(folds)!=111 or set(folds.fold)!=set(range(5)):
        raise ValueError('Invalid saved LAD folds')
    original=proxy.LAD21CD.map(folds.set_index('LAD21CD').fold)
    if original.isna().any() or not np.array_equal(original,grid.fold): raise ValueError('A01 and saved LAD folds differ')
    daily=proxy[keys+TARGETS].copy()
    daily['fold']=original.astype(int)
    daily['PROXY']=proxy.gust.to_numpy();daily['GRID_MAX']=grid.A01_daily_max.to_numpy();daily['weight']=1
    if not np.isfinite(daily[VERSIONS]).all().all() or (daily[VERSIONS]<0).any().any(): raise ValueError('Invalid gust inputs')
    record=dict(rows=len(daily),lads=111,days=1096,start=daily.date.min(),end=daily.date.max(),
        same_keys=True,same_labels=True,same_saved_folds=True,equal_row_weights=True,timezone='UTC',unit='m/s',
        key_label_sha256=frame_hash(daily[keys+TARGETS]),fold_sha256=frame_hash(daily[keys+['fold']]),
        scheme_hashes={v:frame_hash(daily[keys+[v]]) for v in VERSIONS})
    return daily,record


def validate_reused(summary, records, g, y):
    """Check the saved selected solution against the CURRENT same objective.

    This is component compatibility, not a new optimiser search. The saved
    initial/end-point records establish the original finite-budget validity.
    """
    if not records or not summary['valid']: return False,'missing/invalid source diagnostics'
    obj=Objective(g,y);d=obj.diagnostics(obj.encode(**{k:summary[k] for k in ['theta','beta','p0']}))
    if summary['n']!=len(y) or summary['events']!=int(y.sum()):return False,'training sample mismatch'
    if not np.isclose(d['nll'],summary['nll'],rtol=0,atol=RULES['nll_tolerance']):return False,'objective mismatch'
    if not summary['success'] or d['projected_gradient']>RULES['stationary_tolerance']:return False,'stationarity/convergence mismatch'
    if d['prediction_std']<RULES['prediction_std_min']:return False,'degenerate predictions'
    if d['nll']>min(v['nll'] for v in records)+RULES['nll_tolerance']:return False,'better evaluated source point'
    if d['nll']>summary['constant_nll']+RULES['nll_tolerance']:return False,'worse than training constant'
    return True,'same sample/configuration; stable objective, gradient and saved candidate minima compatible'


def one_fit(version,target,scope,g,y):
    info=dict(candidate=version,target=target,scope=scope)
    try:
        summary,records=fit(g,y)
        return dict(**summary,**info),records
    except Exception as exc:
        return dict(**info,n=len(y),events=int(y.sum()),valid=False,success=False,
                    theta=np.nan,beta=np.nan,p0=np.nan,nll=np.nan,weak_identification=True,
                    error=f'{type(exc).__name__}: {exc}'),[]


def calculate(stage,daily,protocol,force,event):
    src=json.loads((ROOT/AGG/'experiment.json').read_text(encoding='utf8'))
    if src['optimizer']!=RULES: raise ValueError('Accepted A01 optimiser configuration differs; do not silently change budgets')
    inventory=json.loads((ROOT/AGG/'inventory.json').read_text(encoding='utf8'))
    inv={r['path']:r['sha256'] for r in inventory['files']}
    for name in ['experiment.json','daily_aggregations.csv.gz','fit_checkpoint.jsonl','fit_summary.csv','oof_predictions.csv.gz','validation.json']:
        if digest(ROOT/AGG/name)!=inv[name]:raise ValueError('Accepted A01 inventory mismatch: '+name)
    source={}
    with (ROOT/AGG/'fit_checkpoint.jsonl').open(encoding='utf8') as f:
        for line in f:
            r=json.loads(line);s=r['summary']
            if s['candidate']=='A01_daily_max':source[(s['target'],s['scope'])]=r
    if len(source)!=48:raise ValueError('A01 source does not cover 48 components')
    old_fits=read(ROOT/AGG/'fit_summary.csv').query("candidate == 'A01_daily_max'")
    fitted={};plans=[];details={}
    for v in VERSIONS:
        for t in TARGETS:
            for s in SCOPES:
                key=(v,t,s);mask=np.ones(len(daily),bool) if s=='full' else daily.fold.to_numpy()!=int(s[-1])
                y=daily.loc[mask,t].to_numpy();g=daily.loc[mask,v].to_numpy()
                action='REFIT';reason='PROXY historical fits use older objective/configuration; no matched stable five-fold components'
                if force:reason='Explicit --recompute-j03: same frozen budget, no imported fits'
                elif v=='GRID_MAX':
                    saved=source[t,s];ok,reason=validate_reused(saved['summary'],saved['candidates'],g,y)
                    row=old_fits[(old_fits.target==t)&(old_fits.scope==s)].iloc[0]
                    if not all(np.isclose(row[k],saved['summary'][k],rtol=0,atol=1e-12) for k in ['theta','beta','p0','nll']):
                        raise ValueError('A01 summary/checkpoint disagree')
                    if ok:
                        action='REUSE';fitted[key]={**saved['summary'],'candidate':v};details[key]=saved['candidates']
                plans.append(dict(candidate=v,target=t,scope=s,action=action,reason=reason,n=len(y),events=int(y.sum()),
                    training_hash=frame_hash(daily.loc[mask,['LAD21CD','date',v,t]]),
                    source=AGG+'fit_checkpoint.jsonl' if action=='REUSE' else 'current frozen APP-J03-COMPARE'))
    plan=pd.DataFrame(plans);table(stage,'J03_COMPONENT_PLAN',plan,R)
    event('Component plan frozen before new fits',reuse=int((plan.action=='REUSE').sum()),refit=int((plan.action=='REFIT').sum()))
    def persist(key):
        with (stage/'data/J03_FIT_COMPONENTS.jsonl').open('a',encoding='utf8') as f:
            f.write(json.dumps(clean(dict(summary=fitted[key],candidates=details[key])),ensure_ascii=False,allow_nan=False)+'\n')
    for key in fitted:persist(key)
    # Parallel execution changes scheduling only; all per-component starts/budgets
    # and training rows remain frozen. Two workers bound memory for dense proxy.
    with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=2) as pool:
        jobs={}
        for r in plan[plan.action=='REFIT'].itertuples():
            mask=np.ones(len(daily),bool) if r.scope=='full' else daily.fold.to_numpy()!=int(r.scope[-1])
            future=pool.submit(one_fit,r.candidate,r.target,r.scope,daily.loc[mask,r.candidate].to_numpy(),daily.loc[mask,r.target].to_numpy())
            jobs[future]=(r.candidate,r.target,r.scope)
        for future in as_completed(jobs):
            key=jobs[future];fitted[key],details[key]=future.result();persist(key)
            event('Fit completed',component='/'.join(key),valid=fitted[key]['valid'],completed=len(fitted),total=96)
    fits=pd.DataFrame([fitted[v,t,s] for v in VERSIONS for t in TARGETS for s in SCOPES])
    table(stage,'J03_FULL_PARAMETERS',fits[fits.scope=='full'],R)
    table(stage,'J03_FOLD_FITS',fits[fits.scope!='full'],R)
    components=plan.merge(fits[['candidate','target','scope','valid','weak_identification']],on=['candidate','target','scope'],validate='one_to_one')
    components['execution']='new_fit_or_source_reuse'
    table(stage,'J03_COMPONENT_MANIFEST',components,R)
    oof=daily[['LAD21CD','date','fold',*TARGETS]].copy()
    for t in TARGETS:
        constant=np.full(len(daily),np.nan)
        for fold in range(5):
            mask=daily.fold.to_numpy()==fold;constant[mask]=daily.loc[~mask,t].mean()
        oof[t+'_constant']=constant
        for v in VERSIONS:
            pred=np.full(len(daily),np.nan)
            for fold in range(5):
                mask=daily.fold.to_numpy()==fold;f=fitted[v,t,f'fold_{fold}']
                if f['valid']:pred[mask]=probabilities(daily.loc[mask,v],**{k:f[k] for k in ['theta','beta','p0']})
            oof[t+'__'+v]=pred
    csv(stage/'data/J03_OOF_PREDICTIONS.csv.gz',oof)
    # Reused GRID_MAX OOF must reproduce its accepted saved predictions by key.
    accepted=read(ROOT/AGG/'oof_predictions.csv.gz').set_index(['LAD21CD','date']).loc[pd.MultiIndex.from_frame(oof[['LAD21CD','date']])]
    comparisons={}
    for t in TARGETS:
        reused=components[(components.candidate=='GRID_MAX')&(components.target==t)&(components.scope!='full')].action.eq('REUSE').all()
        if reused:
            err=float(np.max(np.abs(oof[t+'__GRID_MAX'].to_numpy()-accepted[t+'__A01_daily_max'].to_numpy())))
            if err>1e-12:raise ValueError('Reused GRID_MAX OOF differs: '+t)
            comparisons[t]=err
    protocol['reuse_oof_max_abs_error']=comparisons
    return fits,components,oof


def outputs(stage,daily,fits,components,oof,event):
    metrics,folds,bins,edges=evaluate(oof,fits,candidates=VERSIONS)
    intervals=uncertainty(oof,metrics,candidates=VERSIONS).query("candidate == 'GRID_MAX'").copy()
    intervals=intervals.rename(columns={'absolute_gain_lo':'delta_brier_lo','absolute_gain_hi':'delta_brier_hi'})
    intervals['relative_improvement_pct_lo']=100*intervals.relative_gain_lo
    intervals['relative_improvement_pct_hi']=100*intervals.relative_gain_hi
    table(stage,'J03_PAIRED_INTERVALS',intervals,R)
    rows=[];foldrows=[]
    for t in TARGETS:
        y=oof[t].to_numpy();m=metrics[metrics.target==t].set_index('candidate')
        row=dict(target=t,n=len(y),events=int(y.sum()),observed_rate=float(y.mean()),
            valid_proxy=bool(m.loc['PROXY','valid_cv']),valid_grid=bool(m.loc['GRID_MAX','valid_cv']),
            proxy_brier=m.loc['PROXY','brier'],grid_brier=m.loc['GRID_MAX','brier'],
            constant_brier=m.loc['PROXY','constant_brier'],proxy_bss=m.loc['PROXY','brier_skill'],grid_bss=m.loc['GRID_MAX','brier_skill'],
            delta_brier=m.loc['GRID_MAX','absolute_gain'],relative_improvement_pct=100*m.loc['GRID_MAX','relative_gain'])
        for v in VERSIONS:
            p=oof[t+'__'+v].to_numpy();row[v.lower()+'_mean_prediction']=float(p.mean());row[v.lower()+'_bias']=float((p-y).mean())
        rows.append(row)
        for fold in range(5):
            fm=folds[(folds.target==t)&(folds.fold==fold)].set_index('candidate');mask=oof.fold.to_numpy()==fold
            foldrows.append(dict(target=t,fold=fold,n=int(mask.sum()),events=int(y[mask].sum()),
                valid_proxy=bool(fm.loc['PROXY','valid']),valid_grid=bool(fm.loc['GRID_MAX','valid']),
                proxy_brier=fm.loc['PROXY','brier'],grid_brier=fm.loc['GRID_MAX','brier'],
                delta_brier=fm.loc['GRID_MAX','absolute_gain'],relative_improvement_pct=100*fm.loc['GRID_MAX','relative_gain'],
                training_constant=float(oof.loc[mask,t+'_constant'].iloc[0]),constant_brier=fm.loc['PROXY','constant_brier']))
    paired=pd.DataFrame(rows).merge(intervals.drop(columns='candidate'),on='target',validate='one_to_one')
    table(stage,'J03_PAIRED_METRICS',paired,R);table(stage,'J03_FOLD_METRICS',pd.DataFrame(foldrows),R)
    table(stage,'J03_CALIBRATION',bins,R);js(stage/'data/J03_CALIBRATION_EDGES.json',edges)
    # Save the identical LAD draws, allowing direct reconstruction of paired CIs.
    lads=sorted(daily.LAD21CD.unique());rng=np.random.default_rng(20260909)
    draws=np.array([rng.integers(0,len(lads),len(lads)) for _ in range(1000)])
    csv(stage/'data/J03_BOOTSTRAP_DRAWS.csv.gz',pd.DataFrame(draws,columns=[f'draw_{i}' for i in range(len(lads))]))
    js(stage/'data/J03_BOOTSTRAP_LADS.json',lads)
    historical=json.loads((ROOT/MAIN/'final_models/district_day_fragility.json').read_text(encoding='utf8'))['fits']
    history=[]
    for t in TARGETS:
        old=historical[t]['lognormal'];new=fits[(fits.candidate=='PROXY')&(fits.target==t)&(fits.scope=='full')].iloc[0]
        row=dict(target=t,comparison='full-sample descriptive, not OOF',new_valid=bool(new.valid))
        for k in ['theta','beta','p0','nll']:row['historical_'+k]=old[k];row['stable_'+k]=new[k];row['difference_'+k]=new[k]-old[k]
        prior=probabilities(daily.PROXY,**{k:old[k] for k in ['theta','beta','p0']})
        newer=probabilities(daily.PROXY,**{k:new[k] for k in ['theta','beta','p0']}) if new.valid else np.full(len(daily),np.nan)
        row.update(mean_probability_difference=float(np.mean(newer-prior)),max_abs_probability_difference=float(np.max(np.abs(newer-prior))))
        history.append(row)
    table(stage,'J03_PROXY_HISTORY_COMPARISON',pd.DataFrame(history),R)
    from .j03_report import figures, report
    figures(stage,paired,bins)
    technical(stage,daily,fits,oof,paired,bins,draws,lads)
    event('Paired scores, intervals, calibration and technical checks completed')
    report(stage,paired,components,pd.DataFrame(history))


def technical(stage,daily,fits,oof,paired,bins,draws,lads):
    saved=read(stage/'data/J03_OOF_PREDICTIONS.csv.gz');checks={}
    checks['96_components']=len(fits)==96
    checks['16_full_80_training']=int((fits.scope=='full').sum())==16 and int((fits.scope!='full').sum())==80
    checks['saved_keys_labels_folds']=saved[['LAD21CD','date','fold',*TARGETS]].equals(oof[['LAD21CD','date','fold',*TARGETS]])
    checks['draws_shared_shape']=draws.shape==(1000,111)
    counts=np.array([(daily.LAD21CD==lad).sum() for lad in lads])
    for t in TARGETS:
        y=saved[t].to_numpy();r=paired[paired.target==t].iloc[0]
        for v in VERSIONS:
            p=saved[t+'__'+v].to_numpy();valid=fits[(fits.candidate==v)&(fits.target==t)&(fits.scope!='full')].valid.all()
            checks[f'{t}_{v}_legal_or_explicit_invalid']=bool(np.isfinite(p).all() and ((p>=0)&(p<=1)).all()) if valid else bool(np.isnan(p).any())
            if valid:checks[f'{t}_{v}_score_roundtrip']=bool(np.isclose(np.mean((p-y)**2),r[{'PROXY':'proxy_brier','GRID_MAX':'grid_brier'}[v]],rtol=1e-12,atol=1e-14))
        for fold in range(5):
            mask=saved.fold.to_numpy()==fold
            checks[f'{t}_constant_{fold}']=bool(np.allclose(saved.loc[mask,t+'_constant'],saved.loc[~mask,t].mean(),rtol=0,atol=1e-15))
            for v in VERSIONS:
                f=fits[(fits.candidate==v)&(fits.target==t)&(fits.scope==f'fold_{fold}')].iloc[0]
                if f.valid:
                    expected_p=probabilities(daily.loc[mask,v],**{k:f[k] for k in ['theta','beta','p0']})
                    checks[f'{t}_{v}_training_only_{fold}']=bool(f.n==int((~mask).sum()) and f.events==int(y[~mask].sum()) and np.allclose(expected_p,saved.loc[mask,t+'__'+v],rtol=0,atol=1e-14))
        if r.valid_comparison:
            loss0=(saved[t+'__PROXY'].to_numpy()-y)**2;loss1=(saved[t+'__GRID_MAX'].to_numpy()-y)**2
            sums0=np.array([loss0[daily.LAD21CD==lad].sum() for lad in lads]);sums1=np.array([loss1[daily.LAD21CD==lad].sum() for lad in lads])
            a=sums0[draws].sum(axis=1);b=sums1[draws].sum(axis=1)
            ci=np.quantile((a-b)/counts[draws].sum(axis=1),[.025,.975]);rel=np.quantile(100*(a-b)/a,[.025,.975])
            checks[t+'_same_draw_absolute_interval']=bool(np.allclose(ci,[r.delta_brier_lo,r.delta_brier_hi],rtol=1e-10,atol=1e-14))
            checks[t+'_same_draw_relative_interval']=bool(np.allclose(rel,[r.relative_improvement_pct_lo,r.relative_improvement_pct_hi],rtol=1e-10,atol=1e-12))
    for (t,v),b in bins.groupby(['target','candidate']):
        checks[f'{t}_{v}_bin_counts']=int(b.n.sum())==len(daily) and int(b.events.sum())==int(daily[t].sum())
        checks[f'{t}_{v}_empty_bins_nan']=bool(b.loc[b.n==0,['mean_probability','observed_frequency']].isna().all().all())
    valid=fits[fits.valid]
    checks['valid_fits_finite']=bool(np.isfinite(valid[['theta','beta','p0','nll','projected_gradient']]).all().all())
    checks['valid_fits_saved_rules']=bool(valid.success.all() and (valid.projected_gradient<=RULES['stationary_tolerance']).all() and (valid.prediction_std>=RULES['prediction_std_min']).all())
    js(stage/'logs/J03_TECHNICAL_CHECKS.json',dict(time=now(),checks=checks,all_passed=all(checks.values()),
        valid_components=int(fits.valid.sum()),invalid_components=clean(fits.loc[~fits.valid,['candidate','target','scope']].to_dict('records')),
        scope='J03 matching, training boundaries, serialization, paired fixed-OOF evaluation only'))
    if not all(checks.values()):raise ValueError('J03 technical checks failed: '+str([k for k,v in checks.items() if not v]))


def generate(stage,source_checks,previous,force=False,only=False,base_generator=None,command=''):
    from .runner import safe_child
    relevant=set(J03_SOURCES)
    failed=[r['path'] for r in source_checks if r['path'] in relevant and not r['passed']]
    if failed:raise ValueError('J03 source fingerprint mismatch: '+str(failed))
    old=json.loads((previous/'manifest.json').read_text(encoding='utf8')) if (previous/'manifest.json').exists() else {}
    own={r['path'] for r in old.get('outputs',[]) if r['requirement_id']=='J03'}
    if only:
        if old.get('owner')!='main_appendix.py':raise ValueError('J03-only requires an existing managed J appendix')
        for rel in old['managed_files']:
            if rel in own or rel=='manifest.json':continue
            src=safe_child(previous,rel);dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
        manifest=copy.deepcopy(old)
        manifest['outputs']=[r for r in old.get('outputs',[]) if r['requirement_id']!='J03']
    else:
        manifest=base_generator('J',stage,source_checks)
    for part in ['data','tables','figures','logs']:(stage/part).mkdir(parents=True,exist_ok=True)
    before={p.relative_to(stage).as_posix():digest(p) for p in stage.rglob('*') if p.is_file() and p.name not in ['README.md','manifest.json']}
    daily,matching=matched_inputs()
    code_files=['analysis_new/fragility_optimizer.py','analysis_new/dd_agg01_evaluation.py','analysis_new/grid_fragility_validation.py',
                'analysis_new/appendix/j03_compare.py']
    cache_config=dict(task='APP-J03-COMPARE',rules=RULES,matching=matching,inputs={p:digest(ROOT/p) for p in J03_SOURCES},
                      code={p:digest(ROOT/p) for p in code_files},seed=20260909,repeats=1000,calibration='common pooled two-source OOF quantiles, unique +0/1; side right; sparse<100')
    cache_key=hashlib.sha256(json.dumps(cache_config,sort_keys=True).encode()).hexdigest()
    # One-time migration from the first published J03 cache. The exact previous
    # producer is known; this revision only separates rendering from calculation.
    # Require every scientific setting, source and dependency to remain equal.
    prior_protocol=json.loads((previous/'logs/J03_PROTOCOL.json').read_text(encoding='utf8')) if (previous/'logs/J03_PROTOCOL.json').exists() else {}
    migrated=False
    if prior_protocol.get('code',{}).get('analysis_new/appendix/j03_compare.py')=='67eab118c2b577f422c382592b3747f74a16b0678f48f1a930aab6aec3aeb0e4':
        old_config={k:prior_protocol.get(k) for k in cache_config}
        old_config['code']={k:v for k,v in old_config['code'].items() if k!='analysis_new/appendix/j03_report.py'}
        old_config['code']['analysis_new/appendix/j03_compare.py']=cache_config['code']['analysis_new/appendix/j03_compare.py']
        migrated=old_config==cache_config
    cached=not force and (old.get('j03_cache_key')==cache_key or migrated) and own and all(
        (previous/r['path']).is_file() and digest(previous/r['path'])==r['sha256'] for r in old['outputs'] if r['requirement_id']=='J03')
    protocol={**cache_config,'frozen_at':now(),'command':command,'workers':2,'plan':J03_PLAN,
        'plan_sha256_at_execution':digest(ROOT/J03_PLAN),'primary':'any_gt100','important_secondary':'wthr_gt100',
        'target_rule':'at least one incident; gt0 includes zero-customer incidents, other thresholds strictly >; no daily sums',
        'weather_definition':{'PROXY':'same-day event-anchor interpolation, not daily maximum','GRID_MAX':'independent downloaded ERA5 hourly gust daily maximum at established LAD locations'},
        'scope':'overall exposure-construction comparison; neither source is observed truth; no new weather or anchoring analysis',
        'uncertainty':'paired whole LAD fixed OOF, 1000 draws; no refit/selection/full shared storm-date uncertainty',
        'score_sign':'delta=BS_PROXY-BS_GRID_MAX; relative_pct=100*delta/BS_PROXY; BSS uses common training-fold rate',
        'force_recompute':force,'cached_export':bool(cached),'python':sys.version,
        'previous_attempt_error':old.get('error')}
    def event(message,**extra):
        record=dict(time=now(),message=message,**extra)
        with (stage/'logs/J03_EXECUTION.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(clean(record),ensure_ascii=False)+'\n')
        print(f'[{record["time"]}] J03 {message} '+json.dumps(clean(extra)),flush=True)
    if cached:
        for rel in own:
            dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dest)
        event('Validated cache reused; no fitting',components=96)
        # Rendering changes cannot require another scientific fit. The fitted
        # protocol stays intact; current rendering code is in LAST_EXECUTION.
        from .j03_report import figures,report
        figures(stage,read(stage/'tables/J03_PAIRED_METRICS.csv'),read(stage/'tables/J03_CALIBRATION.csv'))
        report(stage,read(stage/'tables/J03_PAIRED_METRICS.csv'),read(stage/'tables/J03_COMPONENT_MANIFEST.csv'),read(stage/'tables/J03_PROXY_HISTORY_COMPARISON.csv'))
    else:
        js(stage/'logs/J03_PROTOCOL.json',protocol)
        event('Inputs and protocol frozen',rows=len(daily),targets=8)
        csv(stage/'data/J03_MATCHED_PANEL.csv.gz',daily)
        js(stage/'logs/J03_INPUT_MATCH.json',matching)
        table(stage,'J03_MATCHED_SAMPLE',pd.DataFrame([dict(target=t,n=len(daily),lads=111,days=1096,events=int(daily[t].sum()),rate=float(daily[t].mean())) for t in TARGETS]),R)
        fits,components,oof=calculate(stage,daily,protocol,force,event)
        js(stage/'logs/J03_PROTOCOL.json',protocol)
        outputs(stage,daily,fits,components,oof,event)
    # Cached re-export preserves the fitted protocol; records latest command separately.
    js(stage/'logs/J03_LAST_EXECUTION.json',dict(time=now(),command=command,cache_key=cache_key,cached_export=bool(cached),
        cache_schema_migrated=bool(migrated and old.get('j03_cache_key')!=cache_key),
        rendering_sha256=digest(ROOT/'analysis_new/appendix/j03_report.py'),
        newly_fitted_this_execution=0 if cached else int((read(stage/'tables/J03_COMPONENT_MANIFEST.csv').action=='REFIT').sum())))
    unchanged={rel:digest(stage/rel)==sha for rel,sha in before.items()}
    if not all(unchanged.values()):raise ValueError('Non-J03 staged results changed')
    js(stage/'logs/J03_PRESERVATION.json',dict(other_J_managed_files=unchanged,all_unchanged=True,
        unselected_appendices='Not generated; verified separately during execution',original_research='Read-only input hashes in protocol'))
    content=(stage/'README.md').read_text(encoding='utf8')
    content=re.sub(r'### J03 —.*?(?=### J04 —|\Z)','',content,flags=re.S)
    content=content.split('\n## APP-J03-COMPARE')[0]
    content+='\n## APP-J03-COMPARE\n\n'+(stage/'logs/J03_EXECUTION_REPORT.md').read_text(encoding='utf8')+'\n'
    (stage/'README.md').write_text(content,encoding='utf8')
    newfiles={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}-set(before)-{'README.md','manifest.json'}
    for rel in expected(R):
        if not (stage/rel).is_file():raise ValueError('Missing J03 export '+rel)
    for rel in sorted(newfiles):
        p=stage/rel
        manifest['outputs'].append(dict(path=rel,sha256=digest(p),bytes=p.stat().st_size,requirement_id='J03',claim_id='CL_J03',
            source_paths=J03_SOURCES,source_sha256=cache_config['inputs'],producer='analysis_new.appendix.j03_compare:generate',
            export_function='analysis_new.appendix.j03_compare:generate',configuration=R['config'],status='产物已补齐/待研究负责人反馈分析'))
    valid=read(stage/'tables/J03_FULL_PARAMETERS.csv').valid.all() and read(stage/'tables/J03_FOLD_FITS.csv').valid.all()
    manifest['requirements']['J03']='产物已补齐/待研究负责人反馈分析' if valid else '产物已输出/部分拟合无效，待反馈分析'
    manifest.pop('error',None)  # Previous failed attempts remain in the protocol and LOG, not current status.
    manifest.update(owner='main_appendix.py',appendix='J',last_attempt=now(),status='success_with_gaps' if any(v=='有具体原因的缺失' for v in manifest['requirements'].values()) else 'success',
        update_state='本次仅J03更新/其他J结果保留' if only else '本次已更新',j03_cache_key=cache_key,
        managed_files=sorted({p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}|{'manifest.json'}))
    js(stage/'manifest.json',manifest)
    return manifest
