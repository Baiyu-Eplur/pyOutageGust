"""Read-only, scoped verification of APP-GI-PRED saved outputs (no fitting).

Run: python -X utf8 -B test/verify_gi_outputs.py
All output is JSON on stdout; shell redirection may save the receipt.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import numpy as np
from analysis_new.appendix.gi_core import cm,design,ROOT
from analysis_new.appendix.f02_cov import read,js
from analysis_new.appendix.mapping import digest

def main():
    g=ROOT/'results/Appendix/G';i=ROOT/'results/Appendix/I';checks={}
    data=read(g/'data/GI_PREDICTIONS.csv.gz');samples=cm.samples();prep=js(g/'data/GI_PREPROCESSING.json')
    groups={k:v for k,v in data.groupby(['combination','model_id','prediction_type'],sort=False)}
    # Rebuild each saved full/fold design from its documented training rows and
    # multiply SAVED beta, never call OLS.fit or tune a knot.
    differences=[]
    for p in prep:
        d=samples[p['combination']];kind=p['prediction_type'];spec=p['model_id'];fold=p['fold']
        tr=d if fold==-1 else d[d.LAD_fold.ne(fold)]
        va=d if fold==-1 else d[d.LAD_fold.eq(fold)]
        assert cm.token(tr[cm.ID].astype(str).tolist())==p['train_ids_sha256']
        for c,mu in p['means'].items():assert np.isclose(tr[c].mean(),mu,atol=1e-12)
        for c,sd in p['sample_sd_ddof1'].items():assert np.isclose(tr[c].std(ddof=1),sd,atol=1e-12)
        _,X=design(tr,va,p['combination'],spec);X=X.reindex(columns=p['columns'],fill_value=0.)
        stored=groups[(p['combination'],spec,kind)].set_index('observation_id').loc[va[cm.ID]]
        assert np.allclose(stored.y,va.y,atol=1e-12)
        if fold!=-1:assert stored.fold.eq(fold).all() and not set(tr.LAD21CD)&set(va.LAD21CD)
        delta=float(np.max(abs(X.to_numpy()@np.asarray(p['beta'])-stored.prediction.to_numpy())))
        assert delta<1e-8,(p['combination'],spec,fold,delta)
        differences.append(delta)
    checks['saved_parameter_components_recomputed']=len(differences)
    checks['largest_saved_prediction_abs_difference']=max(differences)
    # Independent direct score formulas, all saved groups, including control.
    metrics=read(g/'tables/GI_PREDICTION_METRICS.csv')
    for r in metrics.itertuples():
        v=groups[(r.combination,r.model_id,r.prediction_type)];error=v.prediction.to_numpy()-v.y.to_numpy()
        assert len(v)==r.n
        assert np.isclose(np.sqrt(np.dot(error,error)/len(v)),r.rmse,atol=1e-12)
        assert np.isclose(np.mean(abs(error)),r.mae,atol=1e-12)
        assert np.isclose(np.mean(error),r.bias,atol=1e-12)
    checks['pooled_metrics_groups_recomputed']=len(metrics)
    curves=read(g/'data/GI_RESPONSE_CURVES.csv');ncurves=0
    for d in js(g/'data/GI_CURVE_VARIANCE_CHECKS.json'):
        combo,spec=d['combination'],d['model_id'];a=read(g/f'data/GI_{combo}_{spec}_CURVE_DESIGN.csv').drop(columns=['grid_index','gust'])
        V=read(g/f'data/GI_{combo}_{spec}_COV.csv').set_index('term').loc[a.columns,a.columns].to_numpy()
        var=np.sum((a.to_numpy()@V)*a.to_numpy(),axis=1)
        s=curves[curves.combination.eq(combo)&curves.model_id.eq(spec)]
        assert np.allclose(var,s.variance,atol=1e-12,rtol=1e-10);ncurves+=1
    checks['actual_curve_variances_recomputed']=ncurves
    storm=read(i/'data/GI_STORM_PREDICTIONS.csv.gz');sm=read(i/'tables/GI_STORM_METRICS.csv')
    for r in sm.itertuples():
        v=storm[storm.storm.eq(r.storm)&storm.combination.eq(r.combination)&storm.prediction_type.eq(r.prediction_type)]
        e=v.prediction.to_numpy()-v.y.to_numpy()
        assert len(v)==r.n and np.isclose(np.sqrt(np.dot(e,e)/len(v)),r.rmse,atol=1e-12)
        assert v.excluded_from_primary_metrics.eq(r.prediction_type=='display_only').all()
    u=storm[storm.storm.eq('UNION_DEDUPLICATED')]
    prior=storm[~storm.storm.eq('UNION_DEDUPLICATED')].drop_duplicates(['combination','prediction_type','observation_id'])
    key=['combination','prediction_type','observation_id']
    assert sorted(map(tuple,u[key].to_numpy()))==sorted(map(tuple,prior[key].to_numpy()))
    checks['storm_metrics_groups_recomputed']=len(sm);checks['storm_union_exact']=True
    snapshot=js(ROOT/'docs/new_analysis/GI_PROTECTED_SNAPSHOT.json')
    changed=[p for p,h in snapshot.items() if not (ROOT/p).exists() or digest(ROOT/p)!=h]
    checks['protected_file_count']=len(snapshot);checks['protected_changes']=changed;assert not changed
    for letter in ['G','I']:
        out=ROOT/'results/Appendix'/letter;m=js(out/'manifest.json')
        assert all(digest(out/v['path'])==v['sha256'] for v in m['outputs'])
    checks['manifest_hashes_match']=True
    print(json.dumps(dict(passed=True,checks=checks,scope='saved current GI outputs only; no fits, significance tests, historical audit or independent scientific review'),indent=2))

if __name__=='__main__':main()
