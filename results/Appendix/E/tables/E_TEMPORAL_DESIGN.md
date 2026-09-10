# E_TEMPORAL_DESIGN

需求 E01；E.1–E.3。两期设计及已保存关键系数完整列出。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：系数、两维SE、p、n。

验证：只读已有结果；本轮不拟合。

两个时期分别拟合，规格沿用全期选择；不是开发期冻结预测。时期此前已用于探索。没有保存完整分期系数，不补训。

| period | start | end | fit | information_history | prediction_test |
| --- | --- | --- | --- | --- | --- |
| development | 2021-04-01 | 2023-09-29 | Each period fitted separately; full-period selected specification | Later period previously explored | No frozen development prediction in this incident analysis |
| confirmation | 2023-09-30 | 2024-03-31 | Each period fitted separately; full-period selected specification | Later period previously explored | No frozen development prediction in this incident analysis |
| combined | 2021-04-01 | 2024-03-31 | Each period fitted separately; full-period selected specification | Later period previously explored | No frozen development prediction in this incident analysis |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
