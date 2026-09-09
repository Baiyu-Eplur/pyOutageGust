
# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

# 这个是 lad 数据融合第二步：融合城市化率（基于 BUA 2022 GB 边界）
import os
import geopandas as gpd
import pandas as pd

# =========================
# 1. 路径设置
# =========================
lad_folder = str(data_path('Local_Authority_Districts_December_2021_UK_BGC_2022'))
bua_folder = str(data_path('BUA_2022_GB_-3259870081615132876'))

# 自动寻找 shp 文件
lad_shp = [f for f in os.listdir(read_input(lad_folder)) if f.lower().endswith(".shp")][0]
bua_shp = [f for f in os.listdir(read_input(bua_folder)) if f.lower().endswith(".shp")][0]

lad_path = os.path.join(lad_folder, lad_shp)
bua_path = os.path.join(bua_folder, bua_shp)

print("LAD shapefile:", lad_path)
print("BUA shapefile:", bua_path)

# =========================
# 2. 读取数据
# =========================
lad = gpd.read_file(read_input(lad_path))
bua = gpd.read_file(read_input(bua_path))

print("\nLAD columns:")
print(lad.columns)

print("\nBUA columns:")
print(bua.columns)

print("\nLAD CRS:", lad.crs)
print("BUA CRS:", bua.crs)

print("\nBUA preview:")
print(bua.head())

# =========================
# 3. 统一坐标系
# =========================
if bua.crs != lad.crs:
    bua = bua.to_crs(lad.crs)
    print("\nBUA CRS converted to:", bua.crs)

# =========================
# 4. 保留 LAD 关键字段并计算总面积
# =========================
lad_use = lad[["LAD21CD", "LAD21NM", "geometry"]].copy()
lad_use["area_km2"] = lad_use.geometry.area / 1e6

# 国家标记
lad_use["nation"] = lad_use["LAD21CD"].str[0].map({
    "E": "England",
    "W": "Wales",
    "S": "Scotland",
    "N": "Northern Ireland"
})

# =========================
# 5. 仅对 GB（E/W/S）做 BUA 相交
# 因为 BUA 数据不覆盖 Northern Ireland
# =========================
lad_gb = lad_use[lad_use["nation"].isin(["England", "Wales", "Scotland"])].copy()

print("\nRunning spatial intersection for Great Britain only...")

# BUA 只保留 geometry，减少内存占用
bua_use = bua[["geometry"]].copy()

intersection = gpd.overlay(
    bua_use,
    lad_gb[["LAD21CD", "LAD21NM", "geometry"]],
    how="intersection"
)

print("Intersection finished.")
print("Number of intersected polygons:", len(intersection))

# =========================
# 6. 计算每个交集面的面积并按 LAD 聚合
# =========================
intersection["intersect_area_km2"] = intersection.geometry.area / 1e6

bua_by_lad = (
    intersection.groupby(["LAD21CD", "LAD21NM"], as_index=False)["intersect_area_km2"]
    .sum()
    .rename(columns={"intersect_area_km2": "bua_area_km2"})
)

# =========================
# 7. 合并回 LAD 主表
# =========================
result = lad_use.merge(bua_by_lad, on=["LAD21CD", "LAD21NM"], how="left")

# GB 范围内，没有 BUA 的置 0；Northern Ireland 保持缺失
gb_mask = result["nation"].isin(["England", "Wales", "Scotland"])
result.loc[gb_mask, "bua_area_km2"] = result.loc[gb_mask, "bua_area_km2"].fillna(0)

# 城市化率
result["urban_ratio"] = result["bua_area_km2"] / result["area_km2"]

# 防止少数边界精度问题
result.loc[gb_mask, "urban_ratio"] = result.loc[gb_mask, "urban_ratio"].clip(lower=0, upper=1)

# 覆盖标记
result["bua_gb_coverage"] = gb_mask.astype(int)

# =========================
# 8. 整理输出字段
# =========================
output = result[[
    "LAD21CD", "LAD21NM", "nation",
    "area_km2", "bua_area_km2", "urban_ratio", "bua_gb_coverage"
]].copy()

output.columns = [
    "LADCD", "LADNM", "nation",
    "area_km2", "bua_area_km2", "urban_ratio", "bua_gb_coverage"
]

output["LADCD"] = output["LADCD"].astype(str).str.strip()
output["LADNM"] = output["LADNM"].astype(str).str.strip()

output = output.sort_values("LADCD").reset_index(drop=True)

# =========================
# 9. 输出 CSV
# =========================
output_csv = os.path.join(lad_folder, "LAD_area_with_bua_gb.csv")
output.to_csv(output_csv, index=False, encoding="utf-8-sig")

print("\nDone. Saved to:")
print(output_csv)

print("\nPreview:")
print(output.head(10))

print("\nCoverage check by nation:")
print(output.groupby("nation")[["bua_area_km2", "urban_ratio"]].apply(lambda x: x.isna().sum()))

print("\nSummary (GB only):")
print(output.loc[output["bua_gb_coverage"] == 1, ["area_km2", "bua_area_km2", "urban_ratio"]].describe())