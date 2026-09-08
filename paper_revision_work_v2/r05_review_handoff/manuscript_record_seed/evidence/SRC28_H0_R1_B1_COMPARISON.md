# H0 / R1 / B1实际对照

H0为冻结历史结果，本轮未重跑80次H0。R1已真实运行64次（4全样本+60嵌套OOF），不是把R02/R03候选表当作模型。B1为本轮冻结all_valid正式运行。

|条件|H0|R1输入兼容诊断|B1主方案|
|---|---|---|---|
|时间/天气|历史首行/旧天气|R02最早记录UTC代理与更新天气/年度人口|与R1相同R02输入|
|原因|旧first cause分组|保留旧first cause规则|R02全阶段共识资格|
|恢复尾部|各目标/总体先全样本p99截尾|历史同法，更新输入后重算各总体p99，再分折|all_valid，训练与测试完整有效尾部|
|fold|各总体独立GroupKFold日期分组|复制sklearn重现全部四组旧折算法，按更新日期重新分折|冻结共同1096 UTC日期映射，天气为其子集|
|变换|各训练折ddof=1，原科学列|相同训练变换和原设计|冻结契约设计、训练折变换|
|证据身份|历史比较|输入兼容诊断|修正基线；日OOF诊断|

R1历史全总体p99并不是尚未执行的“共同训练p99”备选，不作为新的主结果选项。H0→R1包括输入更新及由更新诱发的资格/日历/截尾点/折分变化；R1→B1包括取消截尾、共识资格与共同fold协议。不得全部归因某一时间修复，不能据R²选择尾部规则。

## 不同实际总体的评分

R²为log目标上的pooled和未加权mean-fold，二者分别列出；SSE/SST/n见CSV，H0表中未归档的汇总字段保持空值。R0c G为阵风一次、平方、气压交互；K为标准化ln(1+C)一次及平方。对照块共享目标总体内成员/折/权重。

| version | group | target | block | n | pooled_R2 | mean_fold_R2 |
| --- | --- | --- | --- | --- | --- | --- |
| H0 | main | E0 | control | 60437 | 0.017378002 | 0.017109395 |
| H0 | main | E0 | G | 60437 | 0.028123975 | 0.027770739 |
| H0 | main | R0c | control | 59834 | 0.025671746 | 0.022058061 |
| H0 | main | R0c | G | 59834 | 0.031869263 | 0.028014653 |
| H0 | main | R0c | K | 59834 | 0.10298755 | 0.10018762 |
| H0 | main | R0c | GK | 59834 | 0.11053659 | 0.10736674 |
| H0 | weather | E0 | control | 9857 | 0.021581834 | 0.019130767 |
| H0 | weather | E0 | G | 9857 | 0.020103347 | 0.018292917 |
| H0 | weather | R0c | control | 9758 | 0.18845119 | 0.13355022 |
| H0 | weather | R0c | G | 9758 | 0.20276463 | 0.14839497 |
| H0 | weather | R0c | K | 9758 | 0.19847164 | 0.14410152 |
| H0 | weather | R0c | GK | 9758 | 0.21558176 | 0.16171373 |
| R1 | main | E0 | control | 60436 | 0.017070955 | 0.016461057 |
| R1 | main | E0 | G | 60436 | 0.02945983 | 0.028730666 |
| R1 | main | R0c | control | 59832 | 0.025546223 | 0.02209678 |
| R1 | main | R0c | G | 59832 | 0.035457289 | 0.031461128 |
| R1 | main | R0c | K | 59832 | 0.10175888 | 0.099137108 |
| R1 | main | R0c | GK | 59832 | 0.11349336 | 0.11014688 |
| R1 | weather | E0 | control | 9857 | 0.019068346 | 0.018084878 |
| R1 | weather | E0 | G | 9857 | 0.02360737 | 0.023092434 |
| R1 | weather | R0c | control | 9758 | 0.18373578 | 0.12187176 |
| R1 | weather | R0c | G | 9758 | 0.21136136 | 0.14890401 |
| R1 | weather | R0c | K | 9758 | 0.19206951 | 0.13100932 |
| R1 | weather | R0c | GK | 9758 | 0.22458771 | 0.16269972 |
| B1 | main | E0 | control | 60436 | 0.017157091 | 0.016332043 |
| B1 | main | E0 | G | 60436 | 0.029621456 | 0.028723925 |
| B1 | main | R0c | control | 60436 | 0.021492205 | 0.019232831 |
| B1 | main | R0c | G | 60436 | 0.030601167 | 0.02759156 |
| B1 | main | R0c | K | 60436 | 0.080594631 | 0.078971139 |
| B1 | main | R0c | GK | 60436 | 0.092015832 | 0.089448842 |
| B1 | weather | E0 | control | 9857 | 0.020465821 | 0.015129311 |
| B1 | weather | E0 | G | 9857 | 0.024288284 | 0.020016566 |
| B1 | weather | R0c | control | 9857 | 0.19219972 | 0.12104927 |
| B1 | weather | R0c | G | 9857 | 0.22249889 | 0.14922109 |
| B1 | weather | R0c | K | 9857 | 0.20177367 | 0.13196143 |
| B1 | weather | R0c | GK | 9857 | 0.23757071 | 0.16554521 |

