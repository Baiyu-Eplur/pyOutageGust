"""R02 runner: prepare, cache-only weather inspection, and derived input assembly."""
import sys,json,hashlib,argparse,time,io,inspect,platform,datetime
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;P=R.parent;Q=O/'R02'
sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'.venv/Lib/site-packages'))
sys.path.insert(0,str(R/'scripts/event_input_repair'))
import pandas as pd
import numpy as np
import pyarrow
import r02_events as m
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.bool_,)):return bool(x)
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if x is pd.NA or x is pd.NaT:return None
    return x
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,default=str,allow_nan=False),encoding='utf-8')
def log(s):print(s,flush=True)
def prepare():
    log('Preparing from all raw stage rows, with frozen source identities')
    rawp=P/'data/ukpn-iis.csv';v3p=P/'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv'
    raw=pd.read_csv(rawp,dtype=str,keep_default_na=False);raw['source_row_number']=np.arange(1,len(raw)+1,dtype=np.int64)
    cols=['source_row_number',m.ID,'cause_group_official',m.C,m.D,m.A,'Duration (hours)',*m.WX,'wx_time_used_utc','weather_status_v3','request_key','lat','lon','population',*m.REGION]
    v=pd.read_csv(v3p,usecols=cols,low_memory=False)
    assert len(v)==len(raw) and v.source_row_number.is_unique
    check=raw[['source_row_number',m.ID]].merge(v[['source_row_number',m.ID]],on='source_row_number',validate='one_to_one')
    assert check[m.ID+'_x'].eq(check[m.ID+'_y']).all()
    stage=raw.merge(v.drop(columns=m.ID),on='source_row_number',validate='one_to_one',sort=False)
    stage.to_parquet(Q/'data/source_stage_projection.parquet',index=False)
    identity=json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8'))
    rawsha=next(x['sha256'] for x in identity if x['key']=='raw')
    gm=json.loads((O/'contracts/cause_group_map.json').read_text(encoding='utf-8'))['groups']
    e,qa=m.construct_events(stage,rawsha,gm)
    checks={}
    for c in [m.C,m.D,m.A]:
        a=pd.to_numeric(e[c]);b=pd.to_numeric(e['v3_'+c]);err=(a-b).abs()
        bad=(a.isna()!=b.isna())|err.gt(1e-8)
        checks[c]={'mismatches':int(bad.sum()),'max_abs_difference':float(err.max())}
        assert not bad.any(),checks[c]
    save(Q/'checks/aggregation_consistency.json',checks)
    # Reuse the selected point's frozen LAD. Check all earliest candidates for disagreement.
    times,_=m.parse_offset_time(stage['Start Date and Time']);minima=times.groupby(stage[m.ID]).transform('min')
    tie_stage=stage.loc[times.eq(minima)]
    lnu=tie_stage.groupby(m.ID)['LAD21CD'].nunique(dropna=False)
    e['LAD_source_status']='selected_stage_frozen_v3'
    conflicts=e[m.ID].isin(lnu.loc[lnu.gt(1)].index)|e.coordinate_conflict
    e.loc[conflicts,['LAD21CD','LAD21NM']]=pd.NA;e.loc[conflicts,'LAD_source_status']='tie_LAD_or_coordinate_unresolved'
    # Genuinely missing selected LAD with usable point: deterministic same-boundary recovery only.
    needs=e.LAD21CD.isna()&e.weather_query_eligible&~conflicts
    geo={'earliest_tie_LAD_conflicts':int(lnu.gt(1).sum()),'missing_before':int(e.LAD21CD.isna().sum()),'attempted':int(needs.sum())}
    if needs.any():
        import geopandas as gpd
        shp=P/'data/Local_Authority_Districts_December_2021_UK_BGC_2022/LAD_DEC_2021_UK_BGC.shp'
        points=gpd.GeoDataFrame(e.loc[needs,[m.ID,'lat','lon']],geometry=gpd.points_from_xy(e.loc[needs,'lon'],e.loc[needs,'lat']),crs='EPSG:4326')
        lad=gpd.read_file(shp).to_crs('EPSG:4326');join=gpd.sjoin(points,lad[['LAD21CD','LAD21NM','geometry']],how='left',predicate='within')
        counts=join.groupby(m.ID)['LAD21CD'].count();unique=join.loc[join[m.ID].isin(counts.loc[counts.eq(1)].index)].set_index(m.ID)
        for col in ['LAD21CD','LAD21NM']:
            ix=needs&e[m.ID].isin(unique.index);e.loc[ix,col]=e.loc[ix,m.ID].map(unique[col])
        e.loc[needs&e.LAD21CD.notna(),'LAD_source_status']='R02_unique_within_same_2021_boundary'
        geo['ambiguous_matches']=int(counts.gt(1).sum());geo['shapefile_sha256']=sha(shp)
    geo['missing_after']=int(e.LAD21CD.isna().sum());save(Q/'checks/LAD_connection.json',geo)
    # If a new LAD had to be assigned, do not use regional fields from another/missing LAD.
    changed=e.LAD21CD.fillna('<NA>').ne(e.old_LAD21CD.fillna('<NA>'))
    regional_cols=m.REGION[2:]
    if changed.any():
        lookup=stage.dropna(subset=['LAD21CD'])[['LAD21CD',*regional_cols]].drop_duplicates()
        count=lookup.groupby('LAD21CD')[regional_cols].nunique(dropna=False)
        if count.gt(1).any(axis=None):raise ValueError('Static regional lookup conflicts')
        lookup=lookup.drop_duplicates('LAD21CD').set_index('LAD21CD')
        for c in regional_cols:e.loc[changed,c]=e.loc[changed,'LAD21CD'].map(lookup[c])
    e['regional_proxy_flag']=e.LAD21CD.eq('E06000060')
    e.loc[e.regional_proxy_flag,'regional_source_version']='legacy_arithmetic_crosswalk'
    popp=P/'data/population_lad_long.csv';pop=pd.read_csv(popp,low_memory=False)
    e=m.reconnect_population(e,pop)
    save(Q/'checks/population_connection.json',{'path':str(popp),'sha256':sha(popp),'lookup_rows':len(pop),'duplicate_keys':int(pop.duplicated(['LAD23CD','year']).sum()),'events_after_merge':len(e),'missing_population':int(e.population.isna().sum()),'missing_by_year':e.loc[e.population.isna(),'new_year'].value_counts(dropna=False).to_dict()})
    for c,target in [('income_deprivation_rate',.06325),('deprivation_gap_pct',.1875),('morans_i',.30)]:
        assert np.allclose(e.loc[e.regional_proxy_flag,c],target,rtol=0,atol=1e-12),c
    e['regional_basis']='frozen_static_LAD_lookup_with_explicit_Buck_proxy'
    e.to_parquet(Q/'data/pre_weather_events.parquet',index=False)
    save(Q/'checks/event_structure.json',qa)
    save(Q/'checks/runtime.json',{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__,'package_path':str(P/'.venv/Lib/site-packages'),'models_run':0,'new_weather_requests':0})
    log(json.dumps({'prepared_events':len(e),'ties':qa['earliest_tie_events'],'LAD':geo,'aggregates':checks},ensure_ascii=False))

