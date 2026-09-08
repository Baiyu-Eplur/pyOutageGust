# R05 章节与段落候选修改（未写入Word）

本文件是审阅候选，按已核实B1证据收窄论断；不是完成W或论文可投稿。当前五章保持原状。建议将讨论独立为第5章、结论为第6章；如作者保留五章，将讨论职责安排在结论前独立小节。两种选择不改变证据边界。

研究主线：阶段记录→可解释的事件后果→条件阵风关系→阵风/客户事后信息增量→样本、时间、来源与工程适用范围。RQ1回答条件形状及支持范围；RQ2回答固定组内配对增量；RQ3作为建议明确提出适用范围，当前只给回顾性敏感性，完整过程评价与工程误差待V。

数字语义审查：182单元格+64段落绑定逐值对账，A-T10有10处沿用“six-group membership”目标标签但数值已经是主样本decile，现仅修正R05派生标签。950槽位保持独立：包括文献年、公式号、历史和整句处置，绝不等于950个科学主张关闭。11处组合段落全部给完整候选。图像OCR和全部公式对象不在950槽位范围，W仍需最终Word检查。

章节职责：摘要先更新n/最低点/回顾性边界；引言不预设U形与稳健排序；数据按单位→C/D→时间代理→天气/区域→共识与样本；方法区分目标/块/训练内尺度/OOF/物理参照/推断；结果依次形状、贡献、窗口、分期；讨论解释事后信息与观测记录局限；结论只回答已得到的条件点结果。图6/7继续保留，迁至附录仅是建议。

附录A字典与来源；B两个记录比较；C六原因合并总体；D中性阶段组成；E真实历史；F协方差与残差；G支持描述及正增量；H条件点/旧Bootstrap/物理分期/回变换。


## A-P011 → 2 Data / Appendix A regional definitions

旧段：Moran’s I, as used in this paper, is a published statistic describing the spatial clustering of income deprivation across neighbouring districts. It is not a spatial autocorrelation term computed on outage outcomes, and the two should not be conflated. Income deprivation rate, the deprivation gap, and Moran’s I are all drawn from the same underlying deprivation dataset and are moderately to highly correlated with one another at the district level, as would be expected of related measures of the same underlying construct.

前邻：Table A2. Regional covariate sources.

后邻：A.4 Geographic boundaries

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：contracts/WEATHER_AND_REGIONAL_SOURCES.md; R05/tables/SOURCE_DEPENDENCIES.csv; R05/checks/regional_workbook_extract.json；行键：当前对应总体/目标。

候选英文：

The income-deprivation covariates describe conditions within LADs. The published rate aggregates LSOA income-deprivation rates with population weights; the gap is the highest minus the lowest LSOA rate within the LAD, and Moran’s I describes within-LAD LSOA spatial clustering. Rate and gap enter the design on a proportion scale. Buckinghamshire currently carries explicitly labelled historical proxies formed from simple averages across its four former districts. These proxies are retained pending the author-requested LSOA reconstruction and comparison. A link between LAD21 and LAD23 codes does not by itself establish boundary equivalence.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P013 → Appendix A geography

旧段：Local Authority District boundaries follow the December 2021 generalised boundary product published by the Office for National Statistics, in the British National Grid coordinate system (EPSG:27700). All geographic figures in this paper are projected to this coordinate system.

前邻：A.4 Geographic boundaries

后邻：A.5 Open items in the data dictionary

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/frozen/GEOMETRY_MANIFEST.json; R05/tables/SOURCE_DEPENDENCIES.csv；行键：当前对应总体/目标。

候选英文：

The regional reference map uses copied December 2021 LAD geometry in British National Grid coordinates. The incident-location panel instead displays longitude and latitude. Code linkage to later regional tables is retained as a compatibility mapping; equivalence of all relevant boundaries remains a separate source check.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P017 → Appendix B title

旧段：B.1 Comparison against the earliest-stage convention

前邻：Appendix B. Data reconstruction: full evidence chain

后邻：Within the final analysis sample (n = 60,437), the mean of affected customers computed by aggregating across stages, following Equation 1, is 93.02. The mean computed using only the customer count reported in the earliest stage of each incident, the convention used when an incident is treated as equivalent to its first recorded stage, is 47.13. The two figures differ by a factor of 1.97 within the same sample.

段落职责/处理理由：标题消歧，无需称真实初始。

证据：R05/CUSTOMER_COMPARATOR_AUDIT.md；行键：当前对应总体/目标。

候选英文：

B.1 Aggregated customers compared with minimum-stage and earliest-time records

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P018 → 2 Data / Appendix B comparison

旧段：Within the final analysis sample (n = 60,437), the mean of affected customers computed by aggregating across stages, following Equation 1, is 93.02. The mean computed using only the customer count reported in the earliest stage of each incident, the convention used when an incident is treated as equivalent to its first recorded stage, is 47.13. The two figures differ by a factor of 1.97 within the same sample.

前邻：B.1 Comparison against the earliest-stage convention

后邻：B.2 Choice of restoration duration measure

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/CUSTOMER_COMPARATOR_SUMMARY.csv; R05/tables/CUSTOMER_SELECTION_CHECKS.csv；行键：当前对应总体/目标。

候选英文：

Within the common main sample of 60,436 incidents, mean aggregated affected customers are 93.0257. Selecting the record with the minimum available numeric stage number gives a mean of 47.1283 and a ratio of means of 1.9739. Selecting the earliest valid recorded start time, breaking ties by persistent source-row order, gives a mean of 31.1220 and a ratio of 2.9891. All three measures are observed for this common sample. The minimum available stage number exceeds one for 8,817 incidents (14.589%). There are no minimum-stage ties in this sample, but 15,249 incidents have earliest-time ties and 13,266 have differing customer counts among those tied records. These deterministic record comparators are not verified true initial customer counts; the ratios are ratios of sample means, not means of event-level ratios.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P027 → Appendix B record completeness

旧段：For 14,264 of the 135,025 reconstructed incidents (10.56 percent), the lowest recorded stage number is at least 2. This pattern is spread through the study period rather than concentrated at its boundaries. That distribution alone cannot determine whether stage numbering conventions or incomplete records explain the pattern. These incidents were retained without adjustment. A comparison excluding them has not been completed and remains a sensitivity check.

前邻：B.5 Incidents with an apparently missing first stage

后邻：Appendix C. Sample restriction: full six-category comparison

段落职责/处理理由：11处组合段落之一；删除时间分布推断，当前核查未提供分期频数。

证据：R05/tables/CUSTOMER_SELECTION_CHECKS.csv；行键：当前对应总体/目标。

候选英文：

Across the reconstructed event master, the minimum available numeric stage number exceeds one for 14,264 of 135,025 incidents (10.564%). The corresponding figures are 8,817 of 60,436 in the main sample (14.589%) and 2,593 of 9,857 in the weather-attributed sample (26.306%). These counts identify a record-number pattern; they cannot distinguish numbering conventions from incomplete stage coverage. The incidents remain included under the frozen event definition. Sensitivity to excluding or separately characterising them is retained for the stage-quality validation protocol.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P028 → Appendix C title

旧段：Appendix C. Sample restriction: full six-category comparison

前邻：For 14,264 of the 135,025 reconstructed incidents (10.56 percent), the lowest recorded stage number is at least 2. This pattern is spread through the study period rather than concentrated at its boundaries. That distribution alone cannot determine whether stage numbering conventions or incomplete records explain the pattern. These incidents were retained without adjustment. A comparison excluding them has not been completed and remains a sensitivity check.

后邻：Appendix F reports the non-calendar coefficient sets for the two-category combined-sample models. A corresponding full six-category coefficient table was not saved in the available project outputs. Table C1 therefore reports only the five-fold gust summaries actually available for the six-category and two-category recovery samples. This is a retrospective sample-sensitivity comparison.

段落职责/处理理由：合并六组不等于分别拟合六个模型。

证据：R04/tables/AppendixC_fold_summary.csv；行键：当前对应总体/目标。

候选英文：

Appendix C. Retrospective sensitivity in a pooled six-category population

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P029 → 2 Data / Appendix C sample sensitivity

旧段：Appendix F reports the non-calendar coefficient sets for the two-category combined-sample models. A corresponding full six-category coefficient table was not saved in the available project outputs. Table C1 therefore reports only the five-fold gust summaries actually available for the six-category and two-category recovery samples. This is a retrospective sample-sensitivity comparison.

前邻：Appendix C. Sample restriction: full six-category comparison

后邻：Table C1. Gust coefficients, six-category sample versus the two-category main specification.

段落职责/处理理由：当前完整六组合并系数可取档案；旧116064/59834及5/0显著折数不沿用。

证据：R04/tables/AppendixC_fold_summary.csv; R04/supplements_v1/six_group_*.json；行键：当前对应总体/目标。

候选英文：

The six analytical cause groups form an implemented code grouping, whose official documentary semantics remain incompletely established. The current sensitivity analysis fits one pooled six-group recovery population of 117,108 incidents and compares it with the 60,436-incident main population. Across the five overlapping training folds, mean quadratic gust coefficients are 0.07806 and 0.08350, respectively; all are positive and nominally significant under the stated normal-reference LAD calculation. Mean linear coefficients are 0.01892 and −0.00555, with three and one nominally significant folds. These summaries indicate sensitivity to sample composition. They are not six independently fitted cause-specific models, independent replications, or evidence that one group’s association is physical and another’s is not.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P031 → 2 Data / Appendix C sample sensitivity

旧段：Restricting the sample retains positive quadratic terms of the same broad order, significant in all five folds, while the linear term becomes small and non-significant in those folds. The comparison demonstrates dependence on sample definition; it does not establish why the coefficients differ or verify the underlying code classifications.

前邻：Table C1. Gust coefficients, six-category sample versus the two-category main specification.

后邻：Appendix D. The apparent non-monotonic relationship between affected customers and restoration duration

段落职责/处理理由：当前完整六组合并系数可取档案；旧116064/59834及5/0显著折数不沿用。

证据：R04/tables/AppendixC_fold_summary.csv; R04/supplements_v1/six_group_*.json；行键：当前对应总体/目标。

候选英文：

The six analytical cause groups form an implemented code grouping, whose official documentary semantics remain incompletely established. The current sensitivity analysis fits one pooled six-group recovery population of 117,108 incidents and compares it with the 60,436-incident main population. Across the five overlapping training folds, mean quadratic gust coefficients are 0.07806 and 0.08350, respectively; all are positive and nominally significant under the stated normal-reference LAD calculation. Mean linear coefficients are 0.01892 and −0.00555, with three and one nominally significant folds. These summaries indicate sensitivity to sample composition. They are not six independently fitted cause-specific models, independent replications, or evidence that one group’s association is physical and another’s is not.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P032 → Appendix D title

旧段：Appendix D. The apparent non-monotonic relationship between affected customers and restoration duration

前邻：Restricting the sample retains positive quadratic terms of the same broad order, significant in all five folds, while the linear term becomes small and non-significant in those folds. The comparison demonstrates dependence on sample definition; it does not establish why the coefficients differ or verify the underlying code classifications.

后邻：This appendix examines how the observed customer–duration association changes when incidents are grouped by restoration-stage count and when a stage-count control is added. Linear or rank correlations close to zero would not establish independence. The analyses below distinguish descriptive composition patterns from causal explanations.

段落职责/处理理由：删除当前pooled图不支持的apparent non-monotonic预设。

证据：R05/release_v1/figures/figureD1.png；行键：当前对应总体/目标。

候选英文：

Restoration-stage composition and the customer–span association

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P035 → Appendix D populations

旧段：Restoration-stage counts, denoted nstages, range from one to several hundred. Table D1 and the original within-subset summaries in Sections D.2–D.3, together with Table D2, use the earlier-period recovery sample (n = 47,840). Figure D1 in Section D.4 instead uses the final combined recovery sample (n = 59,834). In that final sample, stage groups 1, 2, 3–4 and at least 5 contain 35,599, 9,348, 7,907 and 6,980 incidents respectively. These distinct sample bases must not be combined as if they were one analysis.

前邻：D.1 Number of restoration stages

后邻：Table D1. Restoration-stage distribution in the earlier-period recovery sample (n = 47,840).

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/AppendixD_period_stage_counts.csv; R04_B1_all_valid_v1/*/stage_manifest.json；行键：当前对应总体/目标。

候选英文：

Current full-period main stage groups contain 35,998 one-stage incidents, 9,429 two-stage incidents, 7,972 with three to four rows, and 7,037 with at least five rows, totalling 60,436. Figure D1 uses a common set of numeric customer-bin edges within each population, with separate edges for main and weather populations. Current earlier-period summaries are separately labelled. The historical development tables used different eligibility and tail rules; they are preserved as history and should not be silently combined with current full-period results.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P036 → Appendix D Table D1 caption

旧段：Table D1. Restoration-stage distribution in the earlier-period recovery sample (n = 47,840).

前邻：Restoration-stage counts, denoted nstages, range from one to several hundred. Table D1 and the original within-subset summaries in Sections D.2–D.3, together with Table D2, use the earlier-period recovery sample (n = 47,840). Figure D1 in Section D.4 instead uses the final combined recovery sample (n = 59,834). In that final sample, stage groups 1, 2, 3–4 and at least 5 contain 35,599, 9,348, 7,907 and 6,980 incidents respectively. These distinct sample bases must not be combined as if they were one analysis.

后邻：D.2 Relationship within incidents with a single stage

段落职责/处理理由：建议替代整表，作者仍可保留旧表为显式历史。

证据：R04/tables/AppendixD_period_stage_counts.csv；行键：当前对应总体/目标。

候选英文：

Table D1. Current restoration-stage distribution by explicitly labelled population and period. Main full-period n = 60,436; main earlier-period n = 48,323. The previous n = 47,840 table is retained in the historical ledger and is not the population of the current full-period figure.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P041 → Appendix D title

旧段：D.4 Source of the apparent non-monotonic pattern in the pooled sample

前邻：In the earlier-period investigation, the grouped customer–duration relationship was also reported as decreasing within multi-stage subsets, using bins defined separately within each subset. Such grouped summaries should not be read as proof that the fitted derivative is negative at every customer value. Section D.4 uses a common binning and the larger combined sample, which exposes differences in support across stage strata.

后邻：Without stage stratification, mean duration rises and then falls across customer bins. The mix of stage counts also changes across those bins: multi-stage incidents tend to involve more customers and longer spans. This supports a descriptive composition account of the pooled pattern, but does not prove that stage count is its sole cause or that a direct customer-scale effect is absent.

段落职责/处理理由：删除当前pooled图不支持的apparent non-monotonic预设。

证据：R05/release_v1/figures/figureD1.png；行键：当前对应总体/目标。

候选英文：

Restoration-stage composition and the customer–span association

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P042 → Appendix D / current pooled pattern

旧段：Without stage stratification, mean duration rises and then falls across customer bins. The mix of stage counts also changes across those bins: multi-stage incidents tend to involve more customers and longer spans. This supports a descriptive composition account of the pooled pattern, but does not prove that stage count is its sole cause or that a direct customer-scale effect is absent.

前邻：D.4 Source of the apparent non-monotonic pattern in the pooled sample

后邻：Figure D1 applies common affected-customer quartile bins from the final combined recovery sample (n = 59,834) to every stage stratum. These bins differ from the subset-specific bins used in the earlier-period summaries in Sections D.2 and D.3. Panel (a) shows stratum-specific means and panel (b) the pooled means, using the same combined-sample bin boundaries.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/main_R0c/stage_pooled.csv; weather_R0c/stage_pooled.csv; stage_composition.csv; R05/release_v1/figures/figureD1.png；行键：当前对应总体/目标。

候选英文：

With all valid main-sample spans retained, pooled mean durations across ascending customer bins are 21.4514, 17.6394, 15.8462 and 11.7081 hours. The weather-population values are 28.0381, 19.1823, 12.8393 and 12.1986 hours under its own bin edges. Both pooled sequences decrease, so the former rise-then-fall account is not a description of the current figure. Stage-stratified curves differ, including a non-monotone five-or-more-row pattern and sparse cells. These associations remain sensitive to record composition and tail inclusion; they do not identify repair prioritisation or prove that stage count is the sole source of a pooled pattern.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P043 → Appendix D populations

旧段：Figure D1 applies common affected-customer quartile bins from the final combined recovery sample (n = 59,834) to every stage stratum. These bins differ from the subset-specific bins used in the earlier-period summaries in Sections D.2 and D.3. Panel (a) shows stratum-specific means and panel (b) the pooled means, using the same combined-sample bin boundaries.

前邻：Without stage stratification, mean duration rises and then falls across customer bins. The mix of stage counts also changes across those bins: multi-stage incidents tend to involve more customers and longer spans. This supports a descriptive composition account of the pooled pattern, but does not prove that stage count is its sole cause or that a direct customer-scale effect is absent.

后邻：In Figure D1a, three of the four strata (single-stage, two-stage, and three-to-four-stage incidents) decline from the first bin onward, with the three-to-four-stage stratum showing the steepest decline, from 40.6 hours in the lowest bin to 9.4 hours in the highest. The stratum of five or more stages does not show a clean decline under this shared binning: mean duration rises from the lowest to the second bin before levelling off and then declining slightly. The lowest two bins for this stratum contain only 22 and 18 incidents respectively, because multi-stage incidents rarely fall into the lowest customer bins, and these sparse cells limit interpretation. The earlier-period, subset-specific binning in Section D.3 showed a mild decline, but it uses a different sample and cannot establish that the present rise is solely a small-sample artefact. In Figure D1b, the pooled relationship rises from 11.65 hours in the lowest bin to a peak of 14.19 hours in the second bin, before declining to 9.87 hours in the highest bin. No stratum in Figure D1a shows a comparable rise over the same two bins, other than the small-sample pattern noted above.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/AppendixD_period_stage_counts.csv; R04_B1_all_valid_v1/*/stage_manifest.json；行键：当前对应总体/目标。

