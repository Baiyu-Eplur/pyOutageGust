"""Read-only reproduction checks of C saved data; no fitting or source mutation.

python -X utf8 -B test/verify_appendix_c_saved.py
"""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from analysis_new.appendix.catalog import ROOT,REQUIREMENTS
from analysis_new.appendix.mapping import digest,expected
from analysis_new.appendix.c_models import token

def main():
    root=ROOT/'results/Appendix/C';manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['status']=='success'
    for v in manifest['outputs']:assert digest(root/v['path'])==v['sha256'],v['path']
    planned={p for r in REQUIREMENTS if r['appendix']=='C' for p in expected(r)}
    assert planned<={v['path'] for v in manifest['outputs']}
    components=[];n_predictions=0;n_fits=0;verified_preprocess=0
    for path in sorted((root/'data/models').glob('*/*/result.json')):
        r=json.loads(path.read_text());assert token(r['configuration'])==r['cache_key']
        sample=pd.read_csv(root/f"data/samples/{r['combination']}.csv.gz",float_precision='round_trip')
        assert sample.observation_id.is_unique
        assert token(sample.observation_id.astype(str).tolist())==r['configuration']['sample']['sample_id_sha256']
        for p,h in r['files'].items():assert digest(path.parent/p)==h
        diagnostics=json.loads((path.parent/'preprocessing.json').read_text())
        for row in diagnostics:
            typ=row['prediction_type'];col={'LAD_OOF':'LAD_fold','random_OOF':'cv_fold_v3','year_holdout':'incident_year'}.get(typ)
            mask=pd.Series(True,index=sample.index) if col is None else (sample[col]!=row['fold']) & (sample[col].notna() if typ=='random_OOF' else True)
            assert token(sample.loc[mask,'observation_id'].astype(str).tolist())==row['train_ids_sha256']
            if col:
                assert token(sample.loc[sample[col].eq(row['fold']),'observation_id'].astype(str).tolist())==row['test_ids_sha256']
                assert set(sample.loc[mask,'observation_id']).isdisjoint(sample.loc[sample[col].eq(row['fold']),'observation_id'])
            n_fits+=row['status']=='OLS_pinv_finite';verified_preprocess+=1
        for metric in r['metrics']:
            components.append(metric);p=path.parent/(metric['prediction_type']+'.csv.gz')
            if not p.exists():
                assert metric['component_action'] in ['REUSE','DERIVE'];continue
            d=pd.read_csv(p,float_precision='round_trip');s=sample.set_index('observation_id').loc[d.observation_id]
            assert np.array_equal(d.y,s.y) and np.isfinite(d.prediction).all()
            assert np.isclose(np.sqrt(np.mean((d.y-d.prediction)**2)),metric['rmse'],rtol=2e-10,atol=1e-12)
            n_predictions+=1
    before=json.loads((ROOT/'docs/new_analysis/app_c_complete/protected_before.json').read_text())
    assert all(digest(ROOT/p)==v['sha256'] and (ROOT/p).stat().st_mtime_ns==v['mtime_ns'] for p,v in before.items())
    original={r['path']:r['actual_sha256'] for r in json.loads((ROOT/'results/Appendix/logs/validation.json').read_text())['source_checks']}
    assert all(digest(ROOT/p)==h for p,h in original.items())
    result=dict(passed=True,computed_cells=manifest['computed_cells'],component_actions=pd.Series([v['component_action'] for v in components]).value_counts().to_dict(),
        saved_prediction_files_recomputed=n_predictions,training_partition_records_checked=verified_preprocess,
        saved_new_fits=n_fits,protected_other_appendix_files_unchanged=len(before),source_files_unchanged=len(original),
        cache_hits=manifest['cache_hits'],scope='C sample/ID/fold/parameter partition and saved-score reproduction; byte+mtime protection; no model refit')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
