# 导师分析学习与独立复现

创建：2026-09-09（Europe/London）。逐步开发记录见 `LOG.md`；每次执行的开始/结束时间、目的、开关、输入和源码指纹见 `results/new/<年月日时分秒>/run.json`。

本轮已完成，最终结果为 `results/new/20260909170633/`；完整 16 步数值运行为 `20260909164459`。详细覆盖范围和差异见 [复现验收记录](new_analysis/2026-09-09_REPRODUCTION_REPORT.md)。

## 入口与使用

运行项目环境中的 `python main_new.py`。所有开关在 `main_new.py` 顶部：`STEPS` 的 1 表示运行，0 表示跳过；`RUN_PURPOSE` 记录本次目的；`DRY_RUN=1` 只查看任务；bootstrap 次数默认分别为 500 和 300，随机种子沿用 20260908。入口只负责参数，调度和分析在 `analysis_new/`。

首次完整计算启用全部步骤。以后只画图时，设置 `REUSE_RUN` 为一份已完成运行的 14 位目录名，仅开启对应绘图步骤。调度器先检查相同输入的 SHA-256，再验证、复制该运行的产物到新的时间目录。关闭前置步骤不会自动重算；没有可用前置结果会明确报错。`plot_model_selection` 会重新拟合它所画的七种模型；`final_models`、天气和脆弱性模块也将拟合与图输出放在同一步，和导师程序一致。

输出示例：`results/new/20260909163143/results/figures/fig11_final_models.png`。最外层时间戳保证运行隔离；内层按 `model_selection`、`final_models`、`weather_only`、`figures`、`paper` 分类，保留导师的相对产物名称以便核对。`logs/<步骤>.log` 保存逐步控制台输出。旧 `main.py → pretestmain.py → scripts/` 完整保留，旧输出仍在 `results/pretest/`。

## 数据和独立性

生产分析直接使用自己的 `review_package/data/combined_E0_final.csv`（60,437 行）和 `combined_R0c_final.csv`（59,834 行）。2026-09-09 实际逐字节核对，导师两份 CSV 的 SHA-256 与自己的 CSV 完全一致：

|样本|SHA-256|
|---|---|
|E0|6a82fedd4dd77f4218f89f47058cafea7cc7c34867120589cdbeba8fca63ec38|
|R0c|313e5cea062eec015b5dbfdd61986ed277e058ab8fe9e0fa33ee773d936e72a9|

数据缺失时，通过既有 `main.py` 中 `model_review_package_20260907/materialize_final_data` 对应开关从自己的 `data/external` 与修正逻辑再生成样本；当前自己的静态样本已经与该生成步骤逐字节核验（见 pretest 日志）。不会读取导师数据或拿导师结果作计算缓存。

地图和原有 26 条参考文献取自自己的 `docs/Draft.docx`。`word/media/image1.png` 与导师论文使用的地图 SHA-256 相同。文献条目的“未核实”标记保留，文献核验不属于本轮数值复现。

所有分析子进程装有读写审计：禁止读取 `Comments/` 和旧 `D:/Pyprogramme/STST2603`，写入限于当前运行目录。文档子进程由项目自有 Python/JS 程序运行，其显式输入同样限于本项目原稿和当前运行结果。导师代码仅在开发时作为学习、改编和结果核对参照；生产入口不导入、执行或定位它。`source_inventory.json` 记录改编来源；不是独立发明统计方法的声明。

## 学习得到的结构和方法

