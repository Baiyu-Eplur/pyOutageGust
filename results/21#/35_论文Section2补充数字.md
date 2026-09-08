# Section 2撰写所需的两组补充数字

## Step 1：全量最终样本customers_v2、duration_B完整描述统计表

样本：命令#21确立的全量最终样本（weather_natural+technical_asset）。customers_v2口径n=60,437（E0可用样本），duration_B口径n=59,834（R0c可用样本，已按合并样本重新计算的p99=192.08h截尾）。

### customers_v2

| 统计量 | 原始值尺度 | log1p(customers_v2) |
|---|---|---|
| 均值 | 93.02 | 2.1384 |
| 中位数 | 2.00 | 1.0986 |
| 标准差 | 410.96 | 2.0190 |
| 最小值 | 0.00 | 0.0000 |
| p25 | 1.00 | 0.6931 |
| p75 | 35.00 | 3.5835 |
| 最大值 | 27,013.00 | 10.2041 |

### duration_B（小时）

| 统计量 | 原始值尺度 | log(duration_B) |
|---|---|---|
| 均值 | 11.84 | 1.6558 |
| 中位数 | 6.27 | 1.8352 |
| 标准差 | 19.96 | 1.3493 |
| 最小值 | 0.05 | -2.9957 |
| p25 | 2.03 | 0.7097 |
| p75 | 12.67 | 2.5390 |
| 最大值 | 192.08 | 5.2579 |

n分别为60,437（customers_v2）、59,834（duration_B）。两个变量原始值尺度均严重右偏（均值远大于中位数），log变换后分布更接近对称，这是论文2.3节采用log-OLS规格的直接经验支持。

---

## Step 2：全六组Cause Code vs weather_natural+technical_asset主规格——量化构成偏移证据

**数据来源说明（重要，先声明口径）**：以下数字全部来自命令#12/#13的历史回执文件，**这两个命令的计算发生在命令#16去污染修复之前**（即样本还混有locked_temporal_test污染，命令#12/#13当时称为"WT子集"n=59,834/60,437，是去污染前的完整总体，与命令#21最终确立的干净全量样本n≈相同但成分不完全相同）。**本次核实只从这两份历史文件里提取已有数字，未重新计算，也未尝试用去污染后的最终样本重复这一对比**——如果2.4节需要更新口径一致的数字，需要另外发一条命令在最终样本上重做这一对比；本命令按背景要求，只从命令#12/#13现成回执中核实提取。

### 数字1（推荐，最容易向读者说清楚）：R0c阵风一次项与二次项在两个Cause Code范围下的对比（命令#13）

| 项 | 全六组R0c'_B（n=116,064） | weather_natural+technical_asset子集（n=59,834） |
|---|---|---|
| 一次项 5折同号/显著 | 5/5 · 5/5 | **3/5 · 0/5** |
| 一次项折间均值系数 | 0.0237 | **0.00053**（趋近于零） |
| 二次项 5折同号/显著 | 5/5 · 5/5 | 5/5 · 5/5（**未变**） |
| 二次项折间均值系数 | 0.0687 | 0.0760（**几乎未变**） |
| 二次项折间CV% | 13.88% | 14.40%（**几乎未变**） |

来源：`claude_branch/results/cause_code_robustness/05_一次二次项拆解判断.md`

**可直接用于论文2.4节的表述**：*"When restricting the sample from all six Cause Code groups to the weather_natural+technical_asset subset, the quadratic gust term remains essentially unchanged (0.0687 vs. 0.0760, CV 13.9% vs. 14.4%, significant in 5/5 folds in both cases), while the linear gust term collapses from a stable, significant effect (5/5 folds significant, mean coefficient 0.0237) to a statistically indistinguishable-from-zero estimate (0/5 folds significant, mean coefficient 0.00053). This indicates that the linear-term signal observed in the full six-group sample is at least partly attributable to composition effects from Cause Code categories unrelated to weather (e.g., non_fault_or_unknown), rather than a physically robust wind effect — providing empirical, not merely theoretical, support for excluding these categories from the main specification."*

### 数字2（备选）：R0c'_B恢复侧临界风速点估计在两个范围下的对比（命令#12）

| 范围 | n | 拐点点估计(m/s) | Bootstrap CI(m/s) |
|---|---|---|---|
| 全六组（命令#11） | 116,064 | 8.62 | [7.49, 9.59] |
| weather_natural+technical_asset | 59,834 | 9.87 | [8.43, 12.66] |

来源：`claude_branch/results/cause_code_robustness/03_范围对比与判断.md`

这个数字可以作为数字1的补充说明，但**不如数字1直观**——因为拐点本身是一个比值型指标，命令#13已经精确定位这个差异的根源就是数字1里的一次项塌缩（分子趋零导致比值不可靠），如果2.4节篇幅有限，建议优先使用数字1，数字2作为脚注补充"这也是为什么本文最终不报告一个精确的恢复侧临界风速数值"这一方法论决定的证据。

## 验收标准逐项确认

- Step1描述统计表覆盖customers_v2和duration_B两个变量、原始值和log两种尺度的全部要求统计量（均值/中位数/标准差/最小值/p25/p75/最大值）；✅
- Step2从命令#12/#13的实际历史回执文件中核实提取数字（`05_一次二次项拆解判断.md`、`03_范围对比与判断.md`），未凭空构造，并明确声明了这些数字的口径（去污染修复之前）与本次核实范围（未重新计算）。
