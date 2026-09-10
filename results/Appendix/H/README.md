# 附录 H：替代结果模型与事件条件概率

最近生成：2026-09-10T20:18:39+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices H`；项目根目录以脚本位置解析。

H03已补齐当前全体样本四个既定替代分布候选；H01/H02历史事件条件来源保留，各自适用范围分别标注。状态为产物完成待反馈。

## 关键结果摘要

H03已补齐当前全体样本四个既定替代分布候选；H01/H02历史事件条件来源保留，各自适用范围分别标注。状态为产物完成待反馈。

## 需求、产物与适用范围

### H01 — 已保存NB和序数/逐阈logit结果

已生成。正文定位：§3.1 P031; §4.4 P070; P101。可用于事件条件方法说明；不是当前最终规格分布稳健性证明。McFadden字段null保留缺失。

- [tables/H_ORDINAL_SUMMARY.csv](tables/H_ORDINAL_SUMMARY.csv)

- [tables/H_ORDINAL_SUMMARY.md](tables/H_ORDINAL_SUMMARY.md)

- [tables/H_CONDITIONAL_COEFFICIENTS.csv](tables/H_CONDITIONAL_COEFFICIENTS.csv)

- [tables/H_CONDITIONAL_COEFFICIENTS.md](tables/H_CONDITIONAL_COEFFICIENTS.md)

### H02 — 已保存事件条件lognormal参数与曲线

已生成。正文定位：§4.4 P070; P101。参数仅按既有记录导出，边界/优化诊断保留；极端theta不能当作有效物理阈值。不导出新增降水交互曲面。

- [tables/H_CONDITIONAL_LOGNORMAL.csv](tables/H_CONDITIONAL_LOGNORMAL.csv)

- [tables/H_CONDITIONAL_LOGNORMAL.md](tables/H_CONDITIONAL_LOGNORMAL.md)

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。

## APP-H03-LINK

# APP-H03-LINK 第四工作包执行与回传报告

状态：产物完成，待研究负责人反馈分析。前三包J03/F02/G03/I02已由负责人关闭；GI-W01至W09图文待改继续保留。本报告为本包执行事实，不是独立科学审查或整稿成文。

## 范围与实际动作

本地实际正文§3.1位于DOCX直接body P030（旧登记P031是Table2表注）。该段及H.1既有分布比较指向全体暴露/恢复；没有明确天气子样本替代分布检验要求，因此只执行四项：暴露NB2/Tweedie、恢复Gamma/Tweedie。天气样本仅进入已存在H.3来源整理和原分箱描述，未另拟合GLM。

当前最终X逐行复用G的正式参数/预处理来源，并与保存的OLS预测、C样本指纹相核对。全体E=60437保留8979个0客户、固定14/25平台及温度平方/gust-pressure；全体R=51173保留正式正客户与全期p99规则、二次阵风及温度平方/gust-precip和客户控制。未重新OLS、CV、结点、Cause Code或样本选择。

累计执行4个既定候选的首次拟合，另对无效NB2执行1次有限数值恢复，共5次候选求解调用；复用2个正式OLS参考。NB2首次拟合器内部另拟合一次Poisson取得初值，该辅助步骤不作为候选；恢复阶段没有辅助拟合。当前调用的缓存/拟合数见H03_LAST_EXECUTION.json。H.2/H.3零次拟合；经验频率由现有输入按原阈值/箱汇总。

NB2原默认初始化路径返回alpha=0、非有限目标/score/Hessian并产生溢出，完整失败产物保留为INITIAL_FAILURE。按本包允许的有限数值恢复，协议另记录一次确定性初值修正：令mu0为当前样本客户均值，截距log(mu0)、其他beta为0，alpha初值用本地原_estimate_dispersion(mu0,y−mu0,n−rankX)，下限沿原实现0.05；随后仍联合估计全部beta/alpha。X/y、似然、BFGS200次和gtol1e−5不改，未比较多个有效解择优。原三项有效GLM在该修正中直接复用。详见H03_NUMERICAL_AMENDMENT.json及RECOVERY_START.csv。

## 冻结的family/link与参数规则

旧H.1 step_b_distribution_check.py：NB2使用BFGS最多200次，联合估计当前样本alpha；不能搬旧alpha=4.71044。fragility_demo.py的Poisson矩估alpha=15.9478属于另一自由结点伴随探索，仅登记为历史，不作为本次H.1配置。Gamma显式Log；两Tweedie显式Log、var_power=1.5、eql=True；IRLS最多100次、tol=1e−8。Gamma/Tweedie均采用原Pearson X2 scale，未搜索power。

OLS目标为E[log(1+C)|X]或E[log(T)|X]；log-link GLM以log E[C|X]或log E[T|X]为线性预测器。两者系数幅度没有相等要求，exp(OLS预测)未当作原响应算术均值。未计算跨尺度RMSE或跨变换AIC/BIC排名；Tweedie完整似然和AIC/BIC均NA，其有限准似然deviance/score用于计算诊断。

## 拟合与数值有效范围

|样本|候选|n|收敛|点估计有效|区间完整可用|max abs mean score|scale|alpha|
|---|---|---|---|---|---|---|---|---|
|E0_all|NB2|60437|True|True|True|6.715447330614486e-06|1.0|4.703206959218843|
|E0_all|Tweedie|60437|True|True|True|6.756839702434681e-15|211.24796528607746|NA|
|R0c_all|Gamma|51173|True|True|True|2.6455022445215322e-14|1.978554567676766|NA|
|R0c_all|Tweedie|51173|True|True|True|7.393543390802535e-15|6.405663818323911|NA|

H03_MODEL_STATUS.csv及各模型DIAGNOSTICS/OPTIMIZER保存目标、得分、迭代和全部捕获警告；不只看converged。冻结诊断要求有限参数/正均值/目标/score，max abs mean score≤1e−4及原求解器收敛。失败不以历史解填位，也不因符号不同继续扩大预算。

## 推断路径

使用本地statsmodels的model.score_obs和observed Hessian构造score/Hessian sandwich；two-way=LAD＋date−交叉组，各分量G/(G−1)×(n−1)/(n−k)小样本修正。与直接cov_cluster_2groups(fit, LAD, date)做数值对应。本次全体两个样本各111个LAD，系数区间/p按既定t(110)。

NB2使用完成优化后(beta, alpha)坐标，包含alpha的完整score、Hessian及协方差，k包含alpha；不是固定旧alpha条件推断。Gamma/Tweedie用拟合Pearson scale的beta score与observed Hessian，scale未作为额外联合参数维度。未套用OLS residual sandwich，未混入默认独立SE。

每个候选完整矩阵与LAD/date/交叉分量、实际score、参数和拟合均值均保存。负方差的对应区间留NA；不abs、截零或正定化。非PSD与单系数负方差分开记录，不由前者自动否定所有单项区间。

每个矩阵的observed information秩、最小特征值及负对角项见H03_MODEL_STATUS.csv与逐模型DIAGNOSTICS；不改变先前三包其他矩阵的适用边界。

## 阵风基与交互项的逐项对应

表中“同证据”仅指在同一t规则的95%系数区间是否排除0一致，不是等效性检验；不要求替代模型支持当前形式才能交付。

|样本|替代模型|项|OLS系数|GLM系数|GLM two-way SE|GLM 95% CI|同符号|同95%证据|
|---|---|---|---|---|---|---|---|---|
|E0_all|NB2|z_gust_pressure|-0.0349337059|-0.0456453552|0.0180232351|[-0.0813631767, -0.00992753367]|True|True|
|E0_all|NB2|gust_low|-0.026952198|-0.039297127|0.00755892471|[-0.0542771416, -0.0243171125]|True|True|
|E0_all|NB2|gust_ramp|0.121461728|0.0756282186|0.0156667728|[0.0445803521, 0.106676085]|True|True|
|E0_all|Tweedie|z_gust_pressure|-0.0349337059|-0.041095745|0.0154771324|[-0.0717677888, -0.0104237013]|True|True|
|E0_all|Tweedie|gust_low|-0.026952198|-0.0403649715|0.00777333305|[-0.0557698931, -0.02496005]|True|True|
|E0_all|Tweedie|gust_ramp|0.121461728|0.0782402982|0.014729718|[0.0490494544, 0.107431142]|True|True|
|R0c_all|Gamma|z_gust_0h|-0.000245239894|0.0188401187|0.019391577|[-0.0195894353, 0.0572696727]|False|True|
|R0c_all|Gamma|z_gust_sq|0.0809630592|0.0645483654|0.0088889108|[0.0469326306, 0.0821641002]|True|True|
|R0c_all|Gamma|z_gust_precip|-0.0244544683|-0.0254109071|0.010261609|[-0.0457470076, -0.00507480666]|True|True|
|R0c_all|Tweedie|z_gust_0h|-0.000245239894|0.0343178851|0.025908521|[-0.0170267224, 0.0856624926]|False|True|
|R0c_all|Tweedie|z_gust_sq|0.0809630592|0.0588424812|0.0125658965|[0.0339398238, 0.0837451387]|True|True|
|R0c_all|Tweedie|z_gust_precip|-0.0244544683|-0.0248378384|0.0115493924|[-0.0477260234, -0.00194965352]|True|True|

实际可对应12/12个阵风/交互系数对照；其中2项未同时满足原句的“方向和95%证据一致”。完整p值、OLS及GLM区间见H03_GUST_COMPARISON.csv，不能省略不一致项。

- R0c_all/Gamma/z_gust_0h：同符号=False，OLS 95%排除0=False，GLM 95%排除0=False。

- R0c_all/Tweedie/z_gust_0h：同符号=False，OLS 95%排除0=False，GLM 95%排除0=False。

E0平台约束已经固定在预测变量基中；这四项拟合不能独立证明平台存在或14/25最优。阵风主项与gust-pressure/precip交互分开解释，某单项系数不是所有协变量取值下的总导数。天气单11结点在本包未拟合GLM；未把hinge增量当作结点后总斜率。

## H.2/H.3既有证据与当前经验表

原H_ORDINAL_SUMMARY/H_CONDITIONAL_COEFFICIENTS/H_CONDITIONAL_LOGNORMAL保留。新增H03_EXISTING_H2_H3_SOURCES.csv逐项注明样本、原控制基、参数、图形路径和限制。原序数模型是全体E60437/R59834，恢复含零客户；H.3旧恢复全体59834、天气9806，不能改称当前51173/9254。原全控制系数与ordinal cutpoints未完整保存在summary，不能只凭阵风系数重建整条序数曲线。

已存lognormal参数可直接派生概率网格（H03_EXISTING_LOGNORMAL_CURVES.csv.gz）。六条旧优化诊断均报告success；部分theta/beta极大、与经验频率不符或缺乏可解释位置，不能改写为算法未收敛或物理机制被证伪。本包不修优化器、不重做ordinal/logit/曲面。

H03_EVENT_CONDITIONAL_FREQUENCIES保存当前四组原gust箱的分子/分母/概率，旧恢复同箱参考另放data。客户阈值实际.5/5.5/100.5/1000.5，因客户为整数等价>0/>5/>100/>1000；时长严格>3/>12/>48h。原ordinal标签<3h对应right-closed (0,3]，后续说明应消除标签歧义。所有概率条件于已发生且已纳入样本的事件；不能当作地区日事件概率。

正文§4.4 P069的粗分箱语句对应如下，只合并原箱，分母按事件池化：

|口径|n|>100客户数|当前频率|原文数字|备注|
|---|---|---|---|---|---|
|first original bin (calm not explicitly defined)|5544|808|0.145743146|0.4|calm mapping unconfirmed; first original bin shown explicitly|
|12-18 m/s|11894|1680|0.141247688|0.29|pooled original adjacent bins, not unweighted mean of bin probabilities|
|>23 m/s within existing bins|1601|652|0.407245472|0.48|pooled original adjacent bins, not unweighted mean of bin probabilities|

“calm”原句未明确定义数值边界，这里明确展示原首箱(0,4]，不假称找到了0.40的相同口径。其余12–18及>23范围按原箱闭合规则与上限45汇总，差异留给人工改写；不重开原因范围或旧proxy尾部审计。

## 精确待改原句与可写范围

- §3.1 P030：“A log link…”需区分变换响应OLS与真正log-link GLM；删除两者相同估计对象的暗示。

- 同段“same gust coefficients in sign and significance”：只能按本次逐项对照限定。表中不一致或无相容区间的候选不得写为全部一致；完整条件与例外同时呈现。

- §4.4 P069及Appendix H标题：可以说明本数据中事件条件严重程度与district-day分母不同，以及当前分箱曲线/旧单调形式的适用限制；不能据非单调性普遍禁止其他领域使用fragility一词，也不能用未发生的优化器不收敛作物理结论。无业务字段支持时，不将calm大事件唯一归因为某类运营机制。

- H.2/H.3：恢复旧样本与当前经验表分别标注；旧ordinal<3h标签的实际包含3h规则需写清。不强行把旧曲线的数值和解释迁移到当前恢复样本。

可以客观表述：在固定当前预测变量基及样本条件下，已完成四项既有分布/均值设定的有限全样本敏感性；对应系数的方向、两维聚类区间和例外见表。不能据此宣告主模型最优、结点重新验证或原尺度预测性能获胜。

## 复现、文件与停止

本次命令：`C:\Users\haoya\.conda\envs\pyoutagegust\python.exe D:\Pyprogramme\pyOutageGust\main_appendix.py --appendices H --h03-only`。项目根目录运行`python -X utf8 -B main_appendix.py --appendices H --h03-only`；限定本包重算加`--recompute-h03`；只读预检加`--check-only`。

冻结协议/覆盖矩阵在logs/H03_PROTOCOL.json、data/H03_COVERAGE_PLAN.csv；模型定义、完整系数、关键项对照、当前条件频率在tables；可复算X/响应/参数/拟合均值/score/Hessian/协方差及历史适用范围在data；状态和技术检查在logs。无新增图形：本次表格及旧曲线网格已足够，不为凑family图扩展任务。

原H01/H02及未知人工文件按既有事务机制保留。完成只标产物待反馈，不自动关闭H或开始F–J写作；没有论文修改、ZIP、远程发布或独立科学审查。
