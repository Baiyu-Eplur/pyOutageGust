# P03/P04 实验报告

更新时间：2026-09-09T21:14:43.690270+01:00
结论：**中间状态**

存在未收敛拟合；不据此自动接受或宣称有效比较。

旧面板运行：20260909183317
完成阶段：baseline_and_geometry_verified, complete_hourly_data_aggregated_and_aligned, data_comparison_and_spatial_loo_saved_before_fits, both_versions_fitted_and_validated

## 判断依据

```json
{
  "status": "intermediate",
  "reason": "存在未收敛拟合；不据此自动接受或宣称有效比较。",
  "mean_relative_brier_gain": -0.007188340529907139,
  "mean_relative_calibration_rmse_gain": -0.061437062265349174,
  "brier_gain_ci95": [
    -0.009902395994560696,
    -0.004086534979271705
  ],
  "candidate_min_gain": 0.05
}
```

本实验不会修改 Word、Table 7、旧面板或原始输入。达到候选门槛也必须由用户/设计方核查校准图和数据诊断后决定是否转正。
回滚时建议正文不采用此实验，旧代理保留为明确注明局限的附录；此为实验建议，不是已经完成稿件移动。

## 比较范围

- 新变量为 ERA5、UTC、m/s 的中心点最近网格逐小时阵风之日最大值；不是逐日均值，也不是 LAD 面积最大值或地面观测真值。
- 旧变量使用事件坐标均值位置与事件小时天气插值；新旧差异同时包含来源、中心点及时间聚合变化，不能单独归因于插值误差。
- 面板标签不变，零客户事件仍计入任意事件；全体/天气归因各四阈值，其他协变量不参与本次单变量脆弱性拟合。
- LAD 五折分组方式和种子与既有绘图一致，两版使用相同折。旧代理本身依赖事件位置/日期，仍有事件选择造成的局限；CV 不消除此来源问题。
- 新网格留一区域与排除同网格邻居验证只检查空间连续性。其 RMSE 与旧事件锚点验证不是同一估计对象，不用于机械判定新源优劣。
- LAD 配对 bootstrap 只量化固定折外预测误差的区域抽样不确定性；没有重新训练，也没有按风暴/日期分组。

## 文件清单

见 inventory.json（实际路径、字节与 SHA-256）；experiment.json 保存参数、阶段、边界/输入/源码指纹。
模型完成时：parameters_long.csv / parameters_comparison.csv、brier_comparison.csv、cv_fold_scores.csv、oof_predictions.csv.gz、calibration_bins.csv、calibration.png、decision.json。
数据层完成时：centroids.csv、grid_daily.csv、panel_grid.csv、gust_comparison.csv/json、spatial_validation.json、两种 LOO CSV、grid_cells.csv、quality.json。
weather_raw/*.json.gz 保存逐小时 API 响应及请求信息；requests.jsonl 逐请求记录。未完成阶段不会生成伪造数值。
