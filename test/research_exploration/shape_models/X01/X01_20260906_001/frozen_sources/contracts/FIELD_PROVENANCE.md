# 字段来源表

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
