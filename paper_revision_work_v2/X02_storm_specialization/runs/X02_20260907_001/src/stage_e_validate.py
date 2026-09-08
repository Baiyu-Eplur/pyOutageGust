from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from x02_modeling import RUN,TASKS,MODELS,ALL_GROUPS,load_data,predict_model,sha256,write_json,group_bounds


def raw_metrics(x:pd.DataFrame)->dict:
    e=x.y.to_numpy(float)-x.pred.to_numpy(float); y=x.y.to_numpy(float)
    sse=float(e@e); sst=float(((y-y.mean())**2).sum())
    return {"n":len(x),"mse":float(np.mean(e**2)),"rmse":float(np.sqrt(np.mean(e**2))),"mae":float(np.mean(np.abs(e))),"r2":float(1-sse/sst) if sst>1e-15 else np.nan}


def independent_compare(pred_path:Path,metrics_path:Path,episodes:list[str])->tuple[float,pd.DataFrame]:
    p=pd.read_parquet(pred_path); stored=pd.read_csv(metrics_path); rows=[]
    for (task,model,ep),x in p.groupby(["task","model","episode"]): rows.append({"task":task,"model":model,"episode":ep,**raw_metrics(x)})
    for (task,model),x in p.groupby(["task","model"]):
        rows.append({"task":task,"model":model,"episode":"POOLED",**raw_metrics(x)})
        z=[r for r in rows if r["task"]==task and r["model"]==model and r["episode"] in episodes]
        mm=float(np.mean([r["mse"] for r in z])); rows.append({"task":task,"model":model,"episode":"MACRO","n":sum(r["n"] for r in z),"mse":mm,"rmse":float(np.sqrt(mm)),"mae":np.nan,"r2":np.nan})
    rec=pd.DataFrame(rows); m=rec.merge(stored,on=["task","model","episode"],suffixes=("_recalc","_stored"))
    diffs=[]
    for c in ["mse","rmse","mae","r2"]:
        a=pd.to_numeric(m[c+"_recalc"],errors="coerce"); b=pd.to_numeric(m[c+"_stored"],errors="coerce"); diffs.extend(np.abs(a-b)[a.notna()&b.notna()].tolist())
    return float(max(diffs) if diffs else 0),rec


def savefig(fig,name:str)->None:
    for ext in ["png","svg","pdf"]: fig.savefig(RUN/"figures"/f"{name}.{ext}",dpi=220,bbox_inches="tight")
    plt.close(fig)


def make_figures()->None:
    time=pd.read_parquet(RUN/"predictions"/"time_test_predictions.parquet")
    five=pd.read_parquet(RUN/"predictions"/"fivefold_oof_predictions.parquet")
    lock=json.loads((RUN/"MODEL_SELECTION_LOCK.json").read_text(encoding="utf-8"))
    fig,axs=plt.subplots(3,2,figsize=(10,13))
    for i,task in enumerate(TASKS):
        model=lock["recommendations"][task]["selected_model"]
        for j,ep in enumerate(["P4","P5"]):
            ax=axs[i,j]; x=time[(time.task==task)&(time.model==model)&(time.episode==ep)]
            ax.hexbin(x.y,x.pred,gridsize=30,mincnt=1,bins="log",cmap="viridis")
            lo=min(x.y.min(),x.pred.min()); hi=max(x.y.max(),x.pred.max()); ax.plot([lo,hi],[lo,hi],"--",c="#bb5544",lw=1)
            ax.set(title=f"{task} {model}, {ep}, n={len(x)}",xlabel="Observed log outcome",ylabel="Predicted log outcome")
    fig.suptitle("Frozen time-test predictions",y=1.01); fig.tight_layout(); savefig(fig,"time_test_prediction_observed")

    fig,axs=plt.subplots(3,5,figsize=(18,10),sharex="row",sharey="row")
    for i,task in enumerate(TASKS):
        model=lock["recommendations"][task]["selected_model"]
        for j,ep in enumerate(ALL_GROUPS):
            ax=axs[i,j]; x=five[(five.task==task)&(five.model==model)&(five.episode==ep)]
            ax.scatter(x.y,x.pred,s=4,alpha=.25); lo=min(x.y.min(),x.pred.min()); hi=max(x.y.max(),x.pred.max()); ax.plot([lo,hi],[lo,hi],"--",c="#bb5544",lw=.8)
            ax.set_title(f"{task} {model}\n{ep}, n={len(x)}")
            if i==2: ax.set_xlabel("Observed")
            if j==0: ax.set_ylabel("Predicted")
    fig.suptitle("Five-process outer-fold predictions (Path-A locked model identities)",y=1.01); fig.tight_layout(); savefig(fig,"fivefold_prediction_observed")

    dif=pd.read_csv(RUN/"tables"/"fivefold_paired_differences.csv"); x=dif[dif.episode.isin(ALL_GROUPS)]
    pairs=x.comparison.unique(); fig,axs=plt.subplots(3,1,figsize=(12,11),sharex=True)
    for ax,task in zip(axs,TASKS):
        z=x[x.task==task]; offsets=np.linspace(-.25,.25,len(pairs))
        for off,pair in zip(offsets,pairs):
            q=z[z.comparison==pair].set_index("episode").reindex(ALL_GROUPS); ax.plot(np.arange(5)+off,q.mse_difference,"o-",label=pair,ms=4)
        ax.axhline(0,c="black",lw=.8); ax.set_ylabel(f"{task}\nMSE difference"); ax.grid(alpha=.2)
    axs[-1].set_xticks(range(5),ALL_GROUPS); axs[0].legend(ncol=4,fontsize=8); fig.suptitle("Predeclared paired differences by held process",y=.995); fig.tight_layout(); savefig(fig,"fivefold_process_mse_differences")


