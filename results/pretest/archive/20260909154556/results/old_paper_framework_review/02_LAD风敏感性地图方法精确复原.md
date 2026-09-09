# Step 2：LAD风敏感性地图方法精确复原（核心）

## 生产脚本定位

**`0519_4.3.py`**（787行，完整读取），输出到 `ResultsOutput\new2\Section4_3_VulnerabilityMaps_LogOLS\`，生成 `Figure3A_ExposureVulnerability_Customers_Map.png` 和 `Figure3B_RecoveryVulnerability_Duration_Map.png`（文件内部命名为"Figure3"，正文最终编号为"Figure 6"——脚本命名与论文最终图号不一致，属历史遗留，不影响方法本身）。定位依据：`530_Section4_3_extra.py`（生成Appendix E2相关性检验）明确从`Section4_3_VulnerabilityMaps_LogOLS`目录读取输入，与`项目研究框架与数据结果说明.md`第9.3节点名的脚本完全一致，交叉验证确认无误。

## 问题1：画的是什么量？——**不是阵风系数，是条件预测的结果水平本身**

**关键澄清（推翻了命令背景假设的前提）**：这张图画的**不是每个LAD的"阵风系数"、"交互项系数"或任何弹性/敏感度指标**，而是**在统一天气情景下，每个LAD的条件预测停电结果水平**（预测客户数、预测持续时间本身，不是系数）。

代码原样引用（第581-591行）：

```python
pred_lad["pred_customers_vulnerability"] = prediction_level_ols(
    m_customers,
    pred_lad,
    customers_formula
)

pred_lad["pred_duration_vulnerability"] = prediction_level_ols(
    m_duration,
    pred_lad,
    duration_formula
)
```

其中 `prediction_level_ols`（第144-154行）：

```python
def prediction_level_ols(model, pred_df, formula):
    rhs = formula.split("~", 1)[1].strip()
    X_pred = patsy.dmatrix(rhs, data=pred_df, return_type="dataframe")

    exog_names = list(model.model.exog_names)
    X_pred = X_pred.reindex(columns=exog_names, fill_value=0.0)

    beta = model.params.loc[exog_names]
    eta = X_pred @ beta

    return np.exp(eta)
```

即：把每个LAD的预测协变量代入模型公式算出线性预测值`eta = Xβ`，再取`exp(eta)`还原到原始尺度（因为模型是log-OLS）。**这是"预测的log(客户数)/log(持续时间)取指数后的水平值"，不是任何系数**。命名虽然叫"vulnerability_score"（变量名）、地图标题叫"Predicted affected customers"/"Predicted outage duration"（图注），但底层量就是模型条件预测值本身。

正文明确说明（原文摘录）：*"Because the predictions are obtained by exponentiating the fitted log-OLS values, they recover the conditional median rather than the conditional mean (Jensen's inequality)."*——即这是**条件中位数**（因指数变换的Jensen不等式偏差），不是条件均值，更不是弹性系数。

## 问题2：每个LAD的"敏感度"是怎么估计出来的？——**没有per-LAD单独回归，也没有交互项，也没有收缩/分层处理**

**明确回答三个子问题**：

### (a) 是否对113个LAD分别单独回归？**否。**

`0519_4.3.py`全文**只拟合了两个模型**（一个customers、一个duration），都是在**全量样本**（44,821个完备案例）上一次性估计，代码原样引用（第523-538行）：

```python
rhs = """
z_gust_0h + z_gust_0h_sq +
z_precipitation_24h_sum +
z_temperature_0h +
z_pressure_msl_0h +
z_gust_0h:z_pressure_msl_0h +
urban_binary +
log_population + income_deprivation_rate + deprivation_gap_pct + morans_i +
C(incident_year) + C(incident_month)
"""

customers_formula = f"log_customers ~ {rhs}"
duration_formula = f"log_duration ~ {rhs}"

m_customers, d_customers = fit_ols_clustered(customers_formula, df, cluster_col)
m_duration, d_duration = fit_ols_clustered(duration_formula, df, cluster_col)
```

这与v6论文Table 1（4.1节基线模型）用的是**完全相同的基线回归公式**——LAD地图不是一个独立的新模型，就是复用基线模型做预测。

### (b) 是否用"阵风×LAD"交互项一次性估计全部LAD各自的效应？**否。**

公式里唯一的交互项是`z_gust_0h:z_pressure_msl_0h`（阵风×气压，全国统一的一个交互效应），**完全没有`z_gust_0h × LAD`或`z_gust_0h × C(LAD21CD)`这类交互项**。也就是说，模型里**根本没有"每个LAD自己的阵风系数"这个东西存在**——全国所有LAD共享同一套阵风一次项、二次项、阵风×气压交互项系数。

### (c) 是否用了分层模型/随机效应/经验贝叶斯收缩？**否，完全没有。**

模型是普通OLS（`smf.ols(...).fit(cov_type="cluster", ...)`，第116-126行），LAD只在两个地方出现：①作为聚类稳健标准误的分组变量（`cluster_col = "LAD21CD"`），②作为预测阶段区域协变量取值的分组单位（下面(d)说明）。**没有任何随机效应、混合效应模型、或经验贝叶斯收缩机制**，不存在"小样本LAD的估计值被向整体均值拉近"这种处理。

### (d) LAD之间的差异从哪里来？——完全来自区域协变量取值不同，天气被强制设为同一个值

代码原样引用（第559-579行，构造预测框架的核心逻辑）：

```python
lad_cols = [
    "LAD21CD",
    "log_population",
    "income_deprivation_rate",
    "deprivation_gap_pct",
    "morans_i",
    "urban_binary"
]

