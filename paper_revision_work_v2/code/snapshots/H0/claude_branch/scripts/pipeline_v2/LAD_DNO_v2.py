# 这是第三步，合并的是DNO数据，即每个地区的电力公司名字
import os
import geopandas as gpd
import pandas as pd

# =========================================================
# 1. 路径设置
# =========================================================
lad_folder = r"data\Local_Authority_Districts_December_2021_UK_BGC_2022"
dno_folder = r"data\dno_license_areas_20200506"

# 你当前已经整理好的 LAD 表格
# 如果你的文件名不是这个，请改成你自己的
lad_csv_path = os.path.join(lad_folder, "LAD_area_with_bua_gb.csv")

# LAD 边界 shp
lad_shp = [f for f in os.listdir(lad_folder) if f.lower().endswith(".shp")][0]
lad_shp_path = os.path.join(lad_folder, lad_shp)

# DNO shp
dno_shp = [f for f in os.listdir(dno_folder) if f.lower().endswith(".shp")][0]
dno_shp_path = os.path.join(dno_folder, dno_shp)

print("LAD csv:", lad_csv_path)
print("LAD shapefile:", lad_shp_path)
print("DNO shapefile:", dno_shp_path)

# =========================================================
# 2. 读取数据
# =========================================================
lad_csv = pd.read_csv(lad_csv_path)
lad_gdf = gpd.read_file(lad_shp_path)
dno_gdf = gpd.read_file(dno_shp_path)

print("\nLAD shapefile columns:")
print(lad_gdf.columns)

print("\nDNO shapefile columns:")
print(dno_gdf.columns)

print("\nLAD CRS:", lad_gdf.crs)
print("DNO CRS:", dno_gdf.crs)

# =========================================================
# 3. 统一坐标系
# =========================================================
if dno_gdf.crs != lad_gdf.crs:
    dno_gdf = dno_gdf.to_crs(lad_gdf.crs)
    print("\nDNO CRS converted to:", dno_gdf.crs)

# =========================================================
# 4. LAD 基础表
# =========================================================
lad_use = lad_gdf[["LAD21CD", "LAD21NM", "geometry"]].copy()
lad_use["lad_area_km2"] = lad_use.geometry.area / 1e6
lad_use["nation"] = lad_use["LAD21CD"].astype(str).str[0].map({
    "E": "England",
    "W": "Wales",
    "S": "Scotland",
    "N": "Northern Ireland"
})

# GB only: DNO shapefile 只覆盖 Great Britain
lad_gb = lad_use[lad_use["nation"].isin(["England", "Wales", "Scotland"])].copy()

# =========================================================
# 5. 直接指定 DNO 字段
# =========================================================
dno_name_col = "Name"
dno_area_col = "LongName"

print("\nUsing DNO name column:", dno_name_col)
print("Using DNO licence-area column:", dno_area_col)

dno_use = dno_gdf[[dno_name_col, dno_area_col, "geometry"]].copy()
dno_use = dno_use.rename(columns={
    dno_name_col: "dno_name",
    dno_area_col: "dno_licence_area"
})

# =========================================================
# 6. 面积重叠匹配：LAD × DNO
# =========================================================
print("\nRunning overlay (largest overlap method)...")

inter = gpd.overlay(
    lad_gb[["LAD21CD", "LAD21NM", "lad_area_km2", "geometry"]],
    dno_use,
    how="intersection"
)

print("Overlay finished.")
print("Number of intersected polygons:", len(inter))

# 计算重叠面积
inter["dno_overlap_km2"] = inter.geometry.area / 1e6
inter["dno_overlap_ratio"] = inter["dno_overlap_km2"] / inter["lad_area_km2"]

# 每个 LAD 选重叠面积最大的 DNO
inter = inter.sort_values(
    ["LAD21CD", "dno_overlap_km2"],
    ascending=[True, False]
)

best_match = inter.groupby("LAD21CD", as_index=False).first()

best_match = best_match[[
    "LAD21CD", "LAD21NM",
    "dno_name", "dno_licence_area",
    "dno_overlap_km2", "dno_overlap_ratio"
]].copy()

best_match["match_method"] = "largest_overlap"

# =========================================================
# 7. Northern Ireland 单独处理
# =========================================================
# GB DNO 数据不覆盖 NI，所以直接指定 NIE Networks
ni_rows = lad_use[lad_use["nation"] == "Northern Ireland"][["LAD21CD", "LAD21NM"]].copy()
ni_rows["dno_name"] = "NIE Networks"
ni_rows["dno_licence_area"] = "Northern Ireland"
ni_rows["dno_overlap_km2"] = pd.NA
ni_rows["dno_overlap_ratio"] = 1.0
ni_rows["match_method"] = "manual_NI"

# 合并 GB + NI 匹配表
dno_mapping = pd.concat([
    best_match,
    ni_rows
], ignore_index=True)

dno_mapping = dno_mapping.rename(columns={
    "LAD21CD": "LADCD",
    "LAD21NM": "LADNM"
})

# =========================================================
# 8. merge 到你当前的 LAD 主表
# =========================================================
lad_csv["LADCD"] = lad_csv["LADCD"].astype(str).str.strip()
lad_csv["LADNM"] = lad_csv["LADNM"].astype(str).str.strip()

dno_mapping["LADCD"] = dno_mapping["LADCD"].astype(str).str.strip()
dno_mapping["LADNM"] = dno_mapping["LADNM"].astype(str).str.strip()

final_df = lad_csv.merge(
    dno_mapping[[
        "LADCD", "dno_name", "dno_licence_area",
        "dno_overlap_km2", "dno_overlap_ratio", "match_method"
    ]],
    on="LADCD",
    how="left"
)

# =========================================================
# 9. 输出
# =========================================================
output_path = os.path.join(lad_folder, "LAD_full_dataset_with_dno.csv")
final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("\nDone. Saved to:")
print(output_path)

print("\nPreview:")
print(final_df.head(10))

print("\nMissing DNO rows:", final_df["dno_name"].isna().sum())
print("\nDNO distribution:")
print(final_df["dno_name"].value_counts(dropna=False))