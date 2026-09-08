# RETURN_TO_CHATGPT_X01

## 1. 状态与输入

- run_id / 配置版本：`X01_20260906_001` / X01-v1.0。
- 阶段完成情况：X01-A–X01-F均已实际执行；计算产物已验收。
- 输入快照：`frozen_sources/input/R02_event_master.parquet`，SHA-256 `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`，R02输入manifest标记为已完成事件快照；截止为2026-09-06。
- 人口：来源有效事件人口，未按结果p99截尾；仍受历史天气产品、UTC代理时间和区域代理的已记录限制。
- E / R / R_C：样本、日期、事件数和验证群组见 `tables/task_sample_flow.csv`、`tables/split_summary.csv`。
- 与Claude修复目录：完全隔离；本run只写入`test/research_exploration/shape_models/X01/X01_20260906_001`。
- 复现：见`README.md`的命令（脚本只读取本run冻结副本）。

## 2. 实际评价协议

- 直接原尺度条件均值、固定共同控制和无gust×pressure交互；详情`EXPERIMENT_CONTRACT.md`。
- E为Poisson工作均值损失；R/R_C为Gamma型工作均值损失，非完整分布假设。
- 五折14日时间块、命名风暴合并、48h purge；M03/M04在外层训练内三折调参。
- 回顾性评价，历史数据可能已被此前研究接触；不称确认性未来测试。
- 主指标为合并OOF平均工作偏差，未因结果改动，见`tables/model_leaderboard.csv`。

## 3. 候选覆盖

| 模型 | E状态 | R状态 | R_C状态 | 失败或限制 |
| --- | --- | --- | --- | --- |
| M00 | success | success | success | see `tables/fit_diagnostics.csv` |
| M01 | success | success | success | see `tables/fit_diagnostics.csv` |
| M02 | success | success | success | see `tables/fit_diagnostics.csv` |
| M03 | success | success | success | see `tables/fit_diagnostics.csv` |
| M04 | success | success | success,warning_accepted | see `tables/fit_diagnostics.csv` |
| M05 | success | success | success | see `tables/fit_diagnostics.csv` |
| M06 | success | success | success | see `tables/fit_diagnostics.csv` |
| M07 | success | success | success | see `tables/fit_diagnostics.csv` |
| M08 | success | success | success | see `tables/fit_diagnostics.csv` |

## 4. 各任务短名单


### E

| model_id | mean_deviance | rmse | mae | oof_r2 | total_ratio | oof_coverage | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M03 | 363.134867 | 409.246135 | 135.745856 | 0.008337 | 0.99942 | 1.0 | eligible |
| M05 | 363.984635 | 409.355556 | 135.81782 | 0.007807 | 0.998372 | 1.0 | eligible |
| M04 | 364.48909 | 409.42981 | 135.917709 | 0.007447 | 0.99722 | 1.0 | eligible |
| M02 | 364.832806 | 410.717173 | 137.452217 | 0.001195 | 1.022317 | 1.0 | eligible |
| M08 | 367.809561 | 410.108291 | 135.234593 | 0.004155 | 0.974657 | 1.0 | eligible |

### R

| model_id | mean_deviance | rmse | mae | oof_r2 | total_ratio | oof_coverage | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M05 | 2.367734 | 87.145041 | 19.118155 | -0.001997 | 0.96259 | 1.0 | eligible |
| M08 | 2.368638 | 87.147479 | 19.12421 | -0.002053 | 0.963015 | 1.0 | eligible |
| M07 | 2.369914 | 87.152549 | 19.142716 | -0.00217 | 0.964246 | 1.0 | eligible |
| M04 | 2.370181 | 87.140764 | 19.115715 | -0.001899 | 0.962993 | 1.0 | eligible |
| M06 | 2.370516 | 87.142268 | 19.14962 | -0.001933 | 0.965494 | 1.0 | eligible |

### R_C

| model_id | mean_deviance | rmse | mae | oof_r2 | total_ratio | oof_coverage | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M05 | 2.30097 | 87.003063 | 19.216433 | 0.001265 | 0.959393 | 1.0 | eligible |
| M08 | 2.30138 | 87.005711 | 19.223385 | 0.001204 | 0.959809 | 1.0 | eligible |
| M06 | 2.301393 | 87.005753 | 19.223074 | 0.001203 | 0.959787 | 1.0 | eligible |
| M04 | 2.301873 | 86.997605 | 19.210881 | 0.00139 | 0.959219 | 1.0 | eligible |
| M07 | 2.302424 | 87.011817 | 19.2427 | 0.001064 | 0.961048 | 1.0 | eligible |

完整排行榜：`tables/model_leaderboard.csv`；校准：`tables/calibration_bins.csv`；OOF覆盖：`predictions/oof_predictions.parquet`。

## 5. 关键问题的证据回答

