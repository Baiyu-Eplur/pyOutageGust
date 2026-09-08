import os,sys,json,hashlib
from pathlib import Path
Q=Path(__file__).resolve().parents[1];W=Q.parent;R4=W/'R04';CORE=W/'R03';RUN=R4/'R04_B1_all_valid_v1'
sys.path[:0]=[str(Q/'frozen/R03_src'),str(R4/'runtime/site-packages'),str(CORE/'runtime/site-packages')]
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR=str(Q/'runtime/mplconfig'));sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
from contracts import *
from producer import read,sha,clean,load_events
def put(p,x):
    p=Path(p);assert p.resolve().is_relative_to(Q);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
save=put
def table(p,x):p=Path(p);assert p.resolve().is_relative_to(Q);p.parent.mkdir(parents=True,exist_ok=True);x.to_csv(p,index=False)
def md(d):
    def f(v):return '未定义/不适用' if v is None or isinstance(v,float) and not np.isfinite(v) else f'{v:.9g}' if isinstance(v,float) else str(v).replace('|','／').replace('\n',' ')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(f(x) for x in r)+' |' for r in d.itertuples(index=False,name=None))+'\n'
markdown=md
def write(p,s):p=Path(p);assert p.resolve().is_relative_to(Q);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def events():return load_events(read(CORE/'configs/R04_primary.json'))[0]
def members(e,g,t):return e[e['candidate_'+g+'_'+t]].copy()
def model(g,t):return read(RUN/f'{g}_{t}/full_model.json')
def record(p):return {'path':str(p),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
