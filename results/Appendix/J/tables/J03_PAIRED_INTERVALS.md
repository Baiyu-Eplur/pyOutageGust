# J03_PAIRED_INTERVALS

需求 J03；J.2。已接受且两端优化有效的proxy/grid全八任务比较。

分析单位：LAD-day。样本：111 LAD × 1096 UTC days = 121656 rows; identical eight labels and saved five LAD folds。

模型：shared ddagg01-stable-v1 background-rate lognormal; PROXY versus GRID_MAX。指标：pooled OOF Brier/BSS; delta=PROXY-GRID_MAX; paired conditional 95% interval。

验证：48 components per source; training-only fits; fixed OOF paired LAD bootstrap B=1000 seed=20260909。

第一步仅J03；产物补齐后待研究负责人反馈分析，不自动科学关闭或进入F/GI/H。

| candidate | target | valid_comparison | delta_brier_lo | delta_brier_hi | relative_gain_lo | relative_gain_hi | repeats | seed | relative_improvement_pct_lo | relative_improvement_pct_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GRID_MAX | any_gt0 | True | -0.0002247168483 | 0.0002877561366 | -0.00103326002 | 0.001266008704 | 1000 | 20260909 | -0.103326002 | 0.1266008704 |
| GRID_MAX | any_gt5 | True | -9.547211118e-05 | 0.0002304919267 | -0.0007142374377 | 0.001650765035 | 1000 | 20260909 | -0.07142374377 | 0.1650765035 |
| GRID_MAX | any_gt100 | True | -0.0001382097669 | 4.419958801e-05 | -0.002499646 | 0.000811730707 | 1000 | 20260909 | -0.2499646 | 0.0811730707 |
| GRID_MAX | any_gt1000 | True | -5.773325774e-05 | -1.145645435e-05 | -0.006878104847 | -0.001472029232 | 1000 | 20260909 | -0.6878104847 | -0.1472029232 |
| GRID_MAX | wthr_gt0 | True | -0.000172254872 | 0.0001608335638 | -0.004131456634 | 0.00356457052 | 1000 | 20260909 | -0.4131456634 | 0.356457052 |
| GRID_MAX | wthr_gt5 | True | -0.0001446123308 | 0.0001040676545 | -0.004600430483 | 0.002966623887 | 1000 | 20260909 | -0.4600430483 | 0.2966623887 |
| GRID_MAX | wthr_gt100 | True | -0.0001369352459 | 3.397174087e-05 | -0.007540755017 | 0.00176433978 | 1000 | 20260909 | -0.7540755017 | 0.176433978 |
| GRID_MAX | wthr_gt1000 | True | -4.90966738e-05 | -1.05613428e-05 | -0.01924114366 | -0.004738552821 | 1000 | 20260909 | -1.924114366 | -0.4738552821 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