候选英文：

Current full-period main stage groups contain 35,998 one-stage incidents, 9,429 two-stage incidents, 7,972 with three to four rows, and 7,037 with at least five rows, totalling 60,436. Figure D1 uses a common set of numeric customer-bin edges within each population, with separate edges for main and weather populations. Current earlier-period summaries are separately labelled. The historical development tables used different eligibility and tail rules; they are preserved as history and should not be silently combined with current full-period results.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P044 → Appendix D / current pooled pattern

旧段：In Figure D1a, three of the four strata (single-stage, two-stage, and three-to-four-stage incidents) decline from the first bin onward, with the three-to-four-stage stratum showing the steepest decline, from 40.6 hours in the lowest bin to 9.4 hours in the highest. The stratum of five or more stages does not show a clean decline under this shared binning: mean duration rises from the lowest to the second bin before levelling off and then declining slightly. The lowest two bins for this stratum contain only 22 and 18 incidents respectively, because multi-stage incidents rarely fall into the lowest customer bins, and these sparse cells limit interpretation. The earlier-period, subset-specific binning in Section D.3 showed a mild decline, but it uses a different sample and cannot establish that the present rise is solely a small-sample artefact. In Figure D1b, the pooled relationship rises from 11.65 hours in the lowest bin to a peak of 14.19 hours in the second bin, before declining to 9.87 hours in the highest bin. No stratum in Figure D1a shows a comparable rise over the same two bins, other than the small-sample pattern noted above.

前邻：Figure D1 applies common affected-customer quartile bins from the final combined recovery sample (n = 59,834) to every stage stratum. These bins differ from the subset-specific bins used in the earlier-period summaries in Sections D.2 and D.3. Panel (a) shows stratum-specific means and panel (b) the pooled means, using the same combined-sample bin boundaries.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/main_R0c/stage_pooled.csv; weather_R0c/stage_pooled.csv; stage_composition.csv; R05/release_v1/figures/figureD1.png；行键：当前对应总体/目标。

候选英文：

With all valid main-sample spans retained, pooled mean durations across ascending customer bins are 21.4514, 17.6394, 15.8462 and 11.7081 hours. The weather-population values are 28.0381, 19.1823, 12.8393 and 12.1986 hours under its own bin edges. Both pooled sequences decrease, so the former rise-then-fall account is not a description of the current figure. Stage-stratified curves differ, including a non-monotone five-or-more-row pattern and sparse cells. These associations remain sensitive to record composition and tail inclusion; they do not identify repair prioritisation or prove that stage count is the sole source of a pooled pattern.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P046 → Appendix D Figure D1 caption

旧段：Figure D1. Mean restoration duration by affected-customers quartile bin (computed on the full sample). (a) By number of restoration stages. (b) Pooled across all incidents, without separating by stage count.

前邻：

