# 修订审查、落实说明与待补分析

日期：2026-09-05

## 文件与工作范围

- 基线：最初上传的 `Draft(2).docx`、`Appendix(6).docx`。
- 用户修订：`Paper1_Introduction_draft (6).md`、`Paper1_Appendices (1).md`。
- 本地核实依据：`50_数学审查本地核实.md`。
- 交付：`Draft_revised.docx`、`Appendix_revised.docx`。

本轮完成了能由现有文字、公式及所提供本地核实支持的修复，并对不能闭合的声明收窄、撤回或标记。没有在本环境重新运行原始数据实验，也没有把核实报告引用的本地CSV、脚本或图件当作已实际取得的附件。本轮不声称第3类新增实验已经完成。

Word沿用原稿的A4页面、页边距和Times New Roman正文体系，保留可编辑公式、表格及原始图件；对图3、4、7、10的错误标签和不成立区间作定向处理。附录新增G（用户已提供的Cause Code分布材料，经校正）与H（可追溯的本地数学和实现审查）。原Markdown文末的历史工作日志不作为论文正文导入。

## 对用户第1类措辞修改的审查结论

用户修订方向总体正确，但未全部闭合：一些修复只进入正文局部，摘要、结论或相邻段仍保留旧断言；也有个别新句引入新的数学或证据问题。本轮已进行全篇传播与校准。

| 对应事项 | 用户稿修改审查 | 本轮落实 |
|---|---|---|
| M01 对称性 | 删除19%–48%并说明关于自身顶点对称，核心修改有效 | 保留；补充该百分比实际是无截距阵风项的对数预测子比值，不能解释为客户预测百分比 |
| M02 线性项显著性 | §3.1方向正确，但§4.1仍说线性显著性决定是否能报告具体位置 | 全文删除该判据，恢复模型最低点也被承认存在 |
| M03 气压条件 | 平均气压限定与一般公式有效 | 纳入完整精度9.656/10.694/11.732，并注明交互项不确定性 |
| M04 物理阈值 | 新增边界段有效，但摘要、标题、引言及结论仍称critical/操作触发 | 全部统一为条件拟合最低点；不推荐操作阈值 |
| M05 区间机制 | 用户将分母接近零改为可能原因，尚未利用新诊断 | 依据500次确定性复现撤回该原因；不再将旧物理CI当作已验证结果 |
| E01 开发历史 | 承认早期使用混合数据并修正10.69→12.13→10.69，方向正确 | 删除仍存在的“后期未参与模型开发”“严格确认”；纳入六项早期步骤 |
| E02 样本与图10 | 改为最终合并样本、0.066及最宽区间等修改有效 | 进一步澄清0.066是重叠5折加权汇总，移除其伪独立区间，区分样本专属标准化 |
| E03 风暴证据 | §4.3末段和部分结论正确区分拟合与排序 | 摘要及其余“第二独立方式”等残留同步删除，图9明确样本内检视 |
| E04 贡献与选择 | 仍有“与天气毫无关系”“独立于结果归因”、负增量不是不利证据等残留 | 限定为指定两组预测器的log尺度增量；负增量按预测结果如实解释；加入附录G |
| E05 阶段与机制 | 用户补充非必然延长、非外生阶段数，有效 | 删去首尾“唯一构成解释”和排除中介残留；不从一次项符号推出全域单调 |
| A01 GLM最低点 | 承认GLM也可求最低点，有效；“严格正链接函数导数不变号”不准确 | 改为指数逆链接函数的导数严格为正；统一模型选择理由 |
| A02 反变换 | 未落实实际exp(η)且暴露图未减1 | 全文和图注明确，绝不称为无偏条件算术均值 |
| A03/A04 原因分类 | 承认作者六类分组及天气影响恢复，有效但仍过强 | 保留分类实施规则，明确官方释义映射未补齐，不推断统计独立 |
| A05 图7比值 | 用户已改max/min，正确 | 补齐50点网格与exp(log(1+C))尺度；不沿用报告中方向混乱的客户端点比值 |
| A06 8倍 | 改10–13倍范围，方向正确 | 直接按图5显示顺序给7.87/0.62≈12.7 |
| A07 D1样本量 | 改47,840，正确；“D1–D6均开发样本”仍误包Figure D1 | 分清D1/D2开发样本与Figure D1最终样本，并补最终四组数量 |
| A08 客户数系数 | 已解释D2/F2来自不同样本，正确 | 保留并统一写成标准化log(1+C)及平方；最终全样本多阶段占比约40.5% |
| A09 风暴名称 | 本地文本检查未覆盖原Word图片，不能推翻已看到的Isha | 原图片视觉错误确认；新时间轴用Henk并标明月份示意 |
| A10 悬空引用 | 区域面相关性引用已删；G已新增，但残差占位与其他旧引用未全修 | 改为实际G/H；不声称未附诊断图已经收录；旧数据复核不作独立证据 |
| A11 显著性措辞 | F尾段局部修复有效，但旧版本独立复核语句残留 | 恢复一次项“继续不显著”，删除旧重叠数据独立 corroboration |

