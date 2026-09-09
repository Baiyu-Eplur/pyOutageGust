# 工作命令 #48：独立审稿（IR01/IR04/IR06/IR07）核实与措辞收敛

**背景**：一份独立AI审稿对MD第7版正文+附录第2版提出21项问题。本命令核实分量较重的四项：IR01（时间独立性措辞）、IR04（Bootstrap是否逐次重新标准化）、IR06（gap定义与VIF是否存在数学矛盾）、IR07（duration_B与Ofgem CIt/CMLt的关系是否被过度引用）。全部为只读核实+诊断性计算，未改变任何已有模型结果。产出写入`claude_branch/results/independent_review_ir_20260905/`。

---

## IR06：gap定义与VIF是否存在数学矛盾（最高优先级）

### 1. `deprivation_gap_pct`的确切构造公式——逐行追溯到最原始逻辑

**代码层面**：`IMD_merge.py`第35行确认`deprivation_gap_pct`直接来自源Excel文件`data/localincomedeprivationdata.xlsx`工作表"Rankings for all indicators"的列"Deprivation gap (percentage points)"，本项目代码**未对该数值做任何构造性计算**——`pct_to_float()`函数（第75-81行）只做字符串清洗（去除"%"符号、转数值类型），不涉及任何算术变换。即：`deprivation_gap_pct`在本项目管线中是**直接读取的官方原始数值**，不是本项目自己算出来的衍生量。

**追溯到官方原始定义**：源Excel文件的"Notes"工作表第30行原文明确写道：

> "The deprivation gap for each local authority is calculated by subtracting the lowest 'Income Score (rate)' from the highest 'Income Score (rate)' **within that local authority**."

即：这是**某个LAD内部**最高LSOA收入剥夺分数减去最低LSOA收入剥夺分数——一个**LAD内部（组内）离散度/极差统计量**，衡量的是该LAD内各小区（LSOA）之间收入剥夺程度的不均衡程度。这与`income_deprivation_rate`（"Local authorities"工作表的"Income - Average score"，即该LAD内全部LSOA的人口加权**平均值**——一个**水平**统计量）在统计学意义上是完全不同类型的量：一个是组内极差，一个是组内加权均值。

### 2. 是否严格等于"local income_deprivation_rate减去全国共享常数"？

**明确回答：不是。** 用官方源文件全部316个英格兰LAD的原始数据直接验证：

```
diff = deprivation_gap_pct - income_deprivation_rate
count = 316
mean = 0.186244, std = 0.074506
min = 0.028, max = 0.393
相关系数 r = 0.819（全国316个LAD口径）；本文实际分析样本上为0.771-0.820（因子样本LAD覆盖范围不同）
```

`diff`并非常数（标准差0.0745，最小0.028到最大0.393，跨度达0.365），这在数学上直接排斥"gap = rate − 固定常数"这一假设——若为真，`diff`理应对全部LAD完全相同（标准差应为0）。**审稿的核心前提本身不成立**：不存在"这个全国常数"，因为两者根本不是通过"减去某个常数"这种线性变换关联起来的，它们是基于同一份LSOA级底层数据、用两种不同聚合方式（均值vs极差）分别计算出的两个独立统计量。

### 3. 为什么VIF（3.76）没有捕捉到"理论上应有的精确共线性"

由于第2点已确认不存在"应有的精确共线性"这一前提，VIF=3.76本身没有任何需要被"捕捉"而未捕捉到的东西——3.76这个数值本来就应该反映的是两个**中等相关（r≈0.77-0.82）但非线性依赖**的变量之间的正常膨胀水平，而非某种被遗漏的完美共线性。

**补充说明（借鉴命令#46的经验做诚实的自我复核）**：命令#46核查VIF计算代码时，确实发现并修正过一处真实的实现问题（遗漏常数项导致VIF虚假膨胀至40+）。本命令特意用同一套已修正代码（`c09_vif_fixed.py`，`sm.add_constant`正确加入常数项）在C01修正后数据上重新核实了这一具体数值：`income_deprivation_rate`和`deprivation_gap_pct`的VIF分别为2.576和3.753（E0模型），与论文正文引用的3.76一致。**VIF计算代码本身经核实是正确的**，不存在类似命令#46发现过的那类实现缺陷。