## 条件增量

表中单位为R²；乘100为百分点。G|K=GK−K，K|G=GK−G；另列从control加入的增量。跨主/天气总体只作点描述。

| version | group | target | gust_from_control | customers_from_control | gust_given_customers | customers_given_gust |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | main | E0 | 0.012464365 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| B1 | main | R0c | 0.0091089617 | 0.059102426 | 0.011421201 | 0.061414666 |
| B1 | weather | E0 | 0.0038224634 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| B1 | weather | R0c | 0.030299168 | 0.009573949 | 0.03579704 | 0.01507182 |
| H0 | main | E0 | 0.010745973 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| H0 | main | R0c | 0.0061975171 | 0.077315801 | 0.0075490441 | 0.078667328 |
| H0 | weather | E0 | -0.0014784876 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| H0 | weather | R0c | 0.014313443 | 0.010020449 | 0.017110118 | 0.012817124 |
| R1 | main | E0 | 0.012388875 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| R1 | main | R0c | 0.0099110663 | 0.076212654 | 0.011734488 | 0.078036076 |
| R1 | weather | E0 | 0.0045390235 | 未提供/不适用 | 未提供/不适用 | 未提供/不适用 |
| R1 | weather | R0c | 0.027625583 | 0.0083337322 | 0.032518202 | 0.013226351 |

## 形状和物理尺度

最低点条件于各档案自己的平均物理气压和支持；H0仅保留历史代数顶点，未重新认证。physical_quadratic为β2/sG²，二阶导数是其两倍。无当前最低点CI。

| version | group | target | n | beta_gust | beta_gust2 | beta_interaction | gust_mean | gust_sd | physical_quadratic | conditional_minimum_ms | minimum_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | main | E0 | 60436 | -0.03603576 | 0.10601982 | -0.04658362 | 9.9102224 | 5.2799794 | 0.0038029674 | 10.807545 | conditional_fitted_minimum |
| B1 | main | E0 | 60436 | -0.03603576 | 0.10601982 | -0.04658362 | 9.9102224 | 5.2799794 | 0.0038029674 | 10.807545 | conditional_fitted_minimum |
| H0 | main | E0 | 60437 | -0.032325899 | 0.10276171 | -0.040838436 | 9.8722968 | 5.2227131 | 0.0037673761 | 10.693755 | historical_algebraic_vertex_not_recertified |
| R1 | main | R0c | 59832 | -0.00072143523 | 0.084829212 | 0.021173963 | 9.9131351 | 5.27654 | 0.0030468212 | 9.9355724 | conditional_fitted_minimum |
| B1 | main | R0c | 60436 | -0.0073789491 | 0.087842132 | 0.020822883 | 9.9102224 | 5.2799794 | 0.0031509275 | 10.131988 | conditional_fitted_minimum |
| H0 | main | R0c | 59834 | 0.0001979069 | 0.079237451 | 0.025261497 | 9.8752348 | 5.2190181 | 0.0029090614 | 9.8687172 | historical_algebraic_vertex_not_recertified |
| R1 | weather | E0 | 9857 | 0.13294047 | 0.045698353 | -0.13649101 | 14.386994 | 7.2785135 | 0.00086261135 | 3.8000811 | conditional_fitted_minimum |
| B1 | weather | E0 | 9857 | 0.13294047 | 0.045698353 | -0.13649101 | 14.386994 | 7.2785135 | 0.00086261135 | 3.8000811 | conditional_fitted_minimum |
| H0 | weather | E0 | 9857 | 0.13432628 | 0.041895809 | -0.11661866 | 14.223202 | 7.1522164 | 0.00081901017 | 2.7574891 | historical_algebraic_vertex_not_recertified |
| R1 | weather | R0c | 9758 | 0.25657903 | 0.096514762 | 0.061970412 | 14.312974 | 7.2158268 | 0.0018536236 | 4.7215405 | conditional_fitted_minimum |
| B1 | weather | R0c | 9857 | 0.26334772 | 0.11363397 | 0.069537148 | 14.386994 | 7.2785135 | 0.0021449777 | 5.9529843 | conditional_fitted_minimum |
| H0 | weather | R0c | 9758 | 0.23068494 | 0.082411302 | 0.069526048 | 14.157184 | 7.0935442 | 0.0016377975 | 4.2290929 | historical_algebraic_vertex_not_recertified |

