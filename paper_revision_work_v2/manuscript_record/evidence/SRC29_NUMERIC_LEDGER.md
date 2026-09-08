# R04数值总账

本总账绑定当前R02数据、冻结R04_primary配置与各实际生产者；基线清单给完整SHA。Word位置来自已冻结D/A索引，不改Word。空值表示未提供/未定义/未运行，绝非0。

| 旧定位 | 旧值/说法 | 当前值 | 单位 | 目标/人群 | n | 当前来源 | MR | CL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-P002/039 | 60453/60437/59834 | 60436 E0；60436 R0c | events | main | 60436 | core_actual_acceptance.json | MR01/09/10 | CL01 |
| D-P017 | 9.87 / 5.22 | 9.910222388 / 5.279979383 | m/s mean/SD | main E0 | 60436 | main_E0/full_model.json | MR05/11 | CL01/02 |
| D-P030；A-P018 | 47.13→93.02；1.97 | 47.128334106→93.025729698；1.973881137 | customers / ratio | lowest stage number | 60436 | customer_aggregation_comparison.json | MR04 | CL01 |
| 同上定义核查 | earliest stage文字混用 | 31.121963730→93.025729698；2.989070050 | customers / ratio | earliest record time | 60436 | customer_aggregation_comparison.json | MR04 | CL01 |
| D-P071/073；摘要 | 10.69/10.7 | 10.807545499 | m/s | main E0; mean physical pressure | 60436 | conditional_minimum_no_CI.json | MR18/19 | CL02 |
| D-T04 weather E0 | −0.15 | +0.382246343 | R²百分点 | weather E0 | 9857 | contributions.json | MR12/13/18 | CL03 |
| D-T04 main R0c | gust0.62–0.75；customers7.73–7.87 | G/K1.142120140；K/G6.141466554 | R²百分点 | main R0c | 60436 | contributions.json | MR12/13 | CL03 |
| D-T04 weather R0c | gust1.43–1.71；customers1.00–1.28 | G/K3.579703969；K/G1.507182044 | R²百分点 | weather R0c | 9857 | contributions.json | MR12/13 | CL03 |
| D-P102 | 27日；8.15%；14.72% | 25唯一日；7.366470316%；13.257885884% | days / events% / customers% | main unique storm | 60436 | storm_statistics.csv | MR14/16 | CL04 |
| D-P006 | 1601；101LAD；376712；52.7h | 见storm_LAD_details按main/weather分别取数，旧句混用群体须重写 | events/LAD/customers/h | Eunice | 未提供/不适用 | storm_LAD_details.csv | MR05/16 | CL01/04 |
| MR18三阶旧反证 | E0 ΔR²≈0.001441 | E0 +0.001931639；R0c +0.000498187 | R² | main paired OOF | 60436 | supplement_summary.csv | MR18 | CL02 |
| A-T12；A-P086 | 500次旧bootstrap；9.2–12.1 | 未运行；无合格B1最低点CI | not available | B1 minima | 未提供/不适用 | instruction scope | MR19/20 | CL02 |

## 当前核心完整数字

| version | group | target | block | n | pooled_R2 | mean_fold_R2 | SSE | SST | scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | main | E0 | control | 60436 | 0.017157091 | 0.016332043 | 242119.38 | 246345.96 | log1p_C |
| B1 | main | E0 | G | 60436 | 0.029621456 | 0.028723925 | 239048.84 | 246345.96 | log1p_C |
| B1 | main | R0c | control | 60436 | 0.021492205 | 0.019232831 | 118120.17 | 120714.59 | log_D |
| B1 | main | R0c | G | 60436 | 0.030601167 | 0.02759156 | 117020.58 | 120714.59 | log_D |
| B1 | main | R0c | K | 60436 | 0.080594631 | 0.078971139 | 110985.64 | 120714.59 | log_D |
| B1 | main | R0c | GK | 60436 | 0.092015832 | 0.089448842 | 109606.94 | 120714.59 | log_D |
| B1 | weather | E0 | control | 9857 | 0.020465821 | 0.015129311 | 47484.461 | 48476.574 | log1p_C |
| B1 | weather | E0 | G | 9857 | 0.024288284 | 0.020016566 | 47299.161 | 48476.574 | log1p_C |
| B1 | weather | R0c | control | 9857 | 0.19219972 | 0.12104927 | 18781.371 | 23250.018 | log_D |
| B1 | weather | R0c | G | 9857 | 0.22249889 | 0.14922109 | 18076.914 | 23250.018 | log_D |
| B1 | weather | R0c | K | 9857 | 0.20177367 | 0.13196143 | 18558.776 | 23250.018 | log_D |
| B1 | weather | R0c | GK | 9857 | 0.23757071 | 0.16554521 | 17726.494 | 23250.018 | log_D |

## 物理参考、最低点与支持

