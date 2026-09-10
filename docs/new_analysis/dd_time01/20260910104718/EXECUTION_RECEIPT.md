# DD-TIME01 执行回执

编制日期：2026-09-10（Europe/London，UTC+01:00）。对应运行：`20260910104718`。

本回执依据已保存的协议、运行清单、样本汇总及技术检查记录，记载任务执行与交付情况，不评价预测效果，不作科学审核、模型采用建议或论文结论。本次编写回执未重新运行实验。

## 1. 执行状态

|项目|记录|
|---|---|
|任务|DD-TIME01：正文 district-day proxy 脆弱性模型的固定时间留出检验|
|入口|`main_new.py` → `analysis_new/runner.py` → `analysis_new/dd_time01.py`|
|实际启用阶段|仅 `dd_time01`；其余阶段关闭|
|阶段开始|2026-09-10 10:47:18.721063 +01:00|
|阶段结束|2026-09-10 10:49:58.545852 +01:00|
|阶段耗时|159.829 秒|
|退出码 / 状态|0 / completed|
|有效任务数|8/8，未获得有效预测的任务为 0|
|交付文件开关|20 个阶段开关均保持 0|

记录来源：[运行清单](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/run.json)、[实验清单](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/run_manifest.json)。

## 2. 输入及固定执行规格

输入为正文生产运行 `20260909183317` 的 [district_day_panel.csv](D:/Pyprogramme/pyOutageGust/results/new/20260909183317/results/final_models/district_day_panel.csv)。来源按该运行的 district-day、表格和文档生产链确定；未按文件新旧或预测得分选择输入。输入路径与 SHA256 保存在本轮清单中。

沿用原事件锚点插值 gust proxy、LAD-day 键、日期口径及八项二元标签。任意事件保留零客户事件，其余阈值为严格 `>5`、`>100`、`>1000`；标签表示地区日内至少一个符合条件的事件，不使用当天客户数求和。

|时期|包含两端的日期|天数|LAD 数|地区日数|
|---|---|---:|---:|---:|
|开发期|2021-04-01 至 2023-09-29|912|111|101,232|
|后续评估期|2023-09-30 至 2024-03-31|184|111|20,424|
|合计|2021-04-01 至 2024-03-31|1,096|111|121,656|

原面板缺失 LAD-day 数为 0，期外记录数为 0；两期日期无重叠，LAD 集合一致，未补造观测。记录见 [input_coverage.json](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/input_coverage.json)。

每项任务仅使用开发期拟合背景率 lognormal 模型：

`p(g) = p0 + (1-p0) Φ[(ln g − ln θ)/β]`

执行复用现有稳定优化器及 13 初值策略，随机种子记录为 `20260909`。参数、开发期常数发生率及开发期拟合概率十分位箱在评估标签加载前冻结；随后从冻结文件读取参数进行评估期预测。未在评估期拟合、重新校准或调参。

冻结时间为 `10:49:35.158985 +01:00`；评估标签加载完成记录为 `10:49:35.968070 +01:00`。顺序及冻结文件哈希已纳入技术检查。

评分输出为模型 Brier、开发期发生率常数基准的 Brier、BSS、平均预测、实际发生率及二者差值。校准箱来自开发期概率，重复切点合并，边界覆盖 [0,1]；评估期使用原冻结边界，空箱频率留空。月度摘要使用同一批冻结预测，其中 2023 年 9 月仅含 9 月 30 日。

## 3. 八项任务完成记录

|任务|开发期阳性地区日|评估期阳性地区日|开发拟合及冻结预测|
|---|---:|---:|---|
|全体：任意事件（any_gt0）|34,004|7,922|已完成，有效|
|全体：>5 客户（any_gt5）|16,434|3,851|已完成，有效|
|全体：>100 客户（any_gt100，主要任务）|6,026|1,343|已完成，有效|
|全体：>1000 客户（any_gt1000）|826|194|已完成，有效|
|天气归因：任意事件（wthr_gt0）|4,893|1,229|已完成，有效|
|天气归因：>5 客户（wthr_gt5）|3,498|896|已完成，有效|
|天气归因：>100 客户（wthr_gt100，重要次级任务）|1,960|512|已完成，有效|
|天气归因：>1000 客户（wthr_gt1000）|243|69|已完成，有效|

来源：[sample_summary.csv](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/sample_summary.csv)、[development_fit.csv](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/development_fit.csv)。表内“有效”指现有优化器的技术有效性状态，不表示实验通过某项科学采用标准。

## 4. 交付位置与文件

结果目录：`D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/`。

共 37 个文件，包含 inventory 自身；完整相对路径和指纹见 [inventory.json](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/inventory.json)，用途说明见 [OUTPUT_INDEX.md](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/OUTPUT_INDEX.md)。

