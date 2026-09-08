# R01 数据口径 v1

2026-09-05；状态 rule_defined，尚未实现R02。以下规则用于修复输入；H0保留原行为，R1兼容项必须显式命名，B1尚未生成。科学对象是已记录事件的客户影响与记录恢复跨度的回顾性条件关联。

## 1. 记录与事件身份

原始文件为 `D:\Pyprogramme\STST2603\data\ukpn-iis.csv`，237901行/20源字段；v3逐行保留全部源字段。冻结文件SHA与原始1-based行号共同定义 `source_row_key=(raw_sha256,source_row_number)`。原 `unique_identifier` 保留但不能单独作为主键：发现2行复用同一ID。原始行号须在任何排序、分块、join前赋值并持久化；读v3则核对其既有source_row_number。禁止在打乱后的表上重新编号。

事件暂按规范化Incident Reference聚合，保留全部源行关系。不将同刻、同阶段号、同源ID自动去重；本次源20字段完全相同行为0。对同ID跨原因组、源ID冲突、地域冲突记录 `event_identity_unresolved`，不擅自按年度拆分，也不保证Incident Reference在所有业务情况下对应单次物理故障。

## 2. 起始时间与并列

所有源起止时间带偏移：128323行+01:00，109578行+00:00。逐值按偏移转UTC，保留原字符串和offset；不得移除offset再localize，不使用ambiguous=infer或nonexistent=shift_forward改造这些原数据。当前缺失/无效起止和end<start均为0。未来无偏移值不能默认伦敦或UTC，应报错/隔离为语义未定。

`earliest_recorded_start_utc=min(valid stage start)`，并列候选来自全阶段表。按持久source_row_number升序选最小行，source_row_key为稳定依据，unique_identifier为审查辅助。24893事件并列；其中坐标、原因、licence_area、regulatory_year、substation、SiteFunctionalLocation冲突均为0。未来并列冲突保留所有候选，不按天气完整程度挑选；冲突字段置未决或隔离相应分析，时间最小值仍可报告。

`event_time_proxy_utc=earliest_recorded_start_utc`，`event_time_basis=earliest_available_stage_start`。`business_onset_utc=null`，除非另获事件级业务起始证据。Ofgem区分事件知晓/报告起始与阶段断电起始，最小阶段时间不必等于业务onset。`min_stage_ge2`只表示记录中最小阶段号≥2，不证明一定丢失首阶段，也不把stage1存在当完整性保证。另保留 `first_stage_observed`、`stage_number_missing`、`source_window_left_censoring_possible`、`event_identity_unresolved`。

研究窗采用明确UTC代理口径 `[2021-04-01T00:00Z,2024-04-01T00:00Z)`；历史前后分界为2023-09-30T00:00Z。该分界不是2023-04-01监管年度切点。先全阶段聚合和定时，再按事件代理起始纳入；已入样事件保留窗外恢复阶段/结束，不用结束在窗外作为排除理由。研究calendar year/month/day来自代理UTC时间；原regulatory_year逐行保留，绝不重写为calendar year。

v3构建没有在本地原始237901行内提前裁阶段，但不能证明下载源在2021-04前没有遗漏阶段。原始最早记录2021-04-01 00:07Z，最晚阶段开始2024-04-01 13:26Z、结束2024-04-25 11:23Z。2024-04-01边界有35事件先开始后结束，其中3事件阶段起始跨界；2023-04-01对应62/14。恢复跨界、年度分配与事件开始入样应分开。R02另核真正2023-09-30分界和本地时区边界个案。

## 3. 字段逐项来源

完整字段及信息时间表见 FIELD_PROVENANCE.md / INFORMATION_TIMING.md。天气时间只来自代理；坐标来自最早候选中的一致metadata，不借后行补天气。保留 `coordinate_basis=reported_primary_substation_proxy`，空间点不是已核实故障资产点。LAD取该坐标的2021边界匹配；既有唯一一致LAD可复用并留源行，否则按同一边界重查；多重匹配/边界点必须显式处理，不能first join。

人口按事件代理UTC calendar year和LAD重新关联，不只改year标签。源人口是2023地理代码下的年度估计，当前生产代码直接LAD21/LAD23同码连接；同码不自动证明边界同一。明确记录 geography_compatibility，并输出改年/改LAD/缺人口的事件。禁止沿用改变前年度人口。IMD/RUC/Moran静态不随事件年份改；GVA实际为2016静态，亦不随时间改。

