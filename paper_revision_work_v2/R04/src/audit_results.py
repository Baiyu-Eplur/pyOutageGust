from common import *
from producer import score_oof
from diagnostics import cluster_covariance
from prediction import physical_gust_terms
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from scipy import stats

def run():
    e=events();metrics=[];coefs=[];checks=[];descs=[];storms=[];windows=read(CORE/'configs/storm_windows.json');all_dates=set()
    for w in windows.values():all_dates.update(pd.date_range(w['start'],pd.Timestamp(w['end_exclusive'])-pd.Timedelta(days=1),freq='D').strftime('%Y-%m-%d'))
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        d=members(e,g,t);m=model(g,t);dest=RUN/f'{g}_{t}';x=design(d,m['preprocessor'],m['block']);y=target(d,t);eta=predict_eta(d,m)
        assert set(m['training_ids'])==set(d[ID]);assert np.array_equal(eta,predict_eta(d,read(dest/'full_model.json')))
        cv=read(dest/'cluster_covariance.json');one=sm.OLS(y,x).fit();covinfo={}
        for key,gr in [('LAD_CR1',d.LAD21CD),('date_CR1',d.new_date_utc)]:
            check=cov_cluster(one,pd.factorize(gr)[0]);actual=np.array(cv[key]);assert np.allclose(actual,check,rtol=1e-5,atol=1e-8)
            ncl=gr.nunique();covinfo[key]={'clusters':int(ncl),'factor':ncl/(ncl-1)*(len(d)-1)/(len(d)-x.shape[1]),'effective_k':x.shape[1],'max_against_statsmodels':float(np.max(np.abs(actual-check)))}
        ng=(d.LAD21CD+'|'+d.new_date_utc).nunique();covinfo['intersection']={'clusters':int(ng),'factor':ng/(ng-1)*(len(d)-1)/(len(d)-x.shape[1])}
        for key in ['LAD_CR1','date_CR1','LAD_date_two_way_CR1']:
            arr=np.array(cv[key]);diag=np.diag(arr);assert np.isfinite(arr).all()
            for j,c in enumerate(m['columns']):coefs.append({'group':g,'target':t,'term':c,'coefficient':m['parameters'][j],'covariance':key,'SE':np.sqrt(diag[j]) if diag[j]>=0 else None,'variance_status':'negative_undefined' if diag[j]<0 else 'valid','n':len(d),'k':len(m['columns']),'model_path':str(dest/'full_model.json')})
        blocks=['control','G'] if t=='E0' else ['control','G','K','GK'];ms=read(dest/'metrics.json');predmain=None
        for b in blocks:
            p=pd.read_csv(dest/f'oof_{b}.csv',float_precision='round_trip');expected=d[[ID,'new_date_utc']].merge(pd.read_csv(CORE/'folds/date_to_fold.csv'),left_on='new_date_utc',right_on='date_utc');expected['y']=target(expected.merge(d[[ID,C,D]],on=ID),t)
            measured=score_oof(p,expected);assert abs(measured['pooled_oof_r2']-ms[b]['pooled_oof_r2'])<1e-12
            for f in range(5):
                fm=read(dest/f'model_fold{f}_{b}.json');ev=d.loc[d[ID].isin(p.loc[p.fold.eq(f),ID])];assert not (set(ev.new_date_utc)&set(fm['training_dates']));pp=p.set_index(ID).loc[ev[ID]].prediction_eta.to_numpy();assert np.allclose(predict_eta(ev,fm),pp,rtol=0,atol=1e-12)
                assert fm['training_n']+len(ev)==len(d)
            metrics.append({'version':'B1','group':g,'target':t,'block':b,'n':len(d),'pooled_R2':ms[b]['pooled_oof_r2'],'mean_fold_R2':ms[b]['mean_fold_r2'],'SSE':ms[b]['pooled']['SSE'],'SST':ms[b]['pooled']['SST'],'scale':m['target_scale']})
            if b==m['block']:predmain=p
        minimum=read(dest/'conditional_minimum_no_CI.json');physical=physical_gust_terms(m,m['preprocessor']['mean']['pressure_msl_0h'])
        checks.append({'group':g,'target':t,'n':len(d),'LAD':d.LAD21CD.nunique(),'dates':d.new_date_utc.nunique(),'rank':m['rank'],'k':len(m['columns']),'archive_predict_passed':True,'all_OOF_members_predict_passed':True,'two_way_negative_diagonal':cv['negative_diagonal'],'two_way_min_eigenvalue':cv['two_way_min_eigenvalue'],'covariance_factors':covinfo,'minimum':minimum,'physical':physical,'in_sample_R2':score(y,eta)['r2'],'OOF_log_MAE':float(np.mean(np.abs(predmain.y-predmain.prediction_eta))),'OOF_log_RMSE':float(np.sqrt(np.mean((predmain.y-predmain.prediction_eta)**2))),'train_mean_baseline_RMSE':float(np.sqrt(np.mean((predmain.y-predmain.training_mean_baseline)**2)))})
        for c in [C,D,'gust_0h','stage_row_count']:
            vals=d[c].astype(float);descs.append({'group':g,'target':t,'variable':c,'n':len(d),'mean':vals.mean(),'median':vals.median(),'p1':vals.quantile(.01),'p99':vals.quantile(.99),'max':vals.max(),'missing_first_stage_n':int(d.min_stage_ge2.sum()),'missing_first_stage_pct':100*d.min_stage_ge2.mean()})
    populations={'event_master':e,'main_candidate_E0':members(e,'main','E0'),'main_candidate_R0c':members(e,'main','R0c'),'weather_candidate_E0':members(e,'weather','E0'),'weather_candidate_R0c':members(e,'weather','R0c')}
    for g in ['main','weather']:
      for t in ['E0','R0c']:populations[f'{g}_{t}_actual_fit']=e.loc[e[ID].isin(model(g,t)['training_ids'])]
    for name,d in populations.items():
        mask=pd.DataFrame({key:d.new_time_utc.ge(pd.Timestamp(w['start']))&d.new_time_utc.lt(pd.Timestamp(w['end_exclusive'])) for key,w in windows.items()},index=d.index)
        for win,v in [(k,mask[k]) for k in mask]+[('UNIQUE_ANY',mask.any(axis=1))]:
            z=d.loc[v];storms.append({'population':name,'window':win,'events':len(z),'denominator_events':len(d),'events_pct':100*len(z)/len(d),'customers_sum':z[C].sum(min_count=1),'customers_nonmissing_n':z[C].notna().sum(),'denominator_customers_sum':d[C].sum(min_count=1),'customers_pct':100*z[C].sum()/d[C].sum(),'duration_mean_hours':z[D].mean(),'gust_max_ms':z.gust_0h.max(),'overlap_events':int(mask.sum(axis=1).ge(2).sum()),'summed_window_memberships':int(mask.sum().sum()),'UTC_window_days_unique':len(all_dates),'timezone':'UTC','end_rule':'exclusive next-day midnight'})
    table(Q/'tables/core_metrics.csv',pd.DataFrame(metrics));table(Q/'tables/full_coefficients_CR1.csv',pd.DataFrame(coefs));table(Q/'tables/descriptive_statistics.csv',pd.DataFrame(descs));table(Q/'tables/storm_statistics.csv',pd.DataFrame(storms))
    save(Q/'checks/core_actual_acceptance.json',{'passed':True,'four_groups':checks,'all_folds_complete':True,'formal_core_fits':70,'formal_fit_breakdown':{'nested_OOF':60,'full':4,'stage':4,'development_period':2},'calendar_reference':'UTC','true_process_holdout':False})
    print(pd.DataFrame(metrics).to_string(index=False),flush=True)
if __name__=='__main__':run()
