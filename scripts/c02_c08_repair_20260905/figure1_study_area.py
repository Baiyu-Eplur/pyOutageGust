"""Final regeneration of Figure 1 (study-area map) on C01-corrected data.
No C02-C08 fix applies to this figure; regenerated purely for consistency
(same event set, only per-event gust/date corrected, which does not change
which events appear on the map)."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis")))
from figure_style import apply_style, mm_to_in, save_fig, add_north_arrow, add_scale_bar, add_locator_inset, DOUBLE_COL_MM  # noqa: E402

DNO_SHP = Path(r"D:\Pyprogramme\STST2603\data\dno_license_areas_20200506\DNO_License_Areas_20200506.shp")
GB_BOUNDARY_SHP = Path(r"D:\Pyprogramme\STST2603\data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
UKPN_AREAS = {"UKPN (East)": "EPN", "UKPN (London)": "LPN", "UKPN (South)": "SPN"}


def log_step(msg):
    print(f"[fig1-final] {msg}", flush=True)


def main():
    apply_style()
    combined_wt, _, _, _ = build_corrected_combined_samples()
    log_step(f"n={len(combined_wt)}")

    if "lat" not in combined_wt.columns or "lon" not in combined_wt.columns:
        SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
        coords = pd.read_csv(SRC, usecols=["Incident Reference", "lat", "lon"], low_memory=False).drop_duplicates("Incident Reference")
        combined_wt = combined_wt.merge(coords, on="Incident Reference", how="left")

    n_missing = combined_wt["lat"].isna().sum()
    pts = combined_wt.dropna(subset=["lat", "lon"]).copy()
    gdf_pts = gpd.GeoDataFrame(pts, geometry=[Point(xy) for xy in zip(pts["lon"], pts["lat"])],
                                crs="EPSG:4326").to_crs(epsg=27700)

    dno = gpd.read_file(DNO_SHP)
    ukpn = dno[dno["LongName"].isin(UKPN_AREAS.keys())].copy()
    ukpn["short"] = ukpn["LongName"].map(UKPN_AREAS)

    fig_w = mm_to_in(DOUBLE_COL_MM)
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.95))
    ukpn.boundary.plot(ax=ax, color="#333333", linewidth=1.0, zorder=5)
    x, y = gdf_pts.geometry.x.values, gdf_pts.geometry.y.values
    hb = ax.hexbin(x, y, gridsize=60, cmap="viridis", bins="log", mincnt=1, linewidths=0.1, zorder=2)
    cbar = fig.colorbar(hb, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Event count (log scale)", fontsize=9)
    cbar.ax.tick_params(labelsize=9)
    for _, row in ukpn.iterrows():
        c = row.geometry.centroid
        ax.annotate(row["short"], (c.x, c.y), fontsize=9, fontweight="bold", ha="center", va="center",
                    color="#222222", zorder=6)
    minx, miny, maxx, maxy = ukpn.total_bounds
    dx, dy = maxx - minx, maxy - miny
    ax.set_xlim(minx - 0.05 * dx, maxx + 0.05 * dx)
    ax.set_ylim(miny - 0.05 * dy, maxy + 0.05 * dy)
    ax.set_axis_off()

    add_north_arrow(ax)
    add_scale_bar(ax)
    gb = gpd.read_file(GB_BOUNDARY_SHP).to_crs(epsg=27700)
    gb_gb = gb[gb["LAD21CD"].astype(str).str.startswith(("E", "W", "S"))]
    add_locator_inset(fig, ax, gb_gb.dissolve(), ukpn)

    plt.tight_layout()
    save_fig(fig, OUT_DIR, "Figure_1_study_area_map")
    plt.close(fig)
    log_step(f"Saved. n_events_plotted={len(gdf_pts)}, n_missing_coords_excluded={n_missing}")


if __name__ == "__main__":
    main()
