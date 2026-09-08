# R05-4客户比较：记录选择与分母

只读原始阶段记录，逐事件保留原始SHA:1-based行号、最低数值阶段号、最早有效UTC时刻、各选中行的客户值与聚合C；大表本地Parquet，大小/SHA见checks/customer_comparator_audit.json。阶段编号先数值化，绝不字典序排序。

| population | n | minimum_stage_gt1_n | minimum_stage_gt1_pct | min_stage_tie_n | min_stage_tie_customer_conflict_n | earliest_time_tie_n | earliest_tie_customer_conflict_n | different_selected_record_n | different_selected_customer_n | R02_earliest_field_mismatch_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| event_master | 135025 | 14264 | 10.5639696 | 1 | 0 | 24893 | 21056 | 19701 | 17013 | 0 |
| main | 60436 | 8817 | 14.5889867 | 0 | 0 | 15249 | 13266 | 12823 | 11286 | 0 |
| weather | 9857 | 2593 | 26.3061784 | 0 | 0 | 3528 | 3411 | 2794 | 2668 | 0 |

## 各口径有效人口与共同人口

| population | measure | population_n | own_valid_n | own_missing_n | own_mean | common_valid_n | common_mean | ratio_aggregate_mean_to_measure_mean_common | ratio_aggregate_mean_to_measure_mean_own |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| event_master | aggregate_C | 135025 | 134956 | 69 | 75.5561887 | 134956 | 75.5561887 | 1 | 1 |
| event_master | min_stage_customers | 135025 | 135025 | 0 | 41.1769524 | 134956 | 41.1928036 | 1.83420846 | 1.83491454 |
| event_master | earliest_time_customers | 135025 | 135025 | 0 | 31.164177 | 134956 | 31.1749014 | 2.42362237 | 2.42445641 |
| main | aggregate_C | 60436 | 60436 | 0 | 93.0257297 | 60436 | 93.0257297 | 1 | 1 |
| main | min_stage_customers | 60436 | 60436 | 0 | 47.1283341 | 60436 | 47.1283341 | 1.97388114 | 1.97388114 |
| main | earliest_time_customers | 60436 | 60436 | 0 | 31.1219637 | 60436 | 31.1219637 | 2.98907005 | 2.98907005 |
| weather | aggregate_C | 9857 | 9857 | 0 | 191.961246 | 9857 | 191.961246 | 1 | 1 |
| weather | min_stage_customers | 9857 | 9857 | 0 | 101.310236 | 9857 | 101.310236 | 1.89478628 | 1.89478628 |
| weather | earliest_time_customers | 9857 | 9857 | 0 | 68.4548037 | 9857 | 68.4548037 | 2.80420417 | 2.80420417 |

原R04主组最低编号客户值逐ID比较：0个变化。最早时刻客户字段与R02持久source row和值全部一致。旧source_order没有进入排序是可维护性风险；当前明确以持久原行号作并列规则，打乱内存行序后选择不变。原阶段号并列是否构成结果影响以实测冲突计数为准，不能凭代码风险认定C/D聚合错误。

最早时刻并列若客户数不同，当前值是冻结规则选中行的客户数，不是该时刻全部客户之和，不可称true initial。均值之比不是逐事件比值的平均；逐事件分母为0的比值没有在这里被填0。各有效n和共同有效n已分列，不将缺失跳过隐藏在比值中。冻结事件C/D定义不变，未重拟合模型。