引言中的一般语句合并、英式拼写及正常表述调整均纳入审查；本轮没有因其与审查无关而自动回退。下文附原Word与用户稿的文字对应记录，以及用户稿到交付稿的逐块处理索引。

## 本地核实报告中需要进一步校准的解释

1. **19%–48%不只是比较中心选错。** 报告明确显示分子分母是β₁z+β₂z²，未包括截距、其他变量和指数反变换。这不是客户数拟合值的百分比，不能按报告建议英文直接重新引入正文。
2. **β₂在500次抽样中均为正，不等于每次都显著。** 新附录H只报告符号稳定性。分母最小值0.03659，也不支持旧文“接近零引起失稳”的解释。
3. **分子接近零本身不必然导致偏态或重尾。** 描述已观察到的偏度−0.519和超额峰度1.144，但不把它们唯一归因于分子。需要考虑系数联合分布及参照系变化。
4. **每次重新标准化不自动意味着更保守。** 是否增加或减少最终物理量方差取决于协方差及目标定义。旧9.2–12.1 m/s带不能仅靠固定原样本均值/SD乘回重样本z分位就宣称完成核实。
5. **0.0660的来源是重叠CV加权汇总。** 不是单次全开发样本回归；原加权区间忽略重叠训练样本协方差的风险，不能作为独立拟合区间。已撤其图线，点只作描述。
6. **10.46和2.20是全样本残差因子，不是“真实条件期望倍数”。** 条件残差分布可能随协变量变化。暴露响应还涉及1+C以及减1，所以“所有比值和斜率均不受影响”过强；原图保留的只是exp(η)尺度比值。
7. **局部报告的客户数端点比值方向混乱。** 报告写“严格p99/p1”但对客户曲线又以p1作为分子；本轮不采用其2.53端点解释，只采用已明确追溯的max/min=5.99。
8. **Cause Code分箱是无条件描述。** 不等于比较otherwise similar事件，也不能证明低风速稀释是负增量的唯一根源，或证明恢复模型不受影响。
9. **“本机未搜到Isha”不覆盖上传Word中的图片。** 原附件图3明确写Isha；报告自己也承认未取得当前Word。本轮按实际附件修复。
10. **重新合并的最终样本不是信息意义上的全新独立样本。** 删除“clean全量”的独立验证含义，并避免依据报告中#15/#16交叉的时间戳自行补出精确小时先后。

## 已落实的第2类修复

- 条件最低点：平均气压下0.157286个标准差、10.694 m/s，正文按10.69报告；压力±1SD结果在H1说明。
- Bootstrap：500次、固定种子20260826、匹配误差5.55×10⁻¹⁷、β₂分布和z分位在H2报告；旧物理区间撤回而非替换为编造区间。
- 时序分析：统一Earlier/Later或说明Confirmation只是历史标签；0.0660按CV汇总描述；最终合并恢复β₂=0.079237；参照均值/SD表H3补齐。
- 客户数预测器：标准化log(1+C)及其平方，覆盖§2.4、§3.3、表2、附录A、表D2与F2等。
- 绘图尺度：图4、6、7及正文用exp(fitted log outcome)，暴露图包含加1且未减1，不称条件算术均值。
- 图7：50点网格max/min，保留2.79、2.37、5.99但重新限定解释。
- D1/D2：保留已核实开发样本47,840；Figure D1使用59,834；补最终分组35599/9348/7907/6980，避免拼造5–9/10+分组。
- 附录G：采用用户给出的十分位表及报告确认的端点、63.70%和36.83%，纠正条件比例的分母表达。
- 图3：重绘月份示意时间轴为Henk；图4撤去旧物理CI带；图10撤开发CV nominal区间并改标签；其他图数值不重估。

## 需要补算、补材料或进一步实验的第3类事项

