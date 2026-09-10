# GI_STORM_METRICS

需求 I02；I.2–I.3。当前最终规格风暴预测、误差与紧凑图。

分析单位：incident。样本：accepted E0 all60437/weather9857; positive R0c all51173/weather9254; I all only。

模型：fixed final / exactly identified legacy controls; no model search。指标：pooled log-scale RMSE/MAE/bias; actual fixed gust bins and predicted quantiles; I seven windows and unique union。

验证：original fixed five LAD folds where row outputs absent; in-sample and OOF explicitly separate。

第三包G/I授权完成；只补当前模型底层数组和七场风暴描述；产物完成后待反馈，H未启动。

| storm | combination | prediction_type | excluded_from_primary_metrics | n | rmse | mae | mean_observed | mean_prediction | bias | r2 | correlation | correlation_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Arwen | E0_all | in_sample | False | 270 | 1.984402303 | 1.674331804 | 2.255372787 | 2.227825166 | -0.02754762071 | 0.007688564287 | 0.1147289768 | not calculated |
| Arwen | E0_all | LAD_OOF | False | 270 | 1.989922464 | 1.678309638 | 2.255372787 | 2.229537402 | -0.02583538541 | 0.002160110666 | 0.09909158647 | not calculated |
| Arwen | R0c_all | in_sample | False | 242 | 0.9212530384 | 0.7186004676 | 1.801447297 | 1.894449431 | 0.09300213356 | 0.05143163817 | 0.2664958458 | not calculated |
| Arwen | R0c_all | LAD_OOF | False | 242 | 0.9233859162 | 0.7208910257 | 1.801447297 | 1.901441919 | 0.09999462208 | 0.04703431764 | 0.2633702284 | not calculated |
| Arwen | R0c_all | display_only | True | 1 | 4.336729511 | 4.336729511 | 6.263048995 | 1.926319484 | -4.336729511 | NA | NA | not calculated |
| Dudley | E0_all | in_sample | False | 291 | 2.009282731 | 1.736092869 | 2.385458543 | 2.516953291 | 0.1314947477 | 0.08285238975 | 0.2966987306 | not calculated |
| Dudley | E0_all | LAD_OOF | False | 291 | 2.012042182 | 1.736490264 | 2.385458543 | 2.521164707 | 0.1357061633 | 0.08033152794 | 0.2921980822 | not calculated |
| Dudley | R0c_all | in_sample | False | 254 | 1.377269655 | 1.076350654 | 1.590482298 | 2.385437081 | 0.794954783 | -0.4699937402 | 0.1812452891 | not calculated |
| Dudley | R0c_all | LAD_OOF | False | 254 | 1.382684626 | 1.082245581 | 1.590482298 | 2.389037518 | 0.7985552197 | -0.4815755259 | 0.1701292048 | not calculated |
| Dudley | R0c_all | display_only | True | 2 | 3.390613378 | 3.356876191 | 5.806560369 | 2.449684179 | -3.356876191 | -69.95034915 | NA | not calculated |
| Eunice | E0_all | in_sample | False | 1659 | 2.297445141 | 1.97343319 | 3.409597132 | 3.130378912 | -0.2792182195 | 0.03307310073 | 0.2257622665 | not calculated |
| Eunice | E0_all | LAD_OOF | False | 1659 | 2.302107054 | 1.977088495 | 3.409597132 | 3.129928229 | -0.2796689032 | 0.02914499635 | 0.2193405887 | not calculated |
| Eunice | R0c_all | in_sample | False | 1518 | 1.710841587 | 1.437507407 | 3.187314472 | 2.624805253 | -0.5625092194 | -0.08405225835 | 0.2311886702 | not calculated |
| Eunice | R0c_all | LAD_OOF | False | 1518 | 1.717124712 | 1.442122503 | 3.187314472 | 2.625822342 | -0.5614921298 | -0.09202931915 | 0.2216209251 | not calculated |
| Eunice | R0c_all | display_only | True | 14 | 2.468478902 | 2.365961806 | 5.572103183 | 3.206141377 | -2.365961806 | -83.23309536 | -0.2507735173 | not calculated |
| Franklin | E0_all | in_sample | False | 1132 | 2.147280374 | 1.79017905 | 2.70995579 | 2.522782978 | -0.1871728118 | -0.01172774716 | 0.1033836541 | not calculated |
| Franklin | E0_all | LAD_OOF | False | 1132 | 2.154769601 | 1.794337778 | 2.70995579 | 2.516036579 | -0.1939192104 | -0.01879740834 | 0.08942276758 | not calculated |
| Franklin | R0c_all | in_sample | False | 1064 | 1.708951269 | 1.484501932 | 2.966981387 | 2.31783205 | -0.6491493365 | -0.04896139142 | 0.3283918292 | not calculated |
| Franklin | R0c_all | LAD_OOF | False | 1064 | 1.716275825 | 1.48996128 | 2.966981387 | 2.315962824 | -0.6510185624 | -0.05797234636 | 0.3118681444 | not calculated |
| Franklin | R0c_all | display_only | True | 4 | 2.812315517 | 2.792551824 | 5.540511055 | 2.747959231 | -2.792551824 | -163.346975 | -0.5185756739 | not calculated |
| Babet | E0_all | in_sample | False | 509 | 1.9511353 | 1.647857948 | 2.139311737 | 2.161445403 | 0.02213366525 | 0.03065979066 | 0.1777427322 | not calculated |
| Babet | E0_all | LAD_OOF | False | 509 | 1.954071037 | 1.649813422 | 2.139311737 | 2.167551726 | 0.02823998881 | 0.027740599 | 0.1679497546 | not calculated |
| Babet | R0c_all | in_sample | False | 449 | 0.9600512239 | 0.7378343854 | 1.897076523 | 1.855884154 | -0.04119236886 | 0.09309185362 | 0.3124400305 | not calculated |
| Babet | R0c_all | LAD_OOF | False | 449 | 0.9657340935 | 0.7427675059 | 1.897076523 | 1.856675088 | -0.04040143468 | 0.08232348158 | 0.298177588 | not calculated |
| Babet | R0c_all | display_only | True | 1 | 4.049363083 | 4.049363083 | 5.885640961 | 1.836277878 | -4.049363083 | NA | NA | not calculated |
| Ciaran | E0_all | in_sample | False | 576 | 2.048505843 | 1.787322082 | 2.280156726 | 2.529523041 | 0.2493663149 | 0.1260103989 | 0.3852811578 | not calculated |
| Ciaran | E0_all | LAD_OOF | False | 576 | 2.052894988 | 1.791447277 | 2.280156726 | 2.535389999 | 0.255233273 | 0.1222611518 | 0.3798441035 | not calculated |
| Ciaran | R0c_all | in_sample | False | 466 | 1.066136453 | 0.8199994295 | 1.873626048 | 1.951573645 | 0.07794759645 | 0.04804074928 | 0.252306435 | not calculated |
| Ciaran | R0c_all | LAD_OOF | False | 466 | 1.067716247 | 0.8209046366 | 1.873626048 | 1.946843267 | 0.07321721899 | 0.0452174451 | 0.2485772662 | not calculated |
| Ciaran | R0c_all | display_only | True | 2 | 5.30445971 | 5.293207722 | 6.775197401 | 1.48198968 | -5.293207722 | -28584.62417 | NA | not calculated |
| Henk | E0_all | in_sample | False | 494 | 2.057078865 | 1.765832854 | 2.866812264 | 2.694070332 | -0.1727419321 | 0.1145167697 | 0.3475496605 | not calculated |
| Henk | E0_all | LAD_OOF | False | 494 | 2.058920831 | 1.767177473 | 2.866812264 | 2.697457887 | -0.1693543774 | 0.1129302867 | 0.3448694095 | not calculated |
| Henk | R0c_all | in_sample | False | 439 | 1.175981473 | 0.9182553078 | 1.828533282 | 1.78742474 | -0.04110854122 | 0.05688111049 | 0.2491978544 | not calculated |
| Henk | R0c_all | LAD_OOF | False | 439 | 1.180498954 | 0.9220081505 | 1.828533282 | 1.783233564 | -0.04529971799 | 0.04962129315 | 0.2383390918 | not calculated |
| Henk | R0c_all | display_only | True | 4 | 3.972160837 | 3.958407492 | 5.673485721 | 1.715078229 | -3.958407492 | -71.44113573 | 0.860963269 | not calculated |
| UNION_DEDUPLICATED | E0_all | in_sample | False | 4452 | 2.138684911 | 1.827296576 | 2.810204703 | 2.732746062 | -0.07745864146 | 0.09801631438 | 0.3150859097 | not calculated |
| UNION_DEDUPLICATED | E0_all | LAD_OOF | False | 4452 | 2.143502542 | 1.830667595 | 2.810204703 | 2.733185949 | -0.07701875405 | 0.09394809554 | 0.3084160205 | not calculated |
| UNION_DEDUPLICATED | R0c_all | in_sample | False | 3990 | 1.454035107 | 1.166914957 | 2.525359759 | 2.268461558 | -0.2568982017 | 0.1296065031 | 0.3962317554 | not calculated |
| UNION_DEDUPLICATED | R0c_all | LAD_OOF | False | 3990 | 1.45969038 | 1.171182921 | 2.525359759 | 2.268119673 | -0.2572400863 | 0.1228227806 | 0.3873956758 | not calculated |
| UNION_DEDUPLICATED | R0c_all | display_only | True | 28 | 3.243277786 | 3.064770106 | 5.720629899 | 2.655859793 | -3.064770106 | -53.43682797 | -0.4626577022 | not calculated |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