def weather():
    ep=Q/'data/pre_weather_events.parquet';e=pd.read_parquet(ep);wroot=Q/'weather_checkpoint'
    fingerprint=hashlib.sha256((sha(ep)+inspect.getsource(m.inspect_hourly)).encode()).hexdigest()
    fp=wroot/'fingerprint.json'
    if fp.exists():assert json.loads(fp.read_text())['fingerprint']==fingerprint,'Weather checkpoint incompatible with current event/inspection code'
    else:save(fp,{'fingerprint':fingerprint,'event_sha256':sha(ep),'inspect_function_sha256':hashlib.sha256(inspect.getsource(m.inspect_hourly).encode()).hexdigest()})
    chunks=sorted(wroot.glob('chunk_*.parquet'));done=set()
    for p in chunks:
        part=pd.read_parquet(p,columns=['request_key']);done.update(part.request_key)
    cache=P/'data/weather_request_cache';total=e.loc[e.weather_query_eligible,'request_key'].nunique()
    batches=[];batchnum=len(chunks);count=0;started=time.monotonic()
    log(f'Inspecting {total} distinct earliest-event query keys; resume completed keys={len(done)}')
    for key,group in e.loc[e.weather_query_eligible].groupby('request_key',sort=True):
        if key in done:continue
        path=cache/f'{key}.pkl';hourly=None;err=None;filehash=None;status='missing_file';attrs={};sz=None
        if path.exists():
            try:
                b=path.read_bytes();filehash=hashlib.sha256(b).hexdigest();sz=len(b)
                hourly=pd.read_pickle(io.BytesIO(b));status='readable'
                if not isinstance(hourly,pd.DataFrame):status='invalid_cache_type'
                else:attrs=hourly.attrs
            except Exception as ex:status='unreadable';err=f'{type(ex).__name__}: {ex}'
        for t in sorted(group.new_weather_hour_utc.unique()):
            r={'request_key':key,'weather_hour_utc':pd.Timestamp(t),'cache_file_path':str(path),'cache_status':status,'cache_sha256':filehash,'cache_bytes':sz,'cache_error':err,'cache_attrs_json':json.dumps(attrs,default=str,ensure_ascii=False),'product_status':'historical_model_unresolved','units_basis':'historical_request_code_ms_mm_GMT','units_response_metadata_available':False}
            if status=='readable':r.update(m.inspect_hourly(hourly,t))
            batches.append(r)
        count+=1
        if count%1000==0:
            pd.DataFrame(batches).to_parquet(wroot/f'chunk_{batchnum:04d}.parquet',index=False);batchnum+=1;batches=[]
        if count%2000==0:log(f'Weather keys: {len(done)+count}/{total}; elapsed {time.monotonic()-started:.1f}s')
    if batches:pd.DataFrame(batches).to_parquet(wroot/f'chunk_{batchnum:04d}.parquet',index=False)
    frames=[pd.read_parquet(p) for p in sorted(wroot.glob('chunk_*.parquet'))]
    result=pd.concat(frames,ignore_index=True).sort_values(['request_key','weather_hour_utc'])
    assert not result.duplicated(['request_key','weather_hour_utc']).any()
    result.to_parquet(Q/'data/weather_key_hour_audit.parquet',index=False)
    save(Q/'checks/weather_scan_summary.json',{'eligible_event_count':int(e.weather_query_eligible.sum()),'distinct_query_keys':total,'key_hour_rows':len(result),'existing_files':result.loc[result.cache_status.ne('missing_file'),'request_key'].nunique(),'cache_status_by_file':result.drop_duplicates('request_key').cache_status.value_counts().to_dict(),'key_hour_status_counts':result.cache_status.value_counts().to_dict(),'rain_status_by_key_hour':result.rain_window_status.value_counts(dropna=False).to_dict(),'scan_seconds':time.monotonic()-started,'new_requests':0})
    log('Full earliest-event cache inspection finished')