| 优先级 | 项目 | 需要的输入/做法 | 本轮处理 |
|---|---|---|---|
| P1 | 物理风速Bootstrap CI | 每次β₁、β₂、β₃及gust/pressure均值SD；固定物理气压参照，逐次换算v*后求分位 | 撤旧9.2–12.1带，H.2写明公式及Word批注 |
| P1 | 可比的开发/后期估计与区间 | 单次全开发样本拟合，统一或完整记录尺度；或考虑重叠协方差的重采样 | CV点仅描述，不用旧nominal CI推断 |
| P1 | 真正独立的预测评价 | 从未参与开发的新时期/新风暴；锁定模型后评估 | 当前时序称事后敏感性，风暴称样本内拟合 |
| P2 | 风暴内gust与customers贡献比较 | 按整场风暴或连续块留出，做相同嵌套/消融模型和不确定性比较 | 不再声称第二条证据复现排序反转 |
| P2 | 反变换与条件算术均值 | 明确目标C还是1+C；检查残差随X的变化，评估全局或条件smearing | 保留expη图，准确标注，未生成新均值预测 |
| P2 | 低风速支持与负增量机制 | 支持匹配/重加权或范围敏感性，考虑样本量及选择影响 | G仅描述支持差异，不下唯一机制结论 |
| P2 | 客户数曲线单调性与阶段机制 | 原变量标准化参数和实际范围；导数与分层图；机制需额外识别或过程数据 | 不从单个线性系数符号推全域单调/调度机制 |
| P2 | 原相关性段落的配对样本口径 | Pearson/Spearman/dCor/MI具体事件集合、D缺失/截尾规则和置换结构 | 暂撤原n=60,437相关性数值，保留不独立的概念边界与D的分析，不宣称数值错误 |
| P2 | 缺失首阶段敏感性 | 排除最小阶段号≥2事件后重复关键分析 | B.5保留开放限制 |
| P2 | 原始Cause Code官方映射 | 完整官方字典/依据与逐码映射 | 保留实施分组但明确来源未完成 |
| 补材料 | 残差诊断及替代GLM表 | 报告引用的4张PNG、诊断统计、完整分布/链接/系数与推断设置 | 未虚构附录图，H.5及批注明确尚未提供 |
| 补材料 | 历史duration_A/B论证 | 原始对比输出、必要时在分样本复核 | B.2仅作历史选择依据，不作独立验证 |
| 投稿前 | 参考文献未核实字段 | 正式标题、日期、版次、作者、卷页和URL | 保留原unverified字段并加批注，未猜填 |

这些项目不意味着本轮未完成已获授权的文字修复；它们表示新的数值结论所需的证据尚未提供。当前文稿已经避免把它们表述为已完成实验。

## Word中的追踪方式

正文4条、附录3条定位批注，用于物理CI、开发CV区间、诊断材料、分类字典和参考文献等未闭合事项。批注不等于新增分析结论。交付为清理过正文的修订稿，未开启整篇删除/插入修订，以免公式和图表被大量修订标记打断；下面的对应索引记录变动。

## 原Word与用户Markdown的文字对应审查索引

以下以归一化段落比较定位差异，统一了引号、空白和部分排版标记；公式记法、表格行列和Word自动编号的差异可能同时被列出。对应号为读取时的正文块索引，不是Word页码。数学内容另按M类问题人工检查，未将纯排版差异判为实质错误。

### 正文

