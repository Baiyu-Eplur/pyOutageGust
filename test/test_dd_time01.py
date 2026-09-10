"""Bounded technical tests for the fixed temporal split, without source-data fitting."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from analysis_new.temporal_fragility import (TARGETS, read_period, frozen_edges,
    fit_development, evaluate_frozen, score)
from analysis_new.dd_agg01_evaluation import calibration


def frame(dates,labels):
    return pd.DataFrame(dict(LAD21CD=['A']*len(dates),date=dates,gust=np.arange(len(dates))+10.,
                             **{t:labels for t in TARGETS}))


class TemporalTests(unittest.TestCase):
    def test_period_selection_before_label_conversion(self):
        data=frame(['2023-09-29','2023-09-30'],[0,'poison-evaluation-label'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'panel.csv'; data.to_csv(path,index=False)
            selected=read_period(path,'development')
            self.assertEqual(selected.date.tolist(),['2023-09-29'])
            self.assertEqual(selected.any_gt0.tolist(),[0])
            with self.assertRaises(ValueError): read_period(path,'evaluation')
            data.loc[1,TARGETS]=1; data.to_csv(path,index=False)
            self.assertEqual(read_period(path,'evaluation').date.tolist(),['2023-09-30'])

    def test_only_development_rows_can_fit(self):
        data=frame(['2023-09-28','2023-09-29'],[0,1])
        def stub(g,y):
            np.testing.assert_array_equal(y,[0,1])
            return dict(theta=30.,beta=.4,p0=.01,nll=2.,valid=True,message='stub',selection_reason='test'),[]
        with patch('analysis_new.temporal_fragility.fit',side_effect=stub) as fitting:
            fits,_,edges,prob=fit_development(data)
            self.assertEqual(fitting.call_count,8)
            self.assertTrue((fits.development_rate==.5).all())
            self.assertEqual(edges[TARGETS[0]],frozen_edges(prob[TARGETS[0]]))
            data.loc[1,'date']='2023-09-30'
            with self.assertRaises(ValueError): fit_development(data)
            self.assertEqual(fitting.call_count,8)

    def test_frozen_bins_ties_empties_and_probability_endpoints(self):
        edges=frozen_edges(np.array([.2,.2,.2,.2]))
        self.assertEqual(edges,[0.,.2,1.])
        rows,saved=calibration(np.array([0,1]),{'model':np.array([.2,1.])},'test',edges)
        self.assertEqual(saved,edges); self.assertEqual(rows[0]['n'],0)
        self.assertTrue(np.isnan(rows[0]['observed_frequency']))
        self.assertEqual(rows[1]['n'],2); self.assertEqual(rows[1]['events'],1)
        with self.assertRaises(ValueError): calibration(np.array([0]),{'m':np.array([0.])},'t',[0,.2,.2,1])

    def test_saved_baseline_is_not_evaluation_rate_and_months_pool(self):
        data=frame(['2023-09-30','2023-10-01','2023-10-02'],[1,1,0])
        fits=pd.DataFrame([dict(target=t,theta=30.,beta=.4,p0=.01,valid=True,development_rate=.2,message='ok') for t in TARGETS])
        edges={t:[0.,.05,.2,1.] for t in TARGETS}
        pred,metrics,months,bins=evaluate_frozen(data,fits,edges)
        self.assertTrue((pred.baseline_prediction==.2).all())
        self.assertAlmostEqual(metrics.iloc[0].baseline_brier,np.mean((.2-np.array([1,1,0]))**2))
        sub=months[months.target==TARGETS[0]]
        self.assertAlmostEqual(np.average(sub.model_brier,weights=sub.n),metrics.iloc[0].model_brier)
        altered=data.copy(); altered[TARGETS]=0
        pred2,_,_,bins2=evaluate_frozen(altered,fits,edges)
        np.testing.assert_array_equal(pred.prediction,pred2.prediction)
        pd.testing.assert_frame_equal(bins[['lower','upper','n']],bins2[['lower','upper','n']])

    def test_invalid_development_has_no_model_predictions(self):
        data=frame(['2023-09-28','2023-09-29'],[0,0])
        with patch('analysis_new.temporal_fragility.fit') as fitting:
            fits,_,edges,_=fit_development(data); fitting.assert_not_called()
        evaluation=frame(['2023-09-30','2023-10-01'],[1,0])
        pred,metrics,_,_=evaluate_frozen(evaluation,fits,edges)
        self.assertTrue(pred.prediction.isna().all()); self.assertTrue(metrics.model_brier.isna().all())
        self.assertTrue((metrics.baseline_brier==.5).all())
        self.assertTrue(np.isnan(score([0,0],[0,0],0,True)['brier_skill']))

    def test_entry_independent_disabled_and_last(self):
        import main_new
        from analysis_new.runner import STAGES
        self.assertEqual(list(main_new.STEPS)[-1],'dd_time01')
        self.assertEqual(list(main_new.STEPS),STAGES)
        self.assertEqual(len(STAGES),20); self.assertFalse(any(main_new.STEPS.values()))


if __name__=='__main__': unittest.main()
