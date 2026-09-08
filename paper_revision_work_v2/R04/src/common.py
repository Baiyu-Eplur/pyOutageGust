import sys,os,json,hashlib
from pathlib import Path
Q=Path(__file__).resolve().parents[1];W=Q.parent;CORE=W/'R03';RUN=Q/'R04_B1_all_valid_v1'
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(Q/'runtime/mplconfig');sys.dont_write_bytecode=True
sys.path[:0]=[str(Q/'runtime/site-packages'),str(CORE/'runtime/site-packages'),str(CORE/'src')]
import numpy as np
import pandas as pd
from contracts import *
from producer import read,sha,clean,load_events,config_hash
def save(p,x):
    p=Path(p);assert p.resolve().is_relative_to(Q) or p.resolve().is_relative_to(W/'tables')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def table(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);d.to_csv(p,index=False)
def markdown(d):
    def fmt(x):return '未提供/不适用' if x is None or isinstance(x,float) and not np.isfinite(x) else f'{x:.8g}' if isinstance(x,float) else str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in d.itertuples(index=False,name=None))+'\n'
def events():return load_events(read(CORE/'configs/R04_primary.json'))[0]
def members(e,g,t):return e.loc[e['candidate_'+g+'_'+t]].copy()
def model(g,t):return read(RUN/f'{g}_{t}/full_model.json')
def covariance(x,y,b,groups):
    from diagnostics import cluster_covariance
    return cluster_covariance(pd.DataFrame(x),y-x@b,groups)