### 4. 最终结论：字段描述用词不准确问题，而非模型设定问题

**这是一个真实存在的字段描述用词不准确问题，不是模型设定/VIF计算的问题。** 而且——这个描述错误**不是审稿凭空猜测出来的，而是论文自身文字造成的**：系统检索发现，论文正文和附录中**三处**明确将`deprivation_gap_pct`描述为"the gap between local and national income deprivation"（局部与全国收入剥夺水平之间的差距）：

- Section 2.1（第44行）："...income deprivation rate, **the gap between local and national income deprivation**, and spatial clustering of income deprivation..."
- Section 2.4（第100行）："...income deprivation rate, **the gap between local and national income deprivation**, Moran's I..."
- Appendix A数据字典（`Paper1_Appendices.md`第41行）："Official LAD-level **gap between local and national income deprivation**, used as published"

这三处文字**均不准确**，是审稿IR06质疑的直接根源——审稿完全合理地根据这一（错误的）文字描述推导出"gap应等于local减national常数"，进而合理地质疑为何VIF没有表现出应有的完美共线性。真实情况是：`deprivation_gap_pct`衡量的是**LAD内部**LSOA之间收入剥夺程度的离散度（组内极差），与"全国水平"完全无关，该字段名称中的"gap"指的是LAD内部的差距，不是"local vs national"的差距。**建议网页端将上述三处"the gap between local and national income deprivation"改为准确表述**，例如"the within-district dispersion of income deprivation, measured as the gap between the highest and lowest income deprivation score among the small areas (LSOAs) within each local authority"，无需改动任何模型代码或VIF数字。

---

## IR07：duration_B与Ofgem官方定义的关系

### 1. Ofgem Annex F对CMLt的官方公式定义（核实自官方PDF原文）

已直接下载并解析官方文件*RIIO-ED2 Regulatory Instructions and Guidance – Interruptions* (Ofgem, 2023, v1.1，即论文参考文献[12])，第4.3-4.5段原文关键定义：

> "CIt = the number of Customers interrupted in the relevant year t, excluding re-interruptions."
> "CMLt = the duration of interruptions to supply in the relevant year t, including re-interruptions."
> CMLt = CMLAt + CMLBt + CMLCt + CMLDt + CMLEt（按事件来源分解：本网络计划外事件A、预安排事件B、上级输电网络事件C、分布式发电事件D、其他关联系统事件E）
> CMLAt（本网络计划外事件部分）的公式：CMLA_t = [Σ_i Σ_r N_rit×(T_rit − TI_rit)] / TC_t

**确认两个关键事实**：
(a) **CMLt在官方定义中是一个"年度、全网络"层面的加总统计量**，分子是对该年度内**全部incident（i）与全部restoration stage（r）**的customers×stage_duration双重求和，分母TC_t是该年度网络总接入客户数——它本身**没有"某个具体事件i的CML"这一官方定义的口径**，是一个整年网络平均指标，而非事件级/incident级变量。
(b) 若把CMLA_t公式中对r的内层求和（Σ_r N_rit×stage_duration_rit）解读为"某个事件i对当年CML的贡献量"，这一贡献量的数学形式是**"客户数加权、按阶段累加的分钟数"**，与本项目代码中确实存在的字段`customer_minutes_lost_event`（= Σ_r(customers×stage_duration_hours)×60，见`build_stage_base_v3.py`第132行）在构造逻辑上一致；这个字段存在于本项目管线中，但**从未被用作论文建模的outcome变量**。

### 2. duration_B是否曾被不准确地表述为"沿用CMLt的聚合逻辑"？——确认存在，具体位置如下

**确认存在。** `Paper1_draft.md`第52行（Section 2.2开篇）原文：

