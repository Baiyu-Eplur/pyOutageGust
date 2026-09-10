"""Complete Appendix C components, with immutable source reuse and keyed cache."""
from datetime import datetime
import json
import inspect
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from threadpoolctl import threadpool_limits
from .catalog import ROOT, MAIN, E0, R0, REQUIREMENTS, C_SOURCES
from .mapping import digest, write_json
from .exporters import table
from . import c_models as cm

def now():return datetime.now().astimezone().isoformat(timespec='seconds')
def read(p):return json.loads((ROOT/MAIN/p).read_text(encoding='utf-8'))
def csv(path,d):
    path.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(path,index=False,float_format='%.17g',compression={'method':'gzip','mtime':0} if path.suffix=='.gz' else None)
def source(p,field,value):return dict(path=MAIN+p,field=field,value=value)

def reuse(combo,m):
    """Component-level decisions based on inspected sample, formula and CV code."""
    margin,scope=combo.split('_');mid=m['model_id'];f=m['form'];out={}
    w=read('weather_only/weather_only_summary.json')[margin]
    fin=read('final_models/final_summary.json')[margin]
    ramp=read('model_selection/ramp_model'+('_R0c' if margin=='R0c' else '')+'.json')[scope]
    if m['family']=='historical' and f in cm.SPECS:
        if combo=='E0_all':
            p='model_selection/E0_model_comparison.csv';v=pd.read_csv(ROOT/MAIN/p).set_index('spec').loc[f].to_dict()
            out['in_sample']=source(p,f,v)
            out['coefficients']={'path':MAIN+'model_selection/E0_coefficients.xlsx','sheet':f[:31]}
            for typ,col in [('LAD_OOF','cv_lad'),('random_OOF','cv_random'),('year_holdout','cv_year')]:out[typ]=source(p,f+'/'+col,v[col])
        elif mid=='H05':
            p='final_models/final_summary.json' if scope=='all' else 'weather_only/weather_only_summary.json'
            v={'bic':fin['paper_bic'],'adj_r2':fin['paper_adj_r2']} if scope=='all' else w['fits']['paper']
            out['in_sample']=source(p,margin+('/paper' if scope=='all' else '/fits/paper'),v)
            out['LAD_OOF']=source(p,margin+'/paper_cv_lad' if scope=='all' else margin+'/fits/paper/cv_lad',fin['paper_cv_lad'] if scope=='all' else v['cv_lad'])
            if scope=='all':out['year_holdout']=source(p,margin+'/paper_cv_year',fin['paper_cv_year'])
            else:out['coefficients']={'path':MAIN+f'weather_only/{margin}_weather_paper_twoway.csv'}
    elif mid in ['H13','H14']:
        name='one_knot' if mid=='H13' else 'two_knot'
        if combo=='E0_all':
            p='model_selection/knots.json';d=read(p)['E0'];v=d[name].copy();out['in_sample']=source(p,'E0/'+name,v)
            out['LAD_OOF']=source(p,'E0/nested_cv/rmse_'+name,d['nested_cv']['rmse_'+name])
            out['knots']=[v['k1']] if mid=='H13' else [v['k1'],v['k2']]
        elif scope=='weather':
            p='weather_only/weather_only_summary.json';k=w['knots'];out['knots']=[k['one_knot']] if mid=='H13' else k['two_knot']
            out['in_sample']=source(p,margin+'/knots/'+name,{'simplified_bic':k['one_bic' if mid=='H13' else 'two_bic']})
    elif m['family']=='matched':
        p='model_selection/ramp_model'+('_R0c' if margin=='R0c' else '')+'.json'
        if margin=='E0' and f in ['quadratic','free_two','plateau']:
            key={'quadratic':'quadratic','free_two':'two_hinge','plateau':'ramp'}[f]
            out['LAD_OOF']=source(p,scope+'/nested_cv/'+key,ramp['nested_cv'][key])
            if f=='free_two':
                v=ramp['two_hinge'];out['in_sample']=source(p,scope+'/two_hinge',{'simplified_bic':v['bic']});out['knots']=[v['k1'],v['k2']]
        if (f=='plateau' and margin=='E0') or (f=='quadratic' and combo=='R0c_all') or (f=='single' and combo=='R0c_weather'):
            p='final_models/final_summary.json' if scope=='all' else 'weather_only/weather_only_summary.json'
            v=fin if scope=='all' else w['fits']['final']
            out['in_sample']=source(p,margin+('/final' if scope=='all' else '/fits/final'),v)
            out['coefficients']={'path':MAIN+(f'final_models/{margin}_final_twoway.csv' if scope=='all' else f'weather_only/{margin}_weather_final_twoway.csv')}
            if f=='plateau':out['knots']=fin['knots'] if scope=='all' else w['knots']['selected']
            if f=='single':out['knots']=w['knots']['selected']
            if combo=='R0c_all':out['LAD_OOF']=source(p,margin+'/final_cv_lad',fin['final_cv_lad'])
    # knots.json uses simplified BIC whereas ladder/final/weather fits use full Gaussian BIC.
    if mid in ['H13','H14'] and 'in_sample' in out:
        v=out['in_sample']['value']
        if 'bic' in v:v['simplified_bic']=v.pop('bic')
    return out

