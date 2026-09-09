# 工作命令 #51：核实旧版Appendix H遗留的两处未跟进问题

两项均已在C01+C02-C08修复后的最终数据/bootstrap产出上重新核实（未沿用旧文档基于修复前数据给出的具体数字）。只读操作，未修改任何历史结果文件。核实过程中另外发现一处此前未被注意到的、独立于这两项问题的文字-图表不一致，一并如实报告（见文末"额外发现"）。

---

## 问题一：Bootstrap重抽样中二次项系数是否真的从未接近零

### 核实方法

完全复用命令#43 M05建立的确定性复现方法（同一seed=20260826、同一n_boot=500、同一按日期分块有放回重抽样、同一`v9.design_train_valid`调用），唯一改动是输入换成C01+C02-C08修正后的最终E0样本（n=60,437）。额外验证：复现出的Bootstrap CI（[9.16,12.16] m/s）与命令#45/#48/#50多次报告的数字完全一致，确认复现方法准确无误。

### 1. β₂在全部500次重抽样中的最小值、最大值、非正值次数

| 统计量 | 数值 |
|---|---|
| 全样本点估计 β₂ | 0.10600 |
| 500次重抽样最小值 | **0.04837**（点估计的45.6%） |
| 500次重抽样最大值 | 0.16183 |
| 非正值（≤0）出现次数 | **0 / 500** |
| 负值出现次数 | **0 / 500** |
| 5th/50th/95th百分位 | 0.0766 / 0.1077 / 0.1382 |

**在C01修正后数据上，β₂在全部500次重抽样中从未接近零**——最小值仍达到点估计的45.6%，全部500次均为正值，与命令#43在修复前数据上得到的发现（最小值0.0366，约点估计的35.5%，同样0/500非正）方向完全一致，且本次修正后数据的最小值占比甚至更高（更远离零）。

### 2. "分母接近零导致比值分布重尾"这一机制解释，是否得到实际数据支持

**不成立，没有得到数据支持。** β₂（拐点公式G*=-β₁/(2β₂)中的分母）在全部重抽样中稳定为正、且从未低于点估计的45%，不存在"某些重抽样中分母接近零"这一现象。

**额外发现（有助于给出更准确描述）**：核实过程中同时提取了β₁（分子）的重抽样分布：

| 统计量 | β₁数值 |
|---|---|
| 全样本点估计 | -0.03601 |
| 500次重抽样均值 | -0.03873 |
| 最小值 / 最大值 | -0.11172 / **+0.07081** |
| **正值出现次数** | **49 / 500（9.8%）** |

**β₁（分子，线性项）本身在500次重抽样中有9.8%变号为正**，且其重抽样标准差（0.0298）相对其点估计（-0.0360）的比例远大于β₂的对应比例——这提示：如果要为delta方法与Bootstrap方法的差异寻找一个更具体的经验性来源，**分子（β₁）在零附近的不稳定性/变号，比"分母接近零"更接近实际观察到的现象**。转折点z*的重抽样分布本身呈现明显左偏（偏度-0.686）和尖峰厚尾（超额峰度1.337），这与分子在零附近波动、比值函数在该区域高度非线性放大误差的机制是相符的。

### 3. 更准确的描述（机制未完全确定，给出保守表述）

**保守版本（如实说明"机制不确定"，命令允许的选项）**：

> This difference arises because a ratio of two random coefficients does not follow a normal distribution in general, and the delta method, which relies on a first-order approximation, can understate the width of the true sampling distribution. A direct check of the 500 bootstrap replicates shows that the quadratic coefficient (the denominator of the ratio) remains comfortably positive throughout, with a minimum value equal to 46 percent of its point estimate and no replicate close to zero, so denominator instability is not the source of this difference. The specific mechanism producing the discrepancy between the two methods is not established here; the bootstrap interval is used as the more conservative estimate.

**更具体版本（点出分子而非分母，仍基于实际观察、不过度声称因果机制）**：