后邻：D.5 Regression evidence

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figureD1.png; R04_B1_all_valid_v1/*/stage_manifest.json；行键：当前对应总体/目标。

候选英文：

Figure D1. Mean recorded restoration span by ascending numeric customer bins, separately for the main and weather-attributed populations. Left panels stratify by stage-row count; right panels pool the same population. Bin edges are shared across strata within a population and differ between populations. All valid spans are retained. Connecting means does not establish a continuous derivative or a causal composition mechanism.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P048 → 4.1 / Appendix D stage-control sensitivity

旧段：Table D2 reports the coefficients on affected customers in the recovery model, with and without a control for the logarithm of the number of restoration stages, estimated on the development sample described in Section D.1 (n = 47,840). These coefficients differ from the corresponding uncontrolled coefficients reported for the final combined sample in Table F2 (n = 59,834, affected customers coefficients of 0.339 and -0.396), because the two tables use different samples under an otherwise identical specification, not because of any difference in method.

前邻：D.5 Regression evidence

后邻：Table D2. Coefficients on standardised log(1 + affected customers) and its square, with and without log(stage count), earlier-period recovery sample (n = 47,840).

段落职责/处理理由：建议现有全期对应物替代旧开发表，不自动重跑旧47840人口；精确系数见所附原始小表。

证据：R04_B1_all_valid_v1/main_R0c/step27 outputs; R04_B1_all_valid_v1/weather_R0c/step27 outputs；行键：当前对应总体/目标。

候选英文：

The current full-period stage-control fits are presented as counterparts to the historical development-sample analyses, with main and weather populations labelled separately. Adding log(stage-row count) changes the conditional customer coefficients, but stage-row count is an eventual record characteristic rather than an established pre-event confounder. A linear coefficient alone does not determine the derivative throughout the log-customer range. These comparisons describe sensitivity to conditioning and do not identify crew prioritisation, mediation or a unique compositional mechanism. The full current coefficient tables should replace whole historical tables only with explicit relabelling of the population.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P049 → Appendix D Table D2 caption

旧段：Table D2. Coefficients on standardised log(1 + affected customers) and its square, with and without log(stage count), earlier-period recovery sample (n = 47,840).

前邻：Table D2 reports the coefficients on affected customers in the recovery model, with and without a control for the logarithm of the number of restoration stages, estimated on the development sample described in Section D.1 (n = 47,840). These coefficients differ from the corresponding uncontrolled coefficients reported for the final combined sample in Table F2 (n = 59,834, affected customers coefficients of 0.339 and -0.396), because the two tables use different samples under an otherwise identical specification, not because of any difference in method.

后邻：Adding log(stage count) changes the linear customer coefficient from +0.307 to -0.236 and reduces the magnitude of the negative quadratic coefficient by approximately 21 percent. For the standardised log-customer predictor X, the fitted slope is a+2bX, so the linear coefficient alone does not establish monotonicity over its observed support. The change is consistent with sensitivity to stage composition; a full derivative-based comparison would require the relevant scaling and covariate range.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/R04_B1_all_valid_v1/main_R0c/step27_stage_coefficients.csv; R04/R04_B1_all_valid_v1/weather_R0c/step27_stage_coefficients.csv；行键：当前对应总体/目标。

候选英文：

Table D2. Current full-period recovery coefficients with and without log(stage-row count), for the same eligible population within each comparison. Main n = 60,436; weather-attributed n = 9,857. This table is a separately labelled counterpart to the archived development-sample analysis.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P050 → 4.1 / Appendix D stage-control sensitivity

旧段：Adding log(stage count) changes the linear customer coefficient from +0.307 to -0.236 and reduces the magnitude of the negative quadratic coefficient by approximately 21 percent. For the standardised log-customer predictor X, the fitted slope is a+2bX, so the linear coefficient alone does not establish monotonicity over its observed support. The change is consistent with sensitivity to stage composition; a full derivative-based comparison would require the relevant scaling and covariate range.

前邻：Table D2. Coefficients on standardised log(1 + affected customers) and its square, with and without log(stage count), earlier-period recovery sample (n = 47,840).

后邻：D.6 Interpretation

段落职责/处理理由：建议现有全期对应物替代旧开发表，不自动重跑旧47840人口；精确系数见所附原始小表。

证据：R04_B1_all_valid_v1/main_R0c/step27 outputs; R04_B1_all_valid_v1/weather_R0c/step27 outputs；行键：当前对应总体/目标。

候选英文：

The current full-period stage-control fits are presented as counterparts to the historical development-sample analyses, with main and weather populations labelled separately. Adding log(stage-row count) changes the conditional customer coefficients, but stage-row count is an eventual record characteristic rather than an established pre-event confounder. A linear coefficient alone does not determine the derivative throughout the log-customer range. These comparisons describe sensitivity to conditioning and do not identify crew prioritisation, mediation or a unique compositional mechanism. The full current coefficient tables should replace whole historical tables only with explicit relabelling of the population.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P054 → Appendix D weather sensitivity

旧段：This section describes the reported weather-attributed recovery subset from the final combined sample, rather than the earlier-period-only regression basis of Table D2. Its reported multi-stage share is 49.7 percent. For the final combined recovery sample, the stage counts given in Section D.1 imply a multi-stage share of approximately 40.5 percent. The weather-subset single-stage customer–duration pattern was reported as decreasing in grouped summaries.

前邻：D.7 The same investigation within the weather-attributed subsample

后邻：In the weather-attributed subset, the linear customer coefficient is already negative without a stage control and becomes more negative after adding it. This differs from the earlier-period main-sample sign reversal in Table D2. The findings indicate sensitivity to sample and conditioning, but do not fully identify its source. The available local audit does not provide a new full coefficient table for this subset; no additional numerical estimates are inferred here.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/AppendixD_period_stage_counts.csv; R05/release_v1/figures/figureD1.png；行键：当前对应总体/目标。

候选英文：

The current weather-attributed recovery population comprises 9,857 incidents over the full study period. Its multi-stage share is 49.6500%, compared with 40.4362% in the 60,436-incident main population. The weather and main curves use their own common bin edges and retain all valid spans. The weather pooled means decrease across these bins, while stage strata show different shapes and support. These current full-period descriptions must be distinguished from the older development-only regression table.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P055 → 4.1 / Appendix D stage-control sensitivity

旧段：In the weather-attributed subset, the linear customer coefficient is already negative without a stage control and becomes more negative after adding it. This differs from the earlier-period main-sample sign reversal in Table D2. The findings indicate sensitivity to sample and conditioning, but do not fully identify its source. The available local audit does not provide a new full coefficient table for this subset; no additional numerical estimates are inferred here.

前邻：This section describes the reported weather-attributed recovery subset from the final combined sample, rather than the earlier-period-only regression basis of Table D2. Its reported multi-stage share is 49.7 percent. For the final combined recovery sample, the stage counts given in Section D.1 imply a multi-stage share of approximately 40.5 percent. The weather-subset single-stage customer–duration pattern was reported as decreasing in grouped summaries.

后邻：Appendix E. Development history and retrospective sample separation

段落职责/处理理由：建议现有全期对应物替代旧开发表，不自动重跑旧47840人口；精确系数见所附原始小表。

证据：R04_B1_all_valid_v1/main_R0c/step27 outputs; R04_B1_all_valid_v1/weather_R0c/step27 outputs；行键：当前对应总体/目标。

候选英文：

The current full-period stage-control fits are presented as counterparts to the historical development-sample analyses, with main and weather populations labelled separately. Adding log(stage-row count) changes the conditional customer coefficients, but stage-row count is an eventual record characteristic rather than an established pre-event confounder. A linear coefficient alone does not determine the derivative throughout the log-customer range. These comparisons describe sensitivity to conditioning and do not identify crew prioritisation, mediation or a unique compositional mechanism. The full current coefficient tables should replace whole historical tables only with explicit relabelling of the population.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P064 → Appendix F title

旧段：Appendix F. Full robustness results under single and two-way clustering

前邻：The sequence is 10.69 m/s before separation, 12.13 m/s in the earlier-period exposure sample, and 10.69 m/s after recombining the final data. The repeated rounded value is not a second independent confirmation. A local audit gives the final full-precision point estimate as 10.694 m/s. The interval-crossing entries reproduce historical reports on their standardised scales; they do not provide a harmonised physical-unit confidence interval across samples. Appendix H explains the additional conversion required for the final bootstrap output.

后邻：Tables F1 and F2 report the non-calendar coefficient sets for the final combined exposure sample (n = 60,437) and recovery sample (n = 59,834), under LAD and LAD-and-date clustered standard errors. Additive year and month indicators are included in both fits but their individual coefficients are not reproduced here. Point estimates are identical under the two covariance estimators. The development-only customer coefficients in Table D2 use a different sample and are not expected to match Table F2 numerically.

段落职责/处理理由：避免标题将敏感性直接宣称full robustness。

证据：R05/COVARIANCE_AND_PERIOD_AUDIT.md; R05/release_v1/figures/figureF1.png；行键：当前对应总体/目标。

候选英文：

Appendix F. Coefficients, covariance choices and residual diagnostics

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P065 → 3 Methods / Appendix F inference

旧段：Tables F1 and F2 report the non-calendar coefficient sets for the final combined exposure sample (n = 60,437) and recovery sample (n = 59,834), under LAD and LAD-and-date clustered standard errors. Additive year and month indicators are included in both fits but their individual coefficients are not reproduced here. Point estimates are identical under the two covariance estimators. The development-only customer coefficients in Table D2 use a different sample and are not expected to match Table F2 numerically.

前邻：Appendix F. Full robustness results under single and two-way clustering

后邻：Table F1. Final combined exposure model (n = 60,437): non-calendar coefficients and clustered standard errors.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/COVARIANCE_AND_PERIOD_AUDIT.md; R04/tables/Tables3_F_complete_coefficients.csv；行键：当前对应总体/目标。

候选英文：

The reported OLS coefficients are paired with CR1 standard errors clustered by LAD. Alternative clustering by date and by both LAD and date is evaluated for the same full sample. Reported p-values use the stated normal-reference Wald calculation. Changing the covariance estimator leaves the fitted coefficients unchanged. The full main models each use 60,436 incidents. Covariance conditions are assessed separately for each period. Six matrices for clustering by both LAD and date are not positive semidefinite. The displayed standard errors of the physical terms use LAD covariance, and Figure 10 contains points only. No arbitrary joint Wald inference is authorised from those non-PSD matrices.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P066 → Appendix F Table F1 caption

旧段：Table F1. Final combined exposure model (n = 60,437): non-calendar coefficients and clustered standard errors.

前邻：Tables F1 and F2 report the non-calendar coefficient sets for the final combined exposure sample (n = 60,437) and recovery sample (n = 59,834), under LAD and LAD-and-date clustered standard errors. Additive year and month indicators are included in both fits but their individual coefficients are not reproduced here. Point estimates are identical under the two covariance estimators. The development-only customer coefficients in Table D2 use a different sample and are not expected to match Table F2 numerically.

后邻：Table F2. Final combined recovery model (n = 59,834): non-calendar coefficients and clustered standard errors.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Tables3_F_complete_coefficients.csv; main E0；行键：当前对应总体/目标。

候选英文：

Table F1. Main customer impact model with all valid tails (n = 60,436): coefficients other than calendar terms, CR1 standard errors and Wald p-values from a normal reference. The two covariance columns accompany the same point estimates.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P067 → Appendix F Table F2 caption

旧段：Table F2. Final combined recovery model (n = 59,834): non-calendar coefficients and clustered standard errors.

前邻：Table F1. Final combined exposure model (n = 60,437): non-calendar coefficients and clustered standard errors.

后邻：Both quadratic gust terms remain significant under LAD-and-date clustering. The exposure linear term and both gust-pressure interactions lose significance relative to LAD clustering, while the recovery linear term remains non-significant under both. These changes concern uncertainty around the same combined-sample coefficients. Analyses on earlier versions of overlapping records are not counted as independent corroboration.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Tables3_F_complete_coefficients.csv; main R0c；行键：当前对应总体/目标。

候选英文：

Table F2. Main recovery model with all valid tails (n = 60,436): coefficients other than calendar terms, CR1 standard errors and Wald p-values from a normal reference. Customer covariates use standardised ln(1 + C) and its square.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P068 → 4.4 / Appendix F covariance

旧段：Both quadratic gust terms remain significant under LAD-and-date clustering. The exposure linear term and both gust-pressure interactions lose significance relative to LAD clustering, while the recovery linear term remains non-significant under both. These changes concern uncertainty around the same combined-sample coefficients. Analyses on earlier versions of overlapping records are not counted as independent corroboration.

前邻：Table F2. Final combined recovery model (n = 59,834): non-calendar coefficients and clustered standard errors.

后邻：Appendix G. Cause Code assignment and gust speed

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Tables3_F_complete_coefficients.csv; R05/tables/PERIOD_COVARIANCE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

In the full main recovery model, the quadratic gust coefficient has p-values from a normal reference 1.131e-42 under LAD CR1 and 8.217e-26 under CR1 clustering by both LAD and date. The corresponding customer-impact values are 5.734e-37 and 0.0009155. The covariance table reports the same coefficients with these alternative uncertainty calculations. This result is specific to the full-period fits and should not be extended to unrestricted joint inference using the six non-PSD period two-way matrices. Neither changing covariance nor refitting overlapping data creates independent confirmation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P071 → 4.3 / Appendix G support

旧段：The supplied cause-distribution summaries group incidents by gust decile. The weather-related share rises from 6.89 percent in the lowest decile to 56.10 percent in the highest, increasing across all nine adjacent comparisons (Table G1). These are unadjusted group proportions; they do not compare otherwise identical incidents.

前邻：Appendix G describes the association between gust conditions and membership of the analytical weather-related Cause Code group. This bears on covariate support for the exposure comparison in Section 4.3; it does not identify why any particular incident received its code.

后邻：Table G1. Share of incidents assigned to the weather-related Cause Code category, by gust decile.

段落职责/处理理由：相邻G段落可合并；不要重复三次同一数字。

证据：R04/tables/AppendixG_main_gust_deciles.csv; R04/tables/AppendixG_low_gust_support.csv; R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

In the current main-population gust deciles, the weather-attributed share is 6.9338% in the lowest bin and 57.0714% in the highest. At the main customer-impact reference minimum of 10.8075 m/s, 65.0291% of main incidents and 37.8817% of weather-attributed incidents fall below the reference. These within-population proportions describe different support distributions; they do not compare otherwise identical incidents. The weather customer-impact gust increment is now positive, so these descriptions should not be offered as explanations of the superseded negative increment. Cause assignment and limited support remain relevant uncertainties for both outcomes.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P073 → 4.3 / Appendix G support

旧段：In the full combined exposure sample, 63.70 percent of incidents have gust below the fitted reference value of 10.69 m/s; the corresponding proportion within the weather-attributed exposure subset is 36.83 percent. Thus the within-subset share below that value is approximately 57.8 percent of the full-sample share. This is a comparison of two within-sample proportions, not the proportion of all low-gust incidents belonging to each group. The change documents reduced low-gust support and is consistent with a support-related explanation for the negative predictive increment. It does not establish that selection is the sole cause or that the recovery model is unaffected.

前邻：Table G1. Share of incidents assigned to the weather-related Cause Code category, by gust decile.

后邻：Appendix H. Audit of fitted minima, reference scales and displayed predictions

段落职责/处理理由：相邻G段落可合并；不要重复三次同一数字。

证据：R04/tables/AppendixG_main_gust_deciles.csv; R04/tables/AppendixG_low_gust_support.csv; R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

In the current main-population gust deciles, the weather-attributed share is 6.9338% in the lowest bin and 57.0714% in the highest. At the main customer-impact reference minimum of 10.8075 m/s, 65.0291% of main incidents and 37.8817% of weather-attributed incidents fall below the reference. These within-population proportions describe different support distributions; they do not compare otherwise identical incidents. The weather customer-impact gust increment is now positive, so these descriptions should not be offered as explanations of the superseded negative increment. Cause assignment and limited support remain relevant uncertainties for both outcomes.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P076 → 4.1 / Appendix H conditional point

旧段：The local implementation audit reproduced the final exposure coefficients at full precision: β1=−0.032325899095631154, β2=0.10276170747389514 and β3=−0.0408384359554068. The corresponding gust mean and standard deviation are 9.87229677581956 and 5.222713076874045 m/s. Table H1 evaluates G*P=−β1+β3P/2β2 and converts the point estimates to physical gust units using that fit’s scaling. These deterministic evaluations add no new model fit or independent validation.

前邻：H.1 Conditional exposure minima

后邻：Table H1. Conditional exposure fitted minima using the final combined-sample coefficients.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/AppendixH_pressure_minima.json; R05/tables/PERIOD_PHYSICAL_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

For the main customer-impact fit, the gust mean is 9.910222 m/s and the sample standard deviation is 5.279979 m/s. At the fit’s mean physical pressure the conditional minimum is 10.807545 m/s, within the declared p1–p99 gust support. At pressure one training standard deviation below and above that mean, the corresponding points are 9.647571 and 11.967520 m/s. Each point uses the fitted interaction and that model’s own scaling. These algebraic locations are not confidence intervals, physical damage thresholds or established pressure-response effects.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P081 → Appendix H historical Table H2 caption

旧段：Table H2. Diagnostics from the reproduced 500 day-bootstrap fits.

前邻：The audit deterministically reproduced 500 day-bootstrap fits using seed 20260826. Sorted standardised minima matched the archived output to a maximum difference of 5.55×10−17. Table H2 gives the reported diagnostics. A positive coefficient in every resample is a sign-stability observation; it is not evidence that every resample has a statistically significant coefficient.

后邻：The empirical ratio distribution is asymmetric, but the diagnostics do not isolate the causes of its difference from a Delta approximation. In particular, the denominator does not approach zero in the reported draws. Resample-specific scaling also changes the reference coordinates. Re-estimating scaling is not automatically more conservative: its effect depends on the joint distribution and the precise estimand.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：manuscript_record retained historical bootstrap sources；行键：当前对应总体/目标。

候选英文：

Table H2. Archived diagnostics from the historical 500 day-bootstrap fits. These are not new B1 fits and do not supply a validated current physical-unit confidence interval.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P087 → Appendix H title

旧段：H.3 Temporal scaling and development-fold summaries

前邻：The percentile interval must then be computed from the physical-unit values vb*p0. Alternatively, a minimum at each resample’s own mean pressure is a different reference convention and must be named as such. The summary supplied for this revision does not contain the complete paired pressure-scaling quantities needed to verify a common-reference interval. Accordingly, the former 9.2–12.1 m/s band is not retained as a validated physical-unit interval.

后邻：Table H3. Reported gust scaling in the separate temporal samples.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/PERIOD_PHYSICAL_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

H.3 Current period-specific physical scales and archived development summaries

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P089 → Appendix H period scales

旧段：For a quadratic coefficient estimated on standardised gust, its raw-wind curvature coefficient is β2/sv2. The small differences in SD limit, but do not eliminate, scaling effects on comparisons. These whole-period values do not supply the separate scaling of every training fold. The development recovery point in Figure 10, 0.0660, is an inverse-variance-weighted summary of overlapping cross-validation fits. The archived nominal interval of 0.0587–0.0732 is not used for inference, because treating those fits as independent would omit their covariance. A full-development-sample fit or a covariance-aware resampling procedure is needed for a directly comparable interval.

前邻：Table H3. Reported gust scaling in the separate temporal samples.

后邻：H.4 Exponentiated fitted values and retransformation

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/PERIOD_PHYSICAL_AUDIT.csv; R04/tables/AppendixH_period_scales.csv；行键：当前对应总体/目标。

候选英文：

For each period fit, physical gust curvature is the standardised quadratic coefficient divided by that fit’s squared gust standard deviation. The current table supplies those period-specific scales, and Figure 10 uses the resulting physical coefficients from single full-period fits. The old inverse-variance-weighted summary and its nominal interval are retained only as development history. No new interval is inferred from overlapping fold estimates, and equivalence of the supported calendar encoding does not establish stability across periods.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P091 → Appendix H retransformation

旧段：The audited plotting scripts for Figures 4 and 6 calculate expη without a retransformation correction. For exposure, η predicts ln1+C and the plotting code does not subtract one. The plotted quantities are therefore not arithmetic-mean customer counts or durations. The local audit reports global residual factors n−1i​expεi of 10.46 for exposure and 2.20 for recovery. These are full-sample diagnostics, not proof that the true conditional means are exactly those multiples of the plotted curves.

前邻：H.4 Exponentiated fitted values and retransformation

后邻：For example, ED∣X=expηXEexpε∣X. A single global factor is an adequate conditional correction only under additional assumptions about the residual distribution across covariates. If the target is customer count rather than 1+C, subtraction of one is also required after retransformation. A constant multiplicative factor cancels in ratios of the same positive transformed quantity, but subtraction of one does not; nor must a covariate-dependent factor cancel. The existing figure ratios are retained only on their explicitly stated exponentiated-log scale.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/residual_diagnostics.csv; R05/release_v1/figures/figure04.png and figure06.png；行键：当前对应总体/目标。

候选英文：

Figures 4 and 6 display exponentiated averages of fitted η, using their declared empirical or common-calendar references. They are not arithmetic conditional means. The current full-fit diagnostic means of exp(residual) are 10.448550 for customer impact and 3.463527 for recovery. These factors are not applied to the figures and do not establish a valid covariate-specific retransformation. Any assessment of engineering mean predictions must learn the correction using training data and evaluate it on held-out data. Predictions in customer units must also handle the addition of one explicitly.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## A-P094 → Appendix H current and remaining products

旧段：Complete residual plots and alternative-distribution coefficient tables were reported to exist in the local project but were not included in the material supplied for this revision. They are not reproduced or assigned a figure number here. A common-reference physical bootstrap interval, a directly comparable temporal fit, and out-of-sample storm ablations also remain to be supplied. These omissions are not represented as completed validation.

前邻：H.5 Material still required for additional analyses

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/supplement_summary.csv; R05/tables/CUBIC_PAIRED_AUDIT.csv; R05/release_v1/figures/figureF1.png; REMAINING_VALIDATION.md；行键：当前对应总体/目标。

候选英文：

The current archive now includes the residual panels, alternative-distribution full-fit summaries, paired cubic OOF comparison and directly comparable single-fit period estimates. Their existence does not resolve shape robustness, independent weather-process performance or calibrated prediction on the customer and hour scales. The former bootstrap remains historical and supplies no current common-reference physical interval. Any new minimum interval is conditional on the retained scientific claim and a prespecified physical-reference resampling protocol.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P002 → Abstract

旧段：UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven named storms. Stage-level records are reconstructed into incident-level affected-customer counts and total restoration spans. Aggregating customer counts across eligible stages gives a mean almost twice that obtained from the earliest recorded stage alone. Quadratic regressions of log-transformed outcomes show positive gust curvature in both margins. For affected customers, the full-sample fitted minimum is approximately 10.7 m/s at mean pressure; this is a conditional feature of the response curve, not a physical damage threshold. Positive quadratic terms also appear in alternative distributional specifications and retrospective temporal analyses, but the temporal comparison is not a previously untouched validation because early model development used observations from both periods. Across the combined sample, gust contributes modestly to out-of-sample predictive fit. In the recovery model, its incremental contribution is smaller than that of affected customers; within weather-attributed incidents, this pairwise ordering reverses. Comparisons during the seven storms describe fitted performance and do not independently establish that reversal. The results characterise nonlinear variation in the consequences of recorded outages across a heterogeneous distribution network, complementing component-level fragility research while estimating a different quantity.

前邻：Abstract

后邻：Keywords

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv; R04/tables/AppendixH_pressure_minima.json; R05/tables/CUBIC_PAIRED_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

This retrospective study reconstructs customer impact and restoration spans from stage records for 60,436 eligible outage incidents attributed to weather or asset conditions between April 2021 and March 2024. Quadratic models describe ln(1 + affected customers) and ln(restoration span in hours), conditional on a recorded incident. The customer-impact curve has a fitted minimum of 10.8 m/s at the main-sample mean pressure; its location is conditional on the specification and reference, and no validated physical-unit confidence interval is attached. Paired date-group out-of-fold evaluation gives pooled R² values of 0.0296 and 0.0920 for the two main models. In recovery, the conditional increment from the customer block exceeds the increment from the gust block in the main sample, whereas the ordering of point estimates differs in the weather-attributed subset. This comparison uses eventual customer information and does not establish stable differences across populations or initial-response usefulness. Positive cubic OOF increments and changing period and stage-composition patterns limit claims of a uniquely supported quadratic shape. The analysis describes variation in recorded outage consequences; independent weather-process evaluation and engineering-scale calibration remain necessary.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P006 → 1 Introduction

旧段：Storms and other extreme weather events are the most common cause of power disruptions in Great Britain [1]. In November 2021, Storm Arwen alone left more than one million customers without power [2]. Three months later, three named storms struck the United Kingdom within five days: Dudley, Eunice, and Franklin. Within the service area of UK Power Networks (UKPN), which covers London, the South East, and the East of England, Storm Eunice produced a peak observed gust of 39.4 m/s in Lewes, East Sussex, on 18 February 2022. This value is the highest gust recorded across the entire study period examined in this paper. The storm was associated with 1,601 weather-related outage events across 101 Local Authority Districts, a cumulative estimate of 376,712 affected customers, and a mean restoration time of 52.7 hours. Two days later, Storm Franklin affected the same network and produced a further 1,187 events.

前邻：1. Introduction

后邻：Outage impact can be measured by the number of customers affected, referred to hereafter as the exposure margin, or by the time needed for restoration, referred to hereafter as the recovery margin. These outcomes need not vary in fixed proportion to gust intensity. An increase in gust speed may be associated with different changes in outage consequences at different points in the observed range. Characterising that response can inform understanding of network performance, while any use in advance resource allocation requires separate assessment of predictive accuracy and decision costs.

段落职责/处理理由：删去未经本轮确认的外部灾害总数/现场峰值定位；原文[1]/[2]若保留需独立核源，不把主总体称天气子组。

证据：R04/tables/storm_LAD_details.csv; contracts/WEATHER_AND_REGIONAL_SOURCES.md；行键：当前对应总体/目标。

候选英文：

Severe-weather windows illustrate the scale of consequences recorded within the study network. In the main sample of incidents attributed to weather or asset conditions, the selected Eunice window contains 1,659 incidents across 101 LADs, with 395,470 aggregated affected customers and a mean recorded restoration span of 54.56 hours. The weather-attributed subset of that window contains 1,398 incidents. The largest matched gust value is 39.4 m/s, an archived weather proxy whose historical product and short-duration observational interpretation are not fully established. These incident-conditioned descriptions motivate examining customer impact and restoration spans without treating them as measurements of component failure probability.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P010 → 1 Introduction / research questions

旧段：This study addresses two questions within that operational setting. First, is there a consistent nonlinear association between gust intensity and the consequences of recorded outages, and how stable is the location of any fitted minimum? Second, does the predictive contribution of gust relative to affected-customer scale in a restoration-duration model change when attention is restricted to weather-attributed incidents? Prior work has investigated influential hazard and infrastructure predictors [6]; the comparison here concerns these two particular variable groups within the same network under different cause-based sample definitions.

前邻：Component-level fragility curves describe a specified structure under controlled or simulated loading conditions. Network outage records instead represent heterogeneous assets, locations and restoration circumstances. Field data can therefore provide complementary evidence about the scale and duration of recorded incidents, without identifying the same failure-probability function as a component fragility analysis.

后邻：Addressing both questions requires an observational record long enough, and varied enough, to include both routine operating conditions and a number of distinct severe wind events within the same network. The UKPN dataset examined in this paper spans three years of continuous operation, from April 2021 to March 2024, and includes seven officially named storms, among them Storm Eunice described above. This combination of duration and event coverage makes it possible to estimate a continuous response function across the full range of observed wind conditions, and to examine that function specifically under the seven storm events, rather than relying on a single simulated structure or a short observation window.

段落职责/处理理由：候选RQ3为显式适用范围职责，是否编号交作者；D-P010与012合并时仅采用一次。

证据：R05/OOF_SCORE_AUDIT.md; R05/COVARIANCE_AND_PERIOD_AUDIT.md; R04/tables/supplement_summary.csv；行键：当前对应总体/目标。

候选英文：

The analysis asks how gust is conditionally associated with recorded customer impact and restoration span, and how much gust and eventual customer information add to recovery-model fit under paired evaluation. A further scope question concerns sensitivity to sample definition, calendar period and reference support. Quadratic curves provide a parsimonious description and conditional stationary points, while existing cubic and distributional comparisons help delimit that description. OOF predictions grouped by date assess dates excluded from training. Retrospective periods and plots for named windows provide further descriptions; they do not constitute untouched confirmation or validation of complete weather processes.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P011 → 1 Introduction

旧段：Addressing both questions requires an observational record long enough, and varied enough, to include both routine operating conditions and a number of distinct severe wind events within the same network. The UKPN dataset examined in this paper spans three years of continuous operation, from April 2021 to March 2024, and includes seven officially named storms, among them Storm Eunice described above. This combination of duration and event coverage makes it possible to estimate a continuous response function across the full range of observed wind conditions, and to examine that function specifically under the seven storm events, rather than relying on a single simulated structure or a short observation window.

前邻：This study addresses two questions within that operational setting. First, is there a consistent nonlinear association between gust intensity and the consequences of recorded outages, and how stable is the location of any fitted minimum? Second, does the predictive contribution of gust relative to affected-customer scale in a restoration-duration model change when attention is restricted to weather-attributed incidents? Prior work has investigated influential hazard and infrastructure predictors [6]; the comparison here concerns these two particular variable groups within the same network under different cause-based sample definitions.

后邻：The analysis uses UKPN outage records from April 2021 to March 2024. Separate quadratic specifications describe affected customers and restoration duration conditional on an incident having occurred. The exposure model’s fitted minimum is evaluated at a stated pressure reference, and nested-model comparisons assess the incremental predictive contribution of gust and affected customers to recovery duration. Retrospective temporal analyses examine sample sensitivity, while seven named storms provide a descriptive assessment of fitted performance during severe weather. The development history limits the independence of the temporal evidence, as explained in Section 3.2 and Appendix E.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R03/configs/storm_windows.json; R04/tables/AppendixG_low_gust_support.csv；行键：当前对应总体/目标。

候选英文：

The observation window covers April 2021 to March 2024 and includes seven selected named-storm windows. It provides variation in the recorded weather proxy within one network and reporting system. The amount of support differs across gust levels and cause-defined populations, so coverage of the calendar does not guarantee reliable curve estimation throughout the wind range. Named windows are used for descriptive burden and prediction diagnostics; generalisation to independent weather processes requires a separately defined evaluation protocol.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P012 → 1 Introduction / research questions

旧段：The analysis uses UKPN outage records from April 2021 to March 2024. Separate quadratic specifications describe affected customers and restoration duration conditional on an incident having occurred. The exposure model’s fitted minimum is evaluated at a stated pressure reference, and nested-model comparisons assess the incremental predictive contribution of gust and affected customers to recovery duration. Retrospective temporal analyses examine sample sensitivity, while seven named storms provide a descriptive assessment of fitted performance during severe weather. The development history limits the independence of the temporal evidence, as explained in Section 3.2 and Appendix E.

前邻：Addressing both questions requires an observational record long enough, and varied enough, to include both routine operating conditions and a number of distinct severe wind events within the same network. The UKPN dataset examined in this paper spans three years of continuous operation, from April 2021 to March 2024, and includes seven officially named storms, among them Storm Eunice described above. This combination of duration and event coverage makes it possible to estimate a continuous response function across the full range of observed wind conditions, and to examine that function specifically under the seven storm events, rather than relying on a single simulated structure or a short observation window.

后邻：Section 2 describes the data, incident-level outcome construction and sample. Section 3 presents the regression specifications, model-development history and evaluation procedures. Section 4.1 reports gust curvature and conditional fitted minima; Sections 4.2 and 4.3 examine predictive contributions and storm-period fitted performance; Section 4.4 reports retrospective temporal and clustering checks. Section 5 discusses interpretation, limitations and further work.

段落职责/处理理由：候选RQ3为显式适用范围职责，是否编号交作者；D-P010与012合并时仅采用一次。

证据：R05/OOF_SCORE_AUDIT.md; R05/COVARIANCE_AND_PERIOD_AUDIT.md; R04/tables/supplement_summary.csv；行键：当前对应总体/目标。

候选英文：

The analysis asks how gust is conditionally associated with recorded customer impact and restoration span, and how much gust and eventual customer information add to recovery-model fit under paired evaluation. A further scope question concerns sensitivity to sample definition, calendar period and reference support. Quadratic curves provide a parsimonious description and conditional stationary points, while existing cubic and distributional comparisons help delimit that description. OOF predictions grouped by date assess dates excluded from training. Retrospective periods and plots for named windows provide further descriptions; they do not constitute untouched confirmation or validation of complete weather processes.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P013 → 1 Introduction / roadmap

旧段：Section 2 describes the data, incident-level outcome construction and sample. Section 3 presents the regression specifications, model-development history and evaluation procedures. Section 4.1 reports gust curvature and conditional fitted minima; Sections 4.2 and 4.3 examine predictive contributions and storm-period fitted performance; Section 4.4 reports retrospective temporal and clustering checks. Section 5 discusses interpretation, limitations and further work.

前邻：The analysis uses UKPN outage records from April 2021 to March 2024. Separate quadratic specifications describe affected customers and restoration duration conditional on an incident having occurred. The exposure model’s fitted minimum is evaluated at a stated pressure reference, and nested-model comparisons assess the incremental predictive contribution of gust and affected customers to recovery duration. Retrospective temporal analyses examine sample sensitivity, while seven named storms provide a descriptive assessment of fitted performance during severe weather. The development history limits the independence of the temporal evidence, as explained in Section 3.2 and Appendix E.

后邻：2. Data and Study Setting

段落职责/处理理由：不预先承诺六章；作者选择五章或六章后再落实编号。

证据：R05/MANUSCRIPT_REWRITE_CANDIDATES.md；行键：当前对应总体/目标。

候选英文：

Section 2 defines the records, reconstructed outcomes, source limitations and analysis populations. Section 3 sets out the models, reference quantities and paired date-group evaluation. Section 4 reports conditional shapes, information increments, named-window diagnostics and retrospective period comparisons. Interpretation and limits follow before the final answers to the research questions.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P017 → 2 Data / weather

旧段：Weather variables are matched to each incident using hourly reanalysis data from the Open-Meteo historical weather API [13], which is based on the ERA5 global reanalysis dataset [14]. Data are indexed to the latitude and longitude reported for each incident and the hour in which it began. The primary wind variable used throughout this paper is instantaneous gust speed rather than sustained wind speed. This choice follows the convention in structural wind engineering, where design wind loads are based on a short-duration (3-second) gust rather than a longer-averaged sustained speed, because peak instantaneous loading determines structural response and failure [15]. This convention has been applied specifically to wind-induced damage in electrical grid infrastructure [16]. In the final analysis sample, gust speed has a mean of 9.87 m/s and a standard deviation of 5.22 m/s, referenced in Section 4.1 when reporting the exposure margin’s turning point in physical units.

前邻：UKPN operates the electricity distribution network across London, the South East, and the East of England, and reports outage incidents to Ofgem, the energy regulator for Great Britain, under the regulatory reporting framework set out in the RIIO-ED1 and RIIO-ED2 Annex F guidance [11, 12]. RIIO-ED1 and RIIO-ED2 are successive multi-year price control periods during which Ofgem sets the revenue and performance requirements for UK electricity distribution network operators. This paper draws on UKPN’s outage incident records covering 1 April 2021 to 31 March 2024, a period of three complete regulatory years spanning both the RIIO-ED1 and RIIO-ED2 price control periods. Each record corresponds to a restoration stage rather than a complete outage incident. An incident that requires more than one restoration action, for example because power is restored to part of the affected area before the remainder, is represented by more than one stage-level record sharing a common incident reference. Section 2.2 describes how event-level outcome variables are constructed from these stage-level records.

后邻：Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise resident population from ONS local authority population estimates [17], and income deprivation rate, the gap between local and national income deprivation, and spatial clustering of income deprivation measured by Moran’s I, all drawn from the ONS dataset mapping income deprivation at a local authority level [18]. Moran’s I follows the spatial autocorrelation statistic introduced by Moran [19]. An urban-rural classification is drawn from the same ONS local statistics resource used for the population and deprivation data [17]. LAD boundaries as at December 2021 are taken from the ONS Open Geography Portal [20].

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：contracts/WEATHER_AND_REGIONAL_SOURCES.md; R03/CONTRACTS.md; R04/tables/H0_R1_B1_shape.csv；行键：当前对应总体/目标。

候选英文：

Weather covariates are taken from the frozen historical cache and indexed to the earliest valid recorded start time, converted to UTC and floored to the hour, using coordinates derived from the reported primary-substation field. This timestamp is a record-based proxy for onset. The cached gust field is used in m/s; its specific historical product and equivalence to an observed three-second gust have not been established. The main-sample gust mean and standard deviation are 9.9102 and 5.2800 m/s. The 24-hour precipitation proxy uses the 24 hourly endpoints ending at the matched hour, with complete finite values required; it does not cover the remaining minutes between that hour and the recorded timestamp.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P018 → 2 Data / Appendix A regional definitions

旧段：Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise resident population from ONS local authority population estimates [17], and income deprivation rate, the gap between local and national income deprivation, and spatial clustering of income deprivation measured by Moran’s I, all drawn from the ONS dataset mapping income deprivation at a local authority level [18]. Moran’s I follows the spatial autocorrelation statistic introduced by Moran [19]. An urban-rural classification is drawn from the same ONS local statistics resource used for the population and deprivation data [17]. LAD boundaries as at December 2021 are taken from the ONS Open Geography Portal [20].

前邻：Weather variables are matched to each incident using hourly reanalysis data from the Open-Meteo historical weather API [13], which is based on the ERA5 global reanalysis dataset [14]. Data are indexed to the latitude and longitude reported for each incident and the hour in which it began. The primary wind variable used throughout this paper is instantaneous gust speed rather than sustained wind speed. This choice follows the convention in structural wind engineering, where design wind loads are based on a short-duration (3-second) gust rather than a longer-averaged sustained speed, because peak instantaneous loading determines structural response and failure [15]. This convention has been applied specifically to wind-induced damage in electrical grid infrastructure [16]. In the final analysis sample, gust speed has a mean of 9.87 m/s and a standard deviation of 5.22 m/s, referenced in Section 4.1 when reporting the exposure margin’s turning point in physical units.

后邻：Figure 1 shows the three UKPN licence areas and the spatial density of incidents across the study period. Incident density is not uniform across the service area. It is concentrated around London, which sits at the boundary between the South East and East of England licence areas. A smaller, secondary concentration is visible near the north-east coast of the East of England licence area. The remainder of the service area shows a comparatively even, lower density of incidents.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：contracts/WEATHER_AND_REGIONAL_SOURCES.md; R05/tables/SOURCE_DEPENDENCIES.csv; R05/checks/regional_workbook_extract.json；行键：当前对应总体/目标。

候选英文：

The income-deprivation covariates describe conditions within LADs. The published rate aggregates LSOA income-deprivation rates with population weights; the gap is the highest minus the lowest LSOA rate within the LAD, and Moran’s I describes within-LAD LSOA spatial clustering. Rate and gap enter the design on a proportion scale. Buckinghamshire currently carries explicitly labelled historical proxies formed from simple averages across its four former districts. These proxies are retained pending the author-requested LSOA reconstruction and comparison. A link between LAD21 and LAD23 codes does not by itself establish boundary equivalence.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P019 → 2 Data / Figure 1 caption

旧段：Figure 1 shows the three UKPN licence areas and the spatial density of incidents across the study period. Incident density is not uniform across the service area. It is concentrated around London, which sits at the boundary between the South East and East of England licence areas. A smaller, secondary concentration is visible near the north-east coast of the East of England licence area. The remainder of the service area shows a comparatively even, lower density of incidents.

前邻：Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise resident population from ONS local authority population estimates [17], and income deprivation rate, the gap between local and national income deprivation, and spatial clustering of income deprivation measured by Moran’s I, all drawn from the ONS dataset mapping income deprivation at a local authority level [18]. Moran’s I follows the spatial autocorrelation statistic introduced by Moran [19]. An urban-rural classification is drawn from the same ONS local statistics resource used for the population and deprivation data [17]. LAD boundaries as at December 2021 are taken from the ONS Open Geography Portal [20].

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure01.png; R05/frozen/source_audit/r02_events.py；行键：当前对应总体/目标。

候选英文：

Figure 1 shows hexagonal-bin counts of eligible main-sample incidents at the reported primary-substation coordinates. Colour represents incident counts on a logarithmic scale, rather than an area-normalised density. The current panel uses longitude and latitude and does not display licence-area boundaries or a Great Britain inset. Spatial concentrations in these reported locations should not be interpreted as exact fault-site density or district-level outage risk.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P021 → 2 Data / Figure 1 caption

旧段：Figure 1. Study area and event density. The map shows the three UKPN licence areas (London, South East, East of England) and the spatial density of all incidents in the final analysis sample, rendered as a hexagonal binning of incident coordinates on a logarithmic count scale. The inset shows the location of the UKPN service area within Great Britain.

前邻：

后邻：2.2 Outcome variable construction

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure01.png; R05/frozen/source_audit/r02_events.py；行键：当前对应总体/目标。

候选英文：

Figure 1 shows hexagonal-bin counts of eligible main-sample incidents at the reported primary-substation coordinates. Colour represents incident counts on a logarithmic scale, rather than an area-normalised density. The current panel uses longitude and latitude and does not display licence-area boundaries or a Great Britain inset. Spatial concentrations in these reported locations should not be interpreted as exact fault-site density or district-level outage risk.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P030 → 2 Data / Appendix B comparison

旧段：Constructing affected customers by aggregating across stages, rather than taking the customer count reported in the earliest stage of each incident, changes the sample mean from 47.13 to 93.02 customers, a difference of a factor of 1.97, within the same final analysis sample reported in Table 1. This difference reflects incidents with more than one restoration stage, in which the earliest stage alone does not capture the full extent of the customers affected as the incident evolves. Appendix B reports the full data processing pipeline underlying Equations 1 and 2, including the handling of a small number of boundary cases not covered by the general definitions above.

前邻：where Di is restoration duration for incident i, and Ti,rstart and Ti,rend are the start and end times recorded at stage r.

后邻：2.3 Descriptive statistics and visualization

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/CUSTOMER_COMPARATOR_SUMMARY.csv; R05/tables/CUSTOMER_SELECTION_CHECKS.csv；行键：当前对应总体/目标。

候选英文：

Within the common main sample of 60,436 incidents, mean aggregated affected customers are 93.0257. Selecting the record with the minimum available numeric stage number gives a mean of 47.1283 and a ratio of means of 1.9739. Selecting the earliest valid recorded start time, breaking ties by persistent source-row order, gives a mean of 31.1220 and a ratio of 2.9891. All three measures are observed for this common sample. The minimum available stage number exceeds one for 8,817 incidents (14.589%). There are no minimum-stage ties in this sample, but 15,249 incidents have earliest-time ties and 13,266 have differing customer counts among those tied records. These deterministic record comparators are not verified true initial customer counts; the ratios are ratios of sample means, not means of event-level ratios.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P032 → 2 Data / outcome distributions

旧段：Table 1 reports descriptive statistics for affected customers and restoration duration in the final analysis sample, on the original scale and after log transformation. Both variables are heavily right-skewed on the original scale, with the mean well above the median (93.0 versus 2.0 for affected customers, 11.8 versus 6.3 hours for restoration duration). Figure 2 shows the distribution of each variable before and after transformation. The log transformations substantially reduce this skew, but they do not produce a fully symmetric distribution in either case. The transformed affected-customers variable shows a sawtooth pattern at low values, reflecting the fact that many incidents affect a small integer number of customers. The transformed restoration-duration variable shows two distinct modes, one near one hour and one near seven to twelve hours, separated by a clear trough. Restoration-stage composition is examined separately in Section 4.1 and Appendix D; those analyses describe associations and do not by themselves identify the source of the bimodal duration distribution. Despite this remaining structure, the log transformation is still used for both variables, because it reduces the influence of very large observations on a least-squares fit.

前邻：2.3 Descriptive statistics and visualization

后邻：Table 1. Descriptive statistics for affected customers and restoration duration, final analysis sample.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Table1_current.csv; R05/release_v1/figures/figure02.png；行键：当前对应总体/目标。

候选英文：

The main models each use 60,436 eligible incidents, with all valid outcome tails retained. Affected customers have mean 93.03 and median 2.00; recorded restoration span has mean 17.46 hours and median 6.37 hours. The maximum span is 5547.05 hours, which makes the all-valid duration summary materially different from the earlier trimmed sample. Figure 2 displays raw and log-transformed outcomes without trimming the displayed tails. Transformation limits the leverage of very large values on the target scale but does not establish normal residuals or resolve record-quality uncertainty.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P035 → Figure 2 caption

旧段：Figure 2. Distribution of affected customers and restoration duration, original scale and after log transformation. (a) Affected customers, original scale. (b) log(1+affected customers). (c) Restoration duration, original scale (hours). (d) log(restoration duration).

前邻：

后邻：Affected customers and restoration duration are treated as separate outcome margins because they measure different aspects of an incident. Small linear or rank correlations, where observed, would not establish independence. Appendix D examines the association using restoration-stage strata and additional regression controls. The pooled and stratified patterns differ, indicating sensitivity to event composition; they do not by themselves identify a direct causal effect of customer scale on duration.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure02.png; R04/tables/Table1_current.csv；行键：当前对应总体/目标。

候选英文：

Figure 2. Raw and log-transformed customer impact and restoration span for the 60,436 eligible main-sample incidents. Raw-outcome histograms use logarithmic count axes; transformed-outcome histograms show ln(1 + C) and ln(D/h). All valid tails are retained.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P038 → 2 Data / Appendix C sample sensitivity

旧段：UKPN records a Cause Code for each incident. This paper groups the original codes into six analytical categories, with the mapping reported in Appendix A.2. The main sample retains the weather-related and asset-related groups to examine incidents attributed to weather or network asset condition. Other groups cover no fault found or unknown causes, third-party interference, human error, and external or customer causes. These labels do not establish statistical independence from gust, and weather may affect restoration even when it is not the recorded initiating cause. A six-category sensitivity comparison is reported in Appendix C. Across five folds, the recovery model’s mean quadratic gust coefficient is 0.0608 in the six-category sample (n = 116,064) and 0.0792 in the two-category sample (n = 59,834), with positive significant quadratic terms in all folds. The mean linear coefficient changes from 0.0257 to 0.0002 and is significant in five versus zero folds. This shows sensitivity of the linear term to sample definition, rather than proving that its signal in the wider sample is non-physical. The restriction was originally chosen before temporal separation, as documented in Section 3.2.

前邻：2.4 Sample construction and predictor variables

后邻：The resulting sample comprises 60,453 incidents. After matching weather data and excluding incidents with missing regional covariates, 60,437 incidents are available for the exposure model and 59,834 for the recovery model, the difference reflecting incidents for which restoration duration could not be computed or fell above the 99th percentile of the restoration duration distribution.

段落职责/处理理由：当前完整六组合并系数可取档案；旧116064/59834及5/0显著折数不沿用。

证据：R04/tables/AppendixC_fold_summary.csv; R04/supplements_v1/six_group_*.json；行键：当前对应总体/目标。

候选英文：

The six analytical cause groups form an implemented code grouping, whose official documentary semantics remain incompletely established. The current sensitivity analysis fits one pooled six-group recovery population of 117,108 incidents and compares it with the 60,436-incident main population. Across the five overlapping training folds, mean quadratic gust coefficients are 0.07806 and 0.08350, respectively; all are positive and nominally significant under the stated normal-reference LAD calculation. Mean linear coefficients are 0.01892 and −0.00555, with three and one nominally significant folds. These summaries indicate sensitivity to sample composition. They are not six independently fitted cause-specific models, independent replications, or evidence that one group’s association is physical and another’s is not.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P039 → 2 Data / sample flow

旧段：The resulting sample comprises 60,453 incidents. After matching weather data and excluding incidents with missing regional covariates, 60,437 incidents are available for the exposure model and 59,834 for the recovery model, the difference reflecting incidents for which restoration duration could not be computed or fell above the 99th percentile of the restoration duration distribution.

前邻：UKPN records a Cause Code for each incident. This paper groups the original codes into six analytical categories, with the mapping reported in Appendix A.2. The main sample retains the weather-related and asset-related groups to examine incidents attributed to weather or network asset condition. Other groups cover no fault found or unknown causes, third-party interference, human error, and external or customer causes. These labels do not establish statistical independence from gust, and weather may affect restoration even when it is not the recorded initiating cause. A six-category sensitivity comparison is reported in Appendix C. Across five folds, the recovery model’s mean quadratic gust coefficient is 0.0608 in the six-category sample (n = 116,064) and 0.0792 in the two-category sample (n = 59,834), with positive significant quadratic terms in all folds. The mean linear coefficient changes from 0.0257 to 0.0002 and is significant in five versus zero folds. This shows sensitivity of the linear term to sample definition, rather than proving that its signal in the wider sample is non-physical. The restriction was originally chosen before temporal separation, as documented in Section 3.2.

后邻：The full covariate set comprises gust speed and its square, an interaction between gust speed and mean sea level pressure, 24-hour cumulative precipitation, temperature, mean sea level pressure, log population, income deprivation rate, the gap between local and national income deprivation, Moran’s I, an urban-rural indicator, and calendar year and month fixed effects. The recovery model additionally includes standardised log(1 + affected customers) and its square as covariates, discussed further in Section 4.1.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R02 frozen manifest; R05/OOF_SCORE_AUDIT.csv; R04/tables/core_metrics.csv；行键：当前对应总体/目标。

候选英文：

The frozen reconstruction contains 135,025 incident records. Applying the declared time, identity, cause consensus, weather and regional availability rules yields 60,436 main-sample observations for each current outcome model, including 9,857 weather-attributed observations. The main fits cover 111 LADs and 1,096 dates; the weather fits cover 105 LADs and 1,001 dates. Equality of the current model counts is an observed result of the eligibility rules, not an assumption that every possible customer-impact and recovery population must coincide. The primary analysis retains all valid outcome tails and does not impose the earlier recovery p99 cutoff.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P040 → 2 Data / design variables

旧段：The full covariate set comprises gust speed and its square, an interaction between gust speed and mean sea level pressure, 24-hour cumulative precipitation, temperature, mean sea level pressure, log population, income deprivation rate, the gap between local and national income deprivation, Moran’s I, an urban-rural indicator, and calendar year and month fixed effects. The recovery model additionally includes standardised log(1 + affected customers) and its square as covariates, discussed further in Section 4.1.

前邻：The resulting sample comprises 60,453 incidents. After matching weather data and excluding incidents with missing regional covariates, 60,437 incidents are available for the exposure model and 59,834 for the recovery model, the difference reflecting incidents for which restoration duration could not be computed or fell above the 99th percentile of the restoration duration distribution.

后邻：Variance inflation factors for all continuous covariates in the final model specification are below 4, with the highest value, 3.76, corresponding to the gap between local income deprivation and the national average. Values of 5 and 10 are commonly cited as informal thresholds for concern regarding multicollinearity, although O’Brien [21] cautions that these thresholds are heuristic rather than absolute, and that a given VIF value should be interpreted alongside the sample size and the strength of the effect under study rather than treated as a fixed cutoff. The VIF values obtained here are below both commonly cited thresholds regardless of this qualification.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R03/CONTRACTS.md; R05/frozen/R03_src/contracts.py；行键：当前对应总体/目标。

候选英文：

The control block contains non-gust weather covariates, regional covariates and additive year and month indicators. The gust block adds standardised gust, its square, and its interaction with standardised pressure. The recovery customer block adds standardised ln(1 + aggregated affected customers) and its square. Only the named weather and log-customer variables are standardised; population and deprivation variables retain their declared transformations and units. The deprivation gap denotes within-LAD LSOA dispersion rather than a difference from the national mean.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P041 → 2 Data / collinearity

旧段：Variance inflation factors for all continuous covariates in the final model specification are below 4, with the highest value, 3.76, corresponding to the gap between local income deprivation and the national average. Values of 5 and 10 are commonly cited as informal thresholds for concern regarding multicollinearity, although O’Brien [21] cautions that these thresholds are heuristic rather than absolute, and that a given VIF value should be interpreted alongside the sample size and the strength of the effect under study rather than treated as a fixed cutoff. The VIF values obtained here are below both commonly cited thresholds regardless of this qualification.

前邻：The full covariate set comprises gust speed and its square, an interaction between gust speed and mean sea level pressure, 24-hour cumulative precipitation, temperature, mean sea level pressure, log population, income deprivation rate, the gap between local and national income deprivation, Moran’s I, an urban-rural indicator, and calendar year and month fixed effects. The recovery model additionally includes standardised log(1 + affected customers) and its square as covariates, discussed further in Section 4.1.

后邻：3. Empirical Framework

段落职责/处理理由：11处组合段落；原[21]作为阈值讨论可另保留，当前候选不制造新引文。

证据：R04/tables/VIF_summary.csv；行键：当前对应总体/目标。

候选英文：

The largest continuous-predictor VIFs are 3.7546 for the main customer-impact model and 3.7550 for the main recovery model, both for the deprivation-gap variable. In the weather-attributed models they are 4.9266 and 4.9301; maxima across all included design columns are approximately 5.35 there. Consequently, the earlier statement that every model has a VIF below four cannot be retained. These diagnostics describe the fitted designs and do not validate regional source definitions, rule out omitted-variable bias or justify removing a variable solely to satisfy a numerical threshold.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P048 → 3 Methods / supplementary specifications

旧段：Exploratory specification checks re-estimated the exposure model using negative binomial and Tweedie alternatives and the recovery model using gamma and Tweedie alternatives. The project audit reports positive quadratic gust terms across these checks. They are treated as supplementary sensitivity evidence rather than independent validation. A complete comparison of model settings, coefficients and residual diagnostics remains necessary for a fully reproducible assessment. The main estimates and clustering checks are reported in Table 3 and Appendix F.

前邻：Ordinary least squares is applied to log(1 + affected customers) and log(restoration duration). Both outcomes are strongly right-skewed on their original scales, as shown in Figure 2. Negative binomial, gamma and Tweedie generalised linear models offer alternative distributional specifications for such outcomes [22]. Log-OLS is retained for a common modelling framework and transparent coefficient interpretation; it does not require normally distributed raw outcomes, and residual non-normality alone does not establish that coefficient estimation is invalid. Conditional-mean specification and appropriate treatment of error dependence remain necessary considerations.

后邻：3.2 Model development and retrospective evaluation

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/supplement_summary.csv; R05/tables/CUBIC_PAIRED_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

The current archive contains negative-binomial and Tweedie customer-impact fits and gamma and Tweedie recovery fits, with coefficients, settings and recorded warnings retained. These are full-fit distributional sensitivity checks, with no corresponding GLM OOF evaluation. The paired cubic OOF comparison is a separate product and reports positive increments for both outcomes. These alternatives help delimit the quadratic log-OLS description; agreement in a coefficient sign is not independent validation or proof of a uniquely supported shape.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P051 → 3 Methods / development history

旧段：The period 1 April 2021 to 29 September 2023 is called the development period, and 30 September 2023 to 31 March 2024 the later period. For continuity with the project records and figure labels, the latter is also called the confirmation sample, but that label does not imply independence from model development. The local audit identified six earlier analysis steps covering outcome reconstruction and duration choice, the first turning-point analysis, Cause Code restriction and its supporting checks, and the initial predictive-contribution analysis; all used data containing the later period. Subsequent re-estimation on separated or recombined samples corrected sample allocation without undoing this earlier information use. The historical duration-measure comparison was not repeated on separated data. Appendix E records these limits. Figure 3 places four storms in the earlier period and three in the later period.

前邻：Choosing outcome definitions, sample restrictions and model terms using the same data later used for inference can make reported evidence optimistic. Separating data before exploration is one approach to this problem [23]. In this project, however, the temporal separation was established after several foundational decisions had already used observations from both periods. The subsequent temporal comparison is therefore retrospective and does not constitute validation on a previously untouched sample.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：manuscript_record historical MR18/19 sources; R03/configs/storm_windows.json；行键：当前对应总体/目标。

候选英文：

The earlier period extends from 1 April 2021 through 29 September 2023; the later period extends from 30 September 2023 through 31 March 2024. Both contributed to foundational choices before temporal separation, including outcome definition, sample restriction and initial shape and information comparisons. The later period is therefore described as retrospective rather than an untouched confirmation sample. Re-estimation can check the current computations but does not undo that history. Four selected named-storm windows fall in the earlier period and three in the later period.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P053 → 3 Methods / development history

旧段：Figure 3. Study period and retrospective temporal partition. Storm markers indicate their months of occurrence; the diagram is schematic within each month. The later-period label does not denote a previously untouched validation sample.

前邻：

后邻：Five-fold cross-validation groups incidents by start date, so all incidents starting on a given day enter the same fold. For each comparison, models are fitted on four folds and evaluated on the remaining fold, and fold-level R-squared values are averaged. Sections 4.2 and 4.3 report these predictive comparisons for the combined sample and the weather-attributed subset respectively. The development-only coefficient summaries used in Section 4.4 are separately identified. These evaluations are out of fold for coefficient fitting, but not independent of earlier model selection. Grouping by date also does not guarantee separation of all days belonging to the same storm.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：manuscript_record historical MR18/19 sources; R03/configs/storm_windows.json；行键：当前对应总体/目标。

候选英文：

The earlier period extends from 1 April 2021 through 29 September 2023; the later period extends from 30 September 2023 through 31 March 2024. Both contributed to foundational choices before temporal separation, including outcome definition, sample restriction and initial shape and information comparisons. The later period is therefore described as retrospective rather than an untouched confirmation sample. Re-estimation can check the current computations but does not undo that history. Four selected named-storm windows fall in the earlier period and three in the later period.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P054 → 3 Methods / formal evaluation

旧段：Five-fold cross-validation groups incidents by start date, so all incidents starting on a given day enter the same fold. For each comparison, models are fitted on four folds and evaluated on the remaining fold, and fold-level R-squared values are averaged. Sections 4.2 and 4.3 report these predictive comparisons for the combined sample and the weather-attributed subset respectively. The development-only coefficient summaries used in Section 4.4 are separately identified. These evaluations are out of fold for coefficient fitting, but not independent of earlier model selection. Grouping by date also does not guarantee separation of all days belonging to the same storm.

前邻：Figure 3. Study period and retrospective temporal partition. Storm markers indicate their months of occurrence; the diagram is schematic within each month. The later-period label does not denote a previously untouched validation sample.

后邻：The exposure minimum was first estimated as 10.69 m/s before temporal separation. Restricting the analysis to the earlier-period exposure sample (n = 48,323) changed the estimate to 12.13 m/s. The final combined exposure sample (n = 60,437) gave 10.69 m/s again. These estimates refer to different sample constructions; the repeated rounded value is not an independent replication. Table E2 records this sequence. Sections 4.1 to 4.3 use the final combined sample unless a subset is explicitly identified.

段落职责/处理理由：相邻方法段建议合并为一段，避免重复三次。

证据：R05/OOF_SCORE_AUDIT.md; R05/tables/OOF_SST_DECOMPOSITION.csv；行键：当前对应总体/目标。

候选英文：

Primary performance is evaluated by five-fold OOF prediction with all records sharing a UTC date assigned to the same frozen fold. Each model learns its centring and sample-standard-deviation scaling from its training observations only. Nested blocks are compared on identical eligible events, targets and folds within each population. Pooled OOF R² is calculated from the combined prediction SSE and the total target SST; arithmetic mean fold R² is reported alongside it. Negative OOF increments are permitted. Date grouping prevents the same date entering training and evaluation, but can split a multi-day weather process; it is therefore not complete process validation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P057 → 3 Methods / transformations

旧段：Continuous predictors are standardised using the estimation sample’s means and standard deviations. In cross-validation, scaling is estimated on the training fold and applied to its validation fold. For the separate temporal analyses, each sample has its own scaling; bootstrap fits likewise recompute scaling within each resample. Thus G=0 denotes the mean gust for the relevant fit, not calm conditions. Gust and pressure enter as standardised variables, with gust squared and the gust-pressure product constructed from those variables. In the recovery model, the customer predictor is first transformed as ln1+Ci, then standardised; both this standardised predictor and its square enter the model. Appendix H distinguishes the reference scales used for fitted minima and uncertainty.

前邻：3.3 Model specification

后邻：The final model specification is the same for both outcome margins, except that the recovery model includes two additional terms. This is the full version of Equation 3, with the additional covariates included, given by

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/frozen/R03_src/contracts.py; R05/checks/core_archive_readback.json；行键：当前对应总体/目标。

候选英文：

Gust, pressure, temperature, precipitation and the recovery log-customer predictor use the declared training-sample means and sample standard deviations. Squares and interactions are constructed from these standardised variables. Regional rate and gap remain on their stored proportion scales, log population retains its declared transform, and the urban indicator is binary. Fold models estimate their preprocessing from training data only; period models use their own scales. Consequently, zero standardised gust denotes a model-specific training mean rather than calm conditions.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P060 → 3 Methods / formal evaluation

旧段：where Yi is 1+Ci for the exposure margin and Di for the recovery margin; Gi and Pi are standardised gust and pressure; Xi contains the other continuous and categorical covariates in Table 2; and δyi and θmi are additive year and month effects. The intercept is α, and εi is the error term. For recovery, Xi additionally contains standardised ln1+Ci and its square.

前邻：lnYi=α+β1Gi+β2Gi2+β3GiPi+Xi′γ+δyi+θmi+εi     (4)

后邻：Year and month effects enter as separate dummy-variable sets, not year-by-month interactions. The exposure and recovery equations describe conditional log-scale responses. Let ηi denote a fitted value on that scale. Figures 4 and 6 display expηi without a retransformation correction: for exposure this refers to 1+Ci, and for recovery to duration. These are exponentiated fitted log outcomes, not estimates of conditional arithmetic means. The exposure displays also do not subtract one. Figure 7 retains ratios on this same exponentiated-log scale.

段落职责/处理理由：相邻方法段建议合并为一段，避免重复三次。

证据：R05/OOF_SCORE_AUDIT.md; R05/tables/OOF_SST_DECOMPOSITION.csv；行键：当前对应总体/目标。

候选英文：

Primary performance is evaluated by five-fold OOF prediction with all records sharing a UTC date assigned to the same frozen fold. Each model learns its centring and sample-standard-deviation scaling from its training observations only. Nested blocks are compared on identical eligible events, targets and folds within each population. Pooled OOF R² is calculated from the combined prediction SSE and the total target SST; arithmetic mean fold R² is reported alongside it. Negative OOF increments are permitted. Date grouping prevents the same date entering training and evaluation, but can split a multi-day weather process; it is therefore not complete process validation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P061 → 3 Methods / formal evaluation

旧段：Year and month effects enter as separate dummy-variable sets, not year-by-month interactions. The exposure and recovery equations describe conditional log-scale responses. Let ηi denote a fitted value on that scale. Figures 4 and 6 display expηi without a retransformation correction: for exposure this refers to 1+Ci, and for recovery to duration. These are exponentiated fitted log outcomes, not estimates of conditional arithmetic means. The exposure displays also do not subtract one. Figure 7 retains ratios on this same exponentiated-log scale.

前邻：where Yi is 1+Ci for the exposure margin and Di for the recovery margin; Gi and Pi are standardised gust and pressure; Xi contains the other continuous and categorical covariates in Table 2; and δyi and θmi are additive year and month effects. The intercept is α, and εi is the error term. For recovery, Xi additionally contains standardised ln1+Ci and its square.

后邻：Table 2 lists the covariates and fixed effects included alongside gust, its square and the gust-pressure interaction. Appendix A describes their sources and transformations.

段落职责/处理理由：相邻方法段建议合并为一段，避免重复三次。

证据：R05/OOF_SCORE_AUDIT.md; R05/tables/OOF_SST_DECOMPOSITION.csv；行键：当前对应总体/目标。

候选英文：

Primary performance is evaluated by five-fold OOF prediction with all records sharing a UTC date assigned to the same frozen fold. Each model learns its centring and sample-standard-deviation scaling from its training observations only. Nested blocks are compared on identical eligible events, targets and folds within each population. Pooled OOF R² is calculated from the combined prediction SSE and the total target SST; arithmetic mean fold R² is reported alongside it. Negative OOF increments are permitted. Date grouping prevents the same date entering training and evaluation, but can split a multi-day weather process; it is therefore not complete process validation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P064 → 3 Methods / Appendix F inference

旧段：The main standard errors are clustered by Local Authority District (LAD) [24]. Appendix F also reports two-way clustering by LAD and date for the same final combined-sample coefficients. Changing the covariance estimator changes standard errors and confidence intervals, not the OLS point estimates. These checks address specified patterns of error dependence; they do not remove omitted-variable bias or establish independence across all multi-day storm events.

前邻：Table 2. Other covariates and temporal fixed effects in Equation 4.

后邻：4. Results

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/COVARIANCE_AND_PERIOD_AUDIT.md; R04/tables/Tables3_F_complete_coefficients.csv；行键：当前对应总体/目标。

候选英文：

The reported OLS coefficients are paired with CR1 standard errors clustered by LAD. Alternative clustering by date and by both LAD and date is evaluated for the same full sample. Reported p-values use the stated normal-reference Wald calculation. Changing the covariance estimator leaves the fitted coefficients unchanged. The full main models each use 60,436 incidents. Covariance conditions are assessed separately for each period. Six matrices for clustering by both LAD and date are not positive semidefinite. The displayed standard errors of the physical terms use LAD covariance, and Figure 10 contains points only. No arbitrary joint Wald inference is authorised from those non-PSD matrices.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P068 → 4.1 Shape

旧段：Table 3 reports the final combined-sample gust coefficients. The quadratic terms are positive in both margins (p < 0.001 under LAD clustering). The linear term is negative for exposure (p = 0.022) and close to zero for recovery (p = 0.982). The quadratic terms also retain a positive sign in the reported alternative-distribution and temporal checks. These results support positive curvature within the fitted specifications. They do not establish a physical damage threshold, and the significance of a linear term is not a criterion for deciding whether a fitted minimum exists.

前邻：This section reports the fitted gust-response shape and the location of the exposure minimum under stated reference conditions. Sections 4.2 to 4.4 then examine predictive contributions, storm-period fitted performance and retrospective temporal sensitivity.

后邻：Table 3. Gust coefficients, final model specification.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Tables3_F_complete_coefficients.csv; R05/tables/CUBIC_PAIRED_AUDIT.csv; R04/tables/supplement_summary.csv；行键：当前对应总体/目标。

候选英文：

The main customer-impact model has standardised gust coefficients -0.036036 and 0.106020; the recovery coefficients are -0.007379 and 0.087842. Positive quadratic coefficients describe curvature within these specifications. Existing paired cubic comparisons improve pooled OOF R² by 0.193164 percentage points for customer impact and 0.049819 percentage points for recovery. The gains are small on the R² scale but are not zero, so quadratic uniqueness or robust shape is not established by the quadratic coefficient sign. Alternative GLM results are full-fit sensitivity evidence, not additional OOF confirmation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P073 → 4.1 / Appendix H conditional point

旧段：where β1 and β2 are the fitted linear and quadratic gust coefficients. At another pressure level the location is G*P=−β1+β3P/2β2. Using full-precision combined-sample coefficients gives G*0=0.157286 and a physical gust of 10.694 m/s, reported as 10.69 m/s. The corresponding algebraic estimates at pressure one standard deviation below and above its mean are 9.656 and 11.732 m/s (Appendix H). These are conditional fitted locations; the interaction is not significant under two-way clustering, so the pressure contrast is not presented as an established operational effect.

前邻：G*P=0=−β12β2     (5)

后邻：A quadratic function is symmetric around its own turning point by construction: equal standardised distances on either side of G* correspond to identical fitted values, regardless of whether the linear coefficient is zero. The relevant difference between the two margins is therefore not the shape of the curve around its own turning point, which cannot itself be asymmetric, but where that turning point is located relative to the sample mean gust speed, and how precisely that location can be estimated.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/AppendixH_pressure_minima.json; R05/tables/PERIOD_PHYSICAL_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

For the main customer-impact fit, the gust mean is 9.910222 m/s and the sample standard deviation is 5.279979 m/s. At the fit’s mean physical pressure the conditional minimum is 10.807545 m/s, within the declared p1–p99 gust support. At pressure one training standard deviation below and above that mean, the corresponding points are 9.647571 and 11.967520 m/s. Each point uses the fitted interaction and that model’s own scaling. These algebraic locations are not confidence intervals, physical damage thresholds or established pressure-response effects.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P076 → 4.1 Recovery shape

旧段：For recovery, the near-zero linear term places the fitted minimum close to the sample mean gust under average pressure. That minimum exists mathematically even though the linear coefficient is not significant. We emphasise the positive curvature and do not assign operational meaning to a particular recovery minimum. At other pressure levels, the interaction term shifts its location in the same way as in Equation 5’s generalisation.

前邻：A local audit reproduced the original 500 day-bootstrap fits and examined their coefficients. The quadratic coefficient remained positive, ranging from 0.03659 to 0.16138; the explanation that the interval widened because the denominator approached zero is therefore unsupported. The resampled standardised locations had empirical 2.5th and 97.5th percentiles of -0.1281 and 0.4189. Scaling was re-estimated in every resample, so these locations are measured relative to each resample’s own mean gust and pressure reference. They cannot be treated without further checking as a physical-unit interval at one fixed pressure reference. The previously reported 9.2–12.1 m/s interval is consequently withheld. Appendix H documents the resampling diagnostics and the required conversion. Differences from the Delta approximation [25] may reflect nonlinear estimation and dependence or scaling choices; this audit does not isolate their relative contributions.

后邻：Figure 4 displays the exponentiated fitted log responses under the reference covariates used for the original curves. The asymmetry of the plotted wind range around each minimum makes the high-wind arm extend farther from the minimum; it does not make the fitted function asymmetric about its own vertex. The exponentiated curves are not themselves quadratic on the displayed scale, although their log-scale predictors are quadratic. For exposure the plotted quantity is exp(fitted log(1 + customers)), so it includes the added one and is not a conditional arithmetic mean of customers.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/H0_R1_B1_shape.csv；行键：当前对应总体/目标。

候选英文：

The main recovery curve also has positive fitted gust curvature, with a mean-pressure minimum at approximately 10.13 m/s. Its interpretation depends on the eventual customer covariates and the other reference conditions. A non-significant linear coefficient would not eliminate the mathematical stationary point, and the fitted location is not assigned an operational-trigger interpretation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P077 → 4.1 / Figure 4 caption

旧段：Figure 4 displays the exponentiated fitted log responses under the reference covariates used for the original curves. The asymmetry of the plotted wind range around each minimum makes the high-wind arm extend farther from the minimum; it does not make the fitted function asymmetric about its own vertex. The exponentiated curves are not themselves quadratic on the displayed scale, although their log-scale predictors are quadratic. For exposure the plotted quantity is exp(fitted log(1 + customers)), so it includes the added one and is not a conditional arithmetic mean of customers.

前邻：For recovery, the near-zero linear term places the fitted minimum close to the sample mean gust under average pressure. That minimum exists mathematically even though the linear coefficient is not significant. We emphasise the positive curvature and do not assign operational meaning to a particular recovery minimum. At other pressure levels, the interaction term shifts its location in the same way as in Equation 5’s generalisation.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/*/figure4_curve_data.csv and reference JSON; R05/release_v1/figures/figure04.png；行键：当前对应总体/目标。

