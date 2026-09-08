# 工作命令 #49：最终收尾核实（Moran's I空间计算单元 + 全部引用细节）

本命令为当前修复链路的最后一轮核实。全部核实均基于官方来源直接查证（ONS官方数据集页面/交互式文章、源Excel文件"Notes"工作表、Ofgem官方PDF、arXiv官方元数据、OSTI.GOV、ASCE/开放气象API官网），能核实到什么程度就更新到什么程度，无法核实的均如实说明原因，未编造任何数字或日期。

---

## 一、Moran's I空间计算单元核实

### 结论先行

**Moran's I是在LSOA（Lower Layer Super Output Area，最细粒度小区）层级计算的，但不是"全国一张LSOA邻接网络算完后按LAD汇总/取均值"，也不是"LAD与LAD直接邻接"，而是第三种、命令背景两个假设都未完全覆盖的方式：为每一个LAD单独计算一个Moran's I值，该值只反映该LAD内部各LSOA之间收入剥夺水平的空间聚集程度，空间邻接关系被严格限制在该LAD自己的边界之内，不跨越LAD边界。**

### 证据一：ONS官方交互式文章明确说明"LAD边界"如何影响Moran's I数值

直接访问ONS官方交互式文章*"Exploring local income deprivation"*（`https://www.ons.gov.uk/visualisations/dvc1371/`，发布于2021年5月24日，与命令#49背景所指数据集为同一次发布）原文（用Browser工具实际打开页面提取，非转述）：

> "This shows how Moran's I is affected by local authority boundaries. For example, the southern part of Sefton has a high level of deprivation, although this area is effectively a continuation of central Liverpool."

这段话是**决定性证据**：Sefton南部与利物浦市中心在地理上是连续的贫困片区，如果Moran's I是按"全国LSOA邻接网络"或"LAD与LAD邻接"计算的，跨越Sefton/Liverpool边界的这一连续贫困片区理应被识别为空间聚集的一部分；但ONS原文明确说这一现象**因LAD边界而被割裂**，即Sefton的Moran's I计算**根本不会看到**利物浦一侧的LSOA——这只有在"每个LAD各自独立地、只用自己内部的LSOA邻接网络计算Moran's I"这一设计下才成立。

### 证据二：源数据文件"Notes"工作表关于Isles of Scilly排除理由的表述

直接读取项目已有的源文件`data/localincomedeprivationdata.xlsx`（本项目`IMD_merge.py`的直接数据来源）"Notes"工作表第29-33行原文：

> "Rankings: The deprivation gap for each local authority is calculated by subtracting the lowest 'Income Score (rate)' from the highest 'Income Score (rate)' within that local authority. ... Moran's I for income deprivation is calculated using the shapefile at https://data-communities.opendata.arcgis.com/datasets/5e1c399d787e48c0902e5fe4fc1ccfe3 (NB: Isles of Scilly must be removed from the dataset, because it only has one LSOA and so will not return a value for Moran's I)."

这句"因为Isles of Scilly只有一个LSOA，所以无法得出Moran's I值"是**第二个独立证据**，与证据一指向同一个结论：如果Moran's I是全国性的LSOA网络统计量或LAD-LAD邻接统计量，一个LAD内部只有几个LSOA完全不应该导致"无法计算"（全国网络中该LAD仍会有很多跨LAD的LSOA邻居，或该LAD仍会有相邻的LAD）；唯一能解释"只有1个LSOA就无法算出数值"的原因是：**该LAD的Moran's I是用它自己内部的LSOA互为邻居计算的，只有1个LSOA意味着没有任何"内部邻居对"，统计量因此无定义**。

### 官方方法论文档出处（逐一列出，含无法进一步核实之处）

1. **数据集官方页面**：ONS, "Mapping income deprivation at a local authority level" 数据集页，`https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/mappingincomedeprivationatalocalauthoritylevel`，发布日期**2021年5月24日**，联系人Richard Prothero。（已用Browser工具实际访问确认页面内容与日期。）
2. **配套交互式文章**：ONS, "Exploring local income deprivation"，`https://www.ons.gov.uk/visualisations/dvc1371/`，同日发布，即上方证据一引文出处。
3. **源数据文件自带说明**：`localincomedeprivationdata.xlsx`"Notes"工作表第29-33行（即上方证据二引文出处）——这是唯一同时给出"计算方法"和"底层地理文件"线索的官方文字。
4. **底层GIS地理文件**（Notes工作表指向的实际计算用shapefile）：`https://data-communities.opendata.arcgis.com/datasets/5e1c399d787e48c0902e5fe4fc1ccfe3`——**本命令实际访问此URL，返回HTTP 404（已失效/下线）**，无法独立打开该shapefile核实其具体几何层级（是否确为LSOA边界）和其中记录的邻接关系构造细节。

### 关于空间权重矩阵类型（rook/queen/距离衰减）：**无法确切核实**

