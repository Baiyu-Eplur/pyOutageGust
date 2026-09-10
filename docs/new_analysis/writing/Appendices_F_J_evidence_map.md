# Appendices F–J 写作证据映射

本文件是 APP-FJ-DRAFT 的内部写作记录，不是论文附录正文，也不替代项目的主张—需求—产物登记。唯一可编辑英文稿为 [Appendices_F_J_draft.md](Appendices_F_J_draft.md)。A–E、正文及结果目录不作修改。

## 权威来源与写作合同

本轮采用用户随附的 APP-FJ-DRAFT 指令，接受已完成的科学产物。既有四步台账以 `docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令 (4).md` 第14节的接受结果和更正判断为准；其中旧的“暂不成文”停止安排由本轮明确写作授权取代。`论文整合计划_v9_附录成文与正文衔接.md` 提供结构，但其中旧 J03 缺口/回滚状态不再控制写作。

实际读取的正文为 `results/new/20260909183317/results/paper/Extended_paper_draft.docx`，以直接 body 段落定位 §3.1、§3.4、§4.3–4.5 及已核实参考文献。A–E 初稿与 `APPENDIX_A_E_WRITING_RECORD.md` 只用于术语、样本、符号、编号和风格参考。正文待改记录实际位于 `C:/Users/haoya/Downloads/附录补全过程_正文待修改记录_供导师讨论.md`，使用其中 M01–M24 和 GI-W/H-W 的原映射，不另造正文修订台账。

已接入现有 `results/Appendix/claim_evidence_map.csv`、`appendix_requirements.csv`、`requirement_result_map.csv`、`figure_table_register.csv`。下文显示编号继承现有登记，因此首次出现次序不必是数字递增；本轮没有改动登记表。

| 章节合同 | 读者问题与拟写结论 | 授权证据 | 推断边界与章节衔接 |
| --- | --- | --- | --- |
| F | 明确四个最终均值模型，完整展示系数、实际聚类区间及顺序解释度 | F01/F02/F03，当前 H 的 OLS 参考区间；必要正式设计函数 | 同系数不同协方差；F.3 天气阶梯不误称最终天气函数的分解。C/D 负责模型/结点比较，G 负责预测 |
| G | 小总体偏差与大个体误差并存，分箱残差并非处处为零 | 当前 GI 指标、预测分箱、阵风分箱和两张正式图 | 固定结点 LAD-OOF 不混入 nested CV；非聚类 SEM 不当作 two-way 带 |
| H | 四个替代均值模型多数关键项方向保持，近零恢复线性项有明确例外；旧严重度探索身份保留 | 当前四 GLM、旧序数/条件曲线、当前四样本原分箱频率 | 不跨均值尺度排名；旧恢复不当作当前样本；天气粗分箱旧频率未对齐，不补写确认句 |
| I | 固定风暴窗口下，平均误差与个体误差、不同风暴偏差方向需分别报告 | GI 风暴窗口、样本、样本内预测、正式散点图 | 样本内描述，不是风暴留出；重叠窗口并集去重；超 cap 点只展示 |
| J | 完整呈现八任务下源构造、聚合、持续性与冻结时间检验的结果 | 当前 J03；已接受 DD-AGG01/DD-DUR01/DD-TIME01 的 J 导出 | 保留 PROXY 主线；条件区间不含全部时空不确定性；回顾性时间检验不当作事前预警 |

## 小节—证据—显示编号

以下路径相对项目根目录。CSV 的 `combination`、`model`、`target` 等为内部定位键，不进入读者稿。表格所读取的全部列名、行数及路径另见 [table_sources.json](checks/fj/table_sources.json)。它是格式派生清单，不是新的研究结果清单。