def desired(m):return ['in_sample','LAD_OOF','random_OOF','year_holdout'] if m['form'] in cm.SPECS else ['in_sample','LAD_OOF']

def freeze(stage,datasets):
    (stage/'logs').mkdir(parents=True,exist_ok=True)
    definitions=[];coverage=[];sample_records=[]
    for combo,d in datasets.items():
        sample=cm.token(d[cm.ID].astype(str).tolist());fold=cm.token(d[['LAD_fold','cv_fold_v3','incident_year']].fillna(-999).to_dict('list'))
        sample_records.append(dict(combination=combo,n=len(d),lads=d.LAD21CD.nunique(),zero_customers=int(d[cm.C].eq(0).sum()),
            source=E0 if combo.startswith('E0') else R0,source_sha256=digest(ROOT/(E0 if combo.startswith('E0') else R0)),
            sample_id_sha256=sample,fold_sha256=fold,response='log1p_customers_v2' if combo.startswith('E0') else 'log_duration_B_full_span_hours',
            filtering='accepted curated E0; no additional filter' if combo.startswith('E0') else 'accepted curated R0c; customers > 0',
            scope_filter='cause_group_official == weather_natural' if combo.endswith('weather') else 'none',
            missing_random_folds=int(d.cv_fold_v3.isna().sum())))
        ids=d[[cm.ID,'LAD21CD','incident_date_utc','LAD_fold','cv_fold_v3','incident_year','y',cm.C]].rename(columns={cm.ID:'observation_id'})
        csv(stage/f'data/samples/{combo}.csv.gz',ids)
        for m in cm.MODELS:
            definitions.append(cm.definition(combo,m,d));r=reuse(combo,m)
            parts={typ:('REUSE' if typ in r else 'REFIT') for typ in desired(m)}
            coverage.append(dict(combination=combo,model_id=m['model_id'],status='REFIT' if 'REFIT' in parts.values() else 'REUSE',
                components=json.dumps(parts),reason='same final sample/formula/scales/CV verified; only missing components computed',
                existing_sources=json.dumps(r,ensure_ascii=False),sample_id_sha256=sample,fold_sha256=fold))
    codefiles=['analysis_new/appendix/c_models.py','analysis_new/appendix/c_completion.py','analysis_new/model_selection.py',
        'analysis_new/final_models.py','analysis_new/weather_only_regression.py','analysis_new/knot_estimation.py','analysis_new/plateau_model.py','analysis_new/basis_solver.py','analysis_new/appendix/design_adapter.py']
    protocol=dict(task='APP-C-COMPLETE',frozen_at=now(),seed=cm.SEED,models=cm.MODELS,samples=sample_records,
        candidate_universe='12 literal SPECS + Table 3 one/two free hinges; 8 existing gust forms under final controls; historical weather and D references separately',
        exploratory_screen='hinge_search.py fixed 14/16/18/16+26/14+20+26 are preliminary grid illustrations, not the formal Table 3 ladder; no new grid search/screening included',
        primary_validation='5 LAD folds; shuffle LAD appearance order with seed20260908; same folds within each combination',
        additional_validation='only original 12 ladder: supplied random5 and leave-one-incident-year-out; do not pool designs',
        preprocessing='train-only means/sample SD; train calendar/LAD levels; train percentile cuts; train SSE knot selection',
        metric='pooled row RMSE on log response; full Gaussian OLS AIC/BIC; rank(X), excludes residual variance and selected knots as legacy code',
        simplified_bic_conversion='BIC_full = BIC_simplified + n*(log(2*pi)+1); SSE=n*exp((BIC_full-k*log(n))/n-log(2*pi)-1)',
        fixed_source_knots='existing globally selected fixed-knot CV only in separate reference table, not renamed nested',
        no_other_work='no bootstrap/profile audit, no cause/sample change, no other appendix analyses, no Word modification',
        known_source_issue='R0c D nested quadratic retains gust-pressure; D ramp/free remove it. Matched F uses current final gust-precip for every gust form; no cross-control attribution.',
        code_sha256={p:digest(ROOT/p) for p in codefiles},source_sha256={p:digest(ROOT/p) for p in C_SOURCES})
    write_json(stage/'logs/protocol.json',protocol)
    csv(stage/'logs/coverage_before.csv',pd.DataFrame(coverage));csv(stage/'data/candidate_definitions.csv',pd.DataFrame(definitions))
    return protocol,coverage,pd.DataFrame(definitions)

