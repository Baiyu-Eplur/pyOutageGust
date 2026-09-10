# 每日更新日志

## 2026-09-10（Europe/London，BST / UTC+01:00）

本日汇总依据逐步记录 [LOG.md](LOG.md)、实际代码、运行回执和写作交付文件。表中时间为已有执行记录；“完成”区分技术产物完成、负责人接受和待人工审阅，不表示全部论文主张已经验证。

| 日期与时段 | 改动内容与完成范围 | 对应代码范围 | 对应其他文件范围 |
| --- | --- | --- | --- |
| 2026-09-10 08:55–09:14 | DD-DUR01：在既有ERA5小时数据、标签和LAD折号上，比较日最大阵风基线与两个持续性增量；扩展既有优化器和评价接口。48个基线组件复用、96个增量拟合，144目标有效；完成技术核验及审阅后的客观总结。 | `main_new.py`、`analysis_new/runner.py`、`duration_features.py`、`fragility_optimizer.py`、`dd_agg01_evaluation.py`、`dd_dur01.py`、`dd_dur01_outputs.py`；`test/test_dd_dur01.py`及兼容入口测试 | `results/new/20260910090006/results/dd_dur01/`；`docs/new_analysis/dd_dur01/20260910090006/`；协议、阈值、逐行预测、指标、配对区间、图形、结果总结 |
| 2026-09-10 10:44–11:09 | DD-TIME01：既定PROXY模型按开发期2021-04-01至2023-09-29拟合，冻结后预测2023-09-30至2024-03-31。完成8任务、20424评估LAD-days、开发发生率常数基准、校准/月度/支持摘要；另写执行回执和授权的结果审查。 | `main_new.py`、`analysis_new/runner.py`、`dd_time01.py`、`dd_time01_outputs.py`、`temporal_fragility.py`；`test/test_dd_time01.py` | `results/new/20260910104718/results/dd_time01/`；`docs/new_analysis/dd_time01/20260910104718/EXECUTION_RECEIPT.md`；`docs/new_analysis/reviews/DD_TIME01_REVIEW.md`及计算记录 |
| 2026-09-10 12:39–13:17 | 建立A–J附录固定生产接口、主张—需求—结果映射、来源指纹、图表登记和缺口状态。采用暂存核验后事务替换，保留人工文件和历史运行；补齐既有变量、原因代码、样本/方法描述等派生产物。 | `main_appendix.py`；`analysis_new/appendix/{catalog,mapping,runner,exporters,design_adapter}.py`、`source_fingerprints.json`；`test/test_appendix_production.py`、`verify_appendix_exports.py` | `results/Appendix/A/`至`J/`及根映射、manifest、图表登记、`result_gaps.md`；`docs/APPENDIX_PRODUCTION_GUIDE.md`、执行回执和核验记录；`AGENTS.md`入口例外规则 |
| 2026-09-10 15:06–15:31 | APP-C-COMPLETE：在正式四组样本上补齐既定候选与原设计评价。22候选×4组合共88单元；272组件中196补算、58复用、18系数派生，共记录701次OLS（含CV训练折）。保存OOF/训练预处理与结点信息，更新C04状态；不重跑D审计。 | `analysis_new/appendix/{c_models,c_completion,catalog,mapping,runner}.py`、`main_appendix.py`；`test/test_appendix_c_completion.py`、`test_appendix_c_cache.py`、`verify_appendix_c_saved.py` | `results/Appendix/C/{tables,data,figures,logs}/`，含`logs/APP_C_COMPLETE.md`；`docs/new_analysis/app_c_complete/`；根需求映射与登记 |
| 2026-09-10 15:51–16:08 | APP-WRITE-AE：依据已接受结果完成A–E合并英文初稿、可编辑表格、证据/写作记录和有限作者自查。写作不改变正文和科学结果。 | `docs/new_analysis/writing/checks/`中的只读表格/写作辅助脚本；无统计模型修改 | `Supplementary_Information_A_E_draft.md`、`APPENDIX_A_E_WRITING_RECORD.md`、`APP_WRITE_AE_COMPLETION.md`及写作检查记录，均位于`docs/new_analysis/writing/` |
| 2026-09-10 16:32–16:59 | 第一包J03：PROXY与独立网格日最大天气的正式匹配比较，保持同LAD-day、八标签、五折和稳定优化配置；保存当前OOF配对区间与校准。96组件有效（48复用、48补算）；经后续负责人反馈关闭匹配比较缺口，正文保留PROXY。 | `analysis_new/appendix/{j03_compare,j03_report,runner,catalog,mapping}.py`、`main_appendix.py`；`test/test_j03_outputs.py` | `results/Appendix/J/`下J03产物、协议和执行报告；`docs/new_analysis/reports/APP_J03_COMPLETION.md`；既有四步台账和根状态 |
| 2026-09-10 17:20–17:26 | 第二包F02：复用两个天气最终模型的同X/残差/系数，补全LAD-only与LAD/date two-way协方差和全部逐项SE/区间。零新增OLS；实际df104/103，保留小于1的SE比与协方差适用边界。后续负责人接受关闭。 | `analysis_new/appendix/f02_cov.py`及既有入口/调度/登记；`test/test_f02_cov.py` | `results/Appendix/F/{tables,data,logs}/F02_*`；`docs/new_analysis/reports/APP_F02_COMPLETION.md`及交付核验；四步台账 |
| 2026-09-10 19:10–19:30 | 第三包G/I：补齐当前四组模型预测、三类残差、分箱数据，以及七场固定风暴的主表/展示点和去重并集。明确固定结点OOF、样本内与nested-CV身份。后续负责人接受结果，保留GI-W01至W09写作事项。 | `analysis_new/appendix/{gi_core,gi_outputs,gi_storms,gi_completion}.py`及既有入口/映射；`test/verify_gi_outputs.py` | `results/Appendix/G/`、`results/Appendix/I/`；`docs/new_analysis/reports/APP_GI_COMPLETION.md`及数值/技术快照；四步台账 |
| 2026-09-10 19:52–20:19 | 第四包H03：全体暴露NB2/Tweedie、全体恢复Gamma/Tweedie，复用正式X与OLS参考，补齐score/Hessian两维聚类推断。四项有效；NB2首次初始化失败后按冻结规则有限恢复，失败记录保留。旧序数/事件条件结果只整理。四GLM已获反馈接受，H-W03频率来源仍待局部对齐。 | `analysis_new/appendix/{h03_models,h03_evidence,h03_completion}.py`及入口/映射；`docs/new_analysis/reports/verify_h03_saved.py`、`verify_h03_cache.py` | `results/Appendix/H/`，含`logs/H03_EXECUTION_REPORT.md`及数值恢复记录；`docs/new_analysis/reports/APP_H03_COMPLETION.md`；四步台账(4)第14节 |
| 2026-09-10 21:48–22:10 | APP-FJ-DRAFT：完成F–J五章19节英文初稿、21个原登记表号、5幅现有图；保留112项完整最终系数。实际使用academic-writing-skills；表格/图注/身份与最终候选核对完成，988份正文/A–E/附录源文件保持不变。 | `docs/new_analysis/writing/checks/fj/{prepare_writing,format_tables,check_writing}.py`；仅写作派生，无统计代码修改 | `docs/new_analysis/writing/Appendices_F_J_draft.md`、`Appendices_F_J_evidence_map.md`、`Appendices_F_J_author_notes.md`及`checks/fj/`记录 |
| 2026-09-10 本次发布 | 新增本日日志及关键milestone说明；将尚未发布的当前实现、分析产物与写作成果一并纳入可追溯提交、附注标签和GitHub Release。保留远程已有历史运行，不提交本地既有删除。 | `.gitattributes`新增附录/写作指纹文件的字节保留规则；发布辅助脚本位于`docs/milestones/`，不接入研究入口 | 本文件、`docs/milestones/2026-09-10_analysis-appendices-checkpoint.md`、发布范围清单/核验/回执、README入口、LOG.md |

