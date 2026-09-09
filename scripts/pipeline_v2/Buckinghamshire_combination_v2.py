
# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

from pathlib import Path
import pandas as pd
import numpy as np

# =========================================
# 1. 路径配置
# =========================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = data_path()

IMD_FILE = DATA_DIR / "localincomedeprivationdata.xlsx"
IMD_SHEET = "Rankings for all indicators"

# 这里用你已经 merge 了人口的主表
MAIN_FILE = DATA_DIR / "new//ukpn_master_weather_matrix_with_lad_pop.csv"
OUTPUT_FILE = DATA_DIR / "new//ukpn_master_with_income_deprivation_crosswalk.csv"

# 用于加权的 LAD-year population 长表
POP_LONG_FILE = DATA_DIR / "population_lad_long.csv"

# =========================================
# 2. 手动 crosswalk 映射
#    如果以后还有别的重组区域，继续往这里加
# =========================================
MANUAL_CROSSWALKS = [
    {
        "new_code": "E06000060",
        "new_name": "Buckinghamshire",
        "old_codes": ["E07000004", "E07000005", "E07000006", "E07000007"],
        "old_names": ["Aylesbury Vale", "Chiltern", "South Bucks", "Wycombe"]
    }
]

# =========================================
# 3. 读取 IMD / deprivation 表
# =========================================
imd = pd.read_excel(read_input(IMD_FILE), sheet_name=IMD_SHEET, header=1)
imd.columns = [str(c).strip() for c in imd.columns]

print("原始列名：")
print(imd.columns.tolist())

# =========================================
# 4. 标准化字段名
# =========================================
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
    raise ValueError(f"IMD 表缺少字段：{missing_keep}")

imd = imd[keep_cols].copy()

# =========================================
# 5. 清洗数值列
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

imd["LADCD"] = imd["LADCD"].astype(str).str.strip()
imd["LADNM"] = imd["LADNM"].astype(str).str.strip()

print("\n整理后的 IMD 表预览：")
print(imd.head())
print("\nIMD 表形状：", imd.shape)

# =========================================
# 6. 读取 population 长表（用于权重）
#    这里使用 2021 人口做加权
# =========================================
pop_long = pd.read_csv(read_input(POP_LONG_FILE), low_memory=False)
pop_long["LAD23CD"] = pop_long["LAD23CD"].astype(str).str.strip()
pop_long["year"] = pd.to_numeric(pop_long["year"], errors="coerce")
pop_long["population"] = pd.to_numeric(pop_long["population"], errors="coerce")

pop_2021 = pop_long.loc[pop_long["year"] == 2021, ["LAD23CD", "population"]].copy()
pop_2021 = pop_2021.rename(columns={"LAD23CD": "LADCD"})

# =========================================
# 7. 构造 manual crosswalk 新行
# =========================================
numeric_cols = [
    "deprivation_gap_pct",
    "deprivation_gap_rank",
    "morans_i",
    "morans_i_rank",
    "income_deprivation_rate",
    "income_deprivation_rate_rank",
    "income_deprivation_rate_quintile",
]
categorical_cols = [
    "profile",
    "rural_urban_classification",
]

crosswalk_rows = []

for item in MANUAL_CROSSWALKS:
    old_subset = imd[imd["LADCD"].isin(item["old_codes"])].copy()

    if old_subset.empty:
        print(f"\n[警告] 没找到旧 LAD 行：{item['new_name']} -> {item['old_codes']}")
        continue

    old_subset = old_subset.merge(pop_2021, on="LADCD", how="left")

    # 如果 population 缺失，就退化为简单平均
    use_weight = old_subset["population"].notna().all() and old_subset["population"].sum() > 0

    new_row = {
        "LADCD": item["new_code"],
        "LADNM": item["new_name"],
    }

    # 类别列：取众数
    for col in categorical_cols:
        vals = old_subset[col].dropna()
        if len(vals) == 0:
            new_row[col] = np.nan
        else:
            mode_vals = vals.mode()
            new_row[col] = mode_vals.iloc[0] if len(mode_vals) > 0 else vals.iloc[0]

    # 数值列：用 population 加权平均；如果没有权重就简单平均
    for col in numeric_cols:
        x = pd.to_numeric(old_subset[col], errors="coerce")
        if x.notna().sum() == 0:
            new_row[col] = np.nan
            continue

        if use_weight:
            w = old_subset["population"]
            valid = x.notna() & w.notna()
            if valid.sum() == 0:
                new_row[col] = x.mean()
            else:
                new_row[col] = np.average(x[valid], weights=w[valid])
        else:
            new_row[col] = x.mean()

    crosswalk_rows.append(new_row)

crosswalk_df = pd.DataFrame(crosswalk_rows)

print("\n手动 crosswalk 生成的新 LAD 行：")
print(crosswalk_df)

# =========================================
# 8. 把新行追加到 IMD 表
#    若主表里已经是新 code，就可以直接 merge
# =========================================
imd_augmented = pd.concat([imd, crosswalk_df], ignore_index=True)

# 去重：如果以后你手动又补了同一个 LAD，新行优先
imd_augmented = imd_augmented.drop_duplicates(subset=["LADCD"], keep="last").copy()

print("\n追加 crosswalk 后 IMD 表形状：", imd_augmented.shape)

# =========================================
# 9. 读取主表并 merge
# =========================================
main = pd.read_csv(read_input(MAIN_FILE), low_memory=False)

if "LAD21CD" in main.columns:
    main["LADCD"] = main["LAD21CD"].astype(str).str.strip()
elif "LADCD" not in main.columns:
    raise ValueError("主表中既没有 LAD21CD，也没有 LADCD，无法 merge。")

merged = main.merge(
    imd_augmented,
    on="LADCD",
    how="left",
    suffixes=("", "_imd")
)

# =========================================
# 10. 检查
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

print("\nBuckinghamshire 检查：")
buck = merged.loc[merged["LADCD"] == "E06000060", ["LADCD", "LAD21NM", "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]]
print(buck.head())

# =========================================
# 11. 保存
# =========================================
merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n已输出到: {OUTPUT_FILE}")