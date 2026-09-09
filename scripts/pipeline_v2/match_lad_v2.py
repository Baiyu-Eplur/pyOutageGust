
# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

import pandas as pd
import geopandas as gpd
from pathlib import Path

# =========================
# 1. 路径配置
# =========================
incident_file = data_path('new/ukpn_master_weather_matrix.csv')

lad_shp = Path(
    str(data_path('Local_Authority_Districts_December_2021_UK_BGC_2022/LAD_DEC_2021_UK_BGC.shp'))
)

output_file = data_path('new/ukpn_master_weather_matrix_with_lad.csv')

# =========================
# 2. 读取事故数据
# =========================
df = pd.read_csv(read_input(incident_file))

# 检查经纬度列是否存在
required_cols = ["lat", "lon"]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"事故数据缺少必要字段: {missing_cols}")

# 去掉无效坐标
df = df.dropna(subset=["lat", "lon"]).copy()

# 可选：先做英国范围过滤
df = df[df["lat"].between(49, 61) & df["lon"].between(-9, 3)].copy()

print(f"事故数据条数（清洗后）: {len(df)}")

# =========================
# 3. 转成点 GeoDataFrame
# 注意：points_from_xy 是 (x=lon, y=lat)
# =========================
gdf_points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["lon"], df["lat"]),
    crs="EPSG:4326"
)

# =========================
# 4. 读取 LAD shapefile
# =========================
lad = gpd.read_file(read_input(lad_shp))

print("LAD 字段：")
print(lad.columns.tolist())
print("LAD 原始 CRS:", lad.crs)

# 统一到 WGS84，经纬度坐标系
lad = lad.to_crs("EPSG:4326")

# =========================
# 5. 空间匹配
# =========================
gdf_matched = gpd.sjoin(
    gdf_points,
    lad,
    how="left",
    predicate="within"
)

# =========================
# 6. 检查匹配结果
# =========================
# 常见字段一般是 LAD21CD / LAD21NM
candidate_code_cols = [c for c in gdf_matched.columns if "LAD" in c and "CD" in c]
candidate_name_cols = [c for c in gdf_matched.columns if "LAD" in c and "NM" in c]

print("候选 LAD code 字段:", candidate_code_cols)
print("候选 LAD name 字段:", candidate_name_cols)

if "LAD21CD" in gdf_matched.columns:
    lad_code_col = "LAD21CD"
elif len(candidate_code_cols) > 0:
    lad_code_col = candidate_code_cols[0]
else:
    lad_code_col = None

if "LAD21NM" in gdf_matched.columns:
    lad_name_col = "LAD21NM"
elif len(candidate_name_cols) > 0:
    lad_name_col = candidate_name_cols[0]
else:
    lad_name_col = None

if lad_code_col is None or lad_name_col is None:
    raise ValueError("没有在匹配结果中找到 LAD code/name 字段，请检查 shapefile 字段名。")

missing_rate = gdf_matched[lad_code_col].isna().mean()
print(f"LAD 未匹配比例: {missing_rate:.2%}")

print("\n匹配结果示例：")
print(gdf_matched[["lat", "lon", lad_code_col, lad_name_col]].head(10))

# =========================
# 7. 导出结果
# 去掉 geometry，保存回 csv
# =========================
output_df = pd.DataFrame(gdf_matched.drop(columns="geometry"))

output_df.to_csv(output_file, index=False)

print(f"\n已输出到: {output_file}")