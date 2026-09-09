# 工作命令 #33：全文图表风格规范 + Figure 1、2、6 制作

## Step 0：统一图表风格规范

新建共享样式模块 `claude_branch/scripts/final_combined_analysis/figure_style.py`，供本命令及未来所有图表复用：

- **尺寸**：单栏 90mm / 双栏 185mm（RESS/Elsevier规范），提供 `mm_to_in()` 换算函数。
- **分辨率/格式**：矢量PDF + 300dpi PNG 双格式（`save_fig()`统一输出，Figure 6沿用命令#21原有600dpi PNG设定，见下方说明）。
- **字体**：无衬线，优先Arial，回退DejaVu Sans。**已核实本机确实安装了Arial**（`matplotlib.font_manager`字体列表中确认存在"Arial"，与DejaVu Sans变体并列），因此本命令全部三张图实际渲染字体为**Arial**，未触发回退。
- **字号**：坐标轴标签9pt、刻度标签8pt、图例7pt、正文字号8pt；粗体面板标签(a)(b)另设`panel_label()`辅助函数（9pt）。
- **配色**：连续型数据用viridis（Figure 1 hexbin密度）；分类数据避免红绿对比（Figure 2用青绿`#1b9e77`/橙色`#d95f02`区分customers/duration两组，非红绿对比）；地图类延续项目一贯的Oranges配色（Figure 6，与命令#21保持完全一致，未更改）。
- **图注（caption）**：本命令范围不含图注文字撰写，留待网页端后续统一撰写。

## Figure 1：UKPN服务区域地图 + 事件密度

脚本：`claude_branch/scripts/final_combined_analysis/figure1_study_area.py`

- 使用命令#21`combined_sample_builder.build_combined_samples()`构建的**完整最终样本（n=60,453）**，从`rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv`按`Incident Reference`补齐经纬度（**全部60,453条事件均有有效坐标，零缺失**）。
- 三个UKPN许可区域边界取自`data/dno_license_areas_20200506/DNO_License_Areas_20200506.shp`，按`LongName`筛选`"UKPN (East)"`/`"UKPN (London)"`/`"UKPN (South)"`并标注EPN/LPN/SPN简称。
- **密度渲染方式**：命令明确要求避免约6万点的原始散点重叠问题，本命令采用**hexbin（gridsize=60, viridis配色, 对数计数`bins="log"`）**，未使用原始散点图。渲染结果视觉核实**无过度重叠、伦敦热点清晰可辨、区域边界与密度叠加层次分明**，满足验收标准中"避免过度重叠"这一具体要求。
- 全部坐标系统一转换至EPSG:27700（British National Grid），与项目一贯地图输出保持一致。
- 输出：`Figure_1_study_area_map.pdf` / `.png`（300dpi，双栏尺寸185mm宽）。

## Figure 2：客户影响与恢复时长分布（2×2面板）

脚本：`claude_branch/scripts/final_combined_analysis/figure2_distribution.py`

- 数据来源同为命令#21最终合并样本：customers_v2（E0可用样本，n=60,437）、duration_B（R0c可用样本，n=59,834）。
- 参照Mukherjee et al. (2018) Fig 10/11风格，采用**直方图+核密度估计（scipy.stats.gaussian_kde）**叠加，而非单纯KDE。
- 四面板：(a) customers_v2原始值、(b) log1p(customers_v2)、(c) duration_B原始值、(d) log(duration_B)。
- (a)/(c)两个原始值面板为提升可读性，展示0-99百分位区间（p99_customers=1515.0、p99_duration=116.98h），完整值域另在图注文字中说明（本命令范围内以脚本日志形式记录，供网页端撰写图注时引用）。
- 输出：`Figure_2_distribution.pdf` / `.png`（300dpi，双栏尺寸185mm宽）。

## Figure 6：区域基线差异地图（重新出图，仅改标题文字）

脚本：`claude_branch/scripts/final_combined_analysis/figure6_regional_map.py`

**严格遵循命令#33"仅改标题文字，其余数据/配色/投影/图例设置均不变"这一硬性约束**：

- **数据**：直接读取命令#21已产出的`04_基线区域差异地图数据.csv`（列：`LAD21CD, pred_customers_v2, pred_duration_B`），**未重新拟合任何模型、未重新计算任何预测值**。载入后确认111个LAD有predicted customers_v2、111个有predicted duration_B，与命令#21原始产出完全一致。
- **配色/投影/图例**：完全复用命令#21`step4_baseline_regional_map.py`中的`quantile_limits(0.00, 0.98)`（0-98百分位色阶裁剪）、`Oranges`配色、EPSG:27700投影、`missing_kwds`灰色缺失区域样式、图例样式，**代码逻辑逐行对照未做任何改动**。
- **唯一改动——标题文字**：
  - 旧：`"Baseline regional difference in predicted customers_v2\n(fixed reference weather; region covariates vary)"`
  - 新：`"Baseline regional difference in predicted affected customers\n(fixed reference weather; region covariates vary)"`
  - 旧：`"Baseline regional difference in predicted duration_B\n(fixed reference weather and customers_v2; region covariates vary)"`
  - 新：`"Baseline regional difference in predicted restoration duration\n(fixed reference weather and customers_v2; region covariates vary)"`
  - 括号内说明文字（fixed reference weather等）按命令要求原样保留，仅将变量代号替换为读者友好的英文表述。
- **文件名**：按命令要求从`04a`/`04b`改为`Figure_6a_regional_customers`/`Figure_6b_regional_duration`，避免与命令#21旧文件混淆。
- 输出：`Figure_6a_regional_customers.pdf`/`.png`、`Figure_6b_regional_duration.pdf`/`.png`（600dpi PNG，与命令#21原图分辨率设定一致；同时补充PDF矢量版）。
- **视觉核实**：两张图与命令#21原图`04a`/`04b`并排比对，色阶范围、地图轮廓、图例刻度完全一致，仅标题文字按要求变更，未发现任何数据或视觉设计层面的意外改动。

## 产出文件汇总

全部写入 `claude_branch/results/final_combined_analysis/figures/`（新建目录）：

- `Figure_1_study_area_map.pdf` / `.png`
- `Figure_2_distribution.pdf` / `.png`
- `Figure_6a_regional_customers.pdf` / `.png`
- `Figure_6b_regional_duration.pdf` / `.png`

脚本文件（均写入 `claude_branch/scripts/final_combined_analysis/`）：`figure_style.py`、`figure1_study_area.py`、`figure2_distribution.py`、`figure6_regional_map.py`。

## 验收标准逐项确认

- 三张图尺寸/字体/配色均按Step 0规范执行；Arial字体确认可用并实际生效，未回退DejaVu Sans。
- Figure 1成功避免原始散点重叠问题（采用hexbin对数密度渲染），已如实说明选用理由。
- Figure 6严格做到"仅改标题文字"，数据、配色、投影、图例、其余视觉设计均未改动，文件名按要求重命名避免与命令#21旧文件混淆。
- 全部图表均以PDF（矢量）+ 300dpi（Figure 1/2）或600dpi（Figure 6，沿用命令#21原设定）PNG双格式交付。
- 图注文字撰写不在本命令范围内，留待网页端后续处理。
