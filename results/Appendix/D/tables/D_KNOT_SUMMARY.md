# D_KNOT_SUMMARY

需求 D01；D.1–D.4。结点区间和训练折结点摘要。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：结点m/s、既有95%区间、已保存折结点。

验证：只读已有结果；本轮不拟合。

自由双结点500次与平台300次bootstrap分别标注；R0c自由分段59834含零客户，平台51173/9254为正客户；平台是候选，不是正文最终二次恢复模型的结点。

| margin | sample | n | form | knot | estimate | profile_low | profile_high | bootstrap_B | bootstrap_low | bootstrap_median | bootstrap_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0 | all | 60437 | unconstrained_two_hinge | k1 | 14 | 13 | 14 | 500 | 13 | 14 | 15 |
| E0 | all | 60437 | unconstrained_two_hinge | k2 | 26 | 24 | 29 | 500 | 24 | 26 | 29.525 |
| R0c | all | 59834 | unconstrained_two_hinge | k1 | 14 | 8 | 15 | 500 | 8 | 13 | 16 |
| R0c | all | 59834 | unconstrained_two_hinge | k2 | 20 | 18 | 21 | 500 | 18 | 19 | 25 |
| E0 | all | 60437 | plateau | k1 | 14 | 13 | 14 | 300 | 13 | 14 | 15 |
| E0 | all | 60437 | plateau | k2 | 25 | 24 | 27 | 300 | 24 | 25 | 28 |
| E0 | weather | 9857 | plateau | k1 | 11 | 10 | 13 | 300 | 10 | 11 | 14 |
| E0 | weather | 9857 | plateau | k2 | 24 | 22 | 26 | 300 | 22 | 24 | 26 |
| R0c | all | 51173 | plateau | k1 | 17 | 16 | 18 | 300 | 16 | 17 | 20 |
| R0c | all | 51173 | plateau | k2 | 33 | 31 | 34 | 300 | 29 | 33 | 34 |
| R0c | weather | 9254 | plateau | k1 | 9 | 8 | 12 | 300 | 8 | 10 | 14 |
| R0c | weather | 9254 | plateau | k2 | 33 | 29 | 34 | 300 | 26 | 32 | 34 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
