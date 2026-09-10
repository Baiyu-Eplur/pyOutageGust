# C_REFERENCE_COVERAGE

需求 C04；C.1–C.4。四组合覆盖矩阵及补算完成状态。

分析单位：incident。样本：E0 all60437/weather9857; positive R0c all51173/weather9254。

模型：exact original ladder + separately matched final controls。指标：full Gaussian OLS AIC/BIC; pooled log-response RMSE。

验证：original LAD/random/year rules; train-only scaling/cuts/knots; compatible source components reused。

APP-C-COMPLETE授权仅C补算；历史含零客户恢复结果不作当前排名。

| model_id | combination | status | reason | source | n |
| --- | --- | --- | --- | --- | --- |
| MAIN_final | E0_all | REUSE | F08 full fit only | results/new/20260909183317/results/final_models/final_summary.json#E0 | 60437 |
| MAIN_final | R0c_all | REUSE | F01 | results/new/20260909183317/results/final_models/final_summary.json#R0c | 51173 |
| MAIN_final | E0_weather | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| MAIN_final | R0c_weather | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| D_ramp | E0_all | REUSE | F08 | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/ramp | 60437 |
| D_ramp | R0c_all | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/ramp | 51173 |
| D_ramp | E0_weather | REUSE | F08 | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/ramp | 9857 |
| D_ramp | R0c_weather | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/ramp | 9254 |
| D_two_hinge | E0_all | REUSE | F07 | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/two_hinge | 60437 |
| D_two_hinge | R0c_all | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/two_hinge | 51173 |
| D_two_hinge | E0_weather | REUSE | F07 | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/two_hinge | 9857 |
| D_two_hinge | R0c_weather | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/two_hinge | 9254 |
| D_quadratic | E0_all | REUSE | F01 | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/quadratic | 60437 |
| D_quadratic | R0c_all | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/quadratic | 51173 |
| D_quadratic | E0_weather | REUSE | F01 | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/quadratic | 9857 |
| D_quadratic | R0c_weather | REUSE | separate original controls, not matched F ranking | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/quadratic | 9254 |
| W_paper | E0_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_paper | R0c_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_paper | E0_weather | REUSE | H05 | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/paper | 9857 |
| W_paper | R0c_weather | REUSE | H05 | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/paper | 9254 |
| W_hinge | E0_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_hinge | R0c_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_hinge | E0_weather | REUSE | historical weather build; differs from free-two | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/hinge | 9857 |
| W_hinge | R0c_weather | REUSE | historical weather build; differs from free-two | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/hinge | 9254 |
| W_final | E0_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_final | R0c_all | NOT_APPLICABLE | source branch defined only for all or weather; corresponding current model is separately registered |  | NA |
| W_final | E0_weather | REUSE | F08 full fit only | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/final | 9857 |
| W_final | R0c_weather | REUSE | F06 full fit only | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/final | 9254 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
