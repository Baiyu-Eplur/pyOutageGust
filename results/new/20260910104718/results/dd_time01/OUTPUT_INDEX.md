# DD-TIME01 输出索引

生成：2026-09-10T10:49:57.724216+01:00。仅说明复现、字段、完成状态和技术异常，不作科学审核、模型采用或论文结论。

## 运行

在项目根目录main_new.py中仅将最后的dd_time01设为1，运行 `python -X utf8 -B main_new.py`。当前交付开关仍为0；普通Python程序独立完成全部步骤，无agent/LLM依赖。

本次确切命令：`C:/Users/haoya/.conda/envs/pyoutagegust/python.exe -X utf8 -B -c "import main_new; main_new.STEPS['dd_time01']=1; main_new.main()"`。输入由DD_TIME01_SOURCE_RUN指定为正文生产运行20260909183317的final_models/district_day_panel.csv；无需REUSE_RUN、无需其他阶段开启。每次写新的秒级目录。

## 冻结范围

开发期2021-04-01至2023-09-29，后续评估期2023-09-30至2024-03-31，日期直接使用原面板保存口径，不换时区。只在开发期拟合八项背景率lognormal，复用稳定13初值和既定有限备用策略。模型有效后先冻结参数、开发率、开发期概率十分位箱，再读取评估期标签进行直接预测。无评估期重拟合/重校准/调参，无新的时间/空间划分，无bootstrap、显著性检验或独立样本误差条。

proxy沿用当日事件位置与当日事件天气插值。本检验是相同事后proxy规则下关系的跨时期迁移，不是提前预测故障，也不消除事件锚点依赖。评估期此前已用于探索，属于固定规格回顾性留出，不是从未使用过的独立确认集。没有改为开发期天气代替评估期天气。

## 文件用途

|文件|用途|
|---|---|
|protocol.json / run_manifest.json|设计、来源选择链、输入/源码SHA256、模型配置、随机种子、命令和执行时间|
|input_coverage.json / sample_summary.csv|原键与日期完整性、缺失记录、实际时期/LAD/地区日/各任务阳性数量|
|development_fit.csv / optimizer_candidates.csv.gz|八项开发期参数/有效性/既有诊断及全部初值，不读取历史全样本或LAD折内拟合|
|frozen_development.json / development_probabilities.csv.gz|评估标签加载前冻结的模型、开发常数率、箱边界及开发期概率|
|temporal_predictions.csv.gz|长表LAD/date/target；gust为原proxy(m/s)，y为原二元标签；prediction为开发期冻结模型概率，baseline_prediction为开发期阳性率|
|temporal_metrics.csv|每任务等权池化模型/基准BS，BSS=1−模型BS/基准BS，平均预测、实际率、预测减实际及固定箱校准RMSE；BSS不是准确率/R²/概率百分点|
|calibration_edges.json / calibration_bins.csv|开发概率十分位边界补0/1去重；right归箱。每箱n、events、平均预测和实际频率；空箱频率NaN，n<100保留孤立标记|
|monthly_metrics.csv|同一预测的评估期各月摘要，不重训；2023-09仅包含9月30日，按实际n解读|
|covariate_support.csv|开发/评估gust分布、评估期低于/高于开发范围的数量及比例，不做历史上限、g50或尾部曲线审计|
|figures/ / figure_axes.json|每任务校准全范围+开发概率决定的放大图及箱n/阳性表；月度率与BS图；两期proxy经验分布图|
|technical_checks.json / execution.jsonl / inventory.json|本轮必要复算、训练信息隔离顺序、逐阶段状态、产物清单与指纹|

CSV浮点回读使用 `float_precision='round_trip'`。any_gt0为至少一个事件，保留零客户；wthr_gt0为至少一个天气归因事件（含零客户）；其余标签按地区日内至少一事件客户数严格>5/>100/>1000，不按客户数日和。

## 技术完成状态

有效开发期任务8/8。无效任务及原因：[]。无效任务的正式模型预测、评分与校准留空；开发期常数率基准仍保留，不用全样本或评估标签补救。全部技术检查通过：True，共117项。

缺失LAD-day数：0；超出固定研究期的原记录数：0。如存在日期缺失，保存在input_coverage.json，不填造观测。两时期区域集合一致，不另造空间留出。既有边界、弱识别等拟合诊断按原值保留；成功运行不代表科学采用或参数解释已得到确认。

本轮未重算全研究期模型、历史LAD拟合、旧proxy上限/g50、incident结点联系、锚点剔除、ERA5/持续性比较或降水曲面；没有新天气请求、ZIP、独立审核报告、论文/附录/修订台账修改。到结果交付处停止。
