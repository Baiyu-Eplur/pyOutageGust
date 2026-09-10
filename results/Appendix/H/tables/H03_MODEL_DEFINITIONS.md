# H03_MODEL_DEFINITIONS

需求 H03；H.1。当前正式预测变量基上四项替代均值/分布设定的系数及两维聚类区间；既有事件条件证据整理。

分析单位：incident。样本：E0_all60437 includes8979 zeros; R0c_all51173 positive customers, accepted cleaning。

模型：fixed final E14/25 plateau and R quadratic: E NB2/Tweedie; R Gamma/Tweedie; explicit Log; Tweedie power1.5 EQL。指标：full coefficients, LAD/date score-Hessian covariance and t(G_LAD-1) intervals; no cross-scale ranking。

验证：same design/IDs, lawful raw response, solver/score/Hessian diagnostics, saved means and covariance components; no CV。

第四包四个既定全样本拟合；OLS参考及H2/H3只复用/派生。产物完成待负责人反馈，不自动关闭或成文。

| combination | model | n | response | family_link | prediction_basis | parameters | action | source | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0_all | OLS_reference | 60437 | log1p(C) | OLS identity on transformed response | fixed14/25 platform with temp2 and gust-pressure | saved fixed OLS | REUSE | results/Appendix/G/data/GI_PREPROCESSING.json | E[transformed response\|X] |
| E0_all | NB2 | 60437 | customers C | NB2 / explicit log mean | fixed14/25 platform with temp2 and gust-pressure | jointly estimated alpha, full inference | REFIT_NEEDED | scripts/appendix_h_20260906/step_b_distribution_check.py | log E[raw response\|X]; not numerically same estimand as OLS |
| E0_all | Tweedie | 60437 | customers C | Tweedie / explicit log mean | fixed14/25 platform with temp2 and gust-pressure | power1.5 fixed; Pearson scale; eql=True | REFIT_NEEDED | scripts/appendix_h_20260906/step_b_distribution_check.py | log E[raw response\|X]; not numerically same estimand as OLS |
| R0c_all | OLS_reference | 51173 | log(T) | OLS identity on transformed response | quadratic gust with temp2 and gust-precip, log1p(customers) and square | saved fixed OLS | REUSE | results/Appendix/G/data/GI_PREPROCESSING.json | E[transformed response\|X] |
| R0c_all | Gamma | 51173 | duration T (hours) | Gamma / explicit log mean | quadratic gust with temp2 and gust-precip, log1p(customers) and square | Pearson scale estimated; explicit log link | REFIT_NEEDED | scripts/appendix_h_20260906/step_b_distribution_check.py | log E[raw response\|X]; not numerically same estimand as OLS |
| R0c_all | Tweedie | 51173 | duration T (hours) | Tweedie / explicit log mean | quadratic gust with temp2 and gust-precip, log1p(customers) and square | power1.5 fixed; Pearson scale; eql=True | REFIT_NEEDED | scripts/appendix_h_20260906/step_b_distribution_check.py | log E[raw response\|X]; not numerically same estimand as OLS |
| E0_weather | weather GLM | 9857 | NA | NA | NA | NA | NOT_APPLICABLE | body P030 and H01/H03 registration | H1 old comparator and claim refer to all-incident fits; weather GLM not explicitly required. Weather empirical/legacy H3 still exported. |
| R0c_weather | weather GLM | 9254 | NA | NA | NA | NA | NOT_APPLICABLE | body P030 and H01/H03 registration | H1 old comparator and claim refer to all-incident fits; weather GLM not explicitly required. Weather empirical/legacy H3 still exported. |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
