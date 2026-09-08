from common import *
from sklearn.model_selection import GroupKFold
from producer import run_oof,publish_oof
from prediction import minimum_interface,physical_gust_terms

def folds(d,datecol):
    out=pd.Series(-1,index=d.index,dtype=int)
    for f,(_,vi) in enumerate(GroupKFold(5).split(d,groups=d[datecol].astype(str))):out.iloc[vi]=f
    return out
def run():
    e=events();H=Q/'frozen/H0';out=Q/'R1_input_compat_v1';assert not out.exists();out.mkdir();checks=[];summary=[];fits=0
    cfg=read(CORE/'configs/R04_primary.json');cfg.update(run_id='R04_R1_input_compat_v1',purpose='R1_historical_compatibility_not_B1',training_tail='all_valid',output_root=str(out),compatibility_tail='pretrim each historical target/group on full input population p99 before splitting; not optional shared training p99',compatibility_cause='old first-row cause',compatibility_fold='independent GroupKFold(5) within each group/target using corrected UTC dates')
    save(Q/'configs/R1_input_compat_v1.json',cfg)
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        # Verify copied sklearn fold implementation reproduces H0 assignment without refitting H0.
        hf=pd.read_csv(H/f'{g}_{t}_folds.csv');hf['computed']=folds(hf,'date');assert np.array_equal(hf.fold,hf.computed)
        d=e.loc[e[f'R1_compat_candidate_{g}_{t}']].copy();d['cause_group_event']=d.old_cause_group;d['fold']=folds(d,'new_date_utc');fm=d[['new_date_utc','fold']].drop_duplicates().rename(columns={'new_date_utc':'date_utc'});d=d.drop(columns='fold');result=run_oof(d,fm,g,t,cfg);dest=out/f'{g}_{t}';publish_oof(result,dest)
        prep=fit_preprocessor(d,t);block='G' if t=='E0' else 'GK';m=fit_ols(d,prep,block,{'run_id':cfg['run_id'],'purpose':cfg['purpose'],'input_version':cfg['input_version'],'group':g,'config_sha256':config_hash(cfg),'producer_sha256':sha(Path(__file__))});save(dest/'full_model.json',m);minimum=minimum_interface(m,prep['mean']['pressure_msl_0h'],np.quantile(d.gust_0h,[.01,.99]));save(dest/'minimum.json',minimum)
        for b,metric in result['metrics'].items():summary.append({'version':'R1','group':g,'target':t,'block':b,'n':len(d),'pooled_R2':metric['pooled_oof_r2'],'mean_fold_R2':metric['mean_fold_r2'],'SSE':metric['pooled']['SSE'],'SST':metric['pooled']['SST'],'scale':m['target_scale']})
        checks.append({'group':g,'target':t,'n':len(d),'H0_fold_reproduction':True,'fold_sha':identity(fm.astype(str).agg('|'.join,axis=1)),'minimum':minimum,'physical':physical_gust_terms(m,prep['mean']['pressure_msl_0h']),'input_vs_protocol':'H0 to R1 changes selected time/WX/annual population and derived members/caps/date folds; R1 to B1 changes tail/common fold/cause rules, not a causal decomposition'});fits+=len(result['models'])+1;print(g,t,len(d),'completed',flush=True)
    table(Q/'tables/R1_metrics.csv',pd.DataFrame(summary));save(Q/'checks/R1_acceptance.json',{'passed':True,'fits':fits,'checks':checks,'optional_training_p99_executed':False})
if __name__=='__main__':run()
