"""Command #33/#34 Figure 6: regenerate command #21's baseline regional difference
maps from the EXISTING data CSV (no recomputation). Command #34 revision: removed
the in-figure title entirely (filename now carries the figure's identity), added
scale bar + north arrow + GB locator inset, and raised in-figure text to the
9-10pt band. Colormap/projection/legend/quantile colour limits are unchanged
from command #21's original script."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, add_north_arrow, add_scale_bar, add_locator_inset  # noqa: E402

BOUNDARY_FILE = Path(r"D:\Pyprogramme\STST2603\data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp")
DATA_CSV = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\04_基线区域差异地图数据.csv")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[fig6] {msg}", flush=True)


def quantile_limits(values, lower_q=0.0, upper_q=0.98):
    v = pd.Series(values).replace([np.inf, -np.inf], np.nan).dropna()
    if v.empty:
        return None, None
    vmin, vmax = float(v.quantile(lower_q)), float(v.quantile(upper_q))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        return float(v.min()), float(v.max())
    return vmin, vmax


def plot_map(map_gdf, gb_outline, value_col, out_stub):
    vmin, vmax = quantile_limits(map_gdf[value_col], 0.00, 0.98)
    fig, ax = plt.subplots(figsize=(15 / 2.54, 18 / 2.54))
    map_gdf.plot(
        column=value_col, cmap="Oranges", linewidth=0.18, edgecolor="white",
        legend=True, ax=ax, vmin=vmin, vmax=vmax,
        missing_kwds={"color": "#f0f0f0", "edgecolor": "white"},
        legend_kwds={"shrink": 0.6},
    )
    data_gdf = map_gdf[map_gdf[value_col].notna()]
    if not data_gdf.empty:
        minx, miny, maxx, maxy = data_gdf.total_bounds
        dx, dy = maxx - minx, maxy - miny
        ax.set_xlim(minx - 0.03 * dx, maxx + 0.03 * dx)
        ax.set_ylim(miny - 0.03 * dy, maxy + 0.03 * dy)
    ax.set_axis_off()
    # No in-figure title (command #34): the figure's identity lives in the filename only.

    add_north_arrow(ax)
    add_scale_bar(ax)
    add_locator_inset(fig, ax, gb_outline, data_gdf)

    plt.tight_layout()
    fig.savefig(OUT_DIR / f"{out_stub}.png", dpi=600, bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{out_stub}.pdf", bbox_inches="tight")
    plt.close(fig)
    log_step(f"Saved {out_stub} (vmin={vmin:.3f}, vmax={vmax:.3f})")


def main():
    apply_style()

    log_step(f"Loading existing prediction data from {DATA_CSV} (no recomputation)...")
    pred_lad = pd.read_csv(DATA_CSV)
    log_step(f"n_lads with data: customers={pred_lad['pred_customers_v2'].notna().sum()}, "
              f"duration={pred_lad['pred_duration_B'].notna().sum()}")

    gdf = gpd.read_file(BOUNDARY_FILE)
    code_col = "LAD21CD" if "LAD21CD" in gdf.columns else [c for c in gdf.columns if "LAD" in c.upper() and "CD" in c.upper()][0]
    gdf = gdf.rename(columns={code_col: "LAD21CD"}) if code_col != "LAD21CD" else gdf
    gdf = gdf.to_crs(epsg=27700)
    gdf_gb = gdf[gdf["LAD21CD"].astype(str).str.startswith(("E", "W", "S"))].copy()
    gb_outline = gdf_gb.dissolve()

    map_gdf = gdf_gb.merge(pred_lad, on="LAD21CD", how="left")

    # Colormap/projection/legend/quantile limits are unchanged from command #21's
    # original script; command #34 removes the in-figure title and adds map furniture.
    plot_map(map_gdf, gb_outline, "pred_customers_v2", "Figure_6a_regional_customers")
    plot_map(map_gdf, gb_outline, "pred_duration_B", "Figure_6b_regional_duration")

    log_step("Done.")


if __name__ == "__main__":
    main()
