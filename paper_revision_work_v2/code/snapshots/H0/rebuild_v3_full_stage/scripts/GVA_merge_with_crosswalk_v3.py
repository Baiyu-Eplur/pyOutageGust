import pandas as pd
import numpy as np
from pathlib import Path

# =========================
# 路径
# =========================
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

MAIN_FILE = DATA / "new//ukpn_master_with_income_deprivation_crosswalk.csv"
GVA_FILE = DATA / "gva_industry_2016.csv"

# 用人口长表做 Buckinghamshire 的 gva_pc 重算
POP_FILE = DATA / "population_lad_long.csv"

OUTPUT = DATA / "new//ukpn_master_final.csv"

# =========================
# 读取
# =========================
main = pd.read_csv(MAIN_FILE, low_memory=False)
gva = pd.read_csv(GVA_FILE, low_memory=False)
pop = pd.read_csv(POP_FILE, low_memory=False)

# =========================
# 标准化 LAD code
# =========================
main["LADCD"] = main["LADCD"].astype(str).str.strip()
gva["LADCD"] = gva["LADCD"].astype(str).str.strip()
pop["LAD23CD"] = pop["LAD23CD"].astype(str).str.strip()
pop["year"] = pd.to_numeric(pop["year"], errors="coerce")
pop["population"] = pd.to_numeric(pop["population"], errors="coerce")

# =========================
# Buckinghamshire crosswalk
# 旧 LAD -> 新 Buckinghamshire
# =========================
old_codes = ["E07000004", "E07000005", "E07000006", "E07000007"]
new_code = "E06000060"

gva_old = gva[gva["LADCD"].isin(old_codes)].copy()

if gva_old.empty:
    print("[警告] GVA 表中未找到 Buckinghamshire 旧 LAD 代码，跳过 crosswalk。")
else:
    # 先取 2021 人口做权重/重算 per head
    pop_2021 = pop.loc[pop["year"] == 2021, ["LAD23CD", "population"]].copy()
    pop_2021 = pop_2021.rename(columns={"LAD23CD": "LADCD"})

    gva_old = gva_old.merge(pop_2021, on="LADCD", how="left")

    # 这些列是“总量”或“行业总量”，应该求和
    sum_cols = [
        c for c in gva_old.columns
        if c.startswith("gva_")
        and c not in ["gva_pc"]
        and not c.endswith("_share")
    ]

    new_row = {"LADCD": new_code}

    for col in sum_cols:
        new_row[col] = pd.to_numeric(gva_old[col], errors="coerce").sum()

    # gva_pc 重新计算：总 GVA / 总人口
    total_pop = gva_old["population"].sum(min_count=1)
    if pd.notna(total_pop) and total_pop > 0 and pd.notna(new_row.get("gva_total", np.nan)):
        new_row["gva_pc"] = new_row["gva_total"] / total_pop
    else:
        # fallback：人口加权平均
        x = pd.to_numeric(gva_old["gva_pc"], errors="coerce")
        w = gva_old["population"]
        valid = x.notna() & w.notna()
        new_row["gva_pc"] = np.average(x[valid], weights=w[valid]) if valid.sum() > 0 else np.nan

    # 重新计算 share
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

    total_gva = new_row.get("gva_total", np.nan)
    for col in share_base_cols:
        share_col = col + "_share"
        if pd.notna(total_gva) and total_gva != 0 and col in new_row:
            new_row[share_col] = new_row[col] / total_gva
        else:
            new_row[share_col] = np.nan

    # 追加新行，并保证新 code 优先
    gva = pd.concat([gva, pd.DataFrame([new_row])], ignore_index=True)
    gva = gva.drop_duplicates(subset=["LADCD"], keep="last").copy()

    print("\nBuckinghamshire crosswalk 新行：")
    print(pd.DataFrame([new_row]))

# =========================
# merge
# =========================
merged = main.merge(
    gva,
    on="LADCD",
    how="left"
)

# =========================
# 检查
# =========================
check_cols = [
    "gva_total",
    "gva_pc",
    "gva_manufacturing_share"
]

print("\nGVA merge 后缺失率：")
for c in check_cols:
    if c in merged.columns:
        print(f"{c}: {merged[c].isna().mean():.2%}")

print("\nBuckinghamshire 检查：")
print(
    merged.loc[
        merged["LADCD"] == "E06000060",
        ["LADCD", "LAD21NM", "gva_total", "gva_pc"] +
        [c for c in ["gva_manufacturing_share", "gva_construction_share", "gva_public_share"] if c in merged.columns]
    ].head()
)

# =========================
# 可选：构造 log 变量
# =========================
if "gva_pc" in merged.columns:
    merged["log_gva_pc"] = np.where(merged["gva_pc"] > 0, np.log(merged["gva_pc"]), np.nan)

# =========================
# 保存
# =========================
merged.to_csv(OUTPUT, index=False)
print("\n已保存:", OUTPUT)