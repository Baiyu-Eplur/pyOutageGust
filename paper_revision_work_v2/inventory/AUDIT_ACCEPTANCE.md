# R00 审计接收表

2026-09-05；42 个文件逐一读取；CSV 全记录解析、JSON 全文解析、报告全文读取。数值结论仍属于 H0；本轮接收不冒称再次拟合。逐文件字节数、哈希、结构及完整路径见 audit_acceptance.json。旧清单所列项全部哈希一致。

|文件|记录/结构|证据来源|复用范围|
|---|---|---|---|
|coefficient_archive_comparison.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|command_history_index.csv|43|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|curve_reference_audit.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|deliverable_manifest.csv|41|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|duplicate_report_index.csv|182|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|fold_alignment.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|full_fit_summary.csv|4|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|historical_files_before.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|historical_preservation_check.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|historical_preservation_check_after_trace.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_E0_folds.csv|60437|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_E0_full_coefficients.csv|26|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_E0_oof_predictions.csv|60437|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_E0_representative_row_audit.csv|60437|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_E0_sample_membership.csv|60437|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_R0c_folds.csv|59834|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_R0c_full_coefficients.csv|28|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_R0c_oof_predictions.csv|59834|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_R0c_representative_row_audit.csv|59834|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|main_R0c_sample_membership.csv|59834|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|oof_archive_comparison.csv|14|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|oof_metric_comparison.csv|16|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|per_fold_r2.csv|80|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|project_context.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|representative_row_summary.csv|4|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|runtime.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|script_inventory.csv|82|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|script_inventory.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|source_and_sample_checks.json|JSON|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|storm_exposure_scale_audit.csv|8|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|storm_recovery_membership_audit.csv|7|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_E0_folds.csv|9857|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_E0_full_coefficients.csv|26|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_E0_oof_predictions.csv|9857|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_E0_representative_row_audit.csv|9857|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_E0_sample_membership.csv|9857|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_R0c_folds.csv|9758|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_R0c_full_coefficients.csv|28|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_R0c_oof_predictions.csv|9758|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_R0c_representative_row_audit.csv|9758|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|weather_R0c_sample_membership.csv|9758|verified_from_artifact|H0；修正输入后不直接用于当前结论|
|代码流程核查与研究推进脉络.md|12029|verified_from_artifact|H0；修正输入后不直接用于当前结论|

大数据 SHA 本轮各重算一次并与 H0 相符，之后阶段复用 large_input_identity.json，先检查大小及 mtime；如变动再哈希。当前未重跑 80 折拟合。