代码简写的`analysis_new/*.py`均位于该目录；写作文件简写均位于`docs/new_analysis/writing/`。具体调用、失败/修复和验证命令按LOG.md原时间记录追溯，本日日志不替代原运行协议。

### 今日结果的解释与未决范围

- DD-TIME01八任务BSS均为正，主要/次级约3.03%/7.50%；平均风险低估和月度/分箱偏差同时保留，不称提前预警或全部时间稳健。
- J03未显示GRID_MAX在两个>100客户重点任务上优于PROXY；两个>1000任务的固定OOF条件区间偏向PROXY，不作等效性结论。
- H03恢复线性gust项在两个GLM中变号，但OLS/两GLM区间都含零；不写全部系数符号一致，也不据此自动换主模型。
- H-W03/M15：导师旧粗分箱0.40/0.29/0.48属于天气归因事件；现有全体样本对照不能替代它。F–J稿仅使用明确原分箱，不声称完成粗箱来源对齐。
- M17/GI-W08：旧风暴比例/天数尚待衔接；新稿使用已确认4452/3990去重事件数与28个显示点。
- F.3天气顺序R²沿用全体gust设计，与天气最终11/24平台/固定11单结点不同；稿中已限定，未重算。

### 本次同步承接内容

上次发布停在2026-09-09的导师独立复现节点。本次同时纳入9月9日晚尚未同步的PROXY/P03-P04测试、结果审查、DD-AGG01稳定优化与五聚合比较，以及当前权威运行`20260909183317`。它们是本次发布承接范围，不计作9月10日新完成的实验。

原始输入、导师Comments、环境缓存继续遵循现有忽略规则；本地Windows快捷方式不发布。本地已删除的五个旧运行目录不作恢复或进一步删除，也不把删除提交到远程。最终提交、标签、Release及核验状态见同目录milestone发布回执。
