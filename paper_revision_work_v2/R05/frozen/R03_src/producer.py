"""Explicit R03 production entry: calculation separated from file publication."""
import json,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
from contracts import *
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def code_identity():
    files=[ROOT/'cli.py',*sorted((ROOT/'src').glob('*.py'))]
    return config_hash({p.relative_to(ROOT).as_posix():sha(p) for p in files})
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x
def save_json(path,obj,output_root):
    p=Path(path).resolve();out=Path(output_root).resolve()
    if not out.is_relative_to(WORK.resolve()) or not p.is_relative_to(out):raise ValueError('write outside declared revision output root')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def load_events(config):
    mp=Path(config['input_manifest']);expected=config['input_manifest_sha256']
    if sha(mp)!=expected:raise ValueError('R02 manifest identity changed')
    m=read(mp)
    if m['run_id']!=config['input_version']:raise ValueError('wrong input version')
    p=Path(m['event_table']['path'])
    if sha(p)!=m['event_table']['sha256']:raise ValueError('R02 table hash mismatch')
    d=pd.read_parquet(p)
    if len(d)!=m['event_count'] or not d[ID].is_unique or not d.input_version.eq('R02_20260905').all():raise ValueError('bad event identity/version')
    return d,m
def step0_build_sample(config):
    events,m=load_events(config)
    return events.loc[events.candidate_main_E0|events.candidate_main_R0c].copy(),m
def step2_build_folds(base,config):
    return global_date_folds(base,config['n_splits'])
def run_oof(main_sample,mapping,group,target_name,config):
    d=attach_folds(main_sample,mapping);groupmask=d.cause_group_event.eq('weather_natural') if group=='weather' else pd.Series(True,index=d.index)
    evaluation=d.loc[groupmask].copy();expected=evaluation[[ID,'fold']].copy();expected['y']=target(evaluation,target_name)
    blocks=['control','G'] if target_name=='E0' else ['control','G','K','GK']
    collected={b:[] for b in blocks};archives=[];fold_records=[]
    for f in range(config['n_splits']):
        trainmain=d.loc[d.fold.ne(f)].copy();valid=evaluation.loc[evaluation.fold.eq(f)].copy()
        if not len(valid):raise ValueError('empty evaluation fold')
        train,tail=training_population(trainmain,group,target_name,config['training_tail'])
        if set(train.new_date_utc)&set(valid.new_date_utc):raise ValueError('date group leakage')
        prep=fit_preprocessor(train,target_name)
        fold_records.append({'fold':f,'training':tail,'evaluation_n':len(valid),'evaluation_ids_sha256':identity(valid[ID]),'scaler_sha256':config_hash(prep),'training_mean_target':float(target(train,target_name).mean())})
        for block in blocks:
            meta={'run_id':config['run_id'],'purpose':config['purpose'],'config_sha256':config_hash(config),'code_identity':code_identity(),'input_version':config['input_version'],'group':group,'fold':f,'tail':tail,'evaluation_ids_sha256':identity(valid[ID]),'evaluation_n':len(valid)}
            model=fit_ols(train,prep,block,meta);yp=predict_eta(valid,model);archives.append(model)
            pred=valid[[ID,'fold','new_date_utc','LAD21CD']].copy();pred['y']=target(valid,target_name);pred['prediction_eta']=yp;pred['training_mean_baseline']=float(target(train,target_name).mean());pred['prediction_source']='OOF_date_group_diagnostic';pred['target_scale']=model['target_scale'];pred['run_id']=config['run_id'];pred['purpose']=config['purpose']
            collected[block].append(pred)
    frames={b:pd.concat(v,ignore_index=True) for b,v in collected.items()};metrics={b:score_oof(p,expected) for b,p in frames.items()}
    return {'predictions':frames,'models':archives,'fold_records':fold_records,'metrics':metrics,'contributions':paired_contributions(metrics,target_name),'expected':expected}
def publish_oof(result,output_root):
    out=Path(output_root).resolve()
    if not out.is_relative_to(WORK.resolve()):raise ValueError('old output directory forbidden')
    out.mkdir(parents=True,exist_ok=True)
    for b,p in result['predictions'].items():p.to_csv(out/f'oof_{b}.csv',index=False)
    for model in result['models']:
        save_json(out/f"model_fold{model['metadata']['fold']}_{model['block']}.json",model,out)
    save_json(out/'metrics.json',result['metrics'],out);save_json(out/'contributions.json',result['contributions'],out);save_json(out/'fold_training.json',result['fold_records'],out)
def require_result(path,run_id,allow_smoke=False):
    p=Path(path)
    if not p.exists():raise FileNotFoundError('No declared new artifact; H0 fallback and silent fitting forbidden')
    model=read(p)
    if model.get('schema')!='R03_portable_linear_v1' or model['metadata']['run_id']!=run_id:raise ValueError('artifact version/schema mismatch')
    if model['metadata']['purpose']=='non_inferential_smoke' and not allow_smoke:raise ValueError('smoke artifact cannot supply a publication figure')
    return model
