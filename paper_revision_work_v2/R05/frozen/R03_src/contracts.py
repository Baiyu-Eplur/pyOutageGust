"""Pure declared R03 numerical contracts; no filesystem or historical imports."""
import hashlib,json
import numpy as np
import pandas as pd

ID='Incident Reference';C='customers_v2_event_excl_reinterruptions';D='duration_B_full_span_hours'
WX=['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h']
REGION=['urban_binary','log_population','income_deprivation_rate','deprivation_gap_pct','morans_i']
G=['zG','zG2','zG_zPressure'];K=['zK','zK2']
def identity(values):return hashlib.sha256('\n'.join(sorted(map(str,values))).encode()).hexdigest()
def config_hash(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def target(df,name):
    if name=='E0':return np.log1p(df[C].to_numpy(dtype=float))
    if name=='R0c':return np.log(df[D].to_numpy(dtype=float))
    raise ValueError('unknown target')
def global_date_folds(base,n_splits=5):
    if not base[ID].is_unique:raise ValueError('duplicate candidate ID')
    counts=base.groupby('new_date_utc').size().rename('events').reset_index().sort_values(['events','new_date_utc'],ascending=[False,True],kind='stable')
    if len(counts)<n_splits:raise ValueError('not enough date groups')
    totals=[0]*n_splits;rows=[]
    for date,n in counts.itertuples(index=False,name=None):
        fold=min(range(n_splits),key=lambda f:(totals[f],f));totals[fold]+=int(n)
        rows.append({'date_utc':str(date),'fold':fold,'base_events':int(n)})
    return pd.DataFrame(rows).sort_values('date_utc').reset_index(drop=True)
def attach_folds(df,mapping):
    if not mapping.date_utc.is_unique:raise ValueError('duplicate date map')
    d=df.copy();d['fold']=d.new_date_utc.map(mapping.set_index('date_utc').fold)
    if d.fold.isna().any():raise ValueError('candidate date missing from frozen folds')
    d['fold']=d.fold.astype(int);return d
def training_population(main_train,group,target_name,tail):
    d=main_train.copy();threshold=None
    if tail=='main_train_p99' and target_name=='R0c':
        x=d[D].to_numpy(dtype=float)
        if not len(x) or not (np.isfinite(x)&(x>0)).all():raise ValueError('invalid main training recovery reference')
        threshold=float(np.quantile(x,.99,method='linear'));d=d.loc[d[D].le(threshold)].copy()
    elif tail!='all_valid':
        if not(tail=='main_train_p99' and target_name=='E0'):raise ValueError('unknown tail policy')
    if group=='weather':d=d.loc[d.cause_group_event.eq('weather_natural')].copy()
    elif group!='main':raise ValueError('unknown group')
    return d,{'tail_policy':tail,'threshold_hours':threshold,'quantile':.99 if threshold is not None else None,'algorithm':'numpy.quantile(method=linear)','comparison':'D <= training_threshold','reference_population':'main_training_R0c_eligible','reference_n':len(main_train),'reference_ids_sha256':identity(main_train[ID]),'retained_n':len(d),'retained_ids_sha256':identity(d[ID]),'evaluation':'all valid test IDs; never trimmed using test D'}
def raw_predictors(df,target_name):
    p=df[WX+REGION].astype(float).copy()
    if target_name=='R0c':p['log1p_customers']=np.log1p(df[C].astype(float))
    if not np.isfinite(p).all(axis=None):raise ValueError('incomplete predictors: define common population before fitting')
    return p
def fit_preprocessor(train,target_name):
    raw=raw_predictors(train,target_name);cols=WX+(['log1p_customers'] if target_name=='R0c' else [])
    sd=raw[cols].std(ddof=1)
    if not np.isfinite(sd).all() or sd.le(0).any():raise ValueError('zero/nonfinite training SD')
    return {'target':target_name,'scale_columns':cols,'mean':raw[cols].mean().to_dict(),'sd':sd.to_dict(),'sd_ddof':1,'years':sorted(train.new_year.astype(int).unique().tolist()),'months':sorted(train.new_month.astype(int).unique().tolist()),'unknown_category':'error','region_columns':REGION,'region_scale':'raw; population already natural log','training_ids_sha256':identity(train[ID])}
def design(df,prep,block='full'):
    raw=raw_predictors(df,prep['target']);year=df.new_year.astype(int);month=df.new_month.astype(int)
    if not year.isin(prep['years']).all() or not month.isin(prep['months']).all():raise ValueError('unseen calendar category; no reference fallback')
    z={c:(raw[c]-prep['mean'][c])/prep['sd'][c] for c in prep['scale_columns']}
    x=pd.DataFrame({'const':np.ones(len(df))},index=df.index)
    x['zG']=z[WX[0]];x['zG2']=x.zG**2;x['zRain24']=z[WX[1]];x['zTemp']=z[WX[2]];x['zPressure']=z[WX[3]];x['zG_zPressure']=x.zG*x.zPressure
    for c in REGION:x[c]=raw[c]
    for y in prep['years'][1:]:x[f'year_{y}']=year.eq(y).astype(float)
    for mo in prep['months'][1:]:x[f'month_{mo}']=month.eq(mo).astype(float)
    if prep['target']=='R0c':x['zK']=z['log1p_customers'];x['zK2']=x.zK**2
    if block not in ['full','control','G','K','GK']:raise ValueError('unknown variable block')
    keep_g=block in ['full','G','GK'];keep_k=block in ['full','K','GK']
    if not keep_g:x=x.drop(columns=G)
    if prep['target']=='R0c' and not keep_k:x=x.drop(columns=K)
    if prep['target']=='E0' and block in ['K','GK']:raise ValueError('customer block not defined for E0')
    for name in prep.get('extra_raw_columns',[]):
        if name!='log_n_stages':raise ValueError('unregistered diagnostic covariate')
        stage=df.stage_row_count.astype(float)
        if not (np.isfinite(stage)&stage.gt(0)).all():raise ValueError('invalid stage diagnostic covariate')
        x[name]=np.log(stage)
    return x.astype(float)
def fit_ols(train,prep,block,metadata):
    x=design(train,prep,block);y=target(train,prep['target']);a=x.to_numpy();coef,resid,rank,s=np.linalg.lstsq(a,y,rcond=None)
    if rank!=a.shape[1] or len(a)<=a.shape[1]:raise ValueError(f'unsupported design rank {rank}/{a.shape[1]}, n={len(a)}')
    return {'schema':'R03_portable_linear_v1','target':prep['target'],'target_scale':'log1p_C' if prep['target']=='E0' else 'log_D','block':block,'columns':list(x.columns),'parameters':coef.tolist(),'preprocessor':prep,'training_ids':sorted(train[ID].tolist()),'training_dates':sorted(train.new_date_utc.unique().tolist()),'training_n':len(train),'rank':int(rank),'condition_number':float(s[0]/s[-1]),'metadata':metadata,'uncertainty':'not part of this parameter archive','no_smearing':True}
def predict_eta(df,model):
    x=design(df,model['preprocessor'],model['block'])
    if list(x.columns)!=model['columns']:raise ValueError('design column order mismatch')
    return x.to_numpy()@np.asarray(model['parameters'])
def score(y,pred):
    y=np.asarray(y,dtype=float);p=np.asarray(pred,dtype=float)
    if y.shape!=p.shape or y.ndim!=1 or not np.isfinite(y).all() or not np.isfinite(p).all():raise ValueError('nonfinite/mismatched score inputs')
    n=len(y);sse=float(np.sum((y-p)**2));sst=float(np.sum((y-y.mean())**2)) if n else 0.
    return {'n':n,'SSE':sse,'SST':sst,'r2':None if n<2 or sst==0 else 1-sse/sst,'status':'undefined_small_or_constant' if n<2 or sst==0 else 'defined','weights':'event_equal','SST_center':'evaluation_target_mean'}
def score_oof(predictions,expected):
    if not expected[ID].is_unique or not predictions[ID].is_unique:raise ValueError('duplicate OOF/member IDs')
    if set(predictions[ID])!=set(expected[ID]):raise ValueError('incomplete/extra OOF IDs; no changed denominator')
    p=predictions.set_index(ID).loc[expected[ID]].reset_index();check=expected.set_index(ID).loc[p[ID]]
    if not np.array_equal(p.fold.to_numpy(),check.fold.to_numpy()):raise ValueError('OOF fold mismatch')
    if not np.allclose(p.y.to_numpy(),check.y.to_numpy(),rtol=0,atol=0):raise ValueError('OOF target mismatch')
    if not p.prediction_source.eq('OOF_date_group_diagnostic').all():raise ValueError('non-OOF predictions mixed into scoring')
    pooled=score(p.y,p.prediction_eta);folds={str(f):score(d.y,d.prediction_eta) for f,d in p.groupby('fold')}
    rs=[v['r2'] for v in folds.values()];defined=all(x is not None for x in rs)
    return {'pooled_oof_r2':pooled['r2'],'pooled':pooled,'folds':folds,'mean_fold_r2':float(np.mean(rs)) if defined else None,'mean_fold_policy':'unweighted across all declared folds; undefined if any fold undefined','evaluation_ids_sha256':identity(p[ID]),'failed_folds':[],'prediction_scale':p.target_scale.iloc[0]}
def paired_contributions(metrics,target_name):
    required=['control','G'] if target_name=='E0' else ['control','G','K','GK']
    if set(metrics)!=set(required):raise ValueError('required block comparison incomplete')
    if len({metrics[b]['evaluation_ids_sha256'] for b in required})!=1:raise ValueError('unpaired populations')
    r={b:metrics[b]['pooled_oof_r2'] for b in required}
    def delta(a,b):return None if r[a] is None or r[b] is None else r[a]-r[b]
    out={'gust_from_control':delta('G','control')}
    if target_name=='R0c':out.update(customers_from_control=delta('K','control'),gust_given_customers=delta('GK','K'),customers_given_gust=delta('GK','G'))
    return out