| version | group | target | n | beta_gust | beta_gust2 | beta_interaction | gust_mean | gust_sd | physical_quadratic | conditional_minimum_ms | minimum_status | CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | main | E0 | 60436 | -0.03603576 | 0.10601982 | -0.04658362 | 9.9102224 | 5.2799794 | 0.0038029674 | 10.807545 | conditional_fitted_minimum | not_estimated |
| B1 | main | R0c | 60436 | -0.0073789491 | 0.087842132 | 0.020822883 | 9.9102224 | 5.2799794 | 0.0031509275 | 10.131988 | conditional_fitted_minimum | not_estimated |
| B1 | weather | E0 | 9857 | 0.13294047 | 0.045698353 | -0.13649101 | 14.386994 | 7.2785135 | 0.00086261135 | 3.8000811 | conditional_fitted_minimum | not_estimated |
| B1 | weather | R0c | 9857 | 0.26334772 | 0.11363397 | 0.069537148 | 14.386994 | 7.2785135 | 0.0021449777 | 5.9529843 | conditional_fitted_minimum | not_estimated |

## 风暴总体与分母

| population | window | events | denominator_events | events_pct | customers_sum | customers_nonmissing_n | denominator_customers_sum | customers_pct | duration_mean_hours | gust_max_ms | overlap_events | summed_window_memberships | UTC_window_days_unique | timezone | end_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| event_master | UNIQUE_ANY | 7300 | 135025 | 5.4064062 | 1090242 | 7297 | 10196761 | 10.692042 | 26.347493 | 39.400002 | 702 | 8002 | 25 | UTC | exclusive next-day midnight |
| main_candidate_E0 | UNIQUE_ANY | 4452 | 60436 | 7.3664703 | 745372 | 4452 | 5622103 | 13.257886 | 34.480608 | 39.400002 | 479 | 4931 | 25 | UTC | exclusive next-day midnight |
| main_candidate_R0c | UNIQUE_ANY | 4452 | 60436 | 7.3664703 | 745372 | 4452 | 5622103 | 13.257886 | 34.480608 | 39.400002 | 479 | 4931 | 25 | UTC | exclusive next-day midnight |
| weather_candidate_E0 | UNIQUE_ANY | 2750 | 9857 | 27.898955 | 622601 | 2750 | 1892162 | 32.904212 | 43.147982 | 39.400002 | 356 | 3106 | 25 | UTC | exclusive next-day midnight |
| weather_candidate_R0c | UNIQUE_ANY | 2750 | 9857 | 27.898955 | 622601 | 2750 | 1892162 | 32.904212 | 43.147982 | 39.400002 | 356 | 3106 | 25 | UTC | exclusive next-day midnight |
| main_E0_actual_fit | UNIQUE_ANY | 4452 | 60436 | 7.3664703 | 745372 | 4452 | 5622103 | 13.257886 | 34.480608 | 39.400002 | 479 | 4931 | 25 | UTC | exclusive next-day midnight |
| main_R0c_actual_fit | UNIQUE_ANY | 4452 | 60436 | 7.3664703 | 745372 | 4452 | 5622103 | 13.257886 | 34.480608 | 39.400002 | 479 | 4931 | 25 | UTC | exclusive next-day midnight |
| weather_E0_actual_fit | UNIQUE_ANY | 2750 | 9857 | 27.898955 | 622601 | 2750 | 1892162 | 32.904212 | 43.147982 | 39.400002 | 356 | 3106 | 25 | UTC | exclusive next-day midnight |
| weather_R0c_actual_fit | UNIQUE_ANY | 2750 | 9857 | 27.898955 | 622601 | 2750 | 1892162 | 32.904212 | 43.147982 | 39.400002 | 356 | 3106 | 25 | UTC | exclusive next-day midnight |

## Eunice及所有窗口群体核对

| population | window | events | LAD | customers | duration_mean_hours | gust_max_ms |
| --- | --- | --- | --- | --- | --- | --- |
| event_master | Arwen | 574 | 106 | 39696 | 8.7127178 | 22.200001 |
| event_master | Dudley | 616 | 107 | 51771 | 9.4588745 | 27.700001 |
| event_master | Eunice | 2291 | 109 | 592950 | 47.844689 | 39.400002 |
| event_master | Franklin | 1631 | 109 | 203436 | 38.982679 | 32.200001 |
| event_master | Babet | 1089 | 112 | 85997 | 11.773095 | 24 |
| event_master | Ciaran | 990 | 110 | 107666 | 10.617912 | 32.5 |
| event_master | Henk | 811 | 108 | 94503 | 12.410707 | 29.700001 |
| main | Arwen | 270 | 87 | 25061 | 11.019012 | 22.200001 |
| main | Dudley | 291 | 90 | 30092 | 15.853666 | 27.700001 |
| main | Eunice | 1659 | 101 | 395470 | 54.563984 | 39.400002 |
| main | Franklin | 1132 | 99 | 165963 | 45.924588 | 32.200001 |
| main | Babet | 509 | 106 | 56696 | 14.911067 | 22.799999 |
| main | Ciaran | 576 | 106 | 69801 | 14.302459 | 32.5 |
| main | Henk | 494 | 95 | 68536 | 17.088934 | 29.6 |
| weather | Arwen | 81 | 40 | 14800 | 5.5179012 | 22.200001 |
| weather | Dudley | 121 | 45 | 22156 | 18.456336 | 27.700001 |
| weather | Eunice | 1398 | 79 | 364131 | 59.621507 | 39.400002 |
| weather | Franklin | 884 | 69 | 151854 | 49.939027 | 32.200001 |
| weather | Babet | 80 | 39 | 15516 | 7.1810417 | 22.799999 |
| weather | Ciaran | 206 | 45 | 49112 | 8.8536408 | 32.5 |
| weather | Henk | 336 | 67 | 61405 | 12.242361 | 29.6 |

