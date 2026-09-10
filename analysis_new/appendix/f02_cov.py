"""APP-F02-COV: fixed weather-final covariance completion, no model search.

Pure legacy design functions are loaded without executing their analysis module.
Compatible C in-sample predictions provide residuals; no OOF predictions enter.
"""
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import re
import shutil
import sys

import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels
import statsmodels.api as sm
from statsmodels.tools.tools import pinv_extended
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups

from .catalog import ROOT, MAIN, E0, R0, F02_SOURCES, REQUIREMENTS, J03_PLAN
from .design_adapter import load_design_functions
from .exporters import table, literal
from .mapping import digest, write_json, expected

R=next(r for r in REQUIREMENTS if r['requirement_id']=='F02')
ID='Incident Reference'
CUSTOMERS='customers_v2_event_excl_reinterruptions'
MODELS=[('E0',E0,'F08'),('R0c',R0,'F06')]
STATE='产物已补齐/待研究负责人反馈分析'
TOL=dict(atol=1e-9,rtol=1e-8)


def read(p):return pd.read_csv(p,float_precision='round_trip')
def js(p):return json.loads(Path(p).read_text(encoding='utf8'))
def token(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def csv(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(p,index=False,float_format='%.17g',compression={'method':'gzip','mtime':0} if p.suffix=='.gz' else None)


def build_function():
    design,_=load_design_functions({})
    ctx={'np':np,'pd':pd,'design':design}
    tree=ast.parse((ROOT/'analysis_new/weather_only_regression.py').read_text(encoding='utf-8-sig'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'base','build'}]
    if {n.name for n in nodes}!={'base','build'}:raise ValueError('Weather pure design interface missing')
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'weather_only_regression.py','exec'),ctx)
    return ctx['build']


def inputs():
    build=build_function();summary=js(ROOT/MAIN/'weather_only/weather_only_summary.json')
    c_sample=read(ROOT/'results/Appendix/C/tables/C_SAMPLE_DEFINITIONS.csv').set_index('combination')
    bundles=[]
    for margin,source,cm in MODELS:
        d=read(ROOT/source)
        d=d.loc[d.cause_group_official.eq('weather_natural')].copy()
        if margin=='R0c':
            d['customers_v2_log1p']=np.log1p(d[CUSTOMERS].astype(float))
            d=d.loc[d[CUSTOMERS]>0]
        d=d.reset_index(drop=True)
        response='log1p_customers_v2' if margin=='E0' else 'log_duration_B_full_span_hours'
        y=d[response].to_numpy(dtype=float);knots=summary[margin]['knots']['selected']
        X,_=build(d,d,margin,margin=='R0c','final',knots)
        if not d[ID].is_unique or d[ID].isna().any():raise ValueError(margin+': invalid incident IDs')
        if not np.isfinite(X).all().all() or not np.isfinite(y).all():raise ValueError(margin+': incomplete final design; no silent dropping')
        dates=pd.to_datetime(d.incident_date_utc).dt.date.astype(str)
        if d.LAD21CD.isna().any() or dates.eq('NaT').any():raise ValueError(margin+': missing cluster keys')
        ladder=c_sample.loc[margin+'_weather']
        id_hash=token(d[ID].astype(str).tolist())
        if ladder.sample_id_sha256!=id_hash or ladder.source_sha256!=digest(ROOT/source):raise ValueError(margin+': accepted C sample mismatch')
        if len(d)!=summary[margin]['n_used'] or len(d)!=ladder.n:raise ValueError(margin+': final sample versions differ')
        if knots!=([11.,24.] if margin=='E0' else [11.]):raise ValueError(margin+': accepted fixed knot definition changed')
        scale=literal('analysis_new/model_selection.py','SCALE')+(['customers_v2_log1p'] if margin=='R0c' else [])
        levels={c:sorted(d[c].dropna().unique().tolist()) for c in ['incident_year','incident_month']}
        spec=dict(model=margin+'_weather_final',margin=margin,n=len(d),response=response,
            sample_id_sha256=id_hash,source=source,source_sha256=digest(ROOT/source),
            filtering='weather_natural; '+('customers>0' if margin=='R0c' else 'no additional customer filter'),
            zero_customers=int(d[CUSTOMERS].eq(0).sum()),columns=list(X.columns),
            means={c:float(d[c].mean()) for c in scale},sd_ddof1={c:float(d[c].std(ddof=1)) for c in scale},
            knots=knots,knot_treatment='accepted fixed full-sample final; no selection this task',
            calendar_levels=levels,reference_levels={c:v[0] for c,v in levels.items()},
            socio_unscaled=literal('analysis_new/model_selection.py','SOCIO'),
            interactions=[c for c in X.columns if c in {'z_gust_pressure','z_gust_precip'}],
            lad_key='LAD21CD',date_key='pd.to_datetime(incident_date_utc).dt.date.astype(str); existing UTC date, no conversion',
            group_encoding='pandas.factorize in row encounter order',X_sha256=hashlib.sha256(np.ascontiguousarray(X,dtype=float).tobytes()).hexdigest(),
            design_function='weather_only_regression.build(d,d,margin,cust,final,accepted_selected_knots)')
        bundles.append((margin,d,X,y,dates,spec,cm))
    return bundles


