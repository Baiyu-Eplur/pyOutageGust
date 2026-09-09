"""Quantify audit findings without changing inputs, models or manuscripts."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

import re
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_pipeline as a
import ast
import json
import numpy as np
import pandas as pd
from scipy import stats


def main():
    cols=[a.ID,'Start Date and Time','End Date and Time','Restoration Stage','Cause Code','Number of Customers Restored','Re-interruption Stage','source_row_number','clean_start','wx_time_used_utc','gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h','lat','lon','LAD21CD','population','income_deprivation_rate','deprivation_gap_pct','morans_i','rural_urban_classification',a.C,a.D,'weather_status_v3','cause_group_official','incident_date_utc']
    print('Tracing representative row, weather and storm calculations',flush=True)
    stages=pd.read_csv(read_input(a.SRC),usecols=cols,low_memory=False)
    stages['_start']=pd.to_datetime(stages['Start Date and Time'],utc=True,errors='coerce')
    first=stages.drop_duplicates(a.ID).set_index(a.ID)
    min_idx=stages.groupby(a.ID)['_start'].idxmin().dropna().astype(int)
    earliest=stages.loc[min_idx].set_index(a.ID).reindex(first.index)
    detail=pd.DataFrame(index=first.index)
    detail['source_row_used']=first['source_row_number'];detail['earliest_source_row']=earliest['source_row_number']
    detail['time_used']=first['_start'];detail['earliest_recorded_start']=earliest['_start']
    detail['lag_hours']=(first['_start']-earliest['_start']).dt.total_seconds()/3600
    detail['hour_diff']=(first['_start'].dt.floor('h')!=earliest['_start'].dt.floor('h'))
    detail['date_diff']=(first['_start'].dt.floor('D')!=earliest['_start'].dt.floor('D'))
    for c in a.WEATHER:
        detail[c+'_used']=first[c];detail[c+'_earliest']=earliest[c];detail[c+'_delta']=first[c]-earliest[c]
    detail['earliest_weather_status']=earliest['weather_status_v3']
    detail['coordinate_diff']=first['lat'].ne(earliest['lat'])|first['lon'].ne(earliest['lon'])
    detail['lad_diff']=first['LAD21CD'].ne(earliest['LAD21CD'])
    detail['current_date']=first['incident_date_utc']
    detail['temporal_partition_change']=(first['_start']>=pd.Timestamp('2023-09-30',tz='UTC'))!=(earliest['_start']>=pd.Timestamp('2023-09-30',tz='UTC'))
    rows=[]
    for label in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        membership=pd.read_csv(read_input(a.OUT/f'{label}_sample_membership.csv'))
        d=detail.loc[membership[a.ID]]
        changed=d[d['lag_hours'].ne(0)]
        comparable=d['gust_0h_earliest'].notna() & d['gust_0h_used'].notna()
        delta=d.loc[comparable,'gust_0h_delta']
        rows.append({'sample':label,'n':len(d),'later_stage_start':len(changed),'later_stage_start_pct':100*len(changed)/len(d),'different_hour':int(d['hour_diff'].sum()),'different_date':int(d['date_diff'].sum()),'partition_changes':int(d['temporal_partition_change'].sum()),'lag_changed_median_hours':float(changed['lag_hours'].median()),'lag_changed_max_hours':float(changed['lag_hours'].max()),'earliest_gust_available':int(comparable.sum()),'gust_diff_over_1e_8':int(delta.abs().gt(1e-8).sum()),'gust_diff_over_1ms':int(delta.abs().gt(1).sum()),'gust_diff_over_5ms':int(delta.abs().gt(5).sum()),'max_abs_gust_difference':float(delta.abs().max()),'different_coordinates':int(d['coordinate_diff'].sum()),'different_LAD':int(d['lad_diff'].sum())})
        d.reset_index().to_csv(a.OUT/f'{label}_representative_row_audit.csv',index=False)
    pd.DataFrame(rows).to_csv(a.OUT/'representative_row_summary.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)

    # Reconstruct fitted log outcomes from archived coefficients. No model changes.
    env={'np':np,'pd':pd,'SCALE_COLS':a.WEATHER}
    a.load_pure(a.ROOT/'scripts/v3_validation/v3_validation_pipeline.py',['design_train_valid'],env)
    design=env['design_train_valid']
    def prep(d):
        d=d.copy();d['incident_date_utc']=pd.to_datetime(d['incident_date_utc'])
        urban=d['rural_urban_classification'].astype('string').str.lower()
        d['urban_binary']=np.where(urban.str.contains('urban',na=False),1.,np.where(urban.notna(),0.,np.nan))
        d['log_population']=np.log(d['population'].where(d['population']>0))
        d['incident_year']=d['incident_date_utc'].dt.year;d['incident_month']=d['incident_date_utc'].dt.month
        d['customers_v2_log1p']=np.log1p(d[a.C])
        return d
    coefs=a.ROOT/'results/final_combined_analysis/raw'
    storm_tree=ast.parse((read_input(a.ROOT/'scripts/final_combined_analysis/step13_storm_prediction_check.py')).read_text(encoding='utf-8'))
    storms=next(ast.literal_eval(n.value) for n in storm_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STORMS' for t in n.targets))
    m_e=pd.read_csv(read_input(a.OUT/'main_E0_sample_membership.csv'));m_r=pd.read_csv(read_input(a.OUT/'main_R0c_sample_membership.csv'))
    e=prep(first.loc[m_e[a.ID]]).reset_index();r=prep(first.loc[m_r[a.ID]]).reset_index()
    Xe,_=design(e,e);bet=pd.read_csv(read_input(coefs/'step1_E0_final_full_coefs.csv')).set_index('term')['coefficient']
    eta=(Xe@bet).to_numpy();old_eta=np.logaddexp(0,eta);y=np.log1p(e[a.C]).to_numpy()
    exposure_rows=[];storm_tail=[]
    for storm,interval in [('FULL_SAMPLE',None)]+list(storms.items()):
        mask=np.ones(len(e),dtype=bool) if interval is None else e['incident_date_utc'].between(*interval).to_numpy()
        exposure_rows.append({'storm':storm,'n':int(mask.sum()),'old_corr_log1p_exp_eta':float(stats.pearsonr(old_eta[mask],y[mask]).statistic),'corr_eta':float(stats.pearsonr(eta[mask],y[mask]).statistic),'old_mae_log':float(np.mean(np.abs(old_eta[mask]-y[mask]))),'mae_eta':float(np.mean(np.abs(eta[mask]-y[mask]))),'mean_extra_log_shift':float(np.mean(old_eta[mask]-eta[mask]))})
        if interval:
            es=e.loc[mask & e[a.D].gt(0).to_numpy()]
            fit_ids=set(r[a.ID]);tail=es[~es[a.ID].isin(fit_ids)]
            storm_tail.append({'storm':storm,'start':interval[0],'end':interval[1],'recovery_evaluation_n':len(es),'recovery_fit_member_n':int(es[a.ID].isin(fit_ids).sum()),'not_in_recovery_fit_n':len(tail),'max_duration_hours':float(es[a.D].max())})
    pd.DataFrame(exposure_rows).to_csv(a.OUT/'storm_exposure_scale_audit.csv',index=False)
    pd.DataFrame(storm_tail).to_csv(a.OUT/'storm_recovery_membership_audit.csv',index=False)
    # Compare the two explicit reference settings of the recovery gust curve and map.
    Xr,_=design(r,r,extra_scale_cols=['customers_v2_log1p'])
    br=pd.read_csv(read_input(coefs/'step1_R0c_final_full_coefs.csv')).set_index('term')['coefficient']
    mean_square=float(Xr['z_log1p_customers_v2_sq'].mean())
    a.write_json('curve_reference_audit.json',{'curve_customer_linear':float(Xr['z_log1p_customers_v2'].mean()),'curve_customer_square':mean_square,'map_customer_linear':0.,'map_customer_square':0.,'curve_vs_customer_at_z0_multiplicative_factor':float(np.exp(br['z_log1p_customers_v2_sq']*mean_square)),'interpretation':'Curve fixes mean design-matrix columns (mean square ~1); map explicitly fixes customer z and z squared to 0. This changes levels, not the gust grid max/min ratio.'})
    # Full command history index from LOG, retaining retrospective status labels.
    log=(read_input(a.ROOT/'LOG.md')).read_text(encoding='utf-8')
    sections=re.split(r'(?m)^## ',log)[1:]
    timeline=[]
    for section in sections:
        title=section.splitlines()[0]
        match=re.search(r'#(\d+)',title)
        if match:
            timeline.append({'command':int(match.group(1)),'historical_title':title,'log_line':log[:log.index('## '+title)].count('\n')+1,'script_mentions':'; '.join(sorted(set(re.findall(r'[\w\-/\\.]+\.py',section)))),'source':'LOG.md','status':'Historical record; not a current certification'})
    pd.DataFrame(timeline).to_csv(a.OUT/'command_history_index.csv',index=False,encoding='utf-8-sig')
    # Same-named report duplicates are indexed, not presumed interchangeable.
    byname={}
    for p in (a.ROOT/'results').rglob('*.md'):
        if a.OUT in p.parents:continue
        byname.setdefault(p.name,[]).append(p)
    duplicate=[]
    for name,paths in byname.items():
        if len(paths)>1:
            hashes=[a.sha(p) for p in paths]
            for p,h in zip(paths,hashes):duplicate.append({'filename':name,'path':str(p),'sha256':h,'all_copies_identical':len(set(hashes))==1})
    pd.DataFrame(duplicate).to_csv(a.OUT/'duplicate_report_index.csv',index=False,encoding='utf-8-sig')
    original=json.loads((read_input(a.OUT/'historical_files_before.json')).read_text(encoding='utf-8'))
    a.write_json('historical_preservation_check_after_trace.json',{'watched_files':len(original),'changed_files':[p for p,h in original.items() if not Path(p).exists() or a.sha(Path(p))!=h]})
    print('Focused tracing complete',flush=True)


if __name__=='__main__':main()
