# X02 storm-specialisation report

## Status

X02-A through X02-F completed in the required order. Path A was selected on P1–P3 and scored once on frozen P4/P5 models before Path B began. The first Path-B implementation was invalidated because three long training events crossed held-process buffers; its outputs are retained under `evidence/invalidated_pathB_v1/`. The corrected Path B passed all acceptance checks. No Claude manuscript, prior R-stage result, X01 artifact, Figure 9 file or source dataset was modified.

## Data and Figure 9

The source is the R02 corrected event contract (135,025 unique event rows; SHA256 `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`). The main eligible parent contains 60,436 events per task. Frozen named-window membership contains 4,452 eligible unique events: 3,382 in development P1–P3 and 1,070 in time test P4–P5. Seven names produce five protected groups; 702 events carry overlapping Dudley/Eunice/Franklin name labels but are counted once in P2.

The retained R04 Figure 9 descriptive panels are full-sample fitted values, with all 4,452 plotted events included in the fit. Its companion date-group OOF panels are not protected-process holdouts. Recalculated descriptive prediction SD ratios are 0.335 for E and 0.395 for R: the horizontal-band appearance reflects compressed prediction variation plus process-specific mean bias, not merely one common intercept error and not evidence for a flat gust-response curve.

## Frozen time test

| task | locked_model | episode | n | MSE | RMSE | R2 | skill_vs_B00 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E_log | G02 | P4 | 576 | 4.3532 | 2.0864 | 0.0934 | 0.1593 |
| E_log | G02 | P5 | 494 | 4.3994 | 2.0975 | 0.0794 | 0.0795 |
| E_log | G02 | POOLED | 1070 | 4.3745 | 2.0915 | 0.1029 | 0.1240 |
| E_log | G02 | MACRO | 1070 | 4.3763 | 2.0920 | NA | 0.1210 |
| R_log | G02 | P4 | 576 | 2.0019 | 1.4149 | -0.1470 | 0.3086 |
| R_log | G02 | P5 | 494 | 2.0940 | 1.4470 | -0.0679 | 0.2319 |
| R_log | G02 | POOLED | 1070 | 2.0444 | 1.4298 | -0.1024 | 0.2743 |
| R_log | G02 | MACRO | 1070 | 2.0479 | 1.4311 | NA | 0.2714 |
| R_C_log | G05 | P4 | 576 | 1.3217 | 1.1497 | 0.2427 | 0.5435 |
| R_C_log | G05 | P5 | 494 | 1.8123 | 1.3462 | 0.0757 | 0.3352 |
| R_C_log | G05 | POOLED | 1070 | 1.5482 | 1.2443 | 0.1651 | 0.4504 |
| R_C_log | G05 | MACRO | 1070 | 1.5670 | 1.2518 | NA | 0.4425 |

The development lock selected G02 for E_log and R_log, and G05 for R_C_log. E_log's G05 was within 1% of G02 in development, so the predeclared simplicity rule selected G02. These choices were not revised after seeing P4/P5 or five-process results.

## Predeclared comparisons

Differences are first model minus second model; negative MSE differences favour the first model.

