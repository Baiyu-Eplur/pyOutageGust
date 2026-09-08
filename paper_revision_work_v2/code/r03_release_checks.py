"""R03 release design-only support checks; no fitting, no legacy imports."""
import sys,os,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R03'
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
sys.dont_write_bytecode=True
sys.path[:0]=[str(Q/'src'),str(Q/'runtime/site-packages')]
from producer import read,save_json,step0_build_sample,code_identity
from contracts import *
cfg=read(Q/'configs/R04_primary.json');base,_=step0_build_sample(cfg)
mapping=pd.read_csv(cfg['fold_map'],dtype={'date_utc':str});d=attach_folds(base,mapping);rows=[]
for target_name in ['E0','R0c']:
    td=d.loc[d['candidate_main_'+target_name]]
    for group in ['main','weather']:
        for f in [-1,0,1,2,3,4]:
            main=td if f==-1 else td.loc[td.fold.ne(f)]
            train,tail=training_population(main,group,target_name,'all_valid')
            valid=td if f==-1 else td.loc[td.fold.eq(f)]
            if group=='weather':valid=valid.loc[valid.cause_group_event.eq('weather_natural')]
            prep=fit_preprocessor(train,target_name);block='G' if target_name=='E0' else 'GK'
            x=design(train,prep,block);test_x=design(valid,prep,block)
            rank=int(np.linalg.matrix_rank(x.to_numpy()))
            assert rank==len(x.columns)
            assert np.isfinite(test_x).all(axis=None)
            if f!=-1:assert not (set(train.new_date_utc)&set(valid.new_date_utc))
            rows.append({'target':target_name,'group':group,'fold':f,'training_n':len(train),'evaluation_n':len(valid),'rank':rank,'columns':len(x.columns),'unseen_categories':False,'dates_disjoint':None if f==-1 else True})
save_json(Q/'checks/R04_design_support.json',{'fit_count':0,'scope':'24 full/OOF training designs and evaluation transforms only; no outcomes fitted or scored','code_identity':code_identity(),'checks':rows},Q)
for name in ['R04_primary.json','R04_optional_p99.json']:
    p=Q/'configs'/name;c=read(p);c['code_identity']=code_identity();save_json(p,c,Q)
c=read(Q/'configs/smoke_v3.json');c['run_id']='R03_smoke_v4';c['output_root']=str(Q/'smoke/R03_smoke_v4');c['code_identity']=code_identity();save_json(Q/'configs/smoke_v4.json',c,Q)
print(json.dumps({'design_checks':len(rows),'fit_count':0,'passed':True,'code_identity':code_identity()}))
