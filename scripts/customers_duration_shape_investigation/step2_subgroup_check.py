"""Command #17 Step 2: check whether the inverted-U shape holds independently
within weather_natural and within technical_asset, or is a composition artifact
of mixing the two subgroups.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\dev_sample_decontamination")))
from clean_sample_builder import build_clean_wt_samples  # noqa: E402

OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\customers_duration_shape_investigation")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[v17-step2] {msg}", flush=True)


def decile_bin_report(df: pd.DataFrame, x_col: str, y_col: str, label: str) -> pd.DataFrame:
    d = df[[x_col, y_col]].dropna().copy()
    d["decile"] = pd.qcut(d[x_col], q=10, duplicates="drop")
    rows = []
    for decile, g in d.groupby("decile", observed=True):
        rows.append({
            "label": label, "decile": str(decile), "n": len(g),
            "x_min": float(g[x_col].min()), "x_max": float(g[x_col].max()), "x_median": float(g[x_col].median()),
            "y_mean": float(g[y_col].mean()), "y_median": float(g[y_col].median()),
        })
    return pd.DataFrame(rows)


def main():
    _, _, r0cb_sample, _ = build_clean_wt_samples()
    r0cb_sample = r0cb_sample.copy()

    dist_rows = []
    for grp in ["weather_natural", "technical_asset"]:
        sub = r0cb_sample[r0cb_sample["cause_group_official"] == grp].copy()
        log_step(f"{grp}: n={len(sub)}")
        c = sub["customers_v2_event_excl_reinterruptions"]
        dist_rows.append({
            "group": grp, "n": len(sub), "customers_v2_mean": float(c.mean()), "customers_v2_median": float(c.median()),
            "customers_v2_p25": float(c.quantile(0.25)), "customers_v2_p75": float(c.quantile(0.75)),
            "customers_v2_p99": float(c.quantile(0.99)), "customers_v2_max": float(c.max()),
        })

        bins = decile_bin_report(sub, "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
                                  f"{grp}_raw_scale")
        bins.to_csv(RAW_DIR / f"02_{grp}_raw_scale_bins.csv", index=False)
        print(f"=== {grp}, raw scale ===")
        print(bins.to_string(index=False))

        sub["log1p_customers_v2"] = np.log1p(c.astype(float))
        sub["log_duration_B"] = np.log(sub["duration_B_full_span_hours"].astype(float))
        bins_log = decile_bin_report(sub, "log1p_customers_v2", "log_duration_B", f"{grp}_log_scale")
        bins_log.to_csv(RAW_DIR / f"02_{grp}_log_scale_bins.csv", index=False)
        print(f"=== {grp}, log scale ===")
        print(bins_log.to_string(index=False))

    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(RAW_DIR / "02_subgroup_customers_v2_distribution.csv", index=False)
    print("=== customers_v2 distribution by subgroup ===")
    print(dist_df.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