候选英文：

Figure 4 presents four gust reference curves for the main and weather-attributed customer-impact and recovery models. At each raw-gust grid value, predictions retain the declared empirical reference distribution of the other covariates and fix pressure at the respective full model’s mean physical value; the displayed quantity is exp(mean fitted η). For customer impact, η refers to ln(1 + C), so the plotted quantity includes the added one. These are exponentiated log-response references, not arithmetic conditional means of customers or hours. No smearing correction or minimum confidence band is applied.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P079 → 4.1 / Figure 4 caption

旧段：Figure 4. Exponentiated fitted log responses under the original reference-covariate settings, with pressure at its standardised mean. (a) exp(fitted log(1 + affected customers)); the vertical marker identifies the point estimate 10.69 m/s. (b) exp(fitted log(restoration duration in hours)). No retransformation correction is applied, and panel (a) does not subtract one. The earlier physical-unit bootstrap band is omitted pending a consistent resample-level conversion (Appendix H).

前邻：

后邻：The recovery model includes standardised log(1 + affected customers) and its square. Their association with duration depends on the sample and on restoration-stage controls. Appendix D reports a positive linear coefficient without stage controls in the main sample, a negative coefficient in the weather-attributed subset, and a sign change after adding a stage control in the development-only analysis. These findings show sensitivity to event composition. A linear coefficient alone does not establish monotonicity across the full customer range, and these regressions do not identify a mediation or dispatch-priority mechanism. Gust curvature was reported to remain positive in the stage-control checks.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/*/figure4_curve_data.csv and reference JSON; R05/release_v1/figures/figure04.png；行键：当前对应总体/目标。

候选英文：

Figure 4 presents four gust reference curves for the main and weather-attributed customer-impact and recovery models. At each raw-gust grid value, predictions retain the declared empirical reference distribution of the other covariates and fix pressure at the respective full model’s mean physical value; the displayed quantity is exp(mean fitted η). For customer impact, η refers to ln(1 + C), so the plotted quantity includes the added one. These are exponentiated log-response references, not arithmetic conditional means of customers or hours. No smearing correction or minimum confidence band is applied.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P080 → 4.1 / Appendix D stage-control sensitivity

旧段：The recovery model includes standardised log(1 + affected customers) and its square. Their association with duration depends on the sample and on restoration-stage controls. Appendix D reports a positive linear coefficient without stage controls in the main sample, a negative coefficient in the weather-attributed subset, and a sign change after adding a stage control in the development-only analysis. These findings show sensitivity to event composition. A linear coefficient alone does not establish monotonicity across the full customer range, and these regressions do not identify a mediation or dispatch-priority mechanism. Gust curvature was reported to remain positive in the stage-control checks.

前邻：Figure 4. Exponentiated fitted log responses under the original reference-covariate settings, with pressure at its standardised mean. (a) exp(fitted log(1 + affected customers)); the vertical marker identifies the point estimate 10.69 m/s. (b) exp(fitted log(restoration duration in hours)). No retransformation correction is applied, and panel (a) does not subtract one. The earlier physical-unit bootstrap band is omitted pending a consistent resample-level conversion (Appendix H).

后邻：The exposure minimum marks a zero slope in the fitted response. Its existence does not demonstrate a structural failure threshold or a change in mechanism. The model conditions on a recorded outage and does not estimate the probability of an outage at a given wind speed. Establishing a response trigger would require additional predictive validation and a decision analysis accounting for the consequences of false alarms and missed events.

段落职责/处理理由：建议现有全期对应物替代旧开发表，不自动重跑旧47840人口；精确系数见所附原始小表。

证据：R04_B1_all_valid_v1/main_R0c/step27 outputs; R04_B1_all_valid_v1/weather_R0c/step27 outputs；行键：当前对应总体/目标。

候选英文：

The current full-period stage-control fits are presented as counterparts to the historical development-sample analyses, with main and weather populations labelled separately. Adding log(stage-row count) changes the conditional customer coefficients, but stage-row count is an eventual record characteristic rather than an established pre-event confounder. A linear coefficient alone does not determine the derivative throughout the log-customer range. These comparisons describe sensitivity to conditioning and do not identify crew prioritisation, mediation or a unique compositional mechanism. The full current coefficient tables should replace whole historical tables only with explicit relabelling of the population.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P082 → 4.2 section title

旧段：4.2 Population-level weight of wind

前邻：The exposure minimum marks a zero slope in the fitted response. Its existence does not demonstrate a structural failure threshold or a change in mechanism. The model conditions on a recorded outage and does not estimate the probability of an outage at a given wind speed. Establishing a response trigger would require additional predictive validation and a decision analysis accounting for the consequences of false alarms and missed events.

后邻：A statistically detectable gust coefficient need not provide substantial predictive information. This section assesses the incremental out-of-fold fit associated with gust and other variable groups. The R-squared measures refer to log-transformed outcomes, rather than to variation in raw customer counts or hours.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

4.2 Paired information increments on the log-outcome scale

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P084 → 4.2 Main information increments

旧段：Nested models add non-gust weather variables to a baseline of regional covariates and additive calendar effects, followed by gust terms. For recovery, affected-customer terms are added in either order relative to gust. Changes in mean fold-level out-of-sample R-squared measure conditional predictive increments, which can depend on the order of addition. In the combined exposure sample, gust contributes 1.07 percentage points to a total R-squared of 2.81 percent. In the combined recovery sample, gust contributes 0.62–0.75 percentage points and customer terms contribute 7.73–7.87 percentage points, with a full-model R-squared of 11.05 percent. Figure 5 shows the gust-before-customers order, in which 7.87/0.62 is approximately 12.7. These increments are descriptive predictive comparisons, not shares of a causal effect or an order-invariant variance decomposition.

前邻：A statistically detectable gust coefficient need not provide substantial predictive information. This section assesses the incremental out-of-fold fit associated with gust and other variable groups. The R-squared measures refer to log-transformed outcomes, rather than to variation in raw customer counts or hours.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv; R04/tables/H0_R1_B1_increments.csv；行键：当前对应总体/目标。

候选英文：

The control block already includes non-gust weather, regional and calendar terms. In the main customer-impact model, adding gust increases pooled OOF R² by 1.24644 percentage points to 0.029621. In recovery, pooled OOF R² is 0.021492 for control, 0.030601 with gust, 0.080595 with customer terms and 0.092016 with both blocks. Thus adding gust after customers contributes 1.142120 percentage points, while adding customers after gust contributes 6.141467 percentage points. These are paired within-population conditional increments, not causal variance shares or an order-invariant decomposition. Figure 5 shows the declared nested models; it contains no separately fitted regional-only baseline.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P086 → Figure 5 caption

旧段：Figure 5. Incremental mean out-of-fold R-squared on the log-outcome scale, final combined samples. Groups are added in the displayed order; the recovery panel adds gust before customer terms. “Customers” denotes standardised log(1 + affected customers) and its square.

前邻：

后邻：Figure 6 compares regional variation in exponentiated fitted log responses, holding the non-regional predictors at the reference settings used in the original map calculation. The exposure and recovery maps do not identify the same high-value districts: their cross-district correlations are -0.780 (Pearson) and -0.758 (Spearman). These are correlations between two model-generated surfaces under fixed reference conditions, not correlations between observed district-level outage outcomes. Both maps use exp(fitted log outcome) without a retransformation correction; the exposure surface therefore refers to 1 + affected customers.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure05.png; R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

Figure 5. Main-population nested model fit on log targets, measured by pooled date-group OOF R². The customer-impact panel compares control with control plus gust. The recovery panel adds gust and then eventual customer terms. Control includes non-gust weather, region and calendar. Arithmetic mean fold R² is reported separately in the accompanying table.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P087 → 4.2 / Figure 6 caption

旧段：Figure 6 compares regional variation in exponentiated fitted log responses, holding the non-regional predictors at the reference settings used in the original map calculation. The exposure and recovery maps do not identify the same high-value districts: their cross-district correlations are -0.780 (Pearson) and -0.758 (Spearman). These are correlations between two model-generated surfaces under fixed reference conditions, not correlations between observed district-level outage outcomes. Both maps use exp(fitted log outcome) without a retransformation correction; the exposure surface therefore refers to 1 + affected customers.

前邻：Figure 5. Incremental mean out-of-fold R-squared on the log-outcome scale, final combined samples. Groups are added in the displayed order; the recovery panel adds gust before customer terms. “Customers” denotes standardised log(1 + affected customers) and its square.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/regional_reference_correlations.json; R04_B1_all_valid_v1/main_*/figure6_regional_reference.csv；行键：当前对应总体/目标。

