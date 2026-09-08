from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RUN = Path(__file__).resolve().parents[1]
X02 = RUN.parents[1]
CLAUDE = X02.parents[1]
EVENTS = CLAUDE / "paper_revision_work_v2" / "R02" / "data" / "R02_event_master.parquet"
WINDOWS = X02 / "evidence" / "storm_windows_X01_readonly.json"
SEED = 20260907


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def interval_excluded(start: pd.Series, end: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.Series:
    return (start < hi) & (end >= lo)


def main() -> None:
    state = json.loads((RUN / "RUN_STATE.json").read_text(encoding="utf-8"))
    if state.get("stage") != "X02-A" or not state.get("stage_a_pass"):
        raise RuntimeError("X02-A has not passed")
    mem = pd.read_parquet(RUN / "EPISODE_MEMBERSHIP.parquet")
    cols = ["Incident Reference", "event_time_proxy_utc", "max_stage_end_utc", "candidate_main_E0", "candidate_main_R0c"]
    df = pd.read_parquet(EVENTS, columns=cols)
    d = df.merge(mem[["Incident Reference", "storm_names", "protected_group", "episode_id"]], on="Incident Reference", validate="one_to_one")
    d["event_time_proxy_utc"] = pd.to_datetime(d.event_time_proxy_utc, utc=True)
    d["max_stage_end_utc"] = pd.to_datetime(d.max_stage_end_utc, utc=True)
    windows = json.loads(WINDOWS.read_text(encoding="utf-8"))
    p_bounds = {
        "P1": (pd.Timestamp(windows["Arwen"]["start"]), pd.Timestamp(windows["Arwen"]["end_exclusive"])),
        "P2": (pd.Timestamp(windows["Dudley"]["start"]), pd.Timestamp(windows["Franklin"]["end_exclusive"])),
        "P3": (pd.Timestamp(windows["Babet"]["start"]), pd.Timestamp(windows["Babet"]["end_exclusive"])),
        "P4": (pd.Timestamp(windows["Ciaran"]["start"]), pd.Timestamp(windows["Ciaran"]["end_exclusive"])),
        "P5": (pd.Timestamp(windows["Henk"]["start"]), pd.Timestamp(windows["Henk"]["end_exclusive"])),
    }
    cutoff = p_bounds["P4"][0] - pd.Timedelta(hours=48)
    d["eligible_E_log"] = d.candidate_main_E0.astype(bool)
    d["eligible_R_log"] = d.candidate_main_R0c.astype(bool)
    d["eligible_R_C_log"] = d.candidate_main_R0c.astype(bool)
    d["path_A_role"] = d.protected_group.map({"P1": "development", "P2": "development", "P3": "development", "P4": "time_test", "P5": "time_test"}).fillna("nonstorm_pool")
    d["label_mature_by_time_cutoff_proxy"] = d.max_stage_end_utc.lt(cutoff)
    d["time_cutoff_utc"] = cutoff
    for p, (lo, hi) in p_bounds.items():
        d[f"intersects_{p}_buffer"] = interval_excluded(d.event_time_proxy_utc, d.max_stage_end_utc, lo - pd.Timedelta(hours=48), hi + pd.Timedelta(hours=48))
    d.to_parquet(RUN / "SPLIT_MANIFEST.parquet", index=False)

    config = {
        "run_id": RUN.name,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "source_event_sha256": sha256(EVENTS),
        "tasks": {
            "E_log": {"target": "ln(1+C)", "eligibility": "candidate_main_E0 and C>=0"},
            "R_log": {"target": "ln(D/hour)", "eligibility": "candidate_main_R0c and D>0"},
            "R_C_log": {"target": "ln(D/hour)", "eligibility": "R_log plus final ln(1+C) and square as post-event controls"},
        },
        "F0_numeric": ["pressure_msl_0h", "temperature_0h", "precipitation_24h_sum", "log_population", "urban_binary", "deprivation_gap_pct", "morans_i", "income_deprivation_rate", "season_sin", "season_cos", "time_trend"],
        "F0_categorical": ["licence_area", "rural_urban_classification"],
        "gust": "gust_0h in m/s; raw for tree; training-standardized polynomial powers for parametric models",
        "F1": {"status": "skipped", "reason": "no auditable timestamped operational/pre-forecast archive in verified contract"},
        "calendar": {"basis": "UTC proxy", "season": "sin/cos of fractional day-of-year", "trend_origin": "2021-04-01T00:00:00Z", "trend_unit": "365.2425 days"},
        "missing": "training-fold means for numeric; explicit training levels and unknown all-zero for categorical; audited main population currently complete",
        "scaling": "training-fold mean and population SD for numeric; categorical reference level dropped; no full-sample preprocessing",
        "primary_weight": "event equal",
        "selection_metric": "unweighted mean of protected-process MSE (macro-MSE)",
        "time_path": {"development_groups": ["P1", "P2", "P3"], "test_groups": ["P4", "P5"], "fit_cutoff_utc": cutoff.isoformat(), "label_maturity_proxy": "max_stage_end_utc < cutoff", "test_scoring": "single frozen scoring call after MODEL_SELECTION_LOCK"},
        "five_process_path": {"outer_groups": ["P1", "P2", "P3", "P4", "P5"], "inner": "leave one of remaining four protected groups out", "all_period_pool": "same parent population excluding outer and inner protected intervals plus 48h buffers"},
        "protection": "remove training events whose [event_time_proxy_utc,max_stage_end_utc] intersects held process interval expanded +/-48h",
        "tail": "all eligible evaluation events; no outcome p99 trimming",
        "original_scale_E_auxiliary": "max(exp(z_hat)-1,0), median/central back-transform only; never used for primary log score",
        "models": ["B00", "B01", "G02", "P00", "P02", "S01", "S02", "S03", "S04", "G05", "S05"],
    }
    # JSON is valid YAML 1.2 and avoids introducing a PyYAML runtime dependency.
    (RUN / "run_config.yaml").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = {
        "B00": {"population": "storm", "family": "mean", "gust": "none", "grid": [{}]},
        "B01": {"population": "storm", "family": "ridge_linear", "gust": "none", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "G02": {"population": "all_period", "family": "ridge_linear", "gust": "quadratic", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "P00": {"population": "all_period", "family": "ridge_linear", "gust": "quadratic+storm_offset", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "P02": {"population": "all_period", "family": "ridge_linear", "gust": "quadratic+storm_offset+storm_interactions", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "S01": {"population": "storm", "family": "ridge_linear", "gust": "linear", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "S02": {"population": "storm", "family": "ridge_linear", "gust": "quadratic", "grid": [{"lambda": x} for x in [0, .001, .1]]},
        "S03": {"population": "storm", "family": "cubic_quantile_bspline_generalized_ridge", "gust": "spline", "grid": [{"n_knots": k, "difference_penalty": dp, "control_lambda": cl} for k in [3,5] for dp in [.01,1] for cl in [.001,.1]], "extrapolation": "linear"},
        "S04": {"population": "storm", "family": "profiled_softplus_ridge", "gust": "monotone softplus", "grid": [{"control_lambda": x} for x in [.001,.1]], "tau_bounds": "training gust q01-q99", "h_bounds": [.05,20], "starts": "tau q10/q50/q75/q90 x h .5/2/5 plus b=0 boundary"},
        "G05": {"population": "all_period", "family": "HistGradientBoostingRegressor", "gust": "raw", "grid": [{"max_leaf_nodes": l, "min_samples_leaf": m} for l in [7,15] for m in [20,50]], "fixed": {"loss":"squared_error","learning_rate":.05,"max_iter":200,"early_stopping":False,"l2_regularization":1}},
        "S05": {"population": "storm", "family": "HistGradientBoostingRegressor", "gust": "raw", "grid": [{"max_leaf_nodes": l, "min_samples_leaf": m} for l in [7,15] for m in [20,50]], "fixed": {"loss":"squared_error","learning_rate":.05,"max_iter":200,"early_stopping":False,"l2_regularization":1}},
    }
    write_json(RUN / "MODEL_REGISTRY.json", registry)

    audit = {"cutoff_utc": cutoff.isoformat(), "rows": int(len(d)), "unique_ids": int(d["Incident Reference"].nunique()), "checks": {}}
    for task in ["E_log", "R_log", "R_C_log"]:
        ok = d[f"eligible_{task}"]
        audit["checks"][task] = {"parent_n": int(ok.sum()), "development_n": int((ok & d.protected_group.isin(["P1","P2","P3"])).sum()), "test_n": int((ok & d.protected_group.isin(["P4","P5"])).sum())}
    audit["checks"]["P2_not_split"] = int(d.loc[d.protected_group.eq("P2"), "episode_id"].nunique()) == 1
    audit["checks"]["test_groups_not_mature_training"] = int((d.protected_group.isin(["P4","P5"]) & d.label_mature_by_time_cutoff_proxy).sum()) == 0
    audit["checks"]["all_event_ids_unique"] = d["Incident Reference"].is_unique
    audit["stage_b_pass"] = all(v if isinstance(v, bool) else True for v in [audit["checks"]["P2_not_split"], audit["checks"]["test_groups_not_mature_training"], audit["checks"]["all_event_ids_unique"]])
    write_json(RUN / "SPLIT_AUDIT.json", audit)

    contract = f"""# X02 experiment contract

Frozen UTC: `{config['frozen_utc']}`. Input SHA256: `{config['source_event_sha256']}`. Seed: `{SEED}`.

## Scope and estimands

This is a retrospective conditional prediction study among corrected-contract events in the pre-existing main cause population. E_log is ln(1+C); R_log is ln(D/hour); R_C_log adds final ln(1+C) and its square and is explicitly post-event conditional. All primary scores are squared error on the log target. Test outcomes are never used for trimming.

F0 contains observed historical weather at/through the proxy event hour, static regional covariates, licence/RUC categories, transferable seasonal terms and a continuous trend. Final cause, stage count, end time, final event totals and storm-name identity are not F0 predictors. F1 is skipped because no timestamped operational or forecast archive is verified.

## Path A (must finish first)

Development groups are P1 Arwen, P2 Dudley/Eunice/Franklin and P3 Babet. P4 Ciarán and P5 Henk form the fixed time test. The fitting cutoff is `{cutoff.isoformat()}`. Labels are treated as mature only when the recorded maximum stage end is before the cutoff; publication delay remains unknown. Development tuning uses leave-one-development-process-out macro-MSE. After selection is locked, one frozen fit scores P4/P5 without updating between storms.

## Path B (only after time-test sealing)

Five outer folds leave out P1–P5. Tuning is nested by leaving one of the remaining four groups out. This is retrospective cross-process validation and not forward prediction.

## Protection and preprocessing

The fitting interval [event proxy start, recorded max end] may not intersect a held process interval expanded by 48 hours. Actual fit IDs are saved per fitted model. Numeric means/scales, categorical levels, knots, optimisation and tuning are training-only. Unknown categories map to all-zero reference coding.

## Selection

Candidates and grids are exactly those in `MODEL_REGISTRY.json`. The primary criterion is protected-process macro-MSE. Within 1% of the lowest score, reliable and simpler candidates are preferred in the predeclared order B00, B01, S01/G02/S02, P00, P02, S03, S04, G05/S05. E, R and R_C are selected independently. All valid and failed candidates remain reported.

## Inference boundary

The study can evaluate conditional prediction transfer across five historical process groups under observed-weather covariates. It cannot establish onset-time forecast performance, causal damage thresholds, storm-total impact, or an independent untouched confirmation set.
"""
    (RUN / "EXPERIMENT_CONTRACT.md").write_text(contract, encoding="utf-8")
    audit["protocol_files"] = {p.name: sha256(p) for p in [RUN / "run_config.yaml", RUN / "MODEL_REGISTRY.json", RUN / "EXPERIMENT_CONTRACT.md", RUN / "SPLIT_MANIFEST.parquet", RUN / "SPLIT_AUDIT.json"]}
    write_json(RUN / "evidence" / "PROTOCOL_LOCK.json", {"frozen_utc": config["frozen_utc"], "hashes": audit["protocol_files"], "immutable_after_stage_b": True})
    write_json(RUN / "RUN_STATE.json", {"run_id": RUN.name, "stage": "X02-B", "status": "completed", "completed_utc": datetime.now(timezone.utc).isoformat(), "stage_a_pass": True, "stage_b_pass": audit["stage_b_pass"], "next_allowed_stage": "X02-C"})
    print(json.dumps(audit, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
