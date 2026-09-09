# pretest 步骤目录

开关均位于根目录 main.py。下表顺序就是执行顺序；公共模块列于表后。

| 开关名 | 分类 | 原脚本说明（节选） |
|---|---|---|
| `pipeline_v2/LAD_AreaSummary_v2` | data | LAD_AreaSummary_v2 |
| `pipeline_v2/LAD_urban_Summary_v2` | data | LAD_urban_Summary_v2 |
| `pipeline_v2/LAD_DNO_v2` | data | LAD_DNO_v2 |
| `pipeline_v2/filter_v2` | data | filter_v2.py —— 工作命令 #7 新版事件合并逻辑 2026-09-09 更新：已通过 main.py 在真实原始数据上执行，237901 阶段聚合为 135025 事件，3 份 CSV 均成功写入 pretest 时间目录。记录见运行 20260909155522。这验证输入、执行和输出链路，不替代统计 |
| `pipeline_v2/main1_v2` | data | main1_v2 |
| `pipeline_v2/match_lad_v2` | data | match_lad_v2 |
| `pipeline_v2/poppulation_merge_v2` | data | poppulation_merge_v2 |
| `pipeline_v2/Buckinghamshire_combination_v2` | data | Buckinghamshire_combination_v2 |
| `pipeline_v2/GVA_new_v2` | data | GVA_new_v2 |
| `pipeline_v2/GVA_merge_with_crosswalk_v2` | data | GVA_merge_with_crosswalk_v2 |
| `pipeline_v2/LAD_GeoMerge_v2` | data | LAD_GeoMerge_v2 |
| `pipeline_v2/data_arrange_v2` | data | data_arrange_v2.py —— 工作命令 #7 相对原版 data_arrange.py 的改动说明 ⚠️ 状态声明：与 filter_v2.py 一样，本脚本尚未在真实数据上执行过（下游链路本命令 本就不要求跑通，见 03_下游重跑规模评估.md）；这里只是把"Duration 计算方式需要 调整"这个已 |
| `test1/test1_step0_inventory` | analysis | Test 1 - Step 0: 数据盘点。 只读来源说明：data/new/ukpn_master_with_lad_features_updated.csv（303MB）在设备桥两次 staging 均失败（upload failed，很可能是单文件体积超出传输预算），因此改用已在本地沙箱中的 analysi |
| `test1/test1_full_pipeline` | analysis | Test 1 快速摸底：(duration, customers) 二维结果空间聚类有效性检验。 Steps 1-5. 数据来源见 test1_step0_inventory.py 顶部注释（同一份 62,928 行全量数据）。 |
| `test1b/test1b_independence_pipeline` | analysis | 工作命令 #3：检验 log1p(customers) 与 log1p(duration) 的统计独立性。 数据来源：与工作命令 #2 完全相同、已交叉验证过的替代数据源 (analysis_step2/02_incident_analysis_master_v1_1.parquet 的 Number of Cust |
| `borrowed_from_main/coef_fold_stability_E0_R0` | analysis | Claude branch — 借用自 analysis_step3/run_baseline_models.py 的只读函数 （load_screening_only / prep_base / make_samples / design_train_valid，逻辑未作任何修改， 仅调整了 ROOT 路径以指向本地 |
| `borrowed_from_main/coef_fold_stability_R0_custadj` | analysis | Claude branch —— 工作命令 #4：控制 customers（调度优先级代理变量）后， 重新检验阵风—恢复时长（R0_legacy_log_OLS）系数的样本外稳定性。 本文件是 claude_branch/scripts/borrowed_from_main/coef_fold_stability_E |
| `borrowed_from_main/coef_fold_stability_expansion_validation` | analysis | Claude branch —— 工作命令 #5：扩样本（screening_development + expansion_pool）复现—— 阵风系数"一次项消失/二次项显现"模式稳健性验证。 本文件复制自命令#1的 coef_fold_stability_E0_R0.py 和命令#4的 coef_fold_sta |
| `v3_audit/audit_v3_dataset` | checks | Command #8: audit ukpn_full_stage_dataset_v3.csv structure and quality. Read-only. Writes JSON summaries into claude_branch/results/v3_dataset_audit/raw/ which  |
| `v3_validation/v3_validation_pipeline` | analysis | Command #9: re-validate gust coefficient stability using customers_v2/duration_A/duration_B. Read-only against rebuild_v3_full_stage/ and data/ (LAD shapefile o |
| `v3_controlled_comparison/controlled_comparison_pipeline` | analysis | Command #10: separate the "sample-size effect" from the "variable-redefinition effect" in command #9's E0'/R0'_A/R0'_B/R0c' findings, using a naive/legacy-style |
| `critical_wind_speed/critical_wind_speed_pipeline` | analysis | Command #11: critical wind speed (quadratic turning point) for E0' (exposure) and R0c'_B (recovery, customers_v2-adjusted, duration_B) using command #9/#10's al |
| `variance_decomposition/variance_decomposition_pipeline` | analysis | Command #14: nested-model variance decomposition (in-sample and 5-fold OOS R^2) for E0' (exposure) and R0c'_B (recovery, both covariate orderings), restricted t |
| `cause_code_robustness/step1_composition_diagnostic` | analysis | Command #12 Step 1: Cause Code composition diagnostic across gust bins. Read-only against rebuild_v3_full_stage/. Reuses command #9's deterministic sample-const |
| `cause_code_robustness/step2_wt_subset_critical_wind_speed` | analysis | Command #12 Step 2: full critical-wind-speed re-estimation restricted to the weather_natural + technical_asset Cause Code subset, replicating command #11's enti |
| `dev_sample_decontamination/step1_rebuild_clean_sample` | analysis | Command #16 Step 1: rebuild a clean development sample with the locked_temporal_test date block (>= 2023-09-30) excluded, using whole-date-block exclusion (not  |
| `dev_sample_decontamination/step2_refit_clean` | models | Command #16 Step 2: refit E0' and R0c'_B on the clean (decontaminated) sample. |
| `dev_sample_decontamination/step3_critical_wind_speed_clean` | analysis | Command #16 Step 3: re-estimate the critical wind speed (E0' turning point only, per command scope) on the clean (decontaminated) weather_natural+technical_asse |
| `dev_sample_decontamination/step4_variance_decomposition_clean` | analysis | Command #16 Step 4: re-run command #14's nested variance decomposition on the clean (decontaminated) weather_natural+technical_asset sample. |
| `module_e_final_confirmation/build_holdout_sample` | data | Command #19 Step 0: build the genuine locked_temporal_test holdout sample ([2023-09-30, 2024-03-31]), applying the identical construction pipeline as command #1 |
| `module_e_final_confirmation/fit_holdout_models` | models | Command #19 Steps 1-3: fit E0/R0c on the locked_temporal_test holdout (single fit, no internal CV), estimate critical wind speed if sample size allows, run n_st |
| `final_combined_analysis/combined_sample_builder` | analysis | Command #21 Step 0: build the final combined analysis sample by concatenating command #16's clean development sample with command #19's locked_temporal_test hol |
| `final_combined_analysis/step1_final_fit` | models | Command #21 Step 1: full-sample E0/R0c fit on the final combined sample, reporting the COMPLETE coefficient table (not just gust terms). |
| `final_combined_analysis/step2_critical_wind_and_variance` | analysis | Command #21 Step 2: re-estimate E0's critical wind speed (with bootstrap CI) and re-run variance decomposition (E0 + R0c both orderings), on the final combined  |
| `final_combined_analysis/step3_dose_response_curve` | analysis | Command #21 Step 3: gust dose-response curve (region held fixed at sample mean, only gust varies), using Step 1's final combined-sample model. |
| `final_combined_analysis/step4_baseline_regional_map` | analysis | Command #21 Step 4: "baseline regional difference" map data (weather AND customers_v2 held fixed at the sample mean; only the 5 LAD-level socioeconomic covariat |
| `final_combined_analysis/step7_customers_dose_response` | analysis | Command #22 Step 1-2: customers_v2 dose-response curve for R0c (gust and all other covariates fixed at the SAME reference values command #21 Step3 used), paired |
| `final_combined_analysis/step10_named_storms` | analysis | Command #23: verify named storm events in the final combined weather_natural+technical_asset sample (n=60,453), using officially documented storm dates (UK Met  |
| `final_combined_analysis/step13_storm_prediction_check` | analysis | Command #24: fitted-vs-observed prediction check for the 7 named storms, using command #21's final combined-sample E0/R0c models (refit deterministically, not r |
| `final_combined_analysis/step16_range_restriction` | analysis | Command #25 Step 1: range-restriction diagnostic for command #24's storm-window fitted-vs-observed correlation attenuation, using the classic Thorndike Case 2 d |
| `final_combined_analysis/step17_weather_natural_subsample` | analysis | Command #25 Steps 2-4: build the weather_natural-only subsample (from command #21's final combined sample), refit E0/R0c, run variance decomposition, and re-est |
| `final_combined_analysis/step21_causecode_gust_diagnostic` | analysis | Command #26: pure descriptive diagnostic -- does Cause Code classification (weather_natural vs technical_asset) itself correlate with gust level, and does this  |
| `final_combined_analysis/step30_counterfactual` | analysis | Command #28: storm weight share + counterfactual transportability analysis (weather_natural gust coefficients applied to the full main-spec sample). |
| `final_combined_analysis/step36_six_group_clean_sample` | analysis | Command #31: rebuild the clean, decontaminated final combined sample WITHOUT restricting to weather_natural+technical_asset (all six Cause Code groups kept), re |
| `final_combined_analysis/step38_F4_customers_mean_ratio` | analysis | Command #38 F4: recompute the legacy 'first-stage-only' customers mean on the EXACT final combined E0 sample (n=60,437, command #21), using the same sort+dedup  |
| `final_combined_analysis/step38_M6_decompose_sample_vs_definition` | analysis | Command #38 M6 (extra): decompose whether the drop in customers-duration nonlinear dependence (final sample dcorr=0.199 vs legacy dcorr=0.375-0.519) is driven b |
| `final_combined_analysis/step38_M6_nonlinear_dependence` | analysis | Command #38 M6: distance correlation + mutual information between affected customers (customers_v2) and restoration duration (duration_B) on the FINAL combined  |
| `final_combined_analysis/step40_1_cubic_gust_term` | analysis | Command #40 Test 1: add a cubic gust term (z_gust_0h^3) to E0 and R0c on command #21's final combined sample, checking 5-fold GroupKFold(date) stability (not ju |
| `final_combined_analysis/step40_2_zspace_symmetry` | analysis | Command #40 Test 2: z-space symmetry analysis of the gust quadratic curve for R0c (recovery, linear term ~0) and E0 (exposure, linear term significant, used as  |
| `final_combined_analysis/step40_model_form_check` | analysis | Command #36: re-check log-OLS model-form adequacy on the final corrected samples (affected customers / restoration duration), by (1) refitting the exposure and  |
| `final_combined_analysis/step42_appendixD_composition_crosstab` | analysis | Command #42: n_stages x affected-customers cross-tabulation on the final combined R0c sample (command #21, n=59,834), to directly support Appendix Figure D1 (th |
| `final_combined_analysis/step43_M01_M03_M05` | analysis | Command #43: M01 (z=0 vs turning-point centering, algebraic proof), M03 (pressure-conditional turning points, full precision), M05 (bootstrap resampling diagnos |
| `final_combined_analysis/figure1_study_area` | figures | Command #33 Figure 1: UKPN licence area boundaries + event density hexbin, using the exact final combined sample (n=60,453). |
| `final_combined_analysis/figure2_distribution` | figures | Command #33 Figure 2: 2x2 distribution panels for affected customers and restoration duration, raw and log scale, on the final combined sample. |
| `final_combined_analysis/figure4_dose_response` | figures | Command #37 Figure 4: gust dose-response curves for E0 (exposure) and R0c (recovery), reusing command #21 Step3's existing 50-grid-point curve data (03_阵风剂量反应曲线 |
| `final_combined_analysis/figure5_variance_decomposition` | figures | Command #37 Figure 5: grouped bar chart of marginal OOS R^2 contribution by variable block, for E0 (exposure) and R0c (recovery), on the final combined sample.  |
| `final_combined_analysis/figure6_regional_map` | figures | Command #33/#34 Figure 6: regenerate command #21's baseline regional difference maps from the EXISTING data CSV (no recomputation). Command #34 revision: remove |
| `final_combined_analysis/figure7_magnitude_comparison` | figures | Command #37 Figure 7: simple horizontal bar chart comparing three predicted-value magnitude ratios (max/min across the observed covariate range, all other covar |
| `final_combined_analysis/figure8_weather_subsample_comparison` | figures | Command #37 Figure 8: main-specification vs weather_natural-subsample comparison of marginal OOS R^2 contribution, highlighting command #25's finding that the r |
| `final_combined_analysis/figure9_storm_validation` | figures | Command #37 Figure 9: restyled storm-period fitted-vs-observed scatter. Command #24's original file (13_风暴期预测检验散点图.png) has an in-figure title, 7-8pt default fo |
| `final_combined_analysis/figure10_robustness_forest` | figures | Command #37 Figure 10: robustness forest plot for the gust quadratic term (z_gust_0h_sq), comparing four existing analyses per outcome: 1. Development sample (c |
| `final_combined_analysis/figureD1_composition_effect` | figures | Command #42 Figure D1 (Appendix figure, not part of the main Figure 1-10 series): n_stages x affected-customers composition-effect figure. Panel (a) shows durat |
| `customers_duration_shape_investigation/step1_binned_relationship` | analysis | Command #17 Step 1: raw decile-binned customers_v2 vs duration_B relationship (no quadratic functional-form assumption), on command #16's clean weather_natural+ |
| `customers_duration_shape_investigation/step2_subgroup_check` | analysis | Command #17 Step 2: check whether the inverted-U shape holds independently within weather_natural and within technical_asset, or is a composition artifact of mi |
| `customers_duration_shape_investigation/step3_flexible_form` | analysis | Command #17 Step 3: refit R0c'_B_clean replacing the customers_v2 linear+quadratic terms with decile dummy variables (a fully flexible, non-parametric-in-custom |
| `customers_duration_shape_investigation/step5_n_stages_stratification` | analysis | Command #18: check whether the customers_v2/duration_B inverted-U is a mechanical byproduct of n_stages (both variables are stage-count-dependent by constructio |
| `code_audit_20260905/audit_pipeline` | checks | Read-only source audit and isolated replication of the existing analysis. Run with bundled CPython 3.12 and -B. Reuse installed project packages without repairi |
| `code_audit_20260905/trace_findings` | checks | Quantify audit findings without changing inputs, models or manuscripts. |
| `c01_repair_20260905/step1_representative_row` | analysis | C01 repair Step 1: recompute the correct event-representative row (earliest UTC start time, tie-broken by source_row_number) for every unique Incident Reference |
| `c01_repair_20260905/step2_weather_reextraction` | analysis | C01 repair Step 2: for every event whose representative row changed (Step 1), re-extract gust_0h / pressure_msl_0h / temperature_0h / precipitation_24h_sum at t |
| `c01_repair_20260905/step3_4_corrected_sample_and_refit` | models | C01 repair Steps 3-4: build the corrected event-level weather-matched sample (patching ONLY the fields that actually depend on which stage row is the event's re |
| `c01_repair_20260905/step4b_fold_stability_and_variance` | analysis | C01 repair Step 4b: on the CORRECTED final combined sample, compute (a) 5-fold GroupKFold coefficient stability for the gust linear+quadratic terms (matching th |
| `c01_repair_20260905/step4c_original_baseline_for_comparison` | analysis | C01 repair Step 4c: compute the SAME fold-stability + variance-decomposition diagnostics as step4b, but on the ORIGINAL (uncorrected, pre-C01-fix) final combine |
| `c02_c08_repair_20260905/corrected_sample_builder` | analysis | Reusable C01-corrected final combined sample builder. Encapsulates the same monkey-patch approach used in command #44 (patch v9.step0_build_sample() to return t |
| `c02_c08_repair_20260905/final_core_tables` | analysis | C02-C08 repair: final unified regeneration of all core coefficient/CI/ variance-decomposition numbers on the C01-corrected data, needed to complete Figure 10 (d |
| `c02_c08_repair_20260905/c02_r2_definition_check` | analysis | C02: document the exact R^2 computation method used throughout the project (pooled out-of-fold R^2, not the mean of 5 per-fold R^2 values) and compute the alter |
| `c02_c08_repair_20260905/figure1_study_area` | figures | Final regeneration of Figure 1 (study-area map) on C01-corrected data. No C02-C08 fix applies to this figure; regenerated purely for consistency (same event set |
| `c02_c08_repair_20260905/figure2_distribution` | figures | Final regeneration of Figure 2 (distribution panels) on C01-corrected data. No C02-C08 fix applies; regenerated for consistency with the corrected sample. |
| `c02_c08_repair_20260905/figure4_dose_response` | figures | Final regeneration of Figure 4 (gust dose-response curves), on C01-corrected data, with C07 and C08 fixes applied: C07: the R0c curve's reference scenario for c |
| `c02_c08_repair_20260905/figure5_variance_decomposition` | figures | Final regeneration of Figure 5 (variance decomposition) using the C01-corrected variance-decomposition numbers already computed in c01_repair_20260905/raw/step4 |
| `c02_c08_repair_20260905/figure6_regional_map` | figures | Final regeneration of Figure 6 (regional baseline maps) on C01-corrected data. C07: customers reference scenario confirmed as z_log1p_customers_v2=0 and its squ |
| `c02_c08_repair_20260905/figure7_magnitude_comparison` | figures | Final regeneration of Figure 7 (magnitude comparison) on C01-corrected data. Ratio definition unchanged (curve max / curve min over the plotted 1st-99th percent |
| `c02_c08_repair_20260905/figure8_weather_subsample_comparison` | figures | Final regeneration of Figure 8 on C01-corrected data (main-spec variance decomposition from c01_repair's step4b outputs; weather_natural subsample variance deco |
| `c02_c08_repair_20260905/figure9_storm_validation` | figures | Final regeneration of Figure 9 (storm-period fitted vs observed), on C01-corrected data, with C04 and C05 fixes: C04: predict_for_subset now returns eta (the mo |
| `c02_c08_repair_20260905/figure10_robustness_forest` | figures | Final regeneration of Figure 10 (robustness forest plot) on C01-corrected data, using this command's final_core_tables.py outputs (dev-only 5-fold pooled, holdo |
| `c02_c08_repair_20260905/figureD1_composition_effect` | figures | Final regeneration of Appendix Figure D1 (composition-effect crosstab) on C01-corrected data. No C02-C08 fix applies directly; regenerated for consistency with  |
| `c09_final_cleanup_20260905/a02_duan_smearing` | analysis | A02: compute the Duan (1983) smearing factor on the C01-corrected E0/R0c residuals, to quantify how much the naive exp(eta) predictions shown in Figure 4/6 (com |
| `c09_final_cleanup_20260905/appendixG_recompute` | analysis | Appendix G recomputation on C01-corrected data: 1. weather_natural share of the weather_natural+technical_asset sample, by gust decile (command #26's Table G1,  |
| `c09_final_cleanup_20260905/c09_vif_fixed` | analysis | C09 item 2, corrected computation: the first pass (run_all_c09.py) computed VIF by dropping the Intercept column entirely before calling variance_inflation_fact |
| `c09_final_cleanup_20260905/c09_vif_recompute` | analysis | C09 item 2: recompute VIF on the FULL design matrix (including year/month fixed-effect dummies, which the historical VIF check -- final_combined_analysis/raw/st |
| `c09_final_cleanup_20260905/diag_vif_original` | checks | Diagnostic: reproduce the restricted-variable VIF check on the ORIGINAL (uncorrected, pre-C01) sample pipeline, to check whether the historical step26_E0_vif.cs |
| `c09_final_cleanup_20260905/diag_vif_spike` | checks | Diagnostic: why do log_population/income_deprivation_rate/deprivation_gap_pct/ morans_i show much higher VIF on the corrected sample (15.7/23.0/42.4/8.2) than t |
| `c09_final_cleanup_20260905/run_all_c09` | analysis | Command #46 (C09 final cleanup): run A02 (Duan smearing), Appendix G recompute, and C09 VIF-with-FE recompute all in ONE process, so the expensive build_correct |
| `a02_log_scale_20260905/figure4_dose_response_log_scale` | figures | Command #47: A02 resolution -- Figure 4 redrawn on the log scale directly, removing the final exponentiation step entirely (no Duan smearing, no new bootstrap). |
| `a02_log_scale_20260905/figure6_regional_map_log_scale` | figures | Command #47: A02 resolution -- Figure 6a/6b redrawn with the choropleth color scale showing the model's log-scale predicted value directly (no exponentiation).  |
| `independent_review_ir_20260905/ir04_bootstrap_diagnostic` | analysis | IR04 diagnostic: quantify the difference between the CURRENT bootstrap-CI conversion method used by figure4_dose_response.py (take percentiles on the z-scale bo |
| `appendix_h_20260906/step_a3_curve_comparison` | analysis | Command #50 Step A3: gust curve-shape bake-off (quadratic / natural cubic spline / U-shape-constrained hinge spline / softplus) on the C01+C02-C08 corrected fin |
| `appendix_h_20260906/step_b_distribution_check` | analysis | Command #50 Step B: NB2/Tweedie (E0) and Gamma/Tweedie (R0c) distribution- assumption check, re-run on the C01+C02-C08 CORRECTED final combined sample. Design m |
| `appendix_h_20260906/make_curve_plot` | figures | Command #50 Step D: plot the four gust-shape candidates' fitted curves (full-sample fit, other covariates at their sample means) for E0 and R0c, using the alrea |
| `appendix_h_legacy_followup_20260906/q1_bootstrap_beta2_check` | analysis | Command #51, Question 1: re-run command #43's M05 bootstrap diagnostic (capturing beta1/beta2, not just the turning-point ratio) on the C01+C02-C08 CORRECTED fi |
| `appendix_h_legacy_followup_20260906/q2_figure10_dev_sample_check` | analysis | Command #51, Question 2: verify the "development sample" row in Figure 10. Confirms the current construction (inverse-variance pooling across 5 GroupKFold TRAIN |
| `appendix_h_legacy_followup_20260906/make_figure10_corrected` | figures | Command #51, Question 2: regenerate Figure 10 with the "development sample" row replaced by a genuine single full-sample fit (option a) instead of the inverse-v |
| `figure_relabel_20260906/figure2_distribution` | figures | Command #52: relabeled copy of figure2_distribution.py. ONLY change: panel (a)'s x-axis label no longer includes the internal codename "customers_v2" -- now rea |
| `figure_relabel_20260906/figure5_variance_decomposition` | figures | Command #52: relabeled copy of figure5_variance_decomposition.py. ONLY change: legend labels "E0 (exposure)" / "R0c (recovery, gust-before-customers order)" rep |
| `figure_relabel_20260906/figure7_magnitude_comparison` | figures | Command #52: relabeled copy of figure7_magnitude_comparison.py. ONLY change: the three row labels no longer contain "E0"/"R0c" -- replaced with "exposure margin |
| `figure_relabel_20260906/figure8_weather_subsample_comparison` | figures | Command #52: relabeled copy of figure8_weather_subsample_comparison.py. Changes: "weather_natural" x-tick labels -> "Weather-related"; "E0 (exposure)" text anno |
| `figure_relabel_20260906/figure9_storm_validation` | figures | Command #52: relabeled copy of figure9_storm_validation.py. Changes: "E0 (exposure)" -> "Exposure margin"; "R0c (recovery) open triangles..." -> "Recovery margi |
| `figure_relabel_20260906/figure10_robustness_forest` | figures | Command #52: relabeled copy of figure10_robustness_forest.py. ONLY change: row labels "E0 (exposure)" / "R0c (recovery)" replaced with "Exposure margin" / "Reco |
| `figure_relabel_20260906/figureD1_composition_effect` | figures | Command #52: relabeled copy of figureD1_composition_effect.py. ONLY change: legend labels "n_stages = 1" / "n_stages = 2" / "n_stages = 3-4" / "n_stages >= 5" ( |
| `figure_relabel_20260906/make_figureH1_curve_plot` | figures | Command #52: relabeled copy of appendix_h_20260906/make_curve_plot.py. ONLY change: panel annotation text "Exposure margin (E0)" / "Recovery margin (R0c)" -> "E |
| `distribution_gsa_20260907/task1_distribution_fitting` | models | Command #53, Task 1: descriptive distribution fitting for the continuous covariates listed in Table 2, on the C01+C02-C08 corrected final combined (weather_natu |
| `distribution_gsa_20260907/task1b_ks_supplement` | analysis | Command #53, Task 1 supplement: distfit's default 'score' (RSS on the binned histogram density) is NOT comparable across variables with different value ranges/d |
| `distribution_gsa_20260907/task2_global_sensitivity` | analysis | Command #53, Task 2: global sensitivity analysis (Sobol' + PAWN) of the fitted E0/R0c regression equations (Equation 4), using SALib. This is a SEPARATE, INDEPE |
| `model_review_package_20260907/materialize_final_data` | data | Command #54 preparatory step (run in the main project, NOT part of the review package itself): materialize the actual final E0/R0c analysis-ready DataFrames --  |
| `review_package/run_main_regression` | models | Fit the E0 exposure and R0c recovery models on the corrected analysis samples. Outputs include coefficient tables with LAD and LAD-by-date clustered standard er |
| `event_input_repair/r02_input_pipeline` | checks | Independent R02 input consumer. Never import or patch the historical pipeline. The producer is paper_revision_work_v2/code/run_r02.py. All scientific model exec |
| `event_input_repair/test_r02_events` | checks | Targeted regressions for the known event/time/input failure modes. |

公共模块（由上述步骤导入）：

- `scripts/appendix_h_20260906/appendix_h_common.py`
- `scripts/dev_sample_decontamination/clean_sample_builder.py`
- `scripts/event_input_repair/r02_events.py`
- `scripts/final_combined_analysis/figure_style.py`
