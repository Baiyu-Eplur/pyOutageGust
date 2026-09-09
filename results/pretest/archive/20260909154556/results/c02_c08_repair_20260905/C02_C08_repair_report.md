# 工作命令 #45：C02/C04/C05/C06/C07/C08代码修复 + 基于C01修复数据的最终重新生成

**范围说明**：独立于常规工作命令编号序列的专项修复延续（C01之后），产出全部写入新目录`claude_branch/results/c02_c08_repair_20260905/`与对应脚本目录，未覆盖命令#44（C01修复）之前的任何产出。C03按要求只做事实记录不改代码；C09本命令不涉及。全部代码修复先于最终生成完成，最终生成是基于全部修复代码的唯一一次连贯运行（脚本内部按需重建C01修正样本，但均使用同一份`corrected_sample_builder.py`，未拼接不同批次的中间产物）。

---

## C02：R²定义的文字说明 + 备选口径数字

**核实结论：当前代码（`variance_decomposition_pipeline.py`的`nested_r2_sequence`/`oof_predictions`函数）确实是"拼接全部5折的样本外预测后统一计算一次R²"（pooled out-of-fold R²），不是"5折各自算R²后取平均"。这一实现方式本身合理、常见，未做任何代码修改。**

### 可直接用于论文方法论部分的英文描述

> Out-of-sample R² is computed by pooled out-of-fold prediction: for each of the five date-grouped folds, the model is fit on the other four folds and used to predict the held-out fold; these five sets of held-out predictions are concatenated across all observations before a single R² is computed against the full sample's outcome variance. This differs from, and is not the same statistic as, the simple arithmetic mean of five separately-computed per-fold R² values — the pooled statistic weights each observation equally regardless of which fold it falls in, whereas averaging per-fold R² values implicitly gives each fold equal weight regardless of size.

### 备选口径（5折各自R²的简单平均）具体数字对比

在命令#21最终合并样本（C01修复后）上，同时计算两种口径（脚本`c02_r2_definition_check.py`，`raw/c02_r2_definition_comparison.json`）：

**E0**：

| 步骤 | Pooled OOF R²（当前方法） | 5折简单平均 | 5折各自R²(%) |
|---|---|---|---|
| baseline | 0.7945% | 0.6713% | 0.965, 0.866, 0.408, 1.315, -0.197 |
| +nongust_weather | 1.7000% | 1.5723% | 2.633, 1.476, 1.263, 1.319, 1.171 |
| +gust | 2.9863% | 2.8479% | 4.630, 1.942, 2.718, 2.422, 2.527 |

**R0c（阵风先于customers）**：

| 步骤 | Pooled OOF R²（当前方法） | 5折简单平均 | 5折各自R²(%) |
|---|---|---|---|
| baseline | 1.4738% | 1.1726% | 3.779, 2.727, **-1.401**, 2.151, **-1.393** |
| +nongust_weather | 2.4407% | 2.0991% | 5.768, 3.455, -1.121, 2.612, -0.219 |
| +gust | 3.5017% | 3.0918% | 8.882, 3.179, -0.040, 2.916, 0.522 |
| +customers | 11.3004% | 10.9741% | 14.973, 10.996, 8.171, 12.000, 8.731 |

**如实说明**：Pooled OOF R²在每一步都系统性略高于5折简单平均（差距约0.13-0.35个百分点），且逐折R²本身波动很大——R0c基线模型在两折（第3、5折）甚至出现负R²（模型样本外表现比直接预测均值还差）。这一差异是否需要在论文中同时报告两种口径，留给网页端结合论文语境决定；本命令只提供两组数字供选择。

---

## C04修复：`step13_storm_prediction_check.py`重复log1p变换

**修复前**：`predict_for_subset()`返回`predicted_level = np.exp(eta)`（η是模型在log1p(customers_v2)尺度上的拟合值），随后`figure9_storm_validation.py`绘图时对该level值再做`np.log1p(sub["predicted"])`——即y轴实际画的是`log(1+exp(η))`而非η本身。对R0c（η是log(duration_B)尺度），绘图时用`np.log(sub["predicted"])=log(exp(η))=η`，这一步骤恰好精确抵消（数学巧合），**R0c面板此前实际未受这一bug影响**；E0面板（`log1p(exp(η))≠η`，仅在η较大时才近似相等）**确实受到影响，尤其在低η（低预测值）区域被系统性抬高**。

**修复后**：`predict_for_subset()`直接返回η本身（脚本`c02_c08_repair_20260905/figure9_storm_validation.py`），绘图时不再做任何多余的指数化/对数化。