原因独立处理：规范化数值码为两位文本并保留字母码；全阶段非缺失code一致则 `cause_basis=record_consensus_retrospective`，不是已核实最终诊断；缺失混入另加flag。多code列完整集合并设cause_code_event和cause_group_event为未决，不能随天气代表行变动。R1兼容输出保留 `legacy_first_cause`，只用于解释旧新差异；B1原因限制样本不将原因未决事件归入weather/technical，原事件总账和质量表必须保留并报告其排除原因。

两例具体规则：FREP-338321-Z和FREP-314454-J均标记事件身份/原因未决。它们不能被宣称已修成正确事件，不能靠固定极端阈值删除，更不能把相隔188天解释为连续停电。核查说明见 CAUSE_RULES.md。R02可以生成带flag的代理输入并继续其余事件，正式原因分组中明确单列未决。

## 4. 结果变量

`C=Σ c_s 1(reinterruption not in {Y,1})`，标记N/0视为非重复。源客户数数值解析保留真实零（不推定未发生故障）；空有效集合为缺失，不能sum默认0。若未来出现未知重复标记/负客户/部分缺失，B1 C记为无法完整确定并保存可观测部分和原因；H0/R1历史公式另存。当前N217276/Y20525/0为98/1为2行；负客户0，历史全重复事件69。

`D=duration_B_full_span_hours=(max stage end-min stage start)/3600`，保留重复中断阶段，描述记录覆盖跨度；它不是CML/每客户平均停电/连续失电时间/现场修复工时。若有缺起止，不能把可观测max/min当完整D，B1标记partial；当前起止全有效。未知停钟、视同恢复、临时供电和未记录末阶段不填0或否，写unknown。

A是所有有效阶段（含重复）的客户加权时长，分母为这些阶段客户数；分母≤0则缺失。兼容列`Duration (hours)`实际指A，R02后的恢复模型必须只用明确D列。原客户指标与监管阶段定义一致性得到支持，但源导出如何编码特殊客户/停钟仍未逐业务确认；不称精确去重用户数或官方CI。

`n_stages`为全部源阶段行数，不是max阶段号，不因重复中断而减少；`n_distinct_stage_numbers`另存。行数/客户/时间总量可复现不消除事件身份歧义。

## 5. 天气与区域执行约束

详见 WEATHER_AND_REGIONAL_SOURCES.md。`h=floor(event_time_proxy_utc,1h)`；必须匹配唯一精确小时，不沿用旧nearest fallback。降水只在24个唯一小时端点h−23h…h、各值有限且非负时求和；缺1值为missing。`weather_status_v3=matched`只说明缓存加载，不足以当完整性通过。无最早小时天气则保留事件和缺失标记，不能换较晚行。R02先cache-only重新取特征/校验（v3源行可作对照），不请求当今默认产品。

保留请求round(lat,1)/round(lon,1)和实际产品坐标的区别；0.1度是缓存/请求离散化，不是模型网格分辨率。历史缓存抽查未保存models，不宣称全ERA5或准确3秒峰值。发生时间代理、小时产品定义和历史可用时点三个层次分别报告。

作者已决定Buckinghamshire保留为显式历史代理，后续LSOA重建并对照：令regional_proxy_flag=true、regional_source_version=legacy_arithmetic_crosswalk，禁止称合并地区官方Moran或真正内部极差。代理在R1及明确声明的B1配置中可暂保留，科学区域解释保持未决；重建不在本轮执行。

## 6. R02应保存和验收

输出所有135025源ID的来源/质量主表（不承诺全部进入分析）；字段包括raw_sha/source_rows/earliest_candidates/selected_source_row、old/new time/weather/year/population、各字段basis、C/D/A/n_stages、flags、所有排除理由。保存总体流、共同事件变化及新增/移出事件，不以恢复60437等旧N为目标。

必要检查：冻结源ID后shuffle不变；并列顺序不变；故意使最早天气缺失不后移；跨研究/开发边界；源ID冲突不deduplicate；全年人口随代理年更新；降水24行但含NaN必须缺失；无精确小时不nearest；未经源定义的原因不first/last自动挑选。尚未运行这些R02修复测试。