1. 阵风的增量信息：以每个模型相对M00的OOF偏差、RMSE和R²差判断，见`tables/model_leaderboard.csv`与`tables/paired_comparisons.csv`。
2. 自由曲线下降：直接检查M03曲线和导数，连同每个风速箱的事件/群组数，见`figures/curves_*.png`、`figures/derivative_*.png`、`tables/curve_support.csv`。
3. 约束是否有代价：M04对M03/M00的共同OOF样本差与bootstrap，见`tables/model_leaderboard.csv`、`evidence/bootstrap_refit_*.csv`。
4. 高风速平台：区分观测段、函数渐近和重拟合稳定性，证据为`tables/shape_parameters.csv`、`tables/tail_diagnostics.csv`。
5. 位置/平台稳定性：参数边界与重拟合分布保存在`tables/shape_parameters.csv`、`evidence/bootstrap_refit_*.csv`。
6. 三结果是否相同：逐任务独立短名单与曲线并列在`tables/model_leaderboard.csv`、`figures/curves_*.png`。
7. 尾部敏感性：输入p90与结果p95诊断（后者明示结果条件）在`tables/tail_diagnostics.csv`。

## 6. 不确定性

- OOF配对重抽样：每任务1000次，单位为外层验证群组，结果`tables/paired_comparisons.csv`。
- 入围曲线：每任务两候选、各200次群组重拟合，固定全数据选中的样条超参数；失败不删除，见`evidence/bootstrap_refit_*.csv`。
- 未包含数据定义、所有调参、模型选择和不完整过程识别的不确定性。
- 是否有明确胜者需作者结合区间、曲线支持和工程目的判断；本run只给暂定短名单。

## 7. 暂定推荐与工程解释

- E首选/备选候选：`M03, M05`，以预设OOF损失、覆盖、校准和稳定性排序；非自动论文选型。
- R首选/备选候选：`M05, M08`，以预设OOF损失、覆盖、校准和稳定性排序；非自动论文选型。
- R_C首选/备选候选：`M05, M08`，以预设OOF损失、覆盖、校准和稳定性排序；非自动论文选型。

- 曲线的横轴单位为m/s，纵轴为相对条件均值；其绝对水平取决于控制场景，不能直接解作阈值、机制或总体失效概率。
- 研究故事的具体启示和证据绑定：`RESEARCH_STORY_LOG.md`。

## 8. 交付与未完成项

- 报告：`X01_REPORT.md`；代码：`src/x01_run.py`；表/图/OOF/曲线：`tables/`、`figures/`、`predictions/`、`evidence/`；包：`RETURN_PACKAGE_X01.zip`。
- 不修改Word，不启动R05/V/W，不回写主论文或MR。
- 需要作者判断：各任务最终采用哪一候选；是否接受UTC代理、区域代理和带命名风暴保护的时间块CV作为后续研究基础。


## 实际数值与解释边界

- 三个任务各为60,436个唯一事件、78个验证群组；E保留8,979个零客户事件。
- **E**：M03为主指标首位（平均OOF偏差363.135；M00为370.433），E/M03 相对M00的条件OOF偏差差为 -7.057 （95%群组重抽样区间 -13.81 至 -2.455），RMSE差为 -1.172（-2.459 至 -0.3453）。 M05为备选：E/M05 相对M00的条件OOF偏差差为 -6.211 （95%群组重抽样区间 -12.94 至 -1.699），RMSE差为 -1.064（-2.337 至 -0.2148）。 M03重拟合显示稳定的中高风速上升：E/M03 的200次重拟合中，20 m/s比值中位数 1.47 （2.5%–97.5%：1.16–1.72），30 m/s为 2.87（1.92–3.81）；近零/位置不可识别 0/200，警告接受 0/200。 因此E支持将自由形状与单调/Softplus并列审阅，但仍不能将局部下降或高端回落解释为物理机制。
- **R**：M05点排名第一（2.3677，对M00为2.3766），R/M05 相对M00的条件OOF偏差差为 -0.008904 （95%群组重抽样区间 -0.01711 至 -0.001194），RMSE差为 -0.004207（-0.02532 至 0.01753）。 虽然偏差区间偏向M05，RMSE区间跨零；并且R/M05 的200次重拟合中，20 m/s比值中位数 1.05 （2.5%–97.5%：1.00–1.61），30 m/s为 2.43（1.00–3.14）；近零/位置不可识别 71/200，警告接受 0/200。 这意味着没有稳健证据可把位置或平台当作工程阈值。
- **R_C**：M05点排名第一（2.3010，对M00为2.3128），R_C/M05 相对M00的条件OOF偏差差为 -0.01174 （95%群组重抽样区间 -0.02079 至 -0.003054），RMSE差为 -0.01442（-0.04556 至 0.01425）。 但R_C/M05 的200次重拟合中，20 m/s比值中位数 1.25 （2.5%–97.5%：1.00–1.80），30 m/s为 3.09（1.00–3.73）；近零/位置不可识别 29/200，警告接受 0/200。 R_C使用最终客户规模，故它只支持事后条件关联。
- M08在R_C的200次中有51次warning_accepted；M06/M07/M08的渐近平台仅是函数性质。它们的高风速平台没有被本探索确认为数据已识别的饱和高度。
- 配对区间以固定OOF预测为条件；重拟合固定已选平滑规格。它们均未包含全套模型选择、数据定义或未观测完整天气过程的不确定性。
