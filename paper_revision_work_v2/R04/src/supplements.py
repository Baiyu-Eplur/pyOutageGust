from common import *
from diagnostics import cluster_covariance
from scipy import stats
import statsmodels.api as sm
import warnings

def archive_fit(d,x,t,prep,label,fold=None):
    y=target(d,t);a=x.to_numpy();beta,_,r,_=np.linalg.lstsq(a,y,rcond=None);assert r==len(x.columns)
    cov=cluster_covariance(x,y-a@beta,d.LAD21CD)
    obj={'schema':'R04_supplement_linear_v1','target':t,'label':label,'fold':fold,'columns':list(x),'parameters':beta.tolist(),'preprocessor':prep,'training_ids':sorted(d[ID]),'training_dates':sorted(d.new_date_utc.unique()),'rank':int(r),'n':len(d),'LAD_CR1':cov.tolist(),'producer_sha256':sha(Path(__file__))}
    return obj,beta
def run():
    e=events();out=Q/'supplements_v1';assert not out.exists();out.mkdir();results=[];fits=0;attempts=0
    spec={'run_id':'R04_supplements_v1','source_definitions':'R03 frozen step40_model_form_check, step40_1_cubic_gust_term, step36_six_group_clean_sample','input':'R02','primary_tail':'all_valid','cubic':'original zG^3 only, no model search; same B1 folds; reuse B1 quadratic predictions','six_groups':'R02 complete inputs and all six agreed causes; all_valid harmonized B1 membership, no old global p99; full + shared-date diagnostic','GLM':'original E NB2 BFGS maxiter200, Tweedie power1.5 log eql; R Gamma log, Tweedie1.5 log eql; LAD covariance; no search','producer_sha256':sha(Path(__file__))};save(Q/'configs/supplements_v1.json',spec)
    for t in ['E0','R0c']:
        d=members(e,'main',t);m=model('main',t);block=m['block'];prep=m['preprocessor'];x=design(d,prep,block);yraw=d[C] if t=='E0' else d[D]
        models=[('NB2',lambda:sm.NegativeBinomial(yraw,x).fit(cov_type='cluster',cov_kwds={'groups':d.LAD21CD},maxiter=200,disp=0,method='bfgs'))] if t=='E0' else [('Gamma_log',lambda:sm.GLM(yraw,x,family=sm.families.Gamma(link=sm.families.links.Log())).fit(cov_type='cluster',cov_kwds={'groups':d.LAD21CD}))]
        models.append(('Tweedie_1.5_log',lambda:sm.GLM(yraw,x,family=sm.families.Tweedie(var_power=1.5,link=sm.families.links.Log(),eql=True)).fit(cov_type='cluster',cov_kwds={'groups':d.LAD21CD})))
        for name,fn in models:
            attempts+=1
            try:
                with warnings.catch_warnings(record=True) as warns:
                    warnings.simplefilter('always');fit=fn()
                converged=bool(getattr(fit,'converged',getattr(fit,'mle_retvals',{}).get('converged',False)));cov=np.asarray(fit.cov_params());valid=converged and np.isfinite(fit.params).all() and np.isfinite(cov).all() and (np.diag(cov)>=0).all()
                archive={'target':t,'family':name,'n':len(d),'parameters':fit.params.to_dict(),'columns':list(fit.params.index),'preprocessor':prep,'training_ids':sorted(d[ID]),'covariance':cov.tolist(),'converged':converged,'valid_for_reporting':valid,'warnings':list(dict.fromkeys(str(w.message) for w in warns)),'producer_sha256':sha(Path(__file__))};save(out/f'{t}_{name}_GLM.json',archive);fits+=1
                results.append({'analysis':'GLM','target':t,'variant':name,'n':len(d),'status':'computed' if valid else 'fit_or_covariance_invalid','beta_gust':fit.params.get('zG'),'beta_gust2':fit.params.get('zG2'),'pooled_R2':None,'delta_R2':None,'warning_count':len(warns)})
            except Exception as ex:
                save(out/f'{t}_{name}_failure.json',{'error':repr(ex)});results.append({'analysis':'GLM','target':t,'variant':name,'n':len(d),'status':'technical_failure','error':repr(ex)})
            print('GLM',t,name,results[-1]['status'],flush=True)
        # Existing B1 quadratic full/OOF are the exact paired comparator; no redundant quadratic fitting.
        p=pd.read_csv(RUN/f'main_{t}/oof_{block}.csv',float_precision='round_trip').set_index(ID).loc[d[ID]].reset_index();pred=np.full(len(d),np.nan)
        for f in range(5):
            tr=d.loc[p.fold.to_numpy()!=f];va=d.loc[p.fold.to_numpy()==f];pp=fit_preprocessor(tr,t);xt=design(tr,pp,block);xt['zG3']=xt.zG**3;xv=design(va,pp,block);xv['zG3']=xv.zG**3
            ar,b=archive_fit(tr,xt,t,pp,'cubic',f);save(out/f'{t}_cubic_fold{f}.json',ar);pred[p.fold.to_numpy()==f]=xv.to_numpy()@b;fits+=1;attempts+=1
        xx=x.copy();xx['zG3']=xx.zG**3;ar,b=archive_fit(d,xx,t,prep,'cubic');save(out/f'{t}_cubic_full.json',ar);fits+=1;attempts+=1
        p['cubic_eta']=pred;table(out/f'{t}_cubic_paired_OOF.csv',p);r2=score(target(d,t),pred)['r2'];br2=score(target(d,t),p.prediction_eta)['r2'];results.append({'analysis':'cubic','target':t,'variant':'zG3','n':len(d),'status':'computed','beta_gust':b[list(xx).index('zG')],'beta_gust2':b[list(xx).index('zG2')],'beta_gust3':b[-1],'pooled_R2':r2,'quadratic_R2':br2,'delta_R2':r2-br2})
        print('cubic',t,'delta',r2-br2,flush=True)
    valid=e.new_in_study_utc.fillna(False)&e.cause_group_event.isin(['technical_asset','weather_natural','third_party','external_or_customer','human_error','non_fault_or_unknown'])&np.isfinite(e[WX+REGION+[C,D]].astype(float)).all(axis=1)&e[C].ge(0)&e[D].gt(0)&e.LAD21CD.notna();d=e.loc[valid].copy();fm=pd.read_csv(CORE/'folds/date_to_fold.csv');assert set(d.new_date_utc)<=set(fm.date_utc);d=attach_folds(d,fm);pred=np.full(len(d),np.nan)
    for f in [-1,0,1,2,3,4]:
        tr=d if f==-1 else d.loc[d.fold.ne(f)];pp=fit_preprocessor(tr,'R0c');xt=design(tr,pp,'GK');ar,b=archive_fit(tr,xt,'R0c',pp,'six_groups',f);save(out/f'six_group_{f}.json',ar);fits+=1;attempts+=1
        if f!=-1:va=d.loc[d.fold.eq(f)];pred[d.fold.eq(f).to_numpy()]=design(va,pp,'GK').to_numpy()@b
    oof=d[[ID,'fold']].copy();oof['y']=target(d,'R0c');oof['prediction_eta']=pred;table(out/'six_groups_OOF.csv',oof);r2=score(oof.y,pred)['r2'];results.append({'analysis':'six_groups','target':'R0c','variant':'all_valid_shared_dates','n':len(d),'status':'computed_harmonized_scope','pooled_R2':r2,'delta_R2':None});table(out/'six_group_counts.csv',d.groupby('cause_group_event').size().rename('n').reset_index())
    table(Q/'tables/supplement_summary.csv',pd.DataFrame(results));save(Q/'checks/supplement_execution.json',{'fits_returned':fits,'model_attempts':attempts,'results':results,'no_new_model_search':True,'bootstrap':0})
if __name__=='__main__':run()
