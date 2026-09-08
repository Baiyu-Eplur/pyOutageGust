"""
filter_v2.py —— 工作命令 #7 新版事件合并逻辑

⚠️ 重要状态声明（写在文件最前面，任何后续使用者必须先看到）：
本脚本已完整编写并可读性自查，但【尚未在真实原始数据上执行过】——
`D:\\Pyprogramme\\STST2603\\data\\ukpn-iis.csv`（44MB）在本次工作命令 #7 执行过程中，
经 `device_stage_files` 第三次尝试传输仍失败（错误信息与前两次相同：generic "upload failed"，
工具未返回更细节的诊断信息），本次会话没有 device_bash 权限可对设备上的文件做分块读取，
因此本脚本目前只是"设计完成、逻辑封装完成"的代码，还没有被真正跑过一次、也没有做过
任何实际数值层面的自检（比如"customers_v2 求和是否溢出""duration_A 分母是否会出现0但没
被正确标记"等，这些只能在真实数据上跑过一次才能确认）。
在原始文件可读取问题解决之前，不应假设本脚本已验证正确，只应视为"待验证的候选实现"。
详见 `claude_branch/results/pipeline_v2_output/00_原始字段验证.md` 关于该阻塞点的完整说明。

本脚本相对原版 filter.py 的改动范围（其余函数逐字保留，未改动）：
1. normalize_cause_code() / classify_cause_code()：逐字保留，不做任何改动。
2. generate_weather_fetch_list_strict() → 替换为 generate_event_level_table()：
   - 规则1：不再用 cause_group_official 过滤行，只保留分类标签列，供后续按需筛选。
   - 规则2：用"按 Incident Reference 分组聚合"替代原来的
     drop_duplicates(subset=[incident_col], keep="first")：
       customers_v2  = 该事件所有 Re-interruption Stage != 'Y' 的阶段的
                       Number of Customers Restored 之和（对应官方 CIt 逻辑）
       duration_A    = Σ(该阶段客户数 × 该阶段时长) / Σ(该阶段客户数)，阶段范围包含
                       Re-interruption='Y' 的阶段（对应官方 CMLt 逻辑，量纲：小时）
       duration_B    = 该事件全部阶段中最晚 End − 最早 Start（量纲：小时，"Incident
                       completion" 概念的简化实现，未实现官方 3/18 小时完成判定阈值，
                       原因见文件内 IMPLEMENTATION NOTE）
       边界情况标记   = all_stages_are_reinterruption（该事件全部阶段都标记为
                       Re-interruption='Y'，导致 customers_v2 的求和范围为空集）

官方依据（原样引用自工作命令 #7 正文 0.2 节，本脚本不重新查证 Ofgem 原始 PDF）：
  CIt  = Σᵢ Σᵣ NDrit，NDrit = "Number of Customers interrupted in Restoration Stage r
         of...incident i...excluding re-interruptions to supply"
  CMLt = Σᵢ Σᵣ NNrit × (TRrit − TIrit)，NNrit = "...including re-interruptions to supply"
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


def normalize_cause_code(x):
    """
    将 Cause Code 标准化为官方风格：
    - 数字码补零成两位，如 1 -> '01'
    - 字母数字码保留，如 A1, A2
    - D, X 保留

    （与原版 filter.py 逐字相同，未做任何改动）
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

    （与原版 filter.py 逐字相同，未做任何改动——这是 Step 6 综合结论里
    明确要求"保留分类标签、只是不再用它过滤行"的那部分逻辑）
    """

    # 1) 天气 / 自然暴露
    weather_natural = {
        "01", "02", "03", "04", "05", "06", "07", "10", "18",
        "21", "23", "24", "25", "30", "32", "33",
    }

    # 2) 设备 / 网络内部技术故障
    technical_asset = {
        "14", "15", "16", "17", "19", "22", "26", "64", "67",
        "70", "71", "72", "73", "76", "77", "78", "90", "A1", "A2",
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
        "74", "80", "85", "86", "87", "88", "89",
    }

    # 6) 非明确物理故障 / 不可用
    non_fault_or_unknown = {
        "75", "97", "98", "99", "D", "X",
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


# ============================================================
# 规则1/规则2 的关键实现常量（明确写出、便于复核，而不是散落在函数内部的魔法值）
# ============================================================

# Re-interruption Stage 字段被视为"确实是重复中断、customers_v2 求和时应排除"的取值。
# 原始字段确切名为 "Re-interruption Stage"（经 codex 的 audit_reinterruption_stage.py /
# audit_step0e/canonicalise_stage_data.py 两个独立脚本核实，均直接读取原始
# data/ukpn-iis.csv 得到同一字段名，见 00_原始字段验证.md）。
# 已知取值分布（同样来自上述脚本对原始 237,901 行的实际统计，非猜测）：
#   N: 217,276 行 (91.33%)——不是重复中断
#   Y: 20,525 行 (8.63%)——是重复中断
#   0: 98 行 (0.04%)——罕见旧式代码，仅出现在 RIIO-ED1 时期
#   1: 2 行 (0.0008%)——同上，极罕见
# ⚠️ '0'/'1' 这两个旧式取值的业务含义未经官方文档确认（codex 独立审计
# audit_step0b/00b_raw_stage_audit_report.md 的 D3/D9 决策门同样标注为
# "尚需人工确认"）。本脚本默认将其视为"非重复中断"（与 'N' 同等对待，计入
# customers_v2 求和），因为按官方转述"排除重复中断"的字面意思，只有明确标记为
# 重复中断（'Y'）的阶段才应被排除；但这是一个需要人工确认的假设，不是确凿依据，
# 已在此处集中列出常量，任何人复核/调整时只需改这一个集合，不需要改动函数逻辑。
REINTERRUPTION_EXCLUDE_VALUES = {"Y"}


def generate_event_level_table(
    input_path,
    output_path="unplanned_incidents_event_level_v2.csv",
    boundary_case_output_path="event_level_boundary_cases_v2.csv",
    cause_code_consistency_output_path="event_level_cause_code_consistency_v2.csv",
):
    """
    规则1 + 规则2 的完整实现。

    与原版 generate_weather_fetch_list_strict() 的关键区别：
    - 不再用 cause_group_official 过滤掉任何行（规则1）。
    - 不再用 drop_duplicates(keep="first") 简单去重，而是按 Incident Reference
      分组聚合出 customers_v2 / duration_A / duration_B 三个事件级变量，并生成
      all_stages_are_reinterruption 边界情况标记列（规则2）。
    - 唯一允许的行级筛选是纯技术性清洗（Start/End 时间解析失败），与原版一致。
    """
    print("--- 步骤 1: 读取原始全量数据 ---")
    try:
        df = pd.read_csv(input_path, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding="latin1", low_memory=False)

    df.columns = [c.strip() for c in df.columns]

    # 动态定位关键列（与原版做法一致，保留原有的健壮性）
    incident_col = [c for c in df.columns if "incident" in c.lower() and "ref" in c.lower()][0]
    cause_col = [c for c in df.columns if "cause" in c.lower() and "code" in c.lower()][0]

    # 精确匹配 Restoration Stage / Re-interruption Stage / customers / start / end
    # 字段名（已通过 codex 两个独立脚本的实际 pd.read_csv dtype 声明核实为确切字符串，
    # 非模糊 in 匹配——这是本脚本与原版 filter.py 最大的字段定位差异，原版从不需要
    # 这几个字段，本脚本的聚合逻辑必须精确取到它们）。
    required_exact_cols = [
        "Incident Reference",
        "Restoration Stage",
        "Re-interruption Stage",
        "Start Date and Time",
        "End Date and Time",
        "Number of Customers Restored",
    ]
    missing_exact = [c for c in required_exact_cols if c not in df.columns]
    if missing_exact:
        raise KeyError(
            f"以下字段未在原始数据里按预期的精确名称找到，聚合逻辑无法继续："
            f"{missing_exact}。请先核对原始文件表头是否与预期一致（预期字段名见"
            f"00_原始字段验证.md），不要在字段名不确定的情况下继续跑聚合。"
        )

    initial_count = len(df)
    print(f"成功加载数据。初始总记录数: {initial_count:,} 行")
    print(f"识别到事故列: {incident_col}")
    print(f"识别到原因列: {cause_col}")

    # 标准化 Cause Code（保留分类标签，规则1：不再用它过滤行）
    df["cause_code_norm"] = df[cause_col].apply(normalize_cause_code)
    df["cause_group_official"] = df["cause_code_norm"].apply(classify_cause_code)

    print("\n--- 步骤 2: 官方 Cause Code 分组统计（仅统计，不筛选）---")
    print(df["cause_group_official"].value_counts(dropna=False))

    # ------------------------------------------------------------
    # 纯技术性清洗：Start/End 时间解析失败的行无法参与任何时长计算，
    # 予以剔除（与原版 main1.py 的 dropna(clean_start/lat/lon) 精神一致，
    # 不是分析假设，是数据能否进入后续处理的技术前提）。
    # ------------------------------------------------------------
    df["_start_dt"] = pd.to_datetime(df["Start Date and Time"], errors="coerce", utc=True)
    df["_end_dt"] = pd.to_datetime(df["End Date and Time"], errors="coerce", utc=True)
    n_before_time_clean = len(df)
    df = df[df["_start_dt"].notna() & df["_end_dt"].notna()].copy()
    n_after_time_clean = len(df)
    print(
        f"\n技术性时间清洗：剔除 Start/End 无法解析的行 "
        f"{n_before_time_clean - n_after_time_clean:,} 条，剩余 {n_after_time_clean:,} 条"
    )

    # 阶段级时长（小时），负值（End < Start）视为缺失，在聚合前处理，
    # 不留到聚合完成之后再处理（命令原文明确要求）。
    df["_stage_duration_hours"] = (df["_end_dt"] - df["_start_dt"]).dt.total_seconds() / 3600.0
    df.loc[df["_stage_duration_hours"] < 0, "_stage_duration_hours"] = np.nan

    # 客户数数值化（原始为字符串，可能含千分位逗号等格式问题）
    df["_customers_numeric"] = pd.to_numeric(
        df["Number of Customers Restored"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )

    # 是否为"应排除的重复中断"阶段
    df["_is_excluded_reinterruption"] = df["Re-interruption Stage"].isin(REINTERRUPTION_EXCLUDE_VALUES)

    # 稳定排序，确定"代表行"（该事件时间最早的一条阶段记录，用于承载其余列）
    df = df.sort_values([incident_col, "_start_dt"], kind="stable")

    print("\n--- 步骤 3: 按 Incident Reference 分组聚合（规则2核心）---")

    grouped = df.groupby(incident_col, dropna=False)

    # --- customers_v2：排除重复中断阶段后求和；若全部阶段都是重复中断，求和范围为空 ---
    def _customers_v2(g):
        eligible = g.loc[~g["_is_excluded_reinterruption"], "_customers_numeric"]
        if len(eligible) == 0:
            return np.nan
        return eligible.sum(skipna=True)

    customers_v2 = grouped.apply(_customers_v2)

    # --- 边界情况标记：该事件全部阶段都标记为 Re-interruption='Y' ---
    all_stages_are_reinterruption = grouped["_is_excluded_reinterruption"].agg(
        lambda s: bool(s.all()) and len(s) > 0
    )

    # --- duration_A：客户数加权平均时长（含重复中断阶段），Σ(NNrit×时长)/Σ(NNrit) ---
    def _duration_a(g):
        w = g["_customers_numeric"]
        t = g["_stage_duration_hours"]
        valid = w.notna() & t.notna()
        if valid.sum() == 0:
            return np.nan
        denom = w[valid].sum()
        if denom == 0 or pd.isna(denom):
            return np.nan
        return (w[valid] * t[valid]).sum() / denom

    duration_a = grouped.apply(_duration_a)

    # --- duration_B：事件总跨度 = 全部阶段最晚 End − 最早 Start（小时）---
    # IMPLEMENTATION NOTE：官方"Incident completion"概念区分未使用临时供电（3小时规则）
    # 与使用临时供电（18小时规则），需要一个"是否使用临时供电"的字段才能精确实现。
    # 经 Step 1 字段核实，原始数据中未确认存在这样一个可直接使用的字段（codex 的
    # audit_step0d/00d_three_minute_rule_audit.csv 对"3分钟规则"做过审计，但那是
    # 阶段级最短记录时长的技术判定，不是"是否使用临时供电"这个业务字段）。命令原文
    # 明确授权在找不到该字段或实现复杂度过高时，先用最简单的"最晚End−最早Start"，
    # 并在文档里注明这是已知局限——此处即按此执行，未强行猜测临时供电字段。
    latest_end = grouped["_end_dt"].max()
    earliest_start = grouped["_start_dt"].min()
    duration_b = (latest_end - earliest_start).dt.total_seconds() / 3600.0

    # --- 代表行：该事件时间最早的一条阶段记录（延续原版 keep="first" 的精神，
    #     只是 customers/duration 不再来自这一条，而是来自上面的聚合计算）---
    representative = df.drop_duplicates(subset=[incident_col], keep="first").copy()
    representative = representative.set_index(incident_col)

    # 组装最终事件级表：代表行的全部列 + 新增的四个聚合列
    event_table = representative.copy()
    event_table["customers_v2"] = customers_v2
    event_table["duration_A_customer_weighted_hours"] = duration_a
    event_table["duration_B_full_span_hours"] = duration_b
    event_table["all_stages_are_reinterruption"] = all_stages_are_reinterruption.reindex(event_table.index)
    event_table["stage_row_count"] = grouped.size().reindex(event_table.index)

    event_table = event_table.reset_index()

    # 清理内部临时列（保留 Restoration Stage / Re-interruption Stage 等原始列不变，
    # 只删除本脚本自己新增的下划线开头的内部计算列）
    internal_cols = [c for c in event_table.columns if c.startswith("_")]
    event_table = event_table.drop(columns=internal_cols)

    # ------------------------------------------------------------
    # 边界情况审计表：全部阶段都是 Re-interruption='Y' 的事件单独导出
    # （命令原文明确要求"不能静默输出0或报错崩溃，需要在文档里报告这类事件的数量"）
    # ------------------------------------------------------------
    boundary_cases = event_table[event_table["all_stages_are_reinterruption"] == True].copy()
    boundary_cases.to_csv(boundary_case_output_path, index=False)
    print(
        f"\n边界情况（全部阶段均为 Re-interruption='Y'，customers_v2 无法计算）："
        f"{len(boundary_cases):,} 个事件，已单独导出到 {boundary_case_output_path}"
    )

    # ------------------------------------------------------------
    # Cause Code 一致性审计：同一事件内不同阶段记录的 Cause Code 是否一致
    # ------------------------------------------------------------
    cause_nunique = grouped["cause_code_norm"].nunique(dropna=False)
    cause_inconsistent_incidents = cause_nunique[cause_nunique > 1]
    cause_consistency_df = pd.DataFrame({
        incident_col: cause_nunique.index,
        "distinct_cause_code_count": cause_nunique.values,
    })
    cause_consistency_df.to_csv(cause_code_consistency_output_path, index=False)
    print(
        f"\nCause Code 一致性审计：{len(cause_inconsistent_incidents):,} 个事件在其内部"
        f"不同阶段记录之间 Cause Code 不一致（共 {event_table[incident_col].nunique():,} 个事件），"
        f"已导出到 {cause_code_consistency_output_path}"
    )

    # 保存主输出
    event_table.to_csv(output_path, index=False)

    final_count = len(event_table)
    print("\n" + "=" * 50)
    print("【事件级聚合完成报告（规则1+规则2）】")
    print(f"1. 原始记录总数: {initial_count:,}")
    print(f"2. 技术性时间清洗后剩余记录: {n_after_time_clean:,}")
    print(f"3. 聚合后事件总数（未按 Cause Code 筛选）: {final_count:,}")
    print(f"4. 边界情况（全阶段重复中断）事件数: {len(boundary_cases):,}")
    print(f"5. Cause Code 内部不一致事件数: {len(cause_inconsistent_incidents):,}")
    print(f"6. 主输出文件: {output_path}")
    print("=" * 50)

    return event_table


if __name__ == "__main__":
    ORIGINAL_CSV = r"D:\Pyprogramme\STST2603\data\ukpn-iis.csv"

    # ⚠️ 本脚本尚未执行过——见文件顶部状态声明。以下 __main__ 块保留原版风格
    # （检查文件存在性再运行），但输出路径改为 claude_branch/results/pipeline_v2_output/，
    # 不写入 data/new/（硬性约束2：新数据产出只能放 claude_branch/ 之内）。
    if os.path.exists(ORIGINAL_CSV):
        event_df = generate_event_level_table(
            input_path=ORIGINAL_CSV,
            output_path=r"D:\Pyprogramme\STST2603\claude_branch\results\pipeline_v2_output\unplanned_incidents_event_level_v2.csv",
            boundary_case_output_path=r"D:\Pyprogramme\STST2603\claude_branch\results\pipeline_v2_output\event_level_boundary_cases_v2.csv",
            cause_code_consistency_output_path=r"D:\Pyprogramme\STST2603\claude_branch\results\pipeline_v2_output\event_level_cause_code_consistency_v2.csv",
        )
    else:
        print(f"错误：未能在指定路径找到文件 {ORIGINAL_CSV}")
