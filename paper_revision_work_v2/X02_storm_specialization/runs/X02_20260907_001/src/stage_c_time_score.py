from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from x02_modeling import RUN, TASKS, MODELS, load_data, eligible_mask, predict_model, metrics, sha256, write_json


def main() -> None:
    state=json.loads((RUN/"RUN_STATE.json").read_text(encoding="utf-8"))
    lock=json.loads((RUN/"MODEL_SELECTION_LOCK.json").read_text(encoding="utf-8"))
    if state.get("stage")!="X02-C-development-locked": raise RuntimeError("Development selection is not locked")
    if state.get("model_selection_lock_sha256")!=sha256(RUN/"MODEL_SELECTION_LOCK.json"): raise RuntimeError("Selection lock hash mismatch")
    scored_utc=datetime.now(timezone.utc).isoformat()
    d=load_data(test_only=True)
    preds=[]; rows=[]
    for task in TASKS:
        for model in MODELS:
            p=RUN/"models"/"time_frozen"/task/f"{model}.joblib"
            if not p.exists():
                rows.append({"task":task,"model":model,"episode":"ALL","status":"missing_model"}); continue
            fit=joblib.load(p)
            for group in ["P4","P5"]:
                x=d.loc[eligible_mask(d,task)&d.protected_group.eq(group)].copy()
                pred=predict_model(fit,x); y=x["target_"+task].to_numpy(float)
                met=metrics(y,pred)
                rows.append({"task":task,"model":model,"episode":group,"status":"ok",**met})
                for i,pr in zip(x.index,pred):
                    preds.append({"path":"A_time_test","split":"P4_P5_frozen","episode":group,"task":task,"model":model,
                                  "anon_event_id":x.at[i,"anon_event_id"],"y":float(x.at[i,"target_"+task]),"pred":float(pr),
                                  "gust_0h":float(x.at[i,"gust_0h"]),"event_time_proxy_utc":x.at[i,"event_time_proxy_utc"]})
            x=d.loc[eligible_mask(d,task)].copy(); pred=predict_model(fit,x); y=x["target_"+task].to_numpy(float)
            rows.append({"task":task,"model":model,"episode":"POOLED","status":"ok",**metrics(y,pred)})
    pr=pd.DataFrame(preds); out=RUN/"predictions"/"time_test_predictions.parquet"; pr.to_parquet(out,index=False)
    mt=pd.DataFrame(rows)
    # Add process-equal macro MSE and mean RMSE as explicitly different summaries.
    macro=[]
    for (task,model),x in mt[mt.episode.isin(["P4","P5"])&mt.status.eq("ok")].groupby(["task","model"]):
        macro.append({"task":task,"model":model,"episode":"MACRO","status":"ok","n":int(x.n.sum()),"mse":float(x.mse.mean()),"rmse":float(np.sqrt(x.mse.mean())),"mean_process_rmse":float(x.rmse.mean())})
    mt=pd.concat([mt,pd.DataFrame(macro)],ignore_index=True)
    b00=mt[(mt.model=="B00")][["task","episode","mse"]].rename(columns={"mse":"b00_mse"})
    mt=mt.merge(b00,on=["task","episode"],how="left")
    mt["skill_vs_B00"]=1-mt.mse/mt.b00_mse
    mt.to_csv(RUN/"tables"/"time_test_metrics.csv",index=False)

    diag=[]
    for (task,model,ep),x in pr.groupby(["task","model","episode"]):
        diag.append({"task":task,"model":model,"episode":ep,**metrics(x.y.to_numpy(),x.pred.to_numpy())})
    pd.DataFrame(diag).to_csv(RUN/"tables"/"time_test_residual_diagnostics.csv",index=False)

    selected=[]
    for task,v in lock["recommendations"].items():
        model=v["selected_model"]
        for ep in ["P4","P5","POOLED","MACRO"]:
            z=mt[(mt.task==task)&(mt.model==model)&(mt.episode==ep)].iloc[0].to_dict()
            selected.append(z)
    pd.DataFrame(selected).to_csv(RUN/"tables"/"time_test_locked_recommendations.csv",index=False)

    # Outcome distributions are released only now, after the selection lock.
    dist=[]
    for task in TASKS:
        for ep in ["P4","P5"]:
            x=d.loc[eligible_mask(d,task)&d.protected_group.eq(ep)]
            y=x["target_"+task]
            dist.append({"task":task,"episode":ep,"n":len(x),"target_mean":float(y.mean()),"target_sd":float(y.std(ddof=1)),"target_p50":float(y.quantile(.5)),"target_p95":float(y.quantile(.95)),"target_max":float(y.max()),"gust_min":float(x.gust_0h.min()),"gust_max":float(x.gust_0h.max())})
    pd.DataFrame(dist).to_csv(RUN/"tables"/"time_test_outcome_distribution_postlock.csv",index=False)

    report=["# Frozen time-test report","",f"Scored once at `{scored_utc}` after development lock `{lock['locked_utc']}`.","",
            "P4 Ciarán and P5 Henk used the same per-task/per-model frozen fit. Henk was not updated after Ciarán. All eligible test events were scored; no test-outcome truncation was applied.","",
            "## Locked recommendations","",pd.DataFrame(selected)[["task","model","episode","n","mse","rmse","mae","r2","skill_vs_B00"]].to_csv(index=False),"",
            "The CSV block above is a compact machine-readable excerpt; the complete all-candidate table is `tables/time_test_metrics.csv`. Two process groups do not support a storm-population confidence interval, so none is reported."]
    (RUN/"TIME_TEST_FROZEN_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    receipt={"scored_utc":scored_utc,"selection_lock_sha256":sha256(RUN/"MODEL_SELECTION_LOCK.json"),"predictions_sha256":sha256(out),"metrics_sha256":sha256(RUN/"tables"/"time_test_metrics.csv"),"P4_P5_same_fit":True,"Henk_not_updated_after_Ciaran":True,"score_calls":1}
    write_json(RUN/"evidence"/"TIME_TEST_SEAL.json",receipt)
    write_json(RUN/"RUN_STATE.json",{"run_id":RUN.name,"stage":"X02-C-time-test-sealed","status":"completed","completed_utc":datetime.now(timezone.utc).isoformat(),"time_test_seal_sha256":sha256(RUN/"evidence"/"TIME_TEST_SEAL.json"),"next_allowed_stage":"X02-D"})
    print(pd.DataFrame(selected)[["task","model","episode","n","mse","rmse","r2","skill_vs_B00"]].to_string(index=False))


if __name__=="__main__": main()