| 小节 / 用途 | 样本、模型与评价身份 | 来源及定位 | 显示编号 |
| --- | --- | --- | --- |
| F.1 完整系数与两套区间 | E0_all 60437、R0c_all 51173、E0_weather 9857、R0c_weather 9254；固定最终 OLS | `F/tables/F_FULL_COEFFICIENTS.csv`，four `margin/sample`，two-way 全112项；LAD-only 全体56项；`F/tables/F02_COEFFICIENT_COMPARISON.csv` 天气56项；`H/tables/H03_FULL_COEFFICIENTS.csv` 的两组 `OLS_reference` 区间 | Table F1(a–d) |
| F.1 设计及尺度 | 全体14/25平台、二次恢复；天气11/24平台、固定11单结点；标准化后平方/交互 | `F/data/F02_SPECIFICATIONS.csv`、F02 两份 DESIGN_METADATA；`G/data/GI_PREPROCESSING.json`；`analysis_new/final_models.py:final_design` 与 `weather_only_regression.py:build`，只读方法片段 | F.1、Eq. F.1 |
| F.2 聚类 SE 改变 | 天气同X/系数；df104/103；全体df110 | `F/tables/F02_COEFFICIENT_COMPARISON.csv`，全部项及包含 `gust` 的6项；`F/data/F02_MODEL_STATUS.csv`；`F/logs/F02_EXECUTION_REPORT.md` | Table F3；F1 全项区间 |
| F.3 顺序 OOF R² | 当前四样本；天气子集沿用全体 gust design；固定五折 | `F/tables/F03_R2_DECOMPOSITION.csv` 全14行；`analysis_new/paper_extras.py:groups_design,cv_r2` 及其四样本调用循环。天气末级 .044280/.281245 与 G 最终模型不混写 | Table F2；Eq. F.2 |
| G.1 当前指标与有限比较 | `final` 的四组合×in_sample/LAD_OOF；`paper`四组合和天气`hinge`的LAD_OOF | `G/tables/GI_PREDICTION_METRICS.csv` 对应14行 | Table G4(a,b) |
| G.2 均值与个体离散 | 四个正式样本，固定结点 LAD-OOF；各候选自己的预测分位箱 | `G/data/GI_CALIBRATION_BINS.csv`；`G/figures/GI_PREDICTION_CALIBRATION.png`；`G/data/GI_FIGURE_AXES.json` | Figure G2 |
| G.2 最短观察组 | `observed_duration_group=T<=1h`、`prediction_type=LAD_OOF`，3775/1083 | `G/data/GI_SHORT_DURATION_DESCRIPTION.csv` 两行，bias 2.449839/2.148718；是按已观察时长分组 | 文字，不新增显示编号 |
| G.3 三种残差、箱支持与 SEM | control_residual、final in_sample、final LAD_OOF | `G/data/GI_GUST_BINS.csv`；`G/tables/GI_FINAL_GUST_RESIDUALS.csv` 当前52行；`G/figures/GI_GUST_RESIDUALS.png` | Figure G1 |
| H.1 四 GLM 定义和离散度 | 仅 all 样本；原始 C 或小时 D_B 的 log mean | `H/tables/H03_MODEL_DEFINITIONS.csv` 四候选；`H/data/H03_E0_all_NB2_DIAGNOSTICS.json`、E0_all_Tweedie、R0c_all_Gamma、R0c_all_Tweedie 同名 DIAGNOSTICS；各 SPECIFICATION；当前 H03 执行报告推断段 | Table H7 |
| H.1 关键项全部比较 | 相同当前设计；OLS变换均值 vs GLM原响应均值；t110 | `H/tables/H03_GUST_COMPARISON.csv` 全12行；`H/tables/H03_FULL_COEFFICIENTS.csv` | Table H6 |
| H.2 序数类别与既有阈值回归 | E60437、旧R59834；14/26自由双结点与17单结点 | `H/tables/H_ORDINAL_SUMMARY.csv` 全9行；`H/tables/H_CONDITIONAL_COEFFICIENTS.csv` 中 ordinal 和 cumulative logit，排除另一旧NB伴随探索；H03_EXISTING_H2_H3_SOURCES 记录实际端点和原控制基 | Tables H1、H2 |
| H.3 旧 lognormal 参数 | E60437/9857；旧R59834/9806；common/free beta 分开 | `H/tables/H_CONDITIONAL_LOGNORMAL.csv` 全18行；H03 既有来源记录及执行报告的优化/极端参数说明 | Table H3；Eq. H.1 |
| H.3 当前原分箱经验频率 | 当前四样本；E严格>100、R严格>12h；全13原箱，各样本分开 | `H/tables/H03_EVENT_CONDITIONAL_FREQUENCIES.csv`，按combination/threshold筛选52行；直接读取分子分母，未做粗箱重新合并 | Table H4 两面板 |
| I.1 窗口与样本 | 七窗口及去重并集；all E/R；28点仅展示 | `I/data/GI_STORM_WINDOWS.csv` 全7行；`I/tables/GI_STORM_SAMPLES.csv` 全8行 | Table I3 |
| I.3 各风暴与并集指标 | `prediction_type=in_sample`、`excluded_from_primary_metrics=False` 两组合共16行 | `I/tables/GI_STORM_METRICS.csv`；`I/figures/GI_STORM_FINAL_SCATTER.png` | Table I2；Figure I1 |
| J.1 暴露与标签 | 111×1096；any含零，其他max incident strict threshold | `J/tables/J_PROXY_DEFINITIONS.csv`；`J/tables/J_PROXY_LABELS.csv` 全8行 | Table J2；Eq. J.1 |
| J.2 独立网格定义 | polygon centroid、hourly gust、UTC日最大；111查询位置映射52格点 | `J/tables/J_INDEPENDENT_WEATHER_DEFINITIONS.csv`；`J/tables/J02_GRID_CELLS.csv`、J02_CENTROIDS；当前 J03 协议/报告 | J.2 方法 |
| J.2 八任务正式匹配评分/区间 | 同LAD-day/标签/五折；当前稳定拟合OOF；paired LAD固定预测条件区间 | `J/tables/J03_PAIRED_METRICS.csv` 全8行，含合并后的当前区间；`J03_PAIRED_INTERVALS.csv`；`J03_CALIBRATION.csv` | Table J28（含登记Table J27的区间，不重复列整表）；Figure J3 |
| J.3 五种聚合及八任务 | 同小时气象/位置/标签/折号，仅改变每日summary | `J/tables/J_FROZEN_EXPERIMENT_DEFINITIONS.csv` 中DD-AGG01；`J04_METRICS.csv` 全40行；`J04_PAIRED_UNCERTAINTY.csv` 非参考32行 | Tables J7、J8 |
| J.4 两种持续性增量 | training LAD-hour q90 τ；M0/M1/M2分别估计；同OOF | 同definitions中DD-DUR01；`J05_THRESHOLDS.csv`；`J05_METRICS.csv` 全24行；`J05_PAIRED_UNCERTAINTY.csv` 非参考16行 | Tables J10、J11；Eqs. J.3–J.4 |
| J.5 冻结时间全部任务评分 | 101232开发、20424评估；基准开发率；评估不重新拟合 | `J/tables/J_TIME_METRICS.csv` 全8行；已接受执行回执和DD-TIME01 review；`J_TIME_DEVELOPMENT_FIT.csv` 作身份参考，不将开发参数替换全样本参数 | Table J13；Eq. J.5 |
| J.5 主要/次级月度及校准 | 同批冻结预测；开发分位切点；9月仅一天 | `J/tables/J_TIME_MONTHLY.csv` 两个>100任务共14行；`J_TIME_CALIBRATION_BINS.csv` 两任务最高非空箱及全箱定义；`J/figures/J_TIME_CALIBRATION_MONTHLY.png` | Table J14；Figure J1 |
| J.5 支持摘要 | 已生成两期proxy统计；评估超出开发范围0 | `J/tables/J_TIME_SUPPORT.csv` 两行 | Table J15 |