**修复前后产出差异**：修复前后E0面板的整体视觉形态（列状堆叠、系统性高于参考线）基本保持一致——**说明"暴露侧在低观测值区间系统性高估"这一定性发现不是该bug的产物，是真实存在的模式**；但每个点的精确纵坐标数值已改变（尤其低η区域），任何基于旧数据算出的具体相关系数/MAE数字需要用修复后的重新计算值替换（见下方最终生成结果）。

---

## C05修复：R0c风暴期验证集区分"参与训练"与"被p99截尾排除"

**修复前**：`storm_r0c`子集只要求`duration_B_full_span_hours`非缺失且大于0，**未检查是否超过R0c训练样本自身的p99截尾阈值**，把模型从未见过、且原理上无法评估的极端长时事件与正常验证事件混在同一组"验证集"里呈现。

**修复后**：脚本`figure9_storm_validation.py`用R0c训练样本自身实际使用的p99截尾阈值（修复后数据上为**192.08小时**）对风暴期事件分组，分别标注`in_training_range`（duration_B≤192.08h）与`excluded_by_p99_truncation`（duration_B>192.08h），Figure 9(b)中后者用**空心三角形**单独标出，并分别计算两组的Pearson相关系数。

**修复前后产出差异——一项新发现**：

| 子集 | n | Pearson r | p值 |
|---|---|---|---|
| 全部7场风暴，参与训练范围内 | 4,883 | **+0.378** | 1.90×10⁻¹⁶⁵（极显著） |
| 全部7场风暴，**被p99截尾排除** | 48 | **-0.382** | 0.0073（显著，但方向相反） |

**修复前的呈现方式会把这48个事件的负相关悄悄平均进整体统计里，掩盖了这一实质性差异。修复后清楚显示：模型对训练范围内的风暴事件有真实、强、统计极显著的预测能力，但对超出训练截尾范围的极端长时事件，预测值与观测值不仅不相关，反而呈现统计显著的负相关（模型在这一范围内不具备任何超出随机猜测的预测价值）。** 完整明细：`raw/figure9_R0c_c05_split_summary.csv`。

---

## C06修复：标准化范围的准确描述

**核实结果**：核对`v3_validation_pipeline.py`的`design_train_valid`函数（命令#21等最终模型逐字复用，未改动），设计矩阵中变量的标准化状态如下：

**经z-score标准化（用训练折自身均值/标准差）**：`gust_0h`→`z_gust_0h`（及其平方`z_gust_0h_sq`、与气压的交互项`z_gust_pressure`）、`precipitation_24h_sum`→`z_precipitation_24h_sum`、`temperature_0h`→`z_temperature_0h`、`pressure_msl_0h`→`z_pressure_msl_0h`；R0c模型额外对`log1p(customers_v2)`→`z_log1p_customers_v2`（及其平方）做标准化。

**保留原始/未标准化尺度**：`urban_binary`（0/1二元哑变量）、`log_population`（人口的自然对数，作为连续协变量直接进入模型，**未**做z-score标准化）、`income_deprivation_rate`（原始比率，未标准化）、`deprivation_gap_pct`（原始百分点，未标准化）、`morans_i`（原始统计量，理论范围约[-1,1]，未标准化）、年份与月份固定效应（原始0/1哑变量，参照组编码）。

### 可直接用于论文Table 2/Section 3.3的英文描述

> Standardization is applied selectively, not uniformly, across the covariate set. Gust speed, 24-hour cumulative precipitation, temperature, and mean sea level pressure are each standardized to z-scores using the training fold's own mean and standard deviation before entering the model (including the quadratic gust term and the gust-pressure interaction, both constructed from the already-standardized components); for the recovery model, log1p(affected customers) is standardized the same way. The five region-level socioeconomic covariates (an urban-rural indicator, log population, the income deprivation rate, the income deprivation gap, and Moran's I) and the calendar year and month fixed effects are entered in their original, untransformed scale (log population is log-transformed but not additionally standardized). Coefficients on the standardized covariates are therefore directly comparable to one another as effects per one standard deviation of the underlying variable, while coefficients on the unstandardized covariates retain their natural units.

---

## C07修复：统一Figure 4与Figure 6的customers参照场景

**修复前**：`step3_dose_response_curve.py`（Figure 4）把customers z-score项设为**估计样本的实际列均值**（`Xtr_full.mean(axis=0)`），由于z-score本身的平方项的样本均值在数学上约等于该变量的样本方差（≈1，而非0），导致`z_log1p_customers_v2_sq`≈0.9999833而非精确的0；`step4_baseline_regional_map.py`（Figure 6）则**显式将customers一次项和平方项都设为精确的0.0**。两者参照场景不完全一致。

