"""Bounded checks for aggregation definitions and stable likelihood, not a broad audit."""
import unittest
import numpy as np
import pandas as pd
from scipy.optimize._numdiff import approx_derivative
from scipy.special import ndtr
from analysis_new.daily_aggregations import aggregate,CANDIDATES
from analysis_new.fragility_optimizer import Objective,fit,probabilities
from analysis_new.dd_agg01_evaluation import calibration


class Definitions(unittest.TestCase):
    def test_constant_ordered_and_separated_peaks(self):
        x=np.full((1,24),7.); np.testing.assert_allclose(aggregate(x),7.)
        x=np.arange(24.)[None,:]; a=aggregate(x)[0]
        self.assertAlmostEqual(a[2],np.quantile(x,.9,method='linear'))
        self.assertEqual(a[4],22.)
        x=np.zeros((2,24)); x[0,[4,5,6]]=30; x[1,[0,10,23]]=30
        a=aggregate(x)
        np.testing.assert_allclose(a[:,3],[30,30]); np.testing.assert_allclose(a[:,4],[30,10])

    def test_midnight_no_wrap_or_cross_day_and_zero(self):
        x=np.zeros((2,24)); x[0,22:]=30; x[1,0]=30
        np.testing.assert_allclose(aggregate(x)[:,4],[20,10])
        np.testing.assert_array_equal(aggregate(np.zeros((1,24))),np.zeros((1,5)))
        with self.assertRaises(ValueError): aggregate(np.zeros((1,23)))

    def test_stable_gradient_and_exact_grouping(self):
        g=np.tile(np.array([0.,1.,4.,9.,14.,21.,28.]),20)
        y=(np.arange(len(g))%3==0).astype(float)
        obj=Objective(g,y); x=obj.encode(18,.4,.1)
        numerical=approx_derivative(lambda v:obj.value_gradient(v)[0],x).ravel()
        np.testing.assert_allclose(obj.value_gradient(x)[1],numerical,rtol=1e-5,atol=1e-7)
        p=probabilities(g,18,.4,.1)
        nll=-np.sum(y*np.log(p)+(1-y)*np.log1p(-p))
        self.assertAlmostEqual(obj.nll(x),nll,places=9)
        self.assertEqual(probabilities(np.array([0.]),18,.4,.1)[0],.1)
        self.assertEqual(probabilities(np.array([0.]),18,.4,0.)[0],0.)

    def test_rare_fit_beats_legal_point_and_constant(self):
        rng=np.random.default_rng(731)
        g=rng.choice(np.arange(.1,36,.1),size=7000)
        p=.0014+.9986*ndtr((np.log(g)-np.log(40))/.27)
        y=rng.binomial(1,p)
        result,candidates=fit(g,y); obj=Objective(g,y)
        self.assertTrue(result['valid'],result)
        self.assertLessEqual(result['nll'],obj.nll(obj.encode(40,.27,.0014))+1e-5)
        self.assertLess(result['nll'],result['constant_nll'])
        self.assertGreaterEqual(len(candidates),26)
        self.assertGreater(result['prediction_std'],1e-8)

    def test_shared_calibration_ties_empty_and_sparse(self):
        y=np.r_[np.zeros(100),1.,1.]
        predictions={'first':np.full(102,.1),'second':np.r_[np.full(100,.2),.8,.8]}
        rows,edges=calibration(y,predictions,'test'); frame=pd.DataFrame(rows)
        self.assertEqual(frame.groupby('candidate').n.sum().tolist(),[102,102])
        first=frame[(frame.candidate=='first') & (frame.n>0)]
        self.assertEqual(len(first),1)  # identical probabilities never split
        self.assertTrue(frame.loc[frame.n==0,'observed_frequency'].isna().all())
        self.assertTrue(frame.loc[frame.n==2,'sparse'].all())
        self.assertEqual(edges[0],0.); self.assertEqual(edges[-1],1.)

    def test_entry_off_and_last(self):
        import main_new
        from analysis_new.runner import STAGES
        self.assertEqual(list(main_new.STEPS)[17],'dd_agg01')
        self.assertEqual(set(main_new.STEPS),set(STAGES))
        self.assertFalse(any(main_new.STEPS.values()))


if __name__=='__main__': unittest.main()
