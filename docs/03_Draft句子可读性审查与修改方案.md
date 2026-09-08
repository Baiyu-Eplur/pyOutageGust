# Draft.docx 句子可读性与冗余审查——修改方案

> 审查对象：`D:\Pyprogramme\STST2603\claude_branch\docs\Draft.docx`
> 审查类型：句子层面可读性与冗余审查（非实质性学术审查），使用 academic-humanizer skill
> 状态：本文档为**已确认的最终修改方案**，尚未对 Draft.docx 执行任何实际编辑
> 生成时间：本轮对话产出

---

## 一、本方案的形成过程

本文档整合了两轮工作的结果：

1. 对 Draft.docx 全文（Abstract 至 References）按 8 类句子层面问题（过长句、过密句、过短/欠发展句、重复冗余、"and"过度并列、枚举过载、句界问题、不必要的冗词）逐句审查，产出初版审查报告；
2. 根据用户对初版报告的逐条反馈（认可/撤回/要求修正），对建议清单做出相应调整。

本文档是调整后的**最终版本**，作为后续实际编辑 Draft.docx 时的执行依据。

---

## 二、本轮撤回的建议（3处，维持原文不变）

以下三条在初版报告中被标记为待改进项，经反馈确认后**撤回**，原文保持不变。

### 撤回项 1 — Section 3.2，"A decision was needed on..." ×3

**原文（维持不变）：**
> "A decision was needed on which Cause Code categories to include. A decision was needed on how to define customer counts and outage duration from the raw stage-level records. A decision was needed on how to handle a small number of unusual events."

**撤回理由：** 与上一轮"AI感"审查已确立的原则冲突——该原则明确要求"宁可句子短、朴素一点，也不要为了效率把三句合并成一句带内嵌列表的复合句"。初版报告本身也承认该处"defensible either way"（有理由维持现状）。为保持决策一致性，不再反复横跳，维持原文。

### 撤回项 2 — Section 3.2，"These records are not independent of each other."

**原文（维持不变）：**
> "...This matters because a single storm can generate many outage records on the same day. These records are not independent of each other."

**撤回理由：** 初版报告本身标注为低置信度，并承认这句话的作用是把"为什么按日期分折"的方法论理由显式说出来，而非单纯重复前句。删除会使这一理由从"明说"退化为"读者需要自行推断"，不符合期望的表达方向。维持原文。

### 撤回项 3 — Section 3.1，ML 讨论的五个连续短句

**原文（维持不变）：**
> "A machine learning model, such as a random forest, can often predict outcomes more accurately. It does not, however, give a simple, interpretable threshold value in the same way. For this reason, machine learning is not used as the main method in this paper. A machine learning comparison could still be a useful robustness check in future work. This point is revisited in Section 5."

**撤回理由：** 初版报告同样标注为低置信度，并明确指出"不应机械合并短句"。这五个连续短句恰好体现了本文既定追求的"短句、一句一个意思"的风格效果，不构成问题。维持原文。

---

## 三、需修正后采纳的建议（1处）

### 修正项 — Section 2.2，Para 32（"Constructing affected customers by aggregating across stages..."）

**诊断（维持不变）：** 主语与谓语之间被过长的从句/对比结构隔开，是真实存在的可读性问题，值得修改。

**原文：**
> "Constructing affected customers by aggregating across stages, rather than taking the customer count reported in the earliest stage of each incident, changes the sample mean from 47.13 to 93.02 customers, a difference of a factor of 1.97, within the same final analysis sample reported in Table 1."

**~~旧建议（已作废，因含破折号，违反"不用破折号做插入说明"的既定规则）~~：**
> ~~"The sample mean for affected customers is 93.02 when computed by aggregating across stages, versus 47.13 when using only the customer count reported in the earliest stage — a difference of a factor of 1.97 within the same final analysis sample reported in Table 1."~~

**新建议（改用分句，不含破折号）：**
> "The sample mean for affected customers is 93.02 when computed by aggregating across stages, rather than 47.13 when using only the customer count reported in the earliest stage of each incident. This is a difference of a factor of 1.97, within the same final analysis sample reported in Table 1."

- **操作类型：** RESTRUCTURE（拆分为两句，不使用破折号）
- **置信度：** High

---

## 四、新增建议（2处，语法修正）

以下两处为纯语法错误，原本不在本轮句子层面可读性审查的范围内，但发现后按用户要求一并列入修改方案。

### 语法修正 1 — Section 2.1，Para 18

**原文：** "Moran's I follow the spatial autocorrelation statistic introduced by Moran [19]."

**问题：** 主谓一致错误——"Moran's I"作为统计量名称应视为单数主语。

**建议：** "Moran's I **follows** the spatial autocorrelation statistic introduced by Moran [19]."

- **置信度：** High

### 语法修正 2 — Section 4.2，Para 174

**原文：** "...but for the gust group these ordering reverses, and the exposure-model bar becomes the taller of the two."

