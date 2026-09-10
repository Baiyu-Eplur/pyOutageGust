# APP-F02-COV 第二工作包执行与回传报告

记录时间：2026-09-10T17:22:51+01:00。本包执行完成，待研究负责人反馈分析；不自动关闭F02。

## 范围与来源

仅天气暴露与天气恢复的正式固定final模型。原final two-way CSV已经保存se_lad列；旧缺口文字称其不存在不准确。本轮补齐完整协方差及分量、两套95%区间、同样本来源和复算输入，不重算F.3。

## 实际动作与有效范围

|模型|状态|动作|本次OLS拟合数|原因|
|---|---|---|---|---|
|E0_weather_final|complete|REUSE_C_IN_SAMPLE_AND_FINAL_COEFFICIENTS|0||
|R0c_weather_final|complete|REUSE_C_IN_SAMPLE_AND_FINAL_COEFFICIENTS|0||

## 计算和推断规则

两种推断使用同一设计矩阵、同一残差和同一系数。采用本地statsmodels 0.14.6 cov_cluster/cov_cluster_2groups，use_correction=True；two-way为LAD分量＋date分量−交叉组分量，不是仅按LAD-date交叉组聚类。每个分量分别使用G/(G−1)×(n−1)/(n−k)修正，k为实际设计列数。

95%系数区间及双侧p值均用t(G_LAD−1)，沿用final表p_t_G1规则。该规则不因增加日期维度而改为其他自由度。原代码的SE转换规则为sqrt(maximum(variance,0))；这是代码规则，不表示本次样本曾出现负方差。本轮保留原始矩阵并显式记录异常，不abs或静默截零。

接口参考：[statsmodels两组聚类协方差文档](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html)。实际公式、默认参数和tuple输入支持已按本地0.14.6源码读取并保存哈希，没有升级依赖。

|模型|n|设计列/秩|LAD/date/交叉组|df|固定结点|
|---|---|---|---|---|---|
|E0_weather_final|9857|27/27|105/1001/6122|104|[11.0, 24.0]|
|R0c_weather_final|9254|29/29|104/995/5870|103|[11.0]|

## 与已存final结果的对齐

下列为逐系数最大绝对差，按协议atol=1e−9、rtol=1e−8核对；固定模型系数没有改变。

E0_weather_final：系数最大差0；two-way SE最大差6.1284311e-13；LAD SE最大差3.7325698e-13；原t规则p值最大差9.980905e-14。

R0c_weather_final：系数最大差0；two-way SE最大差3.8957726e-13；LAD SE最大差1.4432899e-13；原t规则p值最大差1.3138449e-13。

## 阵风项及既有交互项

下表保留实际SE变化方向。SE比小于1、区间跨0均不视为计算失败。

|模型/项|系数|LAD SE|two-way SE|比值|LAD 95% CI|two-way 95% CI|
|---|---|---|---|---|---|---|
|E0_weather_final/z_gust_pressure|-0.0864819353|0.0296861507|0.0339621982|1.144042|[-0.14535069, -0.027613184]|[-0.15383025, -0.019133622]|
|E0_weather_final/gust_low|-0.0594900668|0.0120073836|0.0152820249|1.272719|[-0.083301159, -0.035678974]|[-0.089794896, -0.029185238]|
|E0_weather_final/gust_ramp|0.0785017819|0.00761063905|0.00995255001|1.307715|[0.063409599, 0.093593965]|[0.058765502, 0.098238062]|
|R0c_weather_final/z_gust_0h|-0.0544761826|0.0431787049|0.0889725751|2.060566|[-0.14011096, 0.031158595]|[-0.2309323, 0.12197994]|
|R0c_weather_final/gust_hinge_11|0.0695946878|0.0079329687|0.0185293301|2.335737|[0.053861515, 0.08532786]|[0.032846132, 0.10634324]|
|R0c_weather_final/z_gust_precip|-0.0562315736|0.013013482|0.021897824|1.682703|[-0.082040746, -0.030422401]|[-0.099660743, -0.012802404]|

完整逐系数数据见tables/F02_COEFFICIENT_COMPARISON.csv；与原final逐项差值见data/F02_SOURCE_COMPARISON.csv。

## 对后续不确定性表述的直接影响

E0_weather_final：全部系数SE比范围0.952688–1.748490；两套95%区间是否包含0发生变化的项为incident_month[5]。该清单仅描述当前两种推断，不据此重新筛选变量。

R0c_weather_final：全部系数SE比范围0.912230–2.335737；两套95%区间是否包含0发生变化的项为incident_month[5], incident_month[11]。该清单仅描述当前两种推断，不据此重新筛选变量。

E0_weather_final：two-way矩阵最小特征值-9.41676333e-06，负对角项[]，数值修正none。该矩阵不是半正定，但本次各系数对角方差为正；逐系数SE和区间有效性与任意线性组合的方差不是同一判断。本包保留原两维聚类结果，不做联合检验或自动正定化。

R0c_weather_final：two-way矩阵最小特征值1.1437388e-06，负对角项[]，数值修正none。

后续F.2应使用本次同模型逐项结果，不沿用预设的倍数范围；本次原表对齐没有发现需要修改既存two-way单系数数字的实质差异。本轮不修改正文，也不因某项区间跨0改变主模型。

## 核验与文件

F02_TECHNICAL_CHECKS.json记录样本、列序、键、同系数/残差、协方差有限对称、对角/SE、区间规则、旧表对齐及保存输入复算。矩阵负特征值与负方差分别记录；没有自动正定化。

tables仅登记拟用于附录的完整系数比较主表；data/F02_SPECIFICATIONS.csv、F02_MODEL_STATUS.csv、F02_SOURCE_COMPARISON.csv及各模型DESIGN_METADATA、ROWS、DESIGN、COV_*属于支持或复算记录，不自动全列为论文排版表。

## 复现与停止

项目根目录：`python -X utf8 -B main_appendix.py --appendices F --f02-only`。只读预检加`--check-only`；重算本包协方差加`--recompute-f02`，仍优先复用兼容系数/残差，非强制再拟合。

F02_PROTOCOL.json在协方差计算前冻结输入、固定规格、配置和代码；F02_LAST_EXECUTION.json记录当前缓存/计算/拟合动作。输出固定在results/Appendix/F/，其他F管理文件保留。

J03由研究负责人确认匹配比较缺口关闭，保留正文PROXY，本轮未重跑或修改J。第二包待人工＋agent反馈分析；G/I及H未启动。没有独立科学审查、Word修改、ZIP或远程提交。
