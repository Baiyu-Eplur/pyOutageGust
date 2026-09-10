# B_REPRESENTATIVE_REPAIR

需求 B01；B.1–B.2。事件构造规则和代表行修复证据。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

C01清理计数为历史全事件构建范围，不能当作当前60437行回归样本。

| historical_construction_metric | value | scope |
| --- | --- | --- |
| n_total_incidents_v3 | 135025 | C01历史构建全事件范围，非最终回归n |
| n_stage_rows_unparseable_start_time | 0 | C01历史构建全事件范围，非最终回归n |
| n_incidents_unresolvable_no_parseable_start | 0 | C01历史构建全事件范围，非最终回归n |
| unresolvable_incident_ids | [] | C01历史构建全事件范围，非最终回归n |
| n_incidents_with_tie_at_min_start_time | 24893 | C01历史构建全事件范围，非最终回归n |
| n_incidents_compared | 135025 | C01历史构建全事件范围，非最终回归n |
| n_representative_row_changed | 12886 | C01历史构建全事件范围，非最终回归n |
| pct_representative_row_changed | 9.543417885576746 | C01历史构建全事件范围，非最终回归n |
| time_diff_hours_stats_changed_only.mean | 9.121835066480418 | C01历史构建全事件范围，非最终回归n |
| time_diff_hours_stats_changed_only.median | 3.7666666666666666 | C01历史构建全事件范围，非最终回归n |
| time_diff_hours_stats_changed_only.std | 52.855749901507224 | C01历史构建全事件范围，非最终回归n |
| time_diff_hours_stats_changed_only.min | 0.016666666666666666 | C01历史构建全事件范围，非最终回归n |
| time_diff_hours_stats_changed_only.max | 4506.366666666667 | C01历史构建全事件范围，非最终回归n |
| gust_0h_diff_stats_changed_only.n_valid | 11783 | C01历史构建全事件范围，非最终回归n |
| gust_0h_diff_stats_changed_only.mean | 0.25405244786599934 | C01历史构建全事件范围，非最终回归n |
| gust_0h_diff_stats_changed_only.median | 0.0 | C01历史构建全事件范围，非最终回归n |
| gust_0h_diff_stats_changed_only.std | 3.3082806854112317 | C01历史构建全事件范围，非最终回归n |
| gust_0h_diff_stats_changed_only.n_abs_gt_1ms | 6918 | C01历史构建全事件范围，非最终回归n |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
