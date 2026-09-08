import re
from pathlib import Path
import pandas as pd

# =========================================
# 1. 路径配置
# =========================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

POP_FILE = DATA_DIR / "myebtablesuk20112024.xlsx"
POP_SHEET = "MYEB3"

MAIN_FILE = DATA_DIR / "new//ukpn_master_weather_matrix_with_lad.csv"
OUTPUT_FILE = DATA_DIR / "new//ukpn_master_weather_matrix_with_lad_pop.csv"

# 可选：把整理好的 LAD-year 人口长表也单独保存
POP_LONG_FILE = DATA_DIR / "population_lad_long.csv"


# =========================================
# 2. 读取人口表
#    你的说明是“第二行开始是表头”
#    pandas 里 header=1 表示第2行作为列名
# =========================================
pop_raw = pd.read_excel(POP_FILE, sheet_name=POP_SHEET, header=1)

print("原始人口表列名示例：")
print(pop_raw.columns.tolist()[:20])


# =========================================
# 3. 标准化列名
# =========================================
pop_raw.columns = [str(c).strip().lower() for c in pop_raw.columns]

# 兼容你样例里可能出现的列名
rename_map = {}
for c in pop_raw.columns:
    if c == "ladcode23":
        rename_map[c] = "LAD23CD"
    elif c == "laname23":
        rename_map[c] = "LAD23NM"

pop_raw = pop_raw.rename(columns=rename_map)

# 若没有这两列，直接报错
required_base_cols = ["LAD23CD", "LAD23NM"]
missing_base = [c for c in required_base_cols if c not in pop_raw.columns]
if missing_base:
    raise ValueError(f"人口表缺少关键字段: {missing_base}")


# =========================================
# 4. 识别所有 *_YYYY 格式的列
#    例如 population_2024, births_2023 ...
# =========================================
year_pattern = re.compile(r"^(.*)_(20\d{2})$")

year_cols = []
for c in pop_raw.columns:
    m = year_pattern.match(c)
    if m:
        var_name, year = m.group(1), int(m.group(2))
        year_cols.append((c, var_name, year))

if not year_cols:
    raise ValueError("没有识别到 *_YYYY 格式的年度变量列。请检查表头。")

print(f"\n识别到年度变量列数量: {len(year_cols)}")
print("前10个示例：")
print(year_cols[:10])


# =========================================
# 5. 宽表 → 长表
#    目标结构：
#    LAD23CD | LAD23NM | year | population | births | ...
# =========================================
# 先建立所有变量名集合
var_names = sorted(set(v for _, v, _ in year_cols))
years = sorted(set(y for _, _, y in year_cols))

print(f"\n识别到变量: {var_names[:15]}")
print(f"识别到年份范围: {years[0]} - {years[-1]}")

# 先保留基础列
base = pop_raw[["LAD23CD", "LAD23NM"]].copy()

# 为每个变量做一次 melt，然后逐步 merge
long_df = None

for var in var_names:
    var_cols = [col for col, v, y in year_cols if v == var]

    tmp = pop_raw[["LAD23CD", "LAD23NM"] + var_cols].copy()

    tmp_long = tmp.melt(
        id_vars=["LAD23CD", "LAD23NM"],
        value_vars=var_cols,
        var_name="var_year",
        value_name=var
    )

    tmp_long["year"] = tmp_long["var_year"].str.extract(r"(20\d{2})").astype(int)
    tmp_long = tmp_long.drop(columns="var_year")

    # 数值化
    tmp_long[var] = pd.to_numeric(tmp_long[var], errors="coerce")

    if long_df is None:
        long_df = tmp_long
    else:
        long_df = long_df.merge(
            tmp_long,
            on=["LAD23CD", "LAD23NM", "year"],
            how="outer"
        )

# 排序
long_df = long_df.sort_values(["LAD23CD", "year"]).reset_index(drop=True)

print("\n整理后的 LAD-year 长表预览：")
print(long_df.head())
print("\n长表形状：", long_df.shape)

# 保存长表
long_df.to_csv(POP_LONG_FILE, index=False)
print(f"\n已保存人口长表: {POP_LONG_FILE}")


# =========================================
# 6. 读取主数据表
# =========================================
main_df = pd.read_csv(MAIN_FILE, low_memory=False)

print("\n主表列名检查：")
print([c for c in ["LAD21CD", "clean_start", "date", "LAD21NM"] if c in main_df.columns])

if "LAD21CD" not in main_df.columns:
    raise ValueError("主表中没有 LAD21CD，无法按地区 merge。")

# 生成年份
if "clean_start" in main_df.columns:
    main_df["year"] = pd.to_datetime(main_df["clean_start"], errors="coerce").dt.year
elif "date" in main_df.columns:
    main_df["year"] = pd.to_datetime(main_df["date"], errors="coerce").dt.year
else:
    raise ValueError("主表中没有 clean_start 或 date，无法提取年份。")


# =========================================
# 7. LAD code 统一
#    你的主表是 LAD21CD，人口表是 LAD23CD
#    很多地区代码在 2021-2024 期间保持一致，但不保证 100%。
#    这里先直接匹配；后面若缺失率高，再做 code crosswalk。
# =========================================
long_df_for_merge = long_df.rename(columns={"LAD23CD": "LAD21CD"})

# merge
merged = main_df.merge(
    long_df_for_merge,
    on=["LAD21CD", "year"],
    how="left",
    suffixes=("", "_pop")
)

# =========================================
# 8. 简单检查
# =========================================
core_check_cols = [c for c in ["population", "births", "deaths", "internal_in", "internal_out",
                               "international_in", "international_out", "other_change"] if c in merged.columns]

print("\nmerge 后核心变量缺失率：")
for c in core_check_cols:
    print(f"{c}: {merged[c].isna().mean():.2%}")

print("\nmerge 后示例：")
show_cols = [c for c in ["LAD21CD", "year", "LAD21NM", "population", "births", "deaths",
                         "internal_in", "internal_out", "international_in", "international_out",
                         "other_change"] if c in merged.columns]
print(merged[show_cols].head(10))

# 保存
merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n已输出合并后的主表: {OUTPUT_FILE}")