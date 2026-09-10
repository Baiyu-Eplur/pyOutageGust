# APP-C-COMPLETE 交付核验回执

完成时间：2026-09-10T15:31:45+01:00。

- 独立入口：`python main_appendix.py --appendices C`。显式重算C缺失组件：追加`--recompute-c`。C保留原研究来源的只读复用，不通过该选项重做兼容历史计算或D审计。
- 固定结果：`results/Appendix/C/`；完成说明：`results/Appendix/C/logs/APP_C_COMPLETE.md`，阅读入口：`results/Appendix/C/README.md`。
- 原12项×4最终样本及原random/LAD/year均完成；另补正式自由结点及统一最终控制项函数比较。88可计算单元，组件REFIT=196、REUSE=58、DERIVE=18；701次新增OLS拟合含CV训练折。第二、三次生产均缓存命中88/88，没有新增拟合。
- 四样本：全体暴露60437、全体恢复51173、天气暴露9857、天气恢复9254。ID/标签/折在C/data/samples。原随机CV缺折号行按原规则排除，各种CV的实际n另列；不混合不同设计的评分。
- 214份保存预测文件已只读复算池化RMSE；728份训练分区记录已核验ID及折分配。原兼容CV只存汇总的部分明确标注无逐行OOF，未为凑齐底层文件重复计算兼容分数。
- 6项C技术测试、8项既有生产事务测试、1项缓存有效/损坏/变更指纹/force测试通过。缓存测试仅用源结果复用组件，并以mock禁止调用OLS。
- 通用产物完整性54项通过；C专门保存结果核验通过。其他九附录128文件SHA256与mtime均不变；27独立来源文件指纹保持原值。
- 实际查看C_GUST_PERFORMANCE.png两版，仅修正末面板刻度显示拥挤；所有候选、数据及尺度定义不变。设计模板使用自由k，实际所选结点保存在拟合数据中。
- 根三层映射、result_gaps.md、manifest和图表登记已同步，C04已关闭。C共9张CSV/Markdown表和1张图；底层记录见C/manifest.json。

本轮代码：main_appendix.py；analysis_new/appendix/c_models.py、c_completion.py、runner.py、catalog.py、mapping.py、source_fingerprints.json。必要测试位于test/test_appendix_c_completion.py、test_appendix_c_cache.py、verify_appendix_c_saved.py，通用verify_appendix_exports.py兼容C底层文件。旧model_selection/final_models/weather_only/knot_estimation/plateau/basis_solver均未修改。

授权与维护更新：AGENTS.md、docs/APPENDIX_PRODUCTION_GUIDE.md、LOG.md。首次拟合前协议与矩阵在本目录FIRST_EXECUTION_PROTOCOL.json、FIRST_COVERAGE_BEFORE.csv留档；当前运行协议在C/logs/protocol.json。复算命令：`python -X utf8 -B test/verify_appendix_c_saved.py`；证据为verification.json、export_integrity.json。

结果及需人工判断的实际差异已经写入C完成说明，包括当前函数并非所有组LAD误差最小、原D恢复对照交互项不一致。未重新选择正文模型，未修改Word或其他附录科学结果，未启动其他缺口、生成ZIP或远程发布。没有剩余阻塞C04的技术问题。