**修复后**：`figure4_dose_response.py`第69-74行改为与Figure 6完全相同的显式赋值——`X["z_log1p_customers_v2"] = 0.0`、`X["z_log1p_customers_v2_sq"] = 0.0`。

**技术澄清（供图注准确引用，不使用"customers恰好为0"这一容易误导的表述）**：这一参照点是**模型自身标准化空间下的z-score=0**，对应"log1p(customers_v2)取训练样本均值"这一水平（即典型/平均规模事件），**不是字面意义上"受影响客户数恰好为0"这一情景**（若要表示customers_v2=0，需要的z-score是`(log1p(0)-mean)/sd = -mean/sd`，是一个远离0的负值）。已在两个脚本的注释及本报告中明确记录这一区别，避免论文图注沿用不准确的"customers=0"措辞。

**修复前后产出数字差异**：由于customers平方项从≈0.99998变为精确0，Figure 4(b)R0c曲线在η计算里少了`β_sq×(0.99998-0)≈β_sq`这一常数偏移，这是一个**不随阵风变化的常数平移**，不改变曲线形状或拐点位置，只轻微改变纵轴绝对水平（连同C01修复的数据变化一起体现在最终数字中，见下方Figure 4/7结果）。

---

## C08修复：论文文字层面已确立方法论回写到绘图代码

1. **Bootstrap置信区间动态化**：`figure4_dose_response.py`不再包含任何硬编码区间数字，`turning_point_ms`、`boot_lo_ms`、`boot_hi_ms`全部来自脚本内当次实际拟合+500次bootstrap重抽样的计算结果（本次最终生成实际读出9.16-12.16 m/s，见下方最终数字），并写入`raw/figure4_turning_point_summary.json`供核查。
2. **措辞统一**：Figure 4(a)图内标注文字从"critical wind speed"改为"**turning point**"，与论文当前文字（命令#40已确立的"turning point"措辞）保持一致。
3. **Figure 10方法论记录**："development sample"这一行是对命令#16已确立的、在corrected开发样本内部构造的5折系数（`raw/E0_dev_corrected_fold_coefs.csv`等）做**逆方差加权汇总**得到的单点估计，这是对已有多个折系数的meta分析式聚合，**不是重新做一次开发样本整体单次拟合**——这一统计学含义与论文当前对"development sample"作为交叉验证汇总（而非独立单次回归）的描述一致，本命令未发现数字对不上的情况，因此按提醒要求**未重新设计新的森林图方法论**，只在脚本docstring中完整记录这一方法论含义供核查。

---

## C03（如实记录，本命令不涉及代码修复）

**核实结果**：weather_natural子样本比较**确实同时改变了两件事**——

1. **duration_B截尾点不同**：weather_natural子样本自身的p99截尾阈值为**142.84小时**（`final_core_tables.py`运行日志），与主规格（weather_natural+technical_asset合并）的p99截尾阈值**192.08小时**不同。
2. **5折GroupKFold的折分配也不同**：`add_fresh_folds()`对每个子样本分别调用，`GroupKFold`基于**该次调用输入数据自身的唯一日期集合**做分组分配——由于weather_natural子样本的唯一日期集合本身就是主规格样本日期集合的一个子集（且规模小得多，n=9,758 vs 59,834），即使某个具体日期同时出现在两个样本里，其被分到"第几折"的结果在两次独立调用中并不保证相同（`GroupKFold`的折分配依赖于分组的完整数量和顺序，样本范围一变，分配必然重新计算）。

**这意味着weather_natural vs主规格的方差分解/系数稳定性对比，是在"两个不同的因变量分布截尾点+两套不同的交叉验证折分配"下做出的，不是严格意义上"只改变Cause Code筛选范围、其余完全不变"的受控对比。** 建议网页端在论文方法论部分加一句如实说明这一点的文字，例如："The weather_natural subsample comparison necessarily uses its own duration truncation point (142.8h, versus 192.1h in the main specification) and its own independently-constructed cross-validation folds, since both are derived from the subsample's own date and duration distributions; the comparison therefore isolates the combined effect of Cause Code restriction together with these necessary re-derivations, not Cause Code restriction alone."

---

## 最终统一重新生成

用`corrected_sample_builder.py`（封装命令#44的猴子补丁修复逻辑）+ 上述C04/C05/C06/C07/C08全部代码修复，完成唯一一次连贯的最终重新生成。

### 1. 全部核心系数表

