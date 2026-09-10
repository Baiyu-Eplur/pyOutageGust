# J05_THRESHOLDS

需求 J05；J.4。八任务三模型指标、阈值、既有配对区间。

分析单位：LAD-day。样本：与DD-AGG01一致ERA5及固定LAD折。

模型：M0日最大；M1增加h=H/24；M2增加x=log1p(sum(max(g_h²-tau²,0))/(24tau²)))。指标：Brier/增益/BSS；tau(m/s)；既有区间。

验证：tau仅训练小时Q90；冻结折号；无本轮拟合。

H为超阈小时计数，不是最长连续时长；平方累计非结构损伤测量。保留稀有任务微小正向结果。

| scope | tau | training_rows | training_hours | training_lads | held_out_fold | method | quantile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full | 13.6 | 121656 | 2919744 | 111 | -1 | linear | 0.9 |
| fold_0 | 13.6 | 96448 | 2314752 | 88 | 0 | linear | 0.9 |
| fold_1 | 13.6 | 97544 | 2341056 | 89 | 1 | linear | 0.9 |
| fold_2 | 13.6 | 97544 | 2341056 | 89 | 2 | linear | 0.9 |
| fold_3 | 13.5 | 97544 | 2341056 | 89 | 3 | linear | 0.9 |
| fold_4 | 13.7 | 97544 | 2341056 | 89 | 4 | linear | 0.9 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