def full_metrics(y,k,v):
    n=len(y);v=v.copy();k=int(v.get('k',k))
    if 'sse' in v:sse=v['sse']
    elif 'rmse_in' in v:sse=n*v['rmse_in']**2
    else:
        bic=v['bic'] if 'bic' in v else v['simplified_bic']+n*(np.log(2*np.pi)+1)
        sse=n*np.exp((bic-k*np.log(n))/n-np.log(2*np.pi)-1)
    ll=-n/2*(np.log(2*np.pi)+1+np.log(sse/n));r2=1-sse/np.sum((y-y.mean())**2)
    return dict(n=n,k=k,sse=float(sse),aic=float(-2*ll+2*k),bic=float(-2*ll+k*np.log(n)),
        r2=float(r2),adj_r2=float(1-(1-r2)*(n-1)/(n-k)),rmse=float(np.sqrt(sse/n)))

def compute_one(folder,combo,d,m,protocol,force,previous):
    # Presentation edits do not invalidate numerical work; all fitting/reuse
    # functions and legacy design/solver sources do. Full source file hashes
    # remain in the run protocol as the broader code-version record.
    numeric_code={k:v for k,v in protocol['code_sha256'].items() if not k.endswith('c_completion.py')}
    numeric_code['completion_numeric_functions']=cm.token([inspect.getsource(f) for f in [reuse,desired,full_metrics,compute_one]])
    cfg=dict(sample=next(v for v in protocol['samples'] if v['combination']==combo),model=m,seed=cm.SEED,
             code=numeric_code,sources=protocol['source_sha256'],numpy=np.__version__,pandas=pd.__version__,statsmodels=sm.__version__)
    key=cm.token(cfg);old=previous/'result.json'
    if not force and old.exists():
        cached=json.loads(old.read_text());valid=cached.get('cache_key')==key and all((previous/p).is_file() and digest(previous/p)==h for p,h in cached.get('files',{}).items())
        if valid and cached.get('files'):
            shutil.copytree(previous,folder);cached['cache_used']=True;write_json(folder/'result.json',cached);return cached
    folder.mkdir(parents=True,exist_ok=True);r=reuse(combo,m);y=d.y.to_numpy();records=[];diagnostics=[]
    for typ in desired(m):
        if typ in r and typ!='in_sample':
            records.append(dict(prediction_type=typ,n=int(d.cv_fold_v3.notna().sum()) if typ=='random_OOF' else len(d),rmse=float(r[typ]['value']),
                component_action='REUSE',source=r[typ]['path']+'#'+r[typ]['field'],predictions_saved=False,knots_mode='train_selected' if m['form'] in ['single','free_two','plateau'] else 'none_or_fixed10.8'))
            continue
        if typ=='in_sample':
            a,_,knots=cm.matrices(d,d,combo,m,r.get('knots') if typ in r else None)
            if typ in r:
                k=int(r[typ]['value'].get('k',a.shape[1]));v=full_metrics(y,k,r[typ]['value']);action='REUSE'
                if 'coefficients' in r:
                    spec=r['coefficients'];co=(pd.read_excel(ROOT/spec['path'],sheet_name=spec['sheet']) if 'sheet' in spec else pd.read_csv(ROOT/spec['path']))
                    beta=co.set_index('term').coef
                    if set(beta.index)!=set(a.columns):raise ValueError(f'Coefficient design mismatch {combo} {m}: {set(beta.index)^set(a.columns)}')
                    p=a.to_numpy()@beta.reindex(a.columns).to_numpy()
                    if not np.isclose(np.mean((p-y)**2),v['sse']/len(y),rtol=2e-10,atol=1e-12):raise ValueError('Reused beta/full statistic mismatch')
                    csv(folder/'in_sample.csv.gz',pd.DataFrame({'observation_id':d[cm.ID],'y':y,'prediction':p,'prediction_type':typ}))
                    csv(folder/'coefficients.csv',co[['term','coef']]);action='DERIVE'
            else:
                fit=sm.OLS(y,a).fit();v=full_metrics(y,int(fit.df_model+1),{'sse':float(fit.ssr)})
                csv(folder/'coefficients.csv',pd.DataFrame({'term':a.columns,'coef':fit.params.to_numpy()}))
                csv(folder/'in_sample.csv.gz',pd.DataFrame({'observation_id':d[cm.ID],'y':y,'prediction':fit.fittedvalues,'prediction_type':typ}));action='REFIT'
            records.append(dict(prediction_type=typ,**v,n_columns=a.shape[1],knots=json.dumps(knots),component_action=action,
                source=r[typ]['path']+'#'+r[typ]['field'] if typ in r else 'APP-C-COMPLETE',predictions_saved=(folder/'in_sample.csv.gz').exists(),knots_mode='full_sample_selected' if knots else 'none_or_fixed10.8'))
            diagnostics.append(dict(prediction_type=typ,fold='full',**cm.preprocessing(d,combo.startswith('R0c'),a.columns,knots),rank=v['k'],status='source_metrics_reused' if typ in r else 'OLS_pinv_finite'))
            continue
        col={'LAD_OOF':'LAD_fold','random_OOF':'cv_fold_v3','year_holdout':'incident_year'}[typ]
        predictions=np.full(len(d),np.nan);foldrows=[]
        for fold in sorted(d[col].dropna().unique()):
            test=d[col].eq(fold).to_numpy();train=(~test)&(d[col].notna().to_numpy() if typ=='random_OOF' else True)
            a,b,knots=cm.matrices(d.loc[train],d.loc[test],combo,m)
            assert set(d.loc[train,cm.ID]).isdisjoint(d.loc[test,cm.ID])
            assert np.isfinite(a.to_numpy()).all() and np.isfinite(b.to_numpy()).all()
            fit=sm.OLS(y[train],a).fit();p=b.to_numpy()@fit.params.to_numpy();predictions[test]=p
            assert np.isfinite(p).all() and np.isfinite(fit.ssr)
            foldrows.append(dict(fold=float(fold),n_test=int(test.sum()),n_train=int(train.sum()),sse=float(np.sum((p-y[test])**2)),rmse=float(np.sqrt(np.mean((p-y[test])**2))),k=int(fit.df_model+1)))
            diagnostics.append(dict(prediction_type=typ,fold=float(fold),**cm.preprocessing(d.loc[train],combo.startswith('R0c'),a.columns,knots),
                test_ids_sha256=cm.token(d.loc[test,cm.ID].astype(str).tolist()),rank=int(fit.df_model+1),train_sse=float(fit.ssr),
                coefficients=fit.params.to_dict(),status='OLS_pinv_finite'))
        mask=d[col].notna().to_numpy();assert np.isfinite(predictions[mask]).all() and np.isnan(predictions[~mask]).all()
        ptab=pd.DataFrame({'observation_id':d.loc[mask,cm.ID],'y':y[mask],'prediction':predictions[mask],'fold':d.loc[mask,col],'prediction_type':typ})
        csv(folder/(typ+'.csv.gz'),ptab);csv(folder/(typ+'_folds.csv'),pd.DataFrame(foldrows))
        score=float(np.sqrt(np.mean((predictions[mask]-y[mask])**2)))
        assert np.isclose(score,np.sqrt(sum(x['sse'] for x in foldrows)/sum(x['n_test'] for x in foldrows)),rtol=1e-13)
        records.append(dict(prediction_type=typ,n=int(mask.sum()),rmse=score,component_action='REFIT',source='APP-C-COMPLETE',predictions_saved=True,
            knots_mode='train_selected' if m['form'] in ['single','free_two','plateau'] else 'none_or_fixed10.8'))
    write_json(folder/'preprocessing.json',diagnostics)
    files={p.name:digest(p) for p in folder.iterdir() if p.is_file()}
    result=dict(combination=combo,model_id=m['model_id'],family=m['family'],cache_key=key,cache_used=False,configuration=cfg,metrics=records,files=files)
    write_json(folder/'result.json',result);return result

