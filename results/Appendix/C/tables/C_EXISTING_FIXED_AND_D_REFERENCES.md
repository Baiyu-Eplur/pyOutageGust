# C_EXISTING_FIXED_AND_D_REFERENCES

需求 C03；C.3–C.4。同控制阵风比较、地区FE、原天气及D参考结果。

分析单位：incident。样本：E0 all60437/weather9857; positive R0c all51173/weather9254。

模型：exact original ladder + separately matched final controls。指标：full Gaussian OLS AIC/BIC; pooled log-response RMSE。

验证：original LAD/random/year rules; train-only scaling/cuts/knots; compatible source components reused。

APP-C-COMPLETE授权仅C补算；历史含零客户恢复结果不作当前排名。

| combination | model_id | n | formula | controls | bic | LAD_RMSE | year_RMSE | knots_mode | source | status | correspondence | source_simplified_bic | full_sample_k1 | full_sample_k2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0_all | MAIN_final | 60437 | plateau | final | 254416.1172 | 1.984757206 | 1.989730208 | global selected knots fixed in CV | results/new/20260909183317/results/final_models/final_summary.json#E0 | REUSE | F08 full fit only | NA | NA | NA |
| E0_all | D_ramp | 60437 | ramp | M5 + temp squared | NA | 1.984977852 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/ramp | REUSE | F08 | 82903.34089 | 14 | 25 |
| E0_all | D_two_hinge | 60437 | two_hinge | M5 + temp squared | NA | 1.985060266 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/two_hinge | REUSE | F07 | 82912.87628 | 14 | 26 |
| E0_all | D_quadratic | 60437 | quadratic | M5 + temp squared | NA | 1.987247891 | NA | no knots | results/new/20260909183317/results/model_selection/ramp_model.json#all/nested_cv/quadratic | REUSE | F01 | NA | NA | NA |
| E0_weather | W_paper | 9857 | quadratic | M5 non-gust blocks + gust-pressure, no temperature squared | 43457.36974 | 2.178406829 | NA | no knots | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/paper | REUSE | H05 | NA | NA | NA |
| E0_weather | W_hinge | 9857 | plateau | M5 non-gust blocks + gust-pressure, no temperature squared | 43396.90953 | 2.171394005 | NA | global selected knots fixed in CV | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/hinge | REUSE | historical weather build; differs from free-two | NA | NA | NA |
| E0_weather | W_final | 9857 | plateau | final controls; see candidate definitions | 43365.02627 | 2.166861857 | NA | global selected knots fixed in CV | results/new/20260909183317/results/weather_only/weather_only_summary.json#E0/fits/final | REUSE | F08 full fit only | NA | NA | NA |
| E0_weather | D_ramp | 9857 | ramp | M5 + temp squared | NA | 2.16789683 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/ramp | REUSE | F08 | 15392.07203 | 11 | 24 |
| E0_weather | D_two_hinge | 9857 | two_hinge | M5 + temp squared | NA | 2.167370015 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/two_hinge | REUSE | F07 | 15394.75585 | 11 | 26 |
| E0_weather | D_quadratic | 9857 | quadratic | M5 + temp squared | NA | 2.174497853 | NA | no knots | results/new/20260909183317/results/model_selection/ramp_model.json#weather/nested_cv/quadratic | REUSE | F01 | NA | NA | NA |
| R0c_all | MAIN_final | 51173 | quadratic | final | 159553.5987 | 1.150252639 | 1.175262335 | no knots | results/new/20260909183317/results/final_models/final_summary.json#R0c | REUSE | F01 | NA | NA | NA |
| R0c_all | D_ramp | 51173 | ramp | M5 + temp squared - gust-pressure (no gust-precip) | NA | 1.150095076 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/ramp | REUSE | separate original controls, not matched F ranking | 14310.73142 | 17 | 33 |
| R0c_all | D_two_hinge | 51173 | two_hinge | M5 + temp squared - gust-pressure (no gust-precip) | NA | 1.150171549 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/two_hinge | REUSE | separate original controls, not matched F ranking | 14313.03895 | 15 | 20 |
| R0c_all | D_quadratic | 51173 | quadratic | M5 + temp squared | NA | 1.150381864 | NA | no knots | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#all/nested_cv/quadratic | REUSE | separate original controls, not matched F ranking | NA | NA | NA |
| R0c_weather | W_paper | 9254 | quadratic | M5 non-gust blocks + gust-pressure, no temperature squared | 30514.70725 | 1.250445938 | NA | no knots | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/paper | REUSE | H05 | NA | NA | NA |
| R0c_weather | W_hinge | 9254 | single hinge | M5 non-gust blocks + gust-pressure, no temperature squared | 30497.69719 | 1.249665858 | NA | global selected knots fixed in CV | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/hinge | REUSE | historical weather build; differs from free-two | NA | NA | NA |
| R0c_weather | W_final | 9254 | single hinge | final controls; see candidate definitions | 30449.45576 | 1.245920521 | NA | global selected knots fixed in CV | results/new/20260909183317/results/weather_only/weather_only_summary.json#R0c/fits/final | REUSE | F06 full fit only | NA | NA | NA |
| R0c_weather | D_ramp | 9254 | ramp | M5 + temp squared - gust-pressure (no gust-precip) | NA | 1.247826844 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/ramp | REUSE | separate original controls, not matched F ranking | 4191.805178 | 9 | 33 |
| R0c_weather | D_two_hinge | 9254 | two_hinge | M5 + temp squared - gust-pressure (no gust-precip) | NA | 1.248302343 | NA | train_selected | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/two_hinge | REUSE | separate original controls, not matched F ranking | 4200.014021 | 9 | 34 |
| R0c_weather | D_quadratic | 9254 | quadratic | M5 + temp squared | NA | 1.247616001 | NA | no knots | results/new/20260909183317/results/model_selection/ramp_model_R0c.json#weather/nested_cv/quadratic | REUSE | separate original controls, not matched F ranking | NA | NA | NA |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
