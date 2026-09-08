from pathlib import Path
import pandas as pd

# =========================================
# 1. 路径配置
# =========================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

IMD_FILE = DATA_DIR / "localincomedeprivationdata.xlsx"
IMD_SHEET = "Rankings for all indicators"

MAIN_FILE = DATA_DIR / "new//ukpn_master_weather_matrix_with_lad_pop.csv"
OUTPUT_FILE = DATA_DIR / "new//ukpn_master_with_income_deprivation.csv"

# =========================================
# 2. 读取 IMD / income deprivation 表
#    你截图显示表头在第 2 行，所以 header=1
# =========================================
imd = pd.read_excel(IMD_FILE, sheet_name=IMD_SHEET, header=1)

print("原始列名：")
print(imd.columns.tolist())

# =========================================
# 3. 标准化列名
# =========================================
imd.columns = [str(c).strip() for c in imd.columns]

rename_map = {
    "Local Authority District code (2019)": "LADCD",
    "Local Authority District name (2019)": "LADNM",
    "Profile": "profile",
    "Rural-urban classification": "rural_urban_classification",
    "Deprivation gap (percentage points)": "deprivation_gap_pct",
    "Deprivation gap ranking": "deprivation_gap_rank",
    "Moran's I": "morans_i",
    "Moran's I ranking": "morans_i_rank",
    "Income deprivation rate": "income_deprivation_rate",
    "Income deprivation rate ranking": "income_deprivation_rate_rank",
    "Income deprivation rate quintile": "income_deprivation_rate_quintile",
}

imd = imd.rename(columns=rename_map)

# =========================================
# 4. 只保留你现在最有用的字段
#    后面还可以再扩展
# =========================================
keep_cols = [
    "LADCD",
    "LADNM",
    "profile",
    "rural_urban_classification",
    "deprivation_gap_pct",
    "deprivation_gap_rank",
    "morans_i",
    "morans_i_rank",
    "income_deprivation_rate",
    "income_deprivation_rate_rank",
    "income_deprivation_rate_quintile",
]

missing_keep = [c for c in keep_cols if c not in imd.columns]
if missing_keep:
    raise ValueError(f"IMD 表缺少这些字段，请检查表头名称：{missing_keep}")

imd = imd[keep_cols].copy()

# =========================================
# 5. 数值清洗
#    百分比列可能读成字符串，比如 '21.7%'
# =========================================
def pct_to_float(series):
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace({"#N/A": None, "nan": None, "None": None})
        .pipe(pd.to_numeric, errors="coerce")
    )

imd["deprivation_gap_pct"] = pct_to_float(imd["deprivation_gap_pct"])
imd["income_deprivation_rate"] = pct_to_float(imd["income_deprivation_rate"])

for col in [
    "deprivation_gap_rank",
    "morans_i",
    "morans_i_rank",
    "income_deprivation_rate_rank",
    "income_deprivation_rate_quintile",
]:
    imd[col] = pd.to_numeric(imd[col], errors="coerce")

# 去掉 LAD code 缺失的行
imd["LADCD"] = imd["LADCD"].astype(str).str.strip()
imd = imd[imd["LADCD"].notna() & (imd["LADCD"] != "")].copy()

print("\n整理后的 IMD 表预览：")
print(imd.head())
print("\nIMD 表形状：", imd.shape)

# =========================================
# 6. 读取主表
# =========================================
main = pd.read_csv(MAIN_FILE, low_memory=False)

# 统一 LAD code
if "LAD21CD" in main.columns:
    main["LADCD"] = main["LAD21CD"].astype(str).str.strip()
elif "LADCD" not in main.columns:
    raise ValueError("主表中既没有 LAD21CD，也没有 LADCD，无法 merge。")

# =========================================
# 7. merge
#    这是地区固定变量，所以只按 LAD merge，不按 year
# =========================================
merged = main.merge(
    imd,
    on="LADCD",
    how="left",
    suffixes=("", "_imd")
)

# =========================================
# 8. 检查
# =========================================
check_cols = [
    "income_deprivation_rate",
    "deprivation_gap_pct",
    "morans_i",
    "rural_urban_classification",
]

print("\nmerge 后缺失率：")
for c in check_cols:
    if c in merged.columns:
        print(f"{c}: {merged[c].isna().mean():.2%}")

print("\nmerge 后示例：")
show_cols = [
    c for c in [
        "LADCD",
        "LAD21NM",
        "income_deprivation_rate",
        "deprivation_gap_pct",
        "morans_i",
        "profile",
        "rural_urban_classification",
    ] if c in merged.columns
]
print(merged[show_cols].head(10))

# =========================================
# 9. 保存
# =========================================
merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n已输出到: {OUTPUT_FILE}")