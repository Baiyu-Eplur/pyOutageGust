# R01 完成报告

日期：2026-09-05。执行状态 completed；方法处理规则 rule_defined。未修活动生产代码、未构建R02正式修正事件表、未重估模型、未执行V/W，未修改文稿。范围是研究沿革、数据语义和可执行方法契约。

## 本次实际核实与复用的区别

本次读取原始237901阶段、完整时间/元数据，选读v3相关列，检查原IMD/人口/GVA工作簿，定向20个天气源行/14缓存，静态读取相关生产脚本；另查官方Ofgem/ONS/Open-Meteo资料。旧四模型/80折拟合/OOF结果仅从通过哈希校验的42份H0产物接收，未重跑。

H0主E0/R0c为60437/59834，天气9857/9758。主E08199例代表时间较晚；最早行改变会影响天气、日期、年度人口、成员及后续设计，不能只换timestamp字段。旧天气恢复相较主恢复天气成员另排48例来自独立p99，修复目标应是共同总体而非硬凑旧N。

## 新确认的关键发现

1. **4506.37小时事件与原因冲突重合。** FREP-338321-Z两行分别在2022-11-04和2023-05-11，cause98→71、MEI59→41、跨监管年度，站点一致；按ID算C=1、B=4508.933333h。两个阶段不连续，真实事件身份未决，不能直接称持续188天停电。最早行缺天气，旧较晚行有天气且年度人口154321，最早年人口151530。不能借可用天气后移时间。
2. **第二个原因冲突也涉及源ID复用。** FREP-314454-J两行都stage1、同unique_identifier但时间/原因/MEI不同，cause71与87。完全重复源行数为0；因此常规dedup可能删除合法或修订记录，本轮不执行。
3. **24893事件有最早同刻并列。** 并列行在坐标、原因、licence、监管年、站点等6类metadata均无冲突。稳定持久源行号可作为天气metadata选择规则；仍需保留未来冲突分支。
4. **时区链明确，过程完整性尚有限。** 所有源行带偏移，+01为128323、+00为109578；起止无解析缺失、无end<start。最晚结束到2024-04-25；2024-04-01边界35事件跨恢复，3事件跨阶段起始。v3保留原始全部行，不证明下载之前没有缺阶段。
5. **地区定义与旧稿不同，Buckinghamshire还有真实代理问题。** 原gap是LAD内部LSOA最大rate减最小rate，Moran也是LAD内LSOA聚集。Buck四旧区人口权重缺失，实际简单平均得到rate .06325、gap .1875、Moran .30；不是新地区重新计算。影响H0主E0 1151/主R1146，天气293/292。作者已选保留为明确历史代理，后续LSOA重建并对照。
6. **天气抽查不能证明产品身份。** 定向20行中16行有缓存，14文件attrs全空；可用样例均有精确小时和24有效降水值；4行缺缓存。2021春DST早于原始记录范围，未被此样例覆盖。历史请求没有models，本轮未确定原气象产品。0.1°是请求/缓存舍入；小时再分析不是当时实时可用信息。

业务解释依据：Ofgem区分事件起始与恢复阶段起始，因此本轮将min stage start定义为记录代理。[Ofgem阶段定义](https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf)。地区定义来自本地原工作簿Notes，并与[ONS数据页](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/mappingincomedeprivationatalocalauthoritylevel)对应；雨量端点含义参照[Open-Meteo定义](https://open-meteo.com/en/docs/historical-weather-api)。咨询/修订材料的版本边界和未取得UKPN完整字典均详列sources报告，不声称全研究期业务口径已认证。

## 已冻结的R02/R03规则

全阶段先定代理时间再筛窗/天气/原因；源行身份由文件SHA与持久row建立；同刻不按天气优劣挑选；原因全阶段共识而非随天气代表换行；年度人口按代理年份重关联。C排重复中断、空有效集合缺失，D用B，A只兼容；身份冲突/停钟/视同恢复未知保留flag。Buck保留proxy并标明。

E0/R0c保持已核实的部分标准化、平方/交互、年月两套加性哑变量和LAD聚类。B1定义共同有效恢复总体；可选训练p99从主训练样本取得，测试保留全部有效长尾。OOF主指标命名pooled，保留mean-fold另列；新日期fold跨主/天气共享，但仍不当完整过程留出验证。图4人群完整设计后平均η，图6固定天气/客户并共享日历参考，图7基于明确曲线范围，图9η直接对应log目标。所有规则待对应修复阶段实现。

## 研究推进过程与交付

RESEARCH_HISTORY逐一列#1–#43的问题、数据/结果变量、方法、取舍和迁移范围，覆盖v2阻塞→v3、A/B、天气继承、后期污染与自身重拟合、合并p99、天气/六组独有口径、NB/Gamma/Tweedie、E0三阶反向线索及放弃的反事实。E0旧三阶OOF增量约.001441只是旧输入线索，保留并待新输入检验，不把它删去或提前判不成立。

交付 contracts/DATA_CONTRACT.md、FIELD_PROVENANCE.md、INFORMATION_TIMING.md、CAUSE_RULES.md、WEATHER_AND_REGIONAL_SOURCES.md、BASELINE_SPEC.md及JSON、FIGURE_REFERENCE_CONTRACT.md、UNRESOLVED_DEFINITIONS.md；checks保存时间线、并列/原因、区域源值、天气案例和读取哈希。ISSUE_LEDGER同时保留C01–09/T01–14/L01–12，新增C10为Buck代理发现；状态不等同修复完成。

R01验收通过：R02有可实施规则，业务缺件有明确范围/候选/影响。真实onset、两ID身份、历史model、Moran权重和源导出特殊字段仍未解决；它们以受限定义和标记处理。本轮停止于R01，下一阶段R02尚未开始。

## 交付结束保护复核

549个既有受监测文件、91个源码及快照、14个读取天气缓存均未变化；3个读取工作簿哈希一致。raw/v3在R00已核验SHA，结束size/mtime一致。所需交付齐全，#1–#43沿革与全部原C/T/L编号完整；R02及以后状态仍not_started。证据见checks/final_preservation_check.json与final_delivery_checks.json。