**问题：** 单复数不一致——"ordering"为单数名词，应搭配"this"而非"these"。

**建议：** "...but for the gust group **this** ordering reverses, and the exposure-model bar becomes the taller of the two."

- **置信度：** High

---

## 五、维持不变、尚待确认的原有建议（14处）

以下条目在反馈中未被提及，按初版审查报告的诊断、严重程度和建议原样保留，作为**待确认**的修改清单。若后续有取舍意见，将按"接受/修正/撤回"的方式更新。

| 编号 | 位置 | 原文（节选） | 问题类型 | 严重程度 | 建议操作 | 置信度 |
|---|---|---|---|---|---|---|
| 1 | Section 1，Para 7 | "outage impact, measured either by the number of customers affected (...) or by the time needed for restoration (...), does not scale..." | 主谓分离，关键术语定义被埋入插入语 | MEDIUM | RESTRUCTURE | High |
| 2 | Section 1，Para 8 | "This work typically derives fragility curves, which express..., from finite element simulation or scaled physical testing of a specific structure type, such as..." | 密度过高（定义+方法+举例压缩在一句） | LOW | SPLIT（可选） | Medium |
| 3 | Section 1，Para 10 | "Prior work, including one of the studies cited above [6]... but does not report... and does not examine..." | "and/but"链式并列三个独立命题 | HIGH | SPLIT | High |
| 4 | Section 2.1，Para 18 | "These comprise resident population from ONS local authority population estimates [17], and income deprivation rate,..., all drawn from..." | 枚举过载，来源归属需回读才能理清 | MEDIUM | SPLIT（按来源拆分） | High |
| 6 | Section 2.4，Para 80 | "...when the recovery model...is estimated on all six Cause Code categories...rather than...the subset..., the quadratic gust term remains..., while the linear gust term collapses..." | 全文最长最密的句子（约95词） | HIGH | SPLIT（拆为三句） | High |
| 7 | Section 2.4 Para 82 vs. Section 3.3 Table 2 | 协变量清单在两处几乎逐字重复 | 跨章节内容重复 | MEDIUM | CONDENSE（2.4节改为指向Table 2的概括句） | Medium |
| 8 | Section 3.1，Para 89 | "When the quadratic term dominates and the linear term is close to zero, this ratio no longer identifies..., and the quadratic coefficient is instead reported..., describing..." | 密度过高，段落节奏被打断 | MEDIUM | SPLIT | Medium-High |
| 11 | Section 3.3，Para 105 | "Year and month fixed effects are additive,..., and the gust-pressure interaction term is..." | 不当"and"并列两个无关技术点 | MEDIUM | SPLIT | High |
| 13 | Section 4.1，Para 148 | "...the quadratic gust term is significant...: p < 0.001 in both cases, compared with p = 0.022... and p = 0.982, not significant, for..." | 三方统计值对比压缩在一句 | MEDIUM | RESTRUCTURE | Medium |
| 14 | Section 4.2，Para 174 | "For the recovery margin, gust contributes between 0.62 and 0.75...,while affected customers itself contributes between 7.73 and 7.87..., out of a total...11.05 percent..." | 密度过高，两组带条件的数值结果压缩在一句 | MEDIUM-HIGH | SPLIT | High |
| 15 | Section 4.3，Para 190 | "The marginal contribution of gust...more than doubles, from...to..., and now exceeds..., which falls to..." | 密度过高，链式结论+内嵌从句 | MEDIUM | SPLIT | Medium-High |
| 16 | Section 4.1，Para 168 | "Because each turning point falls close to the sample mean,..., and because the fitted curve is approximately quadratic..., this asymmetry...produces..." | 双重"because"从句堆叠 | HIGH | SPLIT | High |
| 17 | Section 5，Para 233（末句） | "The approach used in this paper, reconstructing...and confirming..., is not specific to UK Power Networks." | 主谓分离，位于全文收尾句 | MEDIUM | RESTRUCTURE | Medium |

---

## 六、最终待执行清单汇总

**本轮已确认可直接执行的修改（3处）：**
- 第五节"修正项"（Section 2.2, Para 32，已改用无破折号版本）
- 语法修正 1（Moran's I follow → follows）
- 语法修正 2（these ordering reverses → this ordering reverses）

**已确认维持原文、不再修改（3处）：**
- Section 3.2，"A decision was needed on..." ×3
- Section 3.2，"These records are not independent of each other."
- Section 3.1，ML 讨论的五个连续短句

**待进一步确认的既有建议（14处）：** 见第五节表格，编号 1、2、3、4、6、7、8、11、13、14、15、16、17。

---

## 七、执行说明

- 本文档为修改**方案**，Draft.docx 尚未做任何实际改动。
- 所有建议均不改变任何数字、引用、公式、变量名或技术术语；仅涉及句子结构、句界划分与两处纯语法一致性修正。
- 待第五节 14 处待确认建议逐一表态后，可将全部"已确认"项汇总，一次性对 Draft.docx 执行实际编辑。
