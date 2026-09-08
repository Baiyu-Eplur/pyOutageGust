"""Command #33 Figure 1: UKPN licence area boundaries + event density hexbin,
using the exact final combined sample (n=60,453)."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from combined_sample_builder import build_combined_samples  # noqa: E402
from figure_style import (  # noqa: E402
    apply_style, mm_to_in, save_fig, add_north_arrow, add_scale_bar,
    add_locator_inset, DOUBLE_COL_MM,
)

DNO_SHP = Path(r"D:\Pyprogramme\STST2603\data\dno_license_areas_20200506\DNO_License_Areas_20200506.shp")
GB_BOUNDARY_SHP = Path(r"D:\Pyprogramme\STST2603\data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

UKPN_AREAS = {"UKPN (East)": "EPN", "UKPN (London)": "LPN", "UKPN (South)": "SPN"}


def log_step(msg):
    print(f"[fig1] {msg}", flush=True)


def main():
    apply_style()

    log_step("Building combined final sample...")
    combined_wt, _, _, _ = build_combined_samples()
    log_step(f"n={len(combined_wt)}")

    # need lat/lon: not carried in v9's USECOLS-derived combined_wt frame necessarily -- check
    if "lat" not in combined_wt.columns or "lon" not in combined_wt.columns:
        log_step("lat/lon not in combined sample columns; joining from v3 dataset by Incident Reference...")
        SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
        coords = pd.read_csv(SRC, usecols=["Incident Reference", "lat", "lon", "licence_area"], low_memory=False)
        coords = coords.drop_duplicates("Incident Reference")
        combined_wt = combined_wt.merge(coords, on="Incident Reference", how="left")

    n_missing_coords = combined_wt["lat"].isna().sum()
    log_step(f"Missing coordinates: {n_missing_coords} / {len(combined_wt)}")
    pts = combined_wt.dropna(subset=["lat", "lon"]).copy()

    gdf_pts = gpd.GeoDataFrame(
        pts, geometry=[Point(xy) for xy in zip(pts["lon"], pts["lat"])], crs="EPSG:4326"
    ).to_crs(epsg=27700)

    log_step("Loading DNO licence area boundaries...")
    dno = gpd.read_file(DNO_SHP)
    ukpn = dno[dno["LongName"].isin(UKPN_AREAS.keys())].copy()
    ukpn["short"] = ukpn["LongName"].map(UKPN_AREAS)
    log_step(f"UKPN areas found: {ukpn['short'].tolist()}")

    # ---------------- plot ----------------
    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.95))

    ukpn.boundary.plot(ax=ax, color="#333333", linewidth=1.0, zorder=5)

    x = gdf_pts.geometry.x.values
    y = gdf_pts.geometry.y.values
    hb = ax.hexbin(x, y, gridsize=60, cmap="viridis", bins="log", mincnt=1, linewidths=0.1, zorder=2)

    cbar = fig.colorbar(hb, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Event count (log scale)", fontsize=9)
    cbar.ax.tick_params(labelsize=9)

    for _, row in ukpn.iterrows():
        c = row.geometry.centroid
        ax.annotate(row["short"], (c.x, c.y), fontsize=9, fontweight="bold",
                    ha="center", va="center", color="#222222", zorder=6,
                    path_effects=None)

    minx, miny, maxx, maxy = ukpn.total_bounds
    dx, dy = maxx - minx, maxy - miny
    ax.set_xlim(minx - 0.05 * dx, maxx + 0.05 * dx)
    ax.set_ylim(miny - 0.05 * dy, maxy + 0.05 * dy)
    ax.set_axis_off()
    # No in-figure title (command #34): the figure's identity lives in the filename only.

    add_north_arrow(ax)
    add_scale_bar(ax)

    log_step("Building GB locator inset (dissolved LAD boundary, England+Wales+Scotland)...")
    gb = gpd.read_file(GB_BOUNDARY_SHP)
    code_col = "LAD21CD" if "LAD21CD" in gb.columns else [c for c in gb.columns if "LAD" in c.upper() and "CD" in c.upper()][0]
    gb = gb.to_crs(epsg=27700)
    gb_gb = gb[gb[code_col].astype(str).str.startswith(("E", "W", "S"))]
    gb_outline = gb_gb.dissolve()
    add_locator_inset(fig, ax, gb_outline, ukpn)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_1_study_area_map")
    plt.close(fig)

    log_step(f"Saved to {OUT_DIR}")
    log_step(f"n_events_plotted={len(gdf_pts)}, n_missing_coords_excluded={n_missing_coords}")


if __name__ == "__main__":
    main()