候选英文：

Figure 6 displays regional references for 111 model-covered LADs under a common calendar weighting and the declared non-regional reference settings. The two model-generated exponentiated surfaces have Pearson correlation -0.832995 and Spearman correlation -0.824070. They are not observed district-level outcome averages. The displayed value is exp(weighted mean η), with ln(1 + C) as the customer-impact target and no subtraction of one. Buckinghamshire’s historical regional proxies remain explicitly marked, and LAD21 geometry does not resolve all LAD23 linkage questions.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P089 → 4.2 / Figure 6 caption

旧段：Figure 6. Regional variation in exponentiated fitted log outcomes under fixed reference settings for non-regional predictors. (a) exp(fitted log(1 + affected customers)). (b) exp(fitted log(restoration duration in hours)). Only the five regional covariates vary across LADs. Colour scales are not conditional arithmetic means; panel (a) includes the added one.

前邻：

后邻：Figure 7 reports the highest divided by the lowest exponentiated fitted value on a 50-point grid spanning the driving variable’s 1st to 99th percentiles. This grid-extrema ratio is not the ratio of predictions at the two percentile endpoints. The reported ratios are 2.79 for gust on the exposure response, 2.37 for gust on recovery, and 5.99 for customer scale on recovery. For the gust curves the minima lie inside the range; for the customer curve the maximum is internal. The exposure ratio describes exp(fitted log(1 + customers)), so it should not be read as a fold change in arithmetic-mean customer counts. Each ratio is a reference-scenario contrast and does not quantify a population variance share.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/regional_reference_correlations.json; R04_B1_all_valid_v1/main_*/figure6_regional_reference.csv；行键：当前对应总体/目标。

