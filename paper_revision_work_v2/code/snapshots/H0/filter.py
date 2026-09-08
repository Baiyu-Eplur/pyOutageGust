import pandas as pd
import os
from pathlib import Path


def normalize_cause_code(x):
    """
    将 Cause Code 标准化为官方风格：
    - 数字码补零成两位，如 1 -> '01'
    - 字母数字码保留，如 A1, A2
    - D, X 保留
    """
    if pd.isna(x):
        return None

    s = str(x).strip().upper()

    if s in {"D", "X", "A1", "A2"}:
        return s

    # 处理像 1.0 / 75.0
    try:
        f = float(s)
        if f.is_integer():
            return f"{int(f):02d}"
    except Exception:
        pass

    # 纯数字字符串
    if s.isdigit():
        return f"{int(s):02d}"

    return s


def classify_cause_code(code):
    """
    基于 Ofgem Annex F Appendix 3 的官方 Cause Code 分组。
    """

    # 1) 天气 / 自然暴露
    weather_natural = {
        "01",  # Lightning
        "02",  # Rain
        "03",  # Snow and Ice
        "04",  # Ice
        "05",  # Freezing Fog & Frost
        "06",  # Wind and gale
        "07",  # Solar heat
        "10",  # Airborne deposits
        "18",  # Flooding
        "21",  # Windborne Material
        "23",  # Falling live trees
        "24",  # Falling dead trees
        "25",  # Growing Trees
        "30",  # Birds
        "32",  # Vermin, wild animals and insects
        "33",  # Farm and domestic animals
    }

    # 2) 设备 / 网络内部技术故障
    technical_asset = {
        "14",  # Condensation
        "15",  # Corrosion
        "16",  # Mechanical shock or vibration
        "17",  # Ground subsidence
        "19",  # Fire not due to faults
        "22",  # Disruption of intended indoor environment
        "26",  # Corrosion due to atmosphere/environment
        "64",  # Corrosion due to Bi-Metal Contact
        "67",  # Load current above previous assessment
        "70",  # Inadequate rupturing or short circuit capacity
        "71",  # Deterioration due to ageing or wear
        "72",  # Fault on equipment faulting adjacent equipment
        "73",  # Unsuitable paralleling conditions
        "76",  # Extension of Fault Zone due to Fault Switching
        "77",  # Inadequate or faulty maintenance
        "78",  # Extension of Fault Zone due to incorrect operation of equipment
        "90",  # Faulty manufacturing, design, assembly or materials
        "A1",  # Transient Fault - No Repair
        "A2",  # Premature Insulation Failure
    }

    # 3) 第三方 / 外部施工 / 故意破坏
    third_party = {
        "39", "40", "41", "42", "43", "44", "45",
        "48", "49", "50", "53", "54", "55", "56", "57", "58",
    }

    # 4) DNO / 承包商人为错误
    human_error = {
        "60", "61", "62", "63", "65", "66", "68", "69",
        "81", "82", "83", "84",
    }

    # 5) 外部系统 / 客户侧 / 本地发电
    external_or_customer = {
        "74",  # Failure of infeed from Adjacent Distribution Network
        "80",  # Failure of Supply from Generating Company or NGC
        "85",  # Fault on customers network
        "86",  # Remove local generator / restore temp connections
        "87",  # Local generation failure
        "88",  # Affected by National Grid Company personnel/equipment
        "89",  # Affected by private generator / AEO
    }

    # 6) 非明确物理故障 / 不可用
    non_fault_or_unknown = {
        "75",  # Operational or safety restriction
        "97",  # No Fault Found
        "98",  # Cause Unclassified
        "99",  # Cause Unknown
        "D",   # Dummy - Do not set
        "X",   # NONE
    }

    if code in weather_natural:
        return "weather_natural"
    if code in technical_asset:
        return "technical_asset"
    if code in third_party:
        return "third_party"
    if code in human_error:
        return "human_error"
    if code in external_or_customer:
        return "external_or_customer"
    if code in non_fault_or_unknown:
        return "non_fault_or_unknown"
    return "unmapped"


