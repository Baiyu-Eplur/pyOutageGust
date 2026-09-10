"""APP-C-COMPLETE: frozen identities and pure, train-only legacy design adapters.

No source module with import-time analysis is imported. Searches reuse the
original FWL solvers, grids and SSE objective; no bootstrap/profile audit.
"""
import ast
import hashlib
import json
import warnings
import numpy as np
import pandas as pd
from .catalog import ROOT, MAIN, E0, R0
from .design_adapter import load_design_functions
from .exporters import literal
from analysis_new.basis_solver import Solver

SEED = 20260908
ID = 'Incident Reference'
C = 'customers_v2_event_excl_reinterruptions'
SCALE = ['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h']
SOCIO = ['urban_binary','log_population','income_deprivation_rate','deprivation_gap_pct','morans_i']
SPECS = literal('analysis_new/model_selection.py','SPECS')
DESIGN, FINAL = load_design_functions(json.loads((ROOT/MAIN/'model_selection/knots.json').read_text()))
_ctx = {'np':np, 'pd':pd}
_tree = ast.parse((ROOT/'analysis_new/knot_estimation.py').read_text(encoding='utf-8-sig'))
exec(compile(ast.fix_missing_locations(ast.Module(body=[n for n in _tree.body if
    isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'hinge_cols','KnotSolver'}],type_ignores=[])),
    'analysis_new/knot_estimation.py','exec'),_ctx)
KnotSolver = _ctx['KnotSolver']

FORMS = ['quadratic','cubic','log','bins','fixed10.8','single','free_two','plateau']
MODELS = [dict(model_id=f'H{i:02}',family='historical',form=spec,original=spec) for i,spec in enumerate(SPECS,1)]
MODELS += [dict(model_id='H13',family='historical',form='single',original='one free hinge / Table 3'),
           dict(model_id='H14',family='historical',form='free_two',original='two free hinges / Table 3')]
MODELS += [dict(model_id=f'F{i:02}',family='matched',form=form,original='既定阵风函数 + 当前最终控制项') for i,form in enumerate(FORMS,1)]
COMBOS = ['E0_all','R0c_all','E0_weather','R0c_weather']