表内结果路径的 `F/…` 至 `J/…` 均位于项目 `results/Appendix/` 下。图形在英文稿中使用从写作目录可解析的 `../../../results/Appendix/...` 相对路径。

## 图片实际查看与编排取舍

实际打开查看了 G 的 `GI_PREDICTION_CALIBRATION.png`、`GI_GUST_RESIDUALS.png`，I 的 `GI_STORM_FINAL_SCATTER.png`，J 的 `J03_PRIMARY_CALIBRATION.png`、`J_TIME_CALIBRATION_MONTHLY.png`，以及 `J03_BRIER_COMPARISON.png`。前五张进入稿件；第六张与 Table J28 的评分/区间重复，未再放入。图注按实际横纵轴、颜色、稀疏/空箱、显示点和区间身份撰写。没有重画图、重新生成区间或执行图形所对应的实验。

`GI_RESPONSE_COMPONENTS` 未纳入稿件。当前任务已有充分残差和预测图；不把平移曲线的旧带解释为传播参考点不确定性的差值置信区间，不要求为本稿补算。H未从不完整cutpoints构造序数曲线。F以可编辑完整表为主，不新增形式重复的图。

## 文字复用、解释选择与待接正文位置

五章连续英文论述为本轮新撰；复用 A–E/正文已接受的术语、符号、样本身份、公式定义和参考文献 [29]，没有复制旧报告的执行时间线。现有英文材料中准确的模型名称和方法表述予以沿用。没有新造参考文献；[29] 的 DOI 沿用 A–E 已核实记录。