def references(datasets):
    rows=[];ws=read('weather_only/weather_only_summary.json');fs=read('final_models/final_summary.json')
    for combo,d in datasets.items():
        margin,scope=combo.split('_')
        if scope=='weather':
            for spec,v in ws[margin]['fits'].items():
                form='quadratic' if spec=='paper' else 'plateau' if margin=='E0' else 'single hinge'
                rows.append(dict(combination=combo,model_id='W_'+spec,n=len(d),formula=form,controls='M5 non-gust blocks + gust-pressure, no temperature squared' if spec!='final' else 'final controls; see candidate definitions',
                    bic=v['bic'],LAD_RMSE=v['cv_lad'],year_RMSE=None,knots_mode='global selected knots fixed in CV' if spec!='paper' else 'no knots',
                    source=MAIN+'weather_only/weather_only_summary.json#'+margin+'/fits/'+spec,status='REUSE',
                    correspondence='H05' if spec=='paper' else 'F08 full fit only' if spec=='final' and margin=='E0' else 'F06 full fit only' if spec=='final' else 'historical weather build; differs from free-two'))
        else:
            v=fs[margin];rows.append(dict(combination=combo,model_id='MAIN_final',n=len(d),formula='plateau' if margin=='E0' else 'quadratic',controls='final',
                bic=v['bic'],LAD_RMSE=v['final_cv_lad'],year_RMSE=v['final_cv_year'],knots_mode='global selected knots fixed in CV' if margin=='E0' else 'no knots',
                source=MAIN+'final_models/final_summary.json#'+margin,status='REUSE',correspondence='F08 full fit only' if margin=='E0' else 'F01'))
        p='model_selection/ramp_model'+('_R0c' if margin=='R0c' else '')+'.json';ramp=read(p)[scope]
        for name,score in ramp['nested_cv'].items():
            saved=ramp.get(name,{})
            rows.append(dict(combination=combo,model_id='D_'+name,n=ramp['n'],formula=name,
                controls='M5 + temp squared' if margin=='E0' or name=='quadratic' else 'M5 + temp squared - gust-pressure (no gust-precip)',
                bic=None,source_simplified_bic=saved.get('bic'),full_sample_k1=saved.get('k1'),full_sample_k2=saved.get('k2'),
                LAD_RMSE=score,year_RMSE=None,knots_mode='train_selected' if name!='quadratic' else 'no knots',source=MAIN+p+'#'+scope+'/nested_cv/'+name,status='REUSE',
                correspondence={'quadratic':'F01','ramp':'F08','two_hinge':'F07'}[name] if margin=='E0' else 'separate original controls, not matched F ranking'))
    return pd.DataFrame(rows)

