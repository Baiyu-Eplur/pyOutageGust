# A_FINAL_DESIGN_VIF

需求 A04；A.4。固定最终设计矩阵的VIF描述统计。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：当前全体最终设计矩阵，不读取响应变量拟合。指标：VIF=预测列相关矩阵逆矩阵对角线；包含虚拟变量控制，不含截距。

验证：只读已有结果；本轮不拟合。

复用原纯设计函数的隔离适配层，不执行旧模块顶层运行/拟合。全设计VIF与仅原始连续变量的VIF不是同一口径；不据此调整模型。

| margin | sample | n | term | VIF | controls | formula |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | final_all | 60437 | z_precipitation_24h_sum | 1.440842801 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | z_temperature_0h | 3.206847195 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | z_pressure_msl_0h | 1.896240102 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | z_gust_pressure | 2.310698957 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | urban_binary | 1.165430652 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | log_population | 1.339324567 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | income_deprivation_rate | 2.578144056 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | deprivation_gap_pct | 3.754840191 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | morans_i | 2.508874575 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_year[2022] | 1.954864774 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_year[2023] | 1.863380989 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_year[2024] | 2.177865007 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[2] | 2.114748896 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[3] | 1.86173251 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[4] | 1.987957413 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[5] | 2.472870678 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[6] | 3.253777817 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[7] | 3.541595917 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[8] | 3.051416031 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[9] | 2.871357447 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[10] | 2.795816521 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[11] | 2.366014524 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | incident_month[12] | 2.181017276 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | z_temperature_sq | 1.271356746 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | gust_low | 1.734893634 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| E0 | final_all | 60437 | gust_ramp | 3.075666645 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_gust_0h | 2.393901864 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_precipitation_24h_sum | 1.50460563 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_temperature_0h | 3.202004306 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_pressure_msl_0h | 1.923148602 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_gust_sq | 1.848469642 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | urban_binary | 1.167113324 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | log_population | 1.318624974 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | income_deprivation_rate | 2.640921972 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | deprivation_gap_pct | 3.837426348 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | morans_i | 2.531783441 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_year[2022] | 1.932553395 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_year[2023] | 1.827966413 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_year[2024] | 2.127328639 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[2] | 2.172592797 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[3] | 1.838630959 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[4] | 1.949790648 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[5] | 2.420114709 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[6] | 3.261435457 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[7] | 3.540954752 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[8] | 3.00531339 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[9] | 2.84755772 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[10] | 2.785085565 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[11] | 2.35857713 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | incident_month[12] | 2.202334908 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_customers_v2_log1p | 1.755855925 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_cust_sq | 1.750280995 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_temperature_sq | 1.280207756 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |
| R0c | final_all | 51173 | z_gust_precip | 1.215785104 | All saved final design columns except intercept | diag(inv(correlation(X_without_intercept))) |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
