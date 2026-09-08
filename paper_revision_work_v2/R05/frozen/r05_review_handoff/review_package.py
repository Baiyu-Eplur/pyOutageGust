"""Read-only arithmetic/provenance review of the supplied R04 return package.

No model code is imported; raw data and model archives are not re-estimated.
Run: python review_package.py RECEIVED_DIRECTORY OUTPUT_JSON
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()


def read(rel):
    return json.loads((root / rel).read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def portable(path):
    bits = re.split(r"[\\/]+", path)
    if "paper_revision_work_v2" in bits:
        bits = bits[bits.index("paper_revision_work_v2") + 1:]
    return root.joinpath(*bits)


def verify(rows, source_relative=False):
    present, absent, bad = [], [], []
    for row in rows:
        p = root / "manuscript_record" / row["path"] if source_relative else portable(row["path"])
        if not p.is_file():
            absent.append(row["path"])
            continue
        present.append(row["path"])
        size = row.get("bytes", row.get("size_bytes"))
        if sha(p) != row["sha256"] or (size is not None and p.stat().st_size != size):
            bad.append(row["path"])
    return {"listed": len(rows), "verified_present": len(present), "not_supplied": len(absent),
            "mismatches": bad, "not_supplied_paths": absent}


result = {"review_checkpoint": "MR-v1.4-R04-review", "review_type": "supplied-package arithmetic and provenance review",
          "raw_data_rerun": False, "local_full_model_archives_read": False,
          "R05_completed": False, "Word_modified": False, "checks": {}}
checks = result["checks"]
checks["return_manifest"] = verify(read("R04/RETURN_PACKAGE_MANIFEST.json")["files"])
checks["source_manifest"] = verify(read("manuscript_record/SOURCE_MANIFEST.json")["sources"], True)
bundle = read("manuscript_record/BUNDLE_MANIFEST.json")
checks["ledger_bundle_manifest"] = verify(bundle["files"])
b1 = read("baseline/B1_MANIFEST.json")
checks["B1_supplied_subset"] = verify(b1["outputs"])
result["B1_manifest_sha256"] = sha(root / "baseline/B1_MANIFEST.json")
result["B1_input_identity"] = b1["input_identity"]

metrics = pd.read_csv(root / "R04/tables/H0_R1_B1_metrics.csv")
recomputed = metrics[metrics["SSE"].notna() & metrics["SST"].notna()].copy()
errors = (1 - recomputed.SSE / recomputed.SST - recomputed.pooled_R2).abs()
checks["pooled_R2_from_reported_SSE_SST"] = {"rows": len(recomputed), "max_abs_error": errors.max(), "passed": bool((errors < 1e-12).all())}
increments = pd.read_csv(root / "R04/tables/H0_R1_B1_increments.csv")
inc_errors = []
for row in increments.to_dict("records"):
    m = metrics[(metrics.version == row["version"]) & (metrics.group == row["group"]) & (metrics.target == row["target"])]
    d = dict(zip(m.block, m.pooled_R2))
    diffs = {"gust_from_control": d["G"] - d["control"]}
    if row["target"] == "R0c":
        diffs.update(customers_from_control=d["K"] - d["control"], gust_given_customers=d["GK"] - d["K"], customers_given_gust=d["GK"] - d["G"])
    inc_errors.extend(abs(value - row[key]) for key, value in diffs.items())
checks["increments_from_reported_nested_scores"] = {"contrasts": len(inc_errors), "max_abs_error": max(inc_errors), "passed": max(inc_errors) < 1e-12}
shape = pd.read_csv(root / "R04/tables/H0_R1_B1_shape.csv")
shape = shape[shape.version.isin(["R1", "B1"])].copy()
q_error = (shape.beta_gust2 / shape.gust_sd ** 2 - shape.physical_quadratic).abs()
min_error = (shape.gust_mean - shape.gust_sd * shape.beta_gust / (2 * shape.beta_gust2) - shape.conditional_minimum_ms).abs()
checks["mean_pressure_minimum_and_physical_quadratic"] = {"rows": len(shape), "max_q_error": q_error.max(), "max_minimum_error_ms": min_error.max(), "passed": bool((q_error < 1e-12).all() and (min_error < 1e-10).all()), "interpretation": "algebraic identity only; no uncertainty or physical threshold certification"}
sup = pd.read_csv(root / "R04/tables/supplement_summary.csv")
cubic = sup[sup.analysis == "cubic"].copy()
checks["cubic_delta"] = {"rows": len(cubic), "max_abs_error": (cubic.pooled_R2 - cubic.quadratic_R2 - cubic.delta_R2).abs().max(), "records": cubic[["target", "pooled_R2", "quadratic_R2", "delta_R2"]].to_dict("records")}
storms = pd.read_csv(root / "R04/tables/storm_statistics.csv")
checks["storm_percentages"] = {"rows": len(storms), "max_events_pct_error": (100 * storms.events / storms.denominator_events - storms.events_pct).abs().max(), "max_customers_pct_error": (100 * storms.customers_sum / storms.denominator_customers_sum - storms.customers_pct).abs().max(), "unique_union_rows": storms[storms.window == "UNIQUE_ANY"].to_dict("records"), "limitation": "arithmetic checks of supplied aggregates, not independent raw membership reconstruction"}
customer = read("R04/tables/customer_aggregation_comparison.json")
checks["customer_mean_ratios"] = {"lowest_stage_abs_error": abs(customer["aggregated_customer_mean"] / customer["lowest_stage_number_mean"] - customer["ratio_aggregate_to_lowest_stage"]), "earliest_time_abs_error": abs(customer["aggregated_customer_mean"] / customer["earliest_record_time_customer_mean"] - customer["ratio_aggregate_to_earliest_time"]), "comparison_record_selection_verified": False, "earliest_time_nonmissing_n_supplied": "earliest_record_time_nonmissing_n" in customer}
cov = read("R04/checks/period_covariance_acceptance.json")
twoway = [x for x in cov if x["covariance"] == "two_way"]
negative = [x for x in twoway if x["minimum_eigenvalue"] < -1e-10]
checks["period_covariance_condition"] = {"two_way_matrices": len(twoway), "negative_eigenvalue_beyond_1e_10_screen": len(negative), "negative_diagonal_count": sum(x["negative_diagonal"] for x in twoway), "affected": negative, "interpretation": "reported eigenvalues read from supplied JSON; re-eigendecomposition and actual contrast-consumer audit belong to R05; screening threshold is not a universal statistical acceptance rule"}
slots = pd.read_csv(root / "R04/tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv")
bindings = pd.read_csv(root / "R04/tables/CURRENT_NUMERIC_BINDINGS.csv")
paragraphs = pd.read_csv(root / "R04/tables/CURRENT_PARAGRAPH_NUMERIC_BINDINGS.csv")
checks["numeric_mapping_coverage"] = {"numeric_slots": len(slots), "cell_bindings": len(bindings), "paragraph_bindings": len(paragraphs), "slot_status_counts": slots.status.value_counts().to_dict(), "sentence_rewrite_unique_locations": sorted(slots.loc[slots.status.str.startswith("old_combined_sentence_requires_rewrite"), "old_location"].unique()), "not_a_whole_manuscript_semantic_acceptance": True}
figs = read("R04/figures/FIGURE_MANIFEST.json")
checks["current_figure_files"] = {"groups": len(figs), "all_png_pdf_exist": all((root / "R04/figures" / (x["figure"] + "." + ext)).is_file() for x in figs for ext in ["png", "pdf"]), "manifest_review_status": {x["figure"]: x["visual_review"] for x in figs}}
main = metrics[(metrics.version == "B1") & (((metrics.target == "E0") & (metrics.block == "G")) | ((metrics.target == "R0c") & (metrics.block == "GK")))].copy()
main["pooled_minus_meanfold_R2"] = main.pooled_R2 - main.mean_fold_R2
result["current_headline_metrics"] = main.to_dict("records")
result["production_accounting_as_reported"] = {key: b1[key] for key in ["active_production_fits", "superseded_partial_producer_fits", "ancillary_covariance_verification_fits", "total_producer_parameter_solves", "unarchived_aborted_period_solves", "retained_producer_archives_including_superseded"]}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
print(json.dumps({"output": str(out), "manifest_counts": {k: {a: checks[k][a] for a in ["listed", "verified_present", "not_supplied", "mismatches"]} for k in ["return_manifest", "source_manifest", "ledger_bundle_manifest", "B1_supplied_subset"]}, "negative_period_two_way_matrices": len(negative), "numeric_slots": len(slots), "sentence_rewrite_unique_locations": checks["numeric_mapping_coverage"]["sentence_rewrite_unique_locations"]}, ensure_ascii=False, indent=2))
