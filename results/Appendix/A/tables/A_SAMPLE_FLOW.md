# A_SAMPLE_FLOW

需求 A01；A.1–A.3。固定输入的样本量、原因计数和日期/LAD覆盖。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

恢复回归剔除零客户；不能把59834称为最终恢复样本。

| margin | scope | n | lads | start | end | zero_customers | source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 | saved_input | 60437 | 111 | 2021-04-01 | 2024-03-31 | 8979 | review_package/data/combined_E0_final.csv |
| E0 | final | 60437 | 111 | 2021-04-01 | 2024-03-31 | 8979 | review_package/data/combined_E0_final.csv |
| E0 | weather_final | 9857 | 105 | 2021-04-01 | 2024-03-31 | 572 | review_package/data/combined_E0_final.csv |
| R0c | saved_input | 59834 | 111 | 2021-04-01 | 2024-03-31 | 8661 | review_package/data/combined_R0c_final.csv |
| R0c | final | 51173 | 111 | 2021-04-01 | 2024-03-31 | 0 | review_package/data/combined_R0c_final.csv |
| R0c | weather_final | 9254 | 104 | 2021-04-01 | 2024-03-31 | 0 | review_package/data/combined_R0c_final.csv |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