|文件或文件组|已交付内容|
|---|---|
|protocol.json、run_manifest.json|冻结设计、输入与源码指纹、环境、配置、种子、命令、时间和状态|
|input_coverage.json、sample_summary.csv|键与日期覆盖记录；分时期、分任务共 16 行样本摘要|
|development_fit.csv、optimizer_candidates.csv.gz|8 项开发拟合参数、目标函数、状态、既有诊断及全部初值候选记录|
|frozen_development.json、development_probabilities.csv.gz、calibration_edges.json|冻结参数、开发基准率、开发概率及精确箱边界|
|temporal_predictions.csv.gz|163,392 行任务级评估预测，含 LAD、日期、任务、标签、模型和开发常数基准概率|
|temporal_metrics.csv|8 项任务的池化评分及总体校准摘要|
|calibration_bins.csv|全部冻结箱的边界、样本数、阳性数、平均预测及实际发生率|
|monthly_metrics.csv|8 任务 × 7 个日历月，共 56 行摘要|
|covariate_support.csv|两期 gust 分布及评估期超出开发 gust 范围的数量和比例|
|figures/|8 张校准图、8 张月度图、1 张两期 proxy 分布图，共 17 张|
|figure_axes.json、proxy_distribution_plot_data.csv.gz|图形坐标配置和经验分布绘图数据|
|technical_checks.json、execution.jsonl|必要检查结果与逐步运行记录|
|OUTPUT_INDEX.md、inventory.json|复现与文件索引、产物指纹清单|

## 5. 代码和技术核验记录

新增实验模块为 [dd_time01.py](D:/Pyprogramme/pyOutageGust/analysis_new/dd_time01.py)、[temporal_fragility.py](D:/Pyprogramme/pyOutageGust/analysis_new/temporal_fragility.py)、[dd_time01_outputs.py](D:/Pyprogramme/pyOutageGust/analysis_new/dd_time01_outputs.py)，新增测试为 [test_dd_time01.py](D:/Pyprogramme/pyOutageGust/test/test_dd_time01.py)。

入口改动位于 [main_new.py](D:/Pyprogramme/pyOutageGust/main_new.py) 和 [runner.py](D:/Pyprogramme/pyOutageGust/analysis_new/runner.py)。公共校准函数在 [dd_agg01_evaluation.py](D:/Pyprogramme/pyOutageGust/analysis_new/dd_agg01_evaluation.py) 中增加可选冻结边界参数；原默认行为保留。既有 [test_dd_dur01.py](D:/Pyprogramme/pyOutageGust/test/test_dd_dur01.py) 调整阶段位置断言。稳定拟合实现直接复用，本轮未修改。

|核验项|记录|
|---|---|
|离线单元及兼容测试|17 项通过，包含 6 项 DD-TIME01 新测试|
|相关源码语法检查|8 个 Python 文件 AST 检查通过|
|本轮运行技术检查|117 项全部通过|
|开发拟合状态|8 项有效；无无效任务，既有弱识别和参数边界标记均未触发|
|文件指纹复核|36 条 inventory 记录、根运行清单输出及 41 条源码记录匹配|
|图形完整性查看|已查看主要和重要次级任务校准图、主要任务月度图及两期分布图|
|未完成任务或技术阻断|未记录|

117 项检查覆盖日期不重叠、同组 LAD、键唯一、标签与预测对应、开发标签隔离顺序、开发率基准、冻结参数未变、有限参数与合法概率、开发目标函数及初值选择、保存预测与池化/月度/分箱输出复算。详细布尔结果见 [technical_checks.json](D:/Pyprogramme/pyOutageGust/results/new/20260910104718/results/dd_time01/technical_checks.json)。

图内箱边界按 5 位有效数字显示，极近切点可能显示为相同文字；精确边界保存在 CSV/JSON 中。此显示精度未改变分箱和评分。

## 6. 独立运行方式

在项目根目录运行。本次实际执行命令为：

```powershell
C:/Users/haoya/.conda/envs/pyoutagegust/python.exe -X utf8 -B -c "import main_new; main_new.STEPS['dd_time01']=1; main_new.main()"
```

日常复现可将 `main_new.py` 最后的 `dd_time01` 开关设为 `1`、其余阶段保持 `0`，然后执行：

```powershell
python -X utf8 -B main_new.py
```

程序无需 agent、LLM 或交互操作参与计算，每次生成新的秒级结果目录。当前交付文件的全部阶段开关为 `0`；正式运行清单中的 `dd_time01=1` 为本次内存启用记录。

## 7. 执行边界记录

本轮保留当日事件锚点构造的事后 proxy，采用此前已参与探索的后续时期进行固定规格回顾性时间留出。该信息可用性边界已写入协议；没有将其标记为从未使用过的独立确认集或提前故障预测实验。

未开展历史全样本或 LAD 拟合数值审计、旧 proxy 上限/尾部/g50 核查、incident 结点联系、锚点覆盖或剔除、ERA5 替换、聚合或持续强风比较、新模型或协变量搜索、新空间验证、降水交互检验、新天气请求、额外时间切分、bootstrap 或显著性检验。

未修改 Word、正文、附录或论文修订台账，未覆盖历史结果，未生成 ZIP，未启动独立 agent 审查，未提交或同步 GitHub。执行、测试及本次回执编写均记录于 [LOG.md](D:/Pyprogramme/pyOutageGust/LOG.md)。