**E0（暴露）全样本单次拟合**：β₁(z_gust_0h)=-0.036014，β₂(z_gust_0h_sq)=0.105997（完整表：`c01_repair_20260905/raw/step4_E0_corrected_full_coefs.csv`，本命令的C04-C08修复不改变模型系数本身，只影响绘图/评价代码，故该系数与命令#44完全一致，已用`figure4_dose_response.py`独立重新拟合核实数值不变）。

**R0c（恢复）全样本单次拟合**：β₁(z_gust_0h)=-0.000993，β₂(z_gust_0h_sq)=0.084954。

**5折稳定性（本命令新增，最终版）**：

| | E0二次项 | R0c二次项 |
|---|---|---|
| 开发样本（逆方差加权汇总） | 0.0913±0.0050 | 0.0668±0.0037 |
| 确认样本（单次拟合） | 0.1708 | 0.0730 |
| 全量合并，LAD单向聚类 | 0.1060（se=0.0083） | 0.0850（se=0.0061） |
| 全量合并，LAD×日期双向聚类 | 0.1060（se=0.0320） | 0.0850（se=0.0081） |

四组95% CI均不跨零，二次项在全部四种稳健性检验口径下保持显著（详见Figure 10）。

### 2. 临界风速最终数字

| | 标准化z-score | 物理单位(m/s) |
|---|---|---|
| 点估计 | 0.1699 | **10.81** |
| Delta method 95% CI | — | [10.13, 11.48] |
| Bootstrap 95% CI（500次，种子20260826） | [-0.143, 0.426]（跨零） | **[9.16, 12.16]** |

与命令#44（C01修复）报告的数字完全一致（本命令的C02-C08修复均不涉及模型拟合本身，只涉及展示/评价代码），已用独立重新拟合核实。

### 3. 方差分解最终数字

**主规格**：E0基线0.7945%→+非阵风气象0.9054pp→+阵风**1.2864pp**；R0c（阵风先）基线1.4738%→+非阵风气象0.9669pp→+阵风**1.0611pp**→+customers**7.7987pp**。customers/阵风权重比=7.35倍。

**weather_natural子样本（n=9,857/9,758，p99=142.84h）**：

- E0：基线OOS **-0.8876%**（负）→+非阵风气象+2.7945pp→**+阵风+0.4539pp**
- R0c（阵风先）：基线13.732%→+非阵风气象+4.6416pp→+阵风**+2.7626pp**→+customers**+1.3226pp**

**一项重要发现（C01修复的连锁效应，此前从未在干净数据上出现过）**：命令#25（污染前置数据）曾报告weather_natural子样本里E0的阵风边际贡献为**-0.15pp（负值，与预期方向相反）**，是项目历史上标注为"未解开的异常"之一。**在完成C01（事件代表行）修复后，这一数字变为+0.4539pp（正值），符号方向反转，与"更纯净的天气相关样本应展现更强阵风解释力"这一原始预期一致。** weather_natural子样本E0临界风速点估计（β₁=0.1329，β₂=0.0457，z*=-1.4545，物理单位3.80 m/s，Delta CI含负风速物理不可能值）**依然判定为不可靠**，与命令#25/#26的判断一致，本次修复未改变这一定性判断。

R0c的"阵风在weather_natural子样本反超customers"这一核心发现**依然成立且方向不变**：主规格阵风(1.06)<customers(7.80)，weather_natural阵风(2.76)>customers(1.32)。

### 4. 全部10张图

已重新生成，见`figures/`目录：`Figure_1_study_area_map`、`Figure_2_distribution`、`Figure_4_dose_response`、`Figure_5_variance_decomposition`、`Figure_6a_regional_customers`、`Figure_6b_regional_duration`、`Figure_7_magnitude_comparison`、`Figure_8_weather_subsample_comparison`、`Figure_9_storm_validation`、`Figure_D1_composition_effect`（均PDF+300/600dpi PNG双格式）。

### 5. 详细文字描述（比照命令#35/#37/#42方式）

**Figure 1**：与命令#33/#42版本视觉上几乎无法区分——事件密度热点仍集中在LPN（伦敦）与EPN/SPN交界处，全图分布形态未因C01修复而改变（阵风/日期修正不影响事件的空间位置）。

**Figure 2**：四面板分布形状与此前版本一致（customers右偏、log1p尺度低位锯齿状、duration双峰），因为customers_v2/duration_B均为事件级聚合值，不受C01影响，数字（p99_customers=1515.0, p99_duration=116.98h）与命令#42完全相同。

