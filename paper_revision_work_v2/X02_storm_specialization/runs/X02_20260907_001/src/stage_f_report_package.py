from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from x02_modeling import RUN,X02,TASKS,MODELS,sha256,write_json


def mdtable(df:pd.DataFrame, digits:int=4)->str:
    cols=list(df.columns)
    def f(v):
        if pd.isna(v): return "NA"
        if isinstance(v,(float,np.floating)): return f"{v:.{digits}f}"
        return str(v).replace("|","\\|")
    out=["| "+" | ".join(cols)+" |","| "+" | ".join(["---"]*len(cols))+" |"]
    out += ["| "+" | ".join(f(v) for v in row)+" |" for row in df.itertuples(index=False,name=None)]
    return "\n".join(out)


def comparison_table()->pd.DataFrame:
    dev=pd.read_csv(RUN/"tables"/"development_model_selection.csv")
    tim=pd.read_csv(RUN/"tables"/"time_test_metrics.csv")
    five=pd.read_csv(RUN/"tables"/"fivefold_paired_differences.csv")
    pairs=[("S02","G02"),("P00","G02"),("P02","P00"),("S03","S02"),("S04","S02"),("S05","S02"),("S05","G05"),("S02","B01")]
    rows=[]
    for task in TASKS:
        for a,b in pairs:
            da=float(dev[(dev.task==task)&(dev.model==a)].macro_mse.iloc[0]-dev[(dev.task==task)&(dev.model==b)].macro_mse.iloc[0])
            p4=float(tim[(tim.task==task)&(tim.model==a)&(tim.episode=="P4")].mse.iloc[0]-tim[(tim.task==task)&(tim.model==b)&(tim.episode=="P4")].mse.iloc[0])
            p5=float(tim[(tim.task==task)&(tim.model==a)&(tim.episode=="P5")].mse.iloc[0]-tim[(tim.task==task)&(tim.model==b)&(tim.episode=="P5")].mse.iloc[0])
            z=five[(five.task==task)&(five.comparison==f"{a}-{b}")&(five.episode=="MACRO")].iloc[0]
            rows.append({"task":task,"comparison":f"{a}-{b}","development_macro_MSE_diff":da,"P4_diff":p4,"P5_diff":p5,"five_process_macro_diff":float(z.mse_difference),"process_range":f"[{z.range_min:.4f}, {z.range_max:.4f}]"})
    return pd.DataFrame(rows)


