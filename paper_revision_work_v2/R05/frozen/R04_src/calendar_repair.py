from common import *
from diagnostics import cluster_covariance
from prediction import physical_gust_terms,minimum_interface
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster

def predict_supported(d,m):
    support={tuple(v) for v in m['supported_calendar']}
    if not all(tuple(v) in support for v in d[['new_year','new_month']].astype(int).to_numpy()):raise ValueError('unsupported year-month combination for equivalent period basis')
    x=design(d,m['preprocessor'],m['block'])[m['columns']]
    return x.to_numpy()@np.array(m['parameters'])

def run():
    e=events();rows=[];checks=[];fits=0
    config={'run_id':'R04_period_equivalent_v1','input':'R02_input_20260905','basis_policy':'retain all substantive columns and intercept; add calendar in original deterministic order if independent','relative_rank_tolerance':1e-10,'equivalence_atol':1e-7,'tails':'all_valid','groups':['main','weather'],'targets':['E0','R0c'],'periods':['development','later'],'reference':'each group-target full-period training mean physical pressure; own period gust/pressure scales','covariance':'CR1 with effective full rank k, no CV inverse variance intervals','supported_prediction':'observed year-month combinations within each period only','producer_sha256':sha(Path(__file__))}
    save(Q/'configs/period_equivalent_v1.json',config)
    for g in config['groups']:
      for t in config['targets']:
        full=model(g,t);pressure=full['preprocessor']['mean']['pressure_msl_0h']
        for period in config['periods']:
            d=members(e,g,t);d=d.loc[d.new_period.eq(period)].copy();prep=fit_preprocessor(d,t);block='G' if t=='E0' else 'GK';x=design(d,prep,block);a=x.to_numpy();n,k=a.shape
            substantive=[c for c in x if not c.startswith(('year_','month_'))];calendar=[c for c in x if c not in substantive];keep=substantive.copy()
            # Normalize only for numerical rank selection; raw design/coefficients remain unchanged.
            def rank(cols):
                b=x[cols].to_numpy();b=b/np.linalg.norm(b,axis=0);return int(np.linalg.matrix_rank(b,tol=1e-10))
            assert rank(keep)==len(keep),'substantive block not identifiable'
            for c in calendar:
                if rank(keep+[c])>len(keep):keep.append(c)
            # Preserve original column order in released archive.
            keep=[c for c in x if c in keep];b=x[keep].to_numpy();r=len(keep)
            forward=np.linalg.lstsq(b,a,rcond=None)[0];back=np.linalg.lstsq(a,b,rcond=None)[0]
            y=target(d,t);beta=np.linalg.lstsq(b,y,rcond=None)[0];oldbeta=np.linalg.lstsq(a,y,rcond=None)[0];eta=b@beta
            residual=max(float(np.max(np.abs(b@forward-a))),float(np.max(np.abs(a@back-b))));pred_error=float(np.max(np.abs(eta-a@oldbeta)))
            _,sv,vh=np.linalg.svd(a,full_matrices=False);oldrank=int(np.linalg.matrix_rank(a));null=vh[oldrank:].T
            ident={c:float(np.linalg.norm(null[list(x.columns).index(c)])) for c in substantive}
            # Original intercept can share the calendar null direction under reference coding.
            # Require identifiability of scientific covariates; retain intercept in the new basis.
            assert residual<1e-7 and pred_error<1e-7 and max(v for c,v in ident.items() if c!='const')<1e-7
            covs={};meta={};res=y-eta
            for label,clusters in [('LAD',d.LAD21CD),('date',d.new_date_utc),('intersection',d.LAD21CD+'|'+d.new_date_utc)]:
                cv=cluster_covariance(pd.DataFrame(b),res,clusters);check=cov_cluster(sm.OLS(y,b).fit(),pd.factorize(clusters)[0]);assert np.allclose(cv,check,rtol=1e-5,atol=1e-8)
                covs[label]=cv;ng=clusters.nunique();meta[label]={'clusters':int(ng),'factor':float(ng/(ng-1)*(n-1)/(n-r))}
            covs['two_way']=covs['LAD']+covs['date']-covs['intersection']
            archive={'schema':'R04_equivalent_period_linear_v1','columns':keep,'original_columns':list(x),'parameters':beta.tolist(),'preprocessor':prep,'block':block,'target':t,'target_scale':full['target_scale'],'supported_calendar':d[['new_year','new_month']].drop_duplicates().astype(int).values.tolist(),'training_ids':sorted(d[ID]),'training_dates':sorted(d.new_date_utc.unique()),'training_n':n,'rank':r,'metadata':{'run_id':config['run_id'],'group':g,'period':period,'code_sha256':config['producer_sha256'],'config_sha256':config_hash(config),'input_sha256':sha(W/'R02/data/R02_event_master.parquet')},'covariance':{c:v.tolist() for c,v in covs.items()},'covariance_factors':meta,'residual_df':n-r,'calendar_individual_effects':'not all uniquely identifiable in redundant original encoding'}
            dest=Q/'periods_v2'/f'{g}_{t}_{period}.json';save(dest,archive);assert np.array_equal(predict_supported(d,read(dest)),eta)
            unsupported=d.iloc[:1].copy();unsupported['new_year']=2099
            try:predict_supported(unsupported,archive);raise AssertionError('unsupported category accepted')
            except ValueError:pass
            params=physical_gust_terms(archive,pressure);j={c:i for i,c in enumerate(keep)};sd=prep['sd']['gust_0h'];mu=prep['mean']['gust_0h'];zp=(pressure-prep['mean']['pressure_msl_0h'])/prep['sd']['pressure_msl_0h'];jac=np.zeros((2,r));jac[0,j['zG']]=1/sd;jac[0,j['zG2']]=-2*mu/sd**2;jac[0,j['zG_zPressure']]=zp/sd;jac[1,j['zG2']]=1/sd**2
            pc=jac@covs['LAD']@jac.T;minimum=minimum_interface(archive,pressure,np.quantile(d.gust_0h,[.01,.99]))
            rec={'group':g,'target':t,'period':period,'n':n,'old_k':k,'rank':r,'removed_calendar':';'.join(c for c in x if c not in keep),'beta_gust':beta[j['zG']],'beta_gust2':beta[j['zG2']],**params,'physical_linear_SE':np.sqrt(pc[0,0]) if pc[0,0]>=0 else None,'physical_quadratic_SE':np.sqrt(pc[1,1]) if pc[1,1]>=0 else None,'minimum_ms':minimum['minimum_ms'],'minimum_status':minimum['status'],'status':'equivalent_basis_verified','period_archive':str(dest)};rows.append(rec)
            checks.append({'group':g,'target':t,'period':period,'n':n,'original_columns':list(x),'retained_columns':keep,'old_rank':oldrank,'new_rank':r,'old_condition':float(np.linalg.cond(a)),'new_condition':float(np.linalg.cond(b)),'new_to_old':forward.tolist(),'old_to_new':back.tolist(),'max_space_residual':residual,'max_eta_difference':pred_error,'substantive_nullspace_norms':ident,'covariance_metadata':meta,'effective_k':r,'unsupported_predictions_rejected':True,'minimum':minimum,'year2024_equals_JanFebMar_maxres':float(np.max(np.abs(d.new_year.eq(2024).astype(int)-d.new_month.isin([1,2,3]).astype(int)))) if period=='later' else None})
            fits+=1;print(g,t,period,'rank',oldrank,k,'->',r,'eta error',pred_error,flush=True)
    table(Q/'tables/period_comparison.csv',pd.DataFrame(rows));save(Q/'checks/calendar_equivalence.json',{'passed':True,'fits':fits,'checks':checks})
if __name__=='__main__':run()