> This difference arises because a ratio of two random coefficients does not follow a normal distribution in general, and the delta method, which relies on a first-order approximation, can understate the width of the true sampling distribution. A direct check of the 500 bootstrap replicates shows that the quadratic coefficient (the denominator of the ratio) remains comfortably positive throughout the resampling distribution, so denominator instability is not the source of this difference. The linear coefficient (the numerator), by contrast, is itself small relative to its resampling variability and changes sign in about 10 percent of replicates, which is a more plausible contributor to the skewed, heavy-tailed sampling distribution of the ratio observed in the bootstrap. The bootstrap interval is used here as the more conservative estimate.

两个版本均可直接替换`Paper1_draft.md`第170行"...when the denominator coefficient is close to zero in some resamples..."这句话，具体采用哪个版本（完全保守 vs 指出分子这一更具体的经验观察）留给网页端判断。

---

## 问题二：Figure 10 development sample点估计的区间有效性

### 1. 核实点估计的确切构造方法

直接核对`figure10_robustness_forest.py`第32-38行`pooled_estimate()`函数：**确认为对5折GroupKFold交叉验证的系数做标准逆方差加权汇总**（`w=1/se²`，`pooled=Σ(w·coef)/Σw`，`pooled_se=sqrt(1/Σw)`）——这是标准的meta分析固定效应汇总公式。

**关键细节**：这5个"折系数"不是5个互斥的20%子样本各自的独立拟合结果，而是`v3_validation_pipeline.py::run_model()`对每一折的**训练集**（即排除该折验证集之外的其余80%数据）分别拟合得到的5个系数——直接核实E0'样本的5折训练集两两之间的重叠比例：**任意两折训练集的重叠观测数占比恒定在74.9%-75.3%之间**（10对折两两比较，全部落在此区间）。

### 2. 是否存在"把5折当独立样本处理、忽略折间协方差"的统计问题

**确认存在，且已量化其严重程度。** 由于5个"折系数"实际上来自5个两两重叠75%的高度相关子样本拟合，`se=sqrt(1/Σw)`这一独立性假设下的汇总标准误公式**大幅低估了真实不确定性**。本命令用两种独立方法验证并量化：

| 方法 | E0系数点估计 | E0标准误 | 相对当前汇总SE的倍数 | R0c系数点估计 | R0c标准误 | 相对当前汇总SE的倍数 |
|---|---|---|---|---|---|---|
| **当前构造**（5折逆方差汇总） | 0.09128 | 0.004995 | 1.0×（基准） | 0.06677 | 0.003667 | 1.0×（基准） |
| **选项(a)**：开发样本单次全样本拟合（LAD聚类SE） | 0.08909 | 0.009980 | **2.00×** | 0.07397 | 0.007466 | **2.04×** |
| **选项(b)**：开发样本整体上的按日期分块Bootstrap（500次，seed=20260826，与本项目标准做法一致） | 0.09119（均值） | 0.020881 | **4.18×** | 0.06232（均值） | 0.023756 | **6.48×** |

**结论**：当前Figure 10"Development sample"行报告的标准误比一个方法正确的单次全样本拟合小约2倍，比按日期分块的Bootstrap标准误小4-6.5倍——**这是一个真实存在、量级不小的问题，当前区间确实系统性低估了真实不确定性**，命令背景中"忽略折间协方差"的担忧得到直接数据证实。

### 3. 三个选项的可行性评估