> "Ofgem's Annex F guidance defines two outcome measures for outage reporting [11, 12]. Customer Interruptions (CIt) counts the number of customers affected by an incident, summed across restoration stages and excluding stages flagged as re-interruptions... Customer Minutes Lost (CMLt) measures the duration of interruption, **summed across all restoration stages including re-interruptions**, because each additional interruption stage represents further time without supply for the customers affected at that stage. **This paper constructs two event-level variables following these definitions.**"

而紧接着的Equation 2（第66行）：

$$D_i = \max_{r \,\in\, \mathcal{R}_i} T_{i,r}^{\text{end}} - \min_{r \,\in\, \mathcal{R}_i} T_{i,r}^{\text{start}}$$

这是一个**简单的时间跨度（最晚结束减最早开始）**，既不是"按阶段累加时长"，也没有任何客户数加权，与前一句描述的"CMLt summed across all restoration stages"在数学结构上完全不同。**"This paper constructs two event-level variables following these definitions"这句话对duration_B而言是不准确的**——duration_B（Equation 2）实际实现的是一个时间跨度统计量，而不是CMLt所描述的"按阶段累加"逻辑。相比之下，Equation 1（customers_v2，"excluding re-interruptions"的求和）与CIt的定义匹配良好，问题**只出在duration_B/CMLt这一侧**。

系统检索全文及Appendix B/D，确认CMLt/Ofgem官方定义相关表述**只出现在Section 2.2这一处**（第52行），未在附录中重复或进一步展开引用，因此需要改写的位置只有这一处，但由于第2.1节（第40行）和摘要等处也间接提及"according to Ofgem's official definitions"的措辞框架，建议网页端一并检查是否需要联动调整表述基调。

### 3. duration_B（事件记录跨度）的真实选择理由

**核实结论：真实理由是研究"恢复跨度本身"这一工程问题，而非"这就是官方统计口径"。** 证据：
- 本项目管线中实际计算过一个更接近CMLt聚合逻辑的候选变量`duration_A_customer_weighted_hours`（客户数加权平均阶段时长，`build_stage_base_v3.py`第122行），但该候选**已被放弃**（详见下方IR01核实部分：因与`customers_v2`存在构造性共线，命令#10已发现`duration_A`的加权分母与`customers_v2`的Pearson r=0.962、Spearman ρ=0.997）。
- 项目最终选择`duration_B`（简单时间跨度）而非`duration_A`（客户加权时长）或严格意义上的CMLt风格聚合量，真实理由是**duration_B在构造上不使用customers做权重，与customers_v2没有数学构造关联，只有可能的因果统计关联**（`04_构造关联性检验.md`原文），这是一个**避免构造性共线、保持指标独立性**的工程建模考量，不是"因为这就是Ofgem官方口径"。
- 建议网页端将Section 2.2的表述从"following these definitions"改为更准确的表述，例如说明这是借鉴Ofgem CIt/CMLt区分"客户规模"与"停电时长"两个维度的**思路**，但duration_B的具体构造方式（时间跨度）是本文自己的工程选择，理由是避免与customers_v2产生构造性共线，而非直接复刻CMLt的加总公式。

### 4. duration_B是否涵盖"事件中途曾短暂恢复供电"的时间间隔？

**核实结论：涵盖（不排除），即duration_B会把该间隔计入总时长。** 直接追溯代码`build_stage_base_v3.py`第98-125行：

```python
start = pd.to_datetime(df[START_COL], errors="coerce", utc=True)
end = pd.to_datetime(df[END_COL], errors="coerce", utc=True)
...
duration_b = (end.groupby(key).max() - start.groupby(key).min()).dt.total_seconds() / 3600.0
```

