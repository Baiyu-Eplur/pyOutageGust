# G_FINAL_METRICS

需求 G02；G.1–G.2。最终全体和天气样本RMSE/R²摘要。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

全体final_summary保存RMSE，不保存完整最终OOF逐行值；天气pvo包含3候选均如实保留。

| margin | sample | n | spec | validation | log_RMSE | OOF_R2 | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 | all | 60437 | final | LAD-CV | 1.984757206 | NA | NA |
| E0 | all | 60437 | final | year-CV | 1.989730208 | NA | NA |
| R0c | all | 51173 | final | LAD-CV | 1.150252639 | NA | NA |
| R0c | all | 51173 | final | year-CV | 1.175262335 | NA | NA |
| E0 | weather | 9857 | paper quadratic | LAD-CV | 2.178406829 | 0.0350810895 | 0.8655021664 |
| E0 | weather | 9857 | ramp (11/24 m/s) | LAD-CV | 2.171394005 | 0.04128370894 | 0.8852147493 |
| E0 | weather | 9857 | final specification | LAD-CV | 2.166861857 | 0.04528161079 | 0.8940286594 |
| R0c | weather | 9254 | paper quadratic | LAD-CV | 1.250445938 | 0.2779720752 | 0.9817646668 |
| R0c | weather | 9254 | hinge (11 m/s) | LAD-CV | 1.249665858 | 0.2788726569 | 0.9815764446 |
| R0c | weather | 9254 | final specification | LAD-CV | 1.245920521 | 0.2831887189 | 0.979832935 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
