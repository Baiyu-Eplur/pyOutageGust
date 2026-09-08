> 隔离复核更新：原 v9 已恢复为 H0；当前修复入口为 `D:\Pyprogramme\STST2603\claude_branch\scripts\event_input_repair\r02_input_pipeline.py`。以下 R02 首次执行记录的数值保留，涉及旧入口改写/548 个未变文件的描述属于迁移前历史。当前为 549/549 旧文件一致；详见 reports/R02_ISOLATION_REVIEW.md。

# R02 事件与时间相关输入修复报告

版本：R02_input_20260905；生成时间：2026-09-05T17:00:45.240084+00:00。本轮按用户“按该文件执行”授权，承接 R00–R01，仅完成 R02；未重跑 H0 四模型/80 折拟合，未估计 B1、未修改论文、未开始 R03/V/W。

## 1. 完成状态及关键结果

规则明确（限可执行代理口径）→代码已修→输入已重建→针对性检查通过；模型尚未重估。237,901 条完整阶段记录形成 135,025 个唯一事件；代表 UTC 时刻改变 12,886，天气小时改变 12,018，UTC 日期改变 2,802，年份改变 12，月份改变 95，开发/后期/窗外改变 1，原因组改变 2，人口值或缺失状态改变 12。C/D 全事件容差检查零差异，不能将这些结果表述为模型或科学结论已验证。

| sample | H0 | R02_candidate | common | enter | exit | strict_cache_candidate | conditional_v3_only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| main_E0 | 60437 | 60436 | 60436 | 0 | 1 | 60436 | 0 |
| main_R0c | 59834 | 60436 | 59834 | 602 | 0 | 60436 | 0 |
| weather_E0 | 9857 | 9857 | 9857 | 0 | 0 | 9857 | 0 |
| weather_R0c | 9758 | 9857 | 9758 | 99 | 0 | 9857 | 0 |

R02_candidate 是全有效尾部的输入候选，含明确标记的 v3-only 条件来源；strict_cache_candidate 表示小时、数值及窗口已核查，仍有历史产品限制。恢复成员增加包含尾部口径改变，不能都归因于时间修复。`tables/R02_SAMPLE_FLOW.md` 另列旧首行原因/独立 p99 的 R1_compat 候选诊断、固定顺序排除、转移原因及质量标记；未生成 R1 模型。

## 2. 实际入口与可追溯字段

修改了 `scripts/v3_validation/v3_validation_pipeline.py::step0_build_sample`，这是 combined → dev/holdout → v9 的共享入口。现在读取并校验 `R02/data/EVENT_MANIFEST.json` 对应主表，不再按原行序选代表阶段；缺文件或哈希不一致会失败，不退回 H0。删除 v9 导入时 mkdir；step1 在 R02 下只核查已生成 LAD 覆盖；step2 遇到 R02 明确停止，等待 R03 修复 fold/tail 接口。本轮没有修好所有旧生产脚本或运行图表。

确定性生产者为 `scripts/event_input_repair/r02_events.py`，显式 I/O 运行器为 `code/run_r02.py`（prepare/weather/finish）。raw 原文件在任何排序前标记 1-based source_row_number；稳定源键为 raw SHA256:row。全阶段 UTC 最小时刻并列时以原源行号破同刻，不以天气是否可得选择。24,893 个事件并列，核查 Spatial Coordinates、Cause Code、licence_area、regulatory_year、substation、SiteFunctionalLocation 六项冲突均为 0；不扩大成所有业务属性均无冲突。

原始时间字符串、原偏移、UTC/London 时刻、每事件全源行列表、最早候选行、选中行和旧行均保留。时间取最早有效阶段；天气用选中位置和小时；原因取所有阶段独立共识；人口使用修正 UTC 年份和 LAD→LAD23CD/year 唯一键重关联。业务 onset 留空，首阶段存在不等于已确认真实故障时刻。

研究期为 UTC [2021-04-01 00:00,2024-04-01 00:00)，包括 2024-03-31 全天；后期自 2023-09-30 00:00Z。先用完整阶段计算再筛事件，保留跨研究终点的恢复记录。London 日期、时期和风暴结果并列，详见 `tables/R02_calendar_comparison.csv`、`tables/R02_calendar_boundary_events.csv`；重叠风暴单列 UNIQUE_ANY，不直接相加。

C=sum 非再次中断阶段客户，全部被排除时为空而非零；D=最大恢复结束−最早开始，保持 duration_B 映射；兼容 `Duration (hours)` 仍是 A 加权时长。完整 C 差异 0，D/A 仅机器浮点误差（上限分别约 6.82e−13/1.14e−13 h）。没有按代表行裁掉其他阶段。

## 3. 全量天气核查

可查询事件 129,414，不同最早查询键 82,621，键×小时 122,948；所需现存文件 74,896。目录原有 75,983 个文件。四天气数值完整事件 121,178，其中缓存小时/窗口检查通过 121,178，仅最早 v3 源行数值可用但窗口无法复核 0。不同分母在 `tables/R02_WEATHER_AVAILABILITY.md` 逐项列明。

