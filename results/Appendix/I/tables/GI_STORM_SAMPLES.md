# GI_STORM_SAMPLES

需求 I02；I.2–I.3。当前最终规格风暴预测、误差与紧凑图。

分析单位：incident。样本：accepted E0 all60437/weather9857; positive R0c all51173/weather9254; I all only。

模型：fixed final / exactly identified legacy controls; no model search。指标：pooled log-scale RMSE/MAE/bias; actual fixed gust bins and predicted quantiles; I seven windows and unique union。

验证：original fixed five LAD folds where row outputs absent; in-sample and OOF explicitly separate。

第三包G/I授权完成；只补当前模型底层数组和七场风暴描述；产物完成后待反馈，H未启动。

| storm | exposure_n | recovery_before_duration_cap_positive_customers | recovery_final_n | excluded_zero_or_negative_customers | excluded_duration | display_only_above_cap | exactly_one_hour_positive_customer_included | missing_covariates_in_exposure_source | source_scope | cap_hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Arwen | 270 | 243 | 242 | 27 | 0 | 1 | 1 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Dudley | 291 | 256 | 254 | 35 | 0 | 2 | 0 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Eunice | 1659 | 1532 | 1518 | 127 | 0 | 14 | 1 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Franklin | 1132 | 1068 | 1064 | 64 | 0 | 4 | 3 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Babet | 509 | 450 | 449 | 59 | 0 | 1 | 2 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Ciaran | 576 | 468 | 466 | 108 | 0 | 2 | 1 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| Henk | 494 | 443 | 439 | 51 | 0 | 4 | 1 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |
| UNION_DEDUPLICATED | 4452 | 4018 | 3990 | 434 | 0 | 28 | 9 | 0 | accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe | 192.0833333 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