def export(stage,results,coverage,definitions,protocol):
    req={r['requirement_id']:r for r in REQUIREMENTS if r['appendix']=='C'}
    definitions=definitions.rename(columns={'exact_columns':'design_columns_template'}).copy()
    single=definitions.form.eq('single')
    definitions.loc[single,'design_columns_template']=definitions.loc[single,'design_columns_template'].str.replace('gust_hinge_13','gust_hinge_k (training-selected)',regex=False)
    rows=[];component=[]
    for r in results:
        full=next(v for v in r['metrics'] if v['prediction_type']=='in_sample')
        row=dict(combination=r['combination'],model_id=r['model_id'],family=r['family'],**{k:full.get(k) for k in ['n','k','n_columns','aic','bic','adj_r2','rmse','knots']},
                 full_action=full['component_action'],full_source=full['source'],sample_id_sha256=r['configuration']['sample']['sample_id_sha256'],
                 status='complete',cache_used=r['cache_used'])
        for v in r['metrics']:
            component.append(dict(combination=r['combination'],model_id=r['model_id'],**v))
            if v['prediction_type']!='in_sample':
                typ=v['prediction_type'];row[typ+'_RMSE']=v['rmse'];row[typ+'_n']=v['n'];row[typ+'_action']=v['component_action'];row[typ+'_source']=v['source'];row[typ+'_knots']=v['knots_mode']
        rows.append(row)
    metrics=pd.DataFrame(rows)
    for (combo,family),g in metrics.groupby(['combination','family']):
        # Full Gaussian likelihood same sample; FE kept separate reference below.
        nonfe=g[g.model_id!='H11'];metrics.loc[g.index,'delta_BIC_best_nonFE']=g.bic-nonfe.bic.min();metrics.loc[g.index,'delta_AIC_best_nonFE']=g.aic-nonfe.aic.min()
    csv(stage/'data/component_metrics.csv',pd.DataFrame(component))
    table(stage,'C_CANDIDATE_DEFINITIONS',definitions,req['C01'])
    table(stage,'C_SAMPLE_DEFINITIONS',pd.DataFrame(protocol['samples']),req['C01'])
    cov=pd.DataFrame(coverage);cov['completed_components']=cov.apply(lambda x:json.dumps({v['prediction_type']:v['component_action'] for r in results if r['combination']==x.combination and r['model_id']==x.model_id for v in r['metrics']}),axis=1)
    cov['completion']='complete';table(stage,'C_COVERAGE_MATRIX',cov,req['C04'])
    pivot=cov.pivot(index='model_id',columns='combination',values='status').reset_index();table(stage,'C_COVERAGE_OVERVIEW',pivot,req['C04'])
    table(stage,'C_HISTORICAL_LADDER',metrics[metrics.family.eq('historical')],req['C02'])
    table(stage,'C_GUST_FUNCTION_COMPARISON',metrics[metrics.family.eq('matched')],req['C03'])
    table(stage,'C_LAD_FE_COMPARISON',metrics[metrics.model_id.isin(['H05','H11'])],req['C03'])
    refs=references(cm.samples());table(stage,'C_EXISTING_FIXED_AND_D_REFERENCES',refs,req['C03'])
    # Current coverage includes source-only identities with actual applicability.
    refcov=[]
    for mid in refs.model_id.unique():
        for combo in cm.COMBOS:
            v=refs[(refs.model_id==mid)&(refs.combination==combo)]
            refcov.append(dict(model_id=mid,combination=combo,status='REUSE' if len(v) else 'NOT_APPLICABLE',
                reason=v.iloc[0]['correspondence'] if len(v) else 'source branch defined only for all or weather; corresponding current model is separately registered',
                source=v.iloc[0]['source'] if len(v) else '',n=int(v.iloc[0]['n']) if len(v) else None))
    table(stage,'C_REFERENCE_COVERAGE',pd.DataFrame(refcov),req['C04'])
    plot(stage,metrics,req)
    return metrics,pd.DataFrame(component)

