# R02 两个未决事件

| Incident Reference | source_rows | old_source_row | selected_source_row | old_time_utc | new_time_utc | max_stage_end_utc | cause_codes_all | customers_v2_event_excl_reinterruptions | duration_B_full_span_hours | weather_cache_status | weather_numeric_available | weather_validation_tier | old_population | population | candidate_main_E0 | E0_exclusion_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FREP-314454-J | 94432,147106 | 94432 | 147106 | 2023-04-05 08:23:00+00:00 | 2023-03-24 19:27:00+00:00 | 2023-04-05 10:50:00+00:00 | 71,87 | 2 | 279.3833333333333 | readable | True | strict_cache_checked | 136176.0 | 136176.0 | False | event_identity_unresolved;cause_not_main_or_unresolved |
| FREP-338321-Z | 89486,163320 | 89486 | 163320 | 2023-05-11 11:06:00+00:00 | 2022-11-04 16:44:00+00:00 | 2023-05-11 13:40:00+00:00 | 71,98 | 1 | 4508.933333333333 | missing_file | False | unavailable | 154321.0 | 151530.0 | False | event_identity_unresolved;cause_not_main_or_unresolved;weather_numeric_unavailable |

两事件完整阶段保留，未拆分、未作为完全重复行删除；主表公式值不等于已核实的连续失电或客户真值。FREP-338321-Z 的跨度为 ID 公式 4508.933333 h；FREP-314454-J 的两条 stage 1/同 unique_identifier 记录存在原因差异，C=2 仍是暂定 ID 加总。原因采用所有阶段共识，冲突进入 unresolved，按 R01 CAUSE_RULES 不进入主原因候选。原 MEI、监管年度、起止原字符串见 R02_ambiguous_source_stages.csv。
