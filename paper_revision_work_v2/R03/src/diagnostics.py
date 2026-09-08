"""Reconstructed minimal diagnostic producers; old output values never consumed."""
import numpy as np
import pandas as pd
from contracts import *
def vif_table(x):
    a=x.to_numpy(dtype=float);n,k=a.shape;rank=int(np.linalg.matrix_rank(a));rows=[]
    for j,name in enumerate(x.columns):
        if name=='const':continue
        y=a[:,j];other=np.delete(a,j,axis=1);res=y-other@np.linalg.lstsq(other,y,rcond=None)[0];sst=float(np.sum((y-y.mean())**2));sse=float(res@res)
        val=None if sst==0 or sse<=1e-14*max(sst,1) else sst/sse
        rows.append({'term':name,'VIF':val,'status':'undefined_constant_or_collinear' if val is None else 'defined'})
    return pd.DataFrame(rows),{'producer':'reconstructed_step26_VIF','n':n,'columns':list(x.columns),'design_rank':rank,'k':k,'intercept_in_auxiliary_regressions':True,'intercept_VIF_reported':False,'year_month_dummies_and_square_interaction_included':True,'all_VIF_below4_required':False}
def cluster_covariance(x,residuals,groups):
    a=x.to_numpy(dtype=float);n,k=a.shape;g=pd.Series(groups).astype(str).to_numpy();unique,inv=np.unique(g,return_inverse=True);ng=len(unique)
    if ng<2 or n<=k:raise ValueError('insufficient clusters/residual df')
    scores=np.zeros((ng,k));np.add.at(scores,inv,a*np.asarray(residuals)[:,None]);bread=np.linalg.pinv(a.T@a);correction=ng/(ng-1)*(n-1)/(n-k)
    return correction*bread@(scores.T@scores)@bread
def covariance_producer(train,model):
    x=design(train,model['preprocessor'],model['block']);res=target(train,model['target'])-predict_eta(train,model)
    lad=train.LAD21CD.astype(str);date=train.new_date_utc.astype(str);intersection=lad+'|'+date
    cl=cluster_covariance(x,res,lad);cd=cluster_covariance(x,res,date);ci=cluster_covariance(x,res,intersection);tw=cl+cd-ci
    return {'producer':'reconstructed_step28','columns':list(x.columns),'LAD_CR1':cl.tolist(),'date_CR1':cd.tolist(),'LAD_date_two_way_CR1':tw.tolist(),'two_way_min_eigenvalue':float(np.linalg.eigvalsh(tw).min()),'negative_diagonal':bool((np.diag(tw)<0).any()),'negative_variance_policy':'retain diagnostic flag; no imaginary SE/nominal interval','correction':'each one-way G/(G-1)*(n-1)/(n-k); intersection inclusion-exclusion','LAD_fixed_effects':False,'reference_distribution_for_intervals':'not automatically inferred from CV; formal interval contract recorded separately'}
def stage_composition(events):
    d=events.copy();x=d[C].to_numpy(dtype=float);edges=np.unique(np.quantile(x,[0,.25,.5,.75,1],method='linear'))
    if len(edges)<2:raise ValueError('insufficient customer support')
    d['customer_bin']=pd.cut(d[C].astype(float),edges,include_lowest=True,duplicates='drop').astype(str)
    stage=d.stage_row_count
    if stage.isna().any() or stage.le(0).any():raise ValueError('invalid stage count')
    d['stage_group']=np.select([stage.eq(1),stage.eq(2),stage.between(3,4)],['1','2','3-4'],default='5+')
    table=d.groupby(['stage_group','customer_bin'],observed=True)[D].agg(['count','mean','median']).reset_index()
    pooled=d.groupby('customer_bin',observed=True)[D].agg(['count','mean','median']).reset_index()
    return table,pooled,{'producer':'reconstructed_stage_composition_using_frozen_step42_definition','n':len(d),'event_ids_sha256':identity(d[ID]),'shared_customer_bin_edges':edges.tolist(),'duplicate_quantile_edges':'collapsed and recorded','stage_source':'R02 full-stage stage_row_count','step27_full_original_table':'not claimed reproduced; subgroup-specific historical bins require separate identity'}
def stage_closure(events,metadata):
    """Step27 diagnostic recovered from step5 definitions; explicitly uses current membership."""
    import copy
    prep=fit_preprocessor(events,'R0c');aug=copy.deepcopy(prep);aug['extra_raw_columns']=['log_n_stages']
    plain=fit_ols(events,prep,'GK',dict(metadata,diagnostic='without_stage_control'))
    controlled=fit_ols(events,aug,'GK',dict(metadata,diagnostic='raw_log_stage_control'))
    models=[plain,controlled];rows=[]
    for model in models:
        x=design(events,model['preprocessor'],'GK');res=target(events,'R0c')-predict_eta(events,model);cov=cluster_covariance(x,res,events.LAD21CD)
        for term in ['zG','zG2','zK','zK2','log_n_stages']:
            if term not in model['columns']:continue
            j=model['columns'].index(term);rows.append({'spec':model['metadata']['diagnostic'],'term':term,'coefficient':model['parameters'][j],'LAD_CR1_SE':float(np.sqrt(cov[j,j])) if cov[j,j]>=0 else None,'same_population_sha256':identity(events[ID]),'n':len(events)})
    single=events.loc[events.stage_row_count.eq(1)];bins=None
    if len(single):
        groups=pd.qcut(single[C].astype(float),4,duplicates='drop');bins=single.groupby(groups,observed=True)[D].agg(['count','mean','median']).reset_index();bins[bins.columns[0]]=bins.iloc[:,0].astype(str)
    return pd.DataFrame(rows),models,bins,{'producer':'reconstructed_step27','source_definition':'frozen customers_duration_shape_investigation/step5_n_stages_stratification.py plus archived 27 report','historical_weather_n9806_reused':False,'current_membership_sha256':identity(events[ID]),'stage_transform':'natural log raw; not standardized','single_stage_bins':'within-single-stage quartiles, duplicate edges collapsed','new_mechanism_claim':False}
