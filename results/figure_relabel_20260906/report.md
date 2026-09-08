# 工作命令 #52：全部图表内部代号排查与重新生成

逐一打开全部12张图表（Figure 1/2/4/5/6a/6b/7/8/9/10/D1/H1）对应的**绘图脚本源代码**（非图片描述报告），检查每一处会渲染到图片可见文字的调用（`title`/`xlabel`/`ylabel`/`legend`/`annotate`/`text`/`set_xticklabels`/`set_yticklabels`/`bar(labels=...)`），核对是否有内部代号被直接写入。只读访问已有数据和模型结果，未重新拟合任何模型、未改变任何已发布的统计数字——重新生成的8张图片中的全部数字均与既有版本逐一核对一致，只有文字标签发生变化。

## 排查结果总表

| 图表 | 排查结果 | 具体代号 | 出现位置 |
|---|---|---|---|
| Figure 1（study area map） | **未发现问题** | — | — |
| Figure 2（distribution） | **发现问题** | `customers_v2` | 面板(a)的x轴标签 |
| Figure 4（dose-response，现为log尺度版本） | **未发现问题** | — | — |
| Figure 5（variance decomposition） | **发现问题** | `E0`、`R0c` | 图例（legend）两个条目 |
| Figure 6a（regional customers map，现为log尺度版本） | **未发现问题** | — | — |
| Figure 6b（regional duration map，现为log尺度版本） | **未发现问题** | — | — |
| Figure 7（magnitude comparison） | **发现问题** | `E0`、`R0c` | 横向条形图的3条y轴行标签（其中2条含"R0c"，1条含"E0"） |
| Figure 8（weather subsample comparison） | **发现问题** | `E0`、`R0c`、`weather_natural` | 两个面板各一处文字注释（E0/R0c）+ 两个面板的x轴刻度标签（weather_natural，各1处，共2处） |
| Figure 9（storm validation） | **发现问题** | `E0`、`R0c`、`p99` | 两个面板各一处文字注释（E0/R0c），面板(b)注释内另含"p99 truncation"字样 |
| Figure 10（robustness forest） | **发现问题** | `E0`、`R0c`、`z_gust_0h_sq` | 全部8条y轴行标签（E0/R0c各4条）+ x轴标签括号内的变量名 |
| Figure D1（composition effect，附录D） | **发现问题**（命令未列出的代号） | `n_stages` | 面板(a)图例的4个条目 |
| Figure H1（curve shape comparison，附录H） | **发现问题** | `E0`、`R0c` | 两个面板各一处文字注释 |

**汇总：12张图表中，4张（Figure 1、4、6a、6b）确认干净，8张（Figure 2、5、7、8、9、10、D1、H1）确认存在内部代号被渲染进图片可见文字，全部8张已修改脚本并重新生成。**

---

## 逐图详细修改说明

### Figure 2（distribution）
- **发现**：面板(a) `xlabel="Affected customers (customers_v2)"`——含内部字段名`customers_v2`。其余三个面板（(b)/(c)/(d)）本就已使用正式说法，未受影响。
- **修改**：`"Affected customers (customers_v2)"` → `"Affected customers"`。

### Figure 5（variance decomposition）
- **发现**：`ax.bar(..., label="E0 (exposure)", ...)`、`ax.bar(..., label="R0c (recovery, gust-before-customers order)", ...)`，两条图例直接渲染。
- **修改**：`"E0 (exposure)"` → `"Exposure margin"`；`"R0c (recovery, gust-before-customers order)"` → `"Recovery margin (gust-before-customers order)"`。

### Figure 7（magnitude comparison）
- **发现**：`LABELS`列表中3条y轴行标签分别含"(E0, 1st–99th pct. of gust)"、"(R0c, customers fixed)"、"(R0c, gust fixed)"，经`ax.set_yticklabels(LABELS)`直接渲染。
- **修改**：三条依次改为"(exposure margin, 1st–99th pct. of gust)"、"(recovery margin, customers fixed)"、"(recovery margin, gust fixed)"。日志文字中的`gust->E0`/`gust->R0c`同步改为`gust->exposure`/`gust->recovery`（仅打印日志，不影响图片，一并做了清理）。

### Figure 8（weather subsample comparison）
- **发现**：面板(a)/(b)各有一处`ax.text(...)`注释直接写"E0 (exposure)"/"R0c (recovery)"；面板(a)的`ax.bar(labels_a, ...)`和面板(b)的`ax.set_xticklabels([...])`均含字符串"weather_natural\n(corrected)"，两处x轴刻度标签均渲染该内部字段名。
- **修改**："E0 (exposure)" → "Exposure margin"；"R0c (recovery)" → "Recovery margin"；两处"weather_natural\n(corrected)" → "Weather-related\n(corrected)"。

### Figure 9（storm validation）
- **发现**：面板(a) `ax.text(..., "E0 (exposure)", ...)`；面板(b) `ax.text(..., "R0c (recovery)\nopen triangles = excluded by p99 truncation", ...)`——后者除内部代号外还含"p99"这一未在正文中以此形式出现的技术缩写（论文正文用"99th percentile"表述）。
- **修改**："E0 (exposure)" → "Exposure margin"；"R0c (recovery)\n...excluded by p99 truncation" → "Recovery margin\n...excluded by 99th-percentile truncation"。
- **附带视觉说明**：由于替换后文字略长于原文，面板(b)左上角两行注释文字与右侧图例("Storm"标题+"Arwen"等风暴名)在极少数渲染场景下有轻微重叠（见发送的图片），这是文字加长带来的排版副效应，与原版本的重叠程度基本相当（原文字长度已接近），未做任何超出文字替换本身的排版调整，如需完全消除重叠建议网页端后续单独调整图例位置或字号，本命令未擅自处理。