def token(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def samples():
    result={}
    for margin,path in [('E0',E0),('R0c',R0)]:
        original=pd.read_csv(ROOT/path)
        d=original if margin=='E0' else original.loc[original[C]>0].copy()
        if margin=='R0c': d['customers_v2_log1p']=np.log1p(d[C])
        for scope in ['all','weather']:
            v=(d if scope=='all' else d.loc[d.cause_group_official.eq('weather_natural')]).copy().reset_index(drop=True)
            assert v[ID].notna().all() and v[ID].is_unique
            lads=v.LAD21CD.unique().to_numpy(copy=True);np.random.default_rng(SEED).shuffle(lads)
            v['LAD_fold']=v.LAD21CD.map(dict(zip(lads,np.arange(len(lads))%5)))
            v['y']=v['log1p_customers_v2' if margin=='E0' else 'log_duration_B_full_span_hours']
            assert np.isfinite(v[['y',*SCALE,*SOCIO]].to_numpy()).all()
            result[margin+'_'+scope]=v
    return result

def preprocessing(tr,cust,columns,knots):
    return dict(n_train=len(tr),train_ids_sha256=token(tr[ID].astype(str).tolist()),
        means={c:float(tr[c].mean()) for c in SCALE+(['customers_v2_log1p'] if cust else [])},
        sample_sd_ddof1={c:float(tr[c].std(ddof=1)) for c in SCALE+(['customers_v2_log1p'] if cust else [])},
        gust_quantile_cuts=tr.gust_0h.quantile([.5,.75,.9,.97]).tolist(),
        calendar_levels={c:sorted(tr[c].unique().tolist()) for c in ['incident_year','incident_month']},
        lad_levels=sorted(tr.LAD21CD.unique().tolist()),columns=list(columns),knots=list(knots or []),
        unseen_category_rule='all indicators zero; original omitted reference; OLS pinv for rank deficiency')

def matrices(tr,va,combo,model,knots=None):
    cust=combo.startswith('R0c');form=model['form'];family=model['family']
    if family=='historical' and form in SPECS:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',pd.errors.PerformanceWarning)
            a,b=DESIGN(tr,va,form,cust)
        return a,b,[]
    a,b=DESIGN(tr,va,'M5_+year_month_FE',cust)
    # Controls fixed before looking at candidate scores. Both interaction columns
    # remain raw standardized gust products, regardless of the main gust basis.
    for x,d in [(a,tr),(b,va)]:
        if family=='matched':
            x['z_temperature_sq']=((d.temperature_0h-tr.temperature_0h.mean())/tr.temperature_0h.std(ddof=1))**2
            if cust:
                x.drop(columns='z_gust_pressure',inplace=True)
                x['z_gust_precip']=((d.gust_0h-tr.gust_0h.mean())/tr.gust_0h.std(ddof=1))*((d.precipitation_24h_sum-tr.precipitation_24h_sum.mean())/tr.precipitation_24h_sum.std(ddof=1))
        x.drop(columns=['z_gust_0h','z_gust_sq'],inplace=True)
    if knots is None and form in ['single','free_two','plateau']:
        g=tr.gust_0h.to_numpy();y=tr.y.to_numpy()
        if form=='single':
            # Original single-hinge base keeps a linear gust column.
            x=np.column_stack([a.to_numpy(),(g-tr.gust_0h.mean())/tr.gust_0h.std(ddof=1)])
            solver=KnotSolver(x,g,y,np.arange(8.,35.))
            knots=[min(np.arange(8.,31.),key=lambda k:solver.sse([k]))]
        else:
            solver=Solver(a.to_numpy(),y,g)
            knots=list(min(((x,y) for x in np.arange(8.,21.) for y in np.arange(18.,35.) if y-x>=4),
                           key=lambda ks:solver.at_knots(*ks,tail=form=='free_two')))
    for x,d in [(a,tr),(b,va)]:
        g=d.gust_0h;z=(g-tr.gust_0h.mean())/tr.gust_0h.std(ddof=1)
        if form in ['quadratic','cubic','fixed10.8','single']:
            x['z_gust_0h']=z
        if form in ['quadratic','cubic']: x['z_gust_sq']=z**2
        if form=='cubic':x['z_gust_cu']=z**3
        if form=='log':x['log_gust']=np.log1p(g)
        if form=='bins':
            for i,q in enumerate(tr.gust_0h.quantile([.5,.75,.9,.97])): x[f'gust_ge_q{i}']=(g>=q).astype(float)
        if form in ['fixed10.8','single']:
            for k in ([10.8] if form=='fixed10.8' else knots):x[f'gust_hinge_{k:g}']=np.maximum(g-k,0.)
        if form in ['free_two','plateau']:
            k1,k2=knots;x['gust_low']=np.minimum(g,k1);x['gust_ramp']=np.minimum(np.maximum(g-k1,0.),k2-k1)
            if form=='free_two':x['gust_tail']=np.maximum(g-k2,0.)
    return a,b.reindex(columns=a.columns,fill_value=0.),list(knots or [])

def definition(combo,m,d):
    a,_,_=matrices(d,d,combo,m,knots=[13.] if m['form']=='single' else [14.,26.] if m['form'] in ['free_two','plateau'] else [])
    return dict(combination=combo,**m,response='log(1+customers)' if combo.startswith('E0') else 'log(duration_B_full_span_hours)',
        exact_columns=';'.join(a.columns),controls='current final: temperature squared; E0 gust-pressure / R0 gust-precip' if m['family']=='matched' else 'exact original design; see columns',
        customer_control='standardized log1p(C) + square in every recovery candidate' if combo.startswith('R0c') else 'none',
        scaling='training mean/sample SD ddof=1; socio unscaled; log gust=log1p(raw gust)',
        knots_rule='one 8:30; two k1=8:20,k2=18:34,gap>=4,step=1; train SSE minimum' if m['form'] in ['single','free_two','plateau'] else 'fixed 10.8 or train gust quantiles .50/.75/.90/.97 where applicable',
        validation='LAD / random supplied cv_fold_v3 / leave-one-year-out' if m['form'] in SPECS else 'LAD; knots selected separately in each training fold',
        calendar='train year/month dummy levels, first omitted' if m['family']=='matched' or m['form'] not in SPECS[:4] else 'none',
        lad_effect='train levels, omitted first; unseen LAD all zeros; original pinv' if m['form']=='A6_M5_+LAD_FE' else 'no LAD FE',
        parameter_count='rank(X); variance and selected knot locations excluded, following legacy OLS convention',
        source='analysis_new/model_selection.py; knot_estimation.py; basis_solver.py; final_models.py; weather_only_regression.py')
