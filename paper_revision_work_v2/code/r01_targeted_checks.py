"""R01 source checks only. No model fitting or production event-table repair."""
import sys,json,hashlib,re,datetime
from pathlib import Path
sys.dont_write_bytecode=True
import pandas as pd
import numpy as np
import openpyxl
O=Path(__file__).resolve().parents[1];R=O.parent;P=R.parent;A=R/'results/code_audit_20260905'
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def save(n,x):(O/'checks'/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def csv(n,x):x.to_csv(O/'checks'/n,index=False,encoding='utf-8-sig')
raw=pd.read_csv(P/'data/ukpn-iis.csv',dtype=str,keep_default_na=False)
raw['source_row_number']=np.arange(1,len(raw)+1)
raw['start_utc']=pd.to_datetime(raw['Start Date and Time'],utc=True,format='mixed',errors='coerce')
raw['end_utc']=pd.to_datetime(raw['End Date and Time'],utc=True,format='mixed',errors='coerce')
ID='Incident Reference';g=raw.groupby(ID,sort=False)
minimum=g.start_utc.transform('min');ties=raw.loc[raw.start_utc.eq(minimum)]
tc=ties.groupby(ID).size();tg=ties.groupby(ID)
meta=['Spatial Coordinates','Cause Code','licence_area','regulatory_year','substation','SiteFunctionalLocation']
conf=tg[meta].nunique(dropna=False);conf=conf.loc[tc.gt(1)]
csv('earliest_tie_metadata_conflicts.csv',conf.reset_index())
conf_ids=g['Cause Code'].nunique().loc[lambda s:s>1].index
csv('cause_conflict_stage_rows.csv',raw.loc[raw[ID].isin(conf_ids)])
rep=pd.read_csv(A/'main_E0_representative_row_audit.csv')
eid=rep.loc[rep.lag_hours.idxmax(),ID]
ext=raw.loc[raw[ID].eq(eid)].sort_values(['start_utc','source_row_number']);csv('extreme_4506h_timeline.csv',ext)
stats={'raw_rows':len(raw),'incidents':g.ngroups,'unique_identifier_missing':int(raw.unique_identifier.eq('').sum()),'unique_identifier_duplicate_rows':int(raw.unique_identifier.duplicated(keep=False).sum()),'exact_raw_duplicate_rows':int(raw.drop(columns=['source_row_number','start_utc','end_utc']).duplicated(keep=False).sum()),'time_offset_counts':raw['Start Date and Time'].str.extract(r'(Z|[+-]\d\d:\d\d)$')[0].fillna('none').value_counts().to_dict(),'invalid_start_rows':int(raw.start_utc.isna().sum()),'invalid_end_rows':int(raw.end_utc.isna().sum()),'end_before_start_rows':int(raw.end_utc.lt(raw.start_utc).sum()),'earliest_tied_incidents':int(tc.gt(1).sum()),'earliest_tie_conflicts':conf.gt(1).sum().to_dict(),'cause_conflict_ids':list(conf_ids),'extreme_id':eid,'extreme_old_rep':rep.loc[rep[ID].eq(eid)].to_dict('records'),'extreme_stage_count':len(ext),'extreme_min_start':str(ext.start_utc.min()),'extreme_max_end':str(ext.end_utc.max()),'extreme_duration_B':(ext.end_utc.max()-ext.start_utc.min()).total_seconds()/3600,'extreme_C_nonrepeat':pd.to_numeric(ext.loc[~ext['Re-interruption Stage'].str.upper().isin(['Y','1']),'Number of Customers Restored']).sum(min_count=1),'extreme_metadata_unique':{c:ext[c].unique().tolist() for c in meta},'global_earliest':str(raw.start_utc.min()),'global_latest_start':str(raw.start_utc.max()),'global_latest_end':str(raw.end_utc.max())}
span=g.agg(first=('start_utc','min'),last_start=('start_utc','max'),last_end=('end_utc','max'))
for boundary in ['2021-04-01','2023-04-01','2024-04-01']:
    b=pd.Timestamp(boundary,tz='UTC');stats['boundary_'+boundary]={'start_before_and_end_after':int((span['first'].lt(b)&span.last_end.ge(b)).sum()),'stage_starts_both_sides':int((span['first'].lt(b)&span.last_start.ge(b)).sum())}
stats['reinterruption_values']=raw['Re-interruption Stage'].value_counts().to_dict()
stats['negative_customer_rows']=int(pd.to_numeric(raw['Number of Customers Restored'],errors='coerce').lt(0).sum())
save('event_semantic_checks.json',stats)
print('EVENT',json.dumps(stats,default=str,ensure_ascii=False),flush=True)
# Read selected v3 columns once; all model members already audited in H0.
vc=pd.read_csv(P/'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv',nrows=0).columns
cols=[ID,'source_row_number','LAD21CD','population','income_deprivation_rate','deprivation_gap_pct','morans_i','rural_urban_classification','cause_group_official','lat','lon','request_key','clean_start','gust_0h','precipitation_24h_sum','weather_status_v3']
v=pd.read_csv(P/'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv',usecols=[c for c in cols if c in vc],low_memory=False)
csv('cause_conflict_v3_rows.csv',v.loc[v[ID].isin(conf_ids)])
sel=v.drop_duplicates(ID)
members={s:set(pd.read_csv(A/f'{s}_sample_membership.csv',usecols=[ID])[ID]) for s in ['main_E0','main_R0c','weather_E0','weather_R0c']}
buck={'all_incidents':int(sel.LAD21CD.eq('E06000060').sum()),'H0_sample_incidents':{s:int(sel.loc[sel[ID].isin(ids),'LAD21CD'].eq('E06000060').sum()) for s,ids in members.items()},'values':sel.loc[sel.LAD21CD.eq('E06000060'),['income_deprivation_rate','deprivation_gap_pct','morans_i','rural_urban_classification']].drop_duplicates().to_dict('records')}
# Inspect workbook values and cell formats, preserving files.
wp=P/'data/localincomedeprivationdata.xlsx';w=openpyxl.load_workbook(wp,read_only=True,data_only=True)
notes={}
for sn in w.sheetnames:
    ws=w[sn]
    if sn in ['Notes','Contents','Profiles']:
        notes[sn]=[[str(x) for x in row if x is not None] for row in ws.iter_rows(values_only=True)]
    elif sn in ['Rankings for all indicators','Local authorities']:
        notes[sn+'_head']=list(ws.iter_rows(min_row=1,max_row=5,values_only=True))
ws=w['Rankings for all indicators'];rows=list(ws.iter_rows(values_only=True));header=list(rows[1]);imd=pd.DataFrame(rows[2:],columns=header)
oldcodes=['E07000004','E07000005','E07000006','E07000007']
codecol='Local Authority District code (2019)'
imd=imd.loc[imd[codecol].notna()]
metric=['Deprivation gap (percentage points)',"Moran's I",'Income deprivation rate']
old=imd.loc[imd[codecol].isin(oldcodes),[codecol]+metric];csv('buckinghamshire_original_indicators.csv',old)
pop=pd.read_csv(P/'data/population_lad_long.csv',low_memory=False)
oldpop=pop.loc[pop.LAD23CD.isin(oldcodes)&pop.year.eq(2021),['LAD23CD','year','population']]
csv('buckinghamshire_weight_availability.csv',oldpop)
buck.update(oldcode_2021_population_rows=len(oldpop),arithmetic_mean={c:float(pd.to_numeric(old[c]).mean()) for c in metric},source_workbook_sha256=sha(wp),workbook_sample_cell_formats={f'{cell.coordinate}':{'value':cell.value,'format':cell.number_format} for row in ws.iter_rows(min_row=3,max_row=3) for cell in row if hasattr(cell,'coordinate')})
save('workbook_source_evidence.json',notes);save('buckinghamshire_lineage.json',buck);w.close()
# Other workbook title/notes only; direct source producer scripts are read separately.
others={}
for name in ['myebtablesuk20112024.xlsx','regionalgvabbylainuk.xlsx']:
    p=P/'data'/name;wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
    others[name]={'sha256':sha(p),'sheets':wb.sheetnames,'first_sheet_top':list(wb.worksheets[0].iter_rows(max_row=25,values_only=True))};wb.close()
save('other_workbook_sources.json',others)
print('BUCK',json.dumps(buck,default=str,ensure_ascii=False),flush=True)
# Deterministic case-based weather checks: extreme timeline, cause conflicts, maximal H0 gust,
# first H0 source, and nearest available recorded timestamps to UK DST transition instants.
ids={eid,*conf_ids};chosen=set(v.loc[v[ID].isin(ids),'source_row_number'].astype(int))
chosen.add(int(v.loc[v.gust_0h.idxmax(),'source_row_number']));chosen.add(1)
for t in ['2021-03-28T01:00Z','2021-10-31T01:00Z','2022-03-27T01:00Z','2022-10-30T01:00Z','2023-03-26T01:00Z','2023-10-29T01:00Z','2024-03-31T01:00Z']:
    delta=(raw.start_utc-pd.Timestamp(t)).abs();chosen.update(raw.loc[delta.nsmallest(2).index,'source_row_number'].astype(int))
wr=[];cache_hashes={}
for _,row in v.loc[v.source_row_number.isin(chosen)].iterrows():
    sr=raw.loc[raw.source_row_number.eq(row.source_row_number)].iloc[0];t=sr.start_utc.floor('h');key=row.get('request_key');cp=P/'data/weather_request_cache'/f'{key}.pkl'
    rec={'source_row_number':int(row.source_row_number),ID:row[ID],'source_start':sr['Start Date and Time'],'utc':str(sr.start_utc),'floor_hour_utc':str(t),'request_key':key,'cached':cp.exists(),'v3_gust':row.gust_0h,'v3_precipitation24':row.precipitation_24h_sum}
    if cp.exists():
        cache_hashes[str(cp)]=sha(cp)
        h=pd.read_pickle(cp);ht=pd.to_datetime(h.time_utc,utc=True)
        win=h.loc[ht.gt(t-pd.Timedelta(hours=24))&ht.le(t)]
        valid=pd.to_numeric(win.precipitation,errors='coerce')
        rec.update(cache_rows=len(h),cache_columns=list(h.columns),cache_attrs=h.attrs,exact_hour_rows=int(ht.eq(t).sum()),rain_window_rows=len(win),rain_valid_values=int(np.isfinite(valid).sum()),rain_nonnegative_values=int(valid.ge(0).sum()),rain_strict_sum=float(valid.sum(min_count=24)),rain_legacy_sum=float(valid.sum()),cache_gust_at_hour=h.loc[ht.eq(t),'wind_gusts_10m'].tolist(),cache_duplicate_times=int(ht.duplicated().sum()))
    wr.append(rec)
save('weather_case_checks.json',wr);save('weather_cache_read_hashes.json',cache_hashes)
print('WEATHER',json.dumps({'cases':len(wr),'cache_files':len(cache_hashes),'missing':sum(not x['cached'] for x in wr),'incomplete_precip':sum(x.get('rain_valid_values',24)!=24 for x in wr),'attrs':[x.get('cache_attrs') for x in wr if x.get('cache_attrs')]},default=str),flush=True)
