"""Final regeneration of Figure 6 (regional baseline maps) on C01-corrected
data. C07: customers reference scenario confirmed as z_log1p_customers_v2=0
and its square=0 (unchanged from command #21/#34's original design -- this
script already used this convention; Figure 4 was the one fixed to match it,
not this one). Reuses figure_style.py map furniture (scale bar/north arrow/
locator inset) unchanged."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, add_north_arrow, add_scale_bar, add_locator_inset  # noqa: E402

BOUNDARY_FILE = Path(r"D:\Pyprogramme\STST2603\data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp")
RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig6-final] {msg}", flush=True)


def quantile_limits(values, lower_q=0.0, upper_q=0.98):
    v = pd.Series(values).replace([np.inf, -np.inf], np.nan).dropna()
    if v.empty:
        return None, None
    vmin, vmax = float(v.quantile(lower_q)), float(v.quantile(upper_q))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        return float(v.min()), float(v.max())
    return vmin, vmax


def fit_and_predict_by_lad(v9, sample, target_col, use_customers, label):
    s = sample.copy()
    extra = None
    if use_customers:
        s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
        extra = ["customers_v2_log1p"]
    Xtr, _ = v9.design_train_valid(s, s, extra_scale_cols=extra)
    y = s[target_col].astype(float)
    res = sm.OLS(y, Xtr.astype(float)).fit()

    means = Xtr.mean(axis=0)
    lads = sorted(s["LAD21CD"].dropna().unique().tolist())
    exog_names = list(res.model.exog_names)
    X = pd.DataFrame(0.0, index=range(len(lads)), columns=exog_names)
    if "Intercept" in X.columns:
        X["Intercept"] = 1.0
    lad_cov_cols = ["log_population", "income_deprivation_rate", "deprivation_gap_pct", "morans_i", "urban_binary"]
    for c in exog_names:
        if c in lad_cov_cols or c in ("z_gust_0h", "z_gust_0h_sq", "z_gust_pressure"):
            continue
        if c in means.index:
            X[c] = means[c]
    # weather fixed at sample mean = z-score 0 by construction; customers likewise (C07)
    X["z_gust_0h"] = 0.0
    X["z_gust_0h_sq"] = 0.0
    if "z_gust_pressure" in X.columns:
        X["z_gust_pressure"] = 0.0
    if use_customers:
        X["z_log1p_customers_v2"] = 0.0
        X["z_log1p_customers_v2_sq"] = 0.0

    lad_means = s.groupby("LAD21CD")[lad_cov_cols].mean().reindex(lads)
    for c in lad_cov_cols:
        X[c] = lad_means[c].to_numpy()

    beta = res.params.loc[exog_names]
    eta = X[exog_names].astype(float) @ beta
    pred = np.exp(eta)
    return pd.DataFrame({"LAD21CD": lads, f"pred_{label}": pred.values})


def main():
    apply_style()
    v9, _, _ = _patch_v9()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    log_step("Predicting baseline regional customers_v2 (E0, corrected)...")
    pred_customers = fit_and_predict_by_lad(v9, combined_e0, "log1p_customers_v2", False, "customers_v2")
    log_step("Predicting baseline regional duration_B (R0c, corrected, customers fixed at z=0)...")
    pred_duration = fit_and_predict_by_lad(v9, combined_r0cb, "log_duration_B_full_span_hours", True, "duration_B")
    pred_lad = pred_customers.merge(pred_duration, on="LAD21CD", how="outer")
    pred_lad.to_csv(RAW_DIR / "figure6_regional_predictions_corrected.csv", index=False)

    corr_pearson = pred_lad[["pred_customers_v2", "pred_duration_B"]].corr().iloc[0, 1]
    corr_spearman = pred_lad[["pred_customers_v2", "pred_duration_B"]].corr(method="spearman").iloc[0, 1]
    log_step(f"Predicted-surface correlation (corrected): Pearson={corr_pearson:.3f}, Spearman={corr_spearman:.3f}")

    gdf = gpd.read_file(BOUNDARY_FILE)
    gdf = gdf.to_crs(epsg=27700)
    gdf_gb = gdf[gdf["LAD21CD"].astype(str).str.startswith(("E", "W", "S"))].copy()
    gb_outline = gdf_gb.dissolve()
    map_gdf = gdf_gb.merge(pred_lad, on="LAD21CD", how="left")

    def plot_map(value_col, out_stub, title_note):
        vmin, vmax = quantile_limits(map_gdf[value_col], 0.00, 0.98)
        fig, ax = plt.subplots(figsize=(15 / 2.54, 18 / 2.54))
        map_gdf.plot(column=value_col, cmap="Oranges", linewidth=0.18, edgecolor="white",
                      legend=True, ax=ax, vmin=vmin, vmax=vmax,
                      missing_kwds={"color": "#f0f0f0", "edgecolor": "white"}, legend_kwds={"shrink": 0.6})
        data_gdf = map_gdf[map_gdf[value_col].notna()]
        if not data_gdf.empty:
            minx, miny, maxx, maxy = data_gdf.total_bounds
            dx, dy = maxx - minx, maxy - miny
            ax.set_xlim(minx - 0.03 * dx, maxx + 0.03 * dx)
            ax.set_ylim(miny - 0.03 * dy, maxy + 0.03 * dy)
        ax.set_axis_off()
        add_north_arrow(ax)
        add_scale_bar(ax)
        add_locator_inset(fig, ax, gb_outline, data_gdf)
        plt.tight_layout()
        fig.savefig(OUT_DIR / f"{out_stub}.png", dpi=600, bbox_inches="tight")
        fig.savefig(OUT_DIR / f"{out_stub}.pdf", bbox_inches="tight")
        plt.close(fig)
        log_step(f"Saved {out_stub} (vmin={vmin:.3f}, vmax={vmax:.3f}) [{title_note}]")

    plot_map("pred_customers_v2", "Figure_6a_regional_customers", "predicted affected customers")
    plot_map("pred_duration_B", "Figure_6b_regional_duration", "predicted restoration duration")
    log_step("Done.")


if __name__ == "__main__":
    main()
