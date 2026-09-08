# R03 输入接收与定向对账

基于已冻结 R02 主表及其可读报告，本轮没有重跑天气扫描或 H0 拟合。原 v9 已恢复，实际新入口是 R03/src/producer.py::step0_build_sample/step2_build_folds，经 R03/cli.py 运行。全部项目代码参考来自本地冻结副本，不导入原生产者。

135,025 个事件；主表 SHA256 `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`。两未决 ID 仍保留且不纳入主原因候选；候选身份如下。

| sample | H0 | R02 | common | enter | exit | v3_only |
| --- | --- | --- | --- | --- | --- | --- |
| main_E0 | 60437 | 60436 | 60436 | 0 | 1 | 0 |
| main_R0c | 59834 | 60436 | 59834 | 602 | 0 | 0 |
| weather_E0 | 9857 | 9857 | 9857 | 0 | 0 | 0 |
| weather_R0c | 9758 | 9857 | 9758 | 99 | 0 | 0 |

602/99 的互斥归因采用固定顺序：天气数值资格→年度人口→原因→目标有效性→旧 H0 尾部限制→其他；前项命中后不再重复计入后项。旧 cap 是 H0 描述身份，不是新拟合阈值。

| sample | exclusive_reason_in_order | events |
| --- | --- | --- |
| main_R0c | 旧四天气不完整→新可用 | 0 |
| main_R0c | 旧年份人口缺失→新完整 | 0 |
| main_R0c | 旧原因不符→新共识符合 | 0 |
| main_R0c | 旧目标无效→新有效 | 0 |
| main_R0c | 旧H0截尾→完整有效尾部 | 602 |
| main_R0c | 其他待解释 | 0 |
| weather_R0c | 旧四天气不完整→新可用 | 0 |
| weather_R0c | 旧年份人口缺失→新完整 | 0 |
| weather_R0c | 旧原因不符→新共识符合 | 0 |
| weather_R0c | 旧目标无效→新有效 | 0 |
| weather_R0c | 旧H0截尾→完整有效尾部 | 99 |
| weather_R0c | 其他待解释 | 0 |

可重叠边际标志不能相加：

| sample | overlapping_flag | events |
| --- | --- | --- |
| main_R0c | 时间改变 | 85 |
| main_R0c | 任一天气变化 | 85 |
| main_R0c | R1兼容阈值也会排除 | 602 |
| weather_R0c | 时间改变 | 14 |
| weather_R0c | 任一天气变化 | 14 |
| weather_R0c | R1兼容阈值也会排除 | 99 |

R1_compat 是成员诊断：main_R0c=59,832、weather_R0c=9,758，无 R1 模型。主阈值由 192.083333 变为 191.913333 h 另影响两条旧成员，详见冻结 R02 表。

UTC/London 全事件日期/研究期/时期差异为 1,845/2/2；主候选为 768/0/0，天气候选为 105/0/0。风暴日期来源是冻结 R01 与旧 step10 约定；UTC 为明确分析解释，源业务时区未确证；结束日期包含全天，实际使用次日零时开区间，不随结果调整。

| window | date_start | date_end_inclusive | UTC_events | London_events | membership_difference | main_candidates_UTC | weather_candidates_UTC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Arwen | 2021-11-25 | 2021-11-28 | 574 | 574 | 0 | 270 | 81 |
| Dudley | 2022-02-15 | 2022-02-17 | 616 | 616 | 0 | 291 | 121 |
| Eunice | 2022-02-17 | 2022-02-19 | 2291 | 2291 | 0 | 1659 | 1398 |
| Franklin | 2022-02-19 | 2022-02-22 | 1631 | 1631 | 0 | 1132 | 884 |
| Babet | 2023-10-17 | 2023-10-22 | 1089 | 1087 | 6 | 509 | 80 |
| Ciaran | 2023-10-31 | 2023-11-03 | 990 | 990 | 0 | 576 | 206 |
| Henk | 2024-01-01 | 2024-01-03 | 811 | 811 | 0 | 494 | 336 |

| UTC_UNIQUE_ANY | UTC_overlap_events_ge2 | UTC_summed_window_memberships | UTC_overlap_extra_memberships | London_UNIQUE_ANY | London_overlap_events_ge2 | UTC_London_union_difference |
| --- | --- | --- | --- | --- | --- | --- |
| 7300 | 702 | 8002 | 702 | 7298 | 702 | 6 |

天气事件数：

| weather_cache_status | weather_numeric_available | events |
| --- | --- | --- |
| missing_file | False | 8236 |
| query_ineligible | False | 5611 |
| readable | True | 121178 |

129,414 可查询事件对应 82,621 键、122,948 键×小时；74,896 可读文件、7,725 缺文件键；75,983 是整个目录文件数。121,178 四值完整事件全部缓存小时/窗口通过；可读但数值/小时/窗口失败实数0；不可查询5,611，缺文件事件8,236，其最早v3数值也缺。四候选v3-only实数0；历史model仍未决，不将数据值通过等同来源确定。

区域：113 个非空 LAD21 代码中 113 个出现在 LAD23 人口长表，候选涉及 111 个代码。同码只确认连接覆盖，不证明边界相同。本地 DBF/lookup 元数据见 local_geography_metadata.json，未发现可明确验证 2021→2023 边界等价的来源；没有已证实需改值的错误，保留全部相关代码的未决标志。5,762缺LAD和其中151可用坐标但未新增匹配沿用R02，不强行补区。

Buck：工作簿 localincomedeprivationdata.xlsx SHA `6eb516a87654078ee69d4df55c8bc749b5da5de117f996f262c0c762bc20b38f`，Rankings for all indicators 的 Income deprivation rate、Deprivation gap (percentage points)、Moran's I；比例存储不乘100。普通LAD gap为LSOA rate极差，Buck四旧码简单均值保留 .06325/.1875/.30 及proxy。主候选各1,151、天气各293。原脚本真实路径及SHA已复制登记于 frozen/PROJECT_SOURCE_MANIFEST.json，详证来自 frozen/evidence/buckinghamshire_lineage.json。LSOA重建不在本轮。
