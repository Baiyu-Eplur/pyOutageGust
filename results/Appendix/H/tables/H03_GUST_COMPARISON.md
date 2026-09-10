# H03_GUST_COMPARISON

需求 H03；H.1。当前正式预测变量基上四项替代均值/分布设定的系数及两维聚类区间；既有事件条件证据整理。

分析单位：incident。样本：E0_all60437 includes8979 zeros; R0c_all51173 positive customers, accepted cleaning。

模型：fixed final E14/25 plateau and R quadratic: E NB2/Tweedie; R Gamma/Tweedie; explicit Log; Tweedie power1.5 EQL。指标：full coefficients, LAD/date score-Hessian covariance and t(G_LAD-1) intervals; no cross-scale ranking。

验证：same design/IDs, lawful raw response, solver/score/Hessian diagnostics, saved means and covariance components; no CV。

第四包四个既定全样本拟合；OLS参考及H2/H3只复用/派生。产物完成待负责人反馈，不自动关闭或成文。

| combination | alternative | term | ols_coef | glm_coef | ols_se_twoway | glm_se_twoway | ols_ci_lower | ols_ci_upper | glm_ci_lower | glm_ci_upper | ols_p_t_G1 | glm_p_t_G1 | df | same_sign | ols_95_excludes_zero | glm_95_excludes_zero | same_95_evidence | supported_same_direction_and_95_evidence | status | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0_all | NB2 | z_gust_pressure | -0.03493370587 | -0.04564535517 | 0.01577102277 | 0.01802323505 | -0.06618817125 | -0.003679240488 | -0.08136317667 | -0.009927533668 | 0.02881706163 | 0.01273314697 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| E0_all | NB2 | gust_low | -0.02695219798 | -0.03929712703 | 0.004431726365 | 0.00755892471 | -0.03573483943 | -0.01816955653 | -0.05427714159 | -0.02431711247 | 1.759376809e-08 | 9.341228259e-07 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| E0_all | NB2 | gust_ramp | 0.1214617284 | 0.07562821857 | 0.01384287168 | 0.01566677282 | 0.09402840591 | 0.1488950509 | 0.04458035211 | 0.106676085 | 2.479346358e-14 | 4.494599126e-06 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| E0_all | Tweedie | z_gust_pressure | -0.03493370587 | -0.04109574505 | 0.01577102277 | 0.01547713243 | -0.06618817125 | -0.003679240488 | -0.07176778877 | -0.01042370132 | 0.02881706163 | 0.009101396633 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| E0_all | Tweedie | gust_low | -0.02695219798 | -0.04036497153 | 0.004431726365 | 0.007773333048 | -0.03573483943 | -0.01816955653 | -0.05576989309 | -0.02496004997 | 1.759376809e-08 | 9.587132561e-07 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| E0_all | Tweedie | gust_ramp | 0.1214617284 | 0.07824029824 | 0.01384287168 | 0.01472971803 | 0.09402840591 | 0.1488950509 | 0.04904945443 | 0.107431142 | 2.479346358e-14 | 5.720654175e-07 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Gamma | z_gust_0h | -0.0002452398944 | 0.01884011871 | 0.01920474572 | 0.01939157697 | -0.03830453821 | 0.03781405842 | -0.0195894353 | 0.05726967272 | 0.9898346183 | 0.3334000645 | 110 | False | False | False | True | False | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Gamma | z_gust_sq | 0.08096305923 | 0.06454836542 | 0.007413833277 | 0.008888910795 | 0.06627058184 | 0.09565553663 | 0.04693263061 | 0.08216410023 | 3.001918986e-19 | 5.791711971e-11 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Gamma | z_gust_precip | -0.02445446827 | -0.02541090714 | 0.00999507516 | 0.01026160901 | -0.04426236122 | -0.00464657533 | -0.04574700762 | -0.005074806657 | 0.01600262159 | 0.01479816593 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Tweedie | z_gust_0h | -0.0002452398944 | 0.03431788511 | 0.01920474572 | 0.02590852104 | -0.03830453821 | 0.03781405842 | -0.0170267224 | 0.08566249263 | 0.9898346183 | 0.1880561435 | 110 | False | False | False | True | False | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Tweedie | z_gust_sq | 0.08096305923 | 0.05884248122 | 0.007413833277 | 0.01256589651 | 0.06627058184 | 0.09565553663 | 0.03393982377 | 0.08374513866 | 3.001918986e-19 | 8.1349656e-06 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |
| R0c_all | Tweedie | z_gust_precip | -0.02445446827 | -0.02483783844 | 0.00999507516 | 0.01154939242 | -0.04426236122 | -0.00464657533 | -0.04772602336 | -0.001949653524 | 0.01600262159 | 0.03369896574 | 110 | True | True | True | True | True | available | same basis, different estimands; no coefficient magnitude equivalence or new model ranking |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