|步骤|自有代码|计算内容|主要输出（相对本次 results）|
|---|---|---|---|
|baseline|复用 `review_package/code/run_main_regression.py`|原 M5 双边际回归、LAD 与 LAD×日期聚类 SE、E0 二次转折点|根目录 4 个系数 CSV、`run_summary.json`|
|model_selection|`analysis_new/model_selection.py`|每边际 12 种设定；原随机折、LAD 五折、留年份验证；AIC/BIC|`model_selection/*comparison.csv`、两份 12 工作表 XLSX|
|hinge_search|`analysis_new/hinge_search.py`|补建原包缺失的固定 1/2/3 结点候选比较程序|`model_selection/hinge_knot_search.csv`|
|knot_estimation|`analysis_new/knot_estimation.py`|1 m/s 网格的一/二结点剖面、500 次 LAD bootstrap、折内重选结点的嵌套 CV|`model_selection/knots.json`、2×剖面和 bootstrap CSV|
|plateau_E0 / R0c|`analysis_new/plateau_model.py`、`basis_solver.py`|全体/天气样本上三段平台、自由尾斜率模型和二次模型比较；300 次 bootstrap、嵌套 CV|`model_selection/ramp_model*.json`，另存四组平台剖面与 bootstrap CSV|
|select_final_knots|`analysis_new/select_final_knots.py`|补齐最终 E0 平台结点写回，同时保留原自由结点选择|更新 `knots.json`|
|plot_model_selection|`analysis_new/plot_model_selection.py`|七种模型拟合/验证、校准、偏残差、结点图|fig1–fig6（fig3/4 各含 E0、R0c）、预测汇总 CSV|
|fragility_demo|`analysis_new/fragility_demo.py`|事件条件下有序 logit、逐阈值二元 logit、E0 负二项 GLM|fig8、`fragility_summary.json`|
|fragility_surfaces|`analysis_new/fragility_surfaces.py`|事件条件下对数正态共同/自由离散度拟合；阵风×降水与气压 probit|fig9/10、`fragility_lognormal.json`|
|final_models|`analysis_new/final_models.py`|最终 E0 平台+温度平方；R0c 二次阵风+温度平方+阵风×降水，排除零客户数记录|fig11、`final_models/*final*.csv/json`、`table2_replacement.csv`|
|district_day_fragility|`analysis_new/district_day_fragility.py`|111 地区×观测日期全组合；当天事件天气插值；留地区验证；带背景率的区域日脆弱性|fig12、121,656 行面板、插值和脆弱性 JSON|
|weather_only_regression|`analysis_new/weather_only_regression.py`|天气归因样本重新选结点、三种回归、聚类 SE 和 LAD 验证|fig13/14、`weather_only/` 6 系数表与汇总|
|paper_extras|`analysis_new/paper_extras.py`|2023-09-30 前后分样；顺序加入变量的 LAD 验证 R²；分布描述|figP1/P2、`paper/paper_extras.json`、`r2_decomposition.csv`|
|report_tables|`analysis_new/report_tables.py`|补建四份 JSON 表格桥接、描述统计、中文本次计算摘要|`figures/*_rows.json`、`paper/descriptive_rows.json`、`COMPUTED_RESULTS.md`|
|documents|`analysis_new/documents.py`、两个 JS、`document_plan.py`|本项目原稿地图/参考文献+本次图表，生成探索报告、长短稿、重组计划|探索报告 DOCX、`paper/` 三个 DOCX|

导师编号没有 fig7，不是漏跑。完整分析图共 17 张 PNG。原包 `Paper_reorganisation_plan.docx` 为人工写作计划，无生成器；本项目补建自己的复现与重组计划，不将人工方案误列为数值分析结果。

### 原模型和预处理

响应为 E0 的 `log1p_customers_v2`、R0c 的 `log_duration_B_full_span_hours`。连续天气变量每个训练样本按均值和样本标准差（ddof=1）标准化，验证样本沿用训练尺度；日期固定效应也按训练类别展开。R0c 加入标准化 `log1p(customers)` 及平方。M1 到 M5 逐次加入阵风平方、阵风×气压、社会经济变量、年/月固定效应；七个扩展比较立方、对数、固定铰链、分位数阶梯、天气二次、地区固定效应、去社会经济变量。

LAD 五折使用 `default_rng(20260908)` 打乱按样本出现顺序得到的地区；用地区序号模 5 分折。地区固定效应遇未见验证地区时虚拟变量为零，记录其外地区预测局限。保留原随机折缺失值排除规则。

### 结点、平台和推断

自由一/二结点：保留线性阵风和阵风×气压，加入 `max(g-k,0)`；先用 QR 投影去固定协变量，再通过小 Gram 矩阵计算 SSE。二结点第一结点 8–20、第二结点 18–34 m/s，至少间隔 4 m/s；一结点 8–30。bootstrap 以 LAD 整组有放回抽样，保留导师在全样本预先构造的 X0 子矩阵规则。两结点被保留需 LR p<0.01 且两个 bootstrap 95% 区间宽度都不超过 6 m/s。

平台主效应为 `b_low*min(g,k1) + b_ramp*min(max(g-k1,0),k2-k1)`。E0 保留阵风×气压，R0c 平台比较去掉该交互；两个边际平台模型均加入温度平方。`basis_solver.py` 将 g 与所有候选 hinge 一次残差化，以等价线性变换求两/三维 Gram 解，避免每个候选重复投影。单元测试逐候选与直接 QR 残差回归比较 SSE。

正式模型报告 LAD 单向、LAD×日期双向聚类标准误；最终模型同时报告正态和 t(G−1) p 值。复现保留原脚本的推断定义：结点 LR 和剖面区间使用的卡方近似未调整结点搜索/后选择；不能当作严格已校准的置信保证。剖面 BIC 省略共同高斯常数，与 statsmodels 的绝对 BIC 不可跨表直接混减。

### 两种脆弱性必须区分

