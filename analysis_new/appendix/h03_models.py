"""APP-H03-LINK: four existing families on two fixed final designs.

No OLS fitting, CV or knot selection. NB2 estimates alpha jointly; other
families follow the original H script's log link and Pearson scale.
"""
import inspect
import warnings
import numpy as np
import pandas as pd
import statsmodels
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups,cov_cluster
from .catalog import ROOT,MAIN,E0,R0,MANUSCRIPT
from .gi_core import cm,design
from .f02_cov import read,js,csv,token
from .mapping import digest,write_json

PLAN='docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令 (3).md'
OLD='results/pretest/archive/20260909154556/results/appendix_h_20260906/raw/stepB_distribution_check_corrected.json'
OLD_CODE='scripts/appendix_h_20260906/step_b_distribution_check.py'
G='results/Appendix/G/'
MODELS=[('E0_all','NB2'),('E0_all','Tweedie'),('R0c_all','Gamma'),('R0c_all','Tweedie')]
RULES=dict(nb2=dict(method='bfgs',maxiter=200,gtol=1e-5,alpha='joint MLE in current sample; NB2 parameter alpha after internal log-alpha optimisation',initial='original statsmodels default internal Poisson fit and dispersion estimate'),
    glm=dict(method='IRLS',maxiter=100,tol=1e-8,scale='X2 (Pearson chi square / residual df)',link='Log'),
    tweedie=dict(var_power=1.5,eql=True,power_search=False,likelihood='quasi-score; full likelihood and AIC/BIC not reported'),
    inference=dict(use_correction=True,reference='Student t',df='G_LAD-1',alpha=.05,
        correction='G/(G-1)*(n-1)/(n-k), separate LAD/date/intersection; k includes joint NB alpha',
        score='model.score_obs; GLM at fitted Pearson scale; NB in full beta/alpha coordinates',bread='inverse negative observed Hessian, full joint NB parameters',
        negative_variance='invalid individual interval, no abs/clipping/PSD projection'),
    validity=dict(max_abs_mean_score=1e-4,required='solver convergence, finite parameters/positive fitted mean/objective, finite score, maximum absolute mean score <=1e-4',retry='one NB-only constant-mean numerical recovery after invalid original attempt; same BFGS max200/gtol, no candidate or result-based selection'),
    scope='four full-sample GLM candidates, two saved OLS references; no weather GLM claim found in H1 or body P030; no CV/selection')

def sources():
    paths=[PLAN,MANUSCRIPT,E0,R0,OLD,OLD_CODE,'analysis_new/fragility_demo.py','analysis_new/fragility_surfaces.py',
        'analysis_new/model_selection.py','analysis_new/final_models.py','analysis_new/weather_only_regression.py',
        MAIN+'model_selection/knots.json',MAIN+'weather_only/weather_only_summary.json',
        MAIN+'model_selection/fragility_summary.json',MAIN+'model_selection/fragility_lognormal.json',MAIN+'model_selection/fragility_optimizer_diagnostics.json',
        G+'data/GI_PREPROCESSING.json',G+'data/GI_COEFFICIENTS.csv',G+'data/GI_PREDICTIONS.csv.gz']
    for m in ['E0','R0c']:
        paths += [MAIN+f'final_models/{m}_final_twoway.csv',G+f'data/GI_{m}_all_final_COV.csv',f'results/Appendix/C/data/samples/{m}_all.csv.gz']
    return paths

def matrix(out,stem,a,columns):
    csv(out/f'data/{stem}.csv',pd.DataFrame(a,columns=columns).assign(term=columns)[['term',*columns]])