def finish():
    e=pd.read_parquet(Q/'data/pre_weather_events.parquet');w=pd.read_parquet(Q/'data/weather_key_hour_audit.parquet')
    cols=[c for c in w if c not in ['request_key','weather_hour_utc']]
    w=w.rename(columns={c:'cache_'+c for c in cols})
    e=e.merge(w,left_on=['request_key','new_weather_hour_utc'],right_on=['request_key','weather_hour_utc'],how='left',validate='many_to_one',sort=False)
    for c in m.WX:e[c]=np.nan
    e['weather_source']='none';e['weather_validation_tier']='unavailable'
    readable=e['cache_cache_status'].eq('readable')&e.weather_query_eligible
    for c in m.WX:e.loc[readable,c]=pd.to_numeric(e.loc[readable,'cache_'+c],errors='coerce')
    e.loc[readable,'weather_source']='historical_cache_exact_key';e.loc[readable,'weather_validation_tier']='strict_cache_checked'
    original_hour=pd.to_datetime(e.earliest_v3_wx_time_used_utc,utc=True,format='mixed',errors='coerce')
    fallback=~readable&e.weather_query_eligible&e.request_key.eq(e.earliest_v3_request_key)&original_hour.eq(e.new_weather_hour_utc)
    for c in m.WX:e.loc[fallback,c]=pd.to_numeric(e.loc[fallback,'earliest_v3_'+c],errors='coerce')
    has_value=e[m.WX].notna().any(axis=1)
    e.loc[fallback&has_value,'weather_source']='frozen_v3_selected_source_row';e.loc[fallback&has_value,'weather_validation_tier']='v3_only_window_not_reverified'
    e['weather_numeric_available']=np.isfinite(e[m.WX]).all(axis=1)&e.gust_0h.ge(0)&e.precipitation_24h_sum.ge(0)
    e['weather_product_status']='historical_model_unresolved';e['weather_units_basis']='historical_request_code_ms_mm_GMT'
    e['weather_cache_status']=e.cache_cache_status.fillna('query_ineligible')
    e['weather_source_row']=e.selected_source_row;e['wx_time_used_utc']=e.new_weather_hour_utc.where(e.weather_numeric_available)
    e['rain_window_left_open_utc']=e.new_weather_hour_utc-pd.Timedelta(hours=24);e['rain_window_right_closed_utc']=e.new_weather_hour_utc
    e['weather_source_warning']=np.where(e.weather_validation_tier.eq('v3_only_window_not_reverified'),'original_cache_unavailable_window_values_not_reverified','historical_model_unresolved')
    e=m.qualify(e)
    # Crosswalk from current inputs to all four accepted H0 samples; no model fitting or folds.
    for s in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        old=pd.read_csv(R/f'results/code_audit_20260905/{s}_sample_membership.csv',usecols=[m.ID])
        e['H0_'+s]=e[m.ID].isin(old[m.ID]);e['membership_'+s]=np.select([e['H0_'+s]&e['candidate_'+s],e['H0_'+s]&~e['candidate_'+s],~e['H0_'+s]&e['candidate_'+s]],['common','exit','enter'],default='neither')
    # Explicit diagnostic compatibility membership only; no shared-fold/B1 analysis produced here.
    caps={}
    for prefix,cause in [('main',e.legacy_first_cause.map({code:grp for grp,codes in json.loads((O/'contracts/cause_group_map.json').read_text(encoding='utf-8'))['groups'].items() for code in codes}).isin(['technical_asset','weather_natural'])),('weather',e.old_cause_group.eq('weather_natural'))]:
        compat=e.new_in_study_utc&e.weather_numeric_available&e.region_numeric_complete&cause
        rd=compat&np.isfinite(e[m.D])&e[m.D].gt(0)
        cap=float(e.loc[rd,m.D].quantile(.99));caps[prefix]=cap
        e['R1_compat_candidate_'+prefix+'_E0']=(compat&np.isfinite(e[m.C])&e[m.C].ge(0)).fillna(False).astype(bool)
        e['R1_compat_candidate_'+prefix+'_R0c']=(rd&e[m.D].le(cap)&np.isfinite(e[m.C])&e[m.C].ge(0)).fillna(False).astype(bool)
    save(Q/'checks/R1_compatibility_caps.json',{'warning':'diagnostic historical first-cause/independent-p99 membership only; no model or folds; not B1','p99_hours':caps})
    e['new_storm_count']=e[['new_storm_'+n for n in m.STORMS]].sum(axis=1)
    e['old_storm_count']=e[['old_storm_'+n for n in m.STORMS]].sum(axis=1)
    e['UTC_London_date_diff']=e.new_date_utc.ne(e.new_date_london)
    e['UTC_London_study_diff']=e.new_in_study_utc.ne(e.new_in_study_london)
    e['UTC_London_period_diff']=e.new_period.ne(e.new_period_london)
    for c in m.WX:
        e['delta_'+c]=e[c]-e['old_'+c]
    for s in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        reason=e['R0c_exclusion_reasons' if s.endswith('R0c') else 'E0_exclusion_reasons'].copy()
        if s.startswith('weather'):
            mask=~e.cause_group_event.eq('weather_natural')
            reason.loc[mask]=reason.loc[mask].where(reason.loc[mask].eq(''),reason.loc[mask]+';')+'cause_not_weather_consensus'
        e['membership_reason_'+s]=np.where(e['membership_'+s].eq('exit'),reason,np.where(e['membership_'+s].eq('enter'),'new_candidate_absent_H0;compare_old_inputs_and_R1_compat_membership',''))
        e['oldnew_membership_scope_'+s]='H0 accepted historical membership vs R02 full-valid candidate; no fitted B1'
    e=e.sort_values(m.ID).reset_index(drop=True)
    p=Q/'data/R02_event_master.parquet';e.to_parquet(p,index=False)
    # A compressed CSV is portable outside this Python environment.
    e.to_csv(Q/'data/R02_event_master.csv.gz',index=False,compression='gzip')
    manifest={'run_id':'R02_input_20260905','execution_scope':'input_rebuilt_no_models','event_count':len(e),'source_stage_count':237901,'event_table':{'path':str(p),'sha256':sha(p)},'portable_csv':{'path':str(Q/'data/R02_event_master.csv.gz'),'sha256':sha(Q/'data/R02_event_master.csv.gz')},'input_identity':json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8')),'producer':str(R/'scripts/event_input_repair/r02_events.py'),'producer_sha256':sha(R/'scripts/event_input_repair/r02_events.py'),'runner':str(Path(__file__).resolve()),'runner_sha256':sha(Path(__file__)),'analysis_calendar':'UTC_frozen_R01_proxy','business_calendar':'unknown','historical_weather_model':'unresolved','models_run':0,'columns':list(e.columns)}
    manifest['config_files']=[{'path':str(p),'sha256':sha(p)} for p in sorted((O/'contracts').glob('*')) if p.is_file()]
    manifest['population_connection']=json.loads((Q/'checks/population_connection.json').read_text(encoding='utf-8'))
    manifest['weather_audit']={'path':str(Q/'data/weather_key_hour_audit.parquet'),'sha256':sha(Q/'data/weather_key_hour_audit.parquet'),'network_requests':0}
    manifest['validation_tier_note']='strict_cache_checked verifies hour/value/window only; historical model and response units metadata remain unresolved'
    save(Q/'data/EVENT_MANIFEST.json',manifest)
    log(json.dumps({'event_master':len(e),'numeric_weather':int(e.weather_numeric_available.sum()),'candidates':{s:int(e['candidate_'+s].sum()) for s in ['main_E0','main_R0c','weather_E0','weather_R0c']},'v3_only_numeric_complete':int((e.weather_numeric_available&e.weather_validation_tier.eq('v3_only_window_not_reverified')).sum())},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','weather','finish']);args=parser.parse_args()
    globals()[args.phase]()
