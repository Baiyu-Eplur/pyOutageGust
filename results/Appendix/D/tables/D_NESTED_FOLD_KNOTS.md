# D_NESTED_FOLD_KNOTS

需求 D01；D.1–D.4。结点区间和训练折结点摘要。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：结点m/s、既有95%区间、已保存折结点。

验证：只读已有结果；本轮不拟合。

自由双结点500次与平台300次bootstrap分别标注；R0c自由分段59834含零客户，平台51173/9254为正客户；平台是候选，不是正文最终二次恢复模型的结点。

| margin | sample | n | form | fold_order | k1 | k2 |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | all | 60437 | unconstrained_two_hinge | 0 | 14 | 25 |
| E0 | all | 60437 | unconstrained_two_hinge | 1 | 13 | 29 |
| E0 | all | 60437 | unconstrained_two_hinge | 2 | 14 | 26 |
| E0 | all | 60437 | unconstrained_two_hinge | 3 | 14 | 25 |
| E0 | all | 60437 | unconstrained_two_hinge | 4 | 14 | 26 |
| R0c | all | 59834 | unconstrained_two_hinge | 0 | 15 | 20 |
| R0c | all | 59834 | unconstrained_two_hinge | 1 | 13 | 19 |
| R0c | all | 59834 | unconstrained_two_hinge | 2 | 13 | 20 |
| R0c | all | 59834 | unconstrained_two_hinge | 3 | 13 | 19 |
| R0c | all | 59834 | unconstrained_two_hinge | 4 | 8 | 18 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
