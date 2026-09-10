"""Fixed retrospective temporal holdout, executed by the existing project runner."""
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

from analysis_new.runner import PROJECT, save, digest, now
from analysis_new.p03_p04_grid_weather import previous_run, verified_output
from analysis_new.fragility_optimizer import RULES
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.temporal_fragility import (PERIODS, read_period, fit_development,
    evaluate_frozen, sample_summary, covariate_support)
from analysis_new.dd_time01_outputs import plots, checks, index


def run_experiment(root,settings):
    out=root/'results/dd_time01'; out.mkdir()
    def event(message,**more):
        record=dict(time=now(),message=message,**more)
        with (out/'execution.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(record,ensure_ascii=False,default=str)+'\n')
        print(f'[{record["time"]}] {message}',flush=True)
    def offline(name,args):
        if name in ['socket.connect','socket.getaddrinfo']:
            raise PermissionError('DD-TIME01 is offline: new requests prohibited')
    sys.addaudithook(offline)
    manifest=dict(task='DD-TIME01',started_at=now(),status='running',settings=settings)
    save(out/'run_manifest.json',manifest)
    try:
        source,sm=previous_run(PROJECT,settings.get('source_run','20260909183317'))
        if sm['status']!='completed': raise ValueError('Source production run must be completed')
        stages={s['stage'] for s in sm['steps'] if s['status']=='completed'}
        if not {'district_day_fragility','report_tables','documents'}<=stages:
            raise ValueError('Source must be the identified complete manuscript production route')
        panel=verified_output(source,sm,'results/final_models/district_day_panel.csv')
        rm=json.loads((root/'run.json').read_text(encoding='utf-8'))
        inputs=[dict(path=str(p),sha256=digest(p)) for p in [panel,source/'run.json']]
        command=os.environ.get('DD_TIME01_ENTRY_COMMAND','python -X utf8 -B main_new.py (only dd_time01=1)')
        protocol=dict(task='DD-TIME01',frozen_at=now(),purpose=rm['purpose'],command=command,
            periods=PERIODS,expected_lads=111,expected_days=1096,expected_rows=121656,
            input_panel=str(panel),source_run=source.name,inputs=inputs,
            source_selection='Current manuscript production route, not newest file or predictive performance; district_day_fragility -> report_tables -> documents in this source run',
            producer='analysis_new/district_day_fragility.py: original panel and final_models/district_day_fragility.json; report_tables reads same-run model JSON -> figures/frag_rows.json -> documents',
            proxy=dict(unit='m/s',variable='gust',event_weather='gust_0h',date='Saved original panel date strings (original UTC day); no timezone conversion',
                centers='Original mean event latitude/longitude per LAD, preserved through original panel',
                interpolation='Original Gaussian 40 km; fewer than 5 weights >1e-3 uses nearest 5 inverse-distance weights 1/(distance+1); original planar 111 km/degree and cos(51.8 degrees); not reconstructed'),
            targets=TARGETS,primary='any_gt100',important_secondary='wthr_gt100',
            labels='Original daily labels unchanged: at least one qualifying incident, not sum customers; any_gt0 is n_inc>0, wthr_gt0 is weather-attributed max customers>=0, both include zero-customer events; other targets strictly >5/>100/>1000 using corresponding daily max',
            model='p0+(1-p0)*Phi((ln(g)-ln(theta))/beta); g=0 limit p0',optimizer=RULES,seed=RULES['seed'],
            fit_scope='Development rows only; 13 established starts and existing finite fallback selected on development NLL; no full-period fit or historical fitted parameters',
            freeze='Fit parameters, development constant rates and bins saved before evaluation labels are loaded; no evaluation fitting, tuning or calibration',
            baseline='Development positive LAD-day fraction for each target, never evaluation event rate',
            metrics='Equal LAD-day evaluation Brier, development-constant Brier, BSS=1-model_Brier/baseline_Brier; means, observed rates and prediction-minus-observed; BSS is not accuracy, R2 or probability percentage points',
            calibration='Unique development fitted probability deciles (numpy linear), add 0/1; searchsorted right with final edge inclusive; empty bins NaN; n<100 isolated; no evaluation-based edges; pooled-OOF edges from prior spatial experiments are not applicable',
            support='Monthly summaries of the same frozen predictions; saved-date partial September included; period gust distribution and evaluation rows outside development range only',
            uncertainty='Descriptive single fixed split; no bootstrap, significance tests, independent-row SE or confidence intervals; no post hoc pass/fail/adoption threshold',
            information_boundary='Retrospective holdout previously explored, not untouched confirmation; same-day incident locations construct proxy. Tests temporal transfer under same post hoc proxy rule, not advance fault forecasting and not removal of anchor dependence',
            forbidden=['historical full-sample/LAD numerical audit','old proxy limit/tail/g50 audit','incident knots versus district probability','anchor coverage/removal','ERA5/aggregation/duration comparisons','new variables/models/spatial validation','precipitation surfaces','weather requests','Word/appendix/revision ledger edits','independent scientific review','adoption report','ZIP/return package'])
        np.random.seed(RULES['seed'])
        save(out/'protocol.json',protocol)
        manifest.update(inputs=inputs,sources=rm['sources'],environment=rm['environment'],command=command,
                        seed=RULES['seed'],switches=rm['switches'],protocol_sha256=digest(out/'protocol.json'))
        save(out/'run_manifest.json',manifest)
        # Before development freeze, inspect only keys, never evaluation labels.
        keys=pd.read_csv(panel,usecols=['LAD21CD','date'],dtype=str)
        dates=pd.to_datetime(keys.date,format='%Y-%m-%d',errors='raise')
        if not dates.dt.strftime('%Y-%m-%d').eq(keys.date).all(): raise ValueError('Unexpected saved date format')
        if keys.isna().any().any() or keys.duplicated().any(): raise ValueError('Missing/duplicate LAD-day keys')
        study=keys.date.between(PERIODS['development'][0],PERIODS['evaluation'][1])
        lads=sorted(keys.loc[study,'LAD21CD'].unique())
        expected=pd.MultiIndex.from_product([lads,pd.date_range(PERIODS['development'][0],PERIODS['evaluation'][1]).strftime('%Y-%m-%d')],names=['LAD21CD','date'])
        missing=expected.difference(pd.MultiIndex.from_frame(keys.loc[study]))
        coverage=dict(source_rows=len(keys),actual_lads=len(lads),actual_days=keys.loc[study,'date'].nunique(),
            expected_lads=111,expected_days=1096,expected_rows=121656,
            missing_keys_count=len(missing),missing_keys=[list(k) for k in missing],
            outside_study_rows=int((~study).sum()),outside_study_keys=keys.loc[~study].to_dict('records'),
            handling='No fabricated observations; saved rows only; same LAD sets required in both periods')
        save(out/'input_coverage.json',coverage)
        event('Protocol frozen and original panel verified',coverage=coverage)
        development=read_period(panel,'development')
        event('Development labels loaded; evaluation labels not collected',rows=len(development))
        fits,candidates,edges,dev_predictions=fit_development(development,event)
        fits.to_csv(out/'development_fit.csv',index=False)
        if candidates.empty: candidates=pd.DataFrame(columns=['target','method','start','nll','success','selected'])
        candidates.to_csv(out/'optimizer_candidates.csv.gz',index=False)
        dev_predictions.to_csv(out/'development_probabilities.csv.gz',index=False)
        save(out/'calibration_edges.json',edges)
        times=dict(development_frozen_at=now())
        save(out/'frozen_development.json',dict(frozen_at=times['development_frozen_at'],fits=fits.to_dict('records'),
            edges=edges,development_rows=len(development),development_period=PERIODS['development'],
            development_fit_sha256=digest(out/'development_fit.csv'),development_probabilities_sha256=digest(out/'development_probabilities.csv.gz')))
        freeze_hash=digest(out/'frozen_development.json')
        event('Development parameters and bins frozen',sha256=freeze_hash)
        # Predict from the serialized frozen artifact, not a mutable optimizer result.
        frozen=json.loads((out/'frozen_development.json').read_text(encoding='utf-8'))
        fits=pd.DataFrame(frozen['fits']); edges=frozen['edges']
        evaluation=read_period(panel,'evaluation'); times['evaluation_labels_loaded_at']=now()
        if set(development.LAD21CD)!=set(evaluation.LAD21CD): raise ValueError('Period LAD sets differ; no silent spatial restriction allowed')
        event('Evaluation labels loaded after freeze',rows=len(evaluation))
        pd.DataFrame(sample_summary(development,'development')+sample_summary(evaluation,'evaluation')).to_csv(out/'sample_summary.csv',index=False)
        covariate_support(development,evaluation).to_csv(out/'covariate_support.csv',index=False)
        predictions,metrics,monthly,bins=evaluate_frozen(evaluation,fits,edges)
        for name,frame in [('temporal_predictions.csv.gz',predictions),('temporal_metrics.csv',metrics),
                           ('monthly_metrics.csv',monthly),('calibration_bins.csv',bins)]: frame.to_csv(out/name,index=False)
        plots(out,development,evaluation,dev_predictions,edges,monthly,bins,fits)
        result=checks(out,development,evaluation,fits,candidates,edges,dev_predictions,freeze_hash,times)
        index(out,protocol,result,coverage)
        event('All technical outputs complete',valid_tasks=result['valid_development_tasks'],checks=len(result['checks']))
        manifest.update(status='completed',finished_at=now(),times=times,valid_tasks=result['valid_development_tasks'],
                        invalid_tasks=result['invalid_development_tasks'],technical_checks_passed=result['all_checks_passed'])
        save(out/'run_manifest.json',manifest)
        save(out/'inventory.json',[dict(path=str(p.relative_to(out)).replace('\\','/'),bytes=p.stat().st_size,sha256=digest(p))
                                  for p in sorted(out.rglob('*')) if p.is_file() and p.name!='inventory.json'])
    except BaseException as exc:
        manifest.update(status='failed',finished_at=now(),error=repr(exc)); save(out/'run_manifest.json',manifest)
        event('Technical execution failed',error=repr(exc)); raise


if __name__=='__main__':
    run_experiment(Path(os.environ['NEW_ANALYSIS_RUN']),json.loads(os.environ.get('DD_TIME01_SETTINGS','{}')))