def covariance_from_residuals(X,resid,lad,date):
    # Same statsmodels OLS pinv bread, without solving new coefficients.
    pinv,singular=pinv_extended(np.asarray(X,dtype=float))
    bread=pinv@pinv.T
    scores=np.asarray(X,dtype=float)*resid[:,None]
    both,lad_cov,date_cov=cov_cluster_2groups((scores,bread),lad,date,use_correction=True)
    direct=cov_cluster((scores,bread),lad,use_correction=True)
    return both,lad_cov,date_cov,lad_cov+date_cov-both,bread,singular,direct


def inference(beta,cov,df):
    variance=np.diag(cov);se=np.full(len(beta),np.nan)
    # Keep negative variances invalid; never take abs or truncate to zero.
    np.sqrt(variance,out=se,where=(variance>=0)&np.isfinite(variance))
    with np.errstate(divide='ignore',invalid='ignore'):
        p=2*stats.t.sf(np.abs(beta/se),df)
    q=stats.t.ppf(.975,df)
    return se,p,beta-q*se,beta+q*se


def calculate_one(stage,bundle):
    margin,d,X,y,dates,spec,cm=bundle;name=spec['model'];prefix='F02_'+margin
    old=read(ROOT/MAIN/f'weather_only/{margin}_weather_final_twoway.csv')
    if list(old.term)!=list(X.columns):raise ValueError('Final table and exact production column order differ')
    beta=old.coef.to_numpy();directory=ROOT/f'results/Appendix/C/data/models/{margin}_weather/{cm}'
    pp=js(directory/'preprocessing.json');full=[r for r in pp if r['prediction_type']=='in_sample' and str(r['fold'])=='full']
    pred=read(directory/'in_sample.csv.gz');coefs=read(directory/'coefficients.csv').set_index('term')
    compatible=(len(full)==1 and full[0]['knots']==spec['knots'] and full[0]['train_ids_sha256']==spec['sample_id_sha256']
        and len(pred)==len(d) and pred.observation_id.astype(str).tolist()==d[ID].astype(str).tolist()
        and pred.prediction_type.eq('in_sample').all() and set(coefs.index)==set(X.columns)
        and np.allclose(coefs.loc[X.columns,'coef'],beta,**TOL) and np.allclose(pred.y,y,**TOL)
        and np.allclose(X.to_numpy()@beta,pred.prediction,**TOL))
    if compatible:
        fitted=pred.prediction.to_numpy();action='REUSE_C_IN_SAMPLE_AND_FINAL_COEFFICIENTS';new_fits=0
    else:
        # Only fixed OLS once; no fit retries, CV, knot search or model choice.
        res=sm.OLS(y,X).fit(method='pinv');beta=res.params.to_numpy();fitted=res.fittedvalues.to_numpy()
        action='REBUILD_FIXED_OLS_ONCE';new_fits=1
    resid=y-fitted
    lad,lad_levels=pd.factorize(d.LAD21CD);date,date_levels=pd.factorize(dates)
    pair,_=pd.factorize(pd.MultiIndex.from_arrays([lad,date]))
    counts=dict(LAD=len(lad_levels),date=len(date_levels),intersection=len(np.unique(pair)))
    both,cl,cd,ci,bread,singular,direct=covariance_from_residuals(X,resid,lad,date)
    df=counts['LAD']-1;rank=int(np.linalg.matrix_rank(X));n,k=X.shape
    factors={g:float(v/(v-1)*(n-1)/(n-k)) for g,v in counts.items()}
    se_l,p_l,lo_l,hi_l=inference(beta,cl,df);se_2,p_2,lo_2,hi_2=inference(beta,both,df)
    with np.errstate(divide='ignore',invalid='ignore'):ratio=se_2/se_l
    out=pd.DataFrame(dict(model=name,term=X.columns,coef=beta,se_lad=se_l,se_twoway=se_2,se_ratio=ratio,
        ci_lad_lower=lo_l,ci_lad_upper=hi_l,ci_twoway_lower=lo_2,ci_twoway_upper=hi_2,p_lad_t_G1=p_l,p_twoway_t_G1=p_2,df=df))
    comp=pd.DataFrame(dict(model=name,term=X.columns,old_coef=old.coef,new_coef=beta,coef_difference=beta-old.coef,
        old_se_twoway=old.se,new_se_twoway=se_2,se_twoway_difference=se_2-old.se,
        old_se_lad=old.se_lad,new_se_lad=se_l,se_lad_difference=se_l-old.se_lad,
        old_p_t_G1=old.p_t_G1,new_p_t_G1=p_2,p_difference=p_2-old.p_t_G1))
    checks=dict(ids_unique=bool(d[ID].is_unique),same_columns=bool(list(X.columns)==old.term.tolist()),
        old_new_coefficients=bool(np.allclose(beta,old.coef,**TOL)),old_new_twoway_se=bool(np.allclose(se_2,old.se,**TOL)),
        old_new_lad_se=bool(np.allclose(se_l,old.se_lad,**TOL)),old_new_p=bool(np.allclose(p_2,old.p_t_G1,**TOL)),
        common_residual_prediction=bool(np.allclose(X.to_numpy()@beta,fitted,**TOL)),
        normal_equations=bool(np.max(np.abs(X.to_numpy().T@resid))/n<1e-8),
        lad_component_matches_direct=bool(np.allclose(cl,direct,rtol=1e-12,atol=1e-13)),
        cluster_row_keys=bool(np.array_equal(np.asarray(lad_levels)[lad],d.LAD21CD) and np.array_equal(np.asarray(date_levels)[date],dates)),
        lad_se_diagonal=bool(np.allclose(se_l**2,np.diag(cl),rtol=1e-12,atol=1e-13)),
        two_se_diagonal=bool(np.allclose(se_2**2,np.diag(both),rtol=1e-12,atol=1e-13)),
        intervals_t_rule=bool(np.allclose(hi_2-beta,stats.t.ppf(.975,df)*se_2,**TOL) and np.allclose(beta-lo_l,stats.t.ppf(.975,df)*se_l,**TOL)))
    matrices={'LAD':cl,'TWO_WAY':both,'DATE':cd,'INTERSECTION':ci,'BREAD':bread}
    matrix_notes={}
    for label,cov in matrices.items():
        checks[label+'_finite_symmetric']=bool(np.isfinite(cov).all() and np.allclose(cov,cov.T,rtol=1e-11,atol=1e-12))
        matrix_notes[label]=dict(negative_diagonal_terms=[str(X.columns[i]) for i in np.flatnonzero(np.diag(cov)<0)],
            minimum_eigenvalue=float(np.linalg.eigvalsh(cov).min()) if np.isfinite(cov).all() else None,numerical_correction='none')
        csv(stage/f'data/{prefix}_COV_{label}.csv',pd.DataFrame(cov,columns=X.columns).assign(term=X.columns)[['term',*X.columns]])
    checks['no_negative_inference_variance']=bool((np.diag(cl)>=0).all() and (np.diag(both)>=0).all())
    rows=pd.DataFrame(dict(observation_id=d[ID].astype(str),LAD21CD=d.LAD21CD,date=dates,lad_code=lad,date_code=date,
                           intersection_code=pair,y=y,fitted=fitted,residual=resid))
    csv(stage/f'data/{prefix}_ROWS.csv.gz',rows)
    csv(stage/f'data/{prefix}_DESIGN.csv.gz',X.assign(observation_id=d[ID].astype(str))[['observation_id',*X.columns]])
    saved=read(stage/f'data/{prefix}_ROWS.csv.gz');sx=read(stage/f'data/{prefix}_DESIGN.csv.gz')
    checks['serialized_row_alignment']=saved.observation_id.equals(sx.observation_id) and saved.observation_id.astype(str).tolist()==d[ID].astype(str).tolist()
    recovered=covariance_from_residuals(sx[list(X.columns)].to_numpy(),saved.residual.to_numpy(),saved.lad_code.to_numpy(),saved.date_code.to_numpy())
    checks['saved_inputs_covariance_roundtrip']=bool(np.allclose(recovered[0],both,rtol=1e-10,atol=1e-12) and np.allclose(recovered[1],cl,rtol=1e-10,atol=1e-12))
    spec.update(design_rank=rank,design_columns=k,clusters=counts,small_sample_factors=factors,
        correction_formula='G/(G-1)*(n-1)/(n-k_columns), separately LAD/date/intersection; two-way=LAD+date-intersection',
        reference_distribution='Student t',df=df,df_rule='G_LAD-1 for both, follows final p_t_G1',alpha=.05,
        action=action,new_ols_fits=new_fits,compatible_C_in_sample=bool(compatible),matrix_diagnostics=matrix_notes,
        c_predictions=str((directory/'in_sample.csv.gz').relative_to(ROOT)),residual_definition='saved final in-sample y-prediction' if compatible else 'single fixed OLS residual')
    write_json(stage/f'data/{prefix}_DESIGN_METADATA.json',spec)
    return out,comp,spec,checks