检查精确小时唯一性，(t−24h,t] 雨量 24 个唯一完整整点、有限且非负。无 nearest 代用、不补零，不借后续阶段天气。可读缓存无效时保留失败而非用旧值遮盖；缓存缺失时仅保留键、时刻一致的最早 v3 源行，并标记条件来源。数值可用、缓存文件可得、历史产品可确认是三个独立状态。原请求 wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT 为代码依据，缓存响应单位 metadata 未核清，所有记录仍为 historical_model_unresolved；未新抓天气。

## 4. 未决事件、区域与 C10

FREP-338321-Z 与 FREP-314454-J 均完整保留，按原 ID 公式 C/D 可计算但业务身份/原因未决。全阶段原因冲突进入 unresolved，按冻结 R01 规则不进入主原因候选。前者的 4508.933333 h 不称连续 188 天失电；后者同 stage1/unique_identifier 的两记录不作完全重复行删除。天气与年度人口的实际变化及时间线见 `tables/R02_AMBIGUOUS_EVENTS.md` 与原阶段 CSV。

人口 lookup 无重复键，many_to_one 合并保持 135,025 事件。选中 LAD 缺失 5,762，其中 151 有可用查询坐标，尝试同 2021 边界唯一 within 匹配后无新增匹配；没有任意多配或静默借用另一 LAD。新旧坐标、LAD 与区域缺失影响单列。

C10 原编号与标题：**Buck旧区简单均值proxy**；关联 T01、L01。根因是 Buckinghamshire 合并脚本对四个旧 LAD（E07000004–E07000007）索取 2021 人口时未找到旧码行，进入简单平均分支，将旧区 rate/gap/Moran 的均值作为 E06000060 的输入。证据：`checks/buckinghamshire_lineage.json` 的 oldcode_2021_population_rows=0、`checks/buckinghamshire_original_indicators.csv`、H0 冻结 `Buckinghamshire_combination.py` 和 GVA crosswalk 源码。源工作簿 SHA256 为 `6eb516a87654078ee69d4df55c8bc749b5da5de117f996f262c0c762bc20b38f`。本轮严格保留 .06325/.1875/.30，以 `regional_proxy_flag`、`legacy_arithmetic_crosswalk` 标记；这是已授权的历史代理，尚未重建合并区真值。gap 保持比例单位，普通 LAD 的定义是区域内 LSOA rate 极差；旧极差的平均不等于合并极差，旧 Moran 的平均不等于合并区 Moran。后续以匹配年份、边界、收入分子分母及空间权重进行 LSOA 重建并对照，未执行、未关闭科学问题。

| sample | H0_Buck | R02_Buck | R02_Buck_strict |
| --- | --- | --- | --- |
| main_E0 | 1151 | 1151 | 1151 |
| main_R0c | 1146 | 1151 | 1151 |
| weather_E0 | 293 | 293 | 293 |
| weather_R0c | 292 | 293 | 293 |

## 5. 检查、保护与复现

15 项针对性测试通过；真实 237,901 源行全量随机重排后，203 个构造字段逐项完全一致。另通过全事件 C/D/A 一致性、两个冲突事件保留与资格、人口唯一键、Buck 精确代理值、严格天气窗口及实际入口主表等值测试。检查发现缺坐标标志和缺失 C 候选资格的 nullable 布尔处理问题，已修为明确 False/缺失原因并复测通过，见 `R02/logs/unit_tests.txt`。

保护清单 549 文件，唯一有意修改为 v9 活动源代码，其余 548 哈希一致；raw/v3 再次完整 SHA256 比对一致；人口源一致；75,983 缓存目录文件 size/mtime 清单一致，已读的 74,896 个请求缓存文件逐一二次 SHA256 一致。稿件、只读依赖与历史结果保持原样。细目见 `R02/checks/protection_after.json`。代码差异、H0 快照和代码身份见 `R02/code_changes/`。

运行环境及包版本见 `R02/checks/runtime.json`；复现命令见 `R02/REPRODUCE.md`。manifest 固定原始/v3 输入、配置、生产者和天气审计身份。旧模型/OOF/图仍保存为 H0，依赖修正输入的结果全部需要后续重算。

## 6. 尚未解决与下一阶段边界

仍未决：真实业务 onset 与日历；两个事件的版本/ID 业务关系；历史气象 model、gust 的具体时间语义及响应单位 metadata；Buckinghamshire 真值与 Moran 权重；LAD21/23 同码的完整边界兼容；停钟/视同恢复、真实客户与阶段完整性。UTC 是 R01 冻结分析日历，Europe/London 并列结果用于暴露边界差异。全量缓存可用性检查已经完成，但缺失缓存和产品证据不会因完成扫描而消失。上述限制进入后续解释和敏感性分析，不能用程序一致性替代源业务证据。

R03 仍需统一折分/尾部/评分/变换/图形参考和缺失生产入口，R04 才产生修正模型及 OOF。此处仅提供进入下一轮审阅的输入证据，不宣布 C02–C09 或科学主张全部关闭。本轮完成 R02 后停止。