| task | comparison | development_macro_MSE_diff | P4_diff | P5_diff | five_process_macro_diff | process_range |
| --- | --- | --- | --- | --- | --- | --- |
| E_log | S02-G02 | 1.7159 | 0.7739 | 0.0326 | 0.2685 | [-0.0516, 0.5082] |
| E_log | P00-G02 | 0.1633 | 0.2687 | -0.0187 | 0.0604 | [-0.0344, 0.2095] |
| E_log | P02-P00 | -0.0443 | 0.0246 | -0.1336 | 0.0243 | [-0.0803, 0.0894] |
| E_log | S03-S02 | 0.5549 | -0.6146 | -0.1803 | -0.1232 | [-0.2756, 0.0303] |
| E_log | S04-S02 | -0.5188 | -0.0235 | -0.0024 | -0.0351 | [-0.1405, 0.2100] |
| E_log | S05-S02 | -1.5182 | -0.8465 | -0.2600 | -0.1937 | [-0.3695, 0.0921] |
| E_log | S05-G05 | 0.1632 | 0.0009 | -0.1326 | 0.1121 | [-0.1057, 0.2166] |
| E_log | S02-B01 | 0.6877 | -0.1021 | -0.1311 | -0.1210 | [-0.3235, 0.0309] |
| R_log | S02-G02 | 4.0751 | 0.2038 | 0.0499 | 1.5743 | [-0.4037, 7.5580] |
| R_log | P00-G02 | 0.5507 | 0.6905 | 0.4369 | 0.3313 | [0.1582, 0.5773] |
| R_log | P02-P00 | -0.1048 | 0.2011 | 0.2232 | -0.0135 | [-0.0899, 0.0835] |
| R_log | S03-S02 | -1.3064 | -0.1352 | -0.0106 | -0.0581 | [-0.2543, 0.1821] |
| R_log | S04-S02 | -0.5833 | -0.1013 | 0.0033 | -1.4865 | [-7.0227, -0.0196] |
| R_log | S05-S02 | -3.8785 | -0.4416 | -0.0889 | -1.3807 | [-7.5277, 1.4618] |
| R_log | S05-G05 | 0.1644 | -0.0512 | 0.1103 | 0.2356 | [-0.0281, 1.0209] |
| R_log | S02-B01 | -3.3089 | -0.0859 | 0.0264 | 1.4016 | [-0.1099, 6.9817] |
| R_C_log | S02-G02 | 5.0254 | 0.6224 | 0.0160 | 0.3215 | [-0.2299, 0.6328] |
| R_C_log | P00-G02 | 0.5617 | 0.8739 | 0.4091 | 0.3299 | [0.1373, 0.5366] |
| R_C_log | P02-P00 | -0.0513 | -0.0358 | 0.2813 | -0.0028 | [-0.0506, 0.0714] |
| R_C_log | S03-S02 | -1.4459 | -0.1825 | -0.0088 | 1.5158 | [-0.2672, 8.1188] |
| R_C_log | S04-S02 | -0.7136 | -0.1349 | 0.0009 | -0.0923 | [-0.2881, 0.0004] |
| R_C_log | S05-S02 | -4.9793 | -0.8642 | -0.2348 | -0.2364 | [-0.7616, 1.2800] |
| R_C_log | S05-G05 | 0.1955 | 0.1910 | 0.0559 | 0.2878 | [0.0073, 1.1333] |
| R_C_log | S02-B01 | -3.8983 | -0.1247 | 0.0064 | -0.0153 | [-0.1476, 0.1689] |

The central population hypothesis is not supported: S02 is worse than fair all-period G02 in both time-test processes for all three tasks, and is also worse on five-process macro-MSE. A shared storm offset P00 does not consistently repair the difference; for R and R_C it is worse than G02 in both time tests and five-process macro results. P02 adds no consistent improvement over P00.

Flexible storm curves do not yield a stable universal gain. S04 usually improves on S02, but the E five-process range includes harm and its fitted width reaches the frozen 0.05 m/s lower bound in all three final tasks; this behaves like a sharp hinge and does not identify a physical threshold. S03 has mixed process results and a severe R_C failure in one held process. S05 improves on S02 in several summaries, yet S05 does not outperform the same-information all-period G05 consistently; its five-process macro-MSE is worse than G05 for E, R and R_C. Thus interaction flexibility can help relative to a weak storm-only quadratic, but there is no evidence that storm-only training is the source of the gain.

R_C performs better than R in the locked time test because it conditions on final customer count. This is post-event conditional prediction, not onset-time or real-time improvement. F1 was skipped because no timestamped operational/forecast archive could establish availability.

## Diagnostic interpretation and use boundary

Predictions remain substantially less variable than observations in the time test. For locked E/G02, SD ratios are about 0.27 (P4) and 0.24 (P5); for R/G02 about 0.29 in both; for R_C/G05 about 0.44 and 0.39. R/G02 Pearson correlations are only about 0.067 and 0.090, so its B00 skill is driven substantially by level/control adjustment rather than strong event-level ranking. Process mean bias and within-process residual SSE are separately available in `tables/time_test_residual_diagnostics.csv` and `tables/fivefold_metrics.csv`.

The results support retrospective consequence estimation conditional on observed archived weather for recorded events. They do not support storm-total outage forecasting, event occurrence prediction, causal damage thresholds, a verified pre-storm operational forecast, or generalisation beyond five already studied historical processes.

## Acceptance and reproducibility

Independent prediction-level recalculation exactly matched exported metrics (maximum absolute difference 0). Fit/test ID overlap, held-buffer overlap, time-cutoff violations, forbidden core features and duplicate predictions are all zero. Each task/model has 4,452 corrected outer-fold predictions. Model and fit-ID hashes pass. Full details are in `VALIDATION_REPORT.md`.

The source parquet is intentionally not duplicated. `README.md` records its absolute path and hash. Saved predictions permit metric recalculation without the source data; model refitting requires the verified R02 event contract.
