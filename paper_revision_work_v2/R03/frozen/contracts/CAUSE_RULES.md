# 原因与特殊事件规则

六组码表机器版见 cause_group_map.json，直接AST读取冻结v3 classify_cause_code的字面映射，未import。该函数列名虽叫cause_group_official，六组合并是项目分析分类，不能称监管官方六组。原Ofgem码与作者合并层分开保留。

|事件|本次原始行证据|解释边界与可执行处置|
|---|---|---|
|FREP-338321-Z|原行163320：stage1，2022-11-04 16:44–17:10Z，C_s=0，cause98，MEI59，2022-23；原行89486：stage2，2023-05-11 11:06–13:40Z，C_s=1，cause71，MEI41，2023-24。站点/坐标一致|旧首行晚4506.366667h；按ID公式B=4508.933333h，C=1。两段不连续；无法判定ID复用、修订残留或其他业务情形。不是已证实持续188天停电。flag identity/cause unresolved；记录表保留；不擅自合并语义或按年拆分|
|FREP-314454-J|原行147106：stage1，2023-03-24 19:27Z–04-05 10:50Z，C_s=1，cause71，MEI51；原行94432：stage1，2023-04-05 08:23–10:46Z，C_s=1，cause87，MEI90；同unique_identifier FREP-314454-J1、不同年度|不是完全重复行，不能dedup；按ID客户加总可能含修订/重复，但本轮无依据判定。flag identity/sourceID/cause unresolved；C/D标记provisional，正式原因样本单列|

码71为老化/磨损（不含腐蚀），98为原因未分类，87为孤立系统本地发电失效；参见[Ofgem Annex F Appendix 5](https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf)。2020在线文件呈修订版标记，本轮用来交叉核对语义，不冒称已锁定每个监管年的最终规则版本。

最早天气选择不改变原因来源规则。共识原因使用所有阶段；“最后时间行”不是“最终诊断记录”。继续原因码也不能未经业务依据覆盖主cause。R02输出缺失/冲突全集及原码分布，主样本只接纳共识映射到weather_natural/technical_asset者；六组比较保留相同未决策略。

最小源缺件：两ID的UKPN事件级版本/修订标识、是否跨年复用及正式起始/结束。未获得前保留上述受限身份；不把源缺件阻塞其余135023 ID的确定性规则实现。