def generate_weather_fetch_list_strict(
    input_path,
    output_path="unplanned_incidents_clean.csv",
    excluded_output_path="excluded_incidents_audit.csv",
    summary_output_path="cause_code_screening_summary.csv"
):
    print("--- 步骤 1: 读取原始全量数据 ---")
    try:
        df = pd.read_csv(input_path, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding="latin1", low_memory=False)

    df.columns = [c.strip() for c in df.columns]

    # 动态定位关键列
    incident_col = [c for c in df.columns if "incident" in c.lower() and "ref" in c.lower()][0]
    cause_col = [c for c in df.columns if "cause" in c.lower() and "code" in c.lower()][0]

    # 尽量找到时间列，便于按最早记录去重
    time_candidates = [c for c in df.columns if "start" in c.lower() and "time" in c.lower()]
    time_col = time_candidates[0] if time_candidates else None

    initial_count = len(df)
    print(f"成功加载数据。初始总记录数: {initial_count:,} 行")
    print(f"识别到事故列: {incident_col}")
    print(f"识别到原因列: {cause_col}")
    print(f"识别到时间列: {time_col}")

    # 标准化 Cause Code
    df["cause_code_norm"] = df[cause_col].apply(normalize_cause_code)
    df["cause_group_official"] = df["cause_code_norm"].apply(classify_cause_code)

    # 严格筛选：仅保留天气/自然 + 技术/资产故障
    keep_groups = {"weather_natural", "technical_asset"}
    df["keep_for_weather_analysis"] = df["cause_group_official"].isin(keep_groups)

    print("\n--- 步骤 2: 官方 Cause Code 分组统计 ---")
    print(df["cause_group_official"].value_counts(dropna=False))

    print("\n--- 步骤 3: 严格筛选，剔除非目标事故 ---")
    excluded_df = df[~df["keep_for_weather_analysis"]].copy()
    df_filtered = df[df["keep_for_weather_analysis"]].copy()

    # 若有时间列，先排序，确保去重时保留最早事故记录
    if time_col is not None:
        df_filtered["_sort_time"] = pd.to_datetime(
            df_filtered[time_col],
            errors="coerce",
            utc=True
        )
        df_filtered = df_filtered.sort_values([incident_col, "_sort_time"], kind="stable")
    else:
        df_filtered = df_filtered.sort_values([incident_col], kind="stable")

    print(f"筛选后剩余记录数: {len(df_filtered):,}")

    print("\n--- 步骤 4: 按 Incident Reference 去重，仅保留每个事故最早一条 ---")
    df_unique = df_filtered.drop_duplicates(subset=[incident_col], keep="first").copy()

    # 清理临时列
    if "_sort_time" in df_unique.columns:
        df_unique = df_unique.drop(columns=["_sort_time"])

    final_count = len(df_unique)

    # 保存主输出
    df_unique.to_csv(output_path, index=False)

    # 保存被剔除的审计表
    audit_cols = [incident_col, cause_col, "cause_code_norm", "cause_group_official"]
    existing_audit_cols = [c for c in audit_cols if c in excluded_df.columns]
    excluded_df[existing_audit_cols].to_csv(excluded_output_path, index=False)

    # 保存筛选摘要
    summary = (
        df.groupby(["cause_code_norm", "cause_group_official"], dropna=False)
        .size()
        .reset_index(name="raw_count")
    )

    kept = (
        df_filtered.groupby(["cause_code_norm", "cause_group_official"], dropna=False)
        .size()
        .reset_index(name="kept_count")
    )

    summary = summary.merge(
        kept,
        on=["cause_code_norm", "cause_group_official"],
        how="left"
    )
    summary["kept_count"] = summary["kept_count"].fillna(0).astype(int)
    summary["excluded_count"] = summary["raw_count"] - summary["kept_count"]
    summary.to_csv(summary_output_path, index=False)

    print("\n" + "=" * 50)
    print("【严格筛选完成报告】")
    print(f"1. 原始记录总数: {initial_count:,}")
    print(f"2. 严格筛选后剩余: {len(df_filtered):,}")
    print(f"3. 按事故去重后唯一事故数: {final_count:,}")
    print(f"4. 相对原始记录减少: {((initial_count - final_count) / initial_count) * 100:.1f}%")
    print(f"5. 主输出文件: {output_path}")
    print(f"6. 被剔除事故审计表: {excluded_output_path}")
    print(f"7. Cause Code 筛选摘要: {summary_output_path}")
    print("=" * 50)

    print("\n筛选后前10大 Cause Code：")
    print(df_unique["cause_code_norm"].value_counts().head(10))

    print("\n筛选后前10大官方分组：")
    print(df_unique["cause_group_official"].value_counts().head(10))

    return df_unique


if __name__ == "__main__":
    ORIGINAL_CSV = r"D:\Pyprogramme\STST2603\data\ukpn-iis.csv"

    if os.path.exists(ORIGINAL_CSV):
        clean_df = generate_weather_fetch_list_strict(
            input_path=ORIGINAL_CSV,
            output_path=r"D:\Pyprogramme\STST2603\data\new\unplanned_incidents_clean_2.csv",
            excluded_output_path=r"D:\Pyprogramme\STST2603\data\new\excluded_incidents_audit.csv",
            summary_output_path=r"D:\Pyprogramme\STST2603\data\new\cause_code_screening_summary.csv",
        )
    else:
        print(f"错误：未能在指定路径找到文件 {ORIGINAL_CSV}")