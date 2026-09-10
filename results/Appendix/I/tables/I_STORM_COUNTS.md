# I_STORM_COUNTS

需求 I01；I.1。固定窗口内当前样本计数及客户总量。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：各窗口事件数、客户总量；重叠窗口另提供去重并集。

验证：只读已有结果；本轮不拟合。

只汇总已有窗口；不把窗口描述当作预测验证。

| margin | storm | start | end | n | customers_sum | fraction_of_sample | overlap_rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 | Arwen | 2021-11-25 | 2021-11-28 | 270 | 25061 | 0.004467461985 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Dudley | 2022-02-15 | 2022-02-17 | 291 | 30092 | 0.004814931251 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Eunice | 2022-02-17 | 2022-02-19 | 1659 | 395470 | 0.02745007198 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Franklin | 2022-02-19 | 2022-02-22 | 1132 | 165963 | 0.01873024803 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Babet | 2023-10-17 | 2023-10-22 | 509 | 56696 | 0.00842199315 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Ciaran | 2023-10-31 | 2023-11-03 | 576 | 69801 | 0.009530585568 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | Henk | 2024-01-01 | 2024-01-03 | 494 | 68536 | 0.008173800817 | Inclusive windows; overlapping dates appear in both named rows |
| E0 | UNION_DEDUPLICATED |  |  | 4452 | 745372 | 0.07366348429 | Each incident counted once across all windows |
| R0c | Arwen | 2021-11-25 | 2021-11-28 | 242 | 25054 | 0.004729056338 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Dudley | 2022-02-15 | 2022-02-17 | 254 | 30090 | 0.004963555 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Eunice | 2022-02-17 | 2022-02-19 | 1518 | 394913 | 0.02966408067 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Franklin | 2022-02-19 | 2022-02-22 | 1064 | 165959 | 0.02079221464 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Babet | 2023-10-17 | 2023-10-22 | 449 | 56695 | 0.008774158248 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Ciaran | 2023-10-31 | 2023-11-03 | 466 | 69592 | 0.009106364685 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | Henk | 2024-01-01 | 2024-01-03 | 439 | 68199 | 0.008578742696 | Inclusive windows; overlapping dates appear in both named rows |
| R0c | UNION_DEDUPLICATED |  |  | 3990 | 744255 | 0.07797080492 | Each incident counted once across all windows |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
