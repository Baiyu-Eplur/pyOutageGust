# P03/P04：ERA5 日最大阵风与旧区域日代理比较

状态：2026-09-09 完成实现与离线测试，**没有请求天气数据、没有运行正式实验、没有获得实验结论**。用户手动运行后才产生结果。

## 启动方法

编辑根目录 `main_new.py`：原 16 个开关和新增开关目前均为 0，旁边已有中文说明。只将最后一项改为：

```python
'p03_p04_grid_weather': 1,  # P03/P04 独立实验
```

保留 `DRY_RUN = 0`、`REUSE_RUN = ''`，在自己的项目环境执行 `python main_new.py`。无需开启旧面板、回归、绘图或文档步骤。

`P03_BASE_RUN = '20260909183317'` 指向目前本地已有的已完成运行。必须保留该目录。程序校验 E0 输入、面板和旧插值验收文件 SHA-256，再核对面板事件数与阈值标签；若以后采用其他基准，明确修改编号，不自动猜测“最新”目录。

新增文件进入 `results/new/<本次年月日时分秒>/results/p03_p04/`。首先查看 **`REPORT.md`、`decision.json`、`brier_comparison.csv` 和 `calibration.png`**。外层 run.json/logs 仍记录目的和步骤；实验内部的参数、阶段、边界/源码/输入指纹在 experiment.json。

## 顶部参数与恢复

|参数|含义|
|---|---|
|`P03_BASE_RUN`|旧面板运行编号，只读且必须与当前 E0 样本一致|
|`P03_WEATHER_CACHE_RUN`|默认空；可填上轮 P03 编号，复用验签的天气原始响应，允许该轮最终失败|
|`P03_REQUEST_INTERVAL_SECONDS`|默认 10 秒，相邻 LAD 首次请求间隔|
|`P03_BOOTSTRAPS`|默认 1,000，对固定折外误差做 LAD 配对 bootstrap，不重新拟合|
|`P03_MIN_REL_BRIER_GAIN`|默认 0.05，本轮候选“有意义改善”门槛，必须在看结果前决定|

失败后先看 REPORT.md 与 weather_raw/requests.jsonl。修复网络或等待额度恢复，把失败运行编号填入 P03_WEATHER_CACHE_RUN 再运行。只复用上次 run.json 中哈希正确、参数完全相同且小时完整的响应，不用旧代理补全。每个新运行均保存原始响应副本和日志。

## 数据与方法

1. 读取自己的 `data/external/gis/LAD_DEC_2021_UK_BGC/LAD_DEC_2021_UK_BGC.shp`，按面板选 111 个 LAD，在 EPSG:27700 中计算几何质心后转 WGS84；不使用事件坐标均值或边界的标签位置。
2. 每个质心一次请求 2021-04-01—2024-03-31 的逐小时 `wind_gusts_10m`。固定 `models=era5`、`wind_speed_unit=ms`、`timezone=GMT`、`cell_selection=nearest`、`elevation=nan`，记录请求和返回网格坐标。UTC 与旧面板日期一致，每地必须有 26,304 个连续小时、1,096 天各 24 个有效非负值，之后求日最大值，形成 121,656 行。
3. 原始响应连同请求来源以 gzip 保存。正常约 111 个首次 HTTP 请求；每地失败最多尝试三次，429/5xx 退避上限 60 秒，连续三个 LAD 失败即停止。长日期请求可能按服务规则消耗多个计量单位，111 次 HTTP 不等于保证不触发额度限制。
4. 面板仅替换 gust，旧值备份为 gust_proxy；其余原字段逐项校验不变。八标签为全体/天气归因各自的任意事件、>5、>100、>1000 客户。**零客户事件仍算任意事件**，不应用 R0c 正客户数筛选。
5. 拟合前分别对有事件日、无事件日和全部区域日保存均值差、差值标准差、相关、RMSE 和分位数。差值为“新日最大值−旧代理值”。
6. 空间留一用旧方法的 40 km 高斯核及不足五邻点时的最近邻回退，排除目标 LAD 后重建其网格日最大值。另做排除返回相同网格单元邻居的验证，报告唯一网格数量和质心至网格距离。
7. 复用 `district_day_core.lognormal_mle`：`P=p₀+(1−p₀)Φ((ln(max(g,0.3))−ln θ)/β)`，保持旧方法四初值、参数边界、似然截断和 L-BFGS-B。两版各八组全样本参数；全体和天气归因均以全部区域日为分母。
8. 按旧 plot_model_selection 的 E0 首见 LAD 顺序、随机种子 20260908 和模五规则分组。两版使用同一折，每次在四折区域拟合、预测完整留出区域，输出逐行 OOF 概率与逐折分数。
9. 每阈值报告两版 Brier 和绝对/相对改善。校准图采用两版合并预测的共同分位数分箱，保留稀有事件分辨率，保存每箱人数、事件数、预测和观测频率。八任务平均相对改善用于总体筛查，同时保留全部单阈值结果。

