"""Bounded checks for APP-C-COMPLETE, not a historical numerical audit."""
import unittest
import warnings
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from analysis_new.appendix import c_models as cm
from analysis_new.appendix.c_completion import reuse,full_metrics

class CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limits=threadpool_limits(limits=1);cls.data=cm.samples()
    @classmethod
    def tearDownClass(cls):cls.limits.restore_original_limits()
    def test_final_samples_and_original_fold_identity(self):
        self.assertEqual({k:len(v) for k,v in self.data.items()},dict(E0_all=60437,E0_weather=9857,R0c_all=51173,R0c_weather=9254))
        for d in self.data.values():
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                old=d.LAD21CD.unique();np.random.default_rng(cm.SEED).shuffle(old)
            mapping=dict(zip(old,np.arange(len(old))%5))
            np.testing.assert_array_equal(d.LAD_fold,d.LAD21CD.map(mapping))
    def test_original_design_identity(self):
        d=self.data['E0_weather'].sample(1000,random_state=1)
        for m in cm.MODELS[:12]:
            a,b,_=cm.matrices(d.iloc[:800],d.iloc[800:],'E0_weather',m)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',pd.errors.PerformanceWarning)
                x,z=cm.DESIGN(d.iloc[:800],d.iloc[800:],m['form'],False)
            pd.testing.assert_frame_equal(a,x);pd.testing.assert_frame_equal(b,z)
    def test_no_test_labels_or_covariates_in_training_selection(self):
        d=self.data['R0c_weather'].sample(1800,random_state=2);tr=d.iloc[:1400];va=d.iloc[1400:]
        for mid in ['F04','F06','F07','F08']:
            m=next(m for m in cm.MODELS if m['model_id']==mid)
            a,b,k=cm.matrices(tr,va,'R0c_weather',m)
            changed=va.copy();changed['y']=1e8;changed['gust_0h']+=100
            x,z,j=cm.matrices(tr,changed,'R0c_weather',m)
            pd.testing.assert_frame_equal(a,x);self.assertEqual(k,j)
    def test_common_controls_identical(self):
        d=self.data['R0c_weather'].sample(1000,random_state=3)
        base=None
        for m in cm.MODELS[14:]:
            a,_,_=cm.matrices(d,d,'R0c_weather',m,[13.] if m['form']=='single' else [14.,26.])
            controls=a.drop(columns=[c for c in a if c.startswith(('gust_','log_gust','z_gust_')) and c!='z_gust_precip'])
            if base is None:base=controls
            else:pd.testing.assert_frame_equal(controls,base)
    def test_reuse_not_old_recovery(self):
        for m in cm.MODELS[:12]:
            r=reuse('R0c_all',m)
            if m['model_id']!='H05':self.assertFalse(r)
            else:self.assertIn('final_models/final_summary.json',r['in_sample']['path'])
        self.assertNotIn('LAD_OOF',reuse('R0c_weather',next(m for m in cm.MODELS if m['model_id']=='F06')))
    def test_saved_coefficients_reproduce_compatible_full_scores(self):
        for combo,d in self.data.items():
            for m in cm.MODELS:
                r=reuse(combo,m)
                if 'coefficients' not in r:continue
                a,_,_=cm.matrices(d,d,combo,m,r.get('knots',[]));s=r['coefficients']
                co=pd.read_excel(cm.ROOT/s['path'],sheet_name=s['sheet']) if 'sheet' in s else pd.read_csv(cm.ROOT/s['path'])
                beta=co.set_index('term').coef;self.assertEqual(set(beta.index),set(a.columns))
                v=full_metrics(d.y.to_numpy(),a.shape[1],r['in_sample']['value'])
                self.assertAlmostEqual(np.sqrt(np.mean((a.to_numpy()@beta.reindex(a.columns)-d.y)**2)),v['rmse'],places=9)

if __name__=='__main__':unittest.main()