def bundles(stage):
    samples=cm.samples();preps=js(ROOT/G/'data/GI_PREPROCESSING.json');coefs=read(ROOT/G/'data/GI_COEFFICIENTS.csv')
    pred=read(ROOT/G/'data/GI_PREDICTIONS.csv.gz');result={};definitions=[]
    for combo in ['E0_all','R0c_all']:
        d=samples[combo];X,_=design(d,d,combo,'final');p=next(p for p in preps if p['combination']==combo and p['model_id']=='final' and p['fold']==-1)
        accepted=read(ROOT/f'results/Appendix/C/data/samples/{combo}.csv.gz')
        assert accepted.observation_id.tolist()==d[cm.ID].tolist() and np.allclose(accepted.y,d.y,atol=1e-12)
        assert p['train_ids_sha256']==cm.token(d[cm.ID].astype(str).tolist()) and list(X)==p['columns']
        b=coefs[coefs.combination.eq(combo)&coefs.model_id.eq('final')].set_index('term').loc[X.columns,'coef'].to_numpy()
        gp=pred[pred.combination.eq(combo)&pred.model_id.eq('final')&pred.prediction_type.eq('in_sample')]
        assert gp.observation_id.tolist()==d[cm.ID].tolist() and np.allclose(gp.y,d.y,atol=1e-12)
        assert np.allclose(X.to_numpy()@b,gp.prediction,rtol=1e-10,atol=1e-10)
        raw=d[cm.C if combo.startswith('E0') else 'duration_B_full_span_hours'].to_numpy()
        assert np.isfinite(raw).all() and np.isfinite(X).all().all()
        if combo.startswith('E0'):assert (raw>=0).all() and (raw==np.floor(raw)).all()
        else:assert (raw>0).all() and d[cm.C].gt(0).all()
        lad,ladlevels=pd.factorize(d.LAD21CD);date,dates=pd.factorize(pd.to_datetime(d.incident_date_utc).dt.date.astype(str))
        pair=pd.factorize(pd.MultiIndex.from_arrays([lad,date]))[0]
        row=pd.DataFrame(dict(observation_id=d[cm.ID],LAD21CD=d.LAD21CD,date=pd.to_datetime(d.incident_date_utc).dt.date.astype(str),
            lad_code=lad,date_code=date,intersection_code=pair,raw_response=raw,ols_response=d.y,ols_prediction=gp.prediction.to_numpy()))
        csv(stage/f'data/H03_{combo}_ROWS.csv.gz',row);csv(stage/f'data/H03_{combo}_DESIGN.csv.gz',X.assign(observation_id=d[cm.ID]))
        meta=dict(combination=combo,n=len(d),response='customers C' if combo.startswith('E0') else 'duration T (hours)',
            raw_min=float(raw.min()),raw_max=float(raw.max()),zero_responses=int((raw==0).sum()),noninteger_responses=int((raw!=np.floor(raw)).sum()),
            filtering='accepted E0 including0' if combo.startswith('E0') else 'accepted R0c combined p99 then positive customers; IDs unchanged',
            source=E0 if combo.startswith('E0') else R0,source_sha256=digest(ROOT/(E0 if combo.startswith('E0') else R0)),
            n_columns=X.shape[1],design_rank=int(np.linalg.matrix_rank(X)),LAD_clusters=len(ladlevels),date_clusters=len(dates),intersection_clusters=len(np.unique(pair)),
            sample_id_sha256=cm.token(d[cm.ID].astype(str).tolist()),X_sha256=digest(stage/f'data/H03_{combo}_DESIGN.csv.gz'),
            ols_source=G+'data/GI_PREPROCESSING.json',full_design=p,ols_refit=False)
        write_json(stage/f'data/H03_{combo}_SPECIFICATION.json',meta)
        result[combo]=(d,X,raw,b,lad,date,meta)
        for candidate in ['OLS_reference']+[m for c,m in MODELS if c==combo]:
            definitions.append(dict(combination=combo,model=candidate,n=len(d),response=('log1p(C)' if combo.startswith('E0') else 'log(T)') if candidate=='OLS_reference' else meta['response'],
                family_link='OLS identity on transformed response' if candidate=='OLS_reference' else candidate+' / explicit log mean',
                prediction_basis='fixed14/25 platform with temp2 and gust-pressure' if combo.startswith('E0') else 'quadratic gust with temp2 and gust-precip, log1p(customers) and square',
                parameters='saved fixed OLS' if candidate=='OLS_reference' else 'jointly estimated alpha, full inference' if candidate=='NB2' else 'power1.5 fixed; Pearson scale; eql=True' if candidate=='Tweedie' else 'Pearson scale estimated; explicit log link',
                action='REUSE' if candidate=='OLS_reference' else 'REFIT_NEEDED',source=G+'data/GI_PREPROCESSING.json' if candidate=='OLS_reference' else OLD_CODE,
                interpretation='E[transformed response|X]' if candidate=='OLS_reference' else 'log E[raw response|X]; not numerically same estimand as OLS'))
    definitions += [dict(combination=c,model='weather GLM',n=len(samples[c]),action='NOT_APPLICABLE',source='body P030 and H01/H03 registration',interpretation='H1 old comparator and claim refer to all-incident fits; weather GLM not explicitly required. Weather empirical/legacy H3 still exported.') for c in ['E0_weather','R0c_weather']]
    return result,pd.DataFrame(definitions)