`start`/`end`取自**全部**阶段记录（`r ∈ R_i`，包括被标记为re-interruption的阶段，未做任何排除性过滤），`duration_b`=（全部阶段中最晚的end）−（全部阶段中最早的start）。因此，如果某事件的时间线是：阶段1（08:00-09:00，恢复供电）→ 间隔（09:00-11:00，客户实际有电）→ 阶段2/reinterruption（11:00-14:00，再次停电），`duration_B` = 14:00−08:00 = 6小时，**这6小时中包含了09:00-11:00这2小时客户实际有电的时间段**——duration_B衡量的是"整个事件从开始到彻底解决的总日历时间跨度"，不是"客户实际无电的累计时长"，**不会**从总时长中扣除中途曾短暂恢复供电的间隔。这一点建议在2.2节或方法论限制部分明确说明，避免读者将duration_B误解为"累计停电分钟数"。

---

## IR04：Bootstrap是否逐次重新标准化并正确换算物理单位

### 1-2. 当前实现的确切方式（逐项核实代码）

核实对象：命令#45最终版`figure4_dose_response.py`（E0拐点bootstrap CI，10.81 m/s [9.16, 12.16]的直接产出脚本）及其调用的`critical_wind_speed_pipeline.py::bootstrap_turning_point()`。

**分两步看**：

**第一步（模型拟合阶段，每次重抽样内部）——确认"是"，逐次重新标准化**：`bootstrap_turning_point()`第158-169行，每次重抽样先按日期块（date-block）做有放回抽样构造`boot_df`，然后调用`v9.design_train_valid(boot_df, boot_df, ...)`。核实`design_train_valid()`源码（`v3_validation_pipeline.py`第196行）：`mu, sd = tr[c].mean(), tr[c].std(ddof=1)`——`tr`参数就是传入的第一个参数，在bootstrap场景下即为`boot_df`本身。**这确认：每次重抽样，阵风（以及气压等其余SCALE_COLS协变量、含交互项所需的气压自身μ/σ）确实都用该次重抽样样本自己的均值/标准差重新做了标准化**，不是复用固定的全样本参数。每次重抽样在此基础上重新拟合OLS并提取z尺度的拐点z* = -b1/(2b2)。

**第二步（CI换算阶段，figure4_dose_response.py第119-122行）——确认为"先取分位数再统一换算"（较不严格的做法）**：
```python
boot, n_failed = v11.bootstrap_turning_point(...)      # boot：500个z尺度拐点
boot_lo_z, boot_hi_z = np.percentile(boot, [2.5, 97.5])  # 先在z尺度上取分位数
boot_lo_ms = gust_mean_e0 + boot_lo_z * gust_sd_e0        # 再用固定的全样本μ/σ做一次性换算
boot_hi_ms = gust_mean_e0 + boot_hi_z * gust_sd_e0
```
其中`gust_mean_e0`/`gust_sd_e0`来自`build_curve()`调用`v11.fit_full_sample(sample, ...)`，是在**未重抽样的完整E0全样本**上算出的固定值，全部500次重抽样共享同一对（gust_mean_e0, gust_sd_e0）做最终的m/s换算。

### 3. 明确回答：当前方法是"先分位数、后统一换算"，量化其与更严格做法的差异

**当前实际采用的方法确认为问题描述中的"后者"**：先在标准化尺度上对500个z*值取2.5/97.5分位数，再用一套固定的（全样本）μ、σ做一次性换算成物理单位，而不是"每次重抽样都用该次重抽样自己的μ、σ将z*换算成物理单位，再对全部500个已换算的m/s数值取分位数"。

**量化差异**（诊断脚本`ir04_bootstrap_diagnostic.py`，同一seed=20260826、同一date-block抽样方案，逐一记录每次重抽样自己的gust均值/标准差，分别用两种顺序重新计算CI，供直接对比）：

| 方法 | 下界(m/s) | 上界(m/s) | 区间宽度(m/s) |
|---|---|---|---|
| **当前方法**（先取z尺度分位数，再用全样本固定μ/σ统一换算） | 9.1563 | 12.1609 | 3.0046 |
| **更严格方法**（每次重抽样各自换算成m/s，再对500个m/s值取分位数） | 9.6566 | 12.0402 | 2.3836 |
| 差异 | **当前方法下界低0.50 m/s** | 当前方法上界高0.12 m/s | **当前方法区间宽约26%**（多0.62 m/s） |