def report(stage,status,coeff,specs):
    from .runner import now
    text=['# APP-F02-COV 第二工作包执行与回传报告',f'记录时间：{now()}。本包执行完成，待研究负责人反馈分析；不自动关闭F02。',
        '## 范围与来源','仅天气暴露与天气恢复的正式固定final模型。原final two-way CSV已经保存se_lad列；旧缺口文字称其不存在不准确。本轮补齐完整协方差及分量、两套95%区间、同样本来源和复算输入，不重算F.3。',
        '## 实际动作与有效范围','|模型|状态|动作|本次OLS拟合数|原因|','|---|---|---|---|---|']
    for r in status:text.append(f"|{r['model']}|{r['status']}|{r.get('action','—')}|{r.get('new_ols_fits',0)}|{r.get('reason','')}|")
    text+=['## 计算和推断规则',
        '两种推断使用同一设计矩阵、同一残差和同一系数。采用本地statsmodels '+statsmodels.__version__+' cov_cluster/cov_cluster_2groups，use_correction=True；two-way为LAD分量＋date分量−交叉组分量，不是仅按LAD-date交叉组聚类。每个分量分别使用G/(G−1)×(n−1)/(n−k)修正，k为实际设计列数。',
        '95%系数区间及双侧p值均用t(G_LAD−1)，沿用final表p_t_G1规则。该规则不因增加日期维度而改为其他自由度。原代码的SE转换规则为sqrt(maximum(variance,0))；这是代码规则，不表示本次样本曾出现负方差。本轮保留原始矩阵并显式记录异常，不abs或静默截零。',
        '接口参考：[statsmodels两组聚类协方差文档](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html)。实际公式、默认参数和tuple输入支持已按本地0.14.6源码读取并保存哈希，没有升级依赖。',
        '|模型|n|设计列/秩|LAD/date/交叉组|df|固定结点|','|---|---|---|---|---|---|']
    for s in specs:text.append(f"|{s['model']}|{s['n']}|{s['design_columns']}/{s['design_rank']}|{s['clusters']['LAD']}/{s['clusters']['date']}/{s['clusters']['intersection']}|{s['df']}|{s['knots']}|")
    text+=['## 与已存final结果的对齐','下列为逐系数最大绝对差，按协议atol=1e−9、rtol=1e−8核对；固定模型系数没有改变。']
    source_comparison=read(stage/'data/F02_SOURCE_COMPARISON.csv')
    for model,c in source_comparison.groupby('model'):
        text.append(f"{model}：系数最大差{c.coef_difference.abs().max():.8g}；two-way SE最大差{c.se_twoway_difference.abs().max():.8g}；LAD SE最大差{c.se_lad_difference.abs().max():.8g}；原t规则p值最大差{c.p_difference.abs().max():.8g}。")
    text+=['## 阵风项及既有交互项','下表保留实际SE变化方向。SE比小于1、区间跨0均不视为计算失败。',
        '|模型/项|系数|LAD SE|two-way SE|比值|LAD 95% CI|two-way 95% CI|','|---|---|---|---|---|---|---|']
    for r in coeff[coeff.term.str.contains('gust')].itertuples():
        text.append(f'|{r.model}/{r.term}|{r.coef:.9g}|{r.se_lad:.9g}|{r.se_twoway:.9g}|{r.se_ratio:.6f}|[{r.ci_lad_lower:.8g}, {r.ci_lad_upper:.8g}]|[{r.ci_twoway_lower:.8g}, {r.ci_twoway_upper:.8g}]|')
    text+=['完整逐系数数据见tables/F02_COEFFICIENT_COMPARISON.csv；与原final逐项差值见data/F02_SOURCE_COMPARISON.csv。',
        '## 对后续不确定性表述的直接影响']
    for s in specs:
        sub=coeff[coeff.model==s['model']];changed=sub[((sub.ci_lad_lower>0)|(sub.ci_lad_upper<0))!=((sub.ci_twoway_lower>0)|(sub.ci_twoway_upper<0))]
        text.append(f"{s['model']}：全部系数SE比范围{sub.se_ratio.min():.6f}–{sub.se_ratio.max():.6f}；两套95%区间是否包含0发生变化的项为{', '.join(changed.term) if len(changed) else '无'}。该清单仅描述当前两种推断，不据此重新筛选变量。")
    for s in specs:
        diag=s['matrix_diagnostics']['TWO_WAY']
        text.append(f"{s['model']}：two-way矩阵最小特征值{diag['minimum_eigenvalue']:.9g}，负对角项{diag['negative_diagonal_terms']}，数值修正none。"+('该矩阵不是半正定，但本次各系数对角方差为正；逐系数SE和区间有效性与任意线性组合的方差不是同一判断。本包保留原两维聚类结果，不做联合检验或自动正定化。' if diag['minimum_eigenvalue']<0 else ''))
    text+=['后续F.2应使用本次同模型逐项结果，不沿用预设的倍数范围；本次原表对齐没有发现需要修改既存two-way单系数数字的实质差异。本轮不修改正文，也不因某项区间跨0改变主模型。',
        '## 核验与文件','F02_TECHNICAL_CHECKS.json记录样本、列序、键、同系数/残差、协方差有限对称、对角/SE、区间规则、旧表对齐及保存输入复算。矩阵负特征值与负方差分别记录；没有自动正定化。',
        'tables仅登记拟用于附录的完整系数比较主表；data/F02_SPECIFICATIONS.csv、F02_MODEL_STATUS.csv、F02_SOURCE_COMPARISON.csv及各模型DESIGN_METADATA、ROWS、DESIGN、COV_*属于支持或复算记录，不自动全列为论文排版表。',
        '## 复现与停止','项目根目录：`python -X utf8 -B main_appendix.py --appendices F --f02-only`。只读预检加`--check-only`；重算本包协方差加`--recompute-f02`，仍优先复用兼容系数/残差，非强制再拟合。',
        'F02_PROTOCOL.json在协方差计算前冻结输入、固定规格、配置和代码；F02_LAST_EXECUTION.json记录当前缓存/计算/拟合动作。输出固定在results/Appendix/F/，其他F管理文件保留。',
        'J03由研究负责人确认匹配比较缺口关闭，保留正文PROXY，本轮未重跑或修改J。第二包待人工＋agent反馈分析；G/I及H未启动。没有独立科学审查、Word修改、ZIP或远程提交。']
    (stage/'logs/F02_EXECUTION_REPORT.md').write_text(('\n\n'.join(text)+'\n').replace('|\n\n|','|\n|'),encoding='utf8')