## 候选验收与回滚

原设计没有给出数值门槛。以下为本次**候选筛查规则**，不是通用统计标准；用户可在看结果前修改主要门槛，不能按结果反向调整。

- 平均相对 Brier 改善 ≤0，或某阈值配对改善 95% 区间上界低于 −5%：回滚建议。
- 平均相对改善 <1%：按预设微小改善下限给出回滚建议。
- 平均相对改善 ≥5%、配对 LAD bootstrap 区间下界 >0、无单阈值退化超过 5%、共同分箱校准 RMSE 平均相对改善 ≥5%，且没有数据待核查项：标记 `numerical_candidate=true`。
- 1%–5% 的改善、校准证据不足、空间诊断异常或未收敛：中间状态，列明原因。输入/模型验证未完成时不声称新模型更差。
- 覆盖不全、不可恢复的 API/文件技术障碍：停止并记录回滚建议；不拟合不完整新面板，不以旧代理冒充新天气。

**数值达标仍输出“中间状态：待校准图人工确认”。** 代码不能代替用户/设计方确认图形“明显更贴近对角线”。本功能不会自动改 Table 7、Word 或移动正文/附录。用户确认全部条件后，parameters_comparison.csv 提供转正的八组参数；回滚时建议旧代理仅保留为注明局限的附录。实验建议与稿件实际改动明确区分。

## 解释边界

- ERA5 是再分析网格估计，不是独立地面观测真值。质心最近网格的日最大值不是整个 LAD 的空间最大值。
- 旧代理目标位置为事件坐标均值，新位置为几何质心；旧变量用事件小时天气，新变量是整日日最大值。差异包含位置、来源和聚合三项变化，不能只归因于平滑。
- 新 LOO 衡量网格日最大值的空间可重建性；旧 RMSE 2.221 m/s、相关 0.854 的目标是有事件日的事件阵风均值，锚点也不同。不能机械比较这些数字来判定新源更真实。
- 旧代理依赖当天事件及位置，LAD 留出不能消除其来源选择性。新天气独立于事件，但相邻 LAD 可能共享网格；同网格排除验证仅用于诊断。
- 配对 bootstrap 是固定 OOF 预测下按 LAD 抽样，没有重新训练或按风暴/日期分组，不覆盖全部时间依赖。保留未收敛诊断，不以数值收敛替代科学有效性。

API 参数依据：[Open-Meteo Historical Weather API 官方文档](https://open-meteo.com/en/docs/historical-weather-api)，查阅 2026-09-09。

## 代码与产物清单

|代码|职责|
|---|---|
|`main_new.py`|注释、默认关闭的第 17 个开关与参数|
|`analysis_new/runner.py`|新阶段、参数/源码记录、子进程隔离|
|`analysis_new/district_day_core.py`|共享拟合、插值与分组函数|
|`analysis_new/district_day_fragility.py`|原流程调用共享函数，统计算法不变|
|`analysis_new/grid_weather.py`|质心、严格逐小时采集与缓存|
|`analysis_new/grid_fragility_validation.py`|空间验证、配对拟合/CV、Brier、校准与判定|
|`analysis_new/p03_p04_grid_weather.py`|编排、审计与失败报告|
|`test/test_grid_weather_experiment.py`|离线合成样本/模拟 HTTP 测试|

|输出（相对 `results/p03_p04/`）|内容|
|---|---|
|`REPORT.md`, `decision.json`|结论、候选门槛与依据|
|`experiment.json`, `inventory.json`|参数、时间、阶段、来源、实际路径/字节/哈希清单|
|`centroids.csv`, `grid_cells.csv`|质心、返回网格及距离|
|`weather_raw/*.json.gz`, `weather_raw/requests.jsonl`|逐小时原始响应和逐请求记录|
|`grid_daily.csv`, `panel_grid.csv`|完整日最大天气、新旧阵风与不变标签|
|`gust_comparison.csv/json`, `quality.json`|数据层比较和待核查项|
|`leave_lad_out.csv`, `leave_shared_grid_cell_out.csv`, `spatial_validation.json`|空间验证预测和统计|
|`parameters_long.csv`, `parameters_comparison.csv`|16 组参数及按八阈值并排的 θ/β/p₀|
|`lad_folds.csv`, `oof_predictions.csv.gz`, `cv_fold_scores.csv`|共同分折、折外预测、逐折 Brier|
|`brier_comparison.csv`, `paired_uncertainty.json`|八任务的两版指标与配对区间|
|`calibration_bins.csv`, `calibration.png`|共同分箱和两版校准曲线|
|`optimizer_diagnostics.json`|16 次全样本和 80 次折内拟合收敛诊断|

只列实际完成文件；失败时未执行部分不会生成伪造数值。正式产物由外层 run.json 再统一哈希。开发/预检查/测试记录见根目录 LOG.md。