def plot(stage,metrics,req):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from scripts.final_combined_analysis.figure_style import apply_style,panel_label
    apply_style();fig,axes=plt.subplots(2,2,figsize=(7.28,5.6))
    data=metrics[metrics.family.eq('matched')].copy();csv(stage/'data/C_PERFORMANCE_FIGURE.csv',data)
    for ax,combo,label in zip(axes.flat,cm.COMBOS,['(a) E0 all','(b) R0c all','(c) E0 weather','(d) R0c weather']):
        d=data[data.combination.eq(combo)].sort_values('model_id');base=d.loc[d.model_id.eq('F01'),'LAD_OOF_RMSE'].iloc[0]
        ax.axvline(0,color='.6',linewidth=.8);ax.scatter(d.LAD_OOF_RMSE-base,np.arange(len(d)),s=22)
        ax.set_yticks(np.arange(len(d)),cm.FORMS);ax.invert_yaxis();ax.set_xlabel('LAD pooled RMSE minus quadratic');panel_label(ax,label,x=0,y=1.04)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    fig.tight_layout(h_pad=2);(stage/'figures').mkdir(exist_ok=True);fig.savefig(stage/'figures/C_GUST_PERFORMANCE.png',dpi=400,bbox_inches='tight');plt.close(fig)

def verify(stage,results,protocol):
    checks=[]
    for sample in protocol['samples']:
        d=pd.read_csv(stage/f"data/samples/{sample['combination']}.csv.gz",float_precision='round_trip')
        checks.append(dict(check='sample_unique_and_fold_consistent',combination=sample['combination'],passed=bool(d.observation_id.is_unique and d.groupby('LAD21CD').LAD_fold.nunique().max()==1),n=len(d)))
    for result in results:
        folder=stage/'data/models'/result['combination']/result['model_id'];sample=pd.read_csv(stage/f"data/samples/{result['combination']}.csv.gz",float_precision='round_trip').set_index('observation_id')
        for metric in result['metrics']:
            typ=metric['prediction_type'];path=folder/(typ+'.csv.gz')
            if path.exists():
                d=pd.read_csv(path,float_precision='round_trip');expected=sample.loc[d.observation_id]
                assert d.observation_id.is_unique and np.array_equal(d.y.to_numpy(),expected.y.to_numpy())
                rmse=float(np.sqrt(np.mean((d.prediction-d.y)**2)));assert np.isclose(rmse,metric['rmse'],rtol=2e-10,atol=1e-12)
                if typ!='in_sample':
                    col={'LAD_OOF':'LAD_fold','random_OOF':'cv_fold_v3','year_holdout':'incident_year'}[typ];assert np.array_equal(d.fold.to_numpy(),expected[col].to_numpy())
                checks.append(dict(check='saved_predictions_ids_labels_folds_pooled_RMSE',combination=result['combination'],model_id=result['model_id'],prediction_type=typ,passed=True,rmse=rmse,n=len(d)))
    assert all(c['passed'] for c in checks)
    write_json(stage/'logs/technical_checks.json',dict(passed=True,checks=checks,
        scope='new or parameter-derived predictions independently re-read and recomputed; source-only CV scores checked for compatibility, not re-audited',
        preprocessing='cm.matrices receives training rows plus test covariates; knots solver receives tr.y only; saved training IDs/statistics/coefficients',
        source_only_prediction_limitation='original compatible CV provides pooled score, not per-row OOF; not refitted solely to duplicate an already compatible score'))