候选英文：

Figure 6 displays regional references for 111 model-covered LADs under a common calendar weighting and the declared non-regional reference settings. The two model-generated exponentiated surfaces have Pearson correlation -0.832995 and Spearman correlation -0.824070. They are not observed district-level outcome averages. The displayed value is exp(weighted mean η), with ln(1 + C) as the customer-impact target and no subtraction of one. Buckinghamshire’s historical regional proxies remain explicitly marked, and LAD21 geometry does not resolve all LAD23 linkage questions.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P090 → 4.2 / Figure 7 caption

旧段：Figure 7 reports the highest divided by the lowest exponentiated fitted value on a 50-point grid spanning the driving variable’s 1st to 99th percentiles. This grid-extrema ratio is not the ratio of predictions at the two percentile endpoints. The reported ratios are 2.79 for gust on the exposure response, 2.37 for gust on recovery, and 5.99 for customer scale on recovery. For the gust curves the minima lie inside the range; for the customer curve the maximum is internal. The exposure ratio describes exp(fitted log(1 + customers)), so it should not be read as a fold change in arithmetic-mean customer counts. Each ratio is a reference-scenario contrast and does not quantify a population variance share.

前邻：Figure 6. Regional variation in exponentiated fitted log outcomes under fixed reference settings for non-regional predictors. (a) exp(fitted log(1 + affected customers)). (b) exp(fitted log(restoration duration in hours)). Only the five regional covariates vary across LADs. Colour scales are not conditional arithmetic means; panel (a) includes the added one.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/*/figure7*_ratio.json and figure7_reference.json；行键：当前对应总体/目标。

候选英文：

Figure 7 reports exp(max mean η − min mean η) over each declared 50-point p1–p99 driver grid. The main-population values are 2.885048 for gust and customer impact, 2.586641 for gust and recovery, and 5.642684 for the customer driver and recovery; the weather-population references are shown separately. Grid extrema need not occur at the endpoints. These quantities compare exponentiated log-response references, rather than arithmetic-mean customer or duration responses, causal importance or population variance shares.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P092 → 4.2 / Figure 7 caption

旧段：Figure 7. Maximum/minimum exponentiated fitted value over the 50-point plotting grid (1st–99th percentile range of the driving variable). Ratios are 2.79, 2.37 and 5.99 for gust–exposure, gust–recovery and customers–recovery respectively. The exposure response is on the 1 + customers scale; customer terms in the recovery model use standardised log(1 + customers).

前邻：

后邻：The regional-map ranges in Figure 6 give maximum/minimum ratios of 1.96 for the exponentiated exposure fit and 1.41 for recovery. These are of the same broad order as the gust-driven grid ratios, and smaller than the customer-driven recovery ratio. The comparisons describe fitted variation under different reference scenarios; they do not establish a universal ranking of regional conditions, gust and customer scale.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/*/figure7*_ratio.json and figure7_reference.json；行键：当前对应总体/目标。

