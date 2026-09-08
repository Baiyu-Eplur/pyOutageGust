# 信息可用时间表

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