## 当前VIF（与旧设计不可机械同口径）

| group | target | continuous_max_VIF | term | all_columns_max_VIF |
| --- | --- | --- | --- | --- |
| main | E0 | 3.7545522 | deprivation_gap_pct | 3.7545522 |
| main | R0c | 3.7549728 | deprivation_gap_pct | 3.7549728 |
| weather | E0 | 4.9265827 | deprivation_gap_pct | 5.345618 |
| weather | R0c | 4.9300745 | deprivation_gap_pct | 5.3468462 |

## 补充模型

| analysis | target | variant | n | status | beta_gust | beta_gust2 | pooled_R2 | delta_R2 | warning_count | beta_gust3 | quadratic_R2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GLM | E0 | NB2 | 60436 | computed | -0.1373629 | 0.094259844 | 未提供/不适用 | 未提供/不适用 | 4 | 未提供/不适用 | 未提供/不适用 |
| GLM | E0 | Tweedie_1.5_log | 60436 | computed | -0.13127142 | 0.077939903 | 未提供/不适用 | 未提供/不适用 | 0 | 未提供/不适用 | 未提供/不适用 |
| cubic | E0 | zG3 | 60436 | computed | 0.0065779955 | 0.19667241 | 0.031553095 | 0.0019316391 | 未提供/不适用 | -0.028509607 | 0.029621456 |
| GLM | R0c | Gamma_log | 60436 | computed | -0.051156945 | 0.073090049 | 未提供/不适用 | 未提供/不适用 | 0 | 未提供/不适用 | 未提供/不适用 |
| GLM | R0c | Tweedie_1.5_log | 60436 | computed | -0.041271952 | 0.07733306 | 未提供/不适用 | 未提供/不适用 | 0 | 未提供/不适用 | 未提供/不适用 |
| cubic | R0c | zG3 | 60436 | computed | -0.015411119 | 0.07070966 | 0.092514019 | 0.00049818696 | 未提供/不适用 | 0.0053785026 | 0.092015832 |
| six_groups | R0c | all_valid_shared_dates | 117108 | computed_harmonized_scope | 未提供/不适用 | 未提供/不适用 | 0.039923105 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |

## 逐槽位与逐表细账

ALL_MANUSCRIPT_NUMERIC_SLOTS.csv索引了950个文字/表格数字槽位，不包含图片OCR和全部公式对象。CURRENT_NUMERIC_BINDINGS.csv提供182个表格单元格绑定，CURRENT_PARAGRAPH_NUMERIC_BINDINGS.csv另有64个段落绑定，图注数值也已补记。全部槽位已登记去向，但65个槽位需要整句/组合统计重写、以具名当前数据集替换，不能自动逐数回填；历史实验、引用、公式编号也单列。分类完成不等于所有旧数字均已一对一替换。原Word不动。

- 表1：Table1_current.csv（28个值）；表3/F：Tables3_F_complete_coefficients.csv，含全日历列和三种CR1，p_normal_CR1_descriptive为正态Wald描述；极小p如浮点下溢须读p_log10_normal_CR1及p_status，不写成真实p=0。
- 表4：H0_R1_B1_increments.csv；六组完整系数/各折：supplements_v1/six_group_*.json；当前配对OOF见six_groups_OOF.csv。AppendixC_fold_summary.csv和AppendixC_fold_coefficients.csv提供新5折摘要；重叠训练fold显著次数不作独立重复证据。
- 附录D：AppendixD_period_stage_counts.csv、核心step27_stage_coefficients.csv、stage_composition.csv/stage_pooled.csv。旧earlier+p99与当前全期all_valid必须改标签而非按格覆盖。
- 附录G：AppendixG_main_gust_deciles.csv是主组60436的十分位，weather share从6.933842%到57.071381%；AppendixG_gust_deciles.csv另为六组117108的十分位，不能混分母。AppendixG_low_gust_support.csv分列main/weather支持；并列按qcut实际合并，CSV保留边界。
- 附录H：AppendixH_pressure_minima.json、AppendixH_period_scales.csv、period_comparison.csv；旧Bootstrap仅历史，当前无区间。
- 客户比较：customer_aggregation_comparison.json；残差及global exp(residual)仅诊断：residual_diagnostics.csv，不用于曲线校准。

尚未认证的文献引用数字、官方天气产品语义、许可区几何与未决科学机制不因有当前模型而变为已核实。每一未映射槽位都保留旧定位/值/上下文、MR/CL和状态，可在R05及后续W逐项核对；本轮不宣称全论文已可自动落稿。