候选英文：

Figure 7 reports exp(max mean η − min mean η) over each declared 50-point p1–p99 driver grid. The main-population values are 2.885048 for gust and customer impact, 2.586641 for gust and recovery, and 5.642684 for the customer driver and recovery; the weather-population references are shown separately. Grid extrema need not occur at the endpoints. These quantities compare exponentiated log-response references, rather than arithmetic-mean customer or duration responses, causal importance or population variance shares.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P093 → 4.2 Reference-map scope

旧段：The regional-map ranges in Figure 6 give maximum/minimum ratios of 1.96 for the exponentiated exposure fit and 1.41 for recovery. These are of the same broad order as the gust-driven grid ratios, and smaller than the customer-driven recovery ratio. The comparisons describe fitted variation under different reference scenarios; they do not establish a universal ranking of regional conditions, gust and customer scale.

前邻：Figure 7. Maximum/minimum exponentiated fitted value over the 50-point plotting grid (1st–99th percentile range of the driving variable). Ratios are 2.79, 2.37 and 5.99 for gust–exposure, gust–recovery and customers–recovery respectively. The exposure response is on the 1 + customers scale; customer terms in the recovery model use standardised log(1 + customers).

后邻：The combined-sample recovery comparisons therefore assign a larger predictive increment to customer terms than to gust terms. The exposure model also gains a small positive increment from gust. Section 4.3 examines how these increments change under a weather-attributed sample restriction.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/regional_reference_ranges.csv; R05/tables/SOURCE_DEPENDENCIES.csv；行键：当前对应总体/目标。

候选英文：

Across the 111 displayed LAD references, the maximum/minimum ratios are 1.945442 for customer impact and 1.454100 for recovery. These ratios concern exp(weighted mean η) under the map’s particular reference distribution. Comparing their magnitude with the gust and customer grid ratios mixes different scenario supports, so it cannot establish a universal ranking of regional conditions, gust and customer scale. The map remains descriptive while the regional-proxy reconstruction is pending.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P097 → 4.3 Weather subset

旧段：The recovery model described in Section 3.3 was re-estimated on the subset of incidents for which the Cause Code identifies weather as the direct cause, rather than the combined weather- and asset-related sample used elsewhere in this paper. This subset contains 9,758 incidents, about 16 percent of the main sample. Table 4 compares the two samples directly. The quadratic gust term is close to the same magnitude in both samples and remains significant in both. The marginal contribution of gust to out-of-sample R-squared more than doubles, from between 0.62 and 0.75 percentage points in the main sample to between 1.43 and 1.71 percentage points in the weather-only subset, and now exceeds the marginal contribution of affected customers, which falls to between 1.00 and 1.28 percentage points in this subset. Figure 8 shows this comparison. Figure 8a reports the exposure margin, where the marginal contribution of gust falls from a positive value in the main sample to a small negative value in the weather-only subset, the only instance of a negative bar among all of the figures reported in this paper. Figure 8b reports the recovery margin, where the relative height of the gust and affected-customers bars is reversed between the two samples, from affected customers roughly 12.7 times the height of gust in the main sample to gust slightly exceeding affected customers in the weather-only subset. The weather-attributed recovery sample contains 9,758 incidents; the corresponding exposure sample shown in Figure 8 contains 9,857. Since each sample has its own outcome variance and covariate distribution, the change in R-squared increment is not evidence that a physical wind effect has doubled. The comparison establishes an ordering of reported point estimates between these two variable groups, rather than dominance over all possible predictors.

前邻：This section first restricts the analytical sample to the weather-related Cause Code group and repeats the predictive-contribution comparison. Cause attribution defines a different observed population; it is not assumed to be independent of wind conditions or incident development. A separate descriptive analysis then examines the combined-sample model during seven named storms.

后邻：Table 4. Marginal out-of-sample R-squared, main sample versus weather-only subset.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv; R04/tables/H0_R1_B1_increments.csv；行键：当前对应总体/目标。

候选英文：

The weather-attributed population contains 9,857 eligible incidents for each current model, compared with 60,436 in the main population. For recovery, the pooled OOF increment G|K is 3.579704 percentage points and K|G is 1.507182 percentage points, whereas the main-sample increments are 1.142120 and 6.141467. The ordering of point estimates therefore differs between the two populations. In customer impact, the weather-sample gust increment is positive, at 0.382246 percentage points; the former negative-increment account is not supported by B1. Different outcome variances, support and cause composition prevent a causal or stable cross-population interpretation. Customer terms represent eventual aggregated information, and neither date-group comparison establishes initial-use performance.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P098 → Table 4 caption

旧段：Table 4. Marginal out-of-sample R-squared, main sample versus weather-only subset.

前邻：The recovery model described in Section 3.3 was re-estimated on the subset of incidents for which the Cause Code identifies weather as the direct cause, rather than the combined weather- and asset-related sample used elsewhere in this paper. This subset contains 9,758 incidents, about 16 percent of the main sample. Table 4 compares the two samples directly. The quadratic gust term is close to the same magnitude in both samples and remains significant in both. The marginal contribution of gust to out-of-sample R-squared more than doubles, from between 0.62 and 0.75 percentage points in the main sample to between 1.43 and 1.71 percentage points in the weather-only subset, and now exceeds the marginal contribution of affected customers, which falls to between 1.00 and 1.28 percentage points in this subset. Figure 8 shows this comparison. Figure 8a reports the exposure margin, where the marginal contribution of gust falls from a positive value in the main sample to a small negative value in the weather-only subset, the only instance of a negative bar among all of the figures reported in this paper. Figure 8b reports the recovery margin, where the relative height of the gust and affected-customers bars is reversed between the two samples, from affected customers roughly 12.7 times the height of gust in the main sample to gust slightly exceeding affected customers in the weather-only subset. The weather-attributed recovery sample contains 9,758 incidents; the corresponding exposure sample shown in Figure 8 contains 9,857. Since each sample has its own outcome variance and covariate distribution, the change in R-squared increment is not evidence that a physical wind effect has doubled. The comparison establishes an ordering of reported point estimates between these two variable groups, rather than dominance over all possible predictors.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv; R04/tables/H0_R1_B1_increments.csv；行键：当前对应总体/目标。

候选英文：

Table 4. Paired pooled date-group OOF increments, in percentage points, within the main and weather-attributed populations. Customer-impact entries compare G with control; recovery entries report G|K and K|G. Each within-population comparison uses identical events and folds.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P100 → Figure 8 caption

旧段：Figure 8. Marginal out-of-sample R-squared, main sample versus weather-only subset. (a) Exposure margin. (b) Recovery margin, gust and affected customers shown separately.

前邻：

后邻：For exposure, adding gust reduces mean out-of-fold R-squared by 0.15 percentage points in the weather-attributed sample. This is an unfavourable predictive result for that comparison, although it does not by itself negate a positive fitted quadratic coefficient. Appendix G documents an association between cause classification and gust: the weather-related share rises from 6.89 percent in the lowest gust decile to 56.10 percent in the highest. The share of observations below 10.69 m/s is 63.70 percent in the full exposure sample and 36.83 percent in the weather-attributed subset. This reduced low-gust coverage is a plausible contributor to the exposure result. The descriptive evidence does not establish it as the sole cause, and restricted covariate support can also affect recovery-model estimates.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure08.png; R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

Figure 8. Paired within-population increments in pooled date-group OOF R², in percentage points. The customer-impact panel adds gust to control. The recovery panel reports gust conditional on customers (G|K) and customers conditional on gust (K|G). Main and weather populations are evaluated separately. Bars are point estimates; cross-population ordering stability has not been established.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P101 → 4.3 / Appendix G support

旧段：For exposure, adding gust reduces mean out-of-fold R-squared by 0.15 percentage points in the weather-attributed sample. This is an unfavourable predictive result for that comparison, although it does not by itself negate a positive fitted quadratic coefficient. Appendix G documents an association between cause classification and gust: the weather-related share rises from 6.89 percent in the lowest gust decile to 56.10 percent in the highest. The share of observations below 10.69 m/s is 63.70 percent in the full exposure sample and 36.83 percent in the weather-attributed subset. This reduced low-gust coverage is a plausible contributor to the exposure result. The descriptive evidence does not establish it as the sole cause, and restricted covariate support can also affect recovery-model estimates.

前邻：Figure 8. Marginal out-of-sample R-squared, main sample versus weather-only subset. (a) Exposure margin. (b) Recovery margin, gust and affected customers shown separately.

后邻：Storm periods provide a complementary view of fitted performance. Previous outage research has used named storms for model evaluation [5], but the comparison here is descriptive because the fitted model includes these incidents. The seven storms are Arwen, Dudley, Eunice, Franklin, Babet, Ciarán and Henk. Their selected windows span 27 days, or 2.46 percent of the study period, and contain 8.15 percent of final-sample incidents and 14.72 percent of affected-customer counts. Relative to the whole-period daily average, incident and customer-count concentrations are approximately 3.3 and 6 times as high respectively.

段落职责/处理理由：相邻G段落可合并；不要重复三次同一数字。

证据：R04/tables/AppendixG_main_gust_deciles.csv; R04/tables/AppendixG_low_gust_support.csv; R05/OOF_SCORE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

In the current main-population gust deciles, the weather-attributed share is 6.9338% in the lowest bin and 57.0714% in the highest. At the main customer-impact reference minimum of 10.8075 m/s, 65.0291% of main incidents and 37.8817% of weather-attributed incidents fall below the reference. These within-population proportions describe different support distributions; they do not compare otherwise identical incidents. The weather customer-impact gust increment is now positive, so these descriptions should not be offered as explanations of the superseded negative increment. Cause assignment and limited support remain relevant uncertainties for both outcomes.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P102 → 4.3 Named-window burden

旧段：Storm periods provide a complementary view of fitted performance. Previous outage research has used named storms for model evaluation [5], but the comparison here is descriptive because the fitted model includes these incidents. The seven storms are Arwen, Dudley, Eunice, Franklin, Babet, Ciarán and Henk. Their selected windows span 27 days, or 2.46 percent of the study period, and contain 8.15 percent of final-sample incidents and 14.72 percent of affected-customer counts. Relative to the whole-period daily average, incident and customer-count concentrations are approximately 3.3 and 6 times as high respectively.

前邻：For exposure, adding gust reduces mean out-of-fold R-squared by 0.15 percentage points in the weather-attributed sample. This is an unfavourable predictive result for that comparison, although it does not by itself negate a positive fitted quadratic coefficient. Appendix G documents an association between cause classification and gust: the weather-related share rises from 6.89 percent in the lowest gust decile to 56.10 percent in the highest. The share of observations below 10.69 m/s is 63.70 percent in the full exposure sample and 36.83 percent in the weather-attributed subset. This reduced low-gust coverage is a plausible contributor to the exposure result. The descriptive evidence does not establish it as the sole cause, and restricted covariate support can also affect recovery-model estimates.

后邻：The finalised exposure and recovery models, unchanged from Section 4.1, were then used to predict outcomes for the incidents recorded during each of the seven storms, using the gust and other covariate values actually observed during that storm. Figure 9 compares these predictions against the observed outcomes. For the exposure margin, Figure 9a, the predicted values are systematically higher than the observed values for incidents with a low observed customer count, visible as vertical clusters of points sitting well above the reference line at the low end of the horizontal axis. Predictions come closer to the reference line only among incidents with a comparatively high observed customer count. For the recovery margin, Figure 9b, the points are more evenly distributed around the reference line, without the same one-sided pattern, although two of the seven storms, Eunice and Franklin, each form a distinct local cluster: Eunice’s cluster sits slightly above the reference line, and Franklin’s sits below it.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/storm_statistics.csv; R03/configs/storm_windows.json；行键：当前对应总体/目标。

候选英文：

The seven selected named-storm windows sum to 27 window-days but cover 25 unique UTC dates. Their union contains 4,452 main-sample incidents (7.3665%) and 745,372 aggregated customers (13.2579%). Events that lie in overlapping windows are counted once in these union totals. The separately tabulated per-window sums count repeated membership and must not be substituted for union totals. These statistics describe burdens within selected calendar windows, not an independently verified inventory of all physically storm-caused incidents.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P103 → 4.3 / Figure 9 caption

旧段：The finalised exposure and recovery models, unchanged from Section 4.1, were then used to predict outcomes for the incidents recorded during each of the seven storms, using the gust and other covariate values actually observed during that storm. Figure 9 compares these predictions against the observed outcomes. For the exposure margin, Figure 9a, the predicted values are systematically higher than the observed values for incidents with a low observed customer count, visible as vertical clusters of points sitting well above the reference line at the low end of the horizontal axis. Predictions come closer to the reference line only among incidents with a comparatively high observed customer count. For the recovery margin, Figure 9b, the points are more evenly distributed around the reference line, without the same one-sided pattern, although two of the seven storms, Eunice and Franklin, each form a distinct local cluster: Eunice’s cluster sits slightly above the reference line, and Franklin’s sits below it.

前邻：Storm periods provide a complementary view of fitted performance. Previous outage research has used named storms for model evaluation [5], but the comparison here is descriptive because the fitted model includes these incidents. The seven storms are Arwen, Dudley, Eunice, Franklin, Babet, Ciarán and Henk. Their selected windows span 27 days, or 2.46 percent of the study period, and contain 8.15 percent of final-sample incidents and 14.72 percent of affected-customer counts. Relative to the whole-period daily average, incident and customer-count concentrations are approximately 3.3 and 6 times as high respectively.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/main_*/figure9_*_events.csv; R05/release_v1/figures/figure09.png；行键：当前对应总体/目标。

候选英文：

Figure 9 compares observed log targets with predicted η for the 4,452 unique main-sample incidents in the union of named windows. The upper row uses the full fitted model, whose training population includes these events; the lower row uses each event’s held-out-date prediction. Customer impact is shown as ln(1 + C) and recovery as ln(D/h), with no second log transform. A date-OOF identity prevents evaluation on that event’s training date, but does not remove every part of a multi-day storm from training. The four panels are therefore descriptive and date-group diagnostics, not complete storm-process validation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P105 → 4.3 / Figure 9 caption

旧段：Figure 9. Combined-sample fitted versus observed log outcomes during the seven named storms, with a 45-degree reference line. (a) log(1 + affected customers). (b) log(restoration duration). These events also contributed to fitting the model; the plot is not an out-of-sample storm validation.

前邻：

后邻：The fitted-observed correlation for each margin was also computed separately within each storm and compared against the correlation for the full sample. For the exposure margin, the full-sample correlation is 0.179, and the seven storm-specific correlations range from 0.116 to 0.341, without a consistent direction relative to the full-sample value. For the recovery margin, the full-sample correlation is 0.343, and all seven storm-specific correlations fall below this value, ranging from 0.084 to 0.317. The weakest of these, for Storm Dudley, is not statistically distinguishable from zero.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04_B1_all_valid_v1/main_*/figure9_*_events.csv; R05/release_v1/figures/figure09.png；行键：当前对应总体/目标。

候选英文：

Figure 9 compares observed log targets with predicted η for the 4,452 unique main-sample incidents in the union of named windows. The upper row uses the full fitted model, whose training population includes these events; the lower row uses each event’s held-out-date prediction. Customer impact is shown as ln(1 + C) and recovery as ln(D/h), with no second log transform. A date-OOF identity prevents evaluation on that event’s training date, but does not remove every part of a multi-day storm from training. The four panels are therefore descriptive and date-group diagnostics, not complete storm-process validation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P106 → 4.3 Correlations

旧段：The fitted-observed correlation for each margin was also computed separately within each storm and compared against the correlation for the full sample. For the exposure margin, the full-sample correlation is 0.179, and the seven storm-specific correlations range from 0.116 to 0.341, without a consistent direction relative to the full-sample value. For the recovery margin, the full-sample correlation is 0.343, and all seven storm-specific correlations fall below this value, ranging from 0.084 to 0.317. The weakest of these, for Storm Dudley, is not statistically distinguishable from zero.

前邻：Figure 9. Combined-sample fitted versus observed log outcomes during the seven named storms, with a 45-degree reference line. (a) log(1 + affected customers). (b) log(restoration duration). These events also contributed to fitting the model; the plot is not an out-of-sample storm validation.

