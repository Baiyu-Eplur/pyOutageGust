# RETURN_TO_CHATGPT_X02

## Status and inputs

Run `X02_20260907_001` completed X02-A–F and passed corrected-run acceptance. The corrected R02 event contract contains 135,025 unique events; the main parent has 60,436 eligible events per task. C is summed non-reinterruption restored customers; D is recorded full event span in hours. C=0 is retained for E; D must be positive for R/R_C; no test p99 trimming is used. All source/Claude/X01 artifacts remained read-only.

R04 Figure 9 descriptive values are full-sample fits, not external predictions. Its date-group OOF companion is not a storm-process holdout. The horizontal bands combine prediction-range compression (descriptive SD ratios E 0.335, R 0.395) with process mean bias.

## Storms and validation

Seven frozen UTC-proxy names cover 25 unique days and 4,452 eligible unique events. Dudley/Eunice/Franklin are one P2 group, giving P1–P5. Path A used P1–P3 (3,382) for three-fold development and P4/P5 (1,070) for a single frozen time score after the lock; cutoff was 2023-10-29 00:00 UTC and label maturity used recorded max end before cutoff. Corrected Path B used five outer process folds with four-group nested tuning.

The first Path-B run omitted buffer crossing removal in storm-only fits; 3 underlying long events caused 63 artifact-level violations. Those results are preserved and invalidated. Corrected Path B has zero ID/buffer leakage.

## Information set

F0 uses observed archived gust, pressure, temperature, prior-24-hour precipitation, static regional variables, licence/RUC and transferable calendar terms. It excludes final cause, stages, end time and outcomes. R_C alone includes final C and is post-event conditional. F1 is skipped because no auditable time-stamped operational/forecast archive exists.

## Main results

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

Negative differences favour the first model. S02 did not improve on G02 in either time-test process for any task and was worse on five-process macro-MSE. P00/P02 did not provide a stable repair. S03/S04/S05 show some improvements over S02, but signs vary by process; S04 reaches its minimum width and S05 is not consistently better than same-information G05. The evidence therefore does not support adopting storm-only training as a general replacement.

Locked time-test scores:

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

## Quality, limits and next step

Independent metric recalculation differs by 0; fit/test ID overlap, held-buffer overlap, cutoff violations, forbidden features and duplicate predictions are all zero. Corrected model failures are zero; implementation/reporting failures and the invalidated first Path B are retained in `evidence/FAILURE_LOG.json`.

The study supports only observed-weather conditional retrospective prediction across five previously studied historical processes. It does not establish forecast-time use, a causal wind threshold, storm-total burden or untouched external confirmation. Keep X01's quadratic working-model decision unchanged for now; the minimum next evidence is a timestamped forecast/operational feature archive and genuinely new storms.

Full report: `X02_REPORT.md`. Package: `RETURN_PACKAGE_X02.zip`.