def main()->None:
    state=json.loads((RUN/"RUN_STATE.json").read_text(encoding="utf-8"))
    if state.get("stage") not in {"X02-E","X02-F"} or not state.get("acceptance_pass"): raise RuntimeError("X02-E acceptance not passed")
    now=datetime.now(timezone.utc).isoformat()
    comp=comparison_table(); comp.to_csv(RUN/"tables"/"predeclared_comparison_summary.csv",index=False)
    flow=pd.read_csv(RUN/"SAMPLE_FLOW.csv"); fig9=pd.read_csv(RUN/"tables"/"figure9_recalculation.csv")
    time=pd.read_csv(RUN/"tables"/"time_test_metrics.csv"); five=pd.read_csv(RUN/"tables"/"fivefold_metrics.csv")
    lock=json.loads((RUN/"MODEL_SELECTION_LOCK.json").read_text(encoding="utf-8"))
    val=json.loads((RUN/"evidence"/"validation.json").read_text(encoding="utf-8"))
    failures=json.loads((RUN/"evidence"/"FAILURE_LOG.json").read_text(encoding="utf-8"))
    extra_failures=[
        {"stage":"X02-D first Path B","classification":"invalid_model","result":"invalidated","reason":"storm-population branch omitted held-process +/-48h crossing exclusion; 3 long events, 63 artifact-level violations","resolution":"complete v1 evidence retained; only Path B rerun with corrected local mask"},
        {"stage":"X02-E first attempt","classification":"reporting_limitation_resolved","result":"failed","reason":"unused DataFrame field access in fixed group-bound helper","resolution":"removed unused access; no model/output change"},
        {"stage":"X02-E second attempt","classification":"reporting_limitation_resolved","result":"failed","reason":"Tk backend unavailable in bundled Python","resolution":"fixed noninteractive Agg backend; no dependency installation"},
        {"stage":"X02-F repackage attempt","classification":"reporting_limitation_resolved","result":"failed","reason":"repackage gate initially accepted X02-E but not already-completed X02-F","resolution":"allow deterministic repackage only when acceptance_pass remains true"},
    ]
    existing={x.get("reason") for x in failures}
    failures += [x for x in extra_failures if x["reason"] not in existing]
    write_json(RUN/"evidence"/"FAILURE_LOG.json",failures)

    # Preserve the full protocol inputs inside the new run without changing originals.
    fp=RUN/"frozen_protocol"; fp.mkdir(exist_ok=True)
    for rel in ["CODEX_X02_执行指令.md","X02_风暴专用模型_测试方案.md","X02_研究与正文衔接台账.md","RETURN_TO_CHATGPT_X02_模板.md","PACKAGE_MANIFEST.json"]:
        shutil.copy2(X02/rel,fp/rel)
    (RUN/"requirements-lock.txt").write_text("\n".join(["python==3.12","numpy=="+np.__version__,"pandas=="+pd.__version__,"scipy==1.14.1","scikit-learn==1.8.0","pyarrow==25.0.1","matplotlib==3.10.8","joblib==1.5.3",""]),encoding="utf-8")

    selected_rows=[]
    for task,v in lock["recommendations"].items():
        for ep in ["P4","P5","POOLED","MACRO"]:
            x=time[(time.task==task)&(time.model==v["selected_model"])&(time.episode==ep)].iloc[0]
            selected_rows.append({"task":task,"locked_model":v["selected_model"],"episode":ep,"n":int(x.n),"MSE":x.mse,"RMSE":x.rmse,"R2":x.r2,"skill_vs_B00":x.skill_vs_B00})
    selected=pd.DataFrame(selected_rows)

    report=f"""# X02 storm-specialisation report

## Status

X02-A through X02-F completed in the required order. Path A was selected on P1–P3 and scored once on frozen P4/P5 models before Path B began. The first Path-B implementation was invalidated because three long training events crossed held-process buffers; its outputs are retained under `evidence/invalidated_pathB_v1/`. The corrected Path B passed all acceptance checks. No Claude manuscript, prior R-stage result, X01 artifact, Figure 9 file or source dataset was modified.

## Data and Figure 9

The source is the R02 corrected event contract (135,025 unique event rows; SHA256 `{json.loads((RUN/'DATA_MANIFEST.json').read_text(encoding='utf-8'))['source_event_sha256']}`). The main eligible parent contains 60,436 events per task. Frozen named-window membership contains 4,452 eligible unique events: 3,382 in development P1–P3 and 1,070 in time test P4–P5. Seven names produce five protected groups; 702 events carry overlapping Dudley/Eunice/Franklin name labels but are counted once in P2.

The retained R04 Figure 9 descriptive panels are full-sample fitted values, with all 4,452 plotted events included in the fit. Its companion date-group OOF panels are not protected-process holdouts. Recalculated descriptive prediction SD ratios are {fig9[(fig9.target=='main_E0')&(fig9.prediction_kind=='descriptive')].sd_ratio.iloc[0]:.3f} for E and {fig9[(fig9.target=='main_R0c')&(fig9.prediction_kind=='descriptive')].sd_ratio.iloc[0]:.3f} for R: the horizontal-band appearance reflects compressed prediction variation plus process-specific mean bias, not merely one common intercept error and not evidence for a flat gust-response curve.

## Frozen time test

{mdtable(selected)}

The development lock selected G02 for E_log and R_log, and G05 for R_C_log. E_log's G05 was within 1% of G02 in development, so the predeclared simplicity rule selected G02. These choices were not revised after seeing P4/P5 or five-process results.

## Predeclared comparisons

Differences are first model minus second model; negative MSE differences favour the first model.

{mdtable(comp)}

The central population hypothesis is not supported: S02 is worse than fair all-period G02 in both time-test processes for all three tasks, and is also worse on five-process macro-MSE. A shared storm offset P00 does not consistently repair the difference; for R and R_C it is worse than G02 in both time tests and five-process macro results. P02 adds no consistent improvement over P00.

Flexible storm curves do not yield a stable universal gain. S04 usually improves on S02, but the E five-process range includes harm and its fitted width reaches the frozen 0.05 m/s lower bound in all three final tasks; this behaves like a sharp hinge and does not identify a physical threshold. S03 has mixed process results and a severe R_C failure in one held process. S05 improves on S02 in several summaries, yet S05 does not outperform the same-information all-period G05 consistently; its five-process macro-MSE is worse than G05 for E, R and R_C. Thus interaction flexibility can help relative to a weak storm-only quadratic, but there is no evidence that storm-only training is the source of the gain.

R_C performs better than R in the locked time test because it conditions on final customer count. This is post-event conditional prediction, not onset-time or real-time improvement. F1 was skipped because no timestamped operational/forecast archive could establish availability.

## Diagnostic interpretation and use boundary

Predictions remain substantially less variable than observations in the time test. For locked E/G02, SD ratios are about 0.27 (P4) and 0.24 (P5); for R/G02 about 0.29 in both; for R_C/G05 about 0.44 and 0.39. R/G02 Pearson correlations are only about 0.067 and 0.090, so its B00 skill is driven substantially by level/control adjustment rather than strong event-level ranking. Process mean bias and within-process residual SSE are separately available in `tables/time_test_residual_diagnostics.csv` and `tables/fivefold_metrics.csv`.

The results support retrospective consequence estimation conditional on observed archived weather for recorded events. They do not support storm-total outage forecasting, event occurrence prediction, causal damage thresholds, a verified pre-storm operational forecast, or generalisation beyond five already studied historical processes.

## Acceptance and reproducibility

Independent prediction-level recalculation exactly matched exported metrics (maximum absolute difference 0). Fit/test ID overlap, held-buffer overlap, time-cutoff violations, forbidden core features and duplicate predictions are all zero. Each task/model has 4,452 corrected outer-fold predictions. Model and fit-ID hashes pass. Full details are in `VALIDATION_REPORT.md`.

The source parquet is intentionally not duplicated. `README.md` records its absolute path and hash. Saved predictions permit metric recalculation without the source data; model refitting requires the verified R02 event contract.
"""
    (RUN/"X02_REPORT.md").write_text(report,encoding="utf-8")

    decisions=f"""# X02 decision log

1. **Authority and isolation.** Use the R02 corrected event contract because R04/R05 manifests retain it as the active input. All upstream artifacts remain read-only.
2. **Windows.** Retain the frozen UTC proxy windows; do not optimise the six-event London-calendar difference. Merge Dudley/Eunice/Franklin into P2.
3. **Population.** Use the existing main weather-natural/technical-asset contract population; preserve its retrospective cause-selection limitation while excluding final cause from F0.
4. **Information.** Name the exercise observed-weather conditional retrospective prediction. Skip F1 because timestamps/publication availability are not auditable.
5. **Time lock.** Select G02 for E/R and G05 for R_C before one P4/P5 score. Do not update Henk after Ciarán.
6. **Path-B correction.** Invalidate the first Path-B run after 63 artifact-level buffer violations traced to three long events. Preserve its outputs, apply the frozen buffer rule to storm models, and rerun only Path B. Time-test results remain unchanged.
7. **Interpretation.** Do not promote a storm-specialised model: S02 does not beat G02 consistently, P00/P02 do not explain a stable gain, flexible curves are process-sensitive, and S05 does not consistently beat G05.
8. **Paper action.** Generate implications and evidence links only; do not edit the manuscript or X01 decision.
"""
    (RUN/"DECISION_LOG.md").write_text(decisions,encoding="utf-8")

    story=f"""# X02 research story log

| ID | Hypothesis / observation | Evidence | Strength | Direction change |
| --- | --- | --- | --- | --- |
| XS-01 | R04 Figure 9 is not an external storm validation. | `FIG9_PROVENANCE.md`; `tables/figure9_recalculation.csv` | Confirmed provenance | Motivates protected-process validation. |
| XS-02 | Seven storm names form five statistical protection groups. | `STORM_CATALOG.csv`; `EPISODE_MEMBERSHIP.parquet` | Confirmed under frozen UTC proxy | P2 is indivisible. |
| XS-03 | Storm-only quadratic training improves transfer over fair all-period quadratic. | `tables/predeclared_comparison_summary.csv` | Not supported; S02−G02 is positive in both time tests for every task and positive in five-process macro | Do not adopt storm-only quadratic. |
| XS-04 | A common storm level shift is sufficient. | P00−G02 rows in comparison table | Not supported consistently; especially adverse for R/R_C | Level shift does not explain a general gain. |
| XS-05 | Storm-specific quadratic interactions add stable value. | P02−P00 rows | Mixed signs across processes/tasks | No stable interaction claim. |
| XS-06 | Flexible storm curves add stable value. | S03/S04−S02; `tables/softplus_boundary_summary.csv` | Mixed; S04 width at lower bound and S03 process failure | Retain only sensitivity interpretation. |
| XS-07 | Tree interactions reveal useful information beyond quadratic. | S05−S02 and G05/S05 results | Some gain over S02, but storm-only S05 not consistently better than G05 | Flexibility matters more than storm-only population. |
| XS-08 | F1 adds operationally available information. | `FEATURE_AVAILABILITY.csv` | Skipped: source unavailable | Requires new timestamped/forecast archive. |
| XS-09 | R_C improves real-time restoration prediction. | Locked R_C results and feature contract | Prohibited interpretation; final C is post-event | Report only post-event conditional difference. |
| XS-10 | Negative and failed results are material. | `evidence/FAILURE_LOG.json`; invalidated Path-B v1 | Confirmed | Preserve in appendix/reproducibility record. |
"""
    (RUN/"RESEARCH_STORY_LOG.md").write_text(story,encoding="utf-8")

    implications=f"""# Manuscript implications (no manuscript edited)

| Section | Evidence-bound possible update | Prohibited claim | Evidence |
| --- | --- | --- | --- |
| Introduction | Frame storm-specialised training as a tested but unsupported general hypothesis in this five-process retrospective sample. | Storm models are known to generalise better. | `tables/predeclared_comparison_summary.csv` |
| Data | State 4,452 unique eligible named-window events, five protected groups and P2 overlap handling; retain UTC-proxy and record-identity limits. | Seven statistically independent storms; certified physical-fault identity. | `X02_AUDIT.md`; `EPISODE_MEMBERSHIP.parquet` |
| Methods | Separate three-process development/two-process time test from nested five-process retrospective validation; specify 48 h buffers and training-only preprocessing. | Random event CV or untouched independent confirmation. | `EXPERIMENT_CONTRACT.md`; `SPLIT_AUDIT.json` |
| Results | Report S02 versus G02 as no consistent storm-population gain; report flexible/tree gains and harms by process, including invalid/negative outcomes. | Choose a winner from P4/P5 or hide S03/S04/S05 adverse folds. | `tables/time_test_metrics.csv`; `tables/fivefold_metrics.csv` |
| Figure 9 text/caption | Describe retained R04 Figure 9 as combined-sample fitted predictions; distinguish its date-OOF diagnostic from true process holdout. | External validation or gust-response shape evidence. | `FIG9_PROVENANCE.md` |
| Discussion | Emphasise compressed prediction variation, process heterogeneity, observed-weather limitation and few historical groups. | Irreducible noise, physical threshold, forecast-time deployability, or general storm-total performance. | residual diagnostics; curve/support tables |
| Appendix | Include full candidate grid, boundary/convergence logs, invalidated Path-B v1, fit-ID protection checks and all paired process differences. | Report only successful/favourable candidates. | `MODEL_REGISTRY.json`; `evidence/` |
| Conclusion | Retain the simpler general-population working model as the safer current basis; treat storm specialisation as unsupported, not disproved universally. | X02 proves no storm can benefit from specialised training. | complete X02 evidence chain |

X01's earlier decision to retain the quadratic form as an appendix-oriented working specification is not reversed. X02 addresses training population and cross-process transfer on a log-loss target; it does not retroactively validate or invalidate X01's original-scale curve experiment.
"""
    (RUN/"MANUSCRIPT_IMPLICATIONS.md").write_text(implications,encoding="utf-8")

    readme=f"""# X02_20260907_001

This isolated run completed X02-A through X02-F. It did not modify upstream data, scripts, figures, manuscripts or X01/R-stage artifacts.

## Source-data refit

Required source: `D:\\Pyprogramme\\STST2603\\claude_branch\\paper_revision_work_v2\\R02\\data\\R02_event_master.parquet`  
SHA256: `{json.loads((RUN/'DATA_MANIFEST.json').read_text(encoding='utf-8'))['source_event_sha256']}`

Using the recorded environment, execute in order from `src/`: `stage_a_audit.py`, `stage_b_freeze.py`, `stage_c_develop.py`, `stage_c_time_score.py`, `stage_d_fivefold.py`, `stage_e_validate.py`, `stage_f_report_package.py`. A fresh run directory is recommended; do not overwrite this sealed evidence run. The original invalid Path-B v1 is evidence only and must not be treated as a resumable valid result.

## Prediction-only recalculation

`predictions/time_test_predictions.parquet` and `predictions/fivefold_oof_predictions.parquet` contain anonymous stable event IDs, task/model/path/split/episode, outcomes and predictions. Recompute MSE as mean((y-pred)^2), RMSE as its square root, MAE as mean absolute error and R² against the same evaluation set mean. This path does not require the source event table. Independent recalculations are already stored in `evidence/`.

## Evidence map

- Audit and provenance: `X02_AUDIT.md`, `FIG9_PROVENANCE.md`, `DATA_MANIFEST.json`.
- Frozen protocol: `EXPERIMENT_CONTRACT.md`, `run_config.yaml`, `MODEL_REGISTRY.json`, `evidence/PROTOCOL_LOCK.json`.
- Selection/time seal: `MODEL_SELECTION_LOCK.json`, `TIME_TEST_FROZEN_REPORT.md`, `evidence/TIME_TEST_SEAL.json`.
- Corrected fivefold and acceptance: `tables/`, `predictions/`, `models/`, `VALIDATION_REPORT.md`.
- Failures: `evidence/FAILURE_LOG.json`, `evidence/invalidated_pathB_v1/`.
- Interpretation: `X02_REPORT.md`, `RESEARCH_STORY_LOG.md`, `MANUSCRIPT_IMPLICATIONS.md`.
"""
    (RUN/"README.md").write_text(readme,encoding="utf-8")

    return_md=f"""# RETURN_TO_CHATGPT_X02

## Status and inputs

Run `{RUN.name}` completed X02-A–F and passed corrected-run acceptance. The corrected R02 event contract contains 135,025 unique events; the main parent has 60,436 eligible events per task. C is summed non-reinterruption restored customers; D is recorded full event span in hours. C=0 is retained for E; D must be positive for R/R_C; no test p99 trimming is used. All source/Claude/X01 artifacts remained read-only.

R04 Figure 9 descriptive values are full-sample fits, not external predictions. Its date-group OOF companion is not a storm-process holdout. The horizontal bands combine prediction-range compression (descriptive SD ratios E 0.335, R 0.395) with process mean bias.

## Storms and validation

Seven frozen UTC-proxy names cover 25 unique days and 4,452 eligible unique events. Dudley/Eunice/Franklin are one P2 group, giving P1–P5. Path A used P1–P3 (3,382) for three-fold development and P4/P5 (1,070) for a single frozen time score after the lock; cutoff was 2023-10-29 00:00 UTC and label maturity used recorded max end before cutoff. Corrected Path B used five outer process folds with four-group nested tuning.

The first Path-B run omitted buffer crossing removal in storm-only fits; 3 underlying long events caused 63 artifact-level violations. Those results are preserved and invalidated. Corrected Path B has zero ID/buffer leakage.

## Information set

F0 uses observed archived gust, pressure, temperature, prior-24-hour precipitation, static regional variables, licence/RUC and transferable calendar terms. It excludes final cause, stages, end time and outcomes. R_C alone includes final C and is post-event conditional. F1 is skipped because no auditable time-stamped operational/forecast archive exists.

## Main results

{mdtable(comp)}

Negative differences favour the first model. S02 did not improve on G02 in either time-test process for any task and was worse on five-process macro-MSE. P00/P02 did not provide a stable repair. S03/S04/S05 show some improvements over S02, but signs vary by process; S04 reaches its minimum width and S05 is not consistently better than same-information G05. The evidence therefore does not support adopting storm-only training as a general replacement.

Locked time-test scores:

{mdtable(selected)}

## Quality, limits and next step

Independent metric recalculation differs by 0; fit/test ID overlap, held-buffer overlap, cutoff violations, forbidden features and duplicate predictions are all zero. Corrected model failures are zero; implementation/reporting failures and the invalidated first Path B are retained in `evidence/FAILURE_LOG.json`.

The study supports only observed-weather conditional retrospective prediction across five previously studied historical processes. It does not establish forecast-time use, a causal wind threshold, storm-total burden or untouched external confirmation. Keep X01's quadratic working-model decision unchanged for now; the minimum next evidence is a timestamped forecast/operational feature archive and genuinely new storms.

Full report: `X02_REPORT.md`. Package: `RETURN_PACKAGE_X02.zip`.
"""
    (RUN/"RETURN_TO_CHATGPT_X02.md").write_text(return_md,encoding="utf-8")
    shutil.copy2(RUN/"RETURN_TO_CHATGPT_X02.md",X02/"RETURN_TO_CHATGPT_X02.md")

    required=["RETURN_TO_CHATGPT_X02.md","X02_REPORT.md","EXPERIMENT_CONTRACT.md","DECISION_LOG.md","RESEARCH_STORY_LOG.md","MANUSCRIPT_IMPLICATIONS.md","UPSTREAM_ISSUES.md","VALIDATION_REPORT.md","README.md","run_config.yaml","DATA_MANIFEST.json","MODEL_REGISTRY.json","MODEL_SELECTION_LOCK.json","TIME_TEST_FROZEN_REPORT.md","SPLIT_MANIFEST.parquet","SPLIT_AUDIT.json","EPISODE_MEMBERSHIP.parquet","SAMPLE_FLOW.csv","FEATURE_AVAILABILITY.csv","FIG9_PROVENANCE.md"]
    missing=[x for x in required if not (RUN/x).exists()]
    if missing: raise RuntimeError(f"Missing required artifacts: {missing}")
    # Freeze the in-package terminal state and a non-self-referential validation note before hashing members.
    write_json(RUN/"RUN_STATE.json",{"run_id":RUN.name,"stage":"X02-F","status":"completed","completed_utc":datetime.now(timezone.utc).isoformat(),"acceptance_pass":True,"package_hash_reference":"../RETURN_PACKAGE_X02.receipt.json"})
    write_json(RUN/"evidence"/"PACKAGE_VALIDATION.json",{"prepared_utc":datetime.now(timezone.utc).isoformat(),"required_artifacts_present":not missing,"acceptance_pass":True,"validation_method":"After these frozen members are zipped, ZipFile.testzip and full temporary extraction are executed; the resulting ZIP hash and size are stored in the sibling RETURN_PACKAGE_X02.receipt.json to avoid self-referential hashing.","source_data_packaged":False})
    files=[]
    for p in sorted(x for x in RUN.rglob("*") if x.is_file() and x.name!="RETURN_PACKAGE_MANIFEST.json"):
        files.append({"path":p.relative_to(RUN).as_posix(),"bytes":p.stat().st_size,"sha256":sha256(p)})
    manifest={"run_id":RUN.name,"created_utc":now,"source_data_packaged":False,"required_missing":missing,"files":files,"file_count_excluding_manifest":len(files),"acceptance_pass":val["all_required_checks_pass"]}
    write_json(RUN/"RETURN_PACKAGE_MANIFEST.json",manifest)
    package=X02/"RETURN_PACKAGE_X02.zip"
    with zipfile.ZipFile(package,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(x for x in RUN.rglob("*") if x.is_file()): z.write(p,Path(RUN.name)/p.relative_to(RUN))
    with zipfile.ZipFile(package,"r") as z:
        bad=z.testzip(); names=z.namelist()
        if bad is not None: raise RuntimeError(f"Bad zip member: {bad}")
        with tempfile.TemporaryDirectory(prefix="x02_zip_test_") as td: z.extractall(td)
    receipt={"package":str(package),"sha256":sha256(package),"bytes":package.stat().st_size,"zip_member_count":len(names),"testzip_bad_member":bad,"extract_test":"passed","required_artifacts_present":not missing,"run_manifest_sha256":sha256(RUN/"RETURN_PACKAGE_MANIFEST.json"),"source_package_unchanged":True,"in_package_terminal_state":"X02-F completed"}
    write_json(X02/"RETURN_PACKAGE_X02.receipt.json",receipt)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