系统检索ONS官网、该数据集是否存在独立的"质量与方法说明（QMI）"文档（多数较新的ONS统计产品有此类文档，但本数据集/交互式文章**未找到对应的QMI页面**，可能因为这是一篇交互式数据新闻类文章而非正式统计发布）；上一条提到的底层shapefile链接已失效，无法逆向核实其邻接矩阵构造方式。**如实说明：未能核实ONS官方具体采用的是queen邻接、rook邻接还是距离衰减权重**。一般空间统计文献中，针对这类基于LSOA边界的小区域剥夺聚集度分析，queen邻接（共享顶点即算邻居）是更常见的默认选择，但这只是**一般惯例的参考**，不是针对本数据集的官方确认信息，不应在论文中作为"已核实"的事实呈现。

### 关于映射方式的说明（回应命令背景的具体追问）

命令背景问："如果确认是LSOA层级计算后映射到LAD，需要额外说明这个映射的具体方式（例如取LAD内全部LSOA的Moran's I均值，还是LAD本身作为一个空间单元参与更大范围的LSOA邻接网络计算）"——**以上两种映射方式均不成立**。真实情况是：不存在"先算全国LSOA网络、再映射到LAD"这一步骤；而是**每个LAD各自独立地把自己内部的LSOA集合当作一个封闭的小型空间网络，直接对这个封闭网络计算一次Moran's I，得到该LAD唯一的一个值**——LAD本身不是"参与更大范围LSOA网络"的一个空间单元，而是**限定LSOA邻接搜索范围的边界**。

---

## 二、参考文献细节核实（逐条）

### [1] Institute for Government, "Energy resilience"

**已核实**：确认URL `https://www.instituteforgovernment.org.uk/explainer/energy-resilience`当前可正常访问（HTTP 200）。页面显示更新日期**2026年3月20日**，作者Rosa Hodgkin、Dan Haile。**需向网页端说明的重要背景**：这是一个持续更新的"explainer"类型页面（内容提及"当前中东冲突"这类近期时事），不是一次性发布的静态文章，页面显示的日期更可能是"最近一次更新日期"而非首次发布日期，建议引用格式采用"[更新于2026年3月20日]"或类似措辞，而非视为固定不变的出版日期。

### [2] Ofgem, "Storm Arwen report"

**已核实**：完整标题确认为**"Storm Arwen Report"**（与当前引用文字一致，无需改动标题），Ofgem官网标注类型"Research"，发布日期**2022年6月9日**。URL `https://www.ofgem.gov.uk/research/storm-arwen-report`当前可正常访问（HTTP 200）。

### [11] RIIO-ED1 Annex F

**已核实**：直接下载解析官方PDF（`https://www.ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_regulatory_instructions_and_guidance_annex_f_-_interruptions.pdf`，确认可正常访问下载），封面页原文：

> "Reference: V5V6.10 ... Publication date: Original publication 18 June 2015 ... Revised publication: TBC ... Contact: Jack Ambler"

**确切发布日期为2015年6月18日**（原始发布日期；该文档封面自身注明"修订版发布日期：待定"，说明现存这一版本的封面仍以2015年6月18日为准）。

### [13] Open-Meteo Historical Weather API 官方引用格式

**已核实**：直接访问Open-Meteo官方Licence页面（`https://open-meteo.com/en/licence`）"Citation"章节，官方推荐的引用格式（提供APA/MLA/Harvard/BibTeX四种格式选项，页面默认展示的即为APA格式）：

> **Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software]. Zenodo. https://doi.org/10.5281/ZENODO.7970649**

建议将参考文献[13]从"Open-Meteo. Historical weather API [Internet]. [date unverified]"替换为这一官方软件引用格式，这比引用一个笼统的网站首页链接更精确、更符合学术引用规范。

### [15] ASCE/SEI 7 当前版本号

**已核实**：截至当前时间（2026年9月），ASCE/SEI 7的**现行版本为7-22**（2022年发布，取代7-16版）。ASCE通常按6年周期更新（上一版7-16，下一版理论上应为7-28），检索确认截至目前尚未发布7-28正式版，2026年内仍在为7-22发布补充勘误（Supplement 4/5，涉及不同章节，征求意见截止日期分别为2025年12月和2026年9月），**7-22仍是当前应引用的现行版本**，建议引用格式确定为"ASCE/SEI 7-22"。

### [16] arXiv:2107.00829 发表状态

**已核实，且有重要澄清**：直接访问arXiv官方摘要页（`https://arxiv.org/abs/2107.00829`），页面自带的"Journal reference"字段显示：

> "Journal reference: Proceedings of ENERGY 2021: The Eleventh International Conference on Smart Grids, Green Communications and IT Energy-aware Technologies"

即该文献**确实已经正式发表，不再是单纯的预印本**。作者为Julian M. Stürmer、Anton Plietzsch、Mehrnaz Anvari，原标题为"The Risk of Cascading Failures in Electrical Grids Triggered by Extreme Weather Events"（注意大小写：官方标题"The Risk..."首字母大写，与当前参考文献列表中"The risk..."小写写法略有差异，建议一并订正）。

