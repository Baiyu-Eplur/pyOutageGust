
# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

# LAD 聚合还应该有人口和经济等因素，但是现在都已经融合进入总表中，因此，现在开始针对lad做聚合，这个代码是第一步，聚合面积

import geopandas as gpd
import os

# 1. 路径
folder_path = str(data_path('Local_Authority_Districts_December_2021_UK_BGC_2022'))

# 2. 自动找到 shp
shp_file = [f for f in os.listdir(read_input(folder_path)) if f.endswith(".shp")][0]
shp_path = os.path.join(folder_path, shp_file)

print("Using shapefile:", shp_path)

# 3. 读取
gdf = gpd.read_file(read_input(shp_path))

print("CRS:", gdf.crs)
print(gdf.columns)

# 4. 计算面积（km²）
gdf["area_km2"] = gdf.geometry.area / 1e6

# 5. 提取所需字段
output = gdf[["LAD21CD", "LAD21NM", "area_km2"]].copy()

# 6. 统一字段名，方便后续 merge
output.columns = ["LADCD", "LADNM", "area_km2"]

# 7. 排序
output = output.sort_values("LADCD").reset_index(drop=True)

# 8. 导出 CSV
output_path = os.path.join(folder_path, "LAD_area.csv")
output.to_csv(output_path, index=False, encoding="utf-8-sig")

print("Done. Saved to:", output_path)
print(output.head(10))