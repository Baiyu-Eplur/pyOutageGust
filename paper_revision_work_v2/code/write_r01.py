"""Compose R01 contracts and feedback from completed read-only checks."""
import json,csv,re,ast,hashlib,datetime,math
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;P=R.parent
def put(p,s):
    q=O/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s,encoding='utf-8')
def jput(p,x):put(p,json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False))
put('contracts/DATA_CONTRACT.md','''# R01 数据口径 v1

2026-09-05；状态 rule_defined，尚未实现R02。以下规则用于修复输入；H0保留原行为，R1兼容项必须显式命名，B1尚未生成。科学对象是已记录事件的客户影响与记录恢复跨度的回顾性条件关联。

## 1. 记录与事件身份

原始文件为 `D:\\Pyprogramme\\STST2603\\data\\ukpn-iis.csv`，237901行/20源字段；v3逐行保留全部源字段。冻结文件SHA与原始1-based行号共同定义 `source_row_key=(raw_sha256,source_row_number)`。原 `unique_identifier` 保留但不能单独作为主键：发现2行复用同一ID。原始行号须在任何排序、分块、join前赋值并持久化；读v3则核对其既有source_row_number。禁止在打乱后的表上重新编号。

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
''')
put('contracts/FIELD_PROVENANCE.md','''# 字段来源表

|字段|选取层级/公式|可用/来源身份|冲突或缺失规则|
|---|---|---|---|
|source_row_key|raw SHA + 持久原行号|源行身份|unique_identifier冲突也不删行|
|event_time_proxy_utc|全阶段最小有效起始|记录时间代理|保留未知business_onset；不借天气改时间|
|selected_weather_source_row|最早候选内最小持久行号|仅定位metadata|同刻冲突逐字段标记，不按天气优先|
|query_lat/lon|最早候选一致Spatial Coordinates|上游primary站点代理|缺失不从晚行猜；记录候选冲突|
|LAD21CD|代理点与冻结2021边界|地理匹配结果|多个匹配不first；边界规则需唯一/缺失|
|year/month/day|代理UTC时间|calendar派生|不等于regulatory_year|
|population/log_population|LAD与代理year连接/ln(pop>0)|ONS年度、2023地理；事后发布|保留同码跨地理限制，缺失不旧年填充|
|rural_urban/urban_binary|静态RUC源文本；含urban→1，其余已知rural→0|2011分类继承/重组proxy|未知不默认0；未覆盖类别先报出|
|income_deprivation_rate|2019源LAD收入剥夺比例|静态、LSOA人口权重汇总|比例0–1；Buck proxy另标|
|deprivation_gap_pct|源LAD内部LSOA rate max−min|静态；存储比例差|展示百分点乘100，不是地方−全国|
|morans_i|源LAD内部LSOA空间聚集|静态无量纲；原权重细节未核实|Buck平均值仅proxy；非相邻LAD统计|
|GVA列|2016 workbook→gva_industry_2016→旧master_final lookup|静态地区经济量|当前E0/R0c不入模；不能自动改成年份变量|
|cause_code_event/group|全阶段规范化code共识；六组为研究者映射|回顾性记录分类|多code未决；最终诊断时点未知|
|legacy_first_cause|H0原文件首行|兼容诊断|不作为B1默认事件原因|
|C|非重复阶段客户之和|全事件结束后聚合|空集合/未知记录不填0|
|D/B|全阶段max(end)−min(start)|记录恢复跨度|非连续断电，不自动删长时|
|A|所有有效阶段客户加权duration|兼容历史|不得误接入恢复目标|
|n_stages/min_stage|源阶段行计数/数值阶段号最小|事后过程质量|min≥2不是完整性真值|
|停钟/视同恢复/真实初始客户|当前20源列没有相应明确字段|not_available|unknown/null；不填0|

若metadata字段来自不同源行，分别保存source_row_key，不能只给一个event representative掩盖来源差异。
''')
put('contracts/INFORMATION_TIMING.md','''# 信息可用时间表

|信息|实际测量/生成时点|可否主张故障初期已可用|当前用途|
|---|---|---|---|
|事件原始最早阶段时间|记录阶段断电/去能时间|不等于首次报告/真实物理起始|回顾性天气对齐代理|
|历史天气小时值|事后取得的历史API产品|历史天气不自动等于实时可获取产品|事后危险性协变量|
|降水24h|以floor代理小时为右端、前24小时累计|物理时间窗可早于代理；相对未知真实onset不保证|记录代理前天气条件|
|站点坐标/LAD|资产/站点信息与事后匹配|可能早已存在，但无当时快照证明|地区代理|
|2019剥夺/2011RUC/2016GVA|冻结静态版本|不宣称全部事件当时已有本文件版本|回顾性地区背景|
|年度人口|该年度估计及事后发布/修订|不是当日已知精确人口|回顾性年度控制|
|原因/MEI/损坏标记|业务诊断、记录修订时点未知|不能假设故障初期可用|回顾性原因组成|
|最终C|所有相关阶段结束后计算|否；首阶段restored也不等于initial C|恢复模型事后条件变量|
|D、A、n_stages|恢复过程结束后汇总|否|结果或过程描述|

当前定位不增加初期预测、调度优先级识别、发生概率、工程损伤阈值或因果效应主张。英文候选仅供后续落稿：

“We examine retrospective conditional associations between recorded incident consequences and weather aligned to the earliest available stage-start timestamp.”

“The recovery model conditions on the final aggregated customer count; it is not an onset-time forecasting model.”

本轮没有把上述句子写入稿件。
''')
put('contracts/CAUSE_RULES.md','''# 原因与特殊事件规则

六组码表机器版见 cause_group_map.json，直接AST读取冻结v3 classify_cause_code的字面映射，未import。该函数列名虽叫cause_group_official，六组合并是项目分析分类，不能称监管官方六组。原Ofgem码与作者合并层分开保留。

|事件|本次原始行证据|解释边界与可执行处置|
|---|---|---|
|FREP-338321-Z|原行163320：stage1，2022-11-04 16:44–17:10Z，C_s=0，cause98，MEI59，2022-23；原行89486：stage2，2023-05-11 11:06–13:40Z，C_s=1，cause71，MEI41，2023-24。站点/坐标一致|旧首行晚4506.366667h；按ID公式B=4508.933333h，C=1。两段不连续；无法判定ID复用、修订残留或其他业务情形。不是已证实持续188天停电。flag identity/cause unresolved；记录表保留；不擅自合并语义或按年拆分|
|FREP-314454-J|原行147106：stage1，2023-03-24 19:27Z–04-05 10:50Z，C_s=1，cause71，MEI51；原行94432：stage1，2023-04-05 08:23–10:46Z，C_s=1，cause87，MEI90；同unique_identifier FREP-314454-J1、不同年度|不是完全重复行，不能dedup；按ID客户加总可能含修订/重复，但本轮无依据判定。flag identity/sourceID/cause unresolved；C/D标记provisional，正式原因样本单列|

码71为老化/磨损（不含腐蚀），98为原因未分类，87为孤立系统本地发电失效；参见[Ofgem Annex F Appendix 5](https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf)。2020在线文件呈修订版标记，本轮用来交叉核对语义，不冒称已锁定每个监管年的最终规则版本。

最早天气选择不改变原因来源规则。共识原因使用所有阶段；“最后时间行”不是“最终诊断记录”。继续原因码也不能未经业务依据覆盖主cause。R02输出缺失/冲突全集及原码分布，主样本只接纳共识映射到weather_natural/technical_asset者；六组比较保留相同未决策略。

最小源缺件：两ID的UKPN事件级版本/修订标识、是否跨年复用及正式起始/结束。未获得前保留上述受限身份；不把源缺件阻塞其余135023 ID的确定性规则实现。
''')
tree=ast.parse((P/'rebuild_v3_full_stage/scripts/build_stage_base_v3.py').read_text(encoding='utf-8-sig'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='classify_cause_code')
mapping=ast.literal_eval(fn.body[0].value)
jput('contracts/cause_group_map.json',{'source':str(P/'rebuild_v3_full_stage/scripts/build_stage_base_v3.py'),'basis':'researcher_defined_groups_of_source_codes','groups':{k:sorted(v) for k,v in mapping.items()},'unknown':'unmapped','event_conflict':'unresolved'})
put('contracts/WEATHER_AND_REGIONAL_SOURCES.md','''# 天气与区域来源核实

## 天气：实现证据与产品语义分开

实际链是 `rebuild_v3_full_stage/scripts/weather_cached_chunk_v3.py`→`main1_v3.py`；原`main1.py`历史API请求使用archive端点、hourly数组、wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT，没有models。历史请求key为一位小数坐标与UTC日期。v3对每个阶段floor小时抽取，#9/#10及后续事件分析继承这些天气列、再按源第一行代表事件，不是按新C/B自动重新匹配。

本轮定向20行（极端、原因冲突、最高gust、DST附近和普通样例），16行有缓存，涉及14个pkl；4行缺缓存。缓存内可用样例均有精确小时、24个有效非负降水值；无重复小时。所有读取pkl的DataFrame attrs为空，只有小时列，没有可确认历史实际model的标识。本轮没有全面扫所有缓存/全量有效雨值，也没有解码所有SQLite历史响应；不能据14文件推断全部历史产品一致。文件SHA记录在weather_cache_read_hashes.json。

原始时间保留+01/+00，UTC转换不依赖推断DST。例如源行1原10:32+01→09:32Z→09:00Z；2023-10-29附近源行2794为01:01+00→01:00Z。2021春季DST在数据起点之前，本次选到的是数据首日附近记录，不能算覆盖那个转换日；其余案例逐条见weather_case_checks.json。极端最早源行163320缺对应51.8_1.2_2022-11-04缓存，不能后移到有天气的2023行。

当前官方定义将precipitation记为前一小时累计；floor后使用h−23h…h共24端点，物理累计覆盖(h−24h,h]，实际代理起始晚于h的0–59分未覆盖。降雨值全部有限与24行齐全是两个条件；旧sum跳过NaN可能掩盖缺失。官方gust字段为10m所示小时值，部分产品有特定前一小时最大值含义；历史models未确定，因此不把它写成已确认的ERA5产品或标准3秒峰值。[Open-Meteo小时定义](https://open-meteo.com/en/docs/historical-weather-api)

本次确认的是请求单位m/s、mm、GMT和缓存数值继承，不是每个产品精度或再分析无未来信息。0.1°是请求舍入/缓存分组，不能当实际格网间距。按真实故障onset“绝无未来天气”的判断仍受代理起始和产品语义限制。修复先保留历史产品身份unknown，不用2026默认产品静默填缺；如要新请求，需单独产品固定和兼容对照。

## 地区：已读原工作簿与实际旧lookup

原文件 `D:\\Pyprogramme\\STST2603\\data\\localincomedeprivationdata.xlsx` 的Notes与Rankings for all indicators已读取。收入剥夺率是LSOA人口加权的LAD整体rate；gap是同LAD最高减最低LSOA rate；Moran描述LAD内LSOA空间聚集，不是相邻LAD之间聚集。Notes给出基础shapefile但未指定完整权重矩阵、邻接/距离、标准化和孤岛处理，本轮不编造这些细节。[ONS数据来源页](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/mappingincomedeprivationatalocalauthoritylevel)

数值单位实例：Adur gap单元H3=0.217，Excel格式0.0%，即21.7个百分点；L3 rate=0.108即10.8%。当前脚本保留0–1比例尺度，未乘100；系数解释不能把1单位误当1个百分点。主矩阵满秩、gap非精确仿射接受为H0证据，按源定义也不应预设删gap。

实际继承：Buckinghamshire_combination.py读Rankings与2021人口→data/new/ukpn_master_with_income_deprivation_crosswalk.csv；v3 enrich_downstream_v3.py把旧主表按LADCD取唯一lookup再left merge，没有从原LSOA重算。GVA_new.py读regionalgvabbylainuk.xlsx的2016列→gva_industry_2016.csv；GVA_merge_with_crosswalk.py→data/new/ukpn_master_final.csv；v3同样按LADCD借用。人口源myebtablesuk20112024.xlsx的MYEB3生成population_lad_long.csv。两个源工作簿标题/表单亦本轮读取，见other_workbook_sources.json。GVA当前不在E0/R0c设计中，不因此扩展模型。

## Buckinghamshire新增实证发现（C10，对应T01/L01）

合并前4区E07000004/5/6/7的2021人口在所用LAD23长表中无对应行，所以旧代码退化为简单平均：rate=(.067+.053+.057+.076)/4=.06325；gap=(.196+.216+.134+.204)/4=.1875；Moran=(.47+.29+.02+.42)/4=.30。与v3新代码E06000060值一致。此处不是人口加权，也不是新地区的真实内部极差或重新计算Moran。来源文件名validated不能消除这一方法限制。

影响源事件2313；H0主E0 1151、主R0c1146、天气E0 293、天气R0c292。作者本轮明确选择“保留为代理，后续重建并对照”。规则：保留样本和现值，逐事件/地图标proxy，后续以冻结LSOA边界/权重重建新地理指标并与历史proxy比较；不自动删除该LAD、不重算本轮模型。均值proxy的区域系数解释暂收窄。GVA旧crosswalk亦需按保留用途检查，不能把金额类可加性等同Moran可平均性。

## 源字段语义边界

Ofgem区分事件开始与阶段起始；阶段客户是该阶段恢复网络部分的客户；同一事件可有临时供电/重复中断。[ED1阶段说明§2.34–2.41](https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf)。ED2在线v1.1材料亦区分阶段、停钟及视同恢复；本次取得的是2023年10月咨询附件，用于语义交叉核对，不能替代全研究期最终版适用性核验。[ED2相关章节](https://www.ofgem.gov.uk/sites/default/files/2023-10/RIIO-ED2%20-%20Annex%20F%20Interruptions%20v1.1.pdf)

原20列没有明确停钟起止/视同恢复字段、事件修订号、初始客户真值；这些业务事实not_available。UKPN在线页面已重定向，当前工具未取得完整数据字典/API元数据，portal用途描述主要复用本地data_source_inventory.md的来源记录。不得声称本次已逐项核实官方导出字典。后续最小缺件而非阻断所有计算。
''')
put('contracts/BASELINE_SPEC.md','''# 基线与评价口径 v1

本文件定义后续配置；R00/R01没有生成R1/B1模型，所有旧数值明确属于H0。

|版本|事件与样本|尾部/评价身份|
|---|---|---|
|H0|冻结旧first-row、旧天气/日期；主60437/59834、天气9857/9758|历史主p99=192.083333h；天气142.844667h；dev194.795833h；later167.365333h；各自日期fold|
|R1_input_compat|修时间/天气/依赖年人口，保留旧first原因及独立p99/fold为显式诊断配置|每一改动/样本变化分项报；旧缺陷不算已修复，不把差异全归因单一错误|
|B1_declared|DATA_CONTRACT代理时间/原因共识、Buck proxy已授权并标记、统一基础成员|正式回顾基础有效D>0且C可用，不按天气组另定目标；训练尾部策略与评价总体分离；未完成科学验证|

E0：C有限且≥0，yE=ln(1+C)。R0c：D有限且>0、C有限且≥0，yR=ln(D)，客户K=ln(1+C)。零C保留。完整预测变量分别检测有限值/类别与LAD，不只notna；缺失排除理由可多选，总体流用固定顺序计数且给交集。E/R目标不同不硬凑同N；同目标竞争模型必须同事件评分。

E0设计：截距；zG、zG²、zRain24、zTemp、zPressure、zG×zPressure；urban_binary、ln(population)、income_rate、gap、Moran原尺度；calendar year和month各自加性哑变量（训练内有序首类别为参考）。R0c再加zK及zK²。z的均值和样本SD(ddof=1)来自拟合训练集，平方/交互在标准化后生成；不是所有连续变量都标准化。LAD是聚类推断单位，不是LAD固定效应。历史主设计26/28列满秩不保证新成员下始终满秩。

缺失不在本阶段新增插补。新留出出现训练未见year/month时禁止从测试y拟合类别效应；R3接口应显式raise/记录unknown，V00决定向前预测可用的日历规格；不能把未知类别静默编码参考类冒充已建模新年。

共同恢复总体：先生成全基础、记录有效D/C/协变量、原因共识成员，再从同一基础标weather。B1全样本回顾拟合默认保留所有有效D；如果保留p99训练策略，阈值仅来自训练主恢复总体（所有其他输入资格满足且D>0/C可用），用同一主训练阈值筛主/天气的训练成员。评价为预定义全部有效测试事件，不能因测试D>阈值而删除。旧cap检验另作H0/R1兼容；不得用硬编码48条或旧N作为验收。V01再比较全尾部与训练cap，当前不执行。

R阶段日期诊断共享全局date→fold（先基础事件定统一日fold再派生主/天气，不逐子样本再GroupKFold）；所有嵌套模型在同样成员、fold、评分分母比较。它仍可能拆分天气过程，不能充作V00的完整过程留出。

主评分 `pooled_oof_r2=1−Σ_i(y_i−yhat_i)^2/Σ_i(y_i−mean(y_eval))^2`，报告逐折R²及`mean_fold_r2`但不混名。此R²的评价均值用于定义统计量；另行训练均值基准预测用于误差比较，不能把两种基准混同。常量/极小评价集合R²无定义则null，不填0。同目标组删项/加项的差共享y和分母；G组含gust一次/二次/与pressure交互，删G保留pressure主效应；K含客户一次/二次。日期/过程权重方案未来另冻结。

预测契约：η直接与yE或yR比较；E风暴错误log1p(expη)不得再出现。expη仅指数化拟合log响应；E的expm1η也不自动成为E[C|X]，R的expη不自动成为条件算术均值或中位数。若未来要原尺度均值，独立规定训练内反变换/均值模型与验证。风暴图必须输出训练成员、因训练策略未入fit者、重叠窗口和唯一事件；样本内图不能叫留出验证。

完整配置草案见baseline_spec.json；尚不是V00预注册/科学协议。图形参考规则见FIGURE_REFERENCE_CONTRACT.md。
''')
jput('contracts/baseline_spec.json',{'contract_version':'R01_v1','status':'rule_defined','event_time':'earliest_available_stage_start_utc','study_start_inclusive':'2021-04-01T00:00:00Z','study_end_exclusive':'2024-04-01T00:00:00Z','historical_later_start':'2023-09-30T00:00:00Z','business_onset_verified':False,'source_row_identity':['raw_sha256','source_row_number'],'tie_break':['earliest_valid_start','persisted_source_row_number'],'cause':'full_stage_consensus_else_unresolved','buckinghamshire':'retain_flagged_legacy_proxy_then_LSOA_rebuild_comparison','weather_exact_hour':True,'rain_window_hours':24,'rain_min_valid_values':24,'new_weather_requests':False,'targets':{'E0':'log1p(C)','R0c':'log(duration_B_full_span_hours)'},'scale_cols':['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h'],'recovery_extra_scale':['log1p(C)'],'sd_ddof':1,'regional_scale':'raw except natural log population','calendar':'additive year and month; training levels only','unseen_calendar':'explicit error pending V00 design decision','B1_primary_training_tail':'all_valid','B1_optional_p99_training_reference':'main_training_recovery_eligible','B1_evaluation_tail':'all_valid_no_test_y_trimming','OOF_primary_metric':'pooled_oof_r2','OOF_secondary_metric':'mean_fold_r2','R_stage_splits':'shared_global_UTC_date_fold_not_independent_weather_process_validation','executed_models':[]})
put('contracts/FIGURE_REFERENCE_CONTRACT.md','''# 图件参考条件契约（定义，尚未重绘）

|图|保留要表达的量|具体生成/平均顺序|反变换/区间规则|
|---|---|---|---|
|1–2|样本地点密度/目标分布|分别声明E/R资格；密度用已定义base，不混stage行|统计描述，无预测情景|
|3|历史时段与研究流程|按冻结UTC边界画时间轴|只陈述回顾分期|
|4|同一参考人群下随gust的拟合log响应|每个模型以其B1估计人群、事件等权为reference；将所有行raw gust置同一v、pressure置训练均值p0，其余每行协变量保留；再统一design→η_i→meanη_i|主展示exp(meanη_i)，E仍含+1；同时存meanη、exp(meanη)、mean(expη)并清楚区分。旧物理区间禁止回填|
|5|按规定顺序的pooled OOF增量|来自同评价人群和fold的评分，不是客户曲线|没有协变量参考场景；顺序依赖明示|
|6|共同天气/客户情景下的地区差异|每LAD用相同参考calendar年/月分布；每条日历行只用该LAD对应year人口与静态区域值；raw天气固定训练均值，K固定训练mean ln(1+C)，由其反算C；design后客户z=0、square=0；对日历权重平均η|展示exp(加权meanη)，称共同日历参考；不是把fraction dummy当真实一个年月。只地图内跨LAD同参考，缺地区年度数据不任意补年|
|7|参考曲线上支持区间内max/min指数拟合比|gust沿图4；客户曲线另按同一人群每行置一致C网格、gust与pressure固定训练均值；每次先完整设计再平均η。50网格p1–p99来自相应训练驱动变量并记录具体范围|exp(maxmeanη−minmeanη)；不是η比或因果风险比，网格极值非连续全局极值|
|8|主/天气组边际OOF信息贡献|同基础目标/日期映射，各组评分对象清楚，分别保存事件|无平均协变量情景；组间差不是因果|
|9|历史风暴事件逐个拟合/观察值|真实每事件完整X→η；yE=log1pC，yR=logD；重叠window单列unique ID|η直接评分；样本内身份明确；留出误差留V阶段|
|10|分期/协方差描述比较|逐fit参数及scaler；固定物理单位参照时转换每fit；记录历史CV汇总和独立全fit身份|不得对重叠折套独立SE；旧Bootstrap区间不回填|
|D1|阶段层与客户分箱的D描述|公共客户分箱、各层/总体成员明确|不是场景预测，不宣称阶段控制识别因果|

图4保留人群平均目的，可在OLS线性预测器层与合格的均值设计等价；实现须逐行完整design验证这一等价，不能机械把所有平方列归零。图6固定客户中心情景与图4保留客户分布有不同含义，可保留但不能称同一参考。旧二者的恢复水平比约0.672957仅是H0设计层差异，不能直接带入B1。

所有图保存reference_population_hash、原变量设置、calendar_weights、scaler_hash、设计列、聚合顺序、预测量、支持区间及run_id。跨main/weather要比较同场景时另指定共同reference人群，禁止各自均值场景却称纯模型差。R03实现，R04生成；本轮没有新图或结论。
''')
history=[
('阵风系数稳定吗','legacy筛选事件，旧customers/duration；E0/R0折拟合','折间系数一致性探索；继承问题，不继承输入','archive'),
('后果是否形成离散群','legacy duration/customers二维聚类','未成为现稿主分析；不作分类机制证据','archive'),
('两个后果是否独立','legacy log1pC/log1pDuration依赖检验','继承双后果需分别定义的动机','archive'),
('控制客户后恢复阵风项怎样','legacy恢复加入log客户及平方','客户是事后协变量；保留规格来源，不沿用调度代理解释','archive'),
('扩样本能否再现模式','旧screening+expansion，系数CV','后续换v3；不能当独立新证据','archive'),
('数据聚合来源是什么','追filter/data_arrange/weather/LAD链','早期预筛选及字段含义考古；继承lineage','history'),
('能否完整重建事件','v2尝试C聚合/取消筛选，天气供应阻塞','保留失败记录；v2非最终数据','archive'),
('完整阶段v3怎样用','237901行保留，提出合并/筛选','继承只读v3与source_row；后续first-row问题未解决','migrate'),
('重定义C/A/B是否影响阵风','v3 E0和恢复A/B、客户控制；日期GroupKFold','选择B进入主线；天气仍继承选中源行，未按事件最早时刻修正','migrate'),
('样本变化还是目标定义变化','v3共同样本上naive/新C/A/B受控比较','两因素对照；沿用v9代表行天气；可存历史不混入修正结论','history'),
('二次曲线最低点在哪里','v3 E0和R0c_B；二次顶点/Bootstrap','只保留统计拟合最低点，physical threshold解释撤回','migrate'),
('原因组成是否影响曲率','六组→weather+technical；原因构成/子集','两组主样本选择历史；需声明事后选样','migrate'),
('恢复一次/二次项稳定性','两组R0c_B、折系数','历史支持线索；受新输入影响','migrate'),
('风和客户解释信息分别多少','两组恢复嵌套模型、日期OOF','实际pooled R²；贡献顺序依赖，需明确配对','migrate'),
('能否用锁定后期确认','全前序数据已触碰后期；发现污染停止','失败/污染历史必须保留，不叫未触碰holdout','history'),
('隔离后期后开发结果怎样','<2023-09-30开发；E48323/R47840；自算p99','重建开发是回顾隔离，不抹除选择历史','migrate'),
('客户与恢复为何非单调','开发C/B分箱/亚组/灵活形式','过程关联调查；不认定调度机制','migrate'),
('阶段数组成是否解释形状','开发按n_stages层、共同关系','事后阶段控制/分层仅描述；附录D继承','migrate'),
('后期能否再现','2023-09-30至2024-03-31；E12114/R11992；后期独立重拟合/自p99','自身拟合及方差解释，不是仅用开发模型真正预测未来','migrate'),
('旧地区地图到底画什么','v6地图/0519脚本方法回查','撤回风效应地域异质性误读，转地区基线','history'),
('合并研究的最终结果','开发+后期base60453；主E60437/R59834；重新合并p99','四类输出：OLS/顶点、OOF、曲线、地区地图；核心迁移','migrate'),
('客户变化量级','合并R0c客户曲线、指数预测范围','保留参考人群/尺度，不能把指数拟合当均值','migrate'),
('风暴案例哪些可定位','七命名风暴窗口、合并事件统计','保留窗口出处/重叠，不当七独立试验','migrate'),
('风暴拟合表现','合并模型在风暴事件预测/观察','样本内，旧暴露多log1p、恢复训练成员混合须修','migrate'),
('天气归因组信息贡献','weather子集E9857/R9758；独立p99与fold','排序点估计线索；48条差异和跨样本目标需修','migrate'),
('原因与gust支持关联','合并样本gust分位原因占比','支持描述不识别编码机制；附录G','migrate'),
('撰写前诊断是否齐','最终VIF、阶段、两向协方差等','部分输出缺独立生产者；不继承“无重大问题”口头认证','migrate'),
('能否反事实迁移天气效应','step30把子样本关系迁至总体','已明确放弃；不为保留故事重启反事实','archive'),
('核心数字统一','历史结果总账','当时总账不是当前权威；修正结果需版本化替换','migrate'),
('方法节样本/分布数字','合并样本描述补齐','输入变动后统一重算保留统计','migrate'),
('全六组恢复对照','六组独有R116064、p99/分折；两组比较','回顾样本敏感性，不能称共总体配对验证','migrate'),
('数据引用与实际一致吗','追溯人口/IMD/GVA/天气/地理引用','旧引用有一处与实际文件不一致；本轮溯源接续','history'),
('图形1/2/6生成','合并样本地图/分布/地区拟合','保留可追溯图producer，不把样式当证据','migrate'),
('地图样式修订','原图1/2/6视觉布局','只继承风格，不重复历史视觉探索','archive'),
('图1/2/6文字解释','已有图的描述','数值/对象由新图验证；原文不自动继承','archive'),
('替代分布是否改变结果','E原C：NB2 MLE、Tweedie p1.5 loglink；R原B：Gamma/Tweedie loglink','共设计的分布稳健性线索，不等于形状充分检验；需新输入重新估计保留结果','migrate'),
('主结果图4/5/7/8/9/10','读取现有step结果生成图','硬编码旧区间/评分名仍在；必须修consumer','migrate'),
('审稿数字/重定义与依赖','均值比、样本vs定义分解、非线性依赖','保留核实方法；修正输入影响的数值需重算','migrate'),
('公式/附录材料','A/B/C与阶段、聚类系数历史取材','实现层可复用；样本不同和业务语义继续核实','history'),
('三阶是否反驳二次充分性','合并模型加gust³及z空间对称性','E0旧OOF增量+.001441(约5.1%)是反向线索；R无有用增益。不得删除E不利证据','adverse'),
('补全数据字典与阶段资料','原字段/来源及附录D','后续按本轮源证据更新contract；不改稿','migrate'),
('共箱下阶段构成关系','最终R59834公共客户quartile，分层/合并D均值','附录图D1有实际producer；区别开发分箱表','migrate'),
('最低点/反变换/Bootstrap数学核实','交互顶点、重抽gust scaler、显示尺度、分期scaler','旧结果保留；缺β3/pressure配套、不合格旧CI不回填','migrate')]
idx=list(csv.DictReader((R/'results/code_audit_20260905/command_history_index.csv').open(encoding='utf-8-sig')))
rows=[]
for n,(q,d,decision,inherit) in enumerate(history,1):
    h=next(x for x in idx if int(x['command'])==n)
    rows.append(f"|#{n}|{q}|{d}|{decision}|{inherit}；LOG.md:{h['log_line']}|")
put('contracts/RESEARCH_HISTORY.md','# #1–#43 研究沿革与继承范围\n\n复用已接收的command_history_index.csv及代码核查报告，结合活动源码和本轮源数据检查；以下是历史追溯，不声称43项本轮重跑。完整脚本路径索引见原审计history CSV和本轮source_snapshots.json。\n\n主线：工程后果问题→旧筛选数据探索→v2失败与全阶段v3→C/A/B定义→原因限制和客户条件恢复→回顾分期→合并主线→天气子样本贡献→图表及审查。研究目标现收窄为记录事件的条件关联；“最终”“独立确认”等旧任务标题不决定证据地位。\n\n|命令|当时问题|数据/目标/方法|取舍与当前理解|继承范围/历史锚点|\n|---|---|---|---|---|\n'+'\n'.join(rows)+'''\n
范围说明：migrate指后续R02–R04保留的生产链/输出需要迁移，不表示本轮已迁移；archive保留存档不无目的重跑；history继承方法沿革但不把旧数值混入当前证据；adverse指必须保留、在新输入上再判断的反向线索。恢复D的历史p99与分期自拟合详见BASELINE_SPEC。旧v3天气代表行错误贯穿主线，不能将各命令复用同一输入的结果计为多个独立确认。输入修复影响成员/尺度/分折/输出，数值不可未经重算自动继承。
''')
put('contracts/UNRESOLVED_DEFINITIONS.md','''# 未决语义与最小缺件

R01可执行定义已完成；以下事项未被伪装为已核实。它们限定后续解释或个案处理，不阻止其余确定性R02工作。

|编号|未决项/范围|当前可执行规则|最小缺件/后续动作|对结论影响|
|---|---|---|---|---|
|U01|真实业务onset；所有事件|用earliest available stage start，business_onset=null|UKPN导出字段字典/事件报告时间、首阶段完整性说明|阵风只能称记录时间对齐，不能称真实故障时刻精确危险性|
|U02|两个ID的跨年、原因/阶段ID冲突|保留全记录及代理，identity/cause unresolved；分组单列|两ID的事件版本记录/是否复用和修订关系|不能声称188天连续停电；第二ID不能任意去重或C=2真值|
|U03|历史实际气象model和gust时间定义|历史请求未指定model、读取缓存product unknown|实际原响应metadata/产品ID或有日期的采集记录；只读SQLite可后续增量查|不得称已确定ERA5/标准3秒阵风；新请求需固定产品另做兼容|
|U04|所有缓存每小时有效性/缺失天气|精确小时+24有效雨值；缺失保留原因|R02全事件cache-only特征审查，本轮仅20定向行/14文件|不能根据本轮抽查宣布全体天气无缺失|
|U05|新Buckinghamshire真值|作者决定保留legacy proxy并标记，后续重建对照|LSOA边界/新LAD crosswalk、收入分母与空间权重；2021重组RUC来源|当前1151/1146主事件受proxy影响，区域机制解释受限|
|U06|Moran原空间权重细节|使用已发布旧LAD指标，权重unknown|源计算说明邻接/距离、行标准化、孤岛规则|不能声称已完全独立复现Moran；新LAD不可平均替代|
|U07|LAD21/23人口同码是否全可兼容|按事件year关联且留geography flag|相关代码官方边界crosswalk/匹配缺口表，R02针对改LAD/年度检查|同码不能证明同地理，区域控制解释有限|
|U08|停钟/视同恢复、零客户、真实过程完整|unknown不填0；D为记录跨度，零C不自删|UKPN导出特殊字段及适用年最终Annex F/报告包|D不自动等于连续断电、CI/CML或抢修工时；不能证明无删失|
|U09|数据开始前阶段是否缺失|本地raw→v3无丢行；源左边界可能不完整|下载范围/源年度返回规则/事件完整阶段清单|minstage≥2为疑似标志；首阶段存在也不保证真实onset|

所需作者决定目前仅U05的处置已收到；其余先用以上受限定义实现，不要求作者猜测源业务真值。R02后报告实际受影响成员；若未来坚持实时预测或全物理恢复含义，U01/U03/U08将成为该扩大目标的必要缺证。
''')
put('reports/R01_report.md','''# R01 完成报告

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
''')
put('DECISIONS.md','''# 决定记录

|ID|决定|来源/状态|后续影响|
|---|---|---|---|
|D00|本轮仅R00–R01，研究文稿不修改|用户明确；accepted|R02/R03/R04/V/W未授权本轮执行|
|D01|接收哈希一致H0，不重复80折拟合|v2计划及实际版本核实；accepted|旧结果仅历史，修正输入不能直接继承|
|D02|最早有效阶段起始作为记录时间代理；原因独立共识|R01证据支持的可执行定义；rule_defined|真实onset仍unknown，原因冲突单列|
|D03|Buckinghamshire保留为显式历史代理，后续LSOA重建并对照|用户2026-09-05回复“保留为代理，后续重建并对照”；accepted|不删1151主E事件；不能称新地区官方Moran/内部极差；后续重建未执行|
|D04|保留部分标准化、pooled OOF实际主指标；恢复共同基础、训练/测试尾部分离|R01范围内方法定义；rule_defined|不为匹配旧文字重标所有变量、不硬凑48或旧N|
|D05|图4人群平均η；图6固定天气客户+共同日历平均η|R01参考目的定义；rule_defined|R03实现统一接口并记录反变换顺序|
|D06|两个事件身份冲突保留原始行，不自行拆年或dedup|依据本次原始时间线；rule_defined|生成质量主表；原因限制分析单列未决；需UKPN源定义|
''')
base_c={
'C01':('代表阶段时间','T02/T03/T07/T08；L02/L03/L05/L08','rule_defined','reproduced_this_run','checks/event_semantic_checks.json；contracts/DATA_CONTRACT.md','R02/R04重算'),
'C02':('pooled与mean-fold','T06/T07/T09/T14；L07/L10/L12','rule_defined','verified_from_artifact','H0 oof_metric_comparison.csv；BASELINE_SPEC','R03/R04评分与图件'),
'C03':('独立p99/成员/fold','T04/T06/T07；L04/L07/L08/L11','rule_defined','verified_from_artifact','H0 source_and_sample_checks.json；BASELINE_SPEC','R03/R04共同口径'),
'C04':('暴露多log1p','T09/T14；L10/L12','rule_defined','verified_from_artifact','H0 storm_exposure_scale_audit.csv；BASELINE_SPEC','R03修代码/R04重算'),
'C05':('风暴训练成员与窗口','T04/T07/T09；L04/L08/L10','open','verified_from_artifact','H0 storm_recovery_membership_audit.csv','R03/R04成员接口；V过程留出'),
'C06':('部分标准化','T01/T11/T14；L01/L12','rule_defined','verified_from_artifact','H0 full_fit_summary.csv；FIELD_PROVENANCE','R03统一变换字典'),
'C07':('图形参考与反变换','T09/T14；L10/L12','rule_defined','verified_from_artifact','H0 curve_reference_audit.json；FIGURE_REFERENCE_CONTRACT','R03/R04实际接入'),
'C08':('旧区间/标签回填','T10/T11/T14；L09/L12','open','verified_from_artifact','冻结figure4/figure10/step43源码与H0报告','R03关闭旧回填；V03条件区间'),
'C09':('副作用/环境/缺生产者','T01/T03/T11/T14；L01/L05/L12','rule_defined','reproduced_this_run','inventory/runtime_verified.json；ACTIVE_PIPELINE','运行边界已定义，R03补生产者'),
'C10':('Buck旧区简单均值proxy','T01；L01','rule_defined','reproduced_this_run','checks/buckinghamshire_lineage.json；D03','按作者保留代理、后续LSOA重建对照')}
t_names=['区域源定义及VIF','气象产品/时间匹配','事件与特殊阶段','长尾敏感性','非线性形状','配对贡献稳定性','完整过程留出','信息时点','工程场景/误差','条件最低点区间','诊断及既有材料','可选异质性增强','可选扩大用途','文稿整合']
l_names=['区域变量矛盾','气象/结构风解释','事后客户信息','最长1%与极端叙事','后果工程语义','二次充分性','排序反转稳定性','风暴依赖','最低点区间条件','风暴误差/校准','原因/支持/异质性','全文证据一致性']
issues=[]
for k,(title,related,repair,ev,source,nextstep) in base_c.items():issues.append({'id':k,'title':title,'related':related,'execution_status':'completed' if k in ['C01','C06','C07','C09','C10'] else 'not_started','execution_scope':'R00/R01 definition/intake only','repair_status':repair,'evidence_source':ev,'evidence':source,'remaining':nextstep})
for prefix,names in [('T',t_names),('L',l_names)]:
    for i,title in enumerate(names,1):
        definition=i in ([1,2,3,8] if prefix=='T' else [1,2,3,5])
        issues.append({'id':f'{prefix}{i:02}','title':title,'related':','.join(k for k,v in base_c.items() if f'{prefix}{i:02}' in v[1]),'execution_status':'completed' if definition else 'not_started','execution_scope':'R01 definition part only' if definition else 'future experiment/review','repair_status':'rule_defined' if definition else 'open','evidence_source':'verified_from_artifact' if definition else 'reported_by_local_audit','evidence':'contracts/ + H0 artifacts' if definition else 'handoff ISSUE_MAP and historical review; not a new experiment','remaining':'科学缺口未整体关闭；按R/V/W阶段执行'})
jput('issue_ledger.json',issues)
put('ISSUE_LEDGER.md','# C/T/L问题总账\n\n执行completed仅指表中本轮范围完成；repair_status=rule_defined不是code_patched或recomputed。未关闭科学问题。C01–C09/T01–T14/L01–L12完整保留，C10为本轮新增。逐行结构见issue_ledger.json。\n\n|编号/主题|关联|执行范围/状态|修复状态|证据来源|证据/余项|\n|---|---|---|---|---|---|\n'+'\n'.join(f"|{x['id']} {x['title']}|{x['related']}|{x['execution_scope']} / {x['execution_status']}|{x['repair_status']}|{x['evidence_source']}|{x['evidence']}；{x['remaining']}|" for x in issues)+'\n\n全局缺失清单见UNRESOLVED_DEFINITIONS；这些源真值的证据来源为not_available，不能用程序一致替代。T01精确共线旧猜测已排除，不删除该历史问题，也不预设删gap。\n')
put('checks/RUN_LOG.md','''# 执行日志

2026-09-05 R00：code/r00_intake.py；42产物读取、549保护比对、91源码快照、raw/v3各一次SHA、稿件比对、依赖导入成功。write_r00.py写阶段报告，R00 completed后进入R01。

R01：r01_targeted_checks.py第1次在只读openpyxl空单元格式读取处报AttributeError: EmptyCell has no coordinate；已修为仅访问有coordinate单元，重跑成功。因该失败重读一次v3选定列，未重跑模型、未修改源数据。openpyxl发出Sparkline扩展不支持警告；全程read_only且未save/export源工作簿，不发生原文件转换。保护哈希在结束验证。

探索性读取曾遇到错误假设目录project_memory在分支内，实际在父目录；已改读真实文件。两次未来prompt文件名不符，已list后读取真实路径。rg通配路径错误改用实际目录；这些未影响结果。网页ONS /2019与UKPN API未能读取，ONS改从真实dataset链接读取；UKPN完整字典仍标not_available，没有以失败代替完整核实。

天气只读20定向源行/14pkl，不打开CachedSession、不请求新天气、不运行旧模块。本轮源资料浏览仅官方页面和官方PDF语义查询；2020/2023文档版本限制保留。完整stdout诊断已经落在checks结构文件，不仅存在会话中。

write_r01.py生成方法报告/规则/研究历史/状态。finalize_checks.py执行交付完整性和文件保护复核、JSON标准化、生成最终SHA清单。所有新文件只在paper_revision_work_v2。
''')
put('RETURN_TO_CHATGPT.md','''# R00–R01 返回摘要

2026-09-05。本轮已按v2计划完成R00审计接收与R01数据/方法契约，停在R01。未修改论文、历史代码/结果或外部数据，未执行R02–R05/V/W，也没有修正模型数值。

R00：42审计文件实际读取，原manifest校验一致；549受保护历史文件无变化；raw与v3本轮SHA和H0相同；本地最新两Word与交接包一致。91源码快照和可用Python3.12.14科学依赖已核验。H0四模型/80折拟合复用不重跑。

H0主E0/R0c=60437/59834，天气=9857/9758。主E0有8199例（13.566%）首行比最早阶段晚；独立天气p99多排48条是旧比较配置问题，不能把恢复旧N作为新目标。

本次新增定位：
- 极端FREP-338321-Z跨2022-11-04与2023-05-11，首行晚4506.366667h，cause98/71、MEI59/41、跨监管年度；按旧ID公式B4508.933333h/C1。不是已核实188天连续失电，最早行还缺天气。保留记录、标事件身份/原因未决，不自动拆分或据极值删除。
- FREP-314454-J的两行共用stage1和unique_identifier，原因71/87不同；不能dedup当完全重复。全源完全重复行0。
- 24893事件最早时刻并列，6项metadata冲突均0；用冻结raw SHA+原行号稳定选取。所有时间带偏移，+01有128323行/+00有109578行；未发现无效起止或end<start。2024-04边界35事件跨恢复，保留窗外末阶段。
- 原gap是LAD内LSOA rate极差，存储比例（如.217=21.7个百分点）；Moran为LAD内LSOA聚集。Buckinghamshire实际4旧区简单平均rate .06325/gap .1875/Moran .30，影响H0主E1151/主R1146、天气293/292。作者已决定保留为显式历史代理，后续LSOA重建并对照；本轮未重建。
- 20定向天气行中16有缓存/14文件，样例24有效降水和精确小时通过；4行缺缓存，attrs全部空。历史请求没指定models；不能确定历史产品，更不能把当前默认产品追认历史。全量有效性待R02。

R01已产出#1–#43研究沿革、字段/原因/时间/天气/区域契约、baseline配置和各图参考顺序。全阶段最早记录时间是代理而非真实onset；原因独立共识，年度人口重关联；C排重复空集合缺失，D=B；部分标准化保持、pooled OOF准确命名；主/天气共同恢复基础，训练尾部与测试总体分开；曲线/地图分别明确人群平均与固定情景。

真实onset、两ID身份、历史model、停钟/视同恢复字段、Moran空间权重仍未核实，范围/最低缺件见contracts/UNRESOLVED_DEFINITIONS.md。它们不阻止其余确定性输入修复，但限定科学解释。E0旧三阶OOF增量约.001441保留为反向线索，不能因修时间便删除或继续沿用旧数值。

下一步仅在作者发出后续指令后执行R02：按contracts生成带完整源行/质量/旧新变化的事件输入、重取最早小时缓存、更新年人口、样本流及针对性检查；仍不改稿。R01完成不代表C01–C10代码已修复，更不代表论文科学结论已验证。

交付入口：reports/R00_report.md、reports/R01_report.md；细则在contracts/，证据在checks/，版本/写入范围在inventory/；ISSUE_LEDGER/RUN_STATE/ARTIFACT_MANIFEST保存进度和可追溯性。
''')
state=json.loads((O/'RUN_STATE.json').read_text(encoding='utf-8'))
state.update(active_stage='R01',last_updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline='H0_accepted_no_R1_or_B1_run')
state['stages']['R01'].update(execution_status='completed',report='reports/R01_report.md',inputs=['reports/R00_report.md','inventory/large_input_identity.json'],outputs=['contracts/','checks/','reports/R01_report.md'],blockers=[],unresolved_definitions='contracts/UNRESOLVED_DEFINITIONS.md')
state['invalidated_outputs']=[{'scope':'All retained H0 model/OOF/figure numerical outputs depending on first-row input','status':'historical_only_not_valid_for_corrected_input','reason':'C01 repair not run; preserve H0 and recompute dependent outputs in R04'}]
jput('RUN_STATE.json',state)
put('STATUS.md','# 阶段状态\n\nR00 completed；R01 completed；R02–R05、V00–V04、W00–W01均not_started。当前H0已接收，R1/B1不存在。\n\n规则已定义，活动生产代码未修，模型未重估；源真值未决见contracts/UNRESOLVED_DEFINITIONS.md。作者已决定Buckinghamshire保留proxy、后续LSOA重建并对照。下一步等用户指定R02。\n')
# Correct the intake table against the actual current Figure 5 caption (OOF increments).
p=O/'inventory/ACTIVE_PIPELINE.md';s=p.read_text(encoding='utf-8')
s=s.replace('|图5客户曲线|step7_customers_dose_response.py、figure5*|均值设计；客户平方要连动|按同一参考人群完整设计后平均|','|图5贡献分解|figure5_variance_decomposition.py；step2_critical_wind_and_variance.py|嵌套顺序增量与pooled OOF，标签仍称mean|统一评分成员/分母与命名|\n|客户曲线及图7客户范围|step7_customers_dose_response.py|均值设计；客户平方要连动|按同一参考人群完整设计后平均|')
put('inventory/ACTIVE_PIPELINE.md',s)
print('R01 reports, contracts, history, decisions and state written')
