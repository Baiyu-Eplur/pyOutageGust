# J03_MATCHED_SAMPLE

需求 J03；J.2。已接受且两端优化有效的proxy/grid全八任务比较。

分析单位：LAD-day。样本：111 LAD × 1096 UTC days = 121656 rows; identical eight labels and saved five LAD folds。

模型：shared ddagg01-stable-v1 background-rate lognormal; PROXY versus GRID_MAX。指标：pooled OOF Brier/BSS; delta=PROXY-GRID_MAX; paired conditional 95% interval。

验证：48 components per source; training-only fits; fixed OOF paired LAD bootstrap B=1000 seed=20260909。

第一步仅J03；产物补齐后待研究负责人反馈分析，不自动科学关闭或进入F/GI/H。

| target | n | lads | days | events | rate |
| --- | --- | --- | --- | --- | --- |
| any_gt0 | 121656 | 111 | 1096 | 41926 | 0.3446274742 |
| any_gt5 | 121656 | 111 | 1096 | 20285 | 0.1667406458 |
| any_gt100 | 121656 | 111 | 1096 | 7369 | 0.06057243375 |
| any_gt1000 | 121656 | 111 | 1096 | 1020 | 0.008384296705 |
| wthr_gt0 | 121656 | 111 | 1096 | 6122 | 0.05032222003 |
| wthr_gt5 | 121656 | 111 | 1096 | 4394 | 0.03611823502 |
| wthr_gt100 | 121656 | 111 | 1096 | 2472 | 0.02031958966 |
| wthr_gt1000 | 121656 | 111 | 1096 | 312 | 0.002564608404 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
