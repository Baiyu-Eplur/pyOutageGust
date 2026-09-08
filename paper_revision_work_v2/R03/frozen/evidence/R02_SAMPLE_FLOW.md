# R02 修正输入候选样本流

这些是输入资格与成员，B1 模型和最终 OOF 均未产生。R02_candidate 采用合同的全有效尾部，不应用分组 p99；规则允许明确标记的 v3-only 条件来源，本轮实际为零。strict_cache_candidate 只表示缓存时刻/数值/24小时窗已核查，仍不能确认历史产品。R1_compat_candidate 只按旧首行原因和分别 p99 生成输入诊断成员，没有拟合或折分。

| sample | H0 | R02_candidate | common | enter | exit | strict_cache_candidate | conditional_v3_only | R1_compat_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main_E0 | 60437 | 60436 | 60436 | 0 | 1 | 60436 | 0 | 60436 |
| main_R0c | 59834 | 60436 | 59834 | 602 | 0 | 60436 | 0 | 59832 |
| weather_E0 | 9857 | 9857 | 9857 | 0 | 0 | 9857 | 0 | 9857 |
| weather_R0c | 9758 | 9857 | 9758 | 99 | 0 | 9857 | 0 | 9758 |

固定顺序排除如下，最后一行为主 R0c；倒数第二行为主 E0。天气子集从同一主总体派生。

| step | remaining | removed_this_step |
| --- | --- | --- |
| 全事件 | 135025 | 0 |
| 研究期UTC | 135025 | 0 |
| 身份无未决标志 | 135023 | 2 |
| 原因共识属于主组 | 66078 | 68945 |
| 四天气有限且gust/rain非负 | 62926 | 3152 |
| 区域与人口完整 | 60452 | 2474 |
| C有限且≥0 | 60436 | 16 |
| D有限且>0 | 60436 | 0 |

退出原因（互斥组合）及进入者标志见 R02_transition_reasons.csv；进入标志可重叠，不相加为人数。

| sample | transition | reason | events |
| --- | --- | --- | --- |
| main_E0 | exit | event_identity_unresolved;cause_not_main_or_unresolved;weather_numeric_unavailable | 1 |
| main_E0 | enter_multi_flag | old_four_weather_incomplete | 0 |
| main_E0 | enter_multi_flag | new_population_available_old_missing | 0 |
| main_E0 | enter_multi_flag | old_outside_UTC_study | 0 |
| main_E0 | enter_multi_flag | R1_compat_would_exclude | 0 |
| main_E0 | enter_multi_flag | new_time_changed | 0 |
| main_E0 | enter_multi_flag | new_weather_changed | 0 |
| main_R0c | enter_multi_flag | old_four_weather_incomplete | 0 |
| main_R0c | enter_multi_flag | new_population_available_old_missing | 0 |
| main_R0c | enter_multi_flag | old_outside_UTC_study | 0 |
| main_R0c | enter_multi_flag | R1_compat_would_exclude | 602 |
| main_R0c | enter_multi_flag | new_time_changed | 85 |
| main_R0c | enter_multi_flag | new_weather_changed | 85 |
| weather_E0 | enter_multi_flag | old_four_weather_incomplete | 0 |
| weather_E0 | enter_multi_flag | new_population_available_old_missing | 0 |
| weather_E0 | enter_multi_flag | old_outside_UTC_study | 0 |
| weather_E0 | enter_multi_flag | R1_compat_would_exclude | 0 |
| weather_E0 | enter_multi_flag | new_time_changed | 0 |
| weather_E0 | enter_multi_flag | new_weather_changed | 0 |
| weather_R0c | enter_multi_flag | old_four_weather_incomplete | 0 |
| weather_R0c | enter_multi_flag | new_population_available_old_missing | 0 |
| weather_R0c | enter_multi_flag | old_outside_UTC_study | 0 |
| weather_R0c | enter_multi_flag | R1_compat_would_exclude | 99 |
| weather_R0c | enter_multi_flag | new_time_changed | 14 |
| weather_R0c | enter_multi_flag | new_weather_changed | 14 |

缺首阶段质量标记：

| version | sample | N | min_stage_ge2 | tie_earliest | identity_unresolved | cross_study_recovery |
| --- | --- | --- | --- | --- | --- | --- |
| H0 | main_E0 | 60437 | 8817 | 15249 | 1 | 25 |
| R02_candidate | main_E0 | 60436 | 8817 | 15249 | 0 | 25 |
| H0 | main_R0c | 59834 | 8671 | 15148 | 0 | 16 |
| R02_candidate | main_R0c | 60436 | 8817 | 15249 | 0 | 25 |
| H0 | weather_E0 | 9857 | 2593 | 3528 | 0 | 0 |
| R02_candidate | weather_E0 | 9857 | 2593 | 3528 | 0 | 0 |
| H0 | weather_R0c | 9758 | 2578 | 3503 | 0 | 0 |
| R02_candidate | weather_R0c | 9857 | 2593 | 3528 | 0 | 0 |

Buckinghamshire 代理人数：

| sample | H0_Buck | R02_Buck | R02_Buck_strict |
| --- | --- | --- | --- |
| main_E0 | 1151 | 1151 | 1151 |
| main_R0c | 1146 | 1151 | 1151 |
| weather_E0 | 293 | 293 | 293 |
| weather_R0c | 292 | 293 | 293 |

R1 输入兼容诊断（仍不是 B1）：

| sample | H0 | R1_compat_input | common | enter | exit |
| --- | --- | --- | --- | --- | --- |
| main_E0 | 60437 | 60436 | 60436 | 0 | 1 |
| main_R0c | 59834 | 59832 | 59832 | 0 | 2 |
| weather_E0 | 9857 | 9857 | 9857 | 0 | 0 |
| weather_R0c | 9758 | 9758 | 9758 | 0 | 0 |

| Incident Reference | customers_v2_event_excl_reinterruptions | duration_B_full_span_hours | old_time_utc | new_time_utc | weather_numeric_available | event_identity_status | sample | transition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FREP-338321-Z | 1 | 4508.933333333333 | 2023-05-11 11:06:00+00:00 | 2022-11-04 16:44:00+00:00 | False | unresolved | main_E0 | exit |
| FREP-335700-J | 0 | 192.08333333333334 | 2024-01-03 14:40:00+00:00 | 2024-01-03 14:40:00+00:00 | True | record_id_consistent_not_business_certified | main_R0c | exit |
| FREP-338384-Z | 0 | 192.08333333333334 | 2022-11-03 22:17:00+00:00 | 2022-11-03 22:17:00+00:00 | True | record_id_consistent_not_business_certified | main_R0c | exit |

当前兼容主恢复 p99=191.913333333333 h（H0 为 192.083333333333 h），天气 p99=142.844666666667 h。主组极端事件失去最早天气后，重新计算旧式 p99 又使两条原 H0 恢复成员落到阈值外；这是保留旧缺陷的诊断结果，不用于裁剪 R02 全有效候选。
