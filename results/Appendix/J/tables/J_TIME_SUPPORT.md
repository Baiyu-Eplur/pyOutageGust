# J_TIME_SUPPORT

需求 J06；J.5。八任务开发/评估率、平均偏差、Brier/BSS与支持表。

分析单位：LAD-day。样本：开发2021-04-01–2023-09-29；评估2023-09-30–2024-03-31；同111LAD。

模型：开发期背景率lognormal冻结；开发阳性率常数基准。指标：Brier/BSS为比例；平均偏差另列概率百分点。

验证：只读已有结果；本轮不拟合。

回顾性，评估期此前参与探索；事后proxy构造下跨期迁移，不是提前预警。开发期参数不可替换正文全期参数。

| period | n | mean | sd | min | p05 | p25 | p50 | p75 | p95 | max | below_development_range | above_development_range | outside_development_range | outside_fraction | unit | definition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | 101232 | 8.492389781 | 3.322776861 | 1.953195817 | 4.103636077 | 6.06904985 | 7.922961141 | 10.38667116 | 14.65742032 | 26.79445581 | 0 | 0 | 0 | 0 | m/s | existing incident-anchor interpolated gust proxy |
| evaluation | 20424 | 9.510680409 | 3.609954668 | 2.845693473 | 4.584401864 | 6.504250983 | 9.116513073 | 11.58340166 | 16.0015049 | 23.31562281 | 0 | 0 | 0 | 0 | m/s | existing incident-anchor interpolated gust proxy |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