| 用户稿块 | 原Word最近对应块 | 类型 | 用户稿定位片段 | 审查处置 |
|---|---|---|---|---|
| 3 | 3 | 文字变化 | Power outage; wind fragility; critical wind speed; distribution network; variance decomposition; ext | M04：关键词不再暗示已识别物理临界风速 |
| 6 | 7 | 文字变化 | These events illustrate a general pattern in electricity distribution networks: outage impact, measu | M04：工程动机与当前证据匹配 |
| 7 | 8 | 文字变化 | Existing empirical work on power outage duration and customer impact under severe weather has establ | M04：取消将所有易损性函数视为分段阈值函数的概括 |
| 9 | 10 | 文字变化 | First, neither the statistical outage literature nor the structural fragility literature provides fi | M04/E04：改为可被本文回答的研究问题，避免未经充分核实的排他性文献缺口 |
| 10 | 11 | 文字变化 | Addressing both gaps requires an observational record long enough, and varied enough, to include bot | M04：衔接研究问题 |
| 11 | 12 | 文字变化 | This paper addresses these two gaps using outage records from UKPN covering April 2021 to March 2024 | E01/E03/M04：引言同步最终证据等级 |
| 12 | 13 | 文字变化 | The remainder of this paper is organised as follows. Section 2 describes the UKPN dataset, the const | E01/E03：章节说明不再声称独立确认全部结果 |
| 17 | 18 | 文字变化 | Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 19 | 21 | 文字变化 | **Figure 1.** Study area and event density. The map shows the three UKPN licence areas (London, Sout | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 22 | 24 | 文字变化 | The exposure margin is measured by the number of customers affected by an incident, referred to here | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 25 | 26 | 文字变化 | where $C_i$ is affected customers for incident $i$, $\mathcal{R}_i$ is the set of restoration stages | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 26 | 27 | 文字变化 | The recovery margin is measured by the total duration of the incident, referred to hereafter as rest | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 29 | 29 | 文字变化 | where $D_i$ is restoration duration for incident $i$, and $T_{i,r}^{\text{start}}$ and $T_{i,r}^{\te | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 30 | 30 | 文字变化 | Constructing affected customers by aggregating across stages, rather than taking the customer count  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 32 | 32 | 文字变化 | Table 1 reports descriptive statistics for affected customers and restoration duration in the final  | E05：分布双峰的机制不由现有分层分析直接证明 |
| 34 | 34 | 表格/公式及文字变化 |  /  Statistic  /  Affected customers (n=60,437)  /  log(1+affected customers)  /  Restoration duration, hour | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 35 | 36 | 文字变化 | **Figure 2.** Distribution of affected customers and restoration duration, original scale and after  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 38 | 39 | 文字变化 | UKPN records a Cause Code for each outage incident, describing its underlying original cause at a mo | E01/E04/A03-A04：分类依据和组成检验边界 |
| 40 | 41 | 文字变化 | The full covariate set comprises gust speed and its square, an interaction between gust speed and me | A08：实际客户数预测器变换 |
| 44 | 45 | 文字变化 | This paper uses a parametric regression model, not a machine learning model. The reason is straightf | M02/A01：模型选择依据 |
| 47 | 47 | 文字变化 | where $Y$ denotes the outcome margin (affected customers or restoration duration, in the log scale d | M02/A01：修正用户稿“正链接函数导数不变号”的新错误 |
| 52 | 52 | 文字变化 | This approach is followed here for the model specification described in Section 3.3. Several earlier | E01：纳入#9-14全部六个分析步骤，删除“仅一处例外”“未查看” |
| 55 | 56 | 文字变化 | One specific number illustrates why the confirmation sample matters. An early estimate of the critic | E01/E02：精简正确数字历史 |
| 58 | 59 | 文字变化 | The final model specification is the same for both outcome margins, except that the recovery model i | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 61 | 61 | 文字变化 | where $Y_i$ denotes the outcome for incident $i$ (one plus affected customers for the exposure margi | M03/A08：符号定义和实际模型一致 |
| 62 | 62 | 文字变化 | Year and month fixed effects are additive, entered as separate sets of dummy variables rather than a | A02：expη无减1和无smearing均需明示；不导入报告“真实均值10.5倍”断言 |
| 63 | 63 | 文字变化 | Table 2 lists the covariates denoted $\mathbf{X}_i$ in Equation 4, beyond gust speed, its square, an | A08：表2与公式映射 |
| 64 | 64 | 文字变化 | **Table 2.** Covariates included in $\mathbf{X}_i$, in addition to gust speed, its square, and the g | A08：表2原来把FE和X混同，改宽标题 |
| 65 | 65 | 表格/公式及文字变化 |  /  Variable  /  Category  /  Model  /   / --- / --- / --- /   /  Mean sea level pressure  /  Weather  /  Both  /   /  24-hour | A08：表2实际客户数变量 |
| 70 | 70 | 文字变化 | Table 3 reports the gust coefficients from the final model specification, estimated on the full anal | M02/M04/E01：删去残留线性显著性判据与独立验证 |
| 72 | 72 | 表格/公式及文字变化 |  /  Term  /  Exposure margin  /  Recovery margin  /   / --- / --- / --- /   /  Gust (linear)  /  -0.032 (p = 0.022)  /  0. | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 73 | 73 | 文字变化 | For the exposure margin, the linear gust term is negative and significant, so the two coefficients j | M02/M03：线性项只表示参考点局部斜率 |
| 74 | 41 | 新增/结构变化 | The full model in Equation 4 also includes an interaction between gust and pressure, so the point at | M03：条件化最低点 |
| 77 | 75 | 文字变化 | where $\beta_1$ and $\beta_2$ are the linear and quadratic gust coefficients from Table 3. At other  | M03：使用完整精度本地核查数值 |
| 78 | 76 | 新增/结构变化 | A quadratic function is symmetric around its own turning point by construction: equal standardised d | M01：保留用户已有效完成的对称性修正 |
| 79 | 112 | 新增/结构变化 | For the exposure margin, the turning point is located a small distance above the sample mean, at 10. | M05：撤回分母近零机制和未验证物理CI，新增可核实诊断 |
| 80 | 77 | 文字变化 | For the recovery margin, the linear gust term is not distinguishable from zero (Table 3), so the tur | M02/M03：恢复最低点不因线性不显著而消失 |
| 81 | 78 | 文字变化 | Figure 4 shows the fitted response curve for each margin, with the other covariates held at their sa | M01/A02：区分对数二次函数和指数显示尺度 |
| 82 | 80 | 文字变化 | **Figure 4.** Fitted gust-outcome response curves, other covariates held at sample means and pressur | M05/A02：图中移除未核实CI并纠正纵轴语义 |
| 83 | 81 | 文字变化 | The recovery model also includes affected customers and its square as covariates. Affected customers | E05：去除不变号和排除中介的残留断言 |
| 84 | 121 | 新增/结构变化 | The turning point identified for the exposure margin marks where the slope of the fitted curve chang | M04：与摘要结论一致 |
| 86 | 83 | 文字变化 | The results in Section 4.1 establish that gust has a real, stable relationship with both outcome mar | E04：解释贡献在对数尺度且不等同作用强度 |
| 87 | 84 | 文字变化 | Nested models are used to decompose the explained variance for each margin. Starting from a baseline | E04/A06：确定图5比值、添加顺序、预测与因果边界 |
| 88 | 86 | 文字变化 | **Figure 5.** Marginal out-of-sample R-squared by variable group, exposure and recovery margins. Bar | A08/E02/E04：图5方法与口径 |
| 89 | 87 | 文字变化 | Figure 6 provides a further point of comparison, using the observed variation in regional covariates | A02/A10：地图预测量与相关对象，删除悬空引用 |
| 90 | 89 | 文字变化 | **Figure 6.** Baseline regional variation in predicted outcomes under a fixed reference weather scen | A02：地图图注解释expη |
| 91 | 90 | 文字变化 | The same comparison can also be made directly in terms of predicted outcomes, rather than in terms o | A05/A02：50点网格极值、客户数+1，拒绝本地报告倒置端点比值 |
| 92 | 92 | 文字变化 | **Figure 7.** Ratio of the highest to the lowest fitted value across the plotted range (1st to 99th  | A02/A05：图7精确定义 |
| 94 | 94 | 文字变化 | Taken together, the results in this section support two conclusions rather than one. Gust accounts f | E04：不把恢复模型比较扩展到全部outcomes |
| 96 | 96 | 文字变化 | Section 4.2 describes the full population of weather- and asset-related incidents, most of which hav | E03/E04/A03：取消独立于结果归因的假设 |
| 97 | 97 | 文字变化 | The recovery model described in Section 3.3 was re-estimated on the subset of incidents for which th | E04：不把R2增量翻倍理解为物理作用翻倍 |
| 99 | 99 | 表格/公式及文字变化 |  /  Margin  /  Variable  /  Main sample  /  Weather-only subset  /   / --- / --- / --- / --- /   /  Exposure  /  Gust  /  +1.0 | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 101 | 102 | 文字变化 | The negative result for the exposure margin in the weather-only subset is not treated here as eviden | E04/A10：使用已有选择分布证据但不声称因果机制已确定 |
| 102 | 103 | 文字变化 | A second, independent way of restricting attention to weather-driven incidents is to examine periods | E03：消除第二独立验证的残留说法 |
| 103 | 104 | 文字变化 | The finalised exposure and recovery models, unchanged from Section 4.1, were then used to predict ou | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 107 | 59 | 新增/结构变化 | The predictions evaluated against storm-period outcomes in this section come from a model fitted on  | E03：重复段落内容已纳入风暴开头和图注 |
| 108 | 109 | 文字变化 | The Cause Code approach and the storm-period approach identify weather-driven incidents in different | E03：证据链分别收束 |
| 110 | 111 | 文字变化 | The results reported in Sections 4.1 to 4.3 use the final combined sample, which pools the developme | E01/E02：样本来源和推断等级 |
| 111 | 112 | 文字变化 | For the exposure margin, the linear gust term changes sign between the two separately estimated samp | E02新增：0.066是重叠CV汇总而非单次拟合，撤回不成立的独立加权区间 |
| 112 | 113 | 文字变化 | Figure 10 compares the quadratic gust coefficient across four settings: the development sample, the  | E02：参照系差异与点估计/SE分开 |
| 114 | 116 | 文字变化 | The confirmation sample covers six months within a single autumn and winter period, rather than a fu | E01/E02：不以同号显著证明完整响应相同 |
| 115 | 117 | 文字变化 | Standard errors clustered by both Local Authority District and date, rather than by district alone,  | M05/E01/A11：正确描述SE与旧数据复核 |
| 117 | 119 | 文字变化 | The two central findings of this paper concern the shape of the gust-outage relationship and the wei | M04/M05/E01：结论统一 |
| 118 | 120 | 文字变化 | The second finding, reported in Sections 4.2 and 4.3, is that gust's weight relative to affected cus | E03/E04：结论比较范围 |
| 120 | 122 | 文字变化 | Section 4.1 reports that affected customers, once the number of restoration stages per incident is t | E05：不从关联推断调度机制 |
| 121 | 123 | 文字变化 | Several limitations affect how far these results can be generalised. The temporal holdout used in Se | E01/A02/A03/E05：集中实际限制 |
| 123 | 125 | 文字变化 | The approach used in this paper, reconstructing event-level outcome measures from stage-level regula | E01/E03：最终不再重复独立确认声明 |
| 136 | 139 | 文字变化 | [12] Office of Gas and Electricity Markets. RIIO-ED2 regulatory instructions and guidance: Annex F - | 已审阅，保留用户修订；数值/结构按相应问题限定 |

### 附录

| 用户稿块 | 原Word最近对应块 | 类型 | 用户稿定位片段 | 审查处置 |
|---|---|---|---|---|
| 2 | 2 | 文字变化 | Affected customers ($C_i$) and restoration duration ($D_i$) follow Equations 1 and 2 in Section 2.2. | A08/测量：区分定义、边界、实际预测器 |
| 6 | 6 | 表格/公式及文字变化 |  /  Category  /  Original codes  /   / --- / --- /   /  Weather-related  /  01, 02, 03, 04, 05, 06, 07, 10, 18, 21,  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 11 | 11 | 表格/公式及文字变化 |  /  Variable  /  Source  /  Computation  /  Granularity  /   / --- / --- / --- / --- /   /  Log population  /  ONS populatio | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 24 | 25 | 文字变化 | A sample of 500 incidents (250 drawn from incidents with a single restoration stage and 250 from inc | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 32 | 34 | 表格/公式及文字变化 |  /  Term  /  Six categories (n = 116,064)  /  Main specification (n = 59,834)  /   / --- / --- / --- /   /  Linear ter | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 37 | 40 | 文字变化 | Restoration stages per incident, denoted $n_{stages}$, range from a single stage to several hundred. | A07/A08：D1-D6并非全为开发样本，FigureD1使用最终样本 |
| 39 | 42 | 表格/公式及文字变化 |  /  Stages  /  n  /  Share  /   / --- / --- / --- /   /  1  /  28,328  /  59.2%  /   /  2  /  7,563  /  15.8%  /   /  3–4  /  6,361  /  13 | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 50 | 54 | 文字变化 | Table D2 reports the coefficients on affected customers in the recovery model, with and without a co | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 52 | 56 | 表格/公式及文字变化 |  /  Term  /  Without control  /  With control for log(stages)  /   / --- / --- / --- /   /  Linear term  /  +0.307 (p <  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 55 | 59 | 文字变化 | The rising portion of the uncontrolled relationship between affected customers and restoration durat | E05：保留用户正确修正并移除首尾强因果残留 |
| 57 | 61 | 文字变化 | This section uses the weather-attributed subsample drawn from the final combined sample, as examined | A07：最终全样本40.5%，原40.7不沿用 |
| 62 | 67 | 表格/公式及文字变化 |  /  Stage  /  Contaminated sample  /  Corrected sample  /  Removed  /  Share removed  /   / --- / --- / --- / --- / --- /   /  | E01：避免clean全量被解读成独立 |
| 67 | 72 | 表格/公式及文字变化 |  /  Sample  /  n  /  Point estimate (m/s)  /  Coefficient of variation across folds  /  Bootstrap interval cro | E01：清除误导“clean”独立语义 |
| 72 | 78 | 表格/公式及文字变化 |  /  Term  /  Coefficient  /  SE (LAD)  /  p (LAD)  /  SE (two-way)  /  p (two-way)  /   / --- / --- / --- / --- / --- / --- /   /  | A10：26项具体含义未核实，不虚称26个FE |
| 74 | 80 | 表格/公式及文字变化 |  /  Term  /  Coefficient  /  SE (LAD)  /  p (LAD)  /  SE (two-way)  /  p (two-way)  /   / --- / --- / --- / --- / --- / --- /   /  | A08/A10：系数实际变量 |
| 75 | 81 | 文字变化 | Standard errors are generally wider under two-way clustering than under single clustering. The quadr | A11/E01：尾句同步 |
| 77 | 38 | 文字变化 | Section 4.3 reports that gust's marginal contribution to the exposure margin becomes negative within | E04：原因编码分布不是编码决策因果识别 |
| 78 | 69 | 新增/结构变化 | Incidents in the final combined sample were grouped into ten equally sized bins by gust speed, and t | E04：无条件分箱不是otherwise similar控制比较 |
| 79 | 60 | 文字变化 | **Table G1.** Share of incidents assigned to the weather-related Cause Code category, by gust decile | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 80 | 54 | 新增/结构变化 |  /  Gust decile  /  Share weather-related  /   / --- / --- /   /  Lowest  /  6.89%  /   /  2nd  /  8.07%  /   /  3rd  /  9.55%  /  | 已审阅，保留用户修订；数值/结构按相应问题限定 |
| 81 | 61 | 新增/结构变化 | An incident occurring in calm weather is therefore markedly less likely to be classified as weather- | E04/A10：纠正G段条件概率分母颠倒，并限定机制 |

## 用户稿到交付稿的逐块修复索引

| 文件 | 用户稿块 | 修复依据与处置 |
|---|---|---|
| 正文 | 1 | M01-M05/E01-E04：摘要同步收窄最低点、验证和贡献结论 |
| 正文 | 3 | M04：关键词不再暗示已识别物理临界风速 |
| 正文 | 6 | M04：工程动机与当前证据匹配 |
| 正文 | 7 | M04：取消将所有易损性函数视为分段阈值函数的概括 |
| 正文 | 8 | M04：明确研究对象差异 |
| 正文 | 9 | M04/E04：改为可被本文回答的研究问题，避免未经充分核实的排他性文献缺口 |
| 正文 | 10 | M04：衔接研究问题 |
| 正文 | 11 | E01/E03/M04：引言同步最终证据等级 |
| 正文 | 12 | E01/E03：章节说明不再声称独立确认全部结果 |
| 正文 | 21 | M04/A02：纠正总跨度与监管客户分钟损失的混同 |
| 正文 | 32 | E05：分布双峰的机制不由现有分层分析直接证明 |
| 正文 | 36 | E05/证据口径：原相关性段n与恢复样本不一致且本地报告未给可核验配对样本，暂不保留未对齐统计量 |
| 正文 | 38 | E01/E04/A03-A04：分类依据和组成检验边界 |
| 正文 | 40 | A08：实际客户数预测器变换 |
| 正文 | 44 | M02/A01：模型选择依据 |
| 正文 | 46 | M02：明确拟合对数响应及截距 |
| 正文 | 47 | M02/A01：修正用户稿“正链接函数导数不变号”的新错误 |
| 正文 | 48 | A01：删除唯一/最简阈值模型的残留论据，限定OLS解释 |
| 正文 | 49 | A10：移除悬空诊断附录，保留已报告替代模型检查但不声称已展示完整证据 |
| 正文 | 50 | E01：验证标题与实际历史一致 |
| 正文 | 51 | E01：严格保留先验分样本和事后分析的区别 |
| 正文 | 52 | E01：纳入#9-14全部六个分析步骤，删除“仅一处例外”“未查看” |
| 正文 | 53 | E01/A09：时间轴重新标记用途与月份精度 |
| 正文 | 54 | E01/E02：CV样本口径与选择层面的独立性 |
| 正文 | 55 | E01/E02：精简正确数字历史 |
| 正文 | 57 | M05/E02/A08：复现实际标准化与客户数log1p一二次项 |
| 正文 | 60 | M03：明确完整模型截距与交互项 |
| 正文 | 61 | M03/A08：符号定义和实际模型一致 |
| 正文 | 62 | A02：expη无减1和无smearing均需明示；不导入报告“真实均值10.5倍”断言 |
| 正文 | 63 | A08：表2与公式映射 |
| 正文 | 64 | A08：表2原来把FE和X混同，改宽标题 |
| 正文 | 65 | A08：表2实际客户数变量 |
| 正文 | 66 | M05：聚类仅改变推断，不产生新系数或独立证据 |
| 正文 | 68 | M04：结果标题 |
| 正文 | 69 | E01/E03：段落定位 |
| 正文 | 70 | M02/M04/E01：删去残留线性显著性判据与独立验证 |
| 正文 | 73 | M02/M03：线性项只表示参考点局部斜率 |
| 正文 | 74 | M03：条件化最低点 |
| 正文 | 77 | M03：使用完整精度本地核查数值 |
| 正文 | 78 | M01：保留用户已有效完成的对称性修正 |
| 正文 | 79 | M05：撤回分母近零机制和未验证物理CI，新增可核实诊断 |
| 正文 | 80 | M02/M03：恢复最低点不因线性不显著而消失 |
| 正文 | 81 | M01/A02：区分对数二次函数和指数显示尺度 |
| 正文 | 82 | M05/A02：图中移除未核实CI并纠正纵轴语义 |
| 正文 | 83 | E05：去除不变号和排除中介的残留断言 |
| 正文 | 84 | M04：与摘要结论一致 |
| 正文 | 86 | E04：解释贡献在对数尺度且不等同作用强度 |
| 正文 | 87 | E04/A06：确定图5比值、添加顺序、预测与因果边界 |
| 正文 | 88 | A08/E02/E04：图5方法与口径 |
| 正文 | 89 | A02/A10：地图预测量与相关对象，删除悬空引用 |
| 正文 | 90 | A02：地图图注解释expη |
| 正文 | 91 | A05/A02：50点网格极值、客户数+1，拒绝本地报告倒置端点比值 |
| 正文 | 92 | A02/A05：图7精确定义 |
| 正文 | 93 | E04/A02：限定场景比值解释 |
| 正文 | 94 | E04：不把恢复模型比较扩展到全部outcomes |
| 正文 | 96 | E03/E04/A03：取消独立于结果归因的假设 |
| 正文 | 97 | E04：不把R2增量翻倍理解为物理作用翻倍 |
| 正文 | 101 | E04/A10：使用已有选择分布证据但不声称因果机制已确定 |
| 正文 | 102 | E03：消除第二独立验证的残留说法 |
| 正文 | 104 | E03：图9明确样本内描述 |
| 正文 | 106 | E03/E04：去除整体低R2必然导致风暴低拟合的推断 |
| 正文 | 107 | E03：重复段落内容已纳入风暴开头和图注 |
| 正文 | 108 | E03：证据链分别收束 |
| 正文 | 109 | E01：标题去独立确认 |
| 正文 | 110 | E01/E02：样本来源和推断等级 |
| 正文 | 111 | E02新增：0.066是重叠CV汇总而非单次拟合，撤回不成立的独立加权区间 |
| 正文 | 112 | E02：参照系差异与点估计/SE分开 |
| 正文 | 113 | E02：去掉开发CV的伪独立区间并说明剩余图线 |
| 正文 | 114 | E01/E02：不以同号显著证明完整响应相同 |
| 正文 | 115 | M05/E01/A11：正确描述SE与旧数据复核 |
| 正文 | 117 | M04/M05/E01：结论统一 |
| 正文 | 118 | E03/E04：结论比较范围 |
| 正文 | 119 | M04：删除结论中的急剧上升、操作参考阈值残留 |
| 正文 | 120 | E05：不从关联推断调度机制 |
| 正文 | 121 | E01/A02/A03/E05：集中实际限制 |
| 正文 | 122 | 第3类：准确列待增补分析而不声称完成 |
| 正文 | 123 | E01/E03：最终不再重复独立确认声明 |
| 附录 | 2 | A08/测量：区分定义、边界、实际预测器 |
| 附录 | 7 | A03：不能说官方映射不需要验证 |
| 附录 | 22 | E01/E05：历史选择不是独立证据、不保留未展示counterfactual强断言 |
| 附录 | 26 | 测量边界：空集求和是0，NaN是操作规则 |
| 附录 | 28 | E05：分布均匀不能证明不是缺失 |
| 附录 | 30 | E01/A10：不声称完整系数表已提供 |
| 附录 | 33 | E04：样本构成证据边界 |
| 附录 | 35 | E05：不再说接近独立或指向已暂撤的统计量 |
| 附录 | 37 | A07/A08：D1-D6并非全为开发样本，FigureD1使用最终样本 |
| 附录 | 38 | A07：表D1保留真实开发样本，最终分布另报 |
| 附录 | 43 | E05：避免分箱均值证明连续单调性 |
| 附录 | 45 | E05：构成机制收窄 |
| 附录 | 46 | A07：样本和分箱变化解释清楚 |
| 附录 | 47 | E05：小样本伪影只能可能，不是已验证原因 |
| 附录 | 51 | A08：实际预测器和样本 |
| 附录 | 53 | E05：不从一次项转负证明全域单调 |
| 附录 | 55 | E05：保留用户正确修正并移除首尾强因果残留 |
| 附录 | 57 | A07：最终全样本40.5%，原40.7不沿用 |
| 附录 | 58 | E05：开放问题不强称所有系数稳定 |
| 附录 | 59 | E01：附录标题与真实历史 |
| 附录 | 60 | E01：完整六步骤历史，删除事后排除所有决策错误 |
| 附录 | 61 | E01：表格是移出早期样本，不是从研究中删除 |
| 附录 | 62 | E01：避免clean全量被解读成独立 |
| 附录 | 63 | E01：最终合并重算不是独立复核 |
| 附录 | 64 | E01：起始天气不等于恢复标签可提前得知 |
| 附录 | 65 | M03/E01：跨样本参照压力可能不同 |
| 附录 | 66 | M04：最低点不是critical |
| 附录 | 67 | E01：清除误导“clean”独立语义 |
| 附录 | 68 | E01/M05：历史区间状态不当物理CI |
| 附录 | 70 | A08/A10：所给表并不包含26项FE完整系数，明确省略 |
| 附录 | 71 | A10：完整性表述 |
| 附录 | 73 | A08/A10：样本与完整性 |
| 附录 | 72 | A10：26项具体含义未核实，不虚称26个FE |
| 附录 | 74 | A08/A10：系数实际变量 |
| 附录 | 75 | A11/E01：尾句同步 |
| 附录 | 77 | E04：原因编码分布不是编码决策因果识别 |
| 附录 | 78 | E04：无条件分箱不是otherwise similar控制比较 |
| 附录 | 81 | E04/A10：纠正G段条件概率分母颠倒，并限定机制 |

新增附录H汇集已提供的确定性核实信息，并单独限定尚未完成的计算。已完成正文22页、附录13页的渲染与逐页版面检查，复核公式、图注、表头和跨页；修正公式1集合排除符号的渲染问题、公式编号间距和附录H均值上横线，保留可编辑Word公式。正文4条、附录3条批注锚点均已核对。

本轮逐块修复索引共115项（正文77项、附录38项）；原Word→用户稿的归一化文字差异定位记录共89项（正文68项、附录21项）。这些是段落/表格块计数，不是89个或115个彼此独立的学术错误。
