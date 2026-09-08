from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow
import scipy
import sklearn


RUN = Path(__file__).resolve().parents[1]
X02 = RUN.parents[1]
PROJECT = X02.parents[1]
EVENTS = PROJECT / "paper_revision_work_v2" / "R02" / "data" / "R02_event_master.parquet"
EVENT_MANIFEST = PROJECT / "paper_revision_work_v2" / "R02" / "data" / "EVENT_MANIFEST.json"
WINDOWS = X02 / "evidence" / "storm_windows_X01_readonly.json"
R04 = PROJECT / "paper_revision_work_v2" / "R04" / "R04_B1_all_valid_v1"
FIG9_SCRIPT = PROJECT / "scripts" / "final_combined_analysis" / "figure9_storm_validation.py"
X01_CODE = PROJECT / "test" / "research_exploration" / "shape_models" / "X01" / "X01_20260906_001" / "src" / "x01_run.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    def cell(v: object) -> str:
        if isinstance(v, float):
            return "" if np.isnan(v) else f"{v:.8g}"
        return str(v).replace("|", "\\|")
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in df.itertuples(index=False, name=None))
    return "\n".join(lines)


def windows_frame() -> pd.DataFrame:
    raw = json.loads(WINDOWS.read_text(encoding="utf-8"))
    rows = []
    group = {"Arwen": "P1", "Dudley": "P2", "Eunice": "P2", "Franklin": "P2", "Babet": "P3", "Ciaran": "P4", "Henk": "P5"}
    role = {"P1": "development", "P2": "development", "P3": "development", "P4": "time_test", "P5": "time_test"}
    for name, v in raw.items():
        start = pd.Timestamp(v["start"])
        end = pd.Timestamp(v["end_exclusive"])
        rows.append({"storm_name": name, "start_utc": start, "end_exclusive_utc": end,
                     "window_days": (end - start).total_seconds() / 86400,
                     "protected_group": group[name], "role": role[group[name]],
                     "calendar": v["calendar"], "date_source": v["date_source"],
                     "endpoint": v["endpoint"]})
    return pd.DataFrame(rows)


def assign_membership(df: pd.DataFrame, wf: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"Incident Reference": df["Incident Reference"].astype(str),
                        "event_time_proxy_utc": pd.to_datetime(df["event_time_proxy_utc"], utc=True)})
    memberships = []
    local_memberships = []
    for _, w in wf.iterrows():
        m = (out.event_time_proxy_utc >= w.start_utc) & (out.event_time_proxy_utc < w.end_exclusive_utc)
        out[f"storm_{w.storm_name}"] = m
        memberships.append((w.storm_name, m))
        local_start = w.start_utc.tz_convert("Europe/London").normalize()
        local_end = w.end_exclusive_utc.tz_convert("Europe/London").normalize()
        local_t = out.event_time_proxy_utc.dt.tz_convert("Europe/London")
        local_memberships.append((w.storm_name, (local_t >= local_start) & (local_t < local_end)))
    out["storm_names"] = ["|".join(name for name, m in memberships if bool(m.iloc[i])) for i in range(len(out))]
    out["window_count"] = out[[c for c in out if c.startswith("storm_") and c != "storm_names"]].sum(axis=1).astype(int)
    group_map = {"Arwen": "P1", "Dudley": "P2", "Eunice": "P2", "Franklin": "P2", "Babet": "P3", "Ciaran": "P4", "Henk": "P5"}
    def group_for(names: str) -> str:
        if not names:
            return "NONE"
        gs = {group_map[n] for n in names.split("|")}
        if len(gs) != 1:
            raise RuntimeError(f"Membership crosses protected groups: {names}")
        return next(iter(gs))
    out["protected_group"] = out.storm_names.map(group_for)
    out["episode_id"] = out["protected_group"].map(lambda s: "" if s == "NONE" else "EP-" + s)
    local_names = pd.Series(["|".join(name for name, m in local_memberships if bool(m.iloc[i])) for i in range(len(out))])
    out["london_calendar_storm_names"] = local_names
    out["utc_london_membership_diff"] = out.storm_names.ne(local_names)
    return out


def safe_stats(s: pd.Series) -> dict[str, float | int | None]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if len(x) == 0:
        return {"n": 0, "mean": None, "sd": None, "p50": None, "p95": None, "max": None}
    return {"n": int(len(x)), "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
            "p50": float(x.quantile(.5)), "p95": float(x.quantile(.95)), "max": float(x.max())}


