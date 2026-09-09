"""
data_arrange_v2.py —— 工作命令 #7 相对原版 data_arrange.py 的改动说明

⚠️ 状态声明：与 filter_v2.py 一样，本脚本尚未在真实数据上执行过（下游链路本命令
本就不要求跑通，见 03_下游重跑规模评估.md）；这里只是把"Duration 计算方式需要
调整"这个已授权的改动范围（命令原文 硬性约束3："只修改本命令明确要求修改的部分
——Cause Code筛选步骤、事件合并聚合逻辑、duration计算"）落实成具体代码，供后续
真正跑通九步链路时使用。

与原版的唯一区别：
- 原版自己用 (End − Start) / 3600 重新计算一个单阶段 "Duration (hours)" 列。
  这个计算方式正是 command #6 已定位的问题所在（单阶段，不含跨阶段聚合/客户数加权）。
- 新版不再自己计算 Duration，而是直接透传 filter_v2.py 已经聚合好的
  duration_A_customer_weighted_hours / duration_B_full_span_hours 两列
  （这两列在事件级聚合阶段就已经产生，此处不应该也不需要重复计算或覆盖）。
- Hour / Month / Weekday / Daytime Indicator 四个周边时间变量的计算方式不变
  （依然从代表行的 Start Date and Time 派生，这部分逻辑本身没有问题，属于
  Step 6 复用地图里"应原样复用"的范围，只是被搬到这个新文件里延续使用）。
"""

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import pandas as pd

# ==============================
# File path（占位——本命令不要求真正跑通下游链路，实际路径待后续命令确认）
# ==============================
file_path = str(result_path('pipeline_v2_output/ukpn_master_v2_with_lad_features.csv'))

# ==============================
# Read CSV
# ==============================
df = pd.read_csv(read_input(file_path), low_memory=False)
df.columns = df.columns.str.strip()

# ==============================
# Column names
# ==============================
start_col = "Start Date and Time"
end_col = "End Date and Time"

# ==============================
# Datetime conversion (统一时区 + 去时区)——与原版逐字相同
# ==============================
df[start_col] = pd.to_datetime(df[start_col], errors="coerce", utc=True).dt.tz_convert(None)
df[end_col] = pd.to_datetime(df[end_col], errors="coerce", utc=True).dt.tz_convert(None)

# ==============================
# 计算变量（先不写入 df）
# ==============================

# 【改动点】不再自己计算 Duration (hours)——duration_A_customer_weighted_hours /
# duration_B_full_span_hours 两列已经在 filter_v2.py 的事件级聚合阶段产生，
# 此处只做透传检查（确认这两列确实存在，不重新计算、不覆盖）。
required_v2_duration_cols = ["duration_A_customer_weighted_hours", "duration_B_full_span_hours"]
missing = [c for c in required_v2_duration_cols if c not in df.columns]
if missing:
    raise KeyError(
        "预期的事件级 duration 列缺失：{}。这两列应该已经由 filter_v2.py 的"
        "事件级聚合产生并随后续 LAD/人口/GVA 合并步骤原样透传到这里——如果缺失，"
        "说明上游某一步不小心丢弃了这两列，需要回溯检查，不应该在这里重新用"
        "单阶段 (End-Start) 的方式重算一个新的 Duration 来替代。".format(missing)
    )

# Daytime Indicator（与原版逐字相同——基于代表行的 Start Date and Time，
# 这部分逻辑不受customers/duration改动影响，属于"应原样复用"范围）
start_hour = df[start_col].dt.hour
daytime = ((start_hour >= 6) & (start_hour < 18)).astype("Int64")

# 时间结构变量（与原版逐字相同）
hour = start_hour
month = df[start_col].dt.month
weekday = df[start_col].dt.weekday  # 0=Monday, 6=Sunday

# ==============================
# 一次性写入（避免 fragmentation）——不再包含 Duration (hours)，
# 该列已被 duration_A_customer_weighted_hours / duration_B_full_span_hours 取代
# ==============================
new_cols = pd.DataFrame({
    "Daytime Indicator": daytime,
    "Hour": hour,
    "Month": month,
    "Weekday": weekday
})

df = pd.concat([df, new_cols], axis=1)

# 👉 内存整理（关键，与原版相同）
df = df.copy()

# ==============================
# Save
# ==============================
output_path = str(result_path('pipeline_v2_output/ukpn_master_v2_final.csv'))
df.to_csv(output_path, index=False)

print("Finished.")
print("Added variables:")
print("- Daytime Indicator")
print("- Hour")
print("- Month")
print("- Weekday")
print("(Duration 不在此处计算——沿用 filter_v2.py 产出的 duration_A_customer_weighted_hours / duration_B_full_span_hours)")