后邻：The lower within-storm recovery correlations show that the model describes only a limited part of event-to-event variation during these periods. Possible explanations include restricted covariate ranges and unmeasured restoration demands, such as concurrent incidents or crew availability. These mechanisms are not tested here. Weak storm-period fitted performance is compatible with limited overall fit, but it is not logically implied by the population-level gust increment and does not establish a change in gust’s relative contribution.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/storm_prediction_correlations.csv; keys main,full_fit,ALL versus seven named windows；行键：当前对应总体/目标。

候选英文：

Using full-fit η and observed log targets, the main-sample correlations are 0.184423 for customer impact and 0.315679 for recovery. Across the seven named windows, they range from 0.116005 to 0.345812 and from 0.077678 to 0.307466, respectively. These are within-window descriptive associations; no significance claim is inferred from the smallest correlation. The accompanying table separates full-fit and date-OOF correlations for both populations. Correlation does not quantify engineering error or calibration, and neither prediction identity supplies a second independent test of the gust/customer contribution ordering.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P108 → 4.3 Interpretation

旧段：The reversal in Table 4 is supported by the cause-based predictive comparisons. The storm analysis provides complementary evidence about fitted performance during named events and does not independently compute the same contribution reversal. An out-of-sample storm-level ablation comparison would be needed to examine that question directly.

前邻：The lower within-storm recovery correlations show that the model describes only a limited part of event-to-event variation during these periods. Possible explanations include restricted covariate ranges and unmeasured restoration demands, such as concurrent incidents or crew availability. These mechanisms are not tested here. Weak storm-period fitted performance is compatible with limited overall fit, but it is not logically implied by the population-level gust increment and does not establish a change in gust’s relative contribution.

后邻：4.4 Retrospective temporal and clustering checks

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.md; REMAINING_VALIDATION.md；行键：当前对应总体/目标。

候选英文：

The paired cause-population comparisons establish the reported conditional point increments under the frozen date folds. Named-window plots describe a different aspect of model performance and do not independently corroborate the ordering difference. Paired uncertainty and a protocol that holds out entire weather processes are needed before the ordering can be described as stable across these settings.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P111 → 4.4 Retrospective periods

旧段：The reported exposure quadratic term is positive in both periods, while the linear term changes sign relative to each period’s own mean gust and pressure. The earlier-period exposure minimum is 12.13 m/s, compared with 10.69 m/s in the combined sample. For recovery, the development row in Figure 10 is an inverse-variance-weighted summary of five cross-validation fits, with a value of 0.0660; it is not a single full-development-sample regression. The reported later-period coefficient is approximately 0.064, and the combined-sample coefficient is 0.079237. These results are consistent in sign, but the differing estimation procedures must be recognised. Since cross-validation training sets overlap, the nominal interval previously attached to their weighted summary is omitted rather than treated as an independent-fit confidence interval.

前邻：Sections 4.1 to 4.3 use the final combined sample or explicitly identified cause subsets. This section compares earlier- and later-period estimates and examines alternative standard errors for the combined-sample fits. Because both periods informed early model development (Appendix E), the temporal results are retrospective sensitivity evidence, not confirmation on a previously untouched sample.

后邻：Figure 10 distinguishes the development-fold summaries from the later-period fits and combined-sample clustering results. Mean gust is approximately 9.65 m/s in the earlier period and 10.77 m/s in the later period; standard deviations are approximately 5.21 and 5.17 m/s. The standard-deviation difference is small, but direct comparison of standardised coefficients is still approximate, and the linear terms refer to different physical wind and pressure reference conditions. Appendix H reports the available scaling values. The two combined-sample rows for each outcome have identical point estimates; only the covariance estimator differs.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/PERIOD_PHYSICAL_AUDIT.csv; R04/tables/period_comparison.csv; R05/COVARIANCE_AND_PERIOD_AUDIT.md；行键：当前对应总体/目标。

候选英文：

The period comparison now uses one full fit per outcome and population in each period, with a verified equivalent full-rank calendar basis and each fit’s own training scale. At a fixed main-sample mean physical pressure, the main customer-impact quadratic coefficient is 0.003204 in the earlier period and 0.006284 in the later period, in (m/s)⁻². The corresponding minima are 12.1357 and 9.7775 m/s, compared with 10.8075 m/s for the full period. These estimates replace the mixed full-fit and inverse-variance-weighted CV summaries. Figure 10 reports physical quadratic point estimates without intervals; its physical-term table uses LAD standard errors. Both periods informed historical development, so same-sign curvature is not independent confirmation of stable shape or location.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P112 → 4.4 Retrospective periods

旧段：Figure 10 distinguishes the development-fold summaries from the later-period fits and combined-sample clustering results. Mean gust is approximately 9.65 m/s in the earlier period and 10.77 m/s in the later period; standard deviations are approximately 5.21 and 5.17 m/s. The standard-deviation difference is small, but direct comparison of standardised coefficients is still approximate, and the linear terms refer to different physical wind and pressure reference conditions. Appendix H reports the available scaling values. The two combined-sample rows for each outcome have identical point estimates; only the covariance estimator differs.

前邻：The reported exposure quadratic term is positive in both periods, while the linear term changes sign relative to each period’s own mean gust and pressure. The earlier-period exposure minimum is 12.13 m/s, compared with 10.69 m/s in the combined sample. For recovery, the development row in Figure 10 is an inverse-variance-weighted summary of five cross-validation fits, with a value of 0.0660; it is not a single full-development-sample regression. The reported later-period coefficient is approximately 0.064, and the combined-sample coefficient is 0.079237. These results are consistent in sign, but the differing estimation procedures must be recognised. Since cross-validation training sets overlap, the nominal interval previously attached to their weighted summary is omitted rather than treated as an independent-fit confidence interval.

后邻：

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/tables/PERIOD_PHYSICAL_AUDIT.csv; R04/tables/period_comparison.csv; R05/COVARIANCE_AND_PERIOD_AUDIT.md；行键：当前对应总体/目标。

候选英文：

The period comparison now uses one full fit per outcome and population in each period, with a verified equivalent full-rank calendar basis and each fit’s own training scale. At a fixed main-sample mean physical pressure, the main customer-impact quadratic coefficient is 0.003204 in the earlier period and 0.006284 in the later period, in (m/s)⁻². The corresponding minima are 12.1357 and 9.7775 m/s, compared with 10.8075 m/s for the full period. These estimates replace the mixed full-fit and inverse-variance-weighted CV summaries. Figure 10 reports physical quadratic point estimates without intervals; its physical-term table uses LAD standard errors. Both periods informed historical development, so same-sign curvature is not independent confirmation of stable shape or location.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P114 → Figure 10 caption

旧段：Figure 10. Gust quadratic-coefficient summaries and estimates. Development rows are descriptive summaries of overlapping cross-validation fits and are shown without inferential intervals. Later-period rows retain the reported model intervals; the other two rows use the final combined sample with LAD or LAD-and-date clustered standard errors. Scaling is sample-specific. These are retrospective checks, not four independent validations.

前邻：

后邻：The later period spans six months within autumn and winter rather than a full annual cycle. Sample size, seasonal composition and sample-specific scaling can affect precision and coefficient comparisons, but these observations do not establish the cause of a changed estimate. The temporal analyses provide evidence of a consistently positive quadratic term within the fitted specifications. They do not verify a stable physical minimum, an unchanged full response function or external predictive validity.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/release_v1/figures/figure10.png; R05/COVARIANCE_CONSUMERS.csv；行键：当前对应总体/目标。

候选英文：

Figure 10. Physical gust-quadratic point estimates from eight retrospective period fits: two outcomes, main and weather populations, and earlier and later periods. Every estimate uses its own training scale and the equivalent supported calendar basis. The plot contains no confidence intervals and no inverse-variance-weighted CV estimate. LAD physical-term standard errors and the restricted use of non-PSD period two-way covariances are documented separately.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P116 → 4.4 / Appendix F covariance

旧段：For the final combined sample, the recovery quadratic term remains significant under two-way clustering (p=5.4×10−22, compared with 2.8×10−36 under LAD clustering). The exposure quadratic term also remains significant. The exposure linear term and both gust-pressure interactions are no longer significant under two-way clustering; the recovery linear term remains non-significant. Appendix F gives the reported non-calendar coefficients. Re-estimation on earlier versions of substantially overlapping data is not counted as independent corroboration.

前邻：The later period spans six months within autumn and winter rather than a full annual cycle. Sample size, seasonal composition and sample-specific scaling can affect precision and coefficient comparisons, but these observations do not establish the cause of a changed estimate. The temporal analyses provide evidence of a consistently positive quadratic term within the fitted specifications. They do not verify a stable physical minimum, an unchanged full response function or external predictive validity.

后邻：5. Conclusion

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R04/tables/Tables3_F_complete_coefficients.csv; R05/tables/PERIOD_COVARIANCE_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

In the full main recovery model, the quadratic gust coefficient has p-values from a normal reference 1.131e-42 under LAD CR1 and 8.217e-26 under CR1 clustering by both LAD and date. The corresponding customer-impact values are 5.734e-37 and 0.0009155. The covariance table reports the same coefficients with these alternative uncertainty calculations. This result is specific to the full-period fits and should not be extended to unrestricted joint inference using the six non-PSD period two-way matrices. Neither changing covariance nor refitting overlapping data creates independent confirmation.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P118 → 5 Conclusion or proposed 6 Conclusion

旧段：The analysis finds positive quadratic gust terms in models of log-transformed customer counts and restoration spans among recorded weather- and asset-related outages. The sign of this curvature recurs in the reported sensitivity checks, whereas fitted minima depend on the reference conditions and sample. The exposure point estimate is approximately 10.69 m/s at average pressure in the combined sample. Its physical-unit uncertainty requires a consistent resample-level treatment, and the temporal evidence is retrospective rather than independent.

前邻：5. Conclusion

后邻：Gust adds modest predictive information on the log-outcome scale. In the combined recovery sample its increment is below that of customer terms, while the reported ordering reverses in the weather-attributed subset. This comparison concerns two specified variable groups and depends on the population and evaluation setup; it does not show that wind dominates all determinants or identify causal variance shares. Storm-period plots describe fitted performance and provide no second independent test of that ordering.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.md; R05/tables/CUBIC_PAIRED_AUDIT.csv; R05/tables/PERIOD_PHYSICAL_AUDIT.csv；行键：当前对应总体/目标。

候选英文：

The current models describe positive quadratic gust curvature in log-transformed customer impact and restoration span among eligible recorded incidents. The main customer-impact minimum is approximately 10.8 m/s at the declared mean-pressure reference. Its interpretation remains conditional on the specification, support and source proxies: existing cubic gains and differing period estimates do not establish a stable physical threshold. No current physical-unit confidence interval or operational trigger is claimed.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P119 → 5 Conclusion or proposed 6 Conclusion

旧段：Gust adds modest predictive information on the log-outcome scale. In the combined recovery sample its increment is below that of customer terms, while the reported ordering reverses in the weather-attributed subset. This comparison concerns two specified variable groups and depends on the population and evaluation setup; it does not show that wind dominates all determinants or identify causal variance shares. Storm-period plots describe fitted performance and provide no second independent test of that ordering.

前邻：The analysis finds positive quadratic gust terms in models of log-transformed customer counts and restoration spans among recorded weather- and asset-related outages. The sign of this curvature recurs in the reported sensitivity checks, whereas fitted minima depend on the reference conditions and sample. The exposure point estimate is approximately 10.69 m/s at average pressure in the combined sample. Its physical-unit uncertainty requires a consistent resample-level treatment, and the temporal evidence is retrospective rather than independent.

后邻：The fitted minimum describes a smooth response-function feature, not the onset of structural failure or a validated operational trigger. Translating it into a response rule would require evaluation on previously unused events, an appropriately defined physical-unit uncertainty interval and an assessment of decision costs. The present estimates therefore support descriptive understanding of recorded outage consequences rather than a recommended wind-speed trigger.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/OOF_SCORE_AUDIT.csv; REMAINING_VALIDATION.md；行键：当前对应总体/目标。

候选英文：

Gust contributes a modest positive increment to main-sample log-target OOF fit. In recovery, eventual customer information has the larger conditional increment in the main population, while the ordering of point estimates differs in the weather-attributed population. These are paired descriptive information comparisons within specified populations. Their uncertainty, transfer across independent processes and usefulness before eventual customer counts are known remain unresolved.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P122 → 5 Discussion / limitations and validation

旧段：Several limitations remain. Early modelling used observations from both temporal periods, and the later period covers only one autumn–winter window. The original-code-to-category mapping and the meaning of zero-customer records require fuller documentary verification. Stage-count stratification does not identify the causal origin of the customer–duration relationship. Figure 4 and Figure 6 show uncorrected exponentiated log fits rather than conditional arithmetic means, and the available global residual retransformation factors do not establish a valid conditional-mean correction across all covariate values. These boundaries limit interpretation of both absolute predictions and generalisation.

前邻：The customer–duration association changes with restoration-stage controls and cause restriction (Appendix D). Prior work has also examined the relation between outage scale and recovery [26]. Differences in network conditions, incident definitions and restoration processes may contribute to different patterns across studies. Crew prioritisation is one possible explanation, but the present regressions do not identify it.

后邻：Further work should reconstruct bootstrap minima in physical units at a consistent pressure reference, obtain directly comparable temporal fits, and evaluate predictive performance on unused storm events or future data. Additional checks should assess cause-based support differences, missing first-stage records, concurrent restoration demand and alternative model specifications. A complete residual-diagnostic and alternative-distribution comparison should accompany that work.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/PROVENANCE_AUDIT.md; REMAINING_VALIDATION.md；行键：当前对应总体/目标。

候选英文：

The analysis remains limited by record-based onset and location proxies, incomplete cause-code and historical weather-product provenance, and unresolved regional boundary and aggregation conditions. Buckinghamshire’s proxies will be reconstructed from the available LSOA rate and population table with compatible geometry and a declared spatial-weight rule before dependent validation fits are fixed. Date grouping does not ensure independence across multi-day processes. The remaining validation should prioritise shape and tail sensitivity, paired contribution uncertainty, complete-process performance and engineering-scale error or calibration. Existing residual, cubic, GLM and comparable period products are now available; they should not be listed as wholly missing. New minimum bootstrap calculations are conditional on the surviving shape claim and a frozen physical-reference estimand.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：

## D-P123 → 5 Discussion / limitations and validation

旧段：Further work should reconstruct bootstrap minima in physical units at a consistent pressure reference, obtain directly comparable temporal fits, and evaluate predictive performance on unused storm events or future data. Additional checks should assess cause-based support differences, missing first-stage records, concurrent restoration demand and alternative model specifications. A complete residual-diagnostic and alternative-distribution comparison should accompany that work.

前邻：Several limitations remain. Early modelling used observations from both temporal periods, and the later period covers only one autumn–winter window. The original-code-to-category mapping and the meaning of zero-customer records require fuller documentary verification. Stage-count stratification does not identify the causal origin of the customer–duration relationship. Figure 4 and Figure 6 show uncorrected exponentiated log fits rather than conditional arithmetic means, and the available global residual retransformation factors do not establish a valid conditional-mean correction across all covariate values. These boundaries limit interpretation of both absolute predictions and generalisation.

后邻：Reconstructing incident-level outcomes from stage-level records and separating curve description from predictive evaluation can be applied to other operators with comparable reporting systems. Transfer requires verification of each operator’s field definitions and reporting conventions, as well as fresh evaluation of model behaviour in that setting.

段落职责/处理理由：用当前证据替换原稿对象/口径或推断范围；整段改写避免只换数留下失效逻辑。

证据：R05/PROVENANCE_AUDIT.md; REMAINING_VALIDATION.md；行键：当前对应总体/目标。

候选英文：

The analysis remains limited by record-based onset and location proxies, incomplete cause-code and historical weather-product provenance, and unresolved regional boundary and aggregation conditions. Buckinghamshire’s proxies will be reconstructed from the available LSOA rate and population table with compatible geometry and a declared spatial-weight rule before dependent validation fits are fixed. Date grouping does not ensure independence across multi-day processes. The remaining validation should prioritise shape and tail sensitivity, paired contribution uncertainty, complete-process performance and engineering-scale error or calibration. Existing residual, cubic, GLM and comparable period products are now available; they should not be listed as wholly missing. New minimum bootstrap calculations are conditional on the surviving shape claim and a frozen physical-reference estimand.

衔接检查：从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。

未决：


## 四轮审阅与功能完整性

论证轮：RQ—方法—结果—解释对齐，反向证据（三阶有正增量、天气E转正、D1 pooled下降）已进入主线。证据轮：246绑定有逐值/行键/总体/单位，11组合段落完整，历史Bootstrap不充当B1区间。文字轮：区分stage number/time、span/CML、pooled/mean-fold、curve/reference/arithmetic mean，不新增机制或外部引文事实。交付轮：候选原文与邻段并列，Word SHA锁定，所有图件明确消费者。

FUNCTIONAL-COMPLETENESS RETROSPECTIVE：覆盖R05候选及现有计算，非整篇Word最终校对；项目台账为权威状态，用户的R05范围高于建议技能；observational/computational设计检查及R04-review项目增量适用。六章为reviewer preference，其余数据/运行身份为project state，配对/训练内处理为design requirement，无期刊专属overlay。当前缺口为来源、形状、贡献不确定性、完整过程和工程尺度；没有获准的科学豁免。就进入V协议准备为conditional_for_V，尚非投稿就绪。