def inference(beta,cov,columns,df,combo,model,point_valid=True):
    variance=np.diag(cov);se=np.full(len(beta),np.nan);np.sqrt(variance,out=se,where=np.isfinite(variance)&(variance>=0))
    with np.errstate(divide='ignore',invalid='ignore'):p=2*stats.t.sf(abs(beta/se),df)
    t=stats.t.ppf(.975,df)
    return pd.DataFrame(dict(combination=combo,model=model,term=columns,coef=beta,se_twoway=se,ci_lower=beta-t*se,ci_upper=beta+t*se,p_t_G1=p,df=df,
        variance=variance,point_valid=point_valid,interval_valid=point_valid&np.isfinite(se),reference='t(G_LAD-1)'))

def ols_reference(stage,combo,bundle):
    d,X,y,b,lad,date,meta=bundle
    V=read(ROOT/G/f'data/GI_{combo}_final_COV.csv').set_index('term').loc[X.columns,X.columns].to_numpy()
    old=read(ROOT/MAIN/f'final_models/{combo.split("_")[0]}_final_twoway.csv').set_index('term').loc[X.columns]
    rows=inference(b,V,X.columns,meta['LAD_clusters']-1,combo,'OLS_reference')
    assert np.allclose(rows.coef,old.coef,atol=1e-10) and np.allclose(rows.se_twoway,old.se,atol=1e-9)
    matrix(stage,f'H03_{combo}_OLS_reference_COV_TWO_WAY',V,X.columns)
    return rows

