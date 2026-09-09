"""Command #21 Step 4: "baseline regional difference" map data (weather AND
customers_v2 held fixed at the sample mean; only the 5 LAD-level socioeconomic
covariates vary), reusing command #20's reverse-engineered 0519_4.3.py
prediction-frame logic but with corrected variables and this command's explicit
requirement that customers_v2 also be fixed (not left free) for the R0c map.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402

sys.path.insert(0, str(project_path('scripts/dev_sample_decontamination')))
from clean_sample_builder import v9  # noqa: E402

V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
BOUNDARY_FILE = external_path('data/Local_Authority_Districts_December_2021_UK_BGC_2022/LAD_DEC_2021_UK_BGC.shp')
OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)

LAD_COVARIATE_COLS = ["log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i", "urban_binary"]


def log_step(msg):
    print(f"[v21-step4] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def fit_and_predict_by_lad(sample: pd.DataFrame, target_col: str, use_customers: bool, label: str):
    res, cov, gust_mean, gust_sd, d = v11.fit_full_sample(sample, target_col, use_customers_covariate=use_customers)
    exog_names = list(res.model.exog_names)

    # sample-wide means for everything EXCEPT the 5 LAD covariates (which vary per LAD)
    if use_customers:
        s = sample.copy()
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        Xtr_full, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    else:
        Xtr_full, _ = v9.design_train_valid(sample, sample, extra_scale_cols=None)
    global_means = Xtr_full.mean(axis=0)

    lad_means = d.groupby("LAD21CD")[LAD_COVARIATE_COLS].mean().reset_index()
    log_step(f"{label}: {len(lad_means)} LADs with at least one observation in the estimation sample.")

    X = pd.DataFrame(0.0, index=lad_means.index, columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0
    for c in exog_names:
        if c in LAD_COVARIATE_COLS or c in ("z_gust_0h", "z_gust_0h_sq", "z_gust_pressure"):
            continue
        if c in global_means.index:
            X[c] = global_means[c]
    # weather variables (and, for R0c, customers_v2) fixed at the estimation
    # sample's mean = z-score 0 by construction (z-scoring centres the mean at 0)
    X["z_gust_0h"] = 0.0
    X["z_gust_0h_sq"] = 0.0
    if "z_gust_pressure" in X.columns:
        X["z_gust_pressure"] = 0.0
    if use_customers:
        X["z_log1p_customers_v2"] = 0.0
        X["z_log1p_customers_v2_sq"] = 0.0

    for c in LAD_COVARIATE_COLS:
        X[c] = lad_means[c].values

    beta = res.params.loc[exog_names]
    eta = X[exog_names].astype(float) @ beta
    pred = np.exp(eta)

    out = lad_means[["LAD21CD"]].copy()
    out[f"pred_{label}"] = pred.values
    return out


def main():
    _, combined_e0, combined_r0cb, _ = build_combined_samples()

    log_step("Predicting baseline regional customers_v2 (E0), weather fixed at sample mean...")
    pred_customers = fit_and_predict_by_lad(combined_e0, "log1p_customers_v2", False, "customers_v2")

    log_step("Predicting baseline regional duration_B (R0c), weather AND customers_v2 fixed at sample mean...")
    pred_duration = fit_and_predict_by_lad(combined_r0cb, "log_duration_B_full_span_hours", True, "duration_B")

    pred_lad = pred_customers.merge(pred_duration, on="LAD21CD", how="outer")
    pred_lad.to_csv(OUT_DIR / "04_基线区域差异地图数据.csv", index=False, encoding="utf-8-sig")

    ratio_customers = float(pred_lad["pred_customers_v2"].max() / pred_lad["pred_customers_v2"].min())
    ratio_duration = float(pred_lad["pred_duration_B"].max() / pred_lad["pred_duration_B"].min())
    log_step(f"Regional max/min ratio -- customers_v2: {ratio_customers:.3f}, duration_B: {ratio_duration:.3f}")

    # ---------------- maps ----------------
    log_step("Loading LAD boundary file and plotting maps...")
    gdf = gpd.read_file(read_input(BOUNDARY_FILE))
    code_col = "LAD21CD" if "LAD21CD" in gdf.columns else [c for c in gdf.columns if "LAD" in c.upper() and "CD" in c.upper()][0]
    gdf = gdf.rename(columns={code_col: "LAD21CD"}) if code_col != "LAD21CD" else gdf
    gdf = gdf.to_crs(epsg=27700)
    gdf_gb = gdf[gdf["LAD21CD"].astype(str).str.startswith(("E", "W", "S"))].copy()

    map_gdf = gdf_gb.merge(pred_lad, on="LAD21CD", how="left")

    def quantile_limits(values, lower_q=0.0, upper_q=0.98):
        v = pd.Series(values).replace([np.inf, -np.inf], np.nan).dropna()
        if v.empty:
            return None, None
        vmin, vmax = float(v.quantile(lower_q)), float(v.quantile(upper_q))
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
            return float(v.min()), float(v.max())
        return vmin, vmax

    def plot_map(value_col, out_stub, legend_label):
        vmin, vmax = quantile_limits(map_gdf[value_col], 0.00, 0.98)
        fig, ax = plt.subplots(figsize=(15 / 2.54, 18 / 2.54))
        map_gdf.plot(
            column=value_col, cmap="Oranges", linewidth=0.18, edgecolor="white",
            legend=True, ax=ax, vmin=vmin, vmax=vmax,
            missing_kwds={"color": "#f0f0f0", "edgecolor": "white"},
        )
        data_gdf = map_gdf[map_gdf[value_col].notna()]
        if not data_gdf.empty:
            minx, miny, maxx, maxy = data_gdf.total_bounds
            dx, dy = maxx - minx, maxy - miny
            ax.set_xlim(minx - 0.03 * dx, maxx + 0.03 * dx)
            ax.set_ylim(miny - 0.03 * dy, maxy + 0.03 * dy)
        ax.set_axis_off()
        ax.set_title(legend_label, fontsize=10)
        plt.tight_layout()
        fig.savefig(OUT_DIR / f"{out_stub}.png", dpi=600, bbox_inches="tight")
        fig.savefig(OUT_DIR / f"{out_stub}.pdf", bbox_inches="tight")
        plt.close(fig)

    plot_map("pred_customers_v2", "04a_基线区域差异_预测customers_v2",
              "Baseline regional difference in predicted customers_v2\n(fixed reference weather; region covariates vary)")
    plot_map("pred_duration_B", "04b_基线区域差异_预测duration_B",
              "Baseline regional difference in predicted duration_B\n(fixed reference weather and customers_v2; region covariates vary)")

    summary = {
        "n_lads_customers": int(pred_lad["pred_customers_v2"].notna().sum()),
        "n_lads_duration": int(pred_lad["pred_duration_B"].notna().sum()),
        "customers_max_min_ratio": ratio_customers,
        "duration_max_min_ratio": ratio_duration,
        "customers_min": float(pred_lad["pred_customers_v2"].min()),
        "customers_max": float(pred_lad["pred_customers_v2"].max()),
        "duration_min": float(pred_lad["pred_duration_B"].min()),
        "duration_max": float(pred_lad["pred_duration_B"].max()),
    }
    (RAW_DIR / "step4_regional_map_summary.json").write_text(js(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    log_step("Done.")


if __name__ == "__main__":
    main()