- F.1/F.4 与正文 §3.1 对应 M01；F.2 对应 §3.4/Table5 的 M08/M09；F.3 对应 §4.3。天气R²规格区别只在稿中限定来源，未修订F03产物。
- G 对应 §3.3、§4.1–4.2、Figures3/5/6 的 M07、M10–M14 / GI-W01–W06、W09。
- H 对应 §3.1 与 §4.4 的 M01/M02/M15/M16 / H-W01–W07。H-W03仅保留局部未对齐，不替换原天气数字。
- I 对应 §4.5 的 M17/M18 / GI-W07–W08；只引用已确认窗口和去重事件数，不写原8.2%/27天/14.7%。
- J 对应 §3.5、§4.5、§5.5 的 M19–M23；与E的分期分别拟合保持分工，保留同日PROXY主线。
- M24的正文指向F–J新小节安排只登记在此和作者说明中，不执行正文修改。

## 可复现派生与写作检查范围

`checks/fj/format_tables.py` 只读取保存的结果CSV，筛选/排列/格式化为20个表格块（Table H7为依据四份已存诊断直接逐值整理的定义表）。所有F系数均保留。唯一新派生的推断数值是全体模型LAD-only 95%区间端点：`coef ± scipy.stats.t.ppf(0.975,110) × saved_se_lad`；two-way和天气区间直接读取既有表。没有重算模型或经验频率，没有改变任何原始CSV值。表格脚本默认仅检查稿件表块与上述来源的对应，不覆盖人工正文。

独立运行方式（在项目根目录）：

```powershell
& C:/Users/haoya/.conda/envs/pyoutagegust/python.exe -X utf8 -B docs/new_analysis/writing/checks/fj/format_tables.py
& C:/Users/haoya/.conda/envs/pyoutagegust/python.exe -X utf8 -B docs/new_analysis/writing/checks/fj/check_writing.py
```

技能的任务级 adapter 位于 `checks/fj/manuscript_state.json`，仅记录本轮合同和交付检查，不取代 A–E 的状态文件或项目科学登记。作者自查依次覆盖结构、证据身份、英文表达与交付完整性；这是一轮有限写作核对，不是独立科学审查。具体结果、最终候选指纹和诊断处置见 `checks/fj/writing_checks.json`、`candidate_audit.json` 与 `CHECK_RECORD.md`。对结果目录的哈希对照仅验证本轮未改动来源，不声称独立复算了既有科学结果。
