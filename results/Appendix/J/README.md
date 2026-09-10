# 附录 J：地区日方法与验证

最近生成：2026-09-10T13:17:12+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices J`；项目根目录以脚本位置解析。

ERA5聚合/持续性与正文proxy时间检验分开。八项时间BSS均为正，但校准和月度偏差保留；无新的通过阈值。

## 关键结果摘要

- DD-TIME01 any_gt100：BSS=0.0302875862；平均预测减发生率=-0.21381863概率百分点。
- DD-TIME01 wthr_gt100：BSS=0.0750236326；平均预测减发生率=-0.17158062概率百分点。
- any_gt100模型Brier劣于开发常数的月份：2024-02。九月只有30日一天；月度拆分并非独立重复验证。
- wthr_gt100模型Brier劣于开发常数的月份：2024-02。九月只有30日一天；月度拆分并非独立重复验证。
- 时间八任务BSS均为正，但所有任务总体平均预测低于实际；校准图保留所有非空既定箱。不能等同于所有风险层或月份校准准确。
- DD-AGG01 any_gt100，既有Brier：A01_daily_max=0.0560104363；A02_daily_mean=0.0563327112；A03_daily_q90=0.0561051821；A04_top3_mean=0.0560352197；A05_max_rolling3h_mean=0.0560343489。仅作同实验同任务比较。
- DD-AGG01 wthr_gt100，既有Brier：A01_daily_max=0.0189854173；A02_daily_mean=0.0193135893；A03_daily_q90=0.0190876825；A04_top3_mean=0.0190139439；A05_max_rolling3h_mean=0.0190129813。仅作同实验同任务比较。
- DD-AGG01 any_gt1000，既有Brier：A01_daily_max=0.0082334901；A02_daily_mean=0.0082764973；A03_daily_q90=0.0082351547；A04_top3_mean=0.0082288102；A05_max_rolling3h_mean=0.0082281713。仅作同实验同任务比较。
- DD-AGG01 wthr_gt1000，既有Brier：A01_daily_max=0.0024748567；A02_daily_mean=0.0025174920；A03_daily_q90=0.0024852773；A04_top3_mean=0.0024742581；A05_max_rolling3h_mean=0.0024734702。仅作同实验同任务比较。
- DD-DUR01 any_gt100，既有Brier：M0=0.0560104363；M1=0.0560112976；M2=0.0560188085。仅作同实验同任务比较。
- DD-DUR01 wthr_gt100，既有Brier：M0=0.0189854173；M1=0.0189857351；M2=0.0189881394。仅作同实验同任务比较。
- DD-DUR01 any_gt1000，既有Brier：M0=0.0082334901；M1=0.0082352357；M2=0.0082303183。仅作同实验同任务比较。
- DD-DUR01 wthr_gt1000，既有Brier：M0=0.0024748567；M1=0.0024750495；M2=0.0024731295。仅作同实验同任务比较。

## 需求、产物与适用范围

### J01 — 构造定义与现有面板标签数量

已生成。正文定位：§3.5 P042–043; §4.4 P070–072。当天事件坐标均值中心、40km Gaussian/distance插值，非ERA5日最大；任意事件包含零客户，其他阈值严格>且为至少一个事件。只读定义和标签，不审计历史拟合。

- [tables/J_PROXY_DEFINITIONS.csv](tables/J_PROXY_DEFINITIONS.csv)

- [tables/J_PROXY_DEFINITIONS.md](tables/J_PROXY_DEFINITIONS.md)

- [tables/J_PROXY_LABELS.csv](tables/J_PROXY_LABELS.csv)

- [tables/J_PROXY_LABELS.md](tables/J_PROXY_LABELS.md)

### J02 — 既有覆盖和天气数值比较

已生成。正文定位：v9 §3 J.2；§5.5 P089的已接受补充。覆盖/天气数据可复用；不导入P03历史模型排名或旧置信区间。再分析值不是气象站真值，也非LAD全域最大。

- [tables/J02_GUST_COMPARISON.csv](tables/J02_GUST_COMPARISON.csv)

- [tables/J02_GUST_COMPARISON.md](tables/J02_GUST_COMPARISON.md)

- [tables/J02_GRID_CELLS.csv](tables/J02_GRID_CELLS.csv)

- [tables/J02_GRID_CELLS.md](tables/J02_GRID_CELLS.md)

- [tables/J02_CENTROIDS.csv](tables/J02_CENTROIDS.csv)

- [tables/J02_CENTROIDS.md](tables/J02_CENTROIDS.md)

- [tables/J_INDEPENDENT_WEATHER_DEFINITIONS.csv](tables/J_INDEPENDENT_WEATHER_DEFINITIONS.csv)

- [tables/J_INDEPENDENT_WEATHER_DEFINITIONS.md](tables/J_INDEPENDENT_WEATHER_DEFINITIONS.md)

### J04 — 八任务五候选完整指标与既有配对区间

已生成。正文定位：v9 §3 J.3 / §4.3成果登记。仅在本实验同任务候选内比较；不把不同评估集Brier或不同分箱校准RMSE跨实验排名。

- [tables/J04_METRICS.csv](tables/J04_METRICS.csv)

- [tables/J04_METRICS.md](tables/J04_METRICS.md)

- [tables/J04_PAIRED_UNCERTAINTY.csv](tables/J04_PAIRED_UNCERTAINTY.csv)

- [tables/J04_PAIRED_UNCERTAINTY.md](tables/J04_PAIRED_UNCERTAINTY.md)

- [tables/J04_AGGREGATION_SUMMARY.csv](tables/J04_AGGREGATION_SUMMARY.csv)

- [tables/J04_AGGREGATION_SUMMARY.md](tables/J04_AGGREGATION_SUMMARY.md)

### J05 — 八任务三模型指标、阈值、既有配对区间

已生成。正文定位：v9 §3 J.4 / §4.3成果登记。H为超阈小时计数，不是最长连续时长；平方累计非结构损伤测量。保留稀有任务微小正向结果。

- [tables/J05_METRICS.csv](tables/J05_METRICS.csv)

- [tables/J05_METRICS.md](tables/J05_METRICS.md)

- [tables/J05_PAIRED_UNCERTAINTY.csv](tables/J05_PAIRED_UNCERTAINTY.csv)

- [tables/J05_PAIRED_UNCERTAINTY.md](tables/J05_PAIRED_UNCERTAINTY.md)

- [tables/J05_THRESHOLDS.csv](tables/J05_THRESHOLDS.csv)

- [tables/J05_THRESHOLDS.md](tables/J05_THRESHOLDS.md)

### J06 — 八任务开发/评估率、平均偏差、Brier/BSS与支持表

已生成。正文定位：v9 §3 J.5；§4.5 已接受新增。回顾性，评估期此前参与探索；事后proxy构造下跨期迁移，不是提前预警。开发期参数不可替换正文全期参数。

- [tables/J_TIME_METRICS.csv](tables/J_TIME_METRICS.csv)

- [tables/J_TIME_METRICS.md](tables/J_TIME_METRICS.md)

- [tables/J_TIME_MONTHLY.csv](tables/J_TIME_MONTHLY.csv)

- [tables/J_TIME_MONTHLY.md](tables/J_TIME_MONTHLY.md)

- [tables/J_TIME_SUPPORT.csv](tables/J_TIME_SUPPORT.csv)

- [tables/J_TIME_SUPPORT.md](tables/J_TIME_SUPPORT.md)

- [tables/J_TIME_DEVELOPMENT_FIT.csv](tables/J_TIME_DEVELOPMENT_FIT.csv)

- [tables/J_TIME_DEVELOPMENT_FIT.md](tables/J_TIME_DEVELOPMENT_FIT.md)

### J07 — 全体>100与天气>100校准/月度四面板及八任务既定箱数据

已生成。正文定位：v9 §5 图形呈现。2023-09只有9月30日一天，不与完整月份等量解释；稀疏箱不连成尾部趋势。显示轴覆盖全部非空箱均值，1.15倍最大值向上取0.05整倍数；仅排版，不重分箱。

- [tables/J_TIME_CALIBRATION_BINS.csv](tables/J_TIME_CALIBRATION_BINS.csv)

- [tables/J_TIME_CALIBRATION_BINS.md](tables/J_TIME_CALIBRATION_BINS.md)

- [figures/J_TIME_CALIBRATION_MONTHLY.png](figures/J_TIME_CALIBRATION_MONTHLY.png)

### J08 — 方法/用途/不可支持解释的简明登记

已生成。正文定位：v9 §3 J.6；§5.5 P089。不声称等效、统计显著或完全校准；不自动提出模型替换。

- [tables/J_INTERPRETATION_BOUNDARIES.csv](tables/J_INTERPRETATION_BOUNDARIES.csv)

- [tables/J_INTERPRETATION_BOUNDARIES.md](tables/J_INTERPRETATION_BOUNDARIES.md)

- [tables/J_FROZEN_EXPERIMENT_DEFINITIONS.csv](tables/J_FROZEN_EXPERIMENT_DEFINITIONS.csv)

- [tables/J_FROZEN_EXPERIMENT_DEFINITIONS.md](tables/J_FROZEN_EXPERIMENT_DEFINITIONS.md)

### J09 — 关闭事项登记

用户已关闭。正文定位：研究负责人关闭决定；v9 §1；P074/P089仅作关闭定位。

用户明确停止或未授权；不作为本轮生产的待执行门槛。

### J10 — 关闭事项登记

用户已关闭。正文定位：研究负责人关闭决定；v9 §1；P074/P089仅作关闭定位。

用户明确停止或未授权；不作为本轮生产的待执行门槛。

### J11 — 关闭事项登记

用户已关闭。正文定位：研究负责人关闭决定；v9 §1；P074/P089仅作关闭定位。

用户明确停止或未授权；不作为本轮生产的待执行门槛。

### J12 — 关闭事项登记

用户已关闭。正文定位：研究负责人关闭决定；v9 §1；P074/P089仅作关闭定位。

用户明确停止或未授权；不作为本轮生产的待执行门槛。

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。

## APP-J03-COMPARE

# APP-J03-COMPARE 第一工作包执行与回传报告

完成记录：2026-09-10T16:52:00+01:00。状态：产物已输出，待研究负责人反馈分析；未科学关闭。

## 任务与实际执行

本包只比较正文同日事件锚点PROXY与既下载ERA5小时阵风的日最大GRID_MAX。二者是天气暴露构造方案的整体对照；不把任何一方称为真值，不分解位置/聚合/获取方式的独立作用。

两来源按同一LAD-day键逐一对应：111 LAD、1096 UTC日、121656行、八标签，五折直接复用DD-AGG01保存分配。没有静默取交集、填零、换标签、换时区或请求天气。gt0为任意事件并保留零客户，其他阈值严格>，不是当天客户求和。

目标96组件全部有记录：16全样本、80训练折。该结果集来源动作：{'REFIT': 48, 'REUSE': 48}；有效96/96，弱识别标记0。GRID_MAX复用前核对RULES、训练行数/阳性数、稳定目标函数、梯度及已评价初值/终点最小值；不是仅检查success。

全样本参数仅用于附录描述；OOF概率逐折由对应训练参数生成，常数概率是该训练折发生率。未使用全样本参数生成OOF。当前每次调用是否命中缓存和新拟合次数另记logs/J03_LAST_EXECUTION.json；复用导出不重新计算科学结果。

## 评价口径

Brier按地区日等权池化。ΔBS=BS_PROXY−BS_GRID_MAX，正值表示GRID_MAX误差更低；相对改善=100×ΔBS/BS_PROXY，单位是相对百分比，不是概率百分点。BSS相对于两方案共同的训练折常数预测。

配对区间重新使用当前OOF：整LAD有放回抽样1000次、seed=20260909，两来源和八任务共享抽样，按每次抽中地区日数量池化。它是固定OOF的条件区间，不包含重训、选择和跨LAD共享风暴日期的全部不确定性；没有拼接旧P03区间。

共同校准规则在拟合前冻结：每任务两来源有效OOF概率合并取0–1十分位数，补0/1并去重；规则不读标签决定箱边界，side=right。每箱保存n和阳性，空箱频率为NA，n<100标为稀疏；没有事后调箱。

## 八任务完整结果

|任务|PROXY Brier|GRID_MAX Brier|ΔBS|相对改善 %|配对ΔBS 95%条件区间|PROXY BSS|GRID_MAX BSS|
|---|---|---|---|---|---|---|---|
|any_gt0|0.2239128365|0.2238693497|0.0000434868|0.019421|[-0.0002247168, 0.0002877561]|0.00927509|0.00946750|
|any_gt5|0.1372953091|0.1372253143|0.0000699948|0.050981|[-0.0000954721, 0.0002304919]|0.01217808|0.01268169|
|any_gt100|0.0559632708|0.0560104363|-0.0000471655|-0.084279|[-0.0001382098, 0.0000441996]|0.01659749|0.01576868|
|any_gt1000|0.0081984701|0.0082334901|-0.0000350200|-0.427153|[-0.0000577333, -0.0000114565]|0.01393378|0.00972178|
|wthr_gt0|0.0452936341|0.0453053327|-0.0000116986|-0.025828|[-0.0001722549, 0.0001608336]|0.05252157|0.05227686|
|wthr_gt5|0.0331111136|0.0331368006|-0.0000256870|-0.077578|[-0.0001446123, 0.0001040677]|0.04908766|0.04834996|
|wthr_gt100|0.0189333388|0.0189854173|-0.0000520785|-0.275062|[-0.0001369352, 0.0000339717]|0.04894564|0.04632965|
|wthr_gt1000|0.0024452928|0.0024748567|-0.0000295639|-1.209015|[-0.0000490967, -0.0000105613]|0.04408851|0.03253140|

主要任务为any_gt100，重要次级为wthr_gt100。其余六项全部列出；表格记录差异方向和幅度，不设置通过/失败或主模型更换门槛。总体发生率、平均预测及偏差见J03_PAIRED_METRICS；逐折n/阳性/常数/差异见J03_FOLD_METRICS。

## 与正文已存PROXY结果的直接对照

仅对照本轮同一全样本的新参数与正文已存lognormal参数，并比较二者在同批输入上的描述性概率；不重新拟合旧模型、不审计旧支持上限/g50。下表中变化供研究负责人判断对原参数和文字的影响，未自动改写正文。

|任务|旧θ→新θ|旧β→新β|旧p0→新p0|新NLL−旧NLL|最大绝对概率差|
|---|---|---|---|---|---|
|any_gt0|22.617884 → 22.618016|0.43694735 → 0.43695547|0.31914219 → 0.31914192|-9.4514689e-08|5.2632114e-06|
|any_gt5|23.933084 → 23.93319|0.36224016 → 0.36224309|0.15106376 → 0.15106367|-3.4364348e-08|4.7864213e-06|
|any_gt100|25.081599 → 25.081616|0.29127763 → 0.29127808|0.053124959 → 0.053124958|-7.9307938e-10|9.8974322e-07|
|any_gt1000|30.398417 → 30.398258|0.24393004 → 0.24392443|0.0073129559 → 0.0073130171|-1.017479e-07|3.3313597e-06|
|wthr_gt0|23.124734 → 23.124743|0.33010075 → 0.33010103|0.033569779 → 0.033569769|-4.3655746e-10|5.2563212e-07|
|wthr_gt5|24.2439 → 24.243944|0.32123636 → 0.3212372|0.023860735 → 0.023860762|-1.3631507e-08|2.3794272e-06|
|wthr_gt100|25.365693 → 25.365699|0.2902434 → 0.29024357|0.013155234 → 0.01315523|-1.2914825e-10|3.5820149e-07|
|wthr_gt1000|31.793685 → 31.79369|0.27062316 → 0.27062329|0.0014287518 → 0.0014287509|-6.5938366e-11|8.7865668e-08|

## 必要技术检查与异常

logs/J03_TECHNICAL_CHECKS.json保存匹配、训练/测试边界、合法概率、有效拟合诊断、逐行评分复算、同抽样区间复算及分箱计数检查；logs/J03_PRESERVATION.json记录其他J管理文件的逐文件保留。有效性与弱识别分别保存，不把运行完成解释为科学结论成立。

无效组件：无。

此前发布尝试错误：KeyError: 'grid_max_brier'。此前失败未发布的拟合不计入上表当前结果集的组件动作；跨尝试执行事实见项目LOG.md。

## 复现、文件与回传用途

项目根目录执行：`python -X utf8 -B main_appendix.py --appendices J --j03-only`。普通运行核验有效缓存；强制本包重算：增加`--recompute-j03`，仍使用同一96组件和冻结预算。只读预检：增加`--check-only`。

固定目录：results/Appendix/J/。tables/J03_*为完整精度CSV和阅读版；data/J03_MATCHED_PANEL.csv.gz、J03_FIT_COMPONENTS.jsonl、J03_OOF_PREDICTIONS.csv.gz、J03_BOOTSTRAP_DRAWS.csv.gz及LAD顺序保存底层结果。figures/J03_PRIMARY_CALIBRATION.png为两个重点任务校准图，J03_BRIER_COMPARISON.png为八任务评分/配对区间图。

logs/J03_PROTOCOL.json为冻结协议和来源/代码指纹；J03_INPUT_MATCH.json为匹配记录；J03_LAST_EXECUTION.json区分实际本次新拟合与缓存；本报告可直接用于人工回传，不生成ZIP或回传包。

## 停止与人工事项

第一包执行到结果交付为止。研究负责人随后组织反馈分析，讨论差异方向、量级、条件区间、校准及新PROXY参数对正文的具体影响，再决定是否关闭J03。这里不代写独立科学审核报告，不更换主模型，也不自动进入F02、G/I或H03。

