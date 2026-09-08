from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from x02_modeling import (RUN, TASKS, MODELS, DEV_GROUPS, fit_model, predict_model, model_grid,
                          training_mask, validation_mask, metrics, save_fit, sha256, write_json)


def cfg_id(cfg: dict) -> str:
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"))


def main() -> None:
    state=json.loads((RUN/"RUN_STATE.json").read_text(encoding="utf-8"))
    if state.get("stage")!="X02-B" or not state.get("stage_b_pass"):
        raise RuntimeError("X02-B has not passed")
    # This entry point filters to pre-cutoff events before targets are used; P4/P5 labels are not scored here.
    from x02_modeling import load_data
    d=load_data(before_cutoff_only=True)
    score_rows=[]; failures=[]; opt_logs=[]
    for task in TASKS:
        for model in MODELS:
            for cfg in model_grid(model):
                fold_mse=[]
                for val in DEV_GROUPS:
                    train_groups=[g for g in DEV_GROUPS if g!=val]
                    trm=training_mask(d,task,model,train_groups,[val],time_path=True)
                    vam=validation_mask(d,task,val)
                    train=d.loc[trm].copy(); valid=d.loc[vam].copy()
                    try:
                        fit,logs=fit_model(train,task,model,cfg)
                        pred=predict_model(fit,valid)
                        met=metrics(valid["target_"+task].to_numpy(float),pred)
                        fold_mse.append(met["mse"])
                        score_rows.append({"task":task,"model":model,"config":cfg_id(cfg),"validation_group":val,"train_n":len(train),"validation_n":len(valid),"status":"ok",**met})
                        for x in logs: opt_logs.append({"path":"development","task":task,"model":model,"config":cfg_id(cfg),"split":val,**x})
                    except Exception as exc:
                        failures.append({"stage":"X02-C-development","severity":"invalid_model","task":task,"model":model,"config":cfg_id(cfg),"split":val,"error":repr(exc),"traceback":traceback.format_exc()})
                        score_rows.append({"task":task,"model":model,"config":cfg_id(cfg),"validation_group":val,"train_n":len(train),"validation_n":len(valid),"status":"failed","mse":np.nan})
                # No early stopping on poor scores; every frozen config is attempted.
    scores=pd.DataFrame(score_rows)
    scores.to_csv(RUN/"tables"/"development_inner_scores.csv",index=False)
    pd.DataFrame(opt_logs).to_csv(RUN/"evidence"/"development_optimization_logs.csv",index=False)

    agg=(scores[scores.status.eq("ok")].groupby(["task","model","config"],as_index=False)
         .agg(folds=("validation_group","nunique"),macro_mse=("mse","mean"),pooled_sse=("sse","sum"),pooled_n=("n","sum")))
    agg["pooled_mse"]=agg.pooled_sse/agg.pooled_n
    agg.to_csv(RUN/"tables"/"development_config_summary.csv",index=False)
    selected=[]
    for task in TASKS:
        for model in MODELS:
            x=agg[(agg.task==task)&(agg.model==model)&(agg.folds==3)].sort_values(["macro_mse","config"])
            if x.empty:
                failures.append({"stage":"X02-C-development","severity":"invalid_model","task":task,"model":model,"error":"no configuration completed all three development process folds"})
                continue
            r=x.iloc[0]
            selected.append({"task":task,"model":model,"config":r.config,"macro_mse":float(r.macro_mse),"pooled_mse":float(r.pooled_mse)})
    sel=pd.DataFrame(selected)
    sel.to_csv(RUN/"tables"/"development_model_selection.csv",index=False)

    # Refit each candidate at its own development-selected configuration and save selected-fold predictions/models.
    pred_rows=[]; final_models=[]
    for r in selected:
        task,model,cfg=r["task"],r["model"],json.loads(r["config"])
        for val in DEV_GROUPS:
            trm=training_mask(d,task,model,[g for g in DEV_GROUPS if g!=val],[val],time_path=True)
            vam=validation_mask(d,task,val); train=d.loc[trm].copy(); valid=d.loc[vam].copy()
            try:
                fit,logs=fit_model(train,task,model,cfg); pred=predict_model(fit,valid)
                art=save_fit(fit,RUN/"models"/"development"/task/model/f"holdout_{val}.joblib",train)
                for i,p in zip(valid.index,pred): pred_rows.append({"path":"A_development","split":val,"task":task,"model":model,"episode":val,"anon_event_id":valid.at[i,"anon_event_id"],"y":float(valid.at[i,"target_"+task]),"pred":float(p),"config":r["config"]})
                final_models.append({"path":"development","task":task,"model":model,"split":val,"train_n":len(train),"test_n":len(valid),**art})
            except Exception as exc:
                failures.append({"stage":"X02-C-development-refit","severity":"invalid_model","task":task,"model":model,"split":val,"error":repr(exc),"traceback":traceback.format_exc()})
        trm=training_mask(d,task,model,DEV_GROUPS,["P4","P5"],time_path=True); train=d.loc[trm].copy()
        try:
            fit,logs=fit_model(train,task,model,cfg)
            art=save_fit(fit,RUN/"models"/"time_frozen"/task/f"{model}.joblib",train)
            final_models.append({"path":"time_frozen","task":task,"model":model,"split":"P4_P5","train_n":len(train),"test_n":1070,**art})
            for x in logs: opt_logs.append({"path":"time_frozen_fit","task":task,"model":model,"config":r["config"],"split":"P4_P5",**x})
        except Exception as exc:
            failures.append({"stage":"X02-C-time-final-fit","severity":"invalid_model","task":task,"model":model,"error":repr(exc),"traceback":traceback.format_exc()})
    pd.DataFrame(pred_rows).to_parquet(RUN/"predictions"/"development_predictions.parquet",index=False)
    pd.DataFrame(final_models).to_csv(RUN/"tables"/"model_artifacts_before_time_score.csv",index=False)
    pd.DataFrame(opt_logs).to_csv(RUN/"evidence"/"development_optimization_logs.csv",index=False)
    write_json(RUN/"evidence"/"failures_through_development.json",failures)

    complexity=["B00","B01","S01","G02","S02","P00","P02","S03","S04","G05","S05"]
    recommendations={}
    for task in TASKS:
        x=sel[sel.task.eq(task)].copy()
        minm=float(x.macro_mse.min()); x["within_one_percent"]=x.macro_mse.le(minm*1.01)
        tied=x[x.within_one_percent].copy(); tied["simplicity"]=tied.model.map({m:i for i,m in enumerate(complexity)})
        choice=tied.sort_values(["simplicity","macro_mse"]).iloc[0]
        recommendations[task]={"selected_model":choice.model,"selected_config":json.loads(choice.config),"macro_mse":float(choice.macro_mse),"point_best_model":x.sort_values("macro_mse").iloc[0].model,"point_best_macro_mse":minm,"within_one_percent_models":tied.sort_values("simplicity").model.tolist()}
    lock={"run_id":RUN.name,"locked_utc":datetime.now(timezone.utc).isoformat(),"criterion":"development leave-process-out macro-MSE; within 1% use frozen simplicity order","recommendations":recommendations,
          "all_model_selected_configs":selected,"development_scores_sha256":sha256(RUN/"tables"/"development_inner_scores.csv"),"test_labels_scored":False,
          "protocol_lock_sha256":sha256(RUN/"evidence"/"PROTOCOL_LOCK.json"),"failures_n":len(failures)}
    write_json(RUN/"MODEL_SELECTION_LOCK.json",lock)
    lock["lock_file_sha256_after_write"]=sha256(RUN/"MODEL_SELECTION_LOCK.json")
    write_json(RUN/"evidence"/"MODEL_SELECTION_LOCK_RECEIPT.json",lock)
    write_json(RUN/"RUN_STATE.json",{"run_id":RUN.name,"stage":"X02-C-development-locked","status":"completed","completed_utc":datetime.now(timezone.utc).isoformat(),"next_allowed_stage":"X02-C-time-score","model_selection_lock_sha256":sha256(RUN/"MODEL_SELECTION_LOCK.json")})
    print(json.dumps(recommendations,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
