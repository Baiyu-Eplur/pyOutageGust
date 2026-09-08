from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from x02_modeling import (RUN,TASKS,MODELS,ALL_GROUPS,load_data,model_grid,training_mask,validation_mask,
                          fit_model,predict_model,metrics,save_fit,sha256,write_json)


def cid(c:dict)->str: return json.dumps(c,sort_keys=True,separators=(",",":"))


def main()->None:
    state=json.loads((RUN/"RUN_STATE.json").read_text(encoding="utf-8"))
    if state.get("stage") not in {"X02-C-time-test-sealed","X02-D-invalidated-buffer"}: raise RuntimeError("Time-test results must be sealed before Path B")
    seal_hash=sha256(RUN/"evidence"/"TIME_TEST_SEAL.json")
    if state.get("time_test_seal_sha256")!=seal_hash: raise RuntimeError("Time-test seal mismatch")
    started=datetime.now(timezone.utc).isoformat(); d=load_data()
    inner_rows=[]; selected=[]; preds=[]; arts=[]; failures=[]; opt=[]
    for outer in ALL_GROUPS:
        remaining=[g for g in ALL_GROUPS if g!=outer]
        for task in TASKS:
            for model in MODELS:
                summaries=[]
                for cfg in model_grid(model):
                    mses=[]; good=True
                    for inner in remaining:
                        train_groups=[g for g in remaining if g!=inner]
                        tr=d.loc[training_mask(d,task,model,train_groups,[outer,inner],time_path=False)].copy()
                        va=d.loc[validation_mask(d,task,inner)].copy()
                        try:
                            fit,logs=fit_model(tr,task,model,cfg); pr=predict_model(fit,va); met=metrics(va["target_"+task].to_numpy(float),pr); mses.append(met["mse"])
                            inner_rows.append({"outer_group":outer,"inner_validation_group":inner,"task":task,"model":model,"config":cid(cfg),"train_n":len(tr),"validation_n":len(va),"status":"ok",**met})
                            for z in logs: opt.append({"path":"B_inner","outer":outer,"inner":inner,"task":task,"model":model,"config":cid(cfg),**z})
                        except Exception as exc:
                            good=False; failures.append({"stage":"X02-D-inner","severity":"invalid_model","outer":outer,"inner":inner,"task":task,"model":model,"config":cid(cfg),"error":repr(exc),"traceback":traceback.format_exc()})
                            inner_rows.append({"outer_group":outer,"inner_validation_group":inner,"task":task,"model":model,"config":cid(cfg),"train_n":len(tr),"validation_n":len(va),"status":"failed","mse":np.nan})
                    if good and len(mses)==4: summaries.append((float(np.mean(mses)),cid(cfg),cfg))
                if not summaries:
                    failures.append({"stage":"X02-D-selection","severity":"invalid_model","outer":outer,"task":task,"model":model,"error":"no config completed four inner folds"}); continue
                summaries.sort(key=lambda x:(x[0],x[1])); mm,cs,cfg=summaries[0]
                selected.append({"outer_group":outer,"task":task,"model":model,"config":cs,"inner_macro_mse":mm})
                tr=d.loc[training_mask(d,task,model,remaining,[outer],time_path=False)].copy()
                te=d.loc[validation_mask(d,task,outer)].copy()
                try:
                    fit,logs=fit_model(tr,task,model,cfg); pr=predict_model(fit,te)
                    art=save_fit(fit,RUN/"models"/"fivefold"/task/model/f"outer_{outer}.joblib",tr)
                    arts.append({"path":"B_fivefold","outer_group":outer,"task":task,"model":model,"train_n":len(tr),"test_n":len(te),"config":cs,**art})
                    for i,p in zip(te.index,pr): preds.append({"path":"B_fivefold","split":f"outer_{outer}","episode":outer,"task":task,"model":model,"anon_event_id":te.at[i,"anon_event_id"],"y":float(te.at[i,"target_"+task]),"pred":float(p),"gust_0h":float(te.at[i,"gust_0h"]),"event_time_proxy_utc":te.at[i,"event_time_proxy_utc"],"config":cs})
                    for z in logs: opt.append({"path":"B_outer_fit","outer":outer,"inner":"NA","task":task,"model":model,"config":cs,**z})
                except Exception as exc:
                    failures.append({"stage":"X02-D-outer","severity":"invalid_model","outer":outer,"task":task,"model":model,"config":cs,"error":repr(exc),"traceback":traceback.format_exc()})
    pd.DataFrame(inner_rows).to_csv(RUN/"tables"/"fivefold_inner_scores.csv",index=False)
    pd.DataFrame(selected).to_csv(RUN/"tables"/"fivefold_selected_configs.csv",index=False)
    pd.DataFrame(arts).to_csv(RUN/"tables"/"fivefold_model_artifacts.csv",index=False)
    pd.DataFrame(opt).to_csv(RUN/"evidence"/"fivefold_optimization_logs.csv",index=False)
    write_json(RUN/"evidence"/"failures_fivefold.json",failures)
    pr=pd.DataFrame(preds); pout=RUN/"predictions"/"fivefold_oof_predictions.parquet"; pr.to_parquet(pout,index=False)

    met=[]
    for (task,model,ep),x in pr.groupby(["task","model","episode"]): met.append({"task":task,"model":model,"episode":ep,"summary":"process",**metrics(x.y.to_numpy(),x.pred.to_numpy())})
    for (task,model),x in pr.groupby(["task","model"]):
        met.append({"task":task,"model":model,"episode":"POOLED","summary":"pooled",**metrics(x.y.to_numpy(),x.pred.to_numpy())})
        z=[a for a in met if a["task"]==task and a["model"]==model and a["summary"]=="process"]
        mse=float(np.mean([a["mse"] for a in z])); met.append({"task":task,"model":model,"episode":"MACRO","summary":"macro","n":int(sum(a["n"] for a in z)),"mse":mse,"rmse":float(np.sqrt(mse)),"mean_process_rmse":float(np.mean([a["rmse"] for a in z]))})
    mt=pd.DataFrame(met)
    b=mt[mt.model.eq("B00")][["task","episode","mse"]].rename(columns={"mse":"b00_mse"}); mt=mt.merge(b,on=["task","episode"],how="left"); mt["skill_vs_B00"]=1-mt.mse/mt.b00_mse
    mt.to_csv(RUN/"tables"/"fivefold_metrics.csv",index=False)

    # Predeclared paired MSE differences, negative favors the first model.
    pairs=[("S02","G02"),("P00","G02"),("P02","P00"),("S03","S02"),("S04","S02"),("S05","S02"),("S05","G05"),("S02","B01")]
    dif=[]
    for task in TASKS:
        for a,bm in pairs:
            vals=[]
            for ep in ALL_GROUPS:
                aa=mt[(mt.task==task)&(mt.model==a)&(mt.episode==ep)]
                bb=mt[(mt.task==task)&(mt.model==bm)&(mt.episode==ep)]
                if len(aa)==1 and len(bb)==1:
                    v=float(aa.iloc[0].mse-bb.iloc[0].mse); vals.append(v); dif.append({"task":task,"comparison":f"{a}-{bm}","episode":ep,"mse_difference":v})
            if vals:
                dif.append({"task":task,"comparison":f"{a}-{bm}","episode":"MACRO","mse_difference":float(np.mean(vals)),"range_min":float(np.min(vals)),"range_max":float(np.max(vals))})
                for drop in ALL_GROUPS: dif.append({"task":task,"comparison":f"{a}-{bm}","episode":f"DELETE_{drop}","mse_difference":float(np.mean([v for v,e in zip(vals,ALL_GROUPS) if e!=drop]))})
    pd.DataFrame(dif).to_csv(RUN/"tables"/"fivefold_paired_differences.csv",index=False)

    # Exact one-prediction-per event/task/model check.
    dupe=int(pr.duplicated(["task","model","anon_event_id"]).sum())
    coverage=pr.groupby(["task","model"]).anon_event_id.nunique().reset_index(name="unique_predictions")
    coverage.to_csv(RUN/"tables"/"fivefold_prediction_coverage.csv",index=False)
    receipt={"started_utc":started,"completed_utc":datetime.now(timezone.utc).isoformat(),"time_test_seal_sha256":seal_hash,"predictions_sha256":sha256(pout),"prediction_duplicate_keys":dupe,"failures_n":len(failures),"outer_groups":ALL_GROUPS,"nested_inner_groups":4,"path_A_unchanged":True}
    write_json(RUN/"evidence"/"FIVEFOLD_SEAL.json",receipt)
    write_json(RUN/"RUN_STATE.json",{"run_id":RUN.name,"stage":"X02-D","status":"completed","completed_utc":datetime.now(timezone.utc).isoformat(),"fivefold_seal_sha256":sha256(RUN/"evidence"/"FIVEFOLD_SEAL.json"),"next_allowed_stage":"X02-E"})
    print(mt[mt.episode.eq("MACRO")][["task","model","mse","rmse","skill_vs_B00"]].to_string(index=False)); print("failures",len(failures),"duplicate_keys",dupe)


if __name__=="__main__": main()
