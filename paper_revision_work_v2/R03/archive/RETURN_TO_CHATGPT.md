> 隔离复核更新：原 v9 已恢复为 H0；当前修复入口为 `D:\Pyprogramme\STST2603\claude_branch\scripts\event_input_repair\r02_input_pipeline.py`。以下 R02 首次执行记录的数值保留，涉及旧入口改写/548 个未变文件的描述属于迁移前历史。当前为 549/549 旧文件一致；详见 reports/R02_ISOLATION_REVIEW.md。

# R02 返回摘要

已按指定文件完成 R02：规则明确（限代理口径）、代码已修、输入已重建、针对性检查通过；**模型尚未重估，文稿未修改，R03/V/W 未启动**。

237,901 阶段 → 135,025 唯一事件。UTC 代表时刻改变 12,886；天气小时改变 12,018；日期改变 2,802；年份/月分别改变 12/95；时期改变 1；任一天气值或缺失状态改变 11,227；原因组改变 2；人口改变 12。C/D 全事件一致（浮点容差内）。共同/进入/退出分开如下：

| sample | H0 | R02_candidate | common | enter | exit | strict_cache_candidate | conditional_v3_only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| main_E0 | 60437 | 60436 | 60436 | 0 | 1 | 60436 | 0 |
| main_R0c | 59834 | 60436 | 59834 | 602 | 0 | 60436 | 0 |
| weather_E0 | 9857 | 9857 | 9857 | 0 | 0 | 9857 | 0 |
| weather_R0c | 9758 | 9857 | 9758 | 99 | 0 | 9857 | 0 |

候选恢复总体保留全部有效 D，成员变化不能全部归因于时间修复。旧首行原因/独立 p99 的兼容诊断成员和分项原因另见样本流。

天气全量：129,414 可查询事件、82,621 个键、122,948 个键×小时，所需现存缓存 74,896 个。数值完整 121,178：缓存小时/窗口已验证 121,178，仅最早 v3 值可用、窗口未复核 0。缓存缺失与数值缺失分别计数；历史 model 仍未决，新请求为 0。

两个原因/身份未决事件保留全部源行及 C/D 公式值，按 R01 不纳入主原因候选，不拆分或去重。最早同刻事件 24,893，六项已检查 metadata 冲突为 0；不是对业务语义的全属性担保。Buckinghamshire 新人数如下：

| sample | H0_Buck | R02_Buck | R02_Buck_strict |
| --- | --- | --- | --- |
| main_E0 | 1151 | 1151 | 1151 |
| main_R0c | 1146 | 1151 | 1151 |
| weather_E0 | 293 | 293 | 293 |
| weather_R0c | 292 | 293 | 293 |

C10 原编号与标题：**Buck旧区简单均值proxy**；关联 T01、L01。根因是 Buckinghamshire 合并脚本对四个旧 LAD（E07000004–E07000007）索取 2021 人口时未找到旧码行，进入简单平均分支，将旧区 rate/gap/Moran 的均值作为 E06000060 的输入。证据：`checks/buckinghamshire_lineage.json` 的 oldcode_2021_population_rows=0、`checks/buckinghamshire_original_indicators.csv`、H0 冻结 `Buckinghamshire_combination.py` 和 GVA crosswalk 源码。源工作簿 SHA256 为 `6eb516a87654078ee69d4df55c8bc749b5da5de117f996f262c0c762bc20b38f`。本轮严格保留 .06325/.1875/.30，以 `regional_proxy_flag`、`legacy_arithmetic_crosswalk` 标记；这是已授权的历史代理，尚未重建合并区真值。gap 保持比例单位，普通 LAD 的定义是区域内 LSOA rate 极差；旧极差的平均不等于合并极差，旧 Moran 的平均不等于合并区 Moran。后续以匹配年份、边界、收入分子分母及空间权重进行 LSOA 重建并对照，未执行、未关闭科学问题。

实际入口 `scripts/v3_validation/v3_validation_pipeline.py::step0_build_sample` 已读取哈希校验后的 R02 主表；生成器 `scripts/event_input_repair/r02_events.py`。全量源行扰动等值、15 项针对性测试与实际入口等值检查通过。raw/v3、人口及已读缓存完整哈希保护通过；旧结果、论文未改。旧模型/OOF/图仅保留 H0 身份，修正模型待 R03/R04。

仍未决：真实业务 onset 与日历；两个事件的版本/ID 业务关系；历史气象 model、gust 的具体时间语义及响应单位 metadata；Buckinghamshire 真值与 Moran 权重；LAD21/23 同码的完整边界兼容；停钟/视同恢复、真实客户与阶段完整性。UTC 是 R01 冻结分析日历，Europe/London 并列结果用于暴露边界差异。全量缓存可用性检查已经完成，但缺失缓存和产品证据不会因完成扫描而消失。上述限制进入后续解释和敏感性分析，不能用程序一致性替代源业务证据。

交付：`reports/R02_report.md`；`tables/R02_SAMPLE_FLOW.md`；`tables/R02_OLD_NEW_SUMMARY.md`；`tables/R02_WEATHER_AVAILABILITY.md`；`tables/R02_AMBIGUOUS_EVENTS.md`；主表 `R02/data/R02_event_master.parquet`（另有 csv.gz）、`EVENT_MANIFEST.json`；四样本 H0_R02 crosswalk；`R02/code_changes/`、`R02/checks/` 与更新后的状态清单。以上相对路径均以 `D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2` 为根。