**Figure 4**：(a)E0曲线谷底位置从此前版本的约10.69 m/s右移到**10.81 m/s**，浅绿色阴影置信带（现动态读取而非硬编码）宽度约3 m/s，标注文字已改为"turning point"；(b)R0c曲线形状与此前几乎一致，谷底同样在10 m/s附近，标注的二次项p值现为1.0×10⁻⁴³（读自本次实际拟合，替代此前的固定描述）。

**Figure 5**：与命令#37版本相比，customers柱高从7.87降到**7.80**，阵风柱（E0从1.07到1.29、R0c从0.62到1.06）**两者均明显上升**，baseline柱两者均下降——整体柱状图轮廓保持"customers远高于其余全部类别"的核心视觉印象不变，但阵风两根柱子相对visible地"长高"了一截，肉眼可辨。

**Figure 6a/6b**：与命令#33/#34版本相比，色阶范围（6a: 5.27-10.03，此前5.28-10.13；6b: 5.92-8.15，此前5.99-8.21）几乎无变化，地图空间格局（伦敦核心浅、周边环带深）完全保持一致，因为区域协变量与customers/duration聚合值不受C01影响，颜色刻度上的微小差异全部来自Figure 4/6统一后的customers=0参照点及C01阵风修正对拟合系数的微小扰动。两图预测面相关系数（Pearson=-0.785，Spearman=-0.771）与此前（-0.780/-0.758）基本一致。

**Figure 7**：三条横向柱状的比值全部小幅上升——阵风→E0从2.79变为**2.88**，阵风→R0c从2.37变为**2.56**，customers→R0c从5.99变为**6.02**——**customers这根柱子依然远长于其余两根，视觉排序未变，但两根"阵风"柱子明显更接近customers柱子一些**，与Figure 5看到的"阵风权重上升"这一趋势相互印证。

**Figure 8**：(a)面板此前版本weather_natural柱子指向零线以下（负值），**本次两根柱子均指向零线以上**，这是本命令最值得注意的视觉变化——E0在weather_natural子样本下"阵风解释力不增反降"这一此前的反直觉发现，在C01修复后从图上直接消失。(b)面板weather_natural分组里绿色（阵风）柱子依然略高于紫色（customers）柱子（2.76 vs 1.32），这一"反超"视觉效果保持不变。

**Figure 9**：(a)面板视觉形态与此前几乎相同（低观测值区间竖直列状堆叠、系统性位于参考线上方），确认C04修复未改变这一定性模式。(b)面板新增的空心三角形标记清晰聚集在图右上角（观测值x=5-7.5区间），且**全部明显落在参考线下方**（预测值远低于观测值），肉眼可辨这是一片与其余散点行为方向相反的独立簇团，直观印证了C05发现的"模型对训练范围外的极端事件系统性低估、且相关性转负"这一新结论。

**Figure 10**：森林图整体形态与命令#37版本高度相似（development sample置信区间最窄、holdout对E0给出的点估计明显偏高、LAD双向聚类置信区间最宽），八个点估计的具体位置较此前版本普遍略微右移（数值略增，与前述系数普遍小幅上升的趋势一致），未出现任何置信区间跨零的情况。

**Figure D1**：与命令#42版本**数字完全相同**（10.94/10.75/8.87/2.32等逐格数值一致），因为该图仅依赖n_stages（stage_row_count）、customers_v2、duration_B三个变量，均不受C01/C02-C08任何一项修复影响——这是一项有意义的一致性核对，确认了"C01只影响天气/日期字段"这一修复范围界定本身是准确的。

---

## 产出文件

- 报告：`C02_C08_repair_report.md`（本文件）
- 脚本（`claude_branch/scripts/c02_c08_repair_20260905/`）：`corrected_sample_builder.py`、`final_core_tables.py`、`c02_r2_definition_check.py`、`figure1/2/4/5/6/7/8/9/10/D1_*.py`
- 结果（`claude_branch/results/c02_c08_repair_20260905/`）：`figures/`下10张图PDF+PNG；`raw/`下全部系数表、方差分解表、bootstrap原始数据、C02对比JSON、C05分组统计等

## 验收标准逐项确认

- [x] C02-C08每一项均给出了具体的修复前/修复后产出差异（数字或视觉描述），未止步于"已修复"
- [x] Figure 4与Figure 6修复后的customers参照场景完全一致（均为z-score=0），已用准确措辞记录其真实含义（非"customers恰好为0"字面意义）
- [x] 最终重新生成的全部数字和图表来自同一次连贯运行（统一使用`corrected_sample_builder.py`），未拼接不同批次中间产物
- [x] 全部10张重新生成的图均提供了详细文字描述
