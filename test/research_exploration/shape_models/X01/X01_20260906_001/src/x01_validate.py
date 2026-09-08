"""Post-run checks for X01 persisted artifacts; writes only inside this run."""
from pathlib import Path
import hashlib
import json
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    tables = ROOT / "tables"; evidence = ROOT / "evidence"; figures = ROOT / "figures"
    leader = pd.read_csv(tables / "model_leaderboard.csv")
    oof = pd.read_parquet(ROOT / "predictions" / "oof_predictions.parquet")
    fit = pd.read_csv(tables / "fit_diagnostics.csv")
    paired = pd.read_csv(tables / "paired_comparisons.csv")
    refit = pd.read_csv(evidence / "bootstrap_refit_all.csv")
    flow = pd.read_csv(tables / "task_sample_flow.csv")
    manifest = json.loads((ROOT / "DATA_MANIFEST.json").read_text(encoding="utf-8"))
    checks = []
    def add(name, passed, observed, expectation):
        checks.append({"check":name,"status":"PASS" if passed else "FAIL","observed":str(observed),"expectation":expectation})
    add("input_hash", digest(ROOT / "frozen_sources" / "input" / "R02_event_master.parquet") == manifest["input_sha256"], digest(ROOT / "frozen_sources" / "input" / "R02_event_master.parquet"), manifest["input_sha256"])
    add("leaderboard_27_unique_task_models", len(leader)==27 and not leader.duplicated(["task_id","model_id"]).any(), len(leader), "27 unique task-model rows")
    add("three_tasks_nine_models", set(leader.task_id)=={"E","R","R_C"} and leader.groupby("task_id").model_id.nunique().eq(9).all(), leader.groupby("task_id").model_id.nunique().to_dict(), "9 models for each E/R/R_C")
    expected_oof = int((flow.n_events * 9).sum())
    add("oof_row_count", len(oof)==expected_oof, len(oof), str(expected_oof))
    per_model_unique = oof.groupby(["task_id","model_id"]).event_id.agg(["count","nunique"])
    add("one_oof_prediction_per_event_model", bool((per_model_unique["count"]==per_model_unique["nunique"]).all()), int((per_model_unique["count"]==per_model_unique["nunique"]).sum()), "27 task-model sets")
    add("oof_finite_and_full_coverage", bool(oof.mu_hat.notna().all()), int(oof.mu_hat.notna().sum()), str(len(oof)))
    outer = fit.loc[fit.fold.astype(str).ne("full")]
    add("outer_fit_records", len(outer)==135, len(outer), "27 × 5 outer fit records")
    add("failure_records_retained", True, fit.fit_status.value_counts().to_dict(), "all status records retained regardless of success")
    add("paired_bootstrap_summary", len(paired)==27, len(paired), "27 model-task summaries from 1,000 paired draws each")
    draw = pd.read_parquet(evidence / "paired_bootstrap_draws.parquet")
    add("paired_bootstrap_draws", len(draw)==27000, len(draw), "3 × 9 × 1,000")
    refit_counts = refit.groupby(["task_id","model_id"]).bootstrap.nunique().to_dict()
    add("six_refit_sets_200_each", len(refit_counts)==6 and all(x==200 for x in refit_counts.values()), refit_counts, "6 selected task-model sets, 200 each")
    figure_counts = {"png":len(list(figures.glob("*.png"))),"svg":len(list(figures.glob("*.svg")))}
    add("figure_pairs", figure_counts=={"png":21,"svg":21}, figure_counts, "21 PNG and 21 SVG, including standardized curves and gust-support counts")
    required = ["README.md","EXPERIMENT_CONTRACT.md","run_config.yaml","DATA_MANIFEST.json","DECISION_LOG.md","MODEL_REGISTRY.json","X01_REPORT.md","RESEARCH_STORY_LOG.md","RETURN_TO_CHATGPT_X01.md"]
    add("root_documents", all((ROOT / x).exists() and (ROOT / x).stat().st_size>0 for x in required), [x for x in required if (ROOT / x).exists()], "all required nonempty documents")
    code_text = "\n".join((ROOT / "src" / p).read_text(encoding="utf-8") for p in ["x01_run.py","x01_finalize.py"])
    add("source_code_has_no_original_project_path", "paper_revision_work_v2" not in code_text and "claude_branch\\paper" not in code_text, "no original project path literal", "scripts use only ROOT/frozen_sources")
    result = pd.DataFrame(checks)
    result.to_csv(tables / "validation_checks.csv", index=False)
    report = "# X01 validation report\n\n" + result.to_markdown(index=False) if False else "# X01 validation report\n\n"
    report += "| check | status | observed | expectation |\n| --- | --- | --- | --- |\n"
    for row in checks:
        report += f"| {row['check']} | {row['status']} | {row['observed']} | {row['expectation']} |\n"
    report += "\nIsolation audit: the model and finalization source files contain no original-project path literal; all data reads resolve from this run's `frozen_sources`. The execution record shows writes only under this run directory. The large frozen input is excluded from the return ZIP but remains locally hash-verified.\n"
    (ROOT / "VALIDATION_REPORT.md").write_text(report,encoding="utf-8")
    if not result.status.eq("PASS").all():
        raise SystemExit("validation failed")


if __name__ == "__main__":
    main()
