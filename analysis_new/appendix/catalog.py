"""Three-layer evidence mapping, frozen before implementing exporters (2026-09-10).

This is the single editable registry. CSV views are generated from it, not edited.
Paragraph IDs count direct body paragraphs including empty paragraphs in DOCX XML.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = 'results/new/20260909183317/results/'
P03 = 'results/new/20260909205214/results/p03_p04/'
AGG = 'results/new/20260909231634/results/dd_agg01/'
DUR = 'results/new/20260910090006/results/dd_dur01/'
TIME = 'results/new/20260910104718/results/dd_time01/'
DATA = 'review_package/data/'
OLD = 'results/pretest/archive/20260909154556/results/'
MANUSCRIPT = MAIN + 'paper/Extended_paper_draft.docx'
PLAN = 'docs/new_analysis/instructions/论文整合计划_v9_附录成文与正文衔接.md'
E0 = DATA + 'combined_E0_final.csv'
R0 = DATA + 'combined_R0c_final.csv'
TITLES = dict(zip('ABCDEFGHIJ', ['数据、变量、原因与样本','事件重建与恢复样本','候选规格比较','结点估计与已有不确定性','事件级分期证据','完整系数与增量解释度','事件级预测与残差','替代结果模型与事件条件概率','命名风暴','地区日方法与验证']))
REQUIREMENTS = []

def req(rid, section, location, claim, need, status, action, sources, producer, *,
        unit='incident', sample='E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准',
        model='见需求说明；不合并不同规格排名', metrics='见来源字段，原单位', validation='只读已有结果；本轮不拟合',
        body='', note='', gap='', review='', config=None):
    REQUIREMENTS.append(dict(requirement_id=rid, claim_id='CL_'+rid, appendix=rid[0], subsection=section,
        location=location, claim=claim, question=need, source_status=status, action=action, sources=sources,
        producer=producer, unit=unit, sample=sample, model=model, metrics=metrics, validation=validation,
        body_existing=body, duplicate_body=bool(body), scope_note=note, gap=gap, review=review, config=config or {}))

req('A01','A.1–A.3','§2.1 P015; §2.4 P026–027','研究事件来源、原因类别与分析样本不同','固定输入的样本量、原因计数和日期/LAD覆盖', 'DERIVE','samples',[E0,R0], 'analysis_new/final_models.py; weather_only_regression.py',note='恢复回归剔除零客户；不能把59834称为最终恢复样本。')
req('A02','A.2','§2.1 P015; §3.1 P031; Table 2','结果变换和协变量定义决定回归尺度','变量、单位、来源、变换、参考水平', 'FORMAT','dictionary',[E0,R0,'docs/Appendix_revised_copy.docx','analysis_new/final_models.py','analysis_new/model_selection.py'], 'analysis_new/model_selection.py:design; final_models.py:final_design',note='正文使用变换后OLS；不是GLM log link。地区变量定义复用旧附录A，不迁移旧同字母章节的结论。')
req('A03','A.1','§2.4 P026–027','六类原因分组；主样本只保留天气和资产','原始原因代码映射', 'READY','docx_table',['docs/Appendix_revised_copy.docx'], '已成型附录A Table A1',config={'table':0},note='复用已有原因字典，未对监管原始代码重新审计；样本实际组别见A01。')
req('A04','A.4','§2.3 P021; §2.4 P028','协变量分布及VIF支持设计说明','固定最终设计矩阵的VIF描述统计', 'DERIVE','vif',[E0,R0,'analysis_new/model_selection.py','analysis_new/final_models.py',MAIN+'model_selection/knots.json',MAIN+'final_models/E0_final_twoway.csv',MAIN+'final_models/R0c_final_twoway.csv'], 'analysis_new/model_selection.py:design; final_models.py:final_design',model='当前全体最终设计矩阵，不读取响应变量拟合',metrics='VIF=预测列相关矩阵逆矩阵对角线；包含虚拟变量控制，不含截距',note='复用原纯设计函数的隔离适配层，不执行旧模块顶层运行/拟合。全设计VIF与仅原始连续变量的VIF不是同一口径；不据此调整模型。')
req('A05','A.4','§2.4 P027; §4.2 P058','天气原因份额随gust变化是样本构成描述','已有固定十分位原因构成数据', 'FORMAT','csv',[OLD+'c09_final_cleanup_20260905/raw/appendixG_table_G1_corrected.csv'], 'scripts/c09_final_cleanup_20260905/appendixG_recompute.py',sample='C01 corrected combined WT，包括16条C缺失记录；表中n合计60453',metrics='gust_min/max m/s；pct_weather_natural为百分数，n为计数',note='既有十分位表约6.93%至57.06%；不把它解释成因果分解，也不能替代未定位的91%端点，见A06。')
req('A06','A.4','§2.4 P027','正文天气原因份额7%至91%的具体口径','与91%端点匹配的既有分箱/计数', 'LOCATE','gap',[], 'Extended P027；已有原因十分位来源见A05',gap='已找到的固定十分位表最高箱为57.06%，正文91%所用区间/样本计数未定位；两者不能直接替换。需要人工定位该句的分箱来源或按已存十分位证据限定文字，不新增分箱或推断原因。')
req('B01','B.1–B.2','§2.2 P019','客户数排除再中断；时长保留全部阶段跨度','事件构造规则和代表行修复证据', 'FORMAT','construction',[OLD+'c01_repair_20260905/raw/step1_summary.json','scripts/code_audit_20260905/audit_pipeline.py','scripts/c02_c08_repair_20260905/corrected_sample_builder.py','docs/Appendix_revised_copy.docx'], 'C01 representative row repair; corrected_sample_builder',note='C01清理计数为历史全事件构建范围，不能当作当前60437行回归样本。')
req('B02','B.3–B.4','§2.2 P019; §2.3 P021','零客户时长特征与两种时长定义','在固定恢复输入上汇总零客户/正客户、1小时、A/B时长', 'DERIVE','duration',[R0], '固定输入字段 duration_A_customer_weighted_hours / duration_B_full_span_hours',metrics='计数、比例；时长h',note='不从1小时峰直接推断自动重合闸；加权时长和跨度的差别不自动证明伪相关。')
req('B03','B.1','§2.2 P019','第一阶段客户数会低估重建事件客户数','第一阶段对完整事件的已有比较', 'FORMAT','docx_table',['docs/Appendix_revised_copy.docx'], '已成型附录B.1',config={'paragraphs':[17,18]},note='仅保存既有文字证据及其历史样本说明；不把旧聚合均值直接当作当前E0重新计算结果。')
req('C01','C.1–C.3','§3.1 P031; §3.2 P034; P096','已有候选规格阶梯与性能比较','全体两结果的12项完整候选表与定义', 'FORMAT','csv',[MAIN+'model_selection/all_model_comparison.csv','analysis_new/model_selection.py'], 'analysis_new/model_selection.py:design,run_margin',sample='E0=60437；此候选R0c=59834（包含零客户），区别当前最终恢复51173',metrics='AIC/BIC、R²、log尺度RMSE',validation='来源既定random/LAD/year CV；不与嵌套搜索混成一个排名',config={'files':1},note='C01恢复候选梯级不是当前正客户最终规格的同样本12项比较。')
req('C02','C.2–C.4','§3.2 P035; §4.1 P049; §4.2 P058','平台与自由分段的既有比较','全体/天气平台比较和各自nested CV', 'FORMAT','ramp',[MAIN+'model_selection/ramp_model.json',MAIN+'model_selection/ramp_model_R0c.json'], 'analysis_new/plateau_model.py',sample='E0全体60437/天气9857；R0c平台比较为正客户全体51173/天气9254',metrics='来源简化BIC、nested RMSE、LR；只在同一来源分组内比较',note='来源简化BIC省略常数，不能跨表与statsmodels完整BIC直接相减。C01的R0c阶梯包含零客户，不与本表混成排名。')
req('C03','C.1','§4.2 P058–062; P096','天气样本候选结果','已保存天气quadratic/hinge/final候选摘要', 'FORMAT','csv',[MAIN+'weather_only/weather_only_pred_vs_obs.csv'], 'analysis_new/weather_only_regression.py',sample='E0 weather=9857；恢复weather=9254',metrics='LAD-CV log尺度RMSE、R²、校准斜率',note='当前已定位3种而非完整12种天气候选。')
req('C04','C.1','P096 Supplementary C','正文附录目录声称各样本完整12项候选','天气样本及最终恢复清理口径的完整12项阶梯', 'LOCATE','gap',[], 'analysis_new/model_selection.py',gap='当前model_selection保存全体E0及含零客户R0c各12项；weather_only保存3项。未定位天气完整12项，也未定位与最终51173条正客户恢复样本匹配的12项梯级。若无更多既有产物，写作应限定已完成候选数量与清理口径；本轮不补训。')
req('D01','D.1–D.4','§3.2 P035; §4.1 P049–051','结点位置与已有profile/bootstrap/nested折号','结点区间和训练折结点摘要', 'FORMAT','knots',[MAIN+'model_selection/knots.json',MAIN+'model_selection/ramp_model.json',MAIN+'model_selection/ramp_model_R0c.json'], 'analysis_new/knot_estimation.py; plateau_model.py',metrics='结点m/s、既有95%区间、已保存折结点',note='自由双结点500次与平台300次bootstrap分别标注；R0c自由分段59834含零客户，平台51173/9254为正客户；平台是候选，不是正文最终二次恢复模型的结点。')
req('D02','D.1–D.2','§4.1 P049–051; P097','平台结点定位的补充证据','E0全体及天气平台profile与bootstrap补充图及最小数据', 'FORMAT','profiles',[MAIN+f'model_selection/E0_{s}_plateau_{k}.csv' for s in ['all','weather'] for k in ['profile','bootstrap']], 'analysis_new/plateau_model.py',metrics='来源LR；bootstrap计数',body='Figure 4为自由分段profile；此图补充平台规格',note='使用已保存profile网格和bootstrap样本；不重新搜索或bootstrap。')
req('E01','E.1–E.3','§3.3 P038; §4.5 P077; Table 8','开发/后续两期事件回归比较','两期设计及已保存关键系数完整列出', 'FORMAT','period',[MAIN+'paper/paper_extras.json','analysis_new/paper_extras.py'], 'analysis_new/paper_extras.py',metrics='系数、两维SE、p、n',body='Table 8只列部分核心斜率；此表加入已存交互和SE',note='两个时期分别拟合，规格沿用全期选择；不是开发期冻结预测。时期此前已用于探索。没有保存完整分期系数，不补训。')
req('F01','F.1–F.2','§3.4 P040; §4.1 P052–053; §4.2 P061','四组最终规格及聚类推断','四组完整双向聚类系数和全体LAD-only对照', 'FORMAT','coefficients',[MAIN+f'final_models/{m}_final_{se}.csv' for m in ['E0','R0c'] for se in ['lad','twoway']]+[MAIN+f'weather_only/{m}_weather_final_twoway.csv' for m in ['E0','R0c']], 'analysis_new/final_models.py; weather_only_regression.py',metrics='coef、SE、normal p及t(G-1) p（按源字段）',note='G为LAD数；最终公式为对数结果OLS；参考水平和标准化见A02。')
req('F02','F.2','§3.4 P040; P099','单向与双向SE敏感性','天气最终规格LAD-only SE', 'LOCATE','gap',[], 'analysis_new/weather_only_regression.py',gap='当前weather_only只保存twoway完整表；不存在可直接配对的weather-final LAD-only系数文件。不得以全体或旧规格SE补位；需定位匹配产物，若必须重拟合则后续人工决定。')
req('F03','F.3','§4.3 P064; Table 6','变量块顺序加入的增量解释度','四组完整顺序增量结果', 'FORMAT','csv',[MAIN+'paper/r2_decomposition.csv'], 'analysis_new/paper_extras.py',metrics='OOF R²及增量（比例，非百分数）',validation='固定LAD-CV顺序分解',body='Table 6 / Figure 7；此表保留累计和样本信息',note='Regional + calendar是联合块，不能写成calendar单独贡献；顺序分解不是唯一因果分解。')
req('G01','G.1–G.2','§4.1 P055–056; P100','模型平均关系与单事件预测差距','已有各候选同规格样本内/OOF摘要', 'FORMAT','csv',[MAIN+'model_selection/predicted_vs_observed_summary.csv'], 'analysis_new/plot_model_selection.py',sample='E0=60437; 此梯级R0c=59834包含零客户',metrics='log尺度RMSE、R²、相关、校准斜率',note='属于较早候选诊断，不把不同清理版本差别归因于函数改进；最终汇总另见G02。')
req('G02','G.1–G.2','§4.1 P052–056; §4.2 P062','当前最终模型预测表现','最终全体和天气样本RMSE/R²摘要', 'FORMAT','final_prediction',[MAIN+'final_models/final_summary.json',MAIN+'weather_only/weather_only_pred_vs_obs.csv'], 'analysis_new/final_models.py; weather_only_regression.py',body='Figure 5已有最终预测图，不重复迁入',note='全体final_summary保存RMSE，不保存完整最终OOF逐行值；天气pvo包含3候选均如实保留。')
req('G03','G.3','§4.1 P046; §4.2 P062; P100','gust区间偏差与支持','最终模型固定分箱残差、n和校准绘图数据', 'LOCATE','gap',[], 'analysis_new/final_models.py; weather_only_regression.py',gap='最终图11/13/14存在，但当前运行未保存配套逐行OOF和完整分箱残差表；仅有图像不能可靠导出数字。不新分箱、不重拟合；后续先定位图表原始数据。')
req('H01','H.1–H.2','§3.1 P031; §4.4 P070; P101','替代分布和序数模型的条件对象不同','已保存NB和序数/逐阈logit结果', 'FORMAT','ordinal',[MAIN+'model_selection/fragility_summary.json'], 'analysis_new/fragility_demo.py',sample='E0=60437；R0c=59834（含零客户）；既有探索规格',model='E0自由结点14/26，R0c单结点17；不是最终E0平台14/25或正客户恢复',note='可用于事件条件方法说明；不是当前最终规格分布稳健性证明。McFadden字段null保留缺失。')
req('H02','H.3','§4.4 P070; P101','事件已发生条件下的阈值超越概率','已保存事件条件lognormal参数与曲线', 'FORMAT','conditional',[MAIN+'model_selection/fragility_lognormal.json',MAIN+'model_selection/fragility_optimizer_diagnostics.json'], 'analysis_new/fragility_surfaces.py',sample='源JSON E0全体60437/天气9857，恢复59834/天气9806，含零客户',model='事件条件lognormal；并非district-day背景率模型',note='参数仅按既有记录导出，边界/优化诊断保留；极端theta不能当作有效物理阈值。不导出新增降水交互曲面。')
req('H03','H.1','§3.1 P031; P101','替代Gamma/Tweedie与正文一致性','匹配当前最终样本/规格的替代分布证据', 'LOCATE','gap',[], '历史appendix_h_20260906/raw/stepB_distribution_check_corrected.json',gap='找到旧二次模型E0=60437/R0=59834的Gamma/Tweedie比较，无法支持当前平台及正客户恢复的同规格稳健性主张。本轮不转为当前排名；最小动作是定位匹配结果或限定文字，不能为凑表重训。')
req('I01','I.1','§4.5 P077; P102','七场命名风暴窗口和事件覆盖','固定窗口内当前样本计数及客户总量', 'DERIVE','storms',[E0,R0,'scripts/c02_c08_repair_20260905/figure9_storm_validation.py'], 'figure9_storm_validation.py:STORMS（仅解析常量，不执行旧拟合）',metrics='各窗口事件数、客户总量；重叠窗口另提供去重并集',note='只汇总已有窗口；不把窗口描述当作预测验证。')
req('I02','I.2–I.3','§4.5 P077; P102','命名风暴期间当前事件模型表现','当前最终规格风暴预测、误差与紧凑图', 'LOCATE','gap',[], '历史figure9_storm_validation.py; analysis_new/paper_extras.py',gap='定位到旧二次规格风暴逐行预测，当前最终E0平台/正客户R0的风暴预测未定位。旧预测不能支撑当前最终规格风暴表现；不重训。先定位既有当前预测，再按既定窗口汇总。')
req('J01','J.1','§3.5 P042–043; §4.4 P070–072','地区日分母、八标签和事后事件锚点proxy','构造定义与现有面板标签数量', 'DERIVE','panel',[MAIN+'final_models/district_day_panel.csv','analysis_new/district_day_core.py','analysis_new/district_day_fragility.py'], 'district_day_core:BW_KM,KMIN; district_day_fragility.py标签构造',unit='LAD-day',sample='111 LAD × 1096日期',model='p0+(1-p0)Phi((ln g-ln theta)/beta)',metrics='八标签阳性数、比例',note='当天事件坐标均值中心、40km Gaussian/distance插值，非ERA5日最大；任意事件包含零客户，其他阈值严格>且为至少一个事件。只读定义和标签，不审计历史拟合。')
req('J02','J.2','v9 §3 J.2；§5.5 P089的已接受补充','独立网格天气与proxy定义不同','既有覆盖和天气数值比较', 'FORMAT','grid',[P03+'gust_comparison.csv',P03+'grid_cells.csv',P03+'centroids.csv',P03+'experiment.json',P03+'quality.json'], 'analysis_new/grid_weather.py; p03_p04_grid_weather.py',unit='LAD-day / LAD centroid',sample='111 LAD，2021-04-01至2024-03-31',metrics='天气差值m/s、RMSE m/s、相关（不是概率评分）',note='覆盖/天气数据可复用；不导入P03历史模型排名或旧置信区间。再分析值不是气象站真值，也非LAD全域最大。')
req('J03','J.2','v9 §3 J.2；§4.3成果登记','独立天气替代的有效公平对照','已接受且两端优化有效的proxy/grid全八任务比较', 'MISSING','gap',[], 'DD-AGG01 baseline_repair_comparison; 历史P03',unit='LAD-day',gap='P03含后来确认失效的稀有任务解；DD-AGG01修复了网格A01端，未找到同时匹配有效proxy端及同轮不确定性的全八项最终表。只保留天气定义/数值比较，不能新点估计拼旧区间；不重启关闭审计。')
req('J04','J.3','v9 §3 J.3 / §4.3成果登记','五种日度聚合在同一ERA5分支比较','八任务五候选完整指标与既有配对区间', 'FORMAT','csv',[AGG+'metrics.csv',AGG+'paired_uncertainty.csv',AGG+'aggregation_summary.csv'], 'analysis_new/daily_aggregations.py; dd_agg01_evaluation.py',unit='LAD-day',sample='111×1096；固定LAD折',model='A01最大/A02均值/A03Q90/A04top3/A05rolling3',metrics='Brier、相对A01增益、BSS、已有校准RMSE和已有配对区间',validation='来源固定LAD-CV，来源已有区间；本轮不重采样',review=AGG+'REPORT.md',note='仅在本实验同任务候选内比较；不把不同评估集Brier或不同分箱校准RMSE跨实验排名。')
req('J05','J.4','v9 §3 J.4 / §4.3成果登记','持续性指标相对日最大值的增量','八任务三模型指标、阈值、既有配对区间', 'FORMAT','csv',[DUR+'metrics.csv',DUR+'paired_uncertainty.csv',DUR+'thresholds.csv'], 'analysis_new/duration_features.py; dd_dur01.py',unit='LAD-day',sample='与DD-AGG01一致ERA5及固定LAD折',model='M0日最大；M1增加h=H/24；M2增加x=log1p(sum(max(g_h²-tau²,0))/(24tau²)))',metrics='Brier/增益/BSS；tau(m/s)；既有区间',validation='tau仅训练小时Q90；冻结折号；无本轮拟合',review='docs/new_analysis/dd_dur01/20260910090006/RESULTS_SUMMARY.md',note='H为超阈小时计数，不是最长连续时长；平方累计非结构损伤测量。保留稀有任务微小正向结果。')
req('J06','J.5','v9 §3 J.5；§4.5 已接受新增','正文proxy固定规格回顾性时间迁移','八任务开发/评估率、平均偏差、Brier/BSS与支持表', 'FORMAT','time',[TIME+'temporal_metrics.csv',TIME+'sample_summary.csv',TIME+'monthly_metrics.csv',TIME+'covariate_support.csv',TIME+'development_fit.csv',TIME+'protocol.json'], 'analysis_new/temporal_fragility.py; dd_time01_outputs.py',unit='LAD-day',sample='开发2021-04-01–2023-09-29；评估2023-09-30–2024-03-31；同111LAD',model='开发期背景率lognormal冻结；开发阳性率常数基准',metrics='Brier/BSS为比例；平均偏差另列概率百分点',review='docs/new_analysis/reviews/DD_TIME01_REVIEW.md',note='回顾性，评估期此前参与探索；事后proxy构造下跨期迁移，不是提前预警。开发期参数不可替换正文全期参数。')
req('J07','J.5','v9 §5 图形呈现','重点任务风险校准和月度表现并不完全一致','全体>100与天气>100校准/月度四面板及八任务既定箱数据', 'FORMAT','time_figure',[TIME+'calibration_bins.csv',TIME+'monthly_metrics.csv'], 'analysis_new/dd_time01_outputs.py已存分箱/预测；复用项目figure_style',unit='LAD-day',sample='后续评估期；两个重点任务，其他六项全指标见J06',metrics='预测概率/实际发生率；每箱n、阳性数',validation='沿用开发十分位分箱，空箱留缺失；不移动箱边界',note='2023-09只有9月30日一天，不与完整月份等量解释；稀疏箱不连成尾部趋势。显示轴覆盖全部非空箱均值，1.15倍最大值向上取0.05整倍数；仅排版，不重分箱。')
req('J08','J.6','v9 §3 J.6；§5.5 P089','已完成探索与剩余限制','方法/用途/不可支持解释的简明登记', 'FORMAT','boundaries',[PLAN,TIME+'protocol.json',AGG+'PROTOCOL.md',DUR+'PROTOCOL.md',AGG+'experiment.json',DUR+'protocol.json'], '已接受v9及三实验冻结协议',unit='LAD-day',note='不声称等效、统计显著或完全校准；不自动提出模型替换。')
for rid, claim in [('J09','正文proxy历史全样本/LAD折内数值专项审计'),('J10','旧proxy支持上限、尾部样本与g50历史核查'),('J11','incident平台结点与district-day概率位置联系'),('J12','锚点覆盖及自身锚点剔除诊断')]:
    req(rid,'J.6','研究负责人关闭决定；v9 §1；P074/P089仅作关闭定位',claim,'关闭事项登记','CLOSED','gap',[], '用户决定',unit='不执行',gap='用户明确停止或未授权；不作为本轮生产的待执行门槛。')

# APP-C-COMPLETE explicitly supersedes the earlier export-only C authorization.
# Other appendix registry entries and scientific products remain unchanged.
C_SOURCES = [E0,R0,'analysis_new/model_selection.py','analysis_new/final_models.py',
 'analysis_new/weather_only_regression.py','analysis_new/knot_estimation.py','analysis_new/plateau_model.py','analysis_new/basis_solver.py',
 MAIN+'model_selection/E0_model_comparison.csv',MAIN+'model_selection/E0_coefficients.xlsx',
 MAIN+'model_selection/knots.json',MAIN+'model_selection/ramp_model.json',MAIN+'model_selection/ramp_model_R0c.json',
 MAIN+'final_models/final_summary.json',MAIN+'weather_only/weather_only_summary.json']
C_SOURCES += [MAIN+f'final_models/{m}_final_twoway.csv' for m in ['E0','R0c']]
C_SOURCES += [MAIN+f'weather_only/{m}_weather_{s}_twoway.csv' for m in ['E0','R0c'] for s in ['paper','hinge','final']]
for r in REQUIREMENTS:
    if r['appendix']!='C':continue
    r.update(source_status='COMPLETION',action='c_complete',sources=C_SOURCES,
        producer='analysis_new.appendix.c_completion:generate',sample='E0 all60437/weather9857; positive R0c all51173/weather9254',
        model='exact original ladder + separately matched final controls',metrics='full Gaussian OLS AIC/BIC; pooled log-response RMSE',
        validation='original LAD/random/year rules; train-only scaling/cuts/knots; compatible source components reused',
        gap='',scope_note='APP-C-COMPLETE授权仅C补算；历史含零客户恢复结果不作当前排名。',config={'task':'APP-C-COMPLETE','seed':20260908})
    r['question']={'C01':'四组最终样本及精确候选定义','C02':'原12阶梯及Table 3单/双自由结点比较',
        'C03':'同控制阵风比较、地区FE、原天气及D参考结果','C04':'四组合覆盖矩阵及补算完成状态'}[r['requirement_id']]
    r['subsection']={'C01':'C.1','C02':'C.2','C03':'C.3–C.4','C04':'C.1–C.4'}[r['requirement_id']]

SCOPES = {
 'A':'样本/变量、固定设计VIF和既有原因十分位表可整理；正文91%端点的分箱来源仍未定位。',
 'B':'构造证据与当前固定输入描述分开保存；历史清理范围不可替代当前样本。',
 'C':'最终四样本完整阶梯及同控制阵风函数；兼容组件复用、缺项补算，历史固定结点与D不同控制项另表。',
 'D':'只整理既有结点profile/bootstrap/nested结果；不新增稳定性结论。',
 'E':'Table 8是两个时期各自估计；不能称为冻结模型的后续预测。',
 'F':'四组最终双向完整系数已具备；天气LAD-only仍缺。联合地区+日历块不可拆成日历因果作用。',
 'G':'最终RMSE和已有候选诊断可整理；最终残差数值表仍需定位。正文已有预测图不重复复制。',
 'H':'事件条件探索的样本/形式明确列出；不是当前最终回归的完整替代分布稳健性验证。',
 'I':'七场固定窗口描述可生成；当前最终规格风暴预测未定位，不能用旧二次模型补位。',
 'J':'ERA5聚合/持续性与正文proxy时间检验分开。八项时间BSS均为正，但校准和月度偏差保留；无新的通过阈值。',
}

# APP-J03-COMPARE: explicit first-package authorisation; other gaps stay dormant.
J03_PLAN = 'docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令.md'
J03_SOURCES = [MAIN+'final_models/district_day_panel.csv', MAIN+'final_models/district_day_fragility.json',
    AGG+'experiment.json', AGG+'inventory.json', AGG+'daily_aggregations.csv.gz',
    AGG+'fit_checkpoint.jsonl', AGG+'fit_summary.csv', AGG+'oof_predictions.csv.gz', AGG+'validation.json',
    P03+'lad_folds.csv']
for r in REQUIREMENTS:
    if r['requirement_id']=='J03':
        r.update(source_status='COMPLETION',action='j03_complete',sources=J03_SOURCES,
            producer='analysis_new.appendix.j03_compare:generate',gap='',unit='LAD-day',
            sample='111 LAD × 1096 UTC days = 121656 rows; identical eight labels and saved five LAD folds',
            model='shared ddagg01-stable-v1 background-rate lognormal; PROXY versus GRID_MAX',
            metrics='pooled OOF Brier/BSS; delta=PROXY-GRID_MAX; paired conditional 95% interval',
            validation='48 components per source; training-only fits; fixed OOF paired LAD bootstrap B=1000 seed=20260909',
            scope_note='第一步仅J03；产物补齐后待研究负责人反馈分析，不自动科学关闭或进入F/GI/H。',
            config={'task':'APP-J03-COMPARE','repeats':1000,'seed':20260909,'calibration':'pooled two-source prediction quantiles, same edges, no labels'})

# APP-F02-COV: accepted fixed weather final models, covariance completion only.
F02_SOURCES=[E0,R0,'analysis_new/weather_only_regression.py','analysis_new/model_selection.py',
    'analysis_new/final_models.py','analysis_new/appendix/design_adapter.py',
    MAIN+'weather_only/weather_only_summary.json','results/Appendix/C/tables/C_SAMPLE_DEFINITIONS.csv']
for _margin,_model in [('E0','F08'),('R0c','F06')]:
    F02_SOURCES += [MAIN+f'weather_only/{_margin}_weather_final_twoway.csv']
    F02_SOURCES += [f'results/Appendix/C/data/models/{_margin}_weather/{_model}/{f}' for f in ['result.json','preprocessing.json','in_sample.csv.gz','coefficients.csv']]
for r in REQUIREMENTS:
    if r['requirement_id']=='F02':
        r.update(source_status='COMPLETION',action='f02_complete',sources=F02_SOURCES,
            producer='analysis_new.appendix.f02_cov:generate',gap='',
            question='天气最终固定模型LAD-only与LAD/date双向协方差、完整SE及区间对照',
            sample='E0 weather9857；R0c weather9254，正式正客户恢复样本',
            model='fixed final E0 platform11/24; R0c single knot11; both temperature squared; original full controls',
            metrics='same-coefficient SE ratio, t(G_LAD-1) 95% CI and p; full covariance components',
            validation='same X/residuals/keys; compare saved final coef, se, se_lad and p_t_G1; no CV',
            scope_note='APP-F02-COV仅第二包；原final表已有se_lad列，本轮补矩阵、区间与复算来源；待反馈分析。',
            config={'task':'APP-F02-COV','use_correction':True,'reference':'t','df':'G_LAD-1','alpha':.05})
SCOPES['F']='四组最终系数与既有增量R²保留；F02仅补齐两个天气固定最终模型的LAD/date推断对照。'
for r in REQUIREMENTS:
    if r['requirement_id']=='J03':
        r['scope_note']='研究负责人在F02启动时明确确认J03匹配比较缺口关闭，保留正文PROXY；F02本轮不重跑或改写J。'

# APP-GI-PRED, the accepted third package. Never dispatch H from this action.
GI_PLAN='docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令 (2).md'
GI_SOURCES=[E0,R0,GI_PLAN,MAIN+'final_models/final_summary.json',MAIN+'weather_only/weather_only_summary.json',
    MAIN+'model_selection/knots.json','analysis_new/final_models.py','analysis_new/weather_only_regression.py',
    'analysis_new/model_selection.py','analysis_new/plot_model_selection.py',
    'scripts/c02_c08_repair_20260905/figure9_storm_validation.py','scripts/c02_c08_repair_20260905/corrected_sample_builder.py']
for r in REQUIREMENTS:
    if r['requirement_id'] in ['G03','I02']:
        r.update(source_status='COMPLETION',action='gi_complete',sources=GI_SOURCES,review='',gap='',
            producer='analysis_new.appendix.gi_completion:generate',unit='incident',
            sample='accepted E0 all60437/weather9857; positive R0c all51173/weather9254; I all only',
            model='fixed final / exactly identified legacy controls; no model search',
            metrics='pooled log-scale RMSE/MAE/bias; actual fixed gust bins and predicted quantiles; I seven windows and unique union',
            validation='original fixed five LAD folds where row outputs absent; in-sample and OOF explicitly separate',
            scope_note='第三包G/I授权完成；只补当前模型底层数组和七场风暴描述；产物完成后待反馈，H未启动。',
            config={'task':'APP-GI-PRED','seed':20260908,'knots':'fixed original production','status':'pending researcher feedback'})
    if r['requirement_id']=='F02':r['scope_note']='更新台账(2)第10节已由负责人关闭F02；原表已有se_lad，矩阵/区间和推断规则已补齐；本轮不改写F。'
SCOPES['G']='四组正式固定模型逐行预测、三类残差、校准和响应网格；当前与旧图身份分别登记，完成待反馈。'
SCOPES['I']='七场固定窗口的当前全体final描述和G既有OOF切片；正客户超阈点仅展示，完成待反馈。'

# APP-H03-LINK: fourth package only; earlier output trees remain read-only.
H03_PLAN='docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令 (3).md'
H03_SOURCES=[H03_PLAN,MANUSCRIPT,E0,R0,'scripts/appendix_h_20260906/step_b_distribution_check.py',
    'results/pretest/archive/20260909154556/results/appendix_h_20260906/raw/stepB_distribution_check_corrected.json',
    'analysis_new/final_models.py','analysis_new/model_selection.py','analysis_new/weather_only_regression.py',
    'analysis_new/fragility_demo.py','analysis_new/fragility_surfaces.py',
    MAIN+'model_selection/knots.json',MAIN+'weather_only/weather_only_summary.json',
    MAIN+'model_selection/fragility_summary.json',MAIN+'model_selection/fragility_lognormal.json',MAIN+'model_selection/fragility_optimizer_diagnostics.json',
    'results/Appendix/G/data/GI_PREPROCESSING.json','results/Appendix/G/data/GI_COEFFICIENTS.csv','results/Appendix/G/data/GI_PREDICTIONS.csv.gz']
for _m in ['E0','R0c']:
    H03_SOURCES += [MAIN+f'final_models/{_m}_final_twoway.csv',f'results/Appendix/G/data/GI_{_m}_all_final_COV.csv',f'results/Appendix/C/data/samples/{_m}_all.csv.gz']
for r in REQUIREMENTS:
    if r['requirement_id']=='H03':
        r.update(source_status='COMPLETION',action='h03_complete',sources=H03_SOURCES,review='',gap='',
            location='§3.1 P030; §4.4 P069; Appendix H title P100',
            producer='analysis_new.appendix.h03_completion:generate',unit='incident',
            question='当前正式预测变量基上四项替代均值/分布设定的系数及两维聚类区间；既有事件条件证据整理',
            sample='E0_all60437 includes8979 zeros; R0c_all51173 positive customers, accepted cleaning',
            model='fixed final E14/25 plateau and R quadratic: E NB2/Tweedie; R Gamma/Tweedie; explicit Log; Tweedie power1.5 EQL',
            metrics='full coefficients, LAD/date score-Hessian covariance and t(G_LAD-1) intervals; no cross-scale ranking',
            validation='same design/IDs, lawful raw response, solver/score/Hessian diagnostics, saved means and covariance components; no CV',
            scope_note='第四包四个既定全样本拟合；OLS参考及H2/H3只复用/派生。产物完成待负责人反馈，不自动关闭或成文。',
            config={'task':'APP-H03-LINK','reference':'t(G_LAD-1)','Tweedie_power':1.5,'alpha_NB2':'joint MLE','random_operations':False})
    if r['requirement_id'] in ['G03','I02']:
        r['scope_note']='更新台账(3)第12节已确认关闭第三包结果缺口；GI-W01至W09图文待改保留，不重跑或改写G/I。'
        r['config']['status']='researcher closed results gap; writing changes pending'
SCOPES['G']='第三包结果缺口由负责人关闭；保存四组固定模型底层证据，GI-W图文待改保留。'
SCOPES['I']='第三包七风暴描述结果缺口由负责人关闭；GI-W图文待改保留。'
SCOPES['H']='第四包当前全体样本四项固定规格替代GLM及既有条件概率证据；有效性/例外逐项报告，待反馈。'
