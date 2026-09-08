"""Tests exercise known R03 errors, not old scientific conclusions."""
import unittest,json,tempfile,importlib.util,os
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from contracts import *
from producer import *
from prediction import *
from diagnostics import *

def synthetic(n=300):
    r=np.random.default_rng(20260905);d=pd.DataFrame({ID:[f'test_{i}' for i in range(n)],'new_date_utc':[f'2022-01-{i%25+1:02}' for i in range(n)],'new_year':2022,'new_month':1,'LAD21CD':['L'+str(i%17) for i in range(n)],'cause_group_event':np.where(np.arange(n)%3==0,'weather_natural','technical_asset'),'stage_row_count':r.integers(1,9,n)})
    for c in WX:d[c]=r.normal(10,2,n)
    d['pressure_msl_0h']=r.normal(1010,8,n);d['precipitation_24h_sum']=r.uniform(0,30,n)
    for c in REGION:d[c]=r.normal(0,1,n)
    d['urban_binary']=r.integers(0,2,n);d[C]=r.integers(0,1000,n);d[D]=np.exp(r.normal(1,1,n));d['new_time_utc']=pd.to_datetime(d.new_date_utc,utc=True)
    return d

class PipelineTests(unittest.TestCase):
    def test_input_real_manifest_and_no_fallback(self):
        config=read(ROOT/'configs/R04_primary.json');d,m=load_events(config);self.assertEqual(len(d),135025)
        bad=dict(config,input_manifest=str(ROOT/'checks/absent_manifest.json'))
        with self.assertRaises(FileNotFoundError):load_events(bad)
        bad=dict(config,input_manifest_sha256='incorrect')
        with self.assertRaises(ValueError):load_events(bad)
    def test_shared_dates_and_shuffle(self):
        d=synthetic();a=global_date_folds(d);b=global_date_folds(d.sample(frac=1,random_state=2));pd.testing.assert_frame_equal(a,b)
        main=attach_folds(d,a);weather=attach_folds(d[d.cause_group_event.eq('weather_natural')],a)
        self.assertTrue(weather.fold.eq(weather[ID].map(main.set_index(ID).fold)).all());self.assertTrue(main.groupby('new_date_utc').fold.nunique().eq(1).all())
    def test_test_tail_does_not_leak_training_or_scaler(self):
        d=synthetic();d=attach_folds(d,global_date_folds(d));trainmain=d[d.fold.ne(0)];test=d[d.fold.eq(0)].copy()
        tr,meta=training_population(trainmain,'main','R0c','main_train_p99');prep=fit_preprocessor(tr,'R0c');model=fit_ols(tr,prep,'GK',{'tail':meta})
        test[D]=1e12;test['gust_0h']=1e6;tr2,meta2=training_population(trainmain,'main','R0c','main_train_p99')
        self.assertEqual(meta,meta2);self.assertEqual(prep,fit_preprocessor(tr2,'R0c'));self.assertEqual(len(predict_eta(test,model)),len(test))
        wt,wmeta=training_population(trainmain,'weather','R0c','main_train_p99');self.assertEqual(meta['threshold_hours'],wmeta['threshold_hours'])
    def test_oof_complete_unique_and_paired_blocks(self):
        d=synthetic();mapping=global_date_folds(d);cfg={'n_splits':5,'training_tail':'all_valid','run_id':'synthetic','purpose':'non_inferential_smoke','input_version':'synthetic'}
        r=run_oof(d,mapping,'main','R0c',cfg)
        for frame in r['predictions'].values():self.assertEqual(len(frame),len(d));self.assertTrue(frame[ID].is_unique)
        p=r['predictions']['GK'];expected=r['expected']
        with self.assertRaises(ValueError):score_oof(p.iloc[1:],expected)
        with self.assertRaises(ValueError):score_oof(pd.concat([p,p.iloc[:1]]),expected)
        self.assertEqual(set(r['contributions']),{'gust_from_control','customers_from_control','gust_given_customers','customers_given_gust'})
    def test_pooled_hand_calculation_negative_constant(self):
        a=score([1,2,3],[1,2,2]);self.assertEqual(a['SSE'],1);self.assertEqual(a['SST'],2);self.assertEqual(a['r2'],.5)
        self.assertLess(score([1,2,3],[10,10,10])['r2'],0);self.assertIsNone(score([2,2],[1,3])['r2'])
    def test_eta_zero_double_log_removed(self):
        d=synthetic();prep=fit_preprocessor(d,'E0');m=fit_ols(d,prep,'G',{})
        m['parameters']=[0.]*len(m['parameters']);eta=predict_eta(d,m)
        self.assertTrue(np.array_equal(eta,np.zeros(len(d))));self.assertEqual(aggregate_eta([0])['mean_eta'],0)
        self.assertNotEqual(aggregate_eta([0])['mean_eta'],float(np.log(2)))
    def test_raw_scenario_square_interaction_and_reference_mean(self):
        d=synthetic();prep=fit_preprocessor(d,'R0c');m=fit_ols(d,prep,'GK',{})
        scenario=set_scenario(d,m,{'customers_at_training_log_center':True,'gust_0h':prep['mean']['gust_0h'],'pressure_msl_0h':prep['mean']['pressure_msl_0h']});x=design(scenario,prep,'GK')
        self.assertTrue(np.allclose(x.zK2,0,atol=1e-20));self.assertTrue(np.allclose(x.zG_zPressure,0,atol=1e-20))
        original=design(d,prep,'GK');self.assertGreater(original.zK2.mean(),.9)
        self.assertAlmostEqual(predict_eta(d,m).mean(),float(original.mean().to_numpy()@np.asarray(m['parameters'])))
        a=aggregate_eta([0.,2.]);self.assertNotEqual(a['exp_mean_eta'],a['mean_exp_eta'])
    def test_archive_roundtrip_and_unknown_categories(self):
        d=synthetic();prep=fit_preprocessor(d,'R0c');m=fit_ols(d,prep,'GK',{});reloaded=json.loads(json.dumps(m));self.assertTrue(np.array_equal(predict_eta(d,m),predict_eta(d,reloaded)))
        d.new_year=2099
        with self.assertRaises(ValueError):predict_eta(d,m)
    def test_no_new_result_no_old_figure_or_interval(self):
        with self.assertRaises(FileNotFoundError):require_result(ROOT/'checks/missing_model.json','R04')
        d=synthetic();p=fit_preprocessor(d,'E0');m=fit_ols(d,p,'G',{'run_id':'smoke','purpose':'non_inferential_smoke'})
        path=ROOT/'checks/synthetic_model.json';save_json(path,m,ROOT)
        with self.assertRaises(ValueError):require_result(path,'smoke')
        mi=minimum_interface(m,1010,[0,50]);self.assertIsNone(mi['interval'])
    def test_cluster_covariance_against_frozen_statsmodels(self):
        import statsmodels.api as sm
        from statsmodels.stats.sandwich_covariance import cov_cluster,cov_cluster_2groups
        d=synthetic();p=fit_preprocessor(d,'R0c');m=fit_ols(d,p,'GK',{});x=design(d,p,'GK');fit=sm.OLS(target(d,'R0c'),x).fit();cov=covariance_producer(d,m)
        self.assertTrue(np.allclose(cov['LAD_CR1'],cov_cluster(fit,d.LAD21CD),rtol=1e-7,atol=1e-9))
        groups=np.column_stack([pd.factorize(d.LAD21CD)[0],pd.factorize(d.new_date_utc)[0]])
        self.assertTrue(np.allclose(cov['LAD_date_two_way_CR1'],cov_cluster_2groups(fit,groups)[0],rtol=1e-7,atol=1e-9))
    def test_vif_and_stage_producers(self):
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        d=synthetic();p=fit_preprocessor(d,'R0c');x=design(d,p,'GK');v,meta=vif_table(x)
        expected=[variance_inflation_factor(x.to_numpy(),i) for i in range(1,x.shape[1])]
        self.assertTrue(np.allclose(v.VIF,expected,rtol=1e-7));self.assertEqual(meta['design_rank'],x.shape[1])
        tab,pool,info=stage_composition(d);self.assertEqual(tab['count'].sum(),len(d));self.assertEqual(pool['count'].sum(),len(d))
    def test_storm_unique_union_with_mixed_fit_identity(self):
        d=synthetic();p=fit_preprocessor(d,'E0');m=fit_ols(d.iloc[:200],p,'G',{'tail':{}})
        windows={'A':{'start':'2022-01-01Z'.replace('01Z','01T00:00Z'),'end_exclusive':'2022-01-05T00:00Z'},'B':{'start':'2022-01-03T00:00Z','end_exclusive':'2022-01-08T00:00Z'}}
        result=storm_event_predictions(d,m,windows);self.assertTrue(result[ID].is_unique);self.assertTrue(result.window_count.gt(1).any());self.assertTrue((~result.was_in_this_fit).any())
        self.assertTrue(np.allclose(result.y,np.log1p(d.set_index(ID).loc[result[ID],C])))
    def test_old_output_path_rejected(self):
        with self.assertRaises(ValueError):save_json(WORK.parent/'results/forbidden.json',{},WORK.parent/'results')
    def test_regional_reference_common_calendar(self):
        d=synthetic();p=fit_preprocessor(d,'R0c');m=fit_ols(d,p,'GK',{})
        reg=d.drop_duplicates('LAD21CD')[['LAD21CD','new_year',*REGION]];cal=pd.DataFrame({'new_year':[2022],'new_month':[1],'weight':[1.]})
        out=regional_reference(reg,cal,m);self.assertEqual(len(out),17);self.assertTrue(out.status.eq('descriptive_common_calendar').all())
    def test_stage_closure_raw_log_archive(self):
        d=synthetic();table,models,bins,info=stage_closure(d,{'purpose':'non_inferential_smoke'})
        self.assertEqual(info['stage_transform'],'natural log raw; not standardized')
        augmented=models[1];x=design(d,augmented['preprocessor'],'GK');self.assertTrue(np.array_equal(x.log_n_stages,np.log(d.stage_row_count)))
        self.assertTrue(np.array_equal(predict_eta(d,augmented),predict_eta(d,json.loads(json.dumps(augmented)))))
    def test_calendar_period_rank_failure_not_silent_fit(self):
        from retained import period_comparison
        d=synthetic();d['new_period']=np.where(np.arange(len(d))<100,'development','later')
        d['new_year']=2022;d['new_month']=1
        later=d.new_period.eq('later');d.loc[later,'new_year']=np.where(np.arange(later.sum())%2==0,2023,2024);d.loc[later,'new_month']=np.where(d.loc[later,'new_year'].eq(2023),10,2)
        rows,models=period_comparison(d,'E0',{},1010)
        self.assertEqual(rows.loc[rows.period.eq('later'),'status'].iloc[0],'blocked_calendar_design_rank_deficient');self.assertEqual(len(models),1)
    def test_fresh_import_has_no_writes_or_legacy_modules(self):
        import subprocess,sys
        code='''import sys,os,platform
from pathlib import Path
r=Path(sys.argv[1]);sys.path.insert(0,str(r/'runtime/site-packages'));sys.path.insert(0,str(r/'src'))
# Windows stdlib platform discovery may read `cmd /c ver`; complete that
# OS metadata probe before guarding research/numerical module imports.
platform.uname()
def audit(event,args):
 if event=='open':
  mode,flags=args[1],args[2]
  if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):raise RuntimeError('write on import')
 if event in {'os.mkdir','os.remove','os.rename','socket.connect','subprocess.Popen'}:raise RuntimeError('side effect on import')
sys.addaudithook(audit)
import producer,contracts,prediction,diagnostics,retained,run_pipeline
paths=[Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and not str(m.__file__).startswith('<')]
assert all(p.is_relative_to(r) for p in paths)
print('pure isolated imports passed')
'''
        out=subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(ROOT)],capture_output=True,text=True)
        self.assertEqual(out.returncode,0,out.stderr)