**选项(a)：补做一次真正独立的单次全样本拟合**
- 实施成本：**极低**。本命令已经用现成的`clean_sample_builder.build_clean_wt_samples()`+`v11.fit_full_sample()`（与"Holdout"行完全相同的方法）直接算出结果（E0: 0.08909±0.00998；R0c: 0.07397±0.00747），耗时不到1分钟。
- 优点：**同时修复了一个此前未被注意到的方法论不一致**——Figure 10现有4行中，"Holdout"、"LAD single cluster"、"LAD×date two-way cluster"三行全部是单次全样本拟合，唯独"Development sample"一行是5折meta汇总，方法论本身就不统一；改用选项(a)后四行方法完全一致（单次拟合+LAD聚类SE），可比性更强。
- 缺点：舍弃了"这一行本应汇总5折交叉验证结果"这一初衷（如果这一初衷本身就有价值的话）；点估计相比当前汇总值有小幅变化（E0从0.0913变为0.0891，R0c从0.0668变为0.0740，均在10%以内）。

**选项(b)：协方差感知的重抽样方案**
- 实施成本：**中等**。本命令已经实现了一种可行方案（对完整开发样本做按日期分块Bootstrap，与本项目其余章节的Bootstrap方法完全一致），已给出具体数字。
- 优点：正确处理了同一天多个事件、以及折间数据重叠带来的相关性，是统计上最严谨的方案，且与论文其余部分（如E0拐点的Bootstrap CI）方法论保持一致。
- 缺点：给出的区间明显更宽（尤其R0c，标准误达当前值的6.5倍），如果直接采用，Figure 10的"development sample"行会显得不确定性远高于其余三行，视觉上可能需要额外说明；计算成本高于选项(a)（500次重抽样刷新模型，本命令跑了几分钟）。

**选项(c)：保留当前汇总点估计，加一句说明**
- 实施成本：**最低**（一句图注文字，不改数字）。
- 缺点：由于本命令已经用极低成本算出了选项(a)的具体数字，继续保留一个已知被低估约2-6倍的区间、仅用文字免责声明"可能低估"，说服力弱于直接展示一个方法正确的数字；且由于"development sample"这一行的点估计和区间在4.4节正文中被直接引用用于比较（"the four point estimates fall within a range of 0.015"这类具体表述，见下方Figure 10图注前一段），继续使用一个统计上有问题的区间去支撑这类比较性论述，风险较高。

**本地端建议**：**采用选项(a)**。理由：(1) 成本几乎为零，本命令已经算出完整数字；(2) 同时修复了Figure 10内部方法论不统一的问题（其余三行本就是单次拟合）；(3) 点估计和区间宽度的变化幅度都在合理范围内，不会颠覆4.4节现有的定性结论（见下方Figure 10重新生成后的描述）。如果网页端认为"折间交叉验证的稳定性信息"本身也值得保留，可以考虑同时保留一张单独的（非Figure 10内的）5折系数散点/箱线图作为补充，但不建议再用于构造这一置信区间。

### 4. Figure 10重新生成（已采用选项(a)）

已生成`Figure_10_robustness_forest_REVISED.png`，"Development sample"行替换为选项(a)的单次全样本拟合结果，其余三行保持命令#45已确认的既有数字不变。

**详细文字描述**：

E0（暴露）四行从上到下依次为：LAD×date双向聚类（coef=0.106，95%CI[0.043,0.169]，区间明显最宽）、LAD单向聚类（coef=0.106，95%CI[0.090,0.122]，区间最窄之一）、Holdout确认样本（coef=0.171，95%CI[0.138,0.203]，点估计明显高于其余三行，这与4.4节正文已有描述"confirmation-sample point estimate is visibly higher than the other three"完全一致，改动后依然成立）、**修订后的Development sample单次拟合**（coef=0.089，95%CI[0.070,0.109]——与LAD单向聚类的宽度相近，不再像旧版汇总那样明显更窄）。

R0c（恢复）四行：LAD×date双向聚类（coef=0.085，95%CI[0.069,0.101]）、LAD单向聚类（coef=0.085，95%CI[0.073,0.097]）、Holdout确认样本（coef=0.073，95%CI[0.052,0.094]）、**修订后的Development sample**（coef=0.074，95%CI[0.059,0.089]）——四行点估计彼此接近（0.073-0.085区间内，跨度0.012，比旧版描述的"跨度0.015"略窄但同样支持"四行点估计彼此接近"这一定性结论），区间宽度也彼此接近，与4.4节正文"all four confidence intervals are narrow and overlap closely"的描述完全一致，改动后依然成立。