**需要向网页端明确澄清的一点**：命令背景问的是"是否已经在**同行评审期刊**正式发表"——严格来说，ENERGY 2021是IARIA主办的**国际会议论文集（conference proceedings）**，不是期刊（journal）。是否发表、发表在哪里这两件事已经确认，但"期刊"这一具体表述不准确，应改为"会议论文集"。系统检索未能找到该会议论文集的具体页码范围或ISBN信息（会议论文集官方页面检索无果），如实说明这部分细节**无法进一步核实**。建议引用格式更新为：

> Stürmer JM, Plietzsch A, Anvari M. The risk of cascading failures in electrical grids triggered by extreme weather events. In: Proceedings of ENERGY 2021: The Eleventh International Conference on Smart Grids, Green Communications and IT Energy-aware Technologies; 2021. [页码未能核实]

是否要用会议论文集版本替代arXiv预印本、还是两者并列引用，留给网页端决定；本命令的核实结论是"已正式发表于会议论文集，非期刊"。

### [17] ONS "Explore local statistics"

**部分核实**：该资源是一个持续运行、持续更新的在线交互式服务（`https://www.ons.gov.uk/explore-local-statistics/`，确认可正常访问），**本身没有一个固定的"发布日期"**，不同于一次性发布的统计报告。找到其配套的"质量与方法说明（QMI）"文档页面（`https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/healthandwellbeing/methodologies/explorelocalstatisticsserviceqmi`），显示**"Last revised: 25 April 2025"**。建议引用中标注为"[最近方法说明修订于2025年4月25日，访问于[具体日期]]"这类"持续服务+访问日期"的表述方式，而非试图给这个持续运行的服务安一个固定的"发表日期"。

### [18] ONS "Mapping income deprivation at a local authority level"

**已核实**：数据集官方页面（`https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/datasets/mappingincomedeprivationatalocalauthoritylevel`，确认可正常访问）明确标注**发布日期2021年5月24日**，联系人Richard Prothero，"Next release: To be announced"（无后续更新计划）。当前引用中"[Internet]. 2021"的年份已经正确，可补全为完整日期"24 May 2021"及具体URL。

### 其余机构网页类引用URL有效性逐一确认

| 引用 | URL | 访问结果 |
|---|---|---|
| [1] | instituteforgovernment.org.uk/explainer/energy-resilience | **有效**（HTTP 200，实际打开确认内容） |
| [2] | ofgem.gov.uk/research/storm-arwen-report | **有效**（HTTP 200，实际打开确认内容） |
| [10]（PNNL报告，此前无URL） | pnnl.gov/main/publications/external/technical_reports/PNNL-33587.pdf | **有效**（触发文件下载，确认文件存在） |
| [11] | ofgem.gov.uk/sites/default/files/docs/2020/04/riio-ed1_..._annex_f_-_interruptions.pdf | **有效**（触发文件下载，确认文件存在，已用于核实版本信息） |
| [17] | ons.gov.uk/explore-local-statistics/ | **有效**（HTTP 200，实际打开确认内容） |
| [18] | ons.gov.uk/.../mappingincomedeprivationatalocalauthoritylevel | **有效**（HTTP 200，实际打开确认内容） |
| Notes工作表内引用的shapefile（Moran's I底层GIS数据源，非论文正式引用条目，但与[18]方法论直接相关） | data-communities.opendata.arcgis.com/datasets/5e1c399d787e48c0902e5fe4fc1ccfe3 | **已失效（HTTP 404）**——已在上方Moran's I部分注明 |

### 补充：[10] PNNL报告完整信息（此前完全空白，本命令补全）

系统检索OSTI.GOV官方文献库（`https://www.osti.gov/biblio/1969999`）确认完整信息：

> Kabre WW, Weimar MR. Fragility Functions Resource Report: Documented Sources for Electricity and Water Resilience Valuation. Pacific Northwest National Laboratory (PNNL), Richland, WA; 2022 Oct 1. Report No.: PNNL-33587. DOI: 10.2172/1969999.

命令#49的必须核实清单未列出[10]，但由于其"[author, date unverified]"占位符恰好在本命令核实[11]/RIIO-ED1时顺带用到的同一批检索中被找到完整信息，一并补全，不影响本命令对必须项的核实质量。

---

## 三、验收标准逐项确认

- Moran's I空间单元问题：已给出明确结论（LSOA层级、按LAD边界分别封闭计算，非LAD-LAD邻接也非"全国LSOA网络后映射"），并给出两组独立的官方原文证据（ONS交互式文章的Sefton/Liverpool例子、源文件Notes关于Isles of Scilly的说明）和四项具体官方文档出处，不是"沿用ONS数据"这类笼统说法。空间权重矩阵类型（queen/rook/距离衰减）经系统检索确认**无法找到官方文档明确说明**，已如实说明原因（底层shapefile链接已404失效，且未找到对应QMI文档），未编造具体类型。
- 引用细节核实：[1][2][11][13][15][17][18]全部逐一核实完成并给出具体来源；[16]确认已正式发表并给出会议论文集完整信息（明确澄清是会议论文集而非期刊，且页码/ISBN未能核实的部分已如实说明）；[10]虽非命令必须项但顺带补全完整信息。
- [16]arXiv文献：已确认正式发表状态（会议论文集），给出替代引用信息，不用同行评审期刊的表述误导网页端。
