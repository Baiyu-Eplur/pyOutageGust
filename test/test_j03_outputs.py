"""Synthetic serialization/evaluation/export smoke test; never fits research data."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from analysis_new.appendix.j03_compare import TARGETS, VERSIONS, SCOPES, csv, js, outputs
from analysis_new.fragility_optimizer import probabilities


class J03OutputTest(unittest.TestCase):
    def test_complete_output_pipeline_and_saved_score_checks(self):
        # 111 synthetic groups exercise the fixed draw shape, with unequal
        # source probabilities and explicit empty calibration intervals.
        n=222
        d=pd.DataFrame({'LAD21CD':np.repeat([f'TEST{i:03}' for i in range(111)],2),
                        'date':np.tile(['2000-01-01','2000-01-02'],111),
                        'fold':np.repeat(np.arange(111)%5,2),
                        'PROXY':np.linspace(5,30,n), 'GRID_MAX':np.linspace(6,32,n)})
        for j,t in enumerate(TARGETS):d[t]=(np.arange(n)%(j+3)==0).astype(int)
        oof=d[['LAD21CD','date','fold',*TARGETS]].copy()
        rows=[]
        for t in TARGETS:
            oof[t+'_constant']=oof.fold.map({f:d.loc[d.fold!=f,t].mean() for f in range(5)})
            for v in VERSIONS:
                oof[t+'__'+v]=probabilities(d[v],theta=20,beta=1,p0=.01)
                for s in SCOPES:
                    mask=np.ones(n,bool) if s=='full' else d.fold.to_numpy()!=int(s[-1])
                    rows.append(dict(candidate=v,target=t,scope=s,n=int(mask.sum()),events=int(d.loc[mask,t].sum()),
                                     theta=20.,beta=1.,p0=.01,nll=200.,valid=True,success=True,
                                     projected_gradient=0.,prediction_std=.1,weak_identification=False))
        fits=pd.DataFrame(rows)
        components=fits[['candidate','target','scope','valid','weak_identification']].copy()
        components['action']='SYNTHETIC_TEST_ONLY'
        with tempfile.TemporaryDirectory(prefix='j03-output-test-') as temp:
            p=Path(temp)
            for part in ['data','tables','figures','logs']:(p/part).mkdir()
            js(p/'logs/J03_PROTOCOL.json',{'fixture':'synthetic; not scientific results'})
            csv(p/'data/J03_OOF_PREDICTIONS.csv.gz',oof)
            outputs(p,d,fits,components,oof,lambda *args,**kw:None)
            checks=json.loads((p/'logs/J03_TECHNICAL_CHECKS.json').read_text())
            self.assertTrue(checks['all_passed'])
            for t in TARGETS:self.assertTrue(checks['checks'][t+'_GRID_MAX_score_roundtrip'])
            table=pd.read_csv(p/'tables/J03_PAIRED_METRICS.csv')
            self.assertEqual(len(table),8)
            self.assertTrue((table.delta_brier.abs()>0).any())
            self.assertEqual(len(list((p/'figures').glob('*.png'))),2)
            self.assertTrue((p/'logs/J03_EXECUTION_REPORT.md').exists())


if __name__=='__main__':unittest.main()