（补充诊断：500次重抽样各自的阵风均值范围[9.19, 11.16] m/s、标准差范围[4.32, 6.81] m/s，重抽样之间存在有意义的波动，这正是两种换算顺序产生差异的来源——"先分位数再换算"这一做法，相当于隐式假设"全部重抽样共享同一套换算参数"，而实际上不同重抽样的阵风分布本身在随重抽样漂移。）

**方向与量级总结**：当前方法给出的95%置信区间比更严格做法**更宽**（尤其体现在下界更低，9.16 vs 9.66 m/s），即当前论文报告的不确定性区间**略微偏保守（过宽）**，而非偏乐观。这与命令#43 M05已确认的"标准化参数（阵风均值/标准差）在每次重抽样中均重新估计"这一事实是一致的（M05核实的是拟合阶段的重新估计，本命令进一步核实并量化了CI换算阶段存在的"先分位数后统一换算"这一独立环节，二者不矛盾，是同一套bootstrap流程中两个不同步骤各自的核实结论）。

### 4. 本命令未改变bootstrap方法本身

本命令仅做诊断性核实和量化对比，未修改`figure4_dose_response.py`或`critical_wind_speed_pipeline.py`任何代码，也未重新生成任何图片或改变论文引用的10.81 m/s [9.16, 12.16] CI这一既有数字。是否需要改为"逐次换算再取分位数"的更严格做法、或仅在方法论文字中说明当前做法及其保守性方向，留给网页端判断。

---

## IR01：时间独立性表述的进一步核实

### 1. duration_A/duration_B构造性共线发现是否也在污染样本上得出？是否实质性影响了"选择duration_B"这一决策？

**核实结论：确认是，且确认这一发现确实实质性支撑了"选择duration_B而非duration_A"的方法论决策。**

该发现记录在`claude_branch/results/v3_controlled_comparison/04_构造关联性检验.md`（命令#10产出）：`duration_A`的加权分母（`event_customer_weight_denominator`）与`customers_v2`的Pearson r=0.962（原始值）/0.993（log空间），Spearman ρ=0.997/0.996，远超命令预设的0.8警戒线。该文档明确写道：**"这一发现为解读命令#9 Step5的核心结果...提供了关键背景：duration_A本身在构造上就与customers_v2高度共线...duration_B不存在这种构造层面的高相关性，因此其'控制后依然显著'的结果更不容易被这种机械关联污染。"**——即该发现被明确用作偏好duration_B、质疑duration_A可靠性的支撑证据。

命令#10属于命令#43（E01核查）已确认的"命令#9、#10、#11、#12、#13、#14共六项基础性决策，全部基于locked_temporal_test污染前数据做出"名单中的一项——**该样本（n=122,308-134,956，接近完整v3全量事件数）确认建立于locked_temporal_test时间切分存在之前**，即确认为污染前数据。命令#43此前已记录"duration_A构造性共线发现从未在干净数据上复核，但因duration_A已被放弃未影响最终结论"，本命令进一步确认：这一发现不仅"未影响最终结论"，而且**实质性地充当了选择duration_B的正面论据之一**，这一点此前的记录未充分强调，建议在时间线记录中补充明确这一点。

### 2. "independent temporal holdout"/"not examined at any point"类措辞的具体位置及是否需要改写

系统检索`Paper1_draft.md`全文，定位以下位置：

