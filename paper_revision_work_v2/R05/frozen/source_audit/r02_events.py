"""R02 deterministic event input, with no import-time filesystem/network writes.

Source rows must retain their frozen 1-based source_row_number before any shuffle.
The separate runner owns all I/O. This module contains no model fitting.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

ID='Incident Reference'
C='customers_v2_event_excl_reinterruptions'
D='duration_B_full_span_hours'
A='duration_A_customer_weighted_hours'
WX=['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h']
META=['Spatial Coordinates','Cause Code','licence_area','regulatory_year','substation','SiteFunctionalLocation']
REGION=['LAD21CD','LAD21NM','income_deprivation_rate','deprivation_gap_pct','morans_i','rural_urban_classification']
START=pd.Timestamp('2021-04-01T00:00Z');END=pd.Timestamp('2024-04-01T00:00Z');LATER=pd.Timestamp('2023-09-30T00:00Z')
STORMS={'Arwen':('2021-11-25','2021-11-28'),'Dudley':('2022-02-15','2022-02-17'),'Eunice':('2022-02-17','2022-02-19'),'Franklin':('2022-02-19','2022-02-22'),'Babet':('2023-10-17','2023-10-22'),'Ciaran':('2023-10-31','2023-11-03'),'Henk':('2024-01-01','2024-01-03')}

def parse_offset_time(s):
    text=s.astype('string').str.strip()
    offset=text.str.extract(r'(Z|[+-]\d{2}:\d{2})$')[0]
    parsed=pd.to_datetime(text.where(offset.notna()),utc=True,format='mixed',errors='coerce')
    return parsed,offset

def normalized_cause(s):
    x=s.astype('string').str.strip().str.upper().replace('',pd.NA)
    nums=pd.to_numeric(x,errors='coerce');integer=nums.notna()&nums.mod(1).eq(0)
    x.loc[integer]=nums.loc[integer].astype(int).map(lambda n:f'{n:02d}')
    return x

def temporal_columns(times,prefix=''):
    t=pd.to_datetime(times,utc=True,format='mixed',errors='coerce');london=t.dt.tz_convert('Europe/London')
    d=pd.DataFrame(index=t.index)
    d[prefix+'time_utc']=t;d[prefix+'time_london']=london.astype('string')
    d[prefix+'date_utc']=t.dt.strftime('%Y-%m-%d');d[prefix+'date_london']=london.dt.strftime('%Y-%m-%d')
    d[prefix+'year']=t.dt.year.astype('Int64');d[prefix+'month']=t.dt.month.astype('Int64')
    d[prefix+'year_london']=london.dt.year.astype('Int64');d[prefix+'month_london']=london.dt.month.astype('Int64')
    d[prefix+'weather_hour_utc']=t.dt.floor('h')
    inside=t.ge(START)&t.lt(END)
    d[prefix+'in_study_utc']=inside
    d[prefix+'in_study_london']=london.ge(pd.Timestamp('2021-04-01',tz='Europe/London'))&london.lt(pd.Timestamp('2024-04-01',tz='Europe/London'))
    d[prefix+'period']=np.select([inside&t.lt(LATER),inside&t.ge(LATER)],['development','later'],default='outside_study')
    il=d[prefix+'in_study_london'];lb=pd.Timestamp('2023-09-30',tz='Europe/London')
    d[prefix+'period_london']=np.select([il&london.lt(lb),il&london.ge(lb)],['development','later'],default='outside_study')
    for name,(a,b) in STORMS.items():
        d[prefix+'storm_'+name]=t.ge(pd.Timestamp(a,tz='UTC'))&t.lt(pd.Timestamp(b,tz='UTC')+pd.Timedelta(days=1))
        d[prefix+'storm_london_'+name]=london.ge(pd.Timestamp(a,tz='Europe/London'))&london.lt(pd.Timestamp(b,tz='Europe/London')+pd.DateOffset(days=1))
    return d

def construct_events(stage,raw_sha,group_map):
    s=stage.copy()
    if s.source_row_number.isna().any() or not s.source_row_number.is_unique:raise ValueError('Source row identity absent/duplicated')
    s[ID]=s[ID].astype('string').str.strip()
    if s[ID].isna().any() or s[ID].eq('').any():raise ValueError('Missing Incident Reference')
    s['_start'],s['_offset']=parse_offset_time(s['Start Date and Time'])
    s['_end'],s['_end_offset']=parse_offset_time(s['End Date and Time'])
    s['_cause']=normalized_cause(s['Cause Code'])
    s['_cust']=pd.to_numeric(s['Number of Customers Restored'].astype('string').str.replace(',','',regex=False),errors='coerce')
    ri=s['Re-interruption Stage'].astype('string').str.strip().str.upper()
    s['_repeat']=ri.isin(['Y','1']);s['_repeat_unknown']=~ri.isin(['Y','1','N','0'])
    s['_duration']=(s['_end']-s['_start']).dt.total_seconds().div(3600).where(lambda x:x.ge(0))
    s['_eligible_customers']=s['_cust'].mask(s['_repeat'])
    s['_weighted']=s['_cust']*s['_duration'];s['_weight']=s['_cust'].where(s['_duration'].notna())
    s['_stage_num']=pd.to_numeric(s['Restoration Stage'],errors='coerce')
    s['_sourceid_dup']=s['unique_identifier'].ne('')&s['unique_identifier'].duplicated(keep=False)
    g=s.groupby(ID,sort=True)
    first=s.sort_values('source_row_number',kind='stable').drop_duplicates(ID).set_index(ID)
    earliest=s.sort_values(['_start','source_row_number'],kind='stable',na_position='last').drop_duplicates(ID).set_index(ID)
    e=earliest.copy().drop(columns=[x for x in earliest if x.startswith('_')])
    e=e.sort_index();first=first.reindex(e.index)
    # Source primary keys, full stage membership, and original source strings remain explicit.
    e['raw_sha256']=raw_sha;e['source_rows']=g.source_row_number.agg(lambda v:','.join(map(str,sorted(v))))
    e['selected_source_row']=earliest.source_row_number;e['old_source_row']=first.source_row_number
    e['selected_source_row_key']=raw_sha+':'+e.selected_source_row.astype(str)
    e['selected_start_raw']=earliest['Start Date and Time'];e['selected_start_offset']=earliest['_offset']
    e['selected_end_raw']=earliest['End Date and Time'];e['selected_end_offset']=earliest['_end_offset']
    e['old_start_raw']=first['Start Date and Time'];e['old_start_offset']=first['_offset']
    for prefix,t in [('new_',earliest['_start']),('old_',first['_start'])]:
        e=e.join(temporal_columns(t,prefix))
    e['event_time_proxy_utc']=e.new_time_utc;e['earliest_recorded_start_utc']=e.new_time_utc
    e['business_onset_utc']=pd.NaT;e['business_calendar_timezone']='unknown'
    e['analysis_calendar_timezone']='UTC';e['event_time_basis']='earliest_available_stage_start'
    e['incident_date_utc']=e.new_date_utc;e['incident_year']=e.new_year;e['incident_month']=e.new_month
    e['time_lag_removed_hours']=(e.old_time_utc-e.new_time_utc).dt.total_seconds()/3600
    e['max_stage_end_utc']=g['_end'].max();e['max_stage_start_utc']=g['_start'].max()
    e['n_stages']=g.size();e['stage_row_count']=e.n_stages
    e['min_stage_number']=g['_stage_num'].min();e['n_distinct_stage_numbers']=g['_stage_num'].nunique()
    e['min_stage_ge2']=e.min_stage_number.ge(2);e['first_stage_observed']=g['_stage_num'].agg(lambda x:x.eq(1).any())
    e['stage_number_missing']=g['_stage_num'].count().lt(g.size())
    minimum=g['_start'].transform('min');ties=s.loc[s['_start'].eq(minimum)]
    tg=ties.groupby(ID,sort=True);tn=tg[META].nunique(dropna=False)
    e['earliest_tie_count']=tg.size().reindex(e.index,fill_value=0)
    e['earliest_candidate_source_rows']=tg.source_row_number.agg(lambda x:','.join(map(str,sorted(x)))).reindex(e.index)
    for c in META:e['tie_conflict_'+c]=tn[c].gt(1).reindex(e.index,fill_value=False)
    e['source_id_conflict']=g['_sourceid_dup'].any()
    e['cause_codes_all']=g['_cause'].agg(lambda x:','.join(sorted(x.dropna().unique())))
    nc=g['_cause'].nunique();e['cause_conflict']=nc.gt(1);e['cause_missing_any']=g['_cause'].count().lt(g.size())
    consensus=g['_cause'].first().where(nc.eq(1));e['cause_code_event']=consensus
    lookup={code:grp for grp,codes in group_map.items() for code in codes}
    e['cause_group_event']=consensus.map(lookup).fillna('unmapped').mask(nc.gt(1),'unresolved').mask(nc.eq(0),'missing')
    e['cause_basis']=np.where(nc.eq(1),'record_consensus_retrospective','unresolved_or_missing')
    e['cause_source_rows']=e.source_rows;e['cause_final_diagnosis_verified']=False
    e['legacy_first_cause']=first['_cause'];e['old_cause_group']=first['cause_group_official']
    e['cause_group_official']=e.cause_group_event # compatibility alias, groups remain researcher-defined
    allmeta=g[['Spatial Coordinates','licence_area','substation','SiteFunctionalLocation']].nunique(dropna=False)
    e['event_geography_conflict']=allmeta.gt(1).any(axis=1)
    e['event_identity_unresolved']=e.cause_conflict|e.source_id_conflict|e.event_geography_conflict
    e['event_identity_status']=np.where(e.event_identity_unresolved,'unresolved','record_id_consistent_not_business_certified')
    e['source_window_left_censoring_possible']=True
    for c in ['clock_stopping_status','deemed_restoration_status','true_initial_customers_status','stage_completeness_business']:e[c]='unknown'
    cc=g['_eligible_customers'].sum(min_count=1);dd=(g['_end'].max()-g['_start'].min()).dt.total_seconds()/3600
    aa=g['_weighted'].sum(min_count=1)/g['_weight'].sum(min_count=1).where(lambda x:x.gt(0))
    e['C_id_formula']=cc;e['D_id_formula']=dd;e['A_id_formula']=aa
    e['all_stages_are_reinterruption']=g['_repeat'].all()
    e['customer_input_incomplete']=g['_cust'].count().lt(g.size())|g['_cust'].min().lt(0)|g['_repeat_unknown'].any()
    e['time_input_incomplete']=g['_start'].count().lt(g.size())|g['_end'].count().lt(g.size())|g['_duration'].count().lt(g.size())
    e[C]=cc.mask(e.customer_input_incomplete);e[D]=dd.mask(e.time_input_incomplete);e[A]=aa
    e['outcome_interpretation_status']=np.where(e.event_identity_unresolved,'id_formula_only_identity_unresolved','recorded_consequence_proxy')
    e['Duration (hours)']=e[A]
    for c in [C,D,A,*WX,'wx_time_used_utc','request_key','population',*REGION,'lat','lon']:
        e['old_'+c]=first[c]
    for c in [C,D,A]:e['v3_'+c]=earliest[c]
    for c in [*WX,'wx_time_used_utc','request_key','weather_status_v3','population']:
        e['earliest_v3_'+c]=earliest[c]
    coords=e['Spatial Coordinates'].astype('string').str.split(',',expand=True)
    e['lat']=pd.to_numeric(coords[0],errors='coerce');e['lon']=pd.to_numeric(coords[1],errors='coerce')
    e['coordinate_conflict']=e['tie_conflict_Spatial Coordinates']
    e.loc[e.coordinate_conflict,['lat','lon']]=np.nan
    e['weather_query_eligible']=(e.lat.between(49,61)&e.lon.between(-9,3)&e.new_time_utc.notna()).fillna(False).astype(bool)
    e['lat_r']=e.lat.round(1);e['lon_r']=e.lon.round(1)
    e['request_key']=(e.lat_r.astype(str)+'_'+e.lon_r.astype(str)+'_'+e.new_date_utc).where(e.weather_query_eligible)
    e['coordinate_basis']='reported_primary_substation_proxy';e['coordinate_source_row']=e.selected_source_row
    e['regional_source_row']=e.selected_source_row
    e['regional_source_version']='v3_frozen_static_lookup'
    e['regional_proxy_flag']=e.LAD21CD.eq('E06000060')
    e.loc[e.regional_proxy_flag,'regional_source_version']='legacy_arithmetic_crosswalk'
    e['geography_compatibility']='LAD21_to_LAD23_same_code_not_full_boundary_certification'
    e['recovery_crosses_study_end']=e.new_in_study_utc&e.max_stage_end_utc.ge(END)
    e['stages_cross_study_end']=e.new_in_study_utc&e.max_stage_start_utc.ge(END)
    e['recovery_crosses_development_end']=e.new_time_utc.lt(LATER)&e.max_stage_end_utc.ge(LATER)
    e['input_version']='R02_20260905'
    qa={'tie_metadata_fields':META,'tie_metadata_conflict_counts':{c:int(tn[c].gt(1).sum()) for c in META},'all_stage_geography_conflict_counts':{c:int(allmeta[c].gt(1).sum()) for c in allmeta},'source_rows':len(s),'events':len(e),'earliest_tie_events':int(e.earliest_tie_count.gt(1).sum()),'raw_offset_counts':s['_offset'].value_counts(dropna=False).to_dict()}
    return e.reset_index(),qa

def reconnect_population(events,population):
    e=events.copy();p=population[['LAD23CD','year','population']].copy()
    p['LAD23CD']=p.LAD23CD.astype('string').str.strip();p['year']=pd.to_numeric(p.year,errors='coerce').astype('Int64')
    if p.duplicated(['LAD23CD','year']).any():raise ValueError('Population lookup duplicate key')
    e=e.drop(columns=['population'],errors='ignore')
    e=e.merge(p.rename(columns={'LAD23CD':'LAD21CD','year':'new_year'}),on=['LAD21CD','new_year'],how='left',validate='many_to_one',sort=False)
    e['population_source']='population_lad_long.csv';e['population_lookup_year']=e.new_year
    e['population_join_status']=np.where(e.population.notna(),'matched_same_code','missing_key_or_value')
    e['log_population']=np.log(e.population.where(e.population.gt(0)))
    return e

def inspect_hourly(hourly,target):
    """Strict exact-hour and 24 unique finite nonnegative precipitation endpoints."""
    out={c:None for c in WX};out.update(exact_hour_count=0,rain_window_rows=0,rain_valid_values=0,rain_unique_hours=0,rain_window_status='unreadable',cache_hour_valid=False)
    if not isinstance(hourly,pd.DataFrame) or 'time_utc' not in hourly:return out
    t=pd.Timestamp(target);times=pd.to_datetime(hourly.time_utc,utc=True,format='mixed',errors='coerce')
    here=hourly.loc[times.eq(t)];out['exact_hour_count']=len(here)
    if len(here)==1:
        row=here.iloc[0]
        for dest,source in [('gust_0h','wind_gusts_10m'),('temperature_0h','temperature_2m'),('pressure_msl_0h','pressure_msl')]:
            val=pd.to_numeric(row.get(source),errors='coerce')
            if pd.notna(val) and np.isfinite(val) and (dest!='gust_0h' or val>=0):out[dest]=float(val)
    mask=times.gt(t-pd.Timedelta(hours=24))&times.le(t);wt=times.loc[mask];win=hourly.loc[mask]
    rain=pd.to_numeric(win.get('precipitation',pd.Series(dtype=float)),errors='coerce')
    out.update(rain_window_rows=len(win),rain_unique_hours=int(wt.nunique()),rain_valid_values=int((np.isfinite(rain)&rain.ge(0)).sum()))
    expected=pd.date_range(t-pd.Timedelta(hours=23),t,freq='h')
    if len(win)!=24:status='row_count_not_24'
    elif wt.duplicated().any():status='duplicate_hour'
    elif set(wt)!=set(expected):status='hour_grid_mismatch'
    elif out['rain_valid_values']!=24:status='invalid_or_missing_rain_value'
    else:status='valid_24_unique_values';out['precipitation_24h_sum']=float(rain.sum())
    out['rain_window_status']=status;out['cache_hour_valid']=len(here)==1
    return out

def resolve_weather(v3_row,cache_result,cache_status,query_consistent=True):
    """Cache authoritative when readable; preserve v3-only numeric provenance separately."""
    vals={c:np.nan for c in WX}
    tier='unavailable';source='none'
    if not query_consistent:return {**vals,'weather_source':'query_conflict','weather_validation_tier':'unavailable','weather_numeric_available':False}
    if cache_status=='readable':
        vals.update({c:cache_result.get(c,np.nan) for c in WX});tier='strict_cache_checked';source='historical_cache_exact_key'
    else:
        for c in WX:
            v=pd.to_numeric(v3_row.get('earliest_v3_'+c),errors='coerce')
            if pd.notna(v) and np.isfinite(v):vals[c]=float(v)
        if any(pd.notna(v) for v in vals.values()):tier='v3_only_window_not_reverified';source='frozen_v3_selected_source_row'
    available=all(pd.notna(v) and np.isfinite(v) for v in vals.values())
    if available and (vals['gust_0h']<0 or vals['precipitation_24h_sum']<0):available=False
    return {**vals,'weather_source':source,'weather_validation_tier':tier,'weather_numeric_available':available}

def qualify(events):
    e=events.copy();u=e.rural_urban_classification.astype('string').str.strip().str.lower()
    e['urban_binary']=np.where(u.str.contains('urban',na=False),1.,np.where(u.str.contains('rural',na=False),0.,np.nan))
    e['region_numeric_complete']=np.isfinite(e[['log_population','income_deprivation_rate','deprivation_gap_pct','morans_i','urban_binary']].apply(pd.to_numeric,errors='coerce').astype(float)).all(axis=1)&e.LAD21CD.notna()
    e['cause_in_main']=e.cause_group_event.isin(['weather_natural','technical_asset'])
    e['candidate_base']=e.new_in_study_utc&e.weather_numeric_available&e.region_numeric_complete&e.cause_in_main&~e.event_identity_unresolved
    c_numeric=pd.to_numeric(e[C],errors='coerce').astype(float)
    d_numeric=pd.to_numeric(e[D],errors='coerce').astype(float)
    c_valid=np.isfinite(c_numeric)&c_numeric.ge(0)
    d_valid=np.isfinite(d_numeric)&d_numeric.gt(0)
    e['candidate_main_E0']=(e.candidate_base&c_valid).fillna(False).astype(bool)
    e['candidate_main_R0c']=(e.candidate_main_E0&d_valid).fillna(False).astype(bool)
    e['candidate_weather_E0']=e.candidate_main_E0&e.cause_group_event.eq('weather_natural')
    e['candidate_weather_R0c']=e.candidate_main_R0c&e.cause_group_event.eq('weather_natural')
    e['candidate_status']=np.select([e.candidate_base&e.weather_validation_tier.eq('v3_only_window_not_reverified'),e.candidate_base],['conditional_v3_provenance','eligible_input_candidate'],default='not_eligible')
    reasons=pd.Series('',index=e.index,dtype='string')
    for mask,label in [(~e.new_in_study_utc,'outside_UTC_study'),(e.event_identity_unresolved,'event_identity_unresolved'),(~e.cause_in_main,'cause_not_main_or_unresolved'),(~e.weather_numeric_available,'weather_numeric_unavailable'),(~e.region_numeric_complete,'regional_predictor_missing'),(~c_valid,'C_invalid_or_missing')]:
        reasons.loc[mask]+=label+';'
    e['E0_exclusion_reasons']=reasons.str.rstrip(';')
    rr=reasons.copy();rr.loc[~d_valid]+='D_invalid_or_missing;';e['R0c_exclusion_reasons']=rr.str.rstrip(';')
    e['weather_status_v3']=np.where(e.weather_numeric_available,'matched','R02_numeric_unavailable')
    e['weather_status_alias_note']='compatibility alias; see separate cache/value/product states'
    for s in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        e['strict_candidate_'+s]=e['candidate_'+s]&e.weather_validation_tier.eq('strict_cache_checked')
    return e

def load_active_events(manifest_path=None):
    """Actual active pipeline reader; verify the produced file before returning rows."""
    root=Path(__file__).resolve().parents[2]
    mp=Path(manifest_path) if manifest_path else root/'paper_revision_work_v2/R02/data/EVENT_MANIFEST.json'
    manifest=json.loads(mp.read_text(encoding='utf-8'));p=Path(manifest['event_table']['path'])
    with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=manifest['event_table']['sha256']:raise ValueError('R02 event table hash mismatch')
    e=pd.read_parquet(p)
    if len(e)!=manifest['event_count'] or not e[ID].is_unique:raise ValueError('Event table cardinality invalid')
    return e,manifest
