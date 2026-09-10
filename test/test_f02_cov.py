"""Bounded synthetic checks for F02 covariance reuse and invalid variance handling."""
import unittest
import numpy as np
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from analysis_new.appendix.f02_cov import covariance_from_residuals,inference


class F02CovarianceTest(unittest.TestCase):
    def test_residual_reuse_matches_ols_api_and_two_dimensions(self):
        rng=np.random.default_rng(4402)
        lad=np.repeat(np.arange(12),16);date=np.tile(np.repeat(np.arange(8),2),12)
        X=np.column_stack([np.ones(len(lad)),rng.normal(size=len(lad))])
        y=1+X[:,1]*.4+rng.normal(size=12)[lad]+rng.normal(size=8)[date]+rng.normal(size=len(lad))
        res=sm.OLS(y,X).fit(method='pinv')
        both,cl,cd,ci,bread,sing,direct=covariance_from_residuals(X,res.resid,lad,date)
        actual=cov_cluster_2groups(res,lad,date,use_correction=True)
        for a,b in zip([both,cl,cd],actual):np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-13)
        np.testing.assert_allclose(both,cl+cd-ci,rtol=1e-12,atol=1e-13)
        self.assertFalse(np.allclose(both,ci))
        se,p,lo,hi=inference(res.params,cl,11)
        np.testing.assert_allclose(hi-lo,2*stats.t.ppf(.975,11)*se)
        np.testing.assert_allclose(p,2*stats.t.sf(abs(res.params/se),11))

    def test_negative_variance_remains_missing(self):
        se,p,lo,hi=inference(np.array([1.,2.]),np.diag([-.001,.25]),10)
        self.assertTrue(np.isnan([se[0],p[0],lo[0],hi[0]]).all())
        self.assertEqual(se[1],.5)


if __name__=='__main__':unittest.main()