def curve_outputs(d:pd.DataFrame)->None:
    grids=np.linspace(1,40,157); models=["G02","P02","S01","S02","S03","S04","G05","S05"]
    rows=[]
    ref=d[d.protected_group.isin(["P1","P2","P3"])].sample(n=min(500,len(d)),random_state=20260907).copy()
    for task in TASKS:
        for model in models:
            path=RUN/"models"/"time_frozen"/task/f"{model}.joblib"
            if not path.exists(): continue
            fit=joblib.load(path)
            base=ref.copy(); base.gust_0h=9.; p9=float(np.mean(predict_model(fit,base)))
            trids=pd.read_parquet(path.with_suffix(".fit_ids.parquet"),columns=["anon_event_id"])
            tr=d[d.anon_event_id.isin(set(trids.anon_event_id))]
            gmin,gmax=float(tr.gust_0h.min()),float(tr.gust_0h.max())
            for g in grids:
                z=ref.copy(); z.gust_0h=g; val=float(np.mean(predict_model(fit,z)))-p9
                near=d[d.protected_group.isin(ALL_GROUPS)&d.gust_0h.between(g-.5,g+.5)]
                rows.append({"task":task,"model":model,"gust_mps":g,"log_prediction_difference_from_9mps":val,"training_gust_min":gmin,"training_gust_max":gmax,"inside_training_range":gmin<=g<=gmax,"nearby_event_n":len(near),"nearby_process_n":near.protected_group.nunique()})
    tab=pd.DataFrame(rows); tab.to_csv(RUN/"tables"/"gust_curve_predictions.csv",index=False)
    fig,axs=plt.subplots(3,1,figsize=(10,13),sharex=True)
    for ax,task in zip(axs,TASKS):
        for model in models:
            x=tab[(tab.task==task)&(tab.model==model)]; ax.plot(x.gust_mps,x.log_prediction_difference_from_9mps,label=model,lw=1.3)
        ax.axhline(0,c="black",lw=.7); ax.axvline(9,c="grey",lw=.7,ls=":"); ax.set_ylabel(f"{task}\nΔ log prediction vs 9 m/s"); ax.grid(alpha=.2)
    axs[-1].set_xlabel("Gust (m/s)"); axs[0].legend(ncol=4,fontsize=8); fig.suptitle("Frozen time-path gust response summaries\n(tree lines are average response, not structural laws)",y=.995); fig.tight_layout(); savefig(fig,"gust_response_curves")