## 共同事件的预测变化（与总体评分分表）

共同ID上分别按各版本目标评分；max target差异明确列出。训练成员与日期fold仍可能不同，预测差异不是纯输入的因果分解。

| group | target | comparison | common_n | eta_difference_RMSE | left_common_R2 | right_common_R2 | target_max_difference | fold_same_n | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | E0 | H0→B1 | 60436 | 0.11092455 | 0.028121761 | 0.029621456 | 0 | 14677 | common-event descriptive comparison; training populations and date assignment differ |
| main | E0 | H0→R1 | 60436 | 0.11191696 | 0.028121761 | 0.02945983 | 0 | 15226 | common-event descriptive comparison; training populations and date assignment differ |
| main | E0 | R1→B1 | 60436 | 0.052542403 | 0.02945983 | 0.029621456 | 0 | 17865 | common-event descriptive comparison; training populations and date assignment differ |
| main | R0c | H0→B1 | 59834 | 0.086484439 | 0.11053659 | 0.11058509 | 1.7763568e-15 | 14159 | common-event descriptive comparison; training populations and date assignment differ |
| main | R0c | H0→R1 | 59832 | 0.05938184 | 0.11061265 | 0.11349336 | 1.7763568e-15 | 14715 | common-event descriptive comparison; training populations and date assignment differ |
| main | R0c | R1→B1 | 59832 | 0.074406137 | 0.11349336 | 0.11064546 | 0 | 14931 | common-event descriptive comparison; training populations and date assignment differ |
| weather | E0 | H0→B1 | 9857 | 0.20775101 | 0.020103347 | 0.024288284 | 0 | 3173 | common-event descriptive comparison; training populations and date assignment differ |
| weather | E0 | H0→R1 | 9857 | 0.2042723 | 0.020103347 | 0.02360737 | 0 | 3768 | common-event descriptive comparison; training populations and date assignment differ |
| weather | E0 | R1→B1 | 9857 | 0.1150973 | 0.02360737 | 0.024288284 | 0 | 3274 | common-event descriptive comparison; training populations and date assignment differ |
| weather | R0c | H0→B1 | 9758 | 0.14507221 | 0.21558176 | 0.22725018 | 8.8817842e-16 | 3130 | common-event descriptive comparison; training populations and date assignment differ |
| weather | R0c | H0→R1 | 9758 | 0.13254999 | 0.21558176 | 0.22458771 | 8.8817842e-16 | 3418 | common-event descriptive comparison; training populations and date assignment differ |
| weather | R0c | R1→B1 | 9758 | 0.087810609 | 0.22458771 | 0.22725018 | 0 | 3517 | common-event descriptive comparison; training populations and date assignment differ |

## 风暴与参考

H0历史风暴8.15%/14.72%不能直接继承；当前候选/实际模型/全主表详见storm_statistics.csv。当前曲线exp(meanη)、地图exp(日历加权meanη)、图7指数网格max/min，均使用新档案。H0旧地图/曲线只作历史，不混填新图或置信区间。主B1图9唯一4452事件全部在全拟合训练内；单独OOF版本每事件由未见该日期的模型预测，仍不是留出整个风暴的验证。