def generate(stage,source_checks,previous,force=False):
    bad=[c for c in source_checks if not c['passed']]
    if bad:raise ValueError('C source verification failed: '+str(bad))
    with threadpool_limits(limits=1):
        datasets=cm.samples();protocol,coverage,definitions=freeze(stage,datasets)
        # Freeze is persisted before the first call to a fitting routine.
        with (ROOT/'LOG.md').open('a',encoding='utf-8') as log:
            log.write(f'\n## {now()} — APP-C-COMPLETE 执行配置冻结\n- 四组合实际n：{ {k:len(v) for k,v in datasets.items()} }；22个可计算候选×4。候选/组件REUSE或REFIT已写入C暂存logs/protocol.json、coverage_before.csv（成功后随C事务发布）。\n- 未调用拟合前冻结完成；仅原12项补原random/LAD/year，其余正式函数补LAD训练折结点选择；D仅引用。force={force}。\n')
        results=[];events=[now()+' protocol frozen before fitting']
        for combo,d in datasets.items():
            for m in cm.MODELS:
                print(f'{now()} C {combo} {m["model_id"]} {m["form"]}',flush=True)
                result=compute_one(stage/'data/models'/combo/m['model_id'],combo,d,m,protocol,force,previous/'data/models'/combo/m['model_id'])
                results.append(result);events.append(now()+f' {combo}/{m["model_id"]} '+('cache verified' if result['cache_used'] else 'components completed'))
        metrics,components=export(stage,results,coverage,definitions,protocol);verify(stage,results,protocol)
    summary(stage,metrics,components,results,protocol)
    (stage/'logs/execution.log').write_text('\n'.join(events)+'\n'+now()+' validated before transaction publication\n',encoding='utf-8')
    inputs={c['path']:c['actual_sha256'] for c in source_checks}
    outputs=[]
    for p in sorted(stage.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(stage).as_posix();rid='C01' if any(k in rel for k in ['DEFINITIONS','protocol']) else 'C04' if any(k in rel for k in ['COVERAGE','COMPLETE','checks']) else 'C02' if 'HISTORICAL' in rel else 'C03'
        outputs.append(dict(path=rel,sha256=digest(p),bytes=p.stat().st_size,requirement_id=rid,claim_id='CL_'+rid,
            source_paths=list(inputs),source_sha256=inputs,producer='analysis_new.appendix.c_completion',export_function='generate',configuration={'protocol':'logs/protocol.json'},status='已生成'))
    manifest=dict(owner='main_appendix.py',appendix='C',last_attempt=now(),status='success',update_state='本次已更新',
        requirements={r['requirement_id']:'已生成' for r in REQUIREMENTS if r['appendix']=='C'},outputs=outputs,
        managed_files=sorted([v['path'] for v in outputs]+['manifest.json']),protocol_sha256=digest(stage/'logs/protocol.json'),
        cache_hits=sum(r['cache_used'] for r in results),computed_cells=len(results),component_actions=components.component_action.value_counts().to_dict())
    write_json(stage/'manifest.json',manifest);return manifest

def summary(stage,metrics,components,results,protocol):
    counts=components.component_action.value_counts().to_dict();lines=[];fe_lines=[]
    for combo in cm.COMBOS:
        d=metrics[(metrics.combination==combo)&(metrics.family=='matched')];best=d.loc[d.LAD_OOF_RMSE.idxmin()]
        selected='F08' if combo.startswith('E0') else 'F01' if combo.endswith('all') else 'F06';s=d[d.model_id.eq(selected)].iloc[0]
        bicbest=d.loc[d.bic.idxmin()]
        lines.append(f'- {combo}：当前主函数对应{selected}，LAD RMSE={s.LAD_OOF_RMSE:.10f}；本表最小{best.model_id}={best.LAD_OOF_RMSE:.10f}，绝对差={s.LAD_OOF_RMSE-best.LAD_OOF_RMSE:.10f}。当前BIC={s.bic:.8f}，本组最低{bicbest.model_id}={bicbest.bic:.8f}，差={s.bic-bicbest.bic:.8f}。条件相同；含结点模型此处使用训练折重选。')
        fe=metrics[(metrics.combination==combo)&metrics.model_id.isin(['H05','H11'])].set_index('model_id')
        fe_lines.append(f'- {combo}：H05→H11，样本内调整R² {fe.loc["H05","adj_r2"]:.8f}→{fe.loc["H11","adj_r2"]:.8f}；LAD RMSE {fe.loc["H05","LAD_OOF_RMSE"]:.10f}→{fe.loc["H11","LAD_OOF_RMSE"]:.10f}。')
    text=['# Appendix C 完成说明',f'生成于{now()}。APP-C-COMPLETE仅更新C，正文模型不变。',
        '## C.1 比较设计与候选身份',
        '四组实际样本：'+str({v['combination']:v['n'] for v in protocol['samples']})+'。观测ID、响应、源哈希和折号见data/samples及C_SAMPLE_DEFINITIONS。恢复仅沿用正式管线customers>0，未凑样本数量。',
        '原12项来自model_selection.SPECS，导师design与本地函数一致。H01–H12按原顺序；Table 3另有H13单自由结点、H14自由双结点。F01–F08依次为二次、三次、log1p阵风、百分位阶梯、固定10.8单结点、训练单结点、自由双结点、平台，采用当前最终控制项。完整公式列与训练规则见C_CANDIDATE_DEFINITIONS。',
        '天气原paper=H05；hinge在E0实际是11/24平台（无温度平方），R0是11单结点（保留gust-pressure、无温度平方）；final在E0增加温度平方，在R0为11单结点+温度平方+gust-precip。不能仅凭hinge名称将其视作自由双结点。',
        'Table 3映射：quadratic H05、cubic H06、log H07、steps H09、one H13、two H14、plateau+temperature² F08（E0）、LAD FE H11。原Table 3恢复列是59834条，当前C更新为51173条；旧数值仅为历史来源，不作当前排名。hinge_search早期固定网格示意不是正式阶梯，不扩大为新搜索。',
        '## C.2 协变量阶梯',
        'C_HISTORICAL_LADDER完整保留每组合12项及Table 3两种自由结点。原12项的随机、LAD、按年三种CV分别列出；H01–H05逐步增加阵风平方、gust-pressure、社会变量、日历，其余7项是原替代规格，并非新增全排列消融。所有恢复候选均含标准化log1p客户数及平方。',
        '## C.3 同控制条件的阵风函数比较',
        'C_GUST_FUNCTION_COMPARISON保持相同样本、非阵风协变量及交互：E0含温度平方和gust-pressure；R0含温度平方和gust-precip（去gust-pressure）。主阵风平台约束仅针对主函数，保留交互时并非所有压力/降水值下总效应均平台。AIC/BIC为完整Gaussian OLS，参数计数rank(X)，按原约定不计残差方差和搜索的结点位置；因此是既定条件惩罚口径，不是对全部搜索自由度的独立校正。分组差值只在同组合/同表层内计算。',
        *lines,
        '全体暴露的现有平台在本次同控制表中同时取得最低BIC和LAD误差，提供相应比较支持。其余三组的现有函数并非LAD误差最小；天气暴露平台仍为BIC最小，而最终正客户全体恢复的若干分段候选BIC低于当前二次规格。样本外误差差距的绝对量已逐项给出，不能将它们改写成所有现有主函数均胜出，也未进行不确定性推断或自动替换模型。',
        '## C.4 地区固定效应与选择证据',
        'C_LAD_FE_COMPARISON比较H05与H11。LAD固定效应在样本内可吸收地区差异，留出整个LAD时按原编码规则将未见LAD虚拟变量置零；未为使其失败改变参考水平或编码。k为秩，另存列数，秩亏用原statsmodels伪逆。样本内拟合优劣与LAD外推优劣不等价。',
        *fe_lines,
        '原D恢复nested二次比较保留gust-pressure，但同表ramp/free模型去除了该项且未增加gust-precip；因此其微小得分差不能全归于阵风函数。C_EXISTING_FIXED_AND_D_REFERENCES保留原值与控制项，F表另用统一最终控制。未改写D或重做bootstrap/profile审计。',
        '## 复用、补算与缺口',
        f'88个可计算候选×组合单元全部完成；逐组件动作计数{counts}（DERIVE为从兼容系数生成样本内预测，未重估；计数含复用的原始组件，缓存重复导出不算新增拟合）。本次缓存命中{sum(r["cache_used"] for r in results)}单元。参考表另有天气3项、全体最终及D三项比较，适用性见C_REFERENCE_COVERAGE。',
        'C04已关闭：四组均有同最终样本的原12阶梯与原三种CV。可复用部分未重复拟合；当前历史阶梯的新正客户恢复结果不可与原含零客户结果作同测试集胜负比较。训练折预处理、参数、结点和新增逐行预测在data/models，池化评分已从保存文件复算。原兼容CV仅保存汇总分数而无逐行预测的组件继续引用源路径/指纹，不假称已恢复逐行预测；这不影响C的同定义得分表，不能将其当作后续G/I现成逐行输入。',
        '当前函数是否最小随组合而异，见上方完整原值及CSV，不因运行成功证明主模型，也不因小幅排名自动换模型。需人工判断的是如何表述最终样本上的更新排序，以及原D恢复控制项不一致对原比较措辞的限制；不涉及自动主模型选择。',
        '## 运行与文件',
        '`python main_appendix.py --appendices C`：验证源、样本/规格/折/代码缓存键，复用有效缓存重新导出。`python main_appendix.py --appendices C --recompute-c`：忽略C新计算缓存，重新计算缺失组件；仍直接复用兼容历史结果。`--check-only`只读。结果固定C目录，事务替换保留人工文件。',
        '表图清单见manifest.json及根figure_table_register.csv；logs/protocol.json与coverage_before.csv为拟合前冻结，technical_checks.json为必要技术核验，execution.log记录逐候选完成。没有修改正文、其他附录原产物或历史研究输出，没有新天气、ZIP或远程发布。']
    (stage/'README.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
    (stage/'logs/APP_C_COMPLETE.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
