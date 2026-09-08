"""Scale, reference-population, and storm identities shared by all consumers."""
import numpy as np
import pandas as pd
from contracts import *
from producer import require_result

def aggregate_eta(eta,weights=None):
    a=np.asarray(eta,dtype=float);w=np.ones(len(a)) if weights is None else np.asarray(weights,dtype=float)
    if not len(a) or not np.isfinite(a).all() or len(w)!=len(a) or not np.isfinite(w).all() or (w<0).any() or w.sum()<=0:raise ValueError('invalid reference weights/prediction')
    mean=float(np.average(a,weights=w))
    return {'mean_eta':mean,'exp_mean_eta':float(np.exp(mean)),'mean_exp_eta':float(np.average(np.exp(a),weights=w)),'interpretation':'exponentiated fitted log response; no conditional arithmetic-mean/smearing claim'}
def set_scenario(reference,model,settings):
    d=reference.copy()
    for col,val in settings.items():
        if col=='customers_at_training_log_center':d[C]=np.expm1(model['preprocessor']['mean']['log1p_customers'])
        elif col in WX+[C]:d[col]=val
        else:raise ValueError('scenario requires declared raw variable')
    return d
def reference_curve(reference,model,driver,grid,fixed_pressure=None):
    if driver not in ['gust_0h',C]:raise ValueError('unsupported curve driver')
    prep=model['preprocessor'];rows=[]
    for value in grid:
        settings={driver:float(value),'pressure_msl_0h':prep['mean']['pressure_msl_0h'] if fixed_pressure is None else fixed_pressure}
        if driver==C:settings['gust_0h']=prep['mean']['gust_0h']
        d=set_scenario(reference,model,settings);a=aggregate_eta(predict_eta(d,model))
        rows.append({'raw_driver':driver,'value':float(value),'n_reference':len(d),**a})
    return pd.DataFrame(rows),{'source_run_id':model['metadata']['run_id'],'purpose':model['metadata'].get('purpose'),'target_scale':model['target_scale'],'design_columns':model['columns'],'reference_population_sha256':identity(reference[ID]),'model_training_ids_sha256':prep['training_ids_sha256'],'scaler_sha256':config_hash(prep),'pressure_physical':prep['mean']['pressure_msl_0h'] if fixed_pressure is None else fixed_pressure,'driver':driver,'grid':list(map(float,grid)),'raw_settings':'each row retains regional/calendar covariates; fixed driver, pressure; customer curve fixed gust','reference_order':'set raw -> design squares/interactions -> predict each eta -> aggregate','display':'exp_mean_eta','minimum_CI':None,'no_old_interval_fallback':True}
def minimum_interface(model,pressure_physical,support):
    p=dict(zip(model['columns'],model['parameters']));prep=model['preprocessor']
    b1=p.get('zG');b2=p.get('zG2');b3=p.get('zG_zPressure');mu=prep['mean']['gust_0h'];sd=prep['sd']['gust_0h']
    out={'beta1':b1,'beta2':b2,'beta3_interaction':b3,'gust_mean':mu,'gust_sd':sd,'pressure_physical':pressure_physical,'pressure_mean':prep['mean']['pressure_msl_0h'],'pressure_sd':prep['sd']['pressure_msl_0h'],'support_ms':list(map(float,support)),'status':'unavailable','minimum_ms':None,'interval':None,'interval_status':'not_estimated_do_not_draw'}
    if any(x is None for x in [b1,b2,b3]):out['failure_reason']='required gust terms missing';return out
    if b2<=1e-12:out['failure_reason']='nonpositive_or_near_zero_curvature';return out
    zp=(pressure_physical-prep['mean']['pressure_msl_0h'])/prep['sd']['pressure_msl_0h'];v=mu-sd*(b1+b3*zp)/(2*b2)
    out['curvature_physical']=2*b2/sd**2;out['algebraic_vertex_ms']=float(v)
    if not np.isfinite(v) or not support[0]<=v<=support[1]:out['failure_reason']='outside_declared_support';return out
    out.update(status='conditional_fitted_minimum',minimum_ms=float(v),failure_reason=None);return out
def regional_reference(regional_year,calendar,model):
    """New figure 6 table: raw weather/K center and common calendar, no mean-square shortcut."""
    prep=model['preprocessor'];result=[]
    if regional_year.duplicated(['LAD21CD','new_year']).any():raise ValueError('duplicate regional-year keys')
    if calendar.duplicated(['new_year','new_month']).any():raise ValueError('duplicate reference calendar keys')
    for lad,g in regional_year.groupby('LAD21CD'):
        d=calendar.merge(g,on='new_year',how='left',validate='many_to_one')
        if d[REGION].isna().any(axis=None):result.append({'LAD21CD':lad,'status':'missing_region_year_no_fill'});continue
        d[ID]=[f'{lad}:calendar:{i}' for i in range(len(d))]
        for c in WX:d[c]=prep['mean'][c]
        if model['target']=='R0c':d[C]=np.expm1(prep['mean']['log1p_customers'])
        x=design(d,prep,model['block'])
        if model['target']=='R0c' and 'zK' in x:
            if not np.allclose(x.zK,0,atol=1e-12) or not np.allclose(x.zK2,0,atol=1e-20):raise ValueError('customer reference not at training log center')
        result.append({'LAD21CD':lad,'status':'descriptive_common_calendar',**aggregate_eta(predict_eta(d,model),d.weight)})
    return pd.DataFrame(result)
