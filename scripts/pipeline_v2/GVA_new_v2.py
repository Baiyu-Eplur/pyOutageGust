
# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input

# 这个LAD数据合成的第三步，是gva的合并
import pandas as pd
from pathlib import Path

# =========================================
# 路径配置
# =========================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = data_path()

FILE = DATA_DIR / "regionalgvabbylainuk.xlsx"
OUTPUT_FILE = DATA_DIR / "gva_industry_2016.csv"

# =========================================
# 需要提取的 sheet
# =========================================
GVA_SHEETS = {
    "Total GVA": "gva_total",
    "GVA per head": "gva_pc",
    "ABDE Production": "gva_prod",
    "C Manufacturing": "gva_manufacturing",
    "F Construction": "gva_construction",
    "GHI Distribution": "gva_distribution",
    "J Information": "gva_information",
    "K Finance": "gva_finance",
    "L Real estate": "gva_realestate",
    "MN Professional": "gva_professional",
    "OPQ Public services": "gva_public",
    "RST Other services": "gva_other",
}

POP_SHEET = "Population"
YEAR = "2016"

# =========================================
# 手动 crosswalk：三个新区
# =========================================
MANUAL_CROSSWALKS = [
    {
        "new_code": "E06000060",
        "new_name": "Buckinghamshire",
        "old_codes": ["E07000004", "E07000005", "E07000006", "E07000007"],
    },
    {
        "new_code": "E07000245",
        "new_name": "West Suffolk",
        "old_codes": ["E07000201", "E07000204"],
    },
    {
        "new_code": "E07000244",
        "new_name": "East Suffolk",
        "old_codes": ["E07000205", "E07000206"],
    }
]

# =========================================
# 读取所有 sheet 名，并 strip
# =========================================
xls = pd.ExcelFile(read_input(FILE))
raw_sheets = xls.sheet_names
sheet_map = {s.strip(): s for s in raw_sheets}

print("所有 sheet 名：")
print(raw_sheets)

# =========================================
# 1. 读取 Population sheet，提取 2016 population
# =========================================
if POP_SHEET not in sheet_map:
    raise ValueError(f"找不到 Population sheet: {POP_SHEET}")

pop_df = pd.read_excel(read_input(FILE), sheet_name=sheet_map[POP_SHEET], header=2)
pop_df.columns = [str(c).strip() for c in pop_df.columns]

print("\nPopulation 列名：")
print(pop_df.columns.tolist())

code_col = [c for c in pop_df.columns if "code" in c.lower()][0]
name_col = [c for c in pop_df.columns if "name" in c.lower()][0]

if YEAR not in [str(c).strip() for c in pop_df.columns]:
    raise ValueError(f"Population sheet 找不到年份列 {YEAR}")

pop_df = pop_df.rename(columns={
    code_col: "LADCD",
    name_col: "LADNM"
})

pop_df["LADCD"] = pop_df["LADCD"].astype(str).str.strip()
pop_df = pop_df[pop_df["LADCD"].str.startswith(("E", "W", "S", "N"), na=False)].copy()

pop_sub = pop_df[["LADCD", YEAR]].copy()
pop_sub = pop_sub.rename(columns={YEAR: "population_2016"})
pop_sub["population_2016"] = pd.to_numeric(pop_sub["population_2016"], errors="coerce")

print("\nPopulation 2016 预览：")
print(pop_sub.head())

# =========================================
# 2. 读取各行业 sheet，提取 2016 GVA
# =========================================
merged = pop_sub.copy()

for target_sheet, varname in GVA_SHEETS.items():
    if target_sheet not in sheet_map:
        raise ValueError(f"找不到 sheet: {target_sheet}")

    actual_sheet = sheet_map[target_sheet]
    print(f"\n读取 sheet: {actual_sheet}")

    df = pd.read_excel(read_input(FILE), sheet_name=actual_sheet, header=2)
    df.columns = [str(c).strip() for c in df.columns]

    print("列名示例：", df.columns[:10].tolist())

    code_col = [c for c in df.columns if "code" in c.lower()][0]
    name_col = [c for c in df.columns if "name" in c.lower()][0]

    if YEAR not in [str(c).strip() for c in df.columns]:
        raise ValueError(f"{actual_sheet} 找不到年份列 {YEAR}")

    df = df.rename(columns={
        code_col: "LADCD",
        name_col: "LADNM"
    })

    df["LADCD"] = df["LADCD"].astype(str).str.strip()
    df = df[df["LADCD"].str.startswith(("E", "W", "S", "N"), na=False)].copy()

    sub = df[["LADCD", YEAR]].copy()
    sub = sub.rename(columns={YEAR: varname})
    sub[varname] = pd.to_numeric(sub[varname], errors="coerce")

    merged = merged.merge(sub, on="LADCD", how="outer")

print("\n基础 GVA 表预览：")
print(merged.head())
print("\n基础 GVA 表 shape:", merged.shape)

# =========================================
# 3. 手动 crosswalk：新增三个新区
#    总量类变量求和
#    gva_pc = gva_total / population_2016
# =========================================
sum_cols = [
    "population_2016",
    "gva_total",
    "gva_prod",
    "gva_manufacturing",
    "gva_construction",
    "gva_distribution",
    "gva_information",
    "gva_finance",
    "gva_realestate",
    "gva_professional",
    "gva_public",
    "gva_other",
]

new_rows = []

for item in MANUAL_CROSSWALKS:
    subset = merged[merged["LADCD"].isin(item["old_codes"])].copy()

    if subset.empty:
        print(f"\n[警告] 没找到旧 LAD：{item['new_name']} -> {item['old_codes']}")
        continue

    new_row = {"LADCD": item["new_code"]}

    for col in sum_cols:
        if col not in subset.columns:
            raise ValueError(f"缺少列: {col}")
        new_row[col] = pd.to_numeric(subset[col], errors="coerce").sum()

    total_pop = new_row["population_2016"]
    total_gva = new_row["gva_total"]

    if pd.notna(total_pop) and total_pop > 0 and pd.notna(total_gva):
        new_row["gva_pc"] = total_gva / total_pop
    else:
        new_row["gva_pc"] = pd.NA

    new_rows.append(new_row)

crosswalk_df = pd.DataFrame(new_rows)

print("\n手动 crosswalk 新行：")
print(crosswalk_df)

# =========================================
# 4. 追加新行
# =========================================
merged = pd.concat([merged, crosswalk_df], ignore_index=True)
merged = merged.drop_duplicates(subset=["LADCD"], keep="last").copy()

# =========================================
# 5. 为所有 LAD 统一生成 share
# =========================================
share_base_cols = [
    "gva_prod",
    "gva_manufacturing",
    "gva_construction",
    "gva_distribution",
    "gva_information",
    "gva_finance",
    "gva_realestate",
    "gva_professional",
    "gva_public",
    "gva_other",
]

for col in share_base_cols:
    merged[col + "_share"] = merged[col] / merged["gva_total"]

print("\n加入 share 后预览：")
print(merged.head())

print("\n最终 shape:", merged.shape)

# =========================================
# 6. 检查三个新区
# =========================================
print("\nBuckinghamshire 检查：")
print(merged[merged["LADCD"] == "E06000060"])

print("\nWest Suffolk 检查：")
print(merged[merged["LADCD"] == "E07000245"])

print("\nEast Suffolk 检查：")
print(merged[merged["LADCD"] == "E07000244"])

# =========================================
# 7. 保存
# =========================================
merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n已保存到: {OUTPUT_FILE}")