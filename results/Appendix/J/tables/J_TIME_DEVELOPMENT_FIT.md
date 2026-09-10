# J_TIME_DEVELOPMENT_FIT

需求 J06；J.5。八任务开发/评估率、平均偏差、Brier/BSS与支持表。

分析单位：LAD-day。样本：开发2021-04-01–2023-09-29；评估2023-09-30–2024-03-31；同111LAD。

模型：开发期背景率lognormal冻结；开发阳性率常数基准。指标：Brier/BSS为比例；平均偏差另列概率百分点。

验证：只读已有结果；本轮不拟合。

回顾性，评估期此前参与探索；事后proxy构造下跨期迁移，不是提前预警。开发期参数不可替换正文全期参数。

| start | method | success | iterations | message | theta | beta | p0 | nll | prediction_std | projected_gradient | boundary | n_unique_values | n | events | constant_nll | nll_improvement_vs_constant | valid | weak_identification | theta_outside_support | support_min | support_max | near_optimal_solutions | selection_reason | target | scope | development_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | L-BFGS-B | True | 18 | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 22.58515115 | 0.4201518545 | 0.3141990313 | 64209.24021 | 0.04320443856 | 3.0724203e-09 | NA | 101232 | 101232 | 34004 | 64614.31998 | 405.0797669 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | any_gt0 | development | 0.3359016912 |
| 11 | L-BFGS-B | True | 16 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 24.18843451 | 0.3547937454 | 0.1495747563 | 44480.37647 | 0.03727134786 | 2.963434506e-11 | NA | 101232 | 101232 | 16434 | 44899.40827 | 419.0318066 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | any_gt5 | development | 0.1623399716 |
| 2 | L-BFGS-B | True | 19 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 25.47329696 | 0.2878215442 | 0.0536898447 | 22453.24465 | 0.02776056879 | 4.078795281e-11 | NA | 101232 | 101232 | 6026 | 22844.32107 | 391.0764208 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | any_gt100 | development | 0.0595266319 |
| 1 | L-BFGS-B | True | 24 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 28.87667059 | 0.1948151128 | 0.007430799737 | 4651.728615 | 0.01066233524 | 1.763825567e-10 | NA | 101232 | 101232 | 826 | 4794.504229 | 142.7756139 | True | False | True | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | any_gt1000 | development | 0.008159475265 |
| 0 | L-BFGS-B | True | 29 | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 23.50903109 | 0.3351226554 | 0.03392057703 | 18403.12146 | 0.04447780689 | 1.030199231e-09 | NA | 101232 | 101232 | 4893 | 19596.67529 | 1193.553832 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | wthr_gt0 | development | 0.04833451873 |
| 0 | L-BFGS-B | True | 29 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 24.67125504 | 0.3229790302 | 0.02440854282 | 14247.76664 | 0.03635978368 | 4.152306183e-11 | NA | 101232 | 101232 | 3498 | 15208.40809 | 960.6414519 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | wthr_gt5 | development | 0.03455429113 |
| 1 | L-BFGS-B | True | 25 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 25.7759952 | 0.2888282761 | 0.0136583759 | 8951.249396 | 0.02760759354 | 7.549937507e-11 | NA | 101232 | 101232 | 1960 | 9672.064168 | 720.8147712 | True | False | False | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | wthr_gt100 | development | 0.01936146673 |
| 3 | L-BFGS-B | True | 23 | CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL | 30.49337856 | 0.2342635127 | 0.001572655747 | 1487.264587 | 0.009428554068 | 3.811988895e-11 | NA | 101232 | 101232 | 243 | 1708.51054 | 221.245953 | True | False | True | 1.953195817 | 26.79445581 | 13 | minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions | wthr_gt1000 | development | 0.002400426743 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