`fragility_demo/surfaces` 的分母是已有事件，估计有事件条件下的严重度；E0 阈值 5.5、100.5、1000.5 对应整数客户数分档，R0c 阈值 3、12、48 小时。共同/自由 beta 程序将嵌套阈值的二元对数似然相加，是复合似然形式，不能据此声称各阈值独立。有序 logit 和 NB 为演示模型，保留其诊断用途。

`district_day_fragility` 的分母是全部 111 地区×样本观测日期，没有事件的地区日也计入。地区中心取本项目事件经纬度均值；当天所有事件天气用 40 km 高斯核插值，有效邻居少于 5 时采用最近 5 点的 1/(距离+1) 权重。验证时去掉目标地区自身事件。模型为 `p0 + (1-p0)*Phi((ln(g)-ln(theta))/beta)`，分别拟合任意原因和天气原因的四种阈值。这重现的是导师的插值代理，不是从真实无事件天气观测重新建立的面板。

## 已辨明的版本和解释差异

1. README 默认 500 次 bootstrap，但脚本默认 200；保存结果为 500。入口明确用 500。
2. 自由 E0 两结点是 14/26；最终平台重新估计为 14/25。导师平台脚本只写 `ramp`，未改 `selected`，而保存文件已被手工改过。本项目显式完成衔接，保留 `unconstrained_selected`，按本次计算选择平台结点。
3. 探索预测表和有序 logit 保存结果使用自由铰链 E0 14/26、R0c 17；当前绘图代码却已改为平台，并读取共用 selected。通过保存 SSE 与重新拟合核对，本项目明确恢复探索图/有序模型的自由铰链，读取 `unconstrained_selected`；最终模型继续使用重新估计的平台。`pvo_rows.json` 比 CSV 更旧，还标为 R0c 16；本项目 JSON 重新从 CSV 生成，避免沿用旧表。数值核对记录这种版本差异。
4. E0 平台保留阵风×气压，因此“高风速斜率恒零”仅适用于平均气压下的主效应。低风速斜率可以为负；代码没有把它约束为水平。文字“flat below onset”“physics requires”不是模型中已经验证的结论。
5. 最终 R0c 排除 8,661 条零客户数记录，使用 51,173 条；探索比较/事件脆弱性仍使用 59,834 条，这是原流程的不同分析范围，不是数据不一致。66.5% 恰为一小时是记录特征，单凭此特征不能断言所有记录机制。
6. R0c 平台比较的全样本二次参考去掉阵风×气压，而嵌套 CV 的二次参考仍保留它；原样复现并记录，不静默统一。
7. 最终回归、时间分样和 R² 分解使用已选好的结点；只有专门的结点/平台嵌套 CV 在折内重选。时间分样不是独立的结点确认实验。
8. 事件对数正态的负 beta、接近零斜率、溢出 theta 等属于拟合诊断；必须保留真实结果，不能为了曲线看起来合理修改参数。背景率 p0 也不能直接等同“技术故障真实发生率”。
9. 两个 JS 依赖原作者机器的 `/home/claude`、`python3`、未提供的 refs.md 与四份制表 JSON。本项目替换为当前结果、自己的原稿和 PNG 头尺寸读取；增加全部制表生成器。
10. 文档模板保留导师编写的历史论述，首页明确其范围。动态表格/插图均来自本次计算，描述统计也改为实时生成；其他手填数字、因果解释、首创性主张和参考文献仍需下一轮论文修改。`COMPUTED_RESULTS.md` 与 CSV/JSON 是本轮数值依据。

11. 长稿中原来手填的模型比较表也改为从本次比较/结点/平台结果计算：剖面 BIC 加回共同高斯常数后与 statsmodels 对齐，明确 E0 平台额外含温度平方、结点模型采用嵌套 CV；R0c 平台使用不同的正客户数样本，单元格明确标注不可直接比较。因此该表的 ΔBIC 不机械照抄旧稿手填数字。

## 验证与依赖

使用项目 conda 环境（numpy/pandas/scipy/statsmodels/matplotlib/openpyxl）。文档使用 Codex bundled Node `docx` 与 Python `python-docx`，可用 `NEW_DOC_NODE`、`NEW_DOC_NODE_MODULES`、`NEW_DOC_PYTHON` 替换到另一台机器的已安装依赖。这属于库依赖，不是导师项目依赖。

数值核对程序在 `docs/new_analysis/` 单独运行，允许只读导师保存产物作预期值，绝不参与生产生成流程。比较 CSV 数值/结构、JSON 递归值、XLSX 工作表、PNG 清单和尺寸；对迭代优化与版本差异逐项报告，避免声称所有文件逐字节相同。开发和验收结果在 `LOG.md` 后续步骤记录。