### Figure 10（robustness forest）
- **发现**：`rows`列表全部8行的`model`字段为字面字符串"E0 (exposure)"/"R0c (recovery)"，经`f"{m} – {l}"`拼接后通过`ax.set_yticklabels(...)`渲染为全部8条y轴行标签；另外x轴标签`"Gust quadratic-term coefficient (z_gust_0h_sq), 95% CI"`中的`z_gust_0h_sq`是实际代码变量名（命令#52第0节明确列出这类问题需要一并核查）。
- **修改**："E0 (exposure)" → "Exposure margin"；"R0c (recovery)" → "Recovery margin"；x轴标签删去"(z_gust_0h_sq)"这一变量名，改为"Gust quadratic-term coefficient, 95% CI"。
- **重要说明**：本次只修改文字标签，**未采用**命令#51已经识别并给出选项的"development sample"行置信区间构造问题（逆方差汇总5折训练集导致区间被低估）——那是一个独立的、尚待网页端决定采用哪个选项的统计问题，与本命令"纯文字标签修正、不改变任何统计数字"的范围不同，本次重新生成的Figure 10在CI构造上与目前已发布版本完全一致，只是文字标签不同。

### Figure D1（composition effect，附录D）——**命令未列出、核实中发现的额外代号问题**
- **发现**：面板(a)图例的4个条目通过`GROUP_LABELS`字典渲染为"n_stages = 1"、"n_stages = 2"、"n_stages = 3-4"、"n_stages ≥ 5"，直接使用了原始变量名`n_stages`。核对论文正文（Appendix D及2.2/4.1节），全文从未使用"n_stages"这一写法，一律表述为"the number of restoration stages"。
- **修改**：图例4个条目分别改为"1 restoration stage"、"2 restoration stages"、"3–4 restoration stages"、"5+ restoration stages"。`GROUP_ORDER`/`GROUP_COLORS`/`GROUP_MARKERS`三个字典的**键**（如`"n_stages=1"`）只是内部查找用的Python字典键，不会渲染到图片上，予以保留未改动。

### Figure H1（curve shape comparison，附录H）
- **发现**：`ax.text(..., title, ...)`渲染的面板标注文字为"Exposure margin (E0)"/"Recovery margin (R0c)"。
- **修改**：去掉括号内代号，改为"Exposure margin"/"Recovery margin"。

---

## 未发现问题的4张图（逐一确认，非假设"没提到就没问题"）

- **Figure 1**：逐行核查`figure1_study_area.py`全文，无任何`E0`/`R0c`/`customers_v2`/`duration_B`/`weather_natural`/`technical_asset`/`WT`/`z_gust`字样出现，图内文字仅涉及地图比例尺/指北针/州名等（复用`figure_style.py`共享模块，该模块本身也逐行核查确认干净）。
- **Figure 4（现为命令#47的log尺度版本）**：脚本中`E0`/`R0c`/`z_gust_0h`等字样全部出现在变量名、DataFrame列名、`log_step()`控制台日志或`model_label`（只写入CSV的"model"列，不渲染到图片）中；实际调用`ax.set_xlabel`/`ax.set_ylabel`/`ax.text`的三处渲染文字（"log(1 + affected customers)"、"log(restoration duration)"、"turning point\n{...} m/s"、"quadratic term significant..."）均已核实为正式说法，无代号泄漏。
- **Figure 6a/6b（现为命令#47的log尺度版本）**：色阶图例标签（`legend_kwds={"label": cbar_label}`）已核实为"log(1 + affected customers)"/"log(restoration duration)"，`value_col`/`out_stub`两个参数分别只用于选择DataFrame列和生成文件名，不渲染到图片。

---

## 验收标准逐项确认

- 全部12张图表（Figure 1/2/4/5/6a/6b/7/8/9/10/D1/H1）已逐一打开脚本源码确认排查结果，无遗漏，4张确认干净的图表均给出了具体核查依据（不是简单假设未提及即无问题）。
- 8张确认存在问题的图表，修改后的脚本已重新核查确认不再包含任何内部代号字符串（人工核对代码+目视核对3张关键重新生成图片，其余5张通过运行日志数值比对确认脚本无误）。
- 每张重新生成的图表均给出了具体的修改前后对比说明（见上方逐图小节）。
- 排查中发现命令未列出的额外代号问题（Figure D1的`n_stages`、Figure 10 x轴标签中的`z_gust_0h_sq`、Figure 9注释中的"p99"缩写），均已如实报告并一并修正。

## 产出文件

`figures/`目录下8张图的PNG（300dpi）+PDF：`Figure_2_distribution`、`Figure_5_variance_decomposition`、`Figure_7_magnitude_comparison`、`Figure_8_weather_subsample_comparison`、`Figure_9_storm_validation`、`Figure_10_robustness_forest`、`Figure_D1_composition_effect`、`Figure_H1_curve_shape_comparison`；脚本目录`claude_branch/scripts/figure_relabel_20260906/`下对应8个`.py`文件（均在注释中标明"RELABEL"具体改动点，与既有生产脚本并存、原脚本未被覆盖）。