def fig9_audit() -> tuple[pd.DataFrame, str]:
    rows = []
    for target in ["main_E0", "main_R0c"]:
        for kind in ["descriptive", "OOF_diagnostic"]:
            p = R04 / target / f"figure9_{kind}_events.csv"
            x = pd.read_csv(p)
            rows.append({
                "target": target, "prediction_kind": kind, "path": str(p), "sha256": sha256(p),
                "rows": int(len(x)), "unique_events": int(x["Incident Reference"].nunique()),
                "duplicate_event_rows": int(x.duplicated("Incident Reference").sum()),
                "was_in_this_fit_n": int(x["was_in_this_fit"].astype(bool).sum()),
                "pearson_y_prediction": float(x[["y", "prediction_eta"]].corr().iloc[0, 1]),
                "r_squared_predictive": float(1 - ((x.y-x.prediction_eta)**2).sum()/((x.y-x.y.mean())**2).sum()),
                "mean_y": float(x.y.mean()), "mean_prediction": float(x.prediction_eta.mean()),
                "sd_ratio": float(x.prediction_eta.std(ddof=1)/x.y.std(ddof=1)),
            })
    tab = pd.DataFrame(rows)
    text = ["# Figure 9 provenance", "",
            "The currently retained Figure 9 producer is the R04 formal pipeline output, not the user screenshot.",
            f"Producer: `{FIG9_SCRIPT}` (SHA256 `{sha256(FIG9_SCRIPT)}`).",
            f"Formal run: `{R04}`.", "",
            "The descriptive panels use full-sample fitted values: every plotted event has `was_in_this_fit=True`.",
            "The companion OOF panels use global date-group OOF predictions (`was_in_this_fit=False`), but are not leave-one-storm-process-out predictions.",
            "Thus neither panel is an external storm validation. X02 creates separate protected-process evaluation.", "",
            "The plotted outcome and prediction are both on the direct log target scale (`prediction_eta`); the earlier double-log transform is not used in R04.", "",
            "## Recalculated values", "", markdown_table(tab), "",
            "The original R04 descriptive fit has complete training/plot overlap. The date-OOF diagnostic has no row in its own fitted fold, but storm processes are dispersed across its date folds."]
    return tab, "\n".join(text) + "\n"


