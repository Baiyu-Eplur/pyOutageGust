# C_COVERAGE_OVERVIEW

需求 C04；C.1–C.4。四组合覆盖矩阵及补算完成状态。

分析单位：incident。样本：E0 all60437/weather9857; positive R0c all51173/weather9254。

模型：exact original ladder + separately matched final controls。指标：full Gaussian OLS AIC/BIC; pooled log-response RMSE。

验证：original LAD/random/year rules; train-only scaling/cuts/knots; compatible source components reused。

APP-C-COMPLETE授权仅C补算；历史含零客户恢复结果不作当前排名。

| model_id | E0_all | E0_weather | R0c_all | R0c_weather |
| --- | --- | --- | --- | --- |
| F01 | REFIT | REFIT | REUSE | REFIT |
| F02 | REFIT | REFIT | REFIT | REFIT |
| F03 | REFIT | REFIT | REFIT | REFIT |
| F04 | REFIT | REFIT | REFIT | REFIT |
| F05 | REFIT | REFIT | REFIT | REFIT |
| F06 | REFIT | REFIT | REFIT | REFIT |
| F07 | REUSE | REUSE | REFIT | REFIT |
| F08 | REUSE | REUSE | REFIT | REFIT |
| H01 | REUSE | REFIT | REFIT | REFIT |
| H02 | REUSE | REFIT | REFIT | REFIT |
| H03 | REUSE | REFIT | REFIT | REFIT |
| H04 | REUSE | REFIT | REFIT | REFIT |
| H05 | REUSE | REFIT | REFIT | REFIT |
| H06 | REUSE | REFIT | REFIT | REFIT |
| H07 | REUSE | REFIT | REFIT | REFIT |
| H08 | REUSE | REFIT | REFIT | REFIT |
| H09 | REUSE | REFIT | REFIT | REFIT |
| H10 | REUSE | REFIT | REFIT | REFIT |
| H11 | REUSE | REFIT | REFIT | REFIT |
| H12 | REUSE | REFIT | REFIT | REFIT |
| H13 | REUSE | REFIT | REFIT | REFIT |
| H14 | REUSE | REFIT | REFIT | REFIT |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
