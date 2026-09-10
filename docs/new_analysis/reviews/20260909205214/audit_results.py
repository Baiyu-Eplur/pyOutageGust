"""Read-only numerical review of saved P03/P04 outputs; no fitting or HTTP calls.

Writes only adjacent review artifacts. Run from the project root with its Python.
"""
from pathlib import Path
from datetime import datetime
import gzip
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.special import ndtr

PROJECT = Path(__file__).resolve().parents[4]
RUN = PROJECT/'results/new/20260909205214'
DATA = RUN/'results/p03_p04'
OUT = Path(__file__).resolve().parent
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed, detail=None):
    checks.append(dict(check=name, passed=bool(passed), detail=detail))


def close(a, b, atol=1e-10):
    return np.allclose(a, b, rtol=1e-9, atol=atol, equal_nan=True)


def csv(path):
    # CSV ties at quantile boundaries require round-trip float parsing, not default rounding.
    return pd.read_csv(path, float_precision='round_trip')


def loss(y, g, theta, beta, p0):
    p = np.clip(p0+(1-p0)*ndtr((np.log(np.clip(g,.3,None))-np.log(theta))/beta),1e-9,1-1e-9)
    return float(-np.sum(y*np.log(p)+(1-y)*np.log1p(-p)))


def main():
    manifest=json.loads((RUN/'run.json').read_text(encoding='utf-8'))
    exp=json.loads((DATA/'experiment.json').read_text(encoding='utf-8'))
    inventory=json.loads((DATA/'inventory.json').read_text(encoding='utf-8'))
    coverage=[]
    for r in manifest['outputs']:
        p=RUN/r['path']; ok=p.exists() and sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
        check('outer_hash:'+r['path'],ok)
        coverage.append(dict(path=r['path'],bytes=p.stat().st_size,sha256=sha(p),outer_hash_matches=ok))
    for r in inventory['outputs']:
        check('inner_hash:'+r['path'],sha(RUN/r['path'])==r['sha256'])
    listed={r['path'] for r in manifest['outputs']}
    actual={str(p.relative_to(RUN)).replace('\\','/') for p in DATA.rglob('*') if p.is_file()}
    check('no_unlisted_experiment_files',actual==listed,dict(actual=len(actual),listed=len(listed)))
    for r in [*exp['sources'],*exp['boundary']]:
        check('source_or_boundary:'+r['path'],sha(PROJECT/r['path'])==r['sha256'])
    base=PROJECT/'results/new'/exp['settings']['base_run']
    check('baseline_manifest',sha(base/'run.json')==exp['baseline']['manifest_sha256'])
    check('baseline_panel',sha(base/'results/final_models/district_day_panel.csv')==exp['baseline']['panel_sha256'])
    check('own_E0',sha(PROJECT/'review_package/data/combined_E0_final.csv')==exp['baseline']['sample_sha256'])
    panel=csv(DATA/'panel_grid.csv'); old=csv(base/'results/final_models/district_day_panel.csv')
    grid=csv(DATA/'grid_daily.csv'); cent=csv(DATA/'centroids.csv')
    import geopandas as gpd
    geometry=gpd.read_file(PROJECT/'data/external/gis/LAD_DEC_2021_UK_BGC/LAD_DEC_2021_UK_BGC.shp')
    geometry=geometry.set_index('LAD21CD').loc[cent.LAD21CD].to_crs(27700).geometry.centroid.to_crs(4326)
    check('polygon_centroids',close(geometry.y,cent.lat) and close(geometry.x,cent.lon))
    key=['LAD21CD','date']
    expected=pd.MultiIndex.from_product([sorted(cent.LAD21CD),pd.date_range('2021-04-01','2024-03-31').strftime('%Y-%m-%d')])
    check('full_panel_keys',len(panel)==121656 and not panel.duplicated(key).any() and set(pd.MultiIndex.from_frame(panel[key]))==set(expected))
    serialization_differences=[]
    for col in old.columns.drop('gust'):
        if pd.api.types.is_numeric_dtype(old[col]):
            check('unchanged_nongust:'+col,np.allclose(old[col],panel[col],rtol=0,atol=1e-12,equal_nan=True))
            if not old[col].equals(panel[col]):
                serialization_differences.append(dict(field=col,max_absolute_difference=float(np.max(np.abs(old[col]-panel[col]))),
                                                     explanation='CSV read/write float rounding; not a changed scientific variable'))
        else:
            check('unchanged_nongust:'+col,old[col].equals(panel[col]))
    check('proxy_backup',close(old.gust,panel.gust_proxy))
    ordered=grid.set_index(key).loc[pd.MultiIndex.from_frame(panel[key])]
    check('grid_replaces_gust',close(ordered.gust_grid,panel.gust))
    hourly_expected=pd.date_range('2021-04-01','2024-04-01',freq='h',inclusive='left')
    request_log=[json.loads(line) for line in (DATA/'weather_raw/requests.jsonl').read_text().splitlines()]
    raw_hashes={r['lad']:r['response_sha256'] for r in request_log if 'response_sha256' in r}
    total_hours=0; raw_count=0; raw_max_error=0.
    for f in sorted((DATA/'weather_raw').glob('*.json.gz')):
        lad=f.name.removesuffix('.json.gz'); raw=gzip.decompress(f.read_bytes()); bundle=json.loads(raw)
        req=bundle['request']; response=bundle['response']; vals=np.array(response['hourly']['wind_gusts_10m'],dtype=float)
        timestamps=pd.DatetimeIndex(pd.to_datetime(response['hourly']['time']))
        point=cent.set_index('LAD21CD').loc[lad]
        check('hourly:'+lad,timestamps.equals(hourly_expected) and len(vals)==26304 and np.isfinite(vals).all() and (vals>=0).all())
        check('request_contract:'+lad,req['models']=='era5' and req['hourly']=='wind_gusts_10m' and req['timezone']=='GMT' and req['wind_speed_unit']=='ms' and req['start_date']=='2021-04-01' and req['end_date']=='2024-03-31' and req['cell_selection']=='nearest' and req['elevation']=='nan' and close([req['latitude'],req['longitude']],[point.lat,point.lon]))
        check('raw_provenance:'+lad,hashlib.sha256(raw).hexdigest()==raw_hashes[lad] and response['utc_offset_seconds']==0 and response['hourly_units']['wind_gusts_10m']=='m/s')
        daily=vals.reshape(-1,24).max(axis=1)
        saved=grid[grid.LAD21CD==lad].sort_values('date')
        error=float(np.max(np.abs(daily-saved.gust_grid.to_numpy())))
        raw_max_error=max(raw_max_error,error)
        check('daily_max:'+lad,error<1e-10 and saved.hours.eq(24).all() and close(saved.grid_lat,response['latitude']) and close(saved.grid_lon,response['longitude']))
        total_hours+=len(vals); raw_count+=1
        if raw_count%25==0: print('raw audited',raw_count,flush=True)
    check('111_raw_responses',raw_count==111)
    stats=json.loads((DATA/'gust_comparison.json').read_text())
    for label,m in [('all',np.ones(len(panel),bool)),('with_incident',panel.n_inc>0),('without_incident',panel.n_inc==0)]:
        a=panel.loc[m,'gust_proxy']; b=panel.loc[m,'gust']; d=b-a
        check('difference_stats:'+label,close([d.mean(),d.std(),np.sqrt(np.mean(d*d)),np.corrcoef(a,b)[0,1]],
                                             [stats[label]['mean_difference'],stats[label]['sd_difference'],stats[label]['rmse'],stats[label]['correlation']]))
    spatial=json.loads((DATA/'spatial_validation.json').read_text())
    for name in ['leave_lad_out','leave_shared_grid_cell_out']:
        d=csv(DATA/f'{name}.csv'); delta=d.grid_loo-d.grid_truth
        truth=grid.set_index(key).loc[pd.MultiIndex.from_frame(d[key]),'gust_grid']
        check('spatial_truth:'+name,close(truth,d.grid_truth))
        check('spatial_stats:'+name,close([delta.mean(),delta.std(),np.sqrt(np.mean(delta*delta)),np.corrcoef(d.grid_truth,d.grid_loo)[0,1]],
                                        [spatial[name]['mean_difference'],spatial[name]['sd_difference'],spatial[name]['rmse'],spatial[name]['correlation']]))
        matrix=grid.pivot(index='date',columns='LAD21CD',values='gust_grid')[cent.LAD21CD]
        cells=grid.groupby('LAD21CD')[['grid_lat','grid_lon']].first().loc[cent.LAD21CD].to_numpy()
        predicted=np.empty(matrix.shape)
        for i in range(len(cent)):
            allowed=np.arange(len(cent))!=i
            if name=='leave_shared_grid_cell_out': allowed &= (cells!=cells[i]).any(axis=1)
            idx=np.flatnonzero(allowed)
            distance=np.sqrt(((cent.lat.iloc[i]-cent.lat.to_numpy()[idx])*111)**2+
                             ((cent.lon.iloc[i]-cent.lon.to_numpy()[idx])*111*np.cos(np.radians(51.8)))**2)
            w=np.exp(-.5*(distance/40)**2)
            if (w>1e-3).sum()<5:
                nearest=np.argsort(distance)[:5]; w[:]=0; w[nearest]=1/(distance[nearest]+1)
            w/=w.sum(); predicted[:,i]=matrix.to_numpy()[:,idx]@w
        predicted=pd.DataFrame(predicted,index=matrix.index,columns=matrix.columns).stack()
        check('spatial_loo_recomputed:'+name,close(predicted.loc[pd.MultiIndex.from_frame(d[['date','LAD21CD']])],d.grid_loo,atol=1e-8))
    oof=csv(DATA/'oof_predictions.csv.gz'); scores=csv(DATA/'brier_comparison.csv')
    check('oof_key_order',oof[key].equals(panel[key])); check('oof_single_fold_per_lad',oof.groupby('LAD21CD').fold.nunique().eq(1).all())
    map_saved=csv(DATA/'lad_folds.csv').set_index('LAD21CD').fold
    check('saved_fold_mapping',np.array_equal(oof.LAD21CD.map(map_saved),oof.fold))
    incidents=pd.read_csv(PROJECT/'review_package/data/combined_E0_final.csv')
    incident_dates=pd.to_datetime(incidents.incident_date_utc,utc=True).dt.strftime('%Y-%m-%d')
    own=incidents.assign(date=incident_dates,cust=incidents.customers_v2_event_excl_reinterruptions)
    panel_index=pd.MultiIndex.from_frame(panel[key])
    for prefix,source in [('any',own),('wthr',own[own.cause_group_official.eq('weather_natural')])]:
        maximum=source.groupby(key).cust.max().reindex(panel_index,fill_value=-1)
        for threshold in [0,5,100,1000]:
            check(f'own_incident_label:{prefix}{threshold}',np.array_equal((maximum>=0 if threshold==0 else maximum>threshold).astype(int),panel[f'{prefix}_gt{threshold}']))
    check('own_incident_counts',np.array_equal(own.groupby(key).size().reindex(panel_index,fill_value=0),panel.n_inc))
    lads=np.array(list(dict.fromkeys(incidents.LAD21CD))); np.random.default_rng(20260908).shuffle(lads)
    mapping=dict(zip(lads,np.arange(len(lads))%5))
    check('original_shuffle_rule',np.array_equal(oof.LAD21CD.map(mapping),oof.fold))
    params=csv(DATA/'parameters_long.csv'); diag=pd.DataFrame(json.loads((DATA/'optimizer_diagnostics.json').read_text()))
    wide=csv(DATA/'parameters_comparison.csv').set_index('target')
    for row in params.itertuples(index=False):
        check('wide_parameter_table:'+row.target+row.version,close([row.theta,row.beta,row.p0],
              [wide.loc[row.target,f'{term}_{row.version}'] for term in ['theta','beta','p0']]))
    cal=csv(DATA/'calibration_bins.csv'); fold_file=csv(DATA/'cv_fold_scores.csv')
    metrics=[]; constant_comparison=[]; tail=[]; old_loss=[]; new_loss=[]
    for row in scores.itertuples(index=False):
        target=row.target; y=oof[target+'_y'].to_numpy(); predictions={v:oof[target+'_'+v].to_numpy() for v in ['proxy','era5_daily_max']}
        check('outcome:'+target,np.array_equal(y,panel[target]))
        training_rates={k:float(y[oof.fold.to_numpy()!=k].mean()) for k in range(5)}
        base_pred=oof.fold.map(training_rates).to_numpy()
        baseline_brier=float(np.mean((base_pred-y)**2))
        errors={}
        for v,pred in predictions.items():
            check('probabilities:'+target+v,np.isfinite(pred).all() and (pred>=0).all() and (pred<=1).all())
            brier=float(np.mean((pred-y)**2))
            reported=row.brier_proxy if v=='proxy' else row.brier_grid
            check('brier:'+target+v,close(brier,reported))
            for k in range(5):
                m=oof.fold==k; value=fold_file[(fold_file.target==target)&(fold_file.version==v)&(fold_file.fold==k)].iloc[0]
                check(f'fold_score:{target}:{v}:{k}',close(np.mean((pred[m]-y[m])**2),value.brier) and m.sum()==value.n)
            f=params[(params.target==target)&(params.version==v)].iloc[0]
            g=panel.gust_proxy if v=='proxy' else panel.gust
            check('parameter_nll:'+target+v,close(loss(y,g,f.theta,f.beta,f.p0),f.nll,atol=1e-6))
            c=cal[(cal.target==target)&(cal.version==v)]
            err=float(np.sqrt(np.sum(c.n*(c.mean_probability-c.observed_frequency)**2)/len(y)))
            errors[v]=err
            check('calibration_rmse:'+target+v,close(err,row.calibration_rmse_proxy if v=='proxy' else row.calibration_rmse_grid))
            constant_comparison.append(dict(target=target,version=v,brier=brier,constant_training_rate_brier=baseline_brier,
                skill_vs_constant=1-brier/baseline_brier,max_difference_from_constant=float(np.max(np.abs(pred-base_pred))),
                within_fold_prediction_std_max=float(pd.DataFrame({'p':pred,'fold':oof.fold}).groupby('fold').p.std().max())))
            for c_row in c[c.n<100].to_dict('records'): tail.append(c_row)
        a,b=predictions.values()
        edges=np.unique(np.r_[0.,np.quantile(np.r_[a,b],np.linspace(0,1,11)),1.])
        for v,pred in predictions.items():
            bins=np.clip(np.searchsorted(edges,pred,side='right')-1,0,len(edges)-2)
            for bidx in np.unique(bins):
                m=bins==bidx; c=cal[(cal.target==target)&(cal.version==v)&(cal.bin==bidx)].iloc[0]
                check(f'calibration_bin:{target}:{v}:{bidx}',m.sum()==c.n and close([pred[m].mean(),y[m].mean()],[c.mean_probability,c.observed_frequency]))
        old_loss.append((a-y)**2); new_loss.append((b-y)**2)
        metrics.append(dict(target=target,relative_brier_gain_pct=100*row.relative_improvement,
                            relative_calibration_gain_pct=100*(1-errors['era5_daily_max']/errors['proxy'])))
    groups=oof.LAD21CD.to_numpy(); unique=np.unique(groups)
    old_loss=np.array(old_loss).T; new_loss=np.array(new_loss).T
    a=np.array([old_loss[groups==g].sum(axis=0) for g in unique]); b=np.array([new_loss[groups==g].sum(axis=0) for g in unique])
    rng=np.random.default_rng(20260909); boot=[]
    for _ in range(1000):
        idx=rng.integers(0,len(unique),len(unique)); aa=a[idx].sum(axis=0); bb=b[idx].sum(axis=0)
        boot.append((aa-bb)/np.maximum(aa,1e-15))
    boot=np.array(boot); ci=json.loads((DATA/'paired_uncertainty.json').read_text())
    check('bootstrap_mean_ci',close(np.quantile(boot.mean(axis=1),[.025,.975]),ci['mean_relative_gain_ci95']))
    check('bootstrap_endpoint_ci',close(np.quantile(boot,[.025,.975],axis=0).T,ci['endpoint_relative_gain_ci95']))
    # A fixed admissible point, not a refit: if its likelihood is better, stored fit is not optimum.
    target='wthr_gt1000'; y=panel[target].to_numpy(); candidate=dict(theta=40.,beta=.27,p0=.0014)
    likelihood_check=dict(candidate=candidate,candidate_nll=loss(y,panel.gust,**candidate),
                         saved_nll=float(params[(params.target==target)&(params.version=='era5_daily_max')].nll.iloc[0]),
                         method='post-review fixed parameter point; no optimization, no replacement result')
    rare_folds=[]
    for k in range(5):
        m=oof.fold!=k
        saved=diag[(diag.target==target)&(diag.version=='era5_daily_max')&(diag.scope==f'fold_{k}')].iloc[0]
        rare_folds.append(dict(fold=k,reported_success=bool(saved.success),saved_training_nll=saved.nll,
                               fixed_candidate_training_nll=loss(y[m],panel.loc[m,'gust'],**candidate),
                               train_events=int(y[m].sum()),test_events=int(y[~m].sum())))
    pd.DataFrame(metrics).to_csv(OUT/'review_metric_details.csv',index=False)
    pd.DataFrame(constant_comparison).to_csv(OUT/'review_constant_baseline.csv',index=False)
    pd.DataFrame(tail).to_csv(OUT/'review_small_calibration_bins.csv',index=False)
    pd.DataFrame(coverage).to_csv(OUT/'review_file_coverage.csv',index=False)
    result=dict(reviewed_at=datetime.now().astimezone().isoformat(),run=str(RUN),checks=checks,
                total_checks=len(checks),failed_checks=[x for x in checks if not x['passed']],
                files=len(coverage),raw_responses=raw_count,validated_hourly_values=total_hours,max_daily_max_error=raw_max_error,
                failed_fits=diag[~diag.success].to_dict('records'),likelihood_counterexample=likelihood_check,rare_fold_diagnostics=rare_folds,
                mean_brier_gain_pct=100*scores.relative_improvement.mean(),
                mean_brier_gain_pct_excluding_failed_endpoint=100*scores[scores.target!=target].relative_improvement.mean(),
                mean_gain_ci95_pct_excluding_failed_endpoint=(100*np.quantile(boot[:,scores.target!=target].mean(axis=1),[.025,.975])).tolist(),
                serialization_differences=serialization_differences,
                grid_gust_range=[panel.gust.min(),panel.gust.max()],proxy_gust_range=[panel.gust_proxy.min(),panel.gust_proxy.max()],
                small_calibration_bins=len(tail),tail_examples=tail,
                no_refitting=True,no_weather_requests=True)
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','tail_examples']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