**对4.4节正文的影响**：改动后，E0和R0c两个margin原有的定性描述（"confirmation-sample点估计对E0明显更高""四行对R0c彼此接近"）**均不受影响，无需改写**；唯一需要更新的是如果正文明确引用了development sample行的具体数字（当前引用为R0c的0.067、隐含E0的0.091左右），需要改为选项(a)的新数字（E0: 0.089，R0c: 0.074）。

---

## 额外发现（核实过程中顺带注意到，独立于以上两项问题）

**Section 4.4正文关于"confirmation-sample置信区间最宽"的表述，与实际数据不符——这一问题独立于本命令的两项核实任务，且与Figure 10的既有（未改动）三行数字有关，不受问题二的修订影响。**

`Paper1_draft.md`第239行原文："For the exposure margin, the confirmation-sample point estimate is visibly higher than the other three, ... **and its confidence interval is the widest of the four shown for this margin**."

直接核实E0四行的95%CI宽度（其中Holdout/LAD单向/LAD双向三行均为既有、未被本命令改动的数字）：

| 行 | 95% CI宽度 |
|---|---|
| LAD×date双向聚类 | **0.1254（实际最宽）** |
| Holdout（confirmation） | 0.0652 |
| LAD单向聚类 | 0.0327 |
| Development sample（旧版汇总） | 0.0196 |

**实际上"LAD×date两向聚类"这一行的区间宽度（0.125）明显超过"Holdout confirmation"行（0.065）**，正文"its confidence interval is the widest of the four shown for this margin"这一表述**与图中实际数字不符**——即使不考虑本命令对development sample行的任何修订，这一描述错误在当前（未修订）版本的Figure 10中就已经存在，此前的多轮审查似乎都未专门核对过这一具体的"哪一行最宽"的表述。

**建议修改**：将第239行改为准确描述，例如："For the exposure margin, the confirmation-sample point estimate is visibly higher than the other three, which are themselves close to one another. The two-way clustered estimate has the widest confidence interval of the four shown for this margin, reflecting the additional uncertainty introduced by clustering on both district and date simultaneously."（具体措辞留给网页端定稿，本命令只确认了数字上的不一致并给出可直接参考的修改方向。）

---

## 产出文件

`raw/q1_result.json`、`raw/q1_bootstrap_full_corrected.csv`（500行完整β₁/β₂/z*重抽样明细）、`raw/q2_result.json`、`raw/q2_bootstrap_E0_dev_gustsq.csv`、`raw/q2_bootstrap_R0c_dev_gustsq.csv`；图`figures/Figure_10_robustness_forest_REVISED.png/.pdf`；脚本`q1_bootstrap_beta2_check.py`、`q2_figure10_dev_sample_check.py`、`make_figure10_corrected.py`。

## 验收标准逐项确认

- 问题一基于实际500次重抽样数据给出明确结论（β₂从未接近零，最小值为点估计的45.6%），未重复旧文档"从未接近零"这一说法本身，而是重新在修正数据上验证并给出了具体百分比数字；同时给出了比"分母"更贴合数据的候选解释（分子β₁的变号），以及两版可直接替换论文正文的英文文字。
- 问题二明确了点估计的构造方法（5折训练集逆方差加权，训练集两两重叠约75%），给出选项(a)(b)(c)各自具体的可行性评估（含实际算出的数字：选项(a)/(b)相对当前SE分别为2.0-2.0×和4.2-6.5×），并给出了本地端建议（选项a）及重新生成的Figure 10详细描述。
- 两项均给出了可直接用于修改论文正文的具体文字或数字。
- 核实过程中发现的额外问题（4.4节"confirmation区间最宽"表述与实际数字不符）已如实报告，未局限于命令列出的两项。
