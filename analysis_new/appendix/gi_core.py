"""APP-GI-PRED: pure adapters and a shared incident prediction store.

Only the explicitly needed fixed production models are evaluated. No knot
search is called; C's train-selected family results retain their own identity.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from . import c_models as cm
from .catalog import ROOT, MAIN
from .f02_cov import build_function, covariance_from_residuals, csv, read, js, token
from .mapping import write_json, digest

ID=cm.ID
C=cm.C
D='duration_B_full_span_hours'
BINS=[0,4,6,8,10,12,14,16,18,20,23,26,30,45]
WEATHER=build_function()
KNOTS=js(ROOT/MAIN/'model_selection/knots.json')
WS=js(ROOT/MAIN/'weather_only/weather_only_summary.json')
FS=js(ROOT/MAIN/'final_models/final_summary.json')
FINAL_C={'E0_all':'F08','R0c_all':'F01','E0_weather':'F08','R0c_weather':'F06'}

def knots(combo,spec):
    margin,scope=combo.split('_',1)
    if scope=='weather':return WS[margin]['knots']['selected'] if spec in ['final','hinge'] else []
    if spec=='legacy_hinge':return KNOTS[margin].get('unconstrained_selected',KNOTS[margin]['selected'])
    return KNOTS[margin]['selected'] if spec=='final' and margin=='E0' else []

def design(tr,va,combo,spec):
    margin,scope=combo.split('_',1);cust=margin=='R0c'
    if spec=='final':
        return WEATHER(tr,va,margin,cust,spec,knots(combo,spec)) if scope=='weather' else cm.FINAL(tr,va,margin,cust)
    if spec=='hinge':return WEATHER(tr,va,margin,cust,spec,knots(combo,spec))
    s={'paper':'M5_+year_month_FE','control':'M5_+year_month_FE','cubic':'A1_gust_cubic','log':'A2_log_gust','legacy_hinge':'M5_+year_month_FE'}[spec]
    a,b=cm.DESIGN(tr,va,s,cust)
    for x,d in [(a,tr),(b,va)]:
        if spec=='control':x.drop(columns=[c for c in x if 'gust' in c],inplace=True)
        if spec=='legacy_hinge':
            x.drop(columns='z_gust_sq',inplace=True)
            for k in knots(combo,spec):x[f'hinge_{k:g}']=np.maximum(d.gust_0h-k,0.)
    return a,b

def model_list(combo):
    return ['final','paper','control','hinge'] if combo.endswith('weather') else ['final','paper','control','cubic','log','legacy_hinge']

def c_dir(combo,spec):
    mid=FINAL_C[combo] if spec=='final' else {'paper':'H05','cubic':'H06','log':'H07'}.get(spec)
    return ROOT/f'results/Appendix/C/data/models/{combo}/{mid}' if mid else None

def source_files():
    files=[cm.E0,cm.R0,MAIN+'model_selection/knots.json',MAIN+'final_models/final_summary.json',MAIN+'weather_only/weather_only_summary.json',
        'analysis_new/model_selection.py','analysis_new/final_models.py','analysis_new/weather_only_regression.py','analysis_new/plot_model_selection.py',
        'scripts/c02_c08_repair_20260905/figure9_storm_validation.py','scripts/c02_c08_repair_20260905/corrected_sample_builder.py',
        'results/pretest/archive/20260909154556/results/final_combined_analysis/raw/step0_verification.json']
    for combo in cm.COMBOS:
        for spec in model_list(combo):
            directory=c_dir(combo,spec)
            if directory:
                files += [p.relative_to(ROOT).as_posix() for p in directory.glob('*') if p.name in ['coefficients.csv','in_sample.csv.gz','preprocessing.json','result.json']]
        files += [f'results/Appendix/C/data/samples/{combo}.csv.gz']
    for margin in ['E0','R0c']:
        files += [MAIN+f'final_models/{margin}_final_twoway.csv']
        files += [MAIN+f'weather_only/{margin}_weather_{s}_twoway.csv' for s in ['paper','hinge','final']]
        files += [f'results/Appendix/F/data/F02_{margin}_{s}' for s in ['DESIGN.csv.gz','ROWS.csv.gz','DESIGN_METADATA.json','COV_TWO_WAY.csv']]
    return sorted(set(files))

def coverage(samples):
    rows=[]
    for combo,d in samples.items():
        for spec in model_list(combo):
            cd=c_dir(combo,spec)
            available=cd is not None and (cd/'coefficients.csv').exists()
            saved_formal=spec=='final' or (combo.endswith('weather') and spec in ['paper','hinge'])
            rows.append(dict(combination=combo,model_id=spec,prediction_type='control_residual' if spec=='control' else 'in_sample',
                action='DERIVE' if available or saved_formal else 'REFIT_NEEDED',n=len(d),
                reason='compatible coefficient/design reconstruction; verify IDs and X beta against saved predictions' if available or saved_formal else 'no compatible full coefficient object; one fixed OLS',target='data/GI_PREDICTIONS.csv.gz'))
            if spec in ['final','paper','hinge']:
                rows.append(dict(combination=combo,model_id=spec,prediction_type='LAD_OOF',action='REFIT_NEEDED',n=len(d),
                    reason='existing fixed-production summaries lack row predictions; same original five LAD folds; fixed knots, not nested family CV',target='data/GI_PREDICTIONS.csv.gz'))
    rows.append(dict(combination='R0c_weather',model_id='C/F06 single family',prediction_type='nested_family_LAD_OOF',action='REUSE',n=len(samples['R0c_weather']),reason='reference existing C path only; not a fixed11 final prediction',target='results/Appendix/C/data/models/R0c_weather/F06/LAD_OOF.csv.gz'))
    rows.append(dict(combination='storm/all',model_id='final',prediction_type='in_sample/LAD_OOF',action='EXPORT',n=None,reason='slice shared G predictions; no storm-only fits',target='I/data/GI_STORM_PREDICTIONS.csv.gz'))
    rows.append(dict(combination='storm/all',model_id='final',prediction_type='temporal_holdout',action='NOT_APPLICABLE',n=None,reason='no frozen temporal incident model required; later dates alone do not imply holdout',target='none'))
    return pd.DataFrame(rows)

def full_beta(d,X,combo,spec):
    margin,scope=combo.split('_',1);directory=c_dir(combo,spec)
    source=None
    if spec=='final':source=ROOT/MAIN/(f'weather_only/{margin}_weather_final_twoway.csv' if scope=='weather' else f'final_models/{margin}_final_twoway.csv')
    elif scope=='weather' and spec in ['paper','hinge']:source=ROOT/MAIN/f'weather_only/{margin}_weather_{spec}_twoway.csv'
    elif directory is not None and (directory/'coefficients.csv').exists():source=directory/'coefficients.csv'
    if source is None:
        b=sm.OLS(d.y.to_numpy(),X).fit().params.to_numpy()
        return b,'REFIT_FIXED_OLS',None
    saved=read(source).set_index('term')
    if set(saved.index)!=set(X.columns):raise ValueError(f'{combo}/{spec}: source design terms mismatch')
    b=saved.loc[X.columns,'coef'].to_numpy()
    if directory is not None and (directory/'in_sample.csv.gz').exists():
        p=read(directory/'in_sample.csv.gz');pp=js(directory/'preprocessing.json')
        full=[v for v in pp if v['prediction_type']=='in_sample' and str(v['fold'])=='full']
        assert full[0]['train_ids_sha256']==cm.token(d[ID].astype(str).tolist())
        assert p.observation_id.tolist()==d[ID].tolist() and np.allclose(p.y,d.y,atol=1e-9)
        assert np.allclose(X.to_numpy()@b,p.prediction,atol=1e-8,rtol=1e-8)
    assert np.max(np.abs(X.to_numpy().T@(d.y.to_numpy()-X.to_numpy()@b)))/len(d)<1e-7
    return b,'DERIVE_SAVED_COEFFICIENTS',source.relative_to(ROOT).as_posix()

def row_frame(d,combo,spec,p,kind,fold,training):
    return pd.DataFrame(dict(observation_id=d[ID].astype(str),combination=combo,date=pd.to_datetime(d.incident_date_utc).dt.date.astype(str),
        LAD21CD=d.LAD21CD,gust=d.gust_0h,y=d.y,prediction=p,residual=d.y.to_numpy()-p,
        response_scale='natural_log1p_customers' if combo.startswith('E0') else 'natural_log_duration_hours',
        model_id=spec,prediction_type=kind,fold=fold,training_source=training,valid=np.isfinite(p)))

def compute(stage,samples):
    rows=[];states=[];preps=[];comparison=[];checks={};allbeta=[]
    for combo,d in samples.items():
        saved=read(ROOT/f'results/Appendix/C/data/samples/{combo}.csv.gz')
        assert saved.observation_id.tolist()==d[ID].tolist()
        foldcol='LAD_fold' if 'LAD_fold' in saved else 'lad_fold'
        assert np.array_equal(saved[foldcol],d.LAD_fold)
        checks[combo+'_sample_and_folds']=True
        for spec in model_list(combo):
            print(f'GI {combo}/{spec}: full arrays'+(' + fixed LAD folds' if spec in ['final','paper','hinge'] else ''),flush=True)
            X,_=design(d,d,combo,spec);b,action,source=full_beta(d,X,combo,spec)
            assert np.isfinite(X).all().all() and np.isfinite(b).all()
            p=X.to_numpy()@b;kind='control_residual' if spec=='control' else 'in_sample'
            train_hash=cm.token(d[ID].astype(str).tolist())
            rows.append(row_frame(d,combo,spec,p,kind,-1,train_hash))
            meta=dict(combination=combo,model_id=spec,prediction_type=kind,fold=-1,**cm.preprocessing(d,combo.startswith('R0c'),X.columns,knots(combo,spec)),beta=b.tolist(),source=source,action=action)
            preps.append(meta);states.append(dict(combination=combo,model_id=spec,prediction_type=kind,action=action,new_fits=int(action=='REFIT_FIXED_OLS'),source=source))
            allbeta += [dict(combination=combo,model_id=spec,term=c,coef=v) for c,v in zip(X.columns,b)]
            if spec=='control':assert not any('gust' in c for c in X)
            # Save complete curve covariance once; reuse F02 verbatim for weather final.
            if spec in ['final','hinge']:
                if combo.endswith('weather') and spec=='final':
                    m=combo.split('_')[0];froot=ROOT/'results/Appendix/F/data'
                    fx=read(froot/f'F02_{m}_DESIGN.csv.gz').set_index('observation_id');fr=read(froot/f'F02_{m}_ROWS.csv.gz')
                    assert fx.index.tolist()==d[ID].tolist() and list(fx.columns)==list(X.columns)
                    assert np.allclose(fx,X,atol=1e-12) and np.allclose(fr.residual,d.y-p,atol=1e-8)
                    cv=read(froot/f'F02_{m}_COV_TWO_WAY.csv').set_index('term').loc[X.columns,X.columns].to_numpy()
                else:
                    lad=pd.factorize(d.LAD21CD)[0];date=pd.factorize(pd.to_datetime(d.incident_date_utc).dt.date.astype(str))[0]
                    cv=covariance_from_residuals(X,d.y.to_numpy()-p,lad,date)[0]
                csv(stage/f'data/GI_{combo}_{spec}_COV.csv',pd.DataFrame(cv,columns=X.columns).assign(term=X.columns))
            if spec not in ['final','paper','hinge']:continue
            pred=np.full(len(d),np.nan)
            for fold in range(5):
                mask=d.LAD_fold.eq(fold);tr=d.loc[~mask];va=d.loc[mask];a,v=design(tr,va,combo,spec);v=v.reindex(columns=a.columns,fill_value=0.)
                assert not set(tr.LAD21CD)&set(va.LAD21CD)
                fit=sm.OLS(tr.y.to_numpy(),a).fit();pred[mask]=v.to_numpy()@fit.params.to_numpy()
                preps.append(dict(combination=combo,model_id=spec,prediction_type='LAD_OOF',fold=fold,**cm.preprocessing(tr,combo.startswith('R0c'),a.columns,knots(combo,spec)),beta=fit.params.tolist(),test_ids_sha256=cm.token(va[ID].astype(str).tolist()),action='REFIT_ORIGINAL_FIXED_FOLD'))
            assert np.isfinite(pred).all()
            rows.append(row_frame(d,combo,spec,pred,'LAD_OOF',d.LAD_fold,'GI_PREPROCESSING.json: combination/model_id/fold'))
            states.append(dict(combination=combo,model_id=spec,prediction_type='LAD_OOF',action='REFIT_ORIGINAL_FIXED_FOLDS',new_fits=5,source='final_models.main or weather_only_regression.cv_lad; same seed and fixed knots'))
            margin,scope=combo.split('_',1)
            old=WS[margin]['fits'][spec]['cv_lad'] if scope=='weather' else FS[margin][spec+'_cv_lad']
            score=float(np.sqrt(np.mean((d.y-pred)**2)))
            comparison.append(dict(combination=combo,model_id=spec,prediction_type='LAD_OOF_fixed_production',n=len(d),old_rmse=old,pooled_rmse=score,difference=score-old,within_numeric_tolerance=bool(np.isclose(score,old,atol=1e-9,rtol=1e-8))))
    master=pd.concat(rows,ignore_index=True)
    assert not master.duplicated(['combination','model_id','prediction_type','observation_id']).any()
    csv(stage/'data/GI_PREDICTIONS.csv.gz',master)
    csv(stage/'data/GI_COEFFICIENTS.csv',pd.DataFrame(allbeta));write_json(stage/'data/GI_PREPROCESSING.json',preps)
    csv(stage/'data/GI_COMPONENT_STATUS.csv',pd.DataFrame(states));csv(stage/'data/GI_SUMMARY_ALIGNMENT.csv',pd.DataFrame(comparison))
    checks['all_fixed_oof_match_original_summary']=all(v['within_numeric_tolerance'] for v in comparison)
    checks['unique_prediction_keys']=True
    # Explicitly retain C family CV as a reference, without relabelling or re-fitting.
    path='results/Appendix/C/data/models/R0c_weather/F06/LAD_OOF.csv.gz'
    write_json(stage/'data/GI_NESTED_REFERENCE.json',dict(path=path,sha256=digest(ROOT/path),identity='C matched single-knot family: train-fold selected knots; not fixed11 production',used_for_G_or_I_final_scores=False))
    return master,checks

def scores(y,p):
    y=np.asarray(y);p=np.asarray(p);e=p-y;n=len(y);den=float(np.sum((y-y.mean())**2)) if n else 0
    return dict(n=n,rmse=float(np.sqrt(np.mean(e**2))) if n else np.nan,mae=float(np.mean(abs(e))) if n else np.nan,
        mean_observed=float(y.mean()) if n else np.nan,mean_prediction=float(p.mean()) if n else np.nan,bias=float(e.mean()) if n else np.nan,
        r2=float(1-np.sum(e**2)/den) if den>0 else np.nan,
        correlation=float(np.corrcoef(y,p)[0,1]) if n>=3 and np.std(y)>0 and np.std(p)>0 else np.nan)
