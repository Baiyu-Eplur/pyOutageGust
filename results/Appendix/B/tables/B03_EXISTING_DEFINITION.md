# B03_EXISTING_DEFINITION

需求 B03；B.1。第一阶段对完整事件的已有比较。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

仅保存既有文字证据及其历史样本说明；不把旧聚合均值直接当作当前E0重新计算结果。

| source_paragraph | existing_text |
| --- | --- |
| P017 | B.1 Comparison against the earliest-stage convention |
| P018 | Within the final analysis sample (n = 60,437), the mean of affected customers computed by aggregating across stages, following Equation 1, is 93.02. The mean computed using only the customer count reported in the earliest stage of each incident, the convention used when an incident is treated as equivalent to its first recorded stage, is 47.13. The two figures differ by a factor of 1.97 within the same sample. |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
