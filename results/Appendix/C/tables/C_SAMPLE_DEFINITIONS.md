# C_SAMPLE_DEFINITIONS

需求 C01；C.1。四组最终样本及精确候选定义。

分析单位：incident。样本：E0 all60437/weather9857; positive R0c all51173/weather9254。

模型：exact original ladder + separately matched final controls。指标：full Gaussian OLS AIC/BIC; pooled log-response RMSE。

验证：original LAD/random/year rules; train-only scaling/cuts/knots; compatible source components reused。

APP-C-COMPLETE授权仅C补算；历史含零客户恢复结果不作当前排名。

| combination | n | lads | zero_customers | source | source_sha256 | sample_id_sha256 | fold_sha256 | response | filtering | scope_filter | missing_random_folds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0_all | 60437 | 111 | 8979 | review_package/data/combined_E0_final.csv | 6a82fedd4dd77f4218f89f47058cafea7cc7c34867120589cdbeba8fca63ec38 | 9822b53edfc840d7c823d220988e6180708fc3f04a4f429e9d971a9b991a1f94 | 2b77c93b5578e492b0ec603c46d9f21b38b314713f2a642ad6d31932f28d4585 | log1p_customers_v2 | accepted curated E0; no additional filter | none | 12113 |
| E0_weather | 9857 | 105 | 572 | review_package/data/combined_E0_final.csv | 6a82fedd4dd77f4218f89f47058cafea7cc7c34867120589cdbeba8fca63ec38 | a9fbb6b83c432d5518e046bb51b978b4fc6a08a6477e99a0f8c5870a1a250906 | eafbdcb8abb41958faa96ce768a76571423084f160165cb9e5000dbb78ed6619 | log1p_customers_v2 | accepted curated E0; no additional filter | cause_group_official == weather_natural | 2107 |
| R0c_all | 51173 | 111 | 0 | review_package/data/combined_R0c_final.csv | 313e5cea062eec015b5dbfdd61986ed277e058ab8fe9e0fa33ee773d936e72a9 | 177c17dcd65b1796342780d7fbde690ecf2a6ab2cace39b356253f6628ac9068 | 428ec3f84f42728897b3fcd4fbcdef0f6e9f34adfbda81cc13a6fc3ce9a7433c | log_duration_B_full_span_hours | accepted curated R0c; customers > 0 | none | 9996 |
| R0c_weather | 9254 | 104 | 0 | review_package/data/combined_R0c_final.csv | 313e5cea062eec015b5dbfdd61986ed277e058ab8fe9e0fa33ee773d936e72a9 | 19e0fee1995048631c582d84cc96bb2842c38ca63f26108ad3ac03833db04ddb | 6281212e10ca6966e84006e10ec59f35d5c40c9c695ee789f7931f733d878a1c | log_duration_B_full_span_hours | accepted curated R0c; customers > 0 | cause_group_official == weather_natural | 1977 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