| 位置 | 原文（节选） | 问题 |
|---|---|---|
| Abstract，第10行 | "...confirmed under alternative distributional assumptions, **within an independent temporal holdout**, and across the seven named storms." | 表述本身（"在独立时间保留样本内得到确认"）指的是**结果确认**，不直接断言"整个决策过程独立于holdout"，问题较轻，但与下面两处连用时可能被读者放大误解为"全程独立" |
| 引言第32行 | "Both findings are examined against **an independent temporal holdout not used during model development**." | **需要改写**——"not used during model development"是一个整体性断言，与E01已确认的六项基础性决策（命令#9-14，含Cause Code范围选择、customers/duration口径选择、临界风速方法论、方差分解方法论）均基于locked_temporal_test切分**建立之前**的（即技术上包含了后来成为holdout期间的）数据做出这一事实存在张力 |
| 3.2节第128行 | "**All of the choices** described in Section 2, **and all of the model specification** described in Section 3.3, **were made using only this development sample**." | **最需要改写的一处**——这是全文措辞最强、最具体的一句，直接断言"第2节全部选择+第3.3节全部模型设定"都"仅用开发样本做出"，与E01核实的六项决策（其中就包括第2节所述的Cause Code范围选择、customers_v2/duration_B构造选择）实际发生在locked_temporal_test切分尚不存在、数据未做开发/确认二分之前，直接矛盾 |
| 3.2节第128行同段 | "This six-month period **was not examined at any point** while the model was being developed." | 与上一条同句境，含义相同的整体性断言，同样需要改写 |

**建议网页端重新措辞的方向**（本命令只列位置清单，不代为改写）：将"were made using only this development sample" / "not used during model development" / "not examined at any point"这类**绝对化**表述，改为更精确地区分"用于拟合/选定最终报告模型的那一步"与"早期奠定研究框架的基础性范围决策"两个不同阶段，例如改为"the final model reported in this paper was fitted and validated using only the development sample; several foundational scope decisions made earlier in the project (Cause Code category selection, the choice between candidate duration definitions) were made before the development-confirmation split was constructed, though they do not depend on which side of that split any given event falls"这一类更谨慎的表述，避免暗示整个分析决策过程完全未受确认期数据影响。

---

## 本轮范围说明

按命令要求，本命令优先保证IR01/04/06/07四项核实质量，IR09-IR21未在本轮范围内核实。IR02/IR03/IR08按命令背景说明不在本命令处理范围。

## 产出文件

`raw/ir04_bootstrap_conversion_comparison.json`；脚本`ir04_bootstrap_diagnostic.py`（诊断性，未改变任何既有模型结果）。IR06/IR07核实过程中读取的官方源文件：`data/localincomedeprivationdata.xlsx`（Notes工作表）、Ofgem RIIO-ED2 Annex F – Interruptions（官方PDF，第4.3-4.5段）。

## 验收标准逐项确认

- **IR06**：给出了`deprivation_gap_pct`的确切构造公式（源自官方Excel"Deprivation gap (percentage points)"列，本项目代码未做任何算术变换）和VIF"矛盾"的最终判定——不存在数学矛盾（gap并非rate减常数，用316个LAD全国数据数值验证diff非常数），真实问题是论文正文+附录A三处"the gap between local and national income deprivation"的字段描述用词不准确，已给出具体位置和改写建议方向。
- **IR07**：明确指出Section 2.2（第52行）"This paper constructs two event-level variables following these definitions"这一表述对duration_B而言不准确的具体位置，并用官方Ofgem PDF原文（CMLt公式）和项目代码（`duration_a`已放弃候选、`customer_minutes_lost_event`未使用字段）双重证据支撑判断。
- **IR04**：明确当前bootstrap是"模型拟合阶段逐次重新标准化（含气压等交互项协变量）+ CI换算阶段先在z尺度取分位数、再用固定全样本μ/σ做一次性换算"这一混合方式，并用诊断脚本量化了这一方式与"逐次换算再取分位数"更严格做法之间的具体差异（当前方法CI更宽，下界低0.50 m/s，区间宽度多约26%）。
- **IR01**：给出了需要网页端重新措辞的四处具体位置（Abstract第10行、引言第32行、3.2节第128行的两句），并确认duration_A/B共线发现同样基于污染前数据、且实质性支撑了duration_B的选择这一此前记录未充分强调的细节。
