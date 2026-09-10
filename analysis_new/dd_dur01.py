"""DD-DUR01 ordinary offline program, called through main_new.py's stage runner."""
import gzip
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

from analysis_new.runner import PROJECT, save, digest, now
from analysis_new.p03_p04_grid_weather import previous_run, verified_output
from analysis_new.grid_weather import parse_hourly, START, END, FIELD
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.fragility_optimizer import RULES, DURATION_RULES, Objective, fit, probabilities
from analysis_new.duration_features import MODELS, FEATURES, PEAK_EDGES, threshold, features, support
from analysis_new.dd_dur01_outputs import evaluate_outputs, validate, readme


def read(path): return pd.read_csv(path,float_precision='round_trip')


def run_experiment(root,settings):
    out=root/'results/dd_dur01'; out.mkdir()
    def event(message,**more):
        record=dict(time=now(),message=message,**more)
        with (out/'execution.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(record,ensure_ascii=False,default=str)+'\n')
        print(f'[{record["time"]}] {message}',flush=True)
    def offline(name,args):
        if name in ['socket.connect','socket.getaddrinfo']: raise PermissionError('DD-DUR01 is offline; new requests prohibited')
    sys.addaudithook(offline)
    base,bm=previous_run(PROJECT,settings.get('base_run','20260909231634'))
    weather,wm=previous_run(PROJECT,settings.get('weather_run','20260909205214'))
    if bm['status']!='completed' or wm['status']!='completed': raise ValueError('Requires completed baseline and weather runs')
    paths={}
    for name in ['experiment.json','PROTOCOL.md','fit_summary.csv','parameters.csv','metrics.csv','oof_predictions.csv.gz','optimizer_candidates.csv.gz','daily_aggregations.csv.gz']:
        paths['base/'+name]=verified_output(base,bm,'results/dd_agg01/'+name)
    for name in ['panel_grid.csv','lad_folds.csv']:
        paths['weather/'+name]=verified_output(weather,wm,'results/p03_p04/'+name)
    raw=sorted((weather/'results/p03_p04/weather_raw').glob('*.json.gz'))
    if len(raw)!=111: raise ValueError('Expected 111 cached weather envelopes')
    for p in raw: paths['raw/'+p.name]=verified_output(weather,wm,'results/p03_p04/weather_raw/'+p.name)
    provenance=[dict(path=str(p),sha256=digest(p)) for p in [*paths.values(),base/'run.json',weather/'run.json',PROJECT/'docs/new_analysis/instructions/Codex_DD_DUR01_持续强风增量测试.md']]
    oldprotocol=json.loads(paths['base/experiment.json'].read_text(encoding='utf-8'))
    if oldprotocol['optimizer']!=RULES: raise ValueError('M0 constraints/optimization definition differ from recorded A01')
    rm=json.loads((root/'run.json').read_text(encoding='utf-8'))
    protocol=dict(task='DD-DUR01',frozen_at=now(),purpose=rm['purpose'],inputs=provenance,
        command=os.environ.get('DD_DUR01_ENTRY_COMMAND','python -X utf8 -B main_new.py (only dd_dur01=1)'),
        baseline_run=base.name,weather_run=weather.name,dates=[START,END],timezone='UTC',hour_unit='m/s',hours_per_day=24,
        expected_rows=121656,lads=111,days=1096,targets=TARGETS,primary='any_gt100',important_secondary='wthr_gt100',
        labels='existing panel unchanged; any event includes zero-customer records; other thresholds strictly >k',
        tau='90th percentile linear of ALL training LAD-hour rows; shared grid LADs not deduplicated; full threshold never used for CV',
        features=dict(G='max hourly gust',H='sum(g>tau)*1h',h='H/24h',I='sum(max(g^2-tau^2,0))*1h',J='I/(24h*tau^2)',x='log1p(J)'),
        models=dict(M0='p0+(1-p0)Phi((log G-log theta)/beta)',M1='same with z += gamma*h',M2='same with z += gamma*x'),
        optimizer=RULES,duration_optimizer=DURATION_RULES,
        starts='16: matched training-scope M0 with scaled gamma [0,-1,+1], then old 13 training-only starts with cycling [-1,0,+1]; physical gamma clipped to [-20,20]',
        scope_order=['full']+[f'fold_{i}' for i in range(5)],folds_path=str(paths['weather/lad_folds.csv']),
        metrics='pooled rowwise OOF BS, gain vs M0, fold BS, training-fold constant BSS, shared-bin weighted calibration RMSE; no decision threshold',
        calibration='valid three-model pooled OOF deciles, add0/1 unique; side=right; empty NaN; n<100 isolated; full+supported-bin shared zoom with tail count',
        peak_edges=PEAK_EDGES.tolist(),support='fixed5m/s G bins plus overall summaries per scope train/test; observed joint histograms only',
        uncertainty=dict(repeats=1000,seed=20260909,unit='paired LAD fixed OOF, shared draws, row weights',excludes='retraining, threshold re-estimation, model selection, shared date/storm dependence'),
        csv_read='float_precision=round_trip',sources=rm['sources'],environment=rm['environment'],
        forbidden=['new weather requests','new model specifications/thresholds/time splits','Word modification','return packages','independent review','adoption report'])
    save(out/'protocol.json',protocol)
    (out/'PROTOCOL.md').write_text('''# DD-DUR01 冻结实现协议

本轮只执行指定三模型的实现、运行、必要核验及结果输出，不独立审查、不决定主模型、不改论文、不生成回传包。

固定111 LAD×1096 UTC日，原小时ERA5返回网格、日键、八标签和折号不变。tau按每个训练范围全部LAD小时行的linear90%分位数，测试天气/标签不参与；full阈值只用于full描述。所有任务同折共用tau，不去重共享网格。

G=max(g)，H=sum(g>tau)*1小时，h=H/24小时；I=sum((g²−tau²)+)*1小时，J=I/(24小时*tau²)，x=log1p(J)。G=0时特征为0且预测p0；tau≤0必须报错。

M0为已修复三参数背景率lognormal；M1的z增加gamma*h，M2增加gamma*x；增量模型所有四参数共同估计，gamma允许正负，不加入M3。沿用theta[0.1,200]、beta[0.05,5]、p0[0,1−1e−12]；gamma统一[-20,20]。仅优化坐标为gamma*训练特征RMS（RMS最小1e−6仅防全零坐标除零），特征本身不标准化、不中心化，结果gamma回到模型原尺度。

同一稳定log-CDF、解析梯度、精确组合分组和有限优化框架。增量模型16初值：匹配训练范围M0参数+scaled gamma[0,−1,+1]，另沿用原13组训练初值并循环scaled gamma[−1,0,+1]；physical gamma截于统一边界。L-BFGS-B maxiter600/maxls40/ftol1e−13/gtol1e−9；原统一触发规则最多两次Powell，maxiter300/maxfev3000。不得差于已评价M0合法点或其他初值（总NLL容差1e−5）。success、投影梯度≤1e−5、非恒定预测及常数似然参照共同判有效。

弱识别沿用近优NLL≤0.01的theta/beta倍数>1.25及边界标记，并增加近优gamma跨度×训练特征RMS>0.1或特征恒定标记。theta超G支持范围另列，不能与失败混同。无法解决目标保留无效诊断，其他目标继续，禁止常数填补为有效结果。

复用48个A01时，校验指纹、定义、48项NLL及预测/OOF BS；容差NLL1e−5、概率1e−12、BS1e−14、G1e−12。M1/M2仅新增96拟合。全样本参数和阈值不进入CV。

评价以any_gt100为主、wthr_gt100为重要次级，其余六项完整保存。池化BS、M0绝对/相对差、逐折、训练率BSS，1000次同种子20260909整LAD配对固定OOF区间；不含重训、阈值重估、选择和共享日期/风暴的全部不确定性。不设置采用硬门槛。

三模型有效OOF共同十分位分箱，补0/1去重，right归箱，round_trip回读；n<100不连线，空箱保留NaN。全范围+由n≥100箱最大均值/频率×1.15确定的共同放大范围（至少0.005、至多1），图注尾部数量；不修改评分。与上一轮五模型箱不同，禁止把跨轮分箱RMSE差称为模型进步。G支持箱固定0至60每5m/s及末尾无穷，标签不参与选箱；只输出已有联合组合的全样本描述预测。

输入/折号/代码指纹、执行命令、版本及精确机器规则见protocol.json。规则冻结于任何本轮增量模型性能之前。
''',encoding='utf-8')
    event('Protocol frozen before duration fits',sha256=digest(out/'protocol.json'))
    panel=read(paths['weather/panel_grid.csv']); fold_table=read(paths['weather/lad_folds.csv'])
    if len(panel)!=121656 or panel.duplicated(['LAD21CD','date']).any() or panel.LAD21CD.nunique()!=111: raise ValueError('Invalid panel product')
    if fold_table.LAD21CD.duplicated().any() or len(fold_table)!=111 or set(fold_table.fold)!=set(range(5)): raise ValueError('Invalid original folds')
    folds=panel.LAD21CD.map(fold_table.set_index('LAD21CD').fold).to_numpy()
    if not np.isfinite(folds).all() or not np.isin(panel[TARGETS],[0,1]).all(): raise ValueError('Missing folds/nonbinary targets')
    frames=[]; hourly=[]
    for p in raw:
        lad=p.name.removesuffix('.json.gz')
        with gzip.open(p,'rt',encoding='utf-8') as f: envelope=json.load(f)
        request=envelope['request']
        if any(request[k]!=v for k,v in dict(models='era5',hourly=FIELD,timezone='GMT',wind_speed_unit='ms',start_date=START,end_date=END).items()): raise ValueError('Changed cached weather definition')
        frame=parse_hourly(envelope['response'],lad); frames.append(frame)
        hourly.append(np.asarray(envelope['response']['hourly'][FIELD],dtype=float).reshape(-1,24))
    weather_rows=pd.concat(frames,ignore_index=True); weather_rows['hour_index']=np.arange(len(weather_rows))
    merged=panel[['LAD21CD','date']].merge(weather_rows,on=['LAD21CD','date'],how='left',validate='one_to_one',sort=False)
    if len(weather_rows)!=len(panel) or merged.hour_index.isna().any(): raise ValueError('Hourly/day key mismatch')
    hours=np.concatenate(hourly)[merged.hour_index.to_numpy(dtype=int)]
    if not np.allclose(hours.max(axis=1),panel.gust,atol=1e-12,rtol=0): raise ValueError('G differs from original grid panel')
    if not np.array_equal(merged[['grid_lat','grid_lon']],panel[['grid_lat','grid_lon']]): raise ValueError('Returned grid changed')
    previous_daily=read(paths['base/daily_aggregations.csv.gz']); old_oof=read(paths['base/oof_predictions.csv.gz'])
    for data in [previous_daily,old_oof]:
        if not data[['LAD21CD','date']].equals(panel[['LAD21CD','date']]) or not np.array_equal(data[TARGETS],panel[TARGETS]) or not np.array_equal(data.fold,folds): raise ValueError('A01 inputs/labels/folds mismatch')
    if not np.allclose(previous_daily.A01_daily_max,hours.max(axis=1),atol=1e-12,rtol=0): raise ValueError('G differs from DD-AGG01 A01')
    event('Verified 111 cached hourly files, all row keys, G, labels, grids and original folds')
    feature_tables={}; feature_records=[]; threshold_records=[]; supports=[]
    for scope in protocol['scope_order']:
        train=np.ones(len(panel),dtype=bool) if scope=='full' else folds!=int(scope.split('_')[1])
        tau=threshold(hours,train); table=features(hours,tau); feature_tables[scope]=table
        records=panel[['LAD21CD','date']].copy(); records['fold']=folds; records['scope']=scope
        records['role']='full' if scope=='full' else np.where(train,'train','test'); records['tau']=tau; records[FEATURES]=table
        feature_records.append(records)
        threshold_records.append(dict(scope=scope,tau=tau,training_rows=int(train.sum()),training_hours=int(train.sum()*24),
                                     training_lads=int(panel.loc[train,'LAD21CD'].nunique()),held_out_fold=-1 if scope=='full' else int(scope.split('_')[1]),method='linear',quantile=.9))
        supports.extend(support(table,scope,train))
    pd.DataFrame(threshold_records).to_csv(out/'thresholds.csv',index=False)
    pd.concat(feature_records,ignore_index=True).to_csv(out/'features_by_fold.csv.gz',index=False)
    pd.DataFrame(supports).to_csv(out/'feature_support.csv',index=False)
    event('Training-only thresholds and six full-coverage feature scopes saved')
    oldfits=read(paths['base/fit_summary.csv']); oldparams=read(paths['base/parameters.csv'])
    if not oldfits.equals(oldparams): raise ValueError('A01 parameter and fit tables differ')
    m0=oldfits[oldfits.candidate=='A01_daily_max'].copy()
    if len(m0)!=48 or not m0.valid.all() or m0.duplicated(['target','scope']).any(): raise ValueError('Requires all 48 valid repaired A01 fits')
    match=[]; summaries=[]; candidates=[]; mapping={}
    original_candidates=read(paths['base/optimizer_candidates.csv.gz'])
    oldmetrics=read(paths['base/metrics.csv'])
    for row in m0.to_dict('records'):
        scope=row['scope']; target=row['target']; train=np.ones(len(panel),dtype=bool) if scope=='full' else folds!=int(scope.split('_')[1])
        obj=Objective(panel.loc[train,'gust'],panel.loc[train,target]); params={k:row[k] for k in ['theta','beta','p0']}
        nll=obj.nll(obj.encode(**params)); nll_error=abs(nll-row['nll'])
        if nll_error>1e-5: raise ValueError('Reused M0 NLL mismatch')
        prediction_error=0.
        if scope!='full':
            p=probabilities(panel.loc[~train,'gust'],**params)
            prediction_error=float(np.max(np.abs(p-old_oof.loc[~train,target+'__A01_daily_max'])))
            if prediction_error>1e-12: raise ValueError('Reused M0 OOF prediction mismatch')
        match.append(dict(target=target,scope=scope,nll_absolute_error=nll_error,max_prediction_error=prediction_error))
        row.update(candidate='M0',gamma=0.,origin='reused DD-AGG01 A01',baseline_nll=row['nll'],nll_gain_vs_m0=0.)
        summaries.append(row); mapping['M0',target,scope]=row
    baseline_checks=dict(checked_at=now(),same_inputs_labels_folds=True,G_max_error=float(np.max(np.abs(hours.max(axis=1)-previous_daily.A01_daily_max))),
                         parameter_constraints_unchanged=True,scope_matches=match,score_matches=[])
    for target in TARGETS:
        bs=float(np.mean((old_oof[target+'__A01_daily_max']-panel[target])**2))
        score=oldmetrics[(oldmetrics.target==target)&(oldmetrics.candidate=='A01_daily_max')].iloc[0]
        if abs(bs-score.brier)>1e-14: raise ValueError('Reused M0 Brier mismatch')
        baseline_checks['score_matches'].append(dict(target=target,brier=bs,absolute_error=abs(bs-score.brier)))
    save(out/'baseline_match.json',baseline_checks)
    imported=original_candidates[original_candidates.candidate=='A01_daily_max'].copy()
    imported['candidate']='M0'; imported['gamma']=0.; imported['origin']='reused DD-AGG01 diagnostics'; candidates.extend(imported.to_dict('records'))
    event('48 M0 fits reused after NLL, constraints, OOF and Brier checks')
    for model,column in [('M1','h'),('M2','x')]:
        for target in TARGETS:
            for scope in protocol['scope_order']:
                train=np.ones(len(panel),dtype=bool) if scope=='full' else folds!=int(scope.split('_')[1])
                ft=feature_tables[scope]; baseline=mapping['M0',target,scope]
                try:
                    result,records=fit(ft.loc[train,'G'].to_numpy(),panel.loc[train,target].to_numpy(),feature=ft.loc[train,column].to_numpy(),baseline=baseline)
                except Exception as exc:
                    result=dict(baseline,theta=np.nan,beta=np.nan,p0=np.nan,gamma=np.nan,nll=np.nan,valid=False,weak_identification=False,
                                message=repr(exc),baseline_nll=baseline['nll'],nll_gain_vs_m0=np.nan,selection_reason='exception: no replacement prediction'); records=[]
                result.update(candidate=model,target=target,scope=scope,origin='new duration fit')
                for r in records:
                    r.update(candidate=model,target=target,scope=scope,origin='new duration fit',
                             selected=bool(r['method']==result['method'] and r['start']==result['start']),selection_reason=result['selection_reason'])
                summaries.append(result); candidates.extend(records); mapping[model,target,scope]=result
                with (out/'fit_checkpoint.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(dict(summary=result,candidates=records),default=str)+'\n')
                event(f'Target {len(summaries)}/144 {model} {target} {scope}',valid=result['valid'],message_detail=result['message'])
    fit_summary=pd.DataFrame(summaries); fit_summary.to_csv(out/'fit_summary.csv',index=False); fit_summary.to_csv(out/'parameters.csv',index=False)
    pd.DataFrame(candidates).to_csv(out/'optimizer_candidates.csv.gz',index=False)
    oof=panel[['LAD21CD','date',*TARGETS]].copy(); oof['fold']=folds; oof['tau']=np.nan
    full=panel[['LAD21CD','date',*TARGETS]].copy(); full[FEATURES]=feature_tables['full']
    full['tau']=threshold_records[0]['tau']
    for fold in range(5):
        m=folds==fold; ft=feature_tables[f'fold_{fold}']
        oof.loc[m,FEATURES]=ft.loc[m,FEATURES]; oof.loc[m,'tau']=threshold_records[fold+1]['tau']
    for target in TARGETS:
        constant=np.full(len(panel),np.nan)
        for fold in range(5):
            m=folds==fold; constant[m]=panel.loc[~m,target].mean()
        oof[target+'_constant']=constant
        for model in MODELS:
            prediction=np.full(len(panel),np.nan)
            for fold in range(5):
                m=folds==fold; ft=feature_tables[f'fold_{fold}']; f=mapping[model,target,f'fold_{fold}']
                if np.isfinite(f['theta']):
                    prediction[m]=probabilities(ft.loc[m,'G'],**{k:f[k] for k in ['theta','beta','p0','gamma']},feature=None if model=='M0' else ft.loc[m,'h' if model=='M1' else 'x'])
            oof[target+'__'+model]=prediction
            f=mapping[model,target,'full']
            full[target+'__'+model]=probabilities(full.G,**{k:f[k] for k in ['theta','beta','p0','gamma']},feature=None if model=='M0' else full['h' if model=='M1' else 'x']) if np.isfinite(f['theta']) else np.nan
    oof.to_csv(out/'oof_predictions.csv.gz',index=False); full.to_csv(out/'full_predictions.csv.gz',index=False)
    event('All 144 targets and observed-support full / OOF prediction files saved')
    scores,_,_=evaluate_outputs(out,oof,fit_summary,feature_tables['full'])
    result=validate(out,panel,folds,hours,feature_tables,fit_summary,baseline_checks,scores)
    readme(out,protocol,result)
    event('Technical validation and all required outputs completed',valid_fits=result['valid_fits'],invalid_fits=result['invalid_fits'],checks=len(result['checks']))
    save(out/'inventory.json',dict(created_at=now(),inputs=provenance,files=[dict(path=str(p.relative_to(out)).replace('\\','/'),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='inventory.json']))


if __name__=='__main__':
    run_experiment(Path(os.environ['NEW_ANALYSIS_RUN']),json.loads(os.environ.get('DD_DUR01_SETTINGS','{}')))
