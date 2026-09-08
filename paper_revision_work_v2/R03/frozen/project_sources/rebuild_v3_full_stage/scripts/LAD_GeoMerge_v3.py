#这是我准备的LAD地理信息因素的合并最后一步，把LAD表格合并到总表格中。
import pandas as pd
from pathlib import Path

# =========================================
# 路径
# =========================================
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

MASTER_FILE = DATA / "new//ukpn_master_final.csv"
LAD_FILE = DATA / "Local_Authority_Districts_December_2021_UK_BGC_2022" / "LAD_full_dataset_with_dno.csv"

OUTPUT_FILE = DATA / "new//ukpn_master_with_lad_features.csv"

# =========================================
# 读取数据
# =========================================
master = pd.read_csv(MASTER_FILE, low_memory=False)
lad = pd.read_csv(LAD_FILE, low_memory=False)

print("Master shape:", master.shape)
print("LAD shape:", lad.shape)

# =========================================
# 标准化 key（非常关键）
# =========================================
master["LADCD"] = master["LADCD"].astype(str).str.strip()
lad["LADCD"] = lad["LADCD"].astype(str).str.strip()

# =========================================
# 检查 LAD 表是否唯一（必须）
# =========================================
dup = lad["LADCD"].duplicated().sum()
print("LAD 表重复 LADCD 数量:", dup)

if dup > 0:
    print("⚠️ 警告：LAD 表有重复 key，先去重（保留第一条）")
    lad = lad.drop_duplicates(subset=["LADCD"])

# =========================================
# merge
# =========================================
merged = master.merge(
    lad,
    on="LADCD",
    how="left"
)

print("\n合并后 shape:", merged.shape)

# =========================================
# merge 质量检查（非常关键）
# =========================================
print("\n=== merge 缺失检查 ===")

# 检查几个关键列（你可以按实际列名改）
check_cols = [c for c in ["area_km2", "dno", "region"] if c in merged.columns]

for col in check_cols:
    print(f"{col} 缺失率: {merged[col].isna().mean():.2%}")

# =========================================
# 检查是否有 LAD 完全没匹配上
# =========================================
unmatched = merged[check_cols].isna().all(axis=1)

unmatched_lad = merged.loc[unmatched, ["LADCD", "LAD21NM"]].drop_duplicates()

print("\n未匹配 LAD 数量:", unmatched_lad.shape[0])
print(unmatched_lad.head(20))

# =========================================
# 保存
# =========================================
merged.to_csv(OUTPUT_FILE, index=False)

print(f"\n已保存到: {OUTPUT_FILE}")