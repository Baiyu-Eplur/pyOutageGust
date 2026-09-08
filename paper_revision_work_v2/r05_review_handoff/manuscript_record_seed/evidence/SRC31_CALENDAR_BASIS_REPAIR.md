# R04 图10等价日历基修复：实际验收

8个独立分期档案均已生成并再读校验。主/天气各E0、R0c和earlier/later均检查；核心冻结运行曾跳过后期的事实保留，图10改消费独立 periods_v2 档案。未改R03源代码或核心档案。

| group | target | period | n | old_rank/k | new_rank/k | removed | space_maxerr | eta_maxerr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | E0 | development | 48323 | 25/25 | 25/25 | none | 3.126388e-13 | 0 |
| main | E0 | later | 12113 | 18/19 | 18/18 | month_12 | 5.9952043e-14 | 1.4210855e-14 |
| main | R0c | development | 48323 | 27/27 | 27/27 | none | 3.0198066e-13 | 0 |
| main | R0c | later | 12113 | 20/21 | 20/20 | month_12 | 2.8421709e-14 | 2.6645353e-15 |
| weather | E0 | development | 7750 | 25/25 | 25/25 | none | 8.437695e-14 | 0 |
| weather | E0 | later | 2107 | 17/18 | 17/17 | month_12 | 2.3536728e-14 | 1.0214052e-14 |
| weather | R0c | development | 7750 | 27/27 | 27/27 | none | 9.0594199e-14 | 0 |
| weather | R0c | later | 2107 | 19/20 | 19/19 | month_12 | 2.8865799e-14 | 4.8849813e-15 |

预测期为UTC [2021-04-01,2024-04-01)，later自2023-09-30。后期实际满足 I(year=2024)=I(month∈{1,2,3})，残差为0。在截距及January参考编码下，冗余涉及截距、年份及其余月份；不是阵风与客户项的删选。

固定顺序保留全部实质列和截距，按原日历列顺序逐列加入能增加秩者。秩选择时列以其欧氏范数归一化，绝对阈值1e-10；原始设计和系数未重缩放。四个后期均仅移除month_12。样本列空间双向最小二乘映射及残差、原/新条件数见 checks/calendar_equivalence.json；容许误差1e-7，实际拟合值差异最大约1.42e-14。

用原设计零空间检查所有科学协变量的参数唯一性，包括阵风一次/二次/气压交互、客户项、其他天气及区域项。原截距可与冗余日历共享零空间方向，因此不把原截距或全部原日历系数说成唯一。新基保留截距。旧广义逆仅用于均值投影核对，其日历系数不作单独解释或跨编码比较。

每个档案保存训练ID、设计列、预处理、实际year×month支持。已见组合上的再读预测逐值一致；未支持组合直接报错（2099测试已拒绝）。等价性仅在这些组合及可表达的实质变量行上成立，不扩展到缺失年月组合。

各期采用自己的ddof=1训练尺度。报告物理阵风二次项q=β2/sG²，二阶导数为2q，两者不可混称。气压参考为同一group/target全时期模型的物理均值：主组1012.074826 hPa，天气组1004.983606 hPa；再在各期自己的压力尺度上转换。该共同参考仅用于同一组内分期比较。天气E0早期的代数顶点不在p1–p99支持内，最低点返回未提供，不画作有效最低点。

CR1按有效满秩k计算 G/(G−1)·(n−1)/(n−k)，分别记录LAD、date和交集，并形成双向矩阵。实际样本与复制的statsmodels协方差实现核对。全部分期矩阵的非有限/负对角状态另见 period_covariance_acceptance.json；没有使用旧冗余列数修正因子，也没有拼接重叠CV拟合的逆方差区间。图10仅为全分期拟合的物理尺度点比较；不证明时间稳定性，不新增最低点CI。

原失败的开发期部分档案保留在 periods/；最终可消费版本为 periods_v2/，配置为 configs/period_equivalent_v1.json（run_id沿用其声明的R04_period_equivalent_v1，路径及最终生产者SHA另行绑定）。失败日志保留，不把初次截距零空间断言误写成科学变量不可识别。
| group | target | period | n | old_k | rank | removed_calendar | beta_gust | beta_gust2 | physical_linear_gust | physical_quadratic_gust | pressure_physical | cross_period_independence_assumed | CV_inverse_variance_interval | physical_linear_SE | physical_quadratic_SE | minimum_ms | minimum_status | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | E0 | development | 48323 | 25 | 25 | 未提供/不适用 | -0.08960752 | 0.089107768 | -0.077754622 | 0.0032035588 | 1012.0748 | False | 未提供/不适用 | 0.0081774201 | 0.00035878096 | 12.135664 | conditional_fitted_minimum | equivalent_basis_verified |
| main | E0 | later | 12113 | 19 | 18 | month_12 | 0.066153463 | 0.17076117 | -0.12288387 | 0.0062839873 | 1012.0748 | False | 未提供/不适用 | 0.014458529 | 0.00061166134 | 9.77754 | conditional_fitted_minimum | equivalent_basis_verified |
| main | R0c | development | 48323 | 27 | 27 | 未提供/不适用 | -0.015235599 | 0.078492117 | -0.057717858 | 0.0028219101 | 1012.0748 | False | 未提供/不适用 | 0.0058130031 | 0.00028450047 | 10.226736 | conditional_fitted_minimum | equivalent_basis_verified |
| main | R0c | later | 12113 | 21 | 20 | month_12 | -0.014773078 | 0.070813419 | -0.057055106 | 0.002605924 | 1012.0748 | False | 未提供/不适用 | 0.011328779 | 0.00043125033 | 10.947193 | conditional_fitted_minimum | equivalent_basis_verified |
| weather | E0 | development | 7750 | 25 | 25 | 未提供/不适用 | 0.02760802 | 0.012618089 | 0.0011580652 | 0.00022477652 | 1004.9836 | False | 未提供/不适用 | 0.020971265 | 0.00063588972 | 未提供/不适用 | unavailable | equivalent_basis_verified |
| weather | E0 | later | 2107 | 18 | 17 | month_12 | 0.40232531 | 0.15943088 | -0.062798913 | 0.0040095229 | 1004.9836 | False | 未提供/不适用 | 0.040941146 | 0.0012498308 | 7.8312202 | conditional_fitted_minimum | equivalent_basis_verified |
| weather | R0c | development | 7750 | 27 | 27 | 未提供/不适用 | 0.20409697 | 0.10748417 | -0.027808122 | 0.0019147049 | 1004.9836 | False | 未提供/不适用 | 0.017901058 | 0.00063540407 | 7.2617252 | conditional_fitted_minimum | equivalent_basis_verified |
| weather | R0c | later | 2107 | 20 | 19 | month_12 | 0.33115194 | 0.11871773 | -0.029311561 | 0.0029856291 | 1004.9836 | False | 未提供/不适用 | 0.024788116 | 0.00074912889 | 4.9087748 | conditional_fitted_minimum | equivalent_basis_verified |