lad_df = df[lad_cols].groupby("LAD21CD", as_index=False).mean()

z_gust_benchmark = (GUST_BENCHMARK_MPS - gust_mean) / gust_sd

pred_lad = lad_df.copy()
pred_lad["z_gust_0h"] = z_gust_benchmark
pred_lad["z_gust_0h_sq"] = z_gust_benchmark ** 2
pred_lad["z_precipitation_24h_sum"] = PRECIPITATION_Z
pred_lad["z_temperature_0h"] = TEMPERATURE_Z
pred_lad["z_pressure_msl_0h"] = PRESSURE_Z
pred_lad["incident_year"] = baseline_year
pred_lad["incident_month"] = baseline_month
```

其中固定值（第50-53行）：`GUST_BENCHMARK_MPS = 20.0`（阵风20 m/s）、`PRESSURE_Z = TEMPERATURE_Z = PRECIPITATION_Z = 0.0`（气压/温度/降水都设为标准化均值，即"平均"情景）、年份取样本最早年份、月份取1月。

**每个LAD的输入数据里，只有`log_population`、`income_deprivation_rate`、`deprivation_gap_pct`、`morans_i`、`urban_binary`这5个区域协变量取该LAD自己样本的均值，其余全部变量（阵风一次+二次项、气压、温度、降水、年月）对全部113个LAD都设成完全相同的值。** 因此，图上呈现的LAD间差异，100%来自这5个区域协变量的差异，**不存在任何"该LAD对阵风更敏感/更不敏感"这个信息**——地图字面意思上跟"风敏感性"没有直接关系，只是"在假设所有地方遭遇同样天气的前提下，因为人口/贫困/城乡/空间聚集程度不同，模型预测出的停电水平高低不同"。

### 样本量过小的LAD是否有特殊处理？

**没有任何样本量筛选或标注**——因为根本没有per-LAD单独回归，所以不存在"某个LAD样本太少导致回归不稳定"这个问题。唯一会导致某个LAD在地图上呈现"No estimate"（灰色空白）的情况，是该LAD在数据集里**完全没有出现过一条记录**（`groupby("LAD21CD").mean()`不会为零观测的LAD生成行，merge后该LAD协变量全为NaN，通过`missing_kwds`显示为灰色）——这是"完全无数据"，不是"数据量少但仍勉强回归"。

**这一发现直接推翻了命令背景的核心担忧**：命令#20背景假设"每个LAD自己的阵风系数"可能存在小样本不稳定问题，但实际上v6最终方法里根本不存在这个东西，**这类小样本不稳定风险只存在于早期被放弃的草稿脚本`vulnerability.py`/`figure4_vulnerability.py`里**（这两个脚本确实对每个LAD单独跑Poisson回归，`if len(g) < 200: continue`，见 `01_建模画图脚本清单.md`），但这两个脚本**不是v6最终论文实际采用的方法**。

## 问题3：画图工具与配色

- 地理边界文件：`data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp`（与命令#6/#9/#16全程复用的LAD边界文件同一份）。
- 坐标系：投影到`EPSG:27700`（英国国家格网）。
- 配色方案：`cmap="Oranges"`（单色渐变，不是发散配色）。
- 颜色分箱：**不是分位数分箱（不是把连续值切成几档上色）**，而是用连续色阶，但**颜色范围的上下限用分位数截断**（`MAP_COLOR_LOWER_Q=0.00`、`MAP_COLOR_UPPER_Q=0.98`），即用0-98百分位数确定颜色条的vmin/vmax，防止个别极端LAD压缩其余LAD的颜色区分度——原始数值本身仍完整导出到CSV，只是可视化时对颜色范围做了截断，不影响导出数据。
- 附加地图元素：UK全域缩略图（inset）、比例尺、指北针。
- 输出：PNG（600dpi）+ PDF双格式，同时导出`Figure3_VulnerabilityMap_Data.csv`（含每个LAD的原始预测值，未做颜色截断）和GeoPackage文件。

## 问题4：正文对这些LAD差异的解读

摘录v6正文关键句（合理引用范围内）：

> *"Figure 6(a) shows substantial geographic heterogeneity in the exposure margin... Because the outcome is measured as the number of affected customers, these spatial differences may partly reflect population exposure and demand-related scale, alongside other regional characteristics included in the model. The map should therefore be interpreted as a conditional model-based estimate of absolute customer disruption, rather than as a population-normalised measure of outage vulnerability."*

> *"regions with higher predicted outage exposure do not necessarily exhibit longer predicted outage duration under the same reference weather scenario... The results show a strong negative association between predicted affected customers and predicted outage duration across LADs (i.e. Pearson r = -0.893; Spearman rho = -0.879; both p < 0.001)."*

> *"Since LAD fixed effects are omitted so that observed regional covariates can carry the cross-sectional signal, the mapped patterns may also reflect unobserved regional factors correlated with those covariates. The maps are therefore best read as descriptive conditional regional comparisons, rather than as the isolated effect of any single regional characteristic."*

正文对这张图的解读非常审慎，**多次明确提醒读者不要把它理解成"物理脆弱性地图"或"历史停电发生率地图"**，只是"在统一假设天气情景下，模型预测出的停电水平相对区域比较"，并且明确承认由于没有放LAD固定效应，地图模式可能还掺杂了协变量之外的未观测区域因素。这与本次代码级复原的方法完全吻合，论文正文的措辞谨慎程度与实际方法的局限性是匹配的。
