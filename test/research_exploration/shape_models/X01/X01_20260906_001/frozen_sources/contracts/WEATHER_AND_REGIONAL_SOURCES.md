# 天气与区域来源核实

## 天气：实现证据与产品语义分开

实际链是 `rebuild_v3_full_stage/scripts/weather_cached_chunk_v3.py`→`main1_v3.py`；原`main1.py`历史API请求使用archive端点、hourly数组、wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT，没有models。历史请求key为一位小数坐标与UTC日期。v3对每个阶段floor小时抽取，#9/#10及后续事件分析继承这些天气列、再按源第一行代表事件，不是按新C/B自动重新匹配。

本轮定向20行（极端、原因冲突、最高gust、DST附近和普通样例），16行有缓存，涉及14个pkl；4行缺缓存。缓存内可用样例均有精确小时、24个有效非负降水值；无重复小时。所有读取pkl的DataFrame attrs为空，只有小时列，没有可确认历史实际model的标识。本轮没有全面扫所有缓存/全量有效雨值，也没有解码所有SQLite历史响应；不能据14文件推断全部历史产品一致。文件SHA记录在weather_cache_read_hashes.json。

原始时间保留+01/+00，UTC转换不依赖推断DST。例如源行1原10:32+01→09:32Z→09:00Z；2023-10-29附近源行2794为01:01+00→01:00Z。2021春季DST在数据起点之前，本次选到的是数据首日附近记录，不能算覆盖那个转换日；其余案例逐条见weather_case_checks.json。极端最早源行163320缺对应51.8_1.2_2022-11-04缓存，不能后移到有天气的2023行。

当前官方定义将precipitation记为前一小时累计；floor后使用h−23h…h共24端点，物理累计覆盖(h−24h,h]，实际代理起始晚于h的0–59分未覆盖。降雨值全部有限与24行齐全是两个条件；旧sum跳过NaN可能掩盖缺失。官方gust字段为10m所示小时值，部分产品有特定前一小时最大值含义；历史models未确定，因此不把它写成已确认的ERA5产品或标准3秒峰值。[Open-Meteo小时定义](https://open-meteo.com/en/docs/historical-weather-api)

本次确认的是请求单位m/s、mm、GMT和缓存数值继承，不是每个产品精度或再分析无未来信息。0.1°是请求舍入/缓存分组，不能当实际格网间距。按真实故障onset“绝无未来天气”的判断仍受代理起始和产品语义限制。修复先保留历史产品身份unknown，不用2026默认产品静默填缺；如要新请求，需单独产品固定和兼容对照。

## 地区：已读原工作簿与实际旧lookup

原文件 `D:\Pyprogramme\STST2603\data\localincomedeprivationdata.xlsx` 的Notes与Rankings for all indicators已读取。收入剥夺率是LSOA人口加权的LAD整体rate；gap是同LAD最高减最低LSOA rate；Moran描述LAD内LSOA空间聚集，不是相邻LAD之间聚集。Notes给出基础shapefile但未指定完整权重矩阵、邻接/距离、标准化和孤岛处理，本轮不编造这些细节。[ONS数据来源页](https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/mappingincomedeprivationatalocalauthoritylevel)

数值单位实例：Adur gap单元H3=0.217，Excel格式0.0%，即21.7个百分点；L3 rate=0.108即10.8%。当前脚本保留0–1比例尺度，未乘100；系数解释不能把1单位误当1个百分点。主矩阵满秩、gap非精确仿射接受为H0证据，按源定义也不应预设删gap。

实际继承：Buckinghamshire_combination.py读Rankings与2021人口→data/new/ukpn_master_with_income_deprivation_crosswalk.csv；v3 enrich_downstream_v3.py把旧主表按LADCD取唯一lookup再left merge，没有从原LSOA重算。GVA_new.py读regionalgvabbylainuk.xlsx的2016列→gva_industry_2016.csv；GVA_merge_with_crosswalk.py→data/new/ukpn_master_final.csv；v3同样按LADCD借用。人口源myebtablesuk20112024.xlsx的MYEB3生成population_lad_long.csv。两个源工作簿标题/表单亦本轮读取，见other_workbook_sources.json。GVA当前不在E0/R0c设计中，不因此扩展模型。

## Buckinghamshire新增实证发现（C10，对应T01/L01）

合并前4区E07000004/5/6/7的2021人口在所用LAD23长表中无对应行，所以旧代码退化为简单平均：rate=(.067+.053+.057+.076)/4=.06325；gap=(.196+.216+.134+.204)/4=.1875；Moran=(.47+.29+.02+.42)/4=.30。与v3新代码E06000060值一致。此处不是人口加权，也不是新地区的真实内部极差或重新计算Moran。来源文件名validated不能消除这一方法限制。

影响源事件2313；H0主E0 1151、主R0c1146、天气E0 293、天气R0c292。作者本轮明确选择“保留为代理，后续重建并对照”。规则：保留样本和现值，逐事件/地图标proxy，后续以冻结LSOA边界/权重重建新地理指标并与历史proxy比较；不自动删除该LAD、不重算本轮模型。均值proxy的区域系数解释暂收窄。GVA旧crosswalk亦需按保留用途检查，不能把金额类可加性等同Moran可平均性。

## 源字段语义边界

Ofgem区分事件开始与阶段起始；阶段客户是该阶段恢复网络部分的客户；同一事件可有临时供电/重复中断。[ED1阶段说明§2.34–2.41](https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf)。ED2在线v1.1材料亦区分阶段、停钟及视同恢复；本次取得的是2023年10月咨询附件，用于语义交叉核对，不能替代全研究期最终版适用性核验。[ED2相关章节](https://www.ofgem.gov.uk/sites/default/files/2023-10/RIIO-ED2%20-%20Annex%20F%20Interruptions%20v1.1.pdf)

原20列没有明确停钟起止/视同恢复字段、事件修订号、初始客户真值；这些业务事实not_available。UKPN在线页面已重定向，当前工具未取得完整数据字典/API元数据，portal用途描述主要复用本地data_source_inventory.md的来源记录。不得声称本次已逐项核实官方导出字典。后续最小缺件而非阻断所有计算。
