"""Small discriminating checks for DD-DUR01, no scientific review."""
import unittest
import numpy as np
from scipy.optimize._numdiff import approx_derivative
from analysis_new.duration_features import features,threshold
from analysis_new.fragility_optimizer import Objective,fit,probabilities


class Duration(unittest.TestCase):
    def test_strict_threshold_units_and_zero(self):
        x=np.full((4,24),10.); x[0]=0; x[2]=20; x[3,0]=20
        f=features(x,10.)
        np.testing.assert_array_equal(f.H,[0,0,24,1])
        np.testing.assert_array_equal(f.I,[0,0,24*300,300])
        np.testing.assert_allclose(f.J,[0,0,3,.125])
        np.testing.assert_allclose(f.h,[0,0,1,1/24])
        np.testing.assert_allclose(f.x,np.log1p(f.J))
        with self.assertRaises(ValueError): features(x,0)

    def test_training_only_global_linear_threshold(self):
        x=np.arange(96.).reshape(4,24); train=np.array([True,False,True,False])
        tau=threshold(x,train)
        self.assertEqual(tau,np.quantile(x[train].ravel(),.9,method='linear'))
        changed=x.copy(); changed[~train]=100000
        self.assertEqual(tau,threshold(changed,train))
        duplicated=np.repeat(x[train],2,axis=0)
        self.assertEqual(threshold(duplicated,np.ones(4,dtype=bool)),np.quantile(duplicated,.9,method='linear'))

    def test_nested_zero_gamma_gradient_exact_grouping(self):
        g=np.tile([0.,5.,10.,15.,20.,25.,30.],40); y=(np.arange(len(g))%5==0).astype(float)
        h=np.tile([0.,0.,0.,.1,.5,.7,1.],40)
        for feature in [h,np.log1p(h*2)]:
            a=Objective(g,y); b=Objective(g,y,feature)
            self.assertAlmostEqual(a.nll(a.encode(35,.4,.02)),b.nll(b.encode(35,.4,.02,0)),places=10)
            np.testing.assert_array_equal(probabilities(g,35,.4,.02),probabilities(g,35,.4,.02,0,feature))
            for gamma in [-.6,.6]:
                x=b.encode(35,.4,.02,gamma)
                grad=approx_derivative(lambda v:b.value_gradient(v)[0],x).ravel()
                np.testing.assert_allclose(b.value_gradient(x)[1],grad,rtol=2e-5,atol=1e-7)
                p=probabilities(g,35,.4,.02,gamma,feature)
                raw=-np.sum(y*np.log(p)+(1-y)*np.log1p(-p))
                self.assertAlmostEqual(raw,b.nll(x),places=9)
        self.assertEqual(probabilities(np.array([0.]),35,.4,.02,-2,np.array([0.]))[0],.02)

    def test_extension_reestimates_and_beats_legal_baseline(self):
        rng=np.random.default_rng(1909); g=rng.choice(np.arange(5.,31.),3000)
        h=(g>15)*rng.choice([0.05,.25,.5,.75,1.],3000)
        y=rng.binomial(1,probabilities(g,35,.4,.015,1.2,h))
        baseline,_=fit(g,y); result,records=fit(g,y,feature=h,baseline=baseline)
        self.assertTrue(result['valid'],result)
        self.assertLessEqual(result['nll'],result['baseline_nll']+1e-5)
        starts=[r for r in records if r['method']=='initial']
        self.assertEqual(len(starts),16)
        self.assertEqual(starts[0]['gamma'],0.)
        self.assertTrue(any(r['gamma']<0 for r in starts)); self.assertTrue(any(r['gamma']>0 for r in starts))

    def test_entry_independent_and_disabled(self):
        import main_new
        from analysis_new.runner import STAGES
        self.assertEqual(list(main_new.STEPS)[18],'dd_dur01')
        self.assertEqual(set(main_new.STEPS),set(STAGES))
        self.assertFalse(any(main_new.STEPS.values()))


if __name__=='__main__': unittest.main()
