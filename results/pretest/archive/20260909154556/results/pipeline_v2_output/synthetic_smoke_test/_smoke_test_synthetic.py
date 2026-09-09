"""
仅用于验证 filter_v2.py 的聚合函数逻辑是否按预期工作的合成数据自测——
不涉及任何真实原始数据。构造数据取自 audit_reinterruption_stage 输出里已经
公开的 anonymous_reinterruption_sequences.csv 匿名示例（CASE_03/10/13），
补充构造一个单阶段对照事件。跑通即说明代码逻辑本身没有明显 bug，
但不代表已经在真实数据上验证过（真实数据验证仍被 Step 0 的阻塞点挡住）。
"""
import pandas as pd
import sys
sys.path.insert(0, ".")
from filter_v2 import generate_event_level_table

rows = [
    # CASE_03：6个阶段，其中 stage4 标记 Y（应从 customers_v2 中排除）
    ("INC_A", "2024-03-30T18:22:00", "2024-03-30T19:04:00", 1, "N", 17, "71"),
    ("INC_A", "2024-03-30T18:26:00", "2024-03-30T19:20:00", 2, "N", 1, "71"),
    ("INC_A", "2024-03-30T18:22:00", "2024-03-30T22:55:00", 3, "N", 16, "71"),
    ("INC_A", "2024-03-30T21:43:00", "2024-03-30T22:55:00", 4, "Y", 18, "71"),
    ("INC_A", "2024-03-30T21:43:00", "2024-03-30T22:55:00", 5, "N", 16, "71"),
    ("INC_A", "2024-03-30T18:22:00", "2024-03-30T23:03:00", 6, "N", 1, "71"),
    # CASE_13：4个阶段，含旧式 0/1 legacy 代码（非 Y/N）
    ("INC_B", "2022-09-09T15:55:00", "2022-09-09T16:22:00", 1, "0", 41, "06"),
    ("INC_B", "2022-09-09T16:27:00", "2022-09-09T16:38:00", 2, "1", 41, "06"),
    ("INC_B", "2022-09-09T16:27:00", "2022-09-09T16:38:00", 3, "0", 83, "06"),
    ("INC_B", "2022-09-09T16:38:00", "2022-09-09T21:05:00", 4, "0", 12, "06"),
    # 单阶段对照事件（无重复中断）
    ("INC_C", "2023-01-01T00:00:00", "2023-01-01T05:00:00", 1, "N", 250, "71"),
    # 边界情况：全部阶段都标记 Y
    ("INC_D", "2023-05-01T00:00:00", "2023-05-01T01:00:00", 1, "Y", 30, "71"),
    ("INC_D", "2023-05-01T01:30:00", "2023-05-01T02:00:00", 2, "Y", 10, "71"),
]

df = pd.DataFrame(rows, columns=[
    "Incident Reference", "Start Date and Time", "End Date and Time",
    "Restoration Stage", "Re-interruption Stage", "Number of Customers Restored",
    "Cause Code",
])
df.to_csv("_synthetic_raw.csv", index=False)

result = generate_event_level_table(
    input_path="_synthetic_raw.csv",
    output_path="_synthetic_event_level.csv",
    boundary_case_output_path="_synthetic_boundary.csv",
    cause_code_consistency_output_path="_synthetic_cause_consistency.csv",
)

print("\n\n===== 核对结果 =====")
cols = ["Incident Reference", "customers_v2", "duration_A_customer_weighted_hours",
        "duration_B_full_span_hours", "all_stages_are_reinterruption", "stage_row_count"]
print(result[cols].to_string(index=False))

# 手工核算 INC_A 的 customers_v2 期望值：排除 stage4(Y,18)，其余 17+1+16+16+1=51
expected_customers_A = 17 + 1 + 16 + 16 + 1
actual_customers_A = result.loc[result["Incident Reference"] == "INC_A", "customers_v2"].iloc[0]
assert actual_customers_A == expected_customers_A, f"INC_A customers_v2 不符: 期望{expected_customers_A}, 实际{actual_customers_A}"
print(f"\nINC_A customers_v2 手工核算通过：期望{expected_customers_A}, 实际{actual_customers_A}")

# INC_D 应被标记为 all_stages_are_reinterruption=True，customers_v2 应为 NaN
row_d = result.loc[result["Incident Reference"] == "INC_D"].iloc[0]
assert row_d["all_stages_are_reinterruption"] == True
assert pd.isna(row_d["customers_v2"])
print("INC_D 边界情况标记与 customers_v2=NaN 核算通过")

print("\n全部自测断言通过（合成数据，非真实数据）。")
