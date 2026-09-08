"""Command #42: n_stages x affected-customers cross-tabulation on the final
combined R0c sample (command #21, n=59,834), to directly support Appendix
Figure D1 (the composition-effect / Simpson's-paradox-style figure).

Pure descriptive statistics (group means) -- no new regression modelling.
n_stages is merged from the v3 stage-level dataset's `stage_row_count`
column by Incident Reference, exactly as command #18 did.

Binning choice (documented, not silently substituted): Appendix D.1/D.3's
existing binned tables (customers_duration_shape_investigation/05_...md,
final_combined_analysis/27_...md) used PER-SUBGROUP quantile bin edges
(different edges for the single-stage subset, the n_stages>=2 subset, and
the weather_natural subset) -- these cannot be reused as-is for this figure,
because a shared x-axis across all n_stages strata plus the pooled line
requires ONE common set of bin edges. We therefore compute quartile bins
(4 bins) of customers_v2 on the full n=59,834 sample and apply the SAME
edges to every stratum and to the pooled view, which is the natural
generalisation of the "quartile binning" convention the command anticipated.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[step42] {msg}", flush=True)


def main():
    _, _, combined_r0cb, _ = build_combined_samples()
    n = len(combined_r0cb)
    log_step(f"Final R0c sample n={n} (should match command #21's 59,834)")

    log_step("Merging stage_row_count (n_stages) from v3 stage-level dataset by Incident Reference...")
    ids = combined_r0cb["Incident Reference"].astype(str).unique().tolist()
    id_set = set(ids)
    usecols = ["Incident Reference", "stage_row_count"]
    chunks = []
    for chunk in pd.read_csv(SRC, usecols=usecols, low_memory=False, chunksize=500_000):
        chunk = chunk[chunk["Incident Reference"].astype(str).isin(id_set)]
        if len(chunk):
            chunks.append(chunk.drop_duplicates("Incident Reference"))
    stage_lookup = pd.concat(chunks, ignore_index=True).drop_duplicates("Incident Reference")
    stage_lookup["Incident Reference"] = stage_lookup["Incident Reference"].astype(str)

    df = combined_r0cb.copy()
    df["Incident Reference"] = df["Incident Reference"].astype(str)
    df = df.merge(stage_lookup, on="Incident Reference", how="left")
    n_missing = df["stage_row_count"].isna().sum()
    log_step(f"n_stages missing after merge: {n_missing} / {len(df)}")

    def stage_group(x):
        if x == 1:
            return "n_stages=1"
        if x == 2:
            return "n_stages=2"
        if 3 <= x <= 4:
            return "n_stages=3-4"
        return "n_stages>=5"

    df["n_stages_group"] = df["stage_row_count"].apply(stage_group)
    group_order = ["n_stages=1", "n_stages=2", "n_stages=3-4", "n_stages>=5"]
    log_step("n_stages group sizes:\n" + df["n_stages_group"].value_counts().reindex(group_order).to_string())

    customers = df["customers_v2_event_excl_reinterruptions"].astype(float)
    quartile_edges = customers.quantile([0, 0.25, 0.5, 0.75, 1.0]).to_numpy().copy()
    quartile_edges[0] -= 1e-9  # ensure the minimum value falls inside the first bin
    log_step(f"Quartile edges (customers_v2, full n=59,834 sample): {quartile_edges}")

    bin_labels = [
        f"Q1 [{quartile_edges[0]+1e-9:.0f}-{quartile_edges[1]:.0f}]",
        f"Q2 ({quartile_edges[1]:.0f}-{quartile_edges[2]:.0f}]",
        f"Q3 ({quartile_edges[2]:.0f}-{quartile_edges[3]:.0f}]",
        f"Q4 ({quartile_edges[3]:.0f}-{quartile_edges[4]:.0f}]",
    ]
    df["customers_bin"] = pd.cut(customers, bins=quartile_edges, labels=bin_labels, include_lowest=True)

    # ---- cross-tab: mean duration_B by (n_stages_group, customers_bin) ----
    cross = df.groupby(["n_stages_group", "customers_bin"], observed=True)["duration_B_full_span_hours"].agg(
        ["mean", "median", "count"])
    cross_mean = cross["mean"].unstack("customers_bin").reindex(group_order)[bin_labels]
    cross_n = cross["count"].unstack("customers_bin").reindex(group_order)[bin_labels]
    log_step("Cross-tab mean duration_B (rows=n_stages group, cols=customers quartile):\n" +
              cross_mean.round(2).to_string())
    log_step("Cross-tab n:\n" + cross_n.to_string())

    empty_cells = cross_mean.isna().sum().sum()
    if empty_cells:
        log_step(f"WARNING: {empty_cells} empty cells in the cross-tab!")
    else:
        log_step("Confirmed: all 4x4=16 cells populated, no empty cells.")

    # ---- pooled view: mean duration_B by customers_bin only (no stratification) ----
    pooled = df.groupby("customers_bin", observed=True)["duration_B_full_span_hours"].agg(["mean", "median", "count"])
    pooled = pooled.reindex(bin_labels)
    log_step("Pooled (unstratified) mean duration_B by customers quartile:\n" + pooled.round(2).to_string())

    # ---- save ----
    cross_mean.to_csv(RAW_DIR / "step42_crosstab_mean_duration.csv")
    cross_n.to_csv(RAW_DIR / "step42_crosstab_n.csv")
    pooled.to_csv(RAW_DIR / "step42_pooled_mean_duration.csv")
    df[["Incident Reference", "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
        "stage_row_count", "n_stages_group", "customers_bin"]].to_csv(
        RAW_DIR / "step42_event_level_with_groups.csv", index=False)
    log_step("Saved raw/step42_crosstab_mean_duration.csv, step42_crosstab_n.csv, "
              "step42_pooled_mean_duration.csv, step42_event_level_with_groups.csv")


if __name__ == "__main__":
    main()
