"""Versioned data producers for retained figures and descriptive period comparisons."""
import numpy as np
import pandas as pd
from contracts import *
from producer import ROOT,read,sha,require_result
from prediction import regional_reference,physical_gust_terms
from diagnostics import covariance_producer

def figure6_data(model_path,run_id,reference,all_events,allow_smoke=False):
    model=require_result(model_path,run_id,allow_smoke)
    manifest=read(ROOT/'frozen/REFERENCE_DATA_MANIFEST.json')
    source=next(x for x in manifest if x['original_path'].endswith('population_lad_long.csv'))
    if sha(source['frozen_path'])!=source['sha256']:raise ValueError('frozen population copy changed')
    p=pd.read_csv(source['frozen_path']).rename(columns={'LAD23CD':'LAD21CD','year':'new_year'})
    if p.duplicated(['LAD21CD','new_year']).any():raise ValueError('population duplicate keys')
    cols=['LAD21CD','urban_binary','income_deprivation_rate','deprivation_gap_pct','morans_i','regional_proxy_flag']
    regional=all_events[cols].dropna(subset=['LAD21CD']).drop_duplicates()
    if regional.LAD21CD.duplicated().any():raise ValueError('regional static fields inconsistent')
    grid=regional.merge(p[['LAD21CD','new_year','population']],on='LAD21CD',validate='one_to_many');grid['log_population']=np.log(grid.population.where(grid.population.gt(0)))
    cal=reference.groupby(['new_year','new_month']).size().rename('n').reset_index();cal['weight']=cal.n/cal.n.sum()
    result=regional_reference(grid,cal,model);result=result.merge(regional[['LAD21CD','regional_proxy_flag']],on='LAD21CD',validate='one_to_one')
    return result,{'source_run_id':run_id,'reference_population_sha256':identity(reference[ID]),'calendar_weights':cal.to_dict('records'),'scaler_sha256':config_hash(model['preprocessor']),'order':'physical weather/log-C center -> complete calendar designs -> weighted mean eta -> exp','population_copy_sha256':source['sha256'],'geography':'LAD21 static / same-code LAD23 population; explicit compatibility unresolved','map_geometry_rendering':'not performed in R03'}

def period_comparison(events,target_name,metadata,pressure_physical):
    rows=[];models=[]
    for period in ['development','later']:
        d=events.loc[events.new_period.eq(period)].copy()
        if not len(d):raise ValueError('empty period; no invented coefficients')
        prep=fit_preprocessor(d,target_name);block='G' if target_name=='E0' else 'GK'
        x=design(d,prep,block);rank=int(np.linalg.matrix_rank(x.to_numpy()))
        if rank<len(x.columns):
            rows.append({'period':period,'target':target_name,'n':len(d),'rank':rank,'columns':len(x.columns),'status':'blocked_calendar_design_rank_deficient','physical_linear_gust':None,'physical_quadratic_gust':None,'failure_reason':'additive year/month coding not full rank in this period; no silent term dropping or H0 fallback','nominal_independent_CV_interval':None})
            continue
        _,period_tail=training_population(d,'main',target_name,'all_valid')
        model=fit_ols(d,prep,block,dict(metadata,period=period,fit_type='period_full_sample_descriptive_all_valid',tail=period_tail))
        cov=covariance_producer(d,model);params=physical_gust_terms(model,pressure_physical)
        q=prep;s=q['sd']['gust_0h'];mu=q['mean']['gust_0h'];zp=(pressure_physical-q['mean']['pressure_msl_0h'])/q['sd']['pressure_msl_0h']
        jac=np.zeros((2,len(model['columns'])));ix={c:i for i,c in enumerate(model['columns'])}
        jac[0,ix['zG']]=1/s;jac[0,ix['zG2']]=-2*mu/s**2;jac[0,ix['zG_zPressure']]=zp/s;jac[1,ix['zG2']]=1/s**2
        physical_cov=jac@np.asarray(cov['LAD_CR1'])@jac.T
        rows.append({'period':period,'target':target_name,'n':len(d),'rank':model['rank'],'columns':len(model['columns']),'status':'descriptive_full_fit_available',**params,'physical_linear_SE':float(np.sqrt(physical_cov[0,0])) if physical_cov[0,0]>=0 else None,'physical_quadratic_SE':float(np.sqrt(physical_cov[1,1])) if physical_cov[1,1]>=0 else None,'reference_distribution':'not converted into a cross-period hypothesis test','nominal_independent_CV_interval':None})
        model['LAD_CR1_covariance']=cov['LAD_CR1'];model['physical_gust_covariance']=physical_cov.tolist();models.append(model)
    return pd.DataFrame(rows),models