def fit_one(stage,combo,family,bundle,constant_start=False):
    d,X,y,ols_beta,lad,date,meta=bundle;n=len(d);prefix=f'H03_{combo}_{family}';captured=[];fit=None
    print(f'H03 {combo}/{family}: fixed X, n={n}; original solver budget',flush=True)
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            if family=='NB2':
                model=sm.NegativeBinomial(y,X,loglike_method='nb2')
                start=None
                if constant_start:
                    mu0=np.full(n,float(np.mean(y)));start=np.zeros(X.shape[1]+1)
                    start[list(X.columns).index('Intercept')]=np.log(mu0[0])
                    start[-1]=max(.05,float(model._estimate_dispersion(mu0,y-mu0,df_resid=n-meta['design_rank'])))
                    csv(stage/f'data/{prefix}_RECOVERY_START.csv',pd.DataFrame(dict(term=[*X.columns,'alpha'],value=start)))
                fit=model.fit(start_params=start,method='bfgs',maxiter=200,gtol=1e-5,disp=0)
                columns=[*X.columns,'alpha'];beta=np.asarray(fit.params);scale=1.;mu=np.asarray(fit.predict())
                assert model._transparams is False
                score=model.score_obs(beta);H=model.hessian(beta);conv=bool(fit.mle_retvals.get('converged',False));objective=float(-fit.llf)
                llf=float(fit.llf);dev=np.nan;iterations=fit.mle_retvals
            else:
                fam=sm.families.Gamma(link=sm.families.links.Log()) if family=='Gamma' else sm.families.Tweedie(var_power=1.5,link=sm.families.links.Log(),eql=True)
                model=sm.GLM(y,X,family=fam);fit=model.fit(method='IRLS',maxiter=100,tol=1e-8,scale='X2')
                columns=list(X.columns);beta=np.asarray(fit.params);scale=float(fit.scale);mu=np.asarray(fit.fittedvalues)
                score=model.score_obs(beta,scale=scale);H=model.hessian(beta,scale=scale,observed=True)
                conv=bool(fit.converged);objective=float(fit.deviance);dev=objective
                llf=float(fit.llf) if family=='Gamma' else None
                iterations=dict(iteration=fit.fit_history.get('iteration'),deviance=fit.fit_history.get('deviance'))
        score_error=float(np.max(abs(score.mean(axis=0))))
        valid=bool(conv and np.isfinite(beta).all() and np.isfinite(mu).all() and (mu>0).all() and np.isfinite(objective) and np.isfinite(score).all() and score_error<=RULES['validity']['max_abs_mean_score'])
        if family=='NB2':valid=valid and bool(beta[-1]>0)
        diag=dict(combination=combo,model=family,n=n,solver_converged=conv,point_valid=valid,objective=objective,
            objective_kind='negative full NB2 log likelihood' if family=='NB2' else 'family deviance',
            scale=scale,alpha=float(beta[-1]) if family=='NB2' else None,power=1.5 if family=='Tweedie' else None,
            max_abs_mean_score=score_error,mu_min=float(np.min(mu)),mu_max=float(np.max(mu)),
            likelihood=llf,AIC=None,BIC=None,likelihood_note='quasi-likelihood; no full likelihood/AIC/BIC' if family=='Tweedie' else 'own response likelihood only; no cross-transformation information-criterion ranking',
            covariance_status='not_calculated',parameters=columns,new_primary_fits=1,
            initial_auxiliary=('constant mean initial beta; original _estimate_dispersion rule at constant mean, alpha jointly re-estimated; no auxiliary fit' if constant_start else 'one internal Poisson fit for original NB starting values (not a candidate)') if family=='NB2' else 'original family starting_mu; no preliminary OLS model',
            numerical_recovery=constant_start,
            scale_inference='NB alpha jointly included in Hessian/scores' if family=='NB2' else 'Pearson scale plugged in, beta quasi-score inference; not an added dispersion parameter dimension',
            warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in captured])
        def clean(v):
            if isinstance(v,np.ndarray):return [clean(x) for x in v.tolist()]
            if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
            if isinstance(v,(tuple,list)):return [clean(x) for x in v]
            if isinstance(v,(np.integer,np.bool_)):return v.item()
            if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
            return v
        write_json(stage/f'data/{prefix}_OPTIMIZER.json',clean(iterations))
        csv(stage/f'data/{prefix}_PARAMETERS.csv',pd.DataFrame(dict(term=columns,coef=beta)))
        csv(stage/f'data/{prefix}_FITTED.csv.gz',pd.DataFrame(dict(observation_id=d[cm.ID],raw_response=y,mu=mu,eta=X.to_numpy()@beta[:X.shape[1]],point_valid=valid,prediction_type='full_sample_GLM_raw_conditional_mean')))
        csv(stage/f'data/{prefix}_SCORES.csv.gz',pd.DataFrame(score,columns=columns).assign(observation_id=d[cm.ID]))
        matrix(stage,prefix+'_OBSERVED_INFORMATION',-H,columns)
        try:
            if not np.isfinite(H).all():raise ValueError('nonfinite observed Hessian')
            bread=np.linalg.inv(-H)
            both,cl,cd=cov_cluster_2groups((score,bread),lad,date,use_correction=True)
            direct,_,_=cov_cluster_2groups(fit,lad,date,use_correction=True)
            covs={'TWO_WAY':both,'LAD':cl,'DATE':cd,'INTERSECTION':cl+cd-both,'BREAD':bread}
            finite=all(np.isfinite(v).all() and np.allclose(v,v.T,rtol=1e-9,atol=1e-10) for v in covs.values())
            if not finite:raise ValueError('nonfinite/asymmetric covariance')
            delta=float(np.max(abs(direct-both)));assert np.allclose(direct,both,atol=1e-9,rtol=1e-8)
            for name,v in covs.items():matrix(stage,prefix+'_COV_'+name,v,columns)
            df=meta['LAD_clusters']-1;rows=inference(beta,both,columns,df,combo,family,valid)
            diag.update(covariance_status='full_score_observed_Hessian',inference_valid=bool(valid and rows.interval_valid.all()),
                direct_statsmodels_cov_max_abs_difference=delta,df=df,parameter_count=len(columns),
                correction_factors={k:float(v/(v-1)*(n-1)/(n-len(columns))) for k,v in [('LAD',meta['LAD_clusters']),('date',meta['date_clusters']),('intersection',meta['intersection_clusters'])]},
                observed_information_rank=int(np.linalg.matrix_rank(-H)),observed_information_min_eigenvalue=float(np.linalg.eigvalsh(-H).min()),
                negative_diagonal_terms=[columns[k] for k in np.flatnonzero(np.diag(both)<0)],two_way_min_eigenvalue=float(np.linalg.eigvalsh(both).min()),numerical_correction='none')
        except Exception as exc:
            rows=inference(beta,np.full((len(beta),len(beta)),np.nan),columns,meta['LAD_clusters']-1,combo,family,valid)
            diag.update(covariance_status='unavailable',inference_valid=False,covariance_error=f'{type(exc).__name__}: {exc}')
        write_json(stage/f'data/{prefix}_DIAGNOSTICS.json',clean(diag))
        print(f'H03 {combo}/{family}: converged={conv}, mean-score max={score_error:.5g}, inference={diag["inference_valid"]}',flush=True)
        return rows,diag
    except Exception as exc:
        diag=dict(combination=combo,model=family,n=n,point_valid=False,inference_valid=False,error=f'{type(exc).__name__}: {exc}',
            warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in captured],new_primary_fits=1)
        write_json(stage/f'data/{prefix}_DIAGNOSTICS.json',diag)
        print(f'H03 {combo}/{family}: FAILED {exc}',flush=True)
        return pd.DataFrame(),diag
