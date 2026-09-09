"""项目唯一分析入口：修改下面参数，然后运行 python main.py。"""

# ==================== 统一参数区（无需 config 文件） ====================
RUN_PRETEST = 1                 # 旧研究功能总开关：1 开启，0 关闭
RUN_PURPOSE = "结构调整后检查入口；按需填写本次分析目的"
DRY_RUN = 0                     # 1 仅列出执行计划；0 真正运行
CONTINUE_ON_ERROR = 0           # 0 遇错停止；1 记录错误后继续其他已开启步骤
PYTHON_EXECUTABLE = None        # None 使用当前环境；也可填写其他 Python 的绝对路径

# 每个独立步骤均可设为 1/0，按下表顺序执行，不会自动开启前置步骤。
# 前置步骤为 0 时复用最近成功输出；首次运行则读取迁移前的结果归档。
# 默认全部关闭，避免打开项目时自动触发耗时拟合、bootstrap 或天气下载。
PRETEST_STEPS = {
    # pipeline_v2
    "pipeline_v2/LAD_AreaSummary_v2": 0,
    "pipeline_v2/LAD_urban_Summary_v2": 0,
    "pipeline_v2/LAD_DNO_v2": 0,
    "pipeline_v2/filter_v2": 0,
    "pipeline_v2/main1_v2": 0,
    "pipeline_v2/match_lad_v2": 0,
    "pipeline_v2/poppulation_merge_v2": 0,
    "pipeline_v2/Buckinghamshire_combination_v2": 0,
    "pipeline_v2/GVA_new_v2": 0,
    "pipeline_v2/GVA_merge_with_crosswalk_v2": 0,
    "pipeline_v2/LAD_GeoMerge_v2": 0,
    "pipeline_v2/data_arrange_v2": 0,

    # test1
    "test1/test1_step0_inventory": 0,
    "test1/test1_full_pipeline": 0,

    # test1b
    "test1b/test1b_independence_pipeline": 0,

    # borrowed_from_main
    "borrowed_from_main/coef_fold_stability_E0_R0": 0,
    "borrowed_from_main/coef_fold_stability_R0_custadj": 0,
    "borrowed_from_main/coef_fold_stability_expansion_validation": 0,

    # v3_audit
    "v3_audit/audit_v3_dataset": 0,

    # v3_validation
    "v3_validation/v3_validation_pipeline": 0,

    # v3_controlled_comparison
    "v3_controlled_comparison/controlled_comparison_pipeline": 0,

    # critical_wind_speed
    "critical_wind_speed/critical_wind_speed_pipeline": 0,

    # variance_decomposition
    "variance_decomposition/variance_decomposition_pipeline": 0,

    # cause_code_robustness
    "cause_code_robustness/step1_composition_diagnostic": 0,
    "cause_code_robustness/step2_wt_subset_critical_wind_speed": 0,

    # dev_sample_decontamination
    "dev_sample_decontamination/step1_rebuild_clean_sample": 0,
    "dev_sample_decontamination/step2_refit_clean": 0,
    "dev_sample_decontamination/step3_critical_wind_speed_clean": 0,
    "dev_sample_decontamination/step4_variance_decomposition_clean": 0,

    # module_e_final_confirmation
    "module_e_final_confirmation/build_holdout_sample": 0,
    "module_e_final_confirmation/fit_holdout_models": 0,

    # final_combined_analysis
    "final_combined_analysis/combined_sample_builder": 0,
    "final_combined_analysis/step1_final_fit": 0,
    "final_combined_analysis/step2_critical_wind_and_variance": 0,
    "final_combined_analysis/step3_dose_response_curve": 0,
    "final_combined_analysis/step4_baseline_regional_map": 0,
    "final_combined_analysis/step7_customers_dose_response": 0,
    "final_combined_analysis/step10_named_storms": 0,
    "final_combined_analysis/step13_storm_prediction_check": 0,
    "final_combined_analysis/step16_range_restriction": 0,
    "final_combined_analysis/step17_weather_natural_subsample": 0,
    "final_combined_analysis/step21_causecode_gust_diagnostic": 0,
    "final_combined_analysis/step30_counterfactual": 0,
    "final_combined_analysis/step36_six_group_clean_sample": 0,
    "final_combined_analysis/step38_F4_customers_mean_ratio": 0,
    "final_combined_analysis/step38_M6_decompose_sample_vs_definition": 0,
    "final_combined_analysis/step38_M6_nonlinear_dependence": 0,
    "final_combined_analysis/step40_1_cubic_gust_term": 0,
    "final_combined_analysis/step40_2_zspace_symmetry": 0,
    "final_combined_analysis/step40_model_form_check": 0,
    "final_combined_analysis/step42_appendixD_composition_crosstab": 0,
    "final_combined_analysis/step43_M01_M03_M05": 0,
    "final_combined_analysis/figure1_study_area": 0,
    "final_combined_analysis/figure2_distribution": 0,
    "final_combined_analysis/figure4_dose_response": 0,
    "final_combined_analysis/figure5_variance_decomposition": 0,
    "final_combined_analysis/figure6_regional_map": 0,
    "final_combined_analysis/figure7_magnitude_comparison": 0,
    "final_combined_analysis/figure8_weather_subsample_comparison": 0,
    "final_combined_analysis/figure9_storm_validation": 0,
    "final_combined_analysis/figure10_robustness_forest": 0,
    "final_combined_analysis/figureD1_composition_effect": 0,

    # customers_duration_shape_investigation
    "customers_duration_shape_investigation/step1_binned_relationship": 0,
    "customers_duration_shape_investigation/step2_subgroup_check": 0,
    "customers_duration_shape_investigation/step3_flexible_form": 0,
    "customers_duration_shape_investigation/step5_n_stages_stratification": 0,

    # code_audit_20260905
    "code_audit_20260905/audit_pipeline": 0,
    "code_audit_20260905/trace_findings": 0,

    # c01_repair_20260905
    "c01_repair_20260905/step1_representative_row": 0,
    "c01_repair_20260905/step2_weather_reextraction": 0,
    "c01_repair_20260905/step3_4_corrected_sample_and_refit": 0,
    "c01_repair_20260905/step4b_fold_stability_and_variance": 0,
    "c01_repair_20260905/step4c_original_baseline_for_comparison": 0,

    # c02_c08_repair_20260905
    "c02_c08_repair_20260905/corrected_sample_builder": 0,
    "c02_c08_repair_20260905/final_core_tables": 0,
    "c02_c08_repair_20260905/c02_r2_definition_check": 0,
    "c02_c08_repair_20260905/figure1_study_area": 0,
    "c02_c08_repair_20260905/figure2_distribution": 0,
    "c02_c08_repair_20260905/figure4_dose_response": 0,
    "c02_c08_repair_20260905/figure5_variance_decomposition": 0,
    "c02_c08_repair_20260905/figure6_regional_map": 0,
    "c02_c08_repair_20260905/figure7_magnitude_comparison": 0,
    "c02_c08_repair_20260905/figure8_weather_subsample_comparison": 0,
    "c02_c08_repair_20260905/figure9_storm_validation": 0,
    "c02_c08_repair_20260905/figure10_robustness_forest": 0,
    "c02_c08_repair_20260905/figureD1_composition_effect": 0,

    # c09_final_cleanup_20260905
    "c09_final_cleanup_20260905/a02_duan_smearing": 0,
    "c09_final_cleanup_20260905/appendixG_recompute": 0,
    "c09_final_cleanup_20260905/c09_vif_fixed": 0,
    "c09_final_cleanup_20260905/c09_vif_recompute": 0,
    "c09_final_cleanup_20260905/diag_vif_original": 0,
    "c09_final_cleanup_20260905/diag_vif_spike": 0,
    "c09_final_cleanup_20260905/run_all_c09": 0,

    # a02_log_scale_20260905
    "a02_log_scale_20260905/figure4_dose_response_log_scale": 0,
    "a02_log_scale_20260905/figure6_regional_map_log_scale": 0,

    # independent_review_ir_20260905
    "independent_review_ir_20260905/ir04_bootstrap_diagnostic": 0,

    # appendix_h_20260906
    "appendix_h_20260906/step_a3_curve_comparison": 0,
    "appendix_h_20260906/step_b_distribution_check": 0,
    "appendix_h_20260906/make_curve_plot": 0,

    # appendix_h_legacy_followup_20260906
    "appendix_h_legacy_followup_20260906/q1_bootstrap_beta2_check": 0,
    "appendix_h_legacy_followup_20260906/q2_figure10_dev_sample_check": 0,
    "appendix_h_legacy_followup_20260906/make_figure10_corrected": 0,

    # figure_relabel_20260906
    "figure_relabel_20260906/figure2_distribution": 0,
    "figure_relabel_20260906/figure5_variance_decomposition": 0,
    "figure_relabel_20260906/figure7_magnitude_comparison": 0,
    "figure_relabel_20260906/figure8_weather_subsample_comparison": 0,
    "figure_relabel_20260906/figure9_storm_validation": 0,
    "figure_relabel_20260906/figure10_robustness_forest": 0,
    "figure_relabel_20260906/figureD1_composition_effect": 0,
    "figure_relabel_20260906/make_figureH1_curve_plot": 0,

    # distribution_gsa_20260907
    "distribution_gsa_20260907/task1_distribution_fitting": 0,
    "distribution_gsa_20260907/task1b_ks_supplement": 0,
    "distribution_gsa_20260907/task2_global_sensitivity": 0,

    # model_review_package_20260907
    "model_review_package_20260907/materialize_final_data": 0,

    # review_package
    "review_package/run_main_regression": 0,

    # event_input_repair
    "event_input_repair/r02_input_pipeline": 0,
    "event_input_repair/test_r02_events": 0,

}
# ==================== 参数区结束 ====================


def main():
    if type(RUN_PRETEST) is not int or RUN_PRETEST not in (0, 1):
        raise ValueError("RUN_PRETEST 必须为整数 0 或 1")
    from pretestmain import run_pretests
    # 总开关关闭也记录本次运行目的和参数，但不执行子步骤。
    switches = PRETEST_STEPS if RUN_PRETEST else dict.fromkeys(PRETEST_STEPS, 0)
    manifest = run_pretests(switches, purpose=RUN_PURPOSE, dry_run=DRY_RUN,
                           continue_on_error=CONTINUE_ON_ERROR,
                           python_executable=PYTHON_EXECUTABLE)
    return 1 if manifest["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