def main()->None:
    state=json.loads((RUN/"RUN_STATE.json").read_text(encoding="utf-8"))
    if state.get("stage")!="X02-D": raise RuntimeError("X02-D not complete")
    checks=[]
    tmax,re_time=independent_compare(RUN/"predictions"/"time_test_predictions.parquet",RUN/"tables"/"time_test_metrics.csv",["P4","P5"])
    fmax,re_five=independent_compare(RUN/"predictions"/"fivefold_oof_predictions.parquet",RUN/"tables"/"fivefold_metrics.csv",ALL_GROUPS)
    re_time.to_csv(RUN/"evidence"/"independent_time_metric_recalculation.csv",index=False); re_five.to_csv(RUN/"evidence"/"independent_fivefold_metric_recalculation.csv",index=False)
    checks.append({"check":"independent_time_metric_max_abs_diff","value":tmax,"pass":tmax<=1e-8})
    checks.append({"check":"independent_fivefold_metric_max_abs_diff","value":fmax,"pass":fmax<=1e-8})

    timep=pd.read_parquet(RUN/"predictions"/"time_test_predictions.parquet"); fivep=pd.read_parquet(RUN/"predictions"/"fivefold_oof_predictions.parquet")
    checks.append({"check":"time_prediction_unique_keys","value":int(timep.duplicated(["task","model","anon_event_id"]).sum()),"pass":not timep.duplicated(["task","model","anon_event_id"]).any()})
    checks.append({"check":"fivefold_prediction_unique_keys","value":int(fivep.duplicated(["task","model","anon_event_id"]).sum()),"pass":not fivep.duplicated(["task","model","anon_event_id"]).any()})
    cov=fivep.groupby(["task","model"]).anon_event_id.nunique(); checks.append({"check":"fivefold_complete_4452_each","value":f"min={cov.min()},max={cov.max()}","pass":bool(cov.min()==4452 and cov.max()==4452)})

    cfg=json.loads((RUN/"run_config.yaml").read_text(encoding="utf-8")); cutoff=pd.Timestamp(cfg["time_path"]["fit_cutoff_utc"])
    artifacts=pd.concat([pd.read_csv(RUN/"tables"/"model_artifacts_before_time_score.csv"),pd.read_csv(RUN/"tables"/"fivefold_model_artifacts.csv")],ignore_index=True,sort=False)
    overlaps=0; buffer_viol=0; cutoff_viol=0; feature_viol=[]; hash_viol=0
    for _,a in artifacts.iterrows():
        mp=Path(a.model_path); ip=Path(a.fit_ids_path)
        if sha256(mp)!=a.model_sha256 or sha256(ip)!=a.fit_ids_sha256: hash_viol+=1
        ids=pd.read_parquet(ip); fitset=set(ids.anon_event_id)
        if a.path=="development": test=timep.iloc[0:0] if False else pd.read_parquet(RUN/"predictions"/"development_predictions.parquet"); test=test[(test.task==a.task)&(test.model==a.model)&(test.episode==a.split)]
        elif a.path=="time_frozen": test=timep[(timep.task==a.task)&(timep.model==a.model)]
        else: test=fivep[(fivep.task==a.task)&(fivep.model==a.model)&(fivep.episode==a.outer_group)]
        overlaps += len(fitset & set(test.anon_event_id))
        held=[a.split] if a.path=="development" else (["P4","P5"] if a.path=="time_frozen" else [a.outer_group])
        for g in held:
            lo,hi=group_bounds(pd.DataFrame(),g); lo-=pd.Timedelta(hours=48); hi+=pd.Timedelta(hours=48)
            buffer_viol += int((pd.to_datetime(ids.event_time_proxy_utc,utc=True).lt(hi)&pd.to_datetime(ids.max_stage_end_utc,utc=True).ge(lo)).sum())
        if a.path in {"development","time_frozen"}: cutoff_viol+=int(pd.to_datetime(ids.max_stage_end_utc,utc=True).ge(cutoff).sum())
        fit=joblib.load(mp); enc=fit.get("encoder"); names=[] if enc is None else enc.numeric+enc.categorical
        forbidden={"cause_group_event","cause_code_event","n_stages","max_stage_end_utc","duration_B_full_span_hours","customers_v2_event_excl_reinterruptions"}
        bad=forbidden&set(names)
        if a.task!="R_C_log": bad|={"final_C_log","final_C_log_sq"}&set(names)
        if bad: feature_viol.append({"path":str(mp),"features":sorted(bad)})
    checks += [{"check":"model_and_fit_id_hashes","value":hash_viol,"pass":hash_viol==0},{"check":"fit_test_id_intersections","value":overlaps,"pass":overlaps==0},{"check":"held_buffer_intersections","value":buffer_viol,"pass":buffer_viol==0},{"check":"time_path_label_cutoff_violations","value":cutoff_viol,"pass":cutoff_viol==0},{"check":"forbidden_feature_violations","value":len(feature_viol),"pass":len(feature_viol)==0}]

    package=json.loads((RUN.parents[1]/"PACKAGE_MANIFEST.json").read_text(encoding="utf-8")); protected=[]
    for f in package["files"]:
        p=RUN.parents[1]/f["path"]; protected.append({"path":str(p),"expected":f["sha256"],"actual":sha256(p),"unchanged":sha256(p)==f["sha256"]})
    pd.DataFrame(protected).to_csv(RUN/"evidence"/"protected_source_hash_check.csv",index=False)
    checks.append({"check":"X02_instruction_package_unchanged","value":sum(not x["unchanged"] for x in protected),"pass":all(x["unchanged"] for x in protected)})

    d=load_data(); make_figures(); curve_outputs(d)
    neg=timep[(timep.task=="E_log")].groupby("model").apply(lambda x:float((x.pred<0).mean()),include_groups=False).reset_index(name="negative_log_prediction_fraction")
    neg.to_csv(RUN/"tables"/"negative_E_prediction_fraction.csv",index=False)
    soft=[]
    for p in (RUN/"models").rglob("S04.joblib"):
        f=joblib.load(p); q=f.get("diag",{}); soft.append({"path":str(p),"task":f.get("task"),"tau":f.get("tau"),"h":f.get("h"),"b":float(f["beta"][-1]),**{k:q.get(k) for k in ["success","status","message","iterations","tau_at_bound","h_at_bound","b_at_bound"]}})
    pd.DataFrame(soft).to_csv(RUN/"tables"/"softplus_boundary_summary.csv",index=False)

    failure_log=[{"stage":"X02-A first attempt","classification":"blocking_task_resolved","result":"failed","reason":"local stage script initially resolved claude_branch root two levels too high; FileNotFoundError before audit","resolution":"local X02 script path corrected; source untouched"},{"stage":"X02-A second attempt","classification":"reporting_limitation_resolved","result":"failed","reason":"optional pandas tabulate dependency unavailable","resolution":"deterministic local Markdown serializer used; no installation"},{"stage":"X02-C/D","classification":"reporting_limitation","result":"warning","reason":"joblib could not identify physical core count and used logical core count","resolution":"no numerical/model failure"}]
    failure_log += json.loads((RUN/"evidence"/"failures_through_development.json").read_text(encoding="utf-8"))+json.loads((RUN/"evidence"/"failures_fivefold.json").read_text(encoding="utf-8"))
    write_json(RUN/"evidence"/"FAILURE_LOG.json",failure_log)
    cdf=pd.DataFrame(checks); cdf.to_csv(RUN/"tables"/"acceptance_checks.csv",index=False)
    passed=bool(cdf["pass"].all())
    validation={"completed_utc":datetime.now(timezone.utc).isoformat(),"checks":checks,"feature_violations":feature_viol,"all_required_checks_pass":passed,"rolling_F1_synthetic_test":"not applicable: F1 not implemented and explicitly skipped; no rolling feature enters a model","known_limitations":["business onset/timezone unverified","weather observed archive is not verified forecast-time information","event identity is record-level, not certified physical fault","five historical process groups are few and previously seen"]}
    write_json(RUN/"evidence"/"validation.json",validation)
    report=["# X02 validation report","",f"Acceptance status: **{'PASS' if passed else 'FAIL'}**.","",cdf.to_csv(index=False),"",
            "All exported scores were independently recomputed from event predictions. Actual fit-ID tables were checked against their validation/test events and frozen process buffers. Time-path labels end before the frozen cutoff. Core feature schemas contain no final cause, stage count, end time or outcome fields; final C appears only in R_C.","",
            "F1 and rolling features were not implemented because no auditable timestamped source was available; the synthetic rolling test is therefore not applicable rather than falsely passed.","",f"Failure and negative-result record: `evidence/FAILURE_LOG.json` ({len(failure_log)} entries)."]
    (RUN/"VALIDATION_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    write_json(RUN/"RUN_STATE.json",{"run_id":RUN.name,"stage":"X02-E","status":"completed" if passed else "blocked","completed_utc":datetime.now(timezone.utc).isoformat(),"acceptance_pass":passed,"next_allowed_stage":"X02-F" if passed else None})
    print(cdf.to_string(index=False)); print("PASS",passed)


if __name__=="__main__": main()