def main() -> None:
    for d in [RUN / "tables", RUN / "evidence", RUN / "src", RUN / "models", RUN / "predictions", RUN / "figures", RUN / "logs"]:
        d.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    manifest_source = json.loads(EVENT_MANIFEST.read_text(encoding="utf-8"))
    actual_hash = sha256(EVENTS)
    if actual_hash != manifest_source["event_table"]["sha256"]:
        raise RuntimeError("Event parquet hash does not match R02 EVENT_MANIFEST")

    cols = [
        "Incident Reference", "event_time_proxy_utc", "earliest_recorded_start_utc", "max_stage_end_utc",
        "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours", "duration_A_customer_weighted_hours",
        "gust_0h", "pressure_msl_0h", "temperature_0h", "precipitation_24h_sum", "licence_area",
        "LAD21CD", "LAD21NM", "rural_urban_classification", "urban_binary", "deprivation_gap_pct",
        "morans_i", "income_deprivation_rate", "population", "log_population", "cause_group_event",
        "cause_code_event", "cause_final_diagnosis_verified", "candidate_main_E0", "candidate_main_R0c",
        "weather_numeric_available", "weather_validation_tier", "weather_units_basis", "regional_proxy_flag",
        "event_identity_status", "event_identity_unresolved", "time_input_incomplete", "customer_input_incomplete",
        "recovery_crosses_study_end", "stages_cross_study_end", "n_stages", "stage_row_count",
        "business_calendar_timezone", "analysis_calendar_timezone", "event_time_basis", "input_version"
    ]
    df = pd.read_parquet(EVENTS, columns=cols)
    t = pd.to_datetime(df.event_time_proxy_utc, utc=True)
    end = pd.to_datetime(df.max_stage_end_utc, utc=True)
    wf = windows_frame()
    mem = assign_membership(df, wf)
    if df["Incident Reference"].duplicated().any():
        raise RuntimeError("Incident Reference is not unique in event master")
    if len(mem) != len(df) or mem["Incident Reference"].duplicated().any():
        raise RuntimeError("Membership table lost event uniqueness")
    mem.to_parquet(RUN / "EPISODE_MEMBERSHIP.parquet", index=False)

    storm_mask = mem.protected_group.ne("NONE")
    c = pd.to_numeric(df.customers_v2_event_excl_reinterruptions, errors="coerce")
    d = pd.to_numeric(df.duration_B_full_span_hours, errors="coerce")
    eligible = {
        "E_log": df.candidate_main_E0.astype(bool) & c.notna() & c.ge(0),
        "R_log": df.candidate_main_R0c.astype(bool) & d.notna() & d.gt(0),
        "R_C_log": df.candidate_main_R0c.astype(bool) & d.notna() & d.gt(0) & c.notna() & c.ge(0),
    }
    flow = []
    for task, ok in eligible.items():
        flow += [
            {"task": task, "step": "event_master", "n": int(len(df))},
            {"task": task, "step": "task_eligible_parent", "n": int(ok.sum())},
            {"task": task, "step": "inside_union_of_named_windows", "n": int((ok & storm_mask).sum())},
            {"task": task, "step": "development_P1_P3", "n": int((ok & mem.protected_group.isin(["P1","P2","P3"])).sum())},
            {"task": task, "step": "time_test_P4_P5", "n": int((ok & mem.protected_group.isin(["P4","P5"])).sum())},
        ]
    pd.DataFrame(flow).to_csv(RUN / "SAMPLE_FLOW.csv", index=False)

    catalog = wf.copy()
    for task, ok in eligible.items():
        counts = []
        for _, w in wf.iterrows():
            m = ok & mem[f"storm_{w.storm_name}"]
            counts.append(int(m.sum()))
        catalog[f"n_{task}"] = counts
    catalog.to_csv(RUN / "STORM_CATALOG.csv", index=False)

    proc_rows = []
    for p in ["P1", "P2", "P3", "P4", "P5"]:
        pm = mem.protected_group.eq(p)
        for task, ok in eligible.items():
            m = pm & ok
            gs = safe_stats(df.loc[m, "gust_0h"])
            row = {"protected_group": p, "task": task, "n": int(m.sum()),
                   "unique_LAD": int(df.loc[m, "LAD21CD"].nunique(dropna=True)),
                   "regional_proxy_n": int(df.loc[m, "regional_proxy_flag"].fillna(False).astype(bool).sum()),
                   "missing_gust_n": int(df.loc[m, "gust_0h"].isna().sum()),
                   "recovery_crosses_window_end_n": int(((end > wf.loc[wf.protected_group.eq(p), "end_exclusive_utc"].max()) & m).sum()),
                   **{f"gust_{k}": v for k, v in gs.items()}}
            # Preserve the time-test blind gate: detailed C/D summaries only for development groups.
            if p in {"P1", "P2", "P3"}:
                row.update({f"C_{k}": v for k, v in safe_stats(c[m]).items()})
                row.update({f"D_hours_{k}": v for k, v in safe_stats(d[m]).items()})
            proc_rows.append(row)
    pd.DataFrame(proc_rows).to_csv(RUN / "tables" / "process_support_audit.csv", index=False)

    cause_rows = []
    for p in ["P1", "P2", "P3", "P4", "P5"]:
        m = storm_mask & mem.protected_group.eq(p)
        for cause, n in df.loc[m, "cause_group_event"].fillna("<missing>").value_counts().items():
            cause_rows.append({"protected_group": p, "cause_group": cause, "n": int(n)})
    pd.DataFrame(cause_rows).to_csv(RUN / "tables" / "process_cause_composition.csv", index=False)

    feature_rows = [
        ("gust_0h", "historical hourly weather matched at floor(event proxy hour)", "event proxy hour", "retrospective archive; live product not evidenced", False, "F0"),
        ("pressure_msl_0h", "same historical weather cache", "event proxy hour", "retrospective archive; live product not evidenced", False, "F0"),
        ("temperature_0h", "same historical weather cache", "event proxy hour", "retrospective archive; live product not evidenced", False, "F0"),
        ("precipitation_24h_sum", "24 hourly values ending at event proxy hour", "proxy hours h-23..h", "historical reconstruction", False, "F0"),
        ("licence_area", "event record/static network area", "record metadata", "no event-time snapshot", False, "F0"),
        ("rural_urban_classification", "static 2011 classification proxy", "static", "retrospective join", False, "F0"),
        ("log_population", "annual ONS estimate joined by LAD and proxy year", "annual, published/revised later", "not exact onset-time information", False, "F0"),
        ("deprivation_gap_pct", "static regional proxy", "static", "retrospective join", False, "F0"),
        ("morans_i", "static regional proxy", "static", "retrospective join", False, "F0"),
        ("income_deprivation_rate", "static 2019 regional proxy", "static", "retrospective join", False, "F0"),
        ("season_sin/cos", "derived from event proxy UTC day of year", "event proxy", "deterministic", False, "F0"),
        ("time_trend", "derived from event proxy UTC date", "event proxy", "deterministic", False, "F0"),
        ("I_storm", "membership in frozen named-window union", "retrospective condition label", "known only under fixed historical window definition", False, "P00/P02 only"),
        ("cause_group_event", "full-stage retrospective consensus", "final diagnosis timing unknown", "not onset available", True, "excluded from F0"),
        ("n_stages", "full event aggregation", "after event completion", "not onset available", True, "excluded from F0"),
        ("max_stage_end_utc", "full event aggregation", "after event completion", "not onset available", True, "label maturity/exclusion only"),
        ("log1p_final_C", "full event customer aggregation", "after event completion", "not onset available", True, "R_C only"),
    ]
    fa = pd.DataFrame(feature_rows, columns=["variable", "source", "observation_window", "earliest_availability_evidence", "contains_final_information", "role"])
    fa["F1_status"] = "not available: no auditable timestamped operational/pre-forecast archive found in the verified event contract"
    fa.to_csv(RUN / "FEATURE_AVAILABILITY.csv", index=False)

    figtab, figmd = fig9_audit()
    figtab.to_csv(RUN / "tables" / "figure9_recalculation.csv", index=False)
    (RUN / "FIG9_PROVENANCE.md").write_text(figmd, encoding="utf-8")

    x01_text = X01_CODE.read_text(encoding="utf-8", errors="replace") if X01_CODE.exists() else ""
    bug_hits = [line.strip() for line in x01_text.splitlines() if "cause_asset" in line or "== \"asset\"" in line or "== 'asset'" in line]
    issues = ["# Upstream issues (read-only sources)", "",
              "## U-01 — X01 cause indicator mismatch", "",
              f"Status: confirmed in `{X01_CODE}`." if bug_hits else "Status: source not located.", "",
              "The event contract uses `technical_asset`, whereas X01 searched for `asset`; the resulting indicator was all zero. X02 excludes final cause from F0, so this issue is detected but not used to expand the information set.", "",
              "Evidence lines:", ""]
    issues += [f"- `{re.sub(r'`', '', x)}`" for x in bug_hits[:10]] or ["- none available"]
    issues += ["", "## U-02 — Business onset/time zone", "",
               "The verified contract supplies `event_time_proxy_utc=earliest_available_stage_start`; business onset and business calendar timezone remain unverified. X02 uses the frozen UTC proxy and reports a London-calendar sensitivity only.", "",
               "## U-03 — Weather availability", "",
               "Historical cached observations are auditable as retrospective covariates, but their real-time publication/forecast availability is not. F1 is therefore skipped rather than inferred.", ""]
    (RUN / "UPSTREAM_ISSUES.md").write_text("\n".join(issues), encoding="utf-8")

    summed = float(wf.window_days.sum())
    days = set()
    for _, w in wf.iterrows():
        days.update(pd.date_range(w.start_utc, w.end_exclusive_utc - pd.Timedelta(days=1), freq="D").date)
    group_leak = mem.loc[storm_mask].groupby("Incident Reference").protected_group.nunique().max()
    audit_checks = {
        "event_hash_matches_manifest": actual_hash == manifest_source["event_table"]["sha256"],
        "event_rows": int(len(df)), "unique_event_ids": int(df["Incident Reference"].nunique()),
        "duplicate_event_ids": int(df["Incident Reference"].duplicated().sum()),
        "unresolved_event_identity_n": int(df.event_identity_unresolved.fillna(False).astype(bool).sum()),
        "zero_C_in_E_parent_n": int((eligible["E_log"] & c.eq(0)).sum()),
        "negative_C_in_E_parent_n": int((eligible["E_log"] & c.lt(0)).sum()),
        "nonpositive_D_in_R_parent_n": int((df.candidate_main_R0c.astype(bool) & d.le(0)).sum()),
        "window_days_sum": summed, "window_union_days": len(days),
        "protected_groups": sorted(mem.loc[storm_mask, "protected_group"].unique().tolist()),
        "max_protected_groups_per_event": int(group_leak),
        "multi_named_membership_events": int(mem.window_count.gt(1).sum()),
        "utc_london_membership_difference_events": int(mem.utc_london_membership_diff.sum()),
        "storm_union_unique_events": int(storm_mask.sum()),
        "time_min": str(t.min()), "time_max": str(t.max()),
        "max_end": str(end.max()),
        "stage_a_pass": bool(actual_hash == manifest_source["event_table"]["sha256"] and df["Incident Reference"].is_unique and group_leak == 1 and summed == 27 and len(days) == 25),
    }
    write_json(RUN / "evidence" / "stage_a_checks.json", audit_checks)

    data_manifest = {
        "run_id": RUN.name, "created_utc": datetime.now(timezone.utc).isoformat(), "random_seed": 20260907,
        "source_event_table": str(EVENTS), "source_event_sha256": actual_hash,
        "source_event_manifest": str(EVENT_MANIFEST), "source_event_manifest_sha256": sha256(EVENT_MANIFEST),
        "source_windows": str(WINDOWS), "source_windows_sha256": sha256(WINDOWS),
        "event_rows": int(len(df)), "unique_events": int(df["Incident Reference"].nunique()),
        "input_version": str(df.input_version.dropna().iloc[0]) if df.input_version.notna().any() else None,
        "git_commit": None,
        "runtime": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__, "pyarrow": pyarrow.__version__},
        "source_policy": "read_only; no source file copied or modified",
        "analysis_calendar": "UTC proxy; Europe/London calendar membership sensitivity reported",
    }
    write_json(RUN / "DATA_MANIFEST.json", data_manifest)

    audit_md = ["# X02-A audit", "", f"Run: `{RUN.name}`", f"Started UTC: `{started}`", "",
                "## Input identity", "", f"The authoritative corrected event contract is `{EVENTS}` (SHA256 `{actual_hash}`), matched to its R02 manifest. It contains {len(df):,} unique event rows.", "",
                "The event identity is a record-level incident reference contract, not a certified physical-fault identity; two source cases remain explicitly unresolved and are excluded by the parent candidate flags.", "",
                "## Outcomes", "", "C is the sum of non-reinterruption stage customers. D is the full recorded event span in hours from the earliest stage start to latest stage end. E_log retains C=0; R_log/R_C_log require D>0. No test-outcome p99 truncation is used.", "",
                "## Windows and grouping", "", f"Named windows sum to {summed:g} days and their UTC union has {len(days)} days. They form P1–P5; Dudley/Eunice/Franklin are one protected group P2. The storm union contains {int(storm_mask.sum()):,} unique events; {int(mem.window_count.gt(1).sum()):,} events have multiple name labels but one protected group and are counted once in primary scoring.", "",
                f"UTC versus same-date Europe/London calendar membership differs for {int(mem.utc_london_membership_diff.sum()):,} events. This sensitivity was not used to select windows.", "",
                "## Feature-time boundary", "", "F0 uses audited historical weather and static regional covariates plus transferable calendar encodings. These support observed-weather conditional retrospective prediction only. Final cause, stage count, end time and final C are excluded from F0; final C enters only R_C. F1 is skipped because no auditable timestamped operational/pre-forecast archive is present.", "",
                "## Figure 9", "", "R04 Figure 9 descriptive predictions are full-sample fitted values. The companion date-group OOF panel is not process-held-out. See `FIG9_PROVENANCE.md`.", "",
                "## Gate", "", f"X02-A gate: **{'PASS' if audit_checks['stage_a_pass'] else 'FAIL'}**. Protocol freezing may proceed only if PASS.", ""]
    (RUN / "X02_AUDIT.md").write_text("\n".join(audit_md), encoding="utf-8")

    state = {"run_id": RUN.name, "stage": "X02-A", "status": "completed" if audit_checks["stage_a_pass"] else "blocked",
             "completed_utc": datetime.now(timezone.utc).isoformat(), "stage_a_pass": audit_checks["stage_a_pass"],
             "next_allowed_stage": "X02-B" if audit_checks["stage_a_pass"] else None}
    write_json(RUN / "RUN_STATE.json", state)
    print(json.dumps(audit_checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