def storm_event_predictions(events,model,windows,prediction_source='full_sample_descriptive',oof=None,oof_models=None):
    masks={name:events.new_time_utc.ge(pd.Timestamp(win['start']))&events.new_time_utc.lt(pd.Timestamp(win['end_exclusive'])) for name,win in windows.items()}
    mask=pd.DataFrame(masks,index=events.index);d=events.loc[mask.any(axis=1)].copy()
    if not d[ID].is_unique:raise ValueError('storm union duplicated')
    d['window_list']=[';'.join(mask.columns[mask.loc[i]].tolist()) for i in d.index];d['window_count']=mask.sum(axis=1).loc[d.index]
    d['was_in_this_fit']=d[ID].isin(model['training_ids']);tail=model['metadata'].get('tail',{})
    cap=tail.get('threshold_hours');d['tail_excluded_from_fit']=False if cap is None else d[D].gt(cap)
    d['model_fold']=-1;d['training_threshold_hours']=cap;d['model_training_tail_policy']=tail.get('tail_policy','not_provided');d['fit_model_key']='full_model'
    if prediction_source=='full_sample_descriptive':d['prediction_eta']=predict_eta(d,model)
    elif prediction_source=='OOF_date_group_diagnostic':
        if oof is None or not oof[ID].is_unique or oof_models is None:raise ValueError('missing/duplicate storm OOF or corresponding fold archives')
        d['prediction_eta']=d[ID].map(oof.set_index(ID).prediction_eta)
        if d.prediction_eta.isna().any():raise ValueError('incomplete storm OOF')
        d['was_in_this_fit']=False # each row's corresponding fold fit excludes its date
        d['tail_excluded_from_fit']=False # test tails are retained regardless of D
        d['model_fold']=d[ID].map(oof.set_index(ID).fold)
        for f,g in d.groupby('model_fold'):
            fm=oof_models[int(f)];ft=fm['metadata']['tail']
            if set(g[ID])&set(fm['training_ids']) or set(g.new_date_utc)&set(fm['training_dates']):raise ValueError('storm OOF archive leakage')
            d.loc[g.index,'training_threshold_hours']=ft['threshold_hours'];d.loc[g.index,'model_training_tail_policy']=ft['tail_policy'];d.loc[g.index,'fit_model_key']=f"model_fold{int(f)}_{fm['block']}"
    else:raise ValueError('true holdout protocol not implemented in R03; do not relabel')
    d['prediction_source']=prediction_source;d['target_scale']=model['target_scale'];d['y']=target(d,model['target']);d['squared_error_log']=(d.y-d.prediction_eta)**2
    for key in ['run_id','purpose','input_version']:d[key]=model['metadata'].get(key)
    return d[[ID,'run_id','purpose','input_version','window_list','window_count','was_in_this_fit','tail_excluded_from_fit','model_fold','fit_model_key','model_training_tail_policy','training_threshold_hours','prediction_source','target_scale','y','prediction_eta','squared_error_log']]
def figure4_data(model_file,run_id,reference,grid,allow_smoke=False):
    m=require_result(model_file,run_id,allow_smoke);return reference_curve(reference,m,'gust_0h',grid)
def figure7_data(model_file,run_id,reference,driver,grid,allow_smoke=False):
    m=require_result(model_file,run_id,allow_smoke);curve,meta=reference_curve(reference,m,driver,grid)
    meta['exponentiated_grid_max_min_ratio']=float(np.exp(curve.mean_eta.max()-curve.mean_eta.min()));return curve,meta
def physical_gust_terms(model,pressure):
    p=dict(zip(model['columns'],model['parameters']));q=model['preprocessor'];s=q['sd']['gust_0h'];mu=q['mean']['gust_0h'];zp=(pressure-q['mean']['pressure_msl_0h'])/q['sd']['pressure_msl_0h']
    return {'physical_linear_gust':(p['zG']+p['zG_zPressure']*zp)/s-2*p['zG2']*mu/s**2,'physical_quadratic_gust':p['zG2']/s**2,'pressure_physical':pressure,'source':'single full fit and its own scaler','cross_period_independence_assumed':False,'CV_inverse_variance_interval':None}
