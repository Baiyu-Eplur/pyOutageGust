# A_CAUSE_COUNTS

需求 A01；A.1–A.3。固定输入的样本量、原因计数和日期/LAD覆盖。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

恢复回归剔除零客户；不能把59834称为最终恢复样本。

| margin | scope | cause | n | share |
| --- | --- | --- | --- | --- |
| E0 | saved_input | technical_asset | 50580 | 0.8369045452 |
| E0 | saved_input | weather_natural | 9857 | 0.1630954548 |
| E0 | final | technical_asset | 50580 | 0.8369045452 |
| E0 | final | weather_natural | 9857 | 0.1630954548 |
| E0 | weather_final | weather_natural | 9857 | 1 |
| R0c | saved_input | technical_asset | 50028 | 0.8361132466 |
| R0c | saved_input | weather_natural | 9806 | 0.1638867534 |
| R0c | final | technical_asset | 41919 | 0.8191624489 |
| R0c | final | weather_natural | 9254 | 0.1808375511 |
| R0c | weather_final | weather_natural | 9254 | 1 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