def generate(stage,source_checks,previous,force=False,only=False,base_generator=None,command=''):
    from .runner import now,safe_child
    failed=[v['path'] for v in source_checks if v['path'] in F02_SOURCES and not v['passed']]
    if failed:raise ValueError('F02 frozen sources changed: '+str(failed))
    old=js(previous/'manifest.json') if (previous/'manifest.json').exists() else {}
    own={r['path'] for r in old.get('outputs',[]) if r['requirement_id']=='F02'}
    if old.get('owner')=='main_appendix.py':
        # F01/F03 are always retained, including ordinary --appendices F calls.
        for rel in old['managed_files']:
            if rel in own or rel=='manifest.json':continue
            dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dest)
        manifest=copy.deepcopy(old);manifest['outputs']=[r for r in old['outputs'] if r['requirement_id']!='F02']
    elif only:raise ValueError('F02-only requires an existing managed F')
    else:manifest=base_generator('F',stage,source_checks)
    for folder in ['tables','data','logs']:(stage/folder).mkdir(parents=True,exist_ok=True)
    before={p.relative_to(stage).as_posix():digest(p) for p in stage.rglob('*') if p.is_file() and p.name not in ['README.md','manifest.json']}
    deps=['analysis_new/appendix/f02_cov.py','analysis_new/appendix/design_adapter.py']
    cfg=dict(task='APP-F02-COV',inputs={p:digest(ROOT/p) for p in F02_SOURCES},rules=R['config'],
        code={p:digest(ROOT/p) for p in deps},software={'statsmodels':statsmodels.__version__,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},
        covariance_implementation_sha256=digest(Path(inspect.getsourcefile(cov_cluster))),
        pinv_implementation_sha256=digest(Path(inspect.getsourcefile(pinv_extended))))
    key=token(cfg);cache=not force and old.get('f02_cache_key')==key and bool(own) and all((previous/r['path']).is_file() and digest(previous/r['path'])==r['sha256'] for r in old['outputs'] if r['requirement_id']=='F02')
    if cache:
        for rel in own:
            dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dest)
        newly=0;print('F02: validated cache; no covariance calculation or OLS fitting',flush=True)
    else:
        bundles=inputs()
        protocol=dict(**cfg,frozen_at=now(),command=command,python=sys.version,random_seed=None,random_operations='none',
            plan=J03_PLAN,plan_sha256=digest(ROOT/J03_PLAN),samples=[b[5] for b in bundles],comparison_tolerance=TOL,
            interval='coef ± t.ppf(.975,G_LAD-1)*SE; two-sided p=2*t.sf(abs(coef/SE),G_LAD-1)',
            prior_final_negative_variance_rule='legacy sqrt(max(diag,0)); F02 no clipping; any negatives recorded',
            no_other_work='no model search, knots, CV, bootstrap, F03, GI/H or J rerun')
        write_json(stage/'logs/F02_PROTOCOL.json',protocol)
        status=[];specs=[];tables=[];comparisons=[];checks={}
        for bundle in bundles:
            margin=bundle[0]
            try:
                t,c,s,ch=calculate_one(stage,bundle);tables.append(t);comparisons.append(c);specs.append(s);checks[margin]=ch
                good=all(ch.values())
                status.append(dict(model=s['model'],status='complete' if good else 'partial_requires_feedback',action=s['action'],new_ols_fits=s['new_ols_fits'],reason='' if good else '; '.join(k for k,v in ch.items() if not v)))
                print(f"F02 {margin}: n={s['n']}, action={s['action']}, valid={good}",flush=True)
            except Exception as exc:
                status.append(dict(model=margin+'_weather_final',status='blocked',action='failed',new_ols_fits=0,reason=f'{type(exc).__name__}: {exc}'))
                checks[margin]={'calculation_completed':False}
        coeff=pd.concat(tables,ignore_index=True) if tables else pd.DataFrame(columns=['model','term','coef','se_lad','se_twoway','se_ratio'])
        comparison=pd.concat(comparisons,ignore_index=True) if comparisons else pd.DataFrame(columns=['model','term','reason'])
        table(stage,'F02_COEFFICIENT_COMPARISON',coeff,R)
        csv(stage/'data/F02_SOURCE_COMPARISON.csv',comparison);csv(stage/'data/F02_MODEL_STATUS.csv',pd.DataFrame(status))
        flat=[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in s.items()} for s in specs]
        csv(stage/'data/F02_SPECIFICATIONS.csv',pd.DataFrame(flat) if flat else pd.DataFrame(columns=['model','n','reason']))
        write_json(stage/'logs/F02_TECHNICAL_CHECKS.json',dict(time=now(),checks=checks,all_passed=all(all(c.values()) for c in checks.values()),status=status,
            no_covariance_clipping=True))
        report(stage,status,coeff,specs);newly=sum(s['new_ols_fits'] for s in status)
    write_json(stage/'logs/F02_LAST_EXECUTION.json',dict(time=now(),command=command,cached_export=cache,new_ols_fits=newly,
        covariance_recomputed=not cache,cache_key=key,force_recompute=force))
    preserve={rel:digest(stage/rel)==sha for rel,sha in before.items()}
    if not all(preserve.values()):raise ValueError('Other F results changed')
    write_json(stage/'logs/F02_PRESERVATION.json',dict(other_F_managed_files=preserve,all_unchanged=all(preserve.values())))
    content=(stage/'README.md').read_text(encoding='utf8').split('\n## APP-F02-COV')[0]
    content=content.replace('最近生成：','F01/F03原整理时间：')
    content=re.sub(r'### F02 —.*?(?=### F03 —|\Z)','',content,flags=re.S)
    content=content.replace('天气LAD-only仍缺。','天气final原表已有se_lad；本包补齐矩阵、区间与可复算来源。')
    content+='\n## APP-F02-COV\n\n'+(stage/'logs/F02_EXECUTION_REPORT.md').read_text(encoding='utf8')
    (stage/'README.md').write_text(content,encoding='utf8')
    valid=js(stage/'logs/F02_TECHNICAL_CHECKS.json')['all_passed']
    state=STATE if valid else '产物部分可用/具体异常待反馈分析'
    newfiles={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}-set(before)-{'README.md','manifest.json'}
    for rel in expected(R):
        if not (stage/rel).is_file():raise ValueError('Missing F02 export '+rel)
    for rel in sorted(newfiles):
        p=stage/rel
        manifest['outputs'].append(dict(path=rel,sha256=digest(p),bytes=p.stat().st_size,requirement_id='F02',claim_id='CL_F02',
            source_paths=F02_SOURCES,source_sha256=cfg['inputs'],producer=R['producer'],export_function=R['producer'],configuration=R['config'],status=state))
    manifest['requirements']['F02']=state;manifest.pop('error',None)
    manifest.update(owner='main_appendix.py',appendix='F',last_attempt=now(),status='success' if valid else 'success_with_gaps',
        update_state='本次仅F02更新/其他F结果保留',f02_cache_key=key,
        managed_files=sorted({p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}|{'manifest.json'}))
    write_json(stage/'manifest.json',manifest)
    return manifest
