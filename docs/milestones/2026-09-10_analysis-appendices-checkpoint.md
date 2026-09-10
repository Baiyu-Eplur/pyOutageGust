# 关键里程碑：地区日验证、附录证据补全与A–J英文初稿

日期：2026-09-10（Europe/London）。附注版本标签：`analysis-appendices-checkpoint-20260910`。

本节点保存今日的分析实现、实际产物、评价报告、附录生产接口和两批英文初稿。逐项日期、代码范围与文件范围见根目录 [dailylog.md](../../dailylog.md)，逐步执行见 [LOG.md](../../LOG.md)。这是可追溯的研究与写作检查点，不表示论文已达投稿状态，也不替代研究负责人的科学判断。

## 今日完整更新

1. **DD-DUR01持续强风增量比较。** 复用ERA5小时天气与日最大基线，加入超阈小时比例或归一化平方累计量；144目标（48复用、96新增）均有有效结果，保持八标签、原LAD折号和明确的训练阈值边界。[结果](../../results/new/20260910090006/results/dd_dur01/)与[总结](../new_analysis/dd_dur01/20260910090006/RESULTS_SUMMARY.md)保留重点任务无明确收益、稀有任务微小且不确定的收益。
2. **DD-TIME01固定回顾性时间留出。** 开发期2021-04-01至2023-09-29，后续期2023-09-30至2024-03-31；八任务在20424 LAD-days上冻结预测，并与开发发生率常数比较。八项BSS为正，主要/次级约3.03%/7.50%，同时记录平均低估和风险箱/月度不一致。[完整结果](../../results/new/20260910104718/results/dd_time01/)、[回执](../new_analysis/dd_time01/20260910104718/EXECUTION_RECEIPT.md)、[审查](../new_analysis/reviews/DD_TIME01_REVIEW.md)。
3. **A–J固定附录生产。** 新增[main_appendix.py](../../main_appendix.py)及模块化生产包，维护主张—需求—产物映射、固定目录、来源指纹、图表编号及事务覆盖。原运行只读；不同附录和人工文件受范围保护。[使用说明](../APPENDIX_PRODUCTION_GUIDE.md)、[附录结果](../../results/Appendix/)。
4. **C最终样本的候选规格比较。** 22个既定可计算候选×四组正式样本，共88单元。272组件由196补算、58复用、18系数派生组成，记录701次OLS（含训练折）；保存完整预测、训练预处理、结点与评价身份。C04已更新；不把旧59834恢复样本与当前51173混排。[完成说明](../../results/Appendix/C/logs/APP_C_COMPLETE.md)。
5. **四步证据补全。** J03正式匹配八任务PROXY/GRID_MAX；F02两个天气最终模型同系数的LAD/two-way推断；G/I当前预测残差与七风暴窗口；H03全体暴露NB2/Tweedie、恢复Gamma/Tweedie及正确两维聚类推断。各包的协议、原失败与限定恢复、事实报告、底层预测/矩阵均保留。J/F/GI已获负责人接受；四项H GLM获接受，频率来源映射局部未关闭。[J回执](../new_analysis/reports/APP_J03_COMPLETION.md)、[F回执](../new_analysis/reports/APP_F02_COMPLETION.md)、[GI回执](../new_analysis/reports/APP_GI_COMPLETION.md)、[H回执](../new_analysis/reports/APP_H03_COMPLETION.md)。
6. **A–J英文附录初稿。** [A–E合并稿](../new_analysis/writing/Supplementary_Information_A_E_draft.md)与[F–J合并稿](../new_analysis/writing/Appendices_F_J_draft.md)各为对应章节唯一编辑源。F–J含112项最终系数、21个登记表号和5张原图；有[证据映射](../new_analysis/writing/Appendices_F_J_evidence_map.md)及[中文作者说明](../new_analysis/writing/Appendices_F_J_author_notes.md)。使用本地academic-writing-skills并完成有限写作核对；没有修改正文。

## 入口与复现

- 普通地区日实验：`main_new.py`顶部仅开启所需`dd_dur01`或`dd_time01`，其他阶段保持关闭，然后运行`python -X utf8 -B main_new.py`。本次发布不启动分析。
- 附录生产：`python -X utf8 -B main_appendix.py --appendices C`；专包使用`--appendices J --j03-only`、`--appendices F --f02-only`、GI/H03选项以[当前使用说明](../APPENDIX_PRODUCTION_GUIDE.md)为准。缓存失效或明确重算可能执行已授权模型计算，单纯阅读结果无需运行入口。
- 人工文稿放在`docs/new_analysis/writing/`，与生产接口管理的固定结果目录分离。写作检查脚本仅读取现有产物，不调用拟合入口。

## 仍需人工处理的科学与写作事项

- 正文保留同日事件锚点PROXY。GRID_MAX比较结果、稀有任务和条件区间均保留，不宣称独立天气替换已获采纳或构造等效。
- DD-TIME01是已探索后续时期上的回顾性检验，且使用同日事件锚点；不称独立确认集或事前预警。
- H-W03/M15原天气粗分箱频率尚未同口径对齐；不能用全体频率代替天气旧数字。旧H03报告的这一解释以已接受台账(4)第14节及F–J作者说明为准，原数组没有为写作而改写。
- M17/GI-W08旧风暴比例/天数留待整合；当前已确认并集暴露4452、恢复3990，28个正客户超cap点只展示。
- F.3天气顺序R²使用全体gust函数模板，不是正式天气最终函数的逐块分解；初稿已清楚说明这一来源差别。
- 两批英文稿均待研究负责人和导师审阅；本次发布不自动修改正文、启动后续实验或宣布全部主张得到证明。

## 发布范围与追溯策略

上次同步后的9月9日晚依赖与结果也随本节点保存：P03/P04测试与审查、DD-AGG01稳定优化和五聚合比较、当前权威正文运行`20260909183317`。它们在dailylog中与今日新增工作分开记录。

本次保留远程已跟踪的旧运行文件。工作区原先已有469个历史文件删除，本提交不传播这些删除；不修改或移动已有标签。原始输入、Comments与环境缓存维持既有忽略策略，Windows快捷方式不发布。新增`results/Appendix`及文稿/源码采用字节保留属性，以保持已记录指纹可核对。

发布形式沿用项目既有习惯：实现与日志同一提交，附注Git标签固定指向该提交，GitHub Release使用本说明。发布范围及每个待提交文件的SHA256保存为同目录`2026-09-10_checkpoint-files.csv`；暂存字节核验保存为`2026-09-10_checkpoint-verification.json`。成功发布后新增`2026-09-10_checkpoint-publication.json`回执并作单独文档提交，标签不移动。
