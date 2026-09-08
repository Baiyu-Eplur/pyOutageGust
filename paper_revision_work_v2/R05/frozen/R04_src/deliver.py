"""R04 evidence collation and delivery only. No model fitting or manuscript editing."""
from common import *
import copy,datetime,shutil,zipfile,re

M=W/'manuscript_record'
def write(p,s):
    p=Path(p);assert p.resolve().is_relative_to(W);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def put(p,x):write(p,json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False))
def csv(name):return pd.read_csv(Q/'tables'/name)
def entry(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def run():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    acc=read(Q/'checks/core_actual_acceptance.json');cal=read(Q/'checks/calendar_equivalence.json');assert acc['passed'] and cal['passed']
    metrics=csv('H0_R1_B1_metrics.csv');shapes=csv('H0_R1_B1_shape.csv');incs=csv('H0_R1_B1_increments.csv');period=csv('period_comparison.csv');storms=csv('storm_statistics.csv');sup=csv('supplement_summary.csv');fd=read(Q/'checks/final_data.json')
    figs=read(Q/'figures/FIGURE_MANIFEST.json');assert all(x['visual_review']=='passed' for x in figs),'Finish actual visual review first'
    formal=read(RUN/'RUN_MANIFEST.json');assert formal['formal_B1'] is True
    # Compare actual turn-start protected paths, not the historical R00 baseline.
    protected=read(Q/'checks/protected_at_start.json');changed=[{'path':p,'before':h,'after':sha(p)} for p,h in protected.items() if sha(p)!=h]
    old=read(Q/'archive/ARTIFACT_MANIFEST.json');frozen=[x for x in old['files'] if str(CORE) in x['path'] or str(W/'R02') in x['path'] or str(W/'code/snapshots') in x['path']]
    bad=[x['path'] for x in frozen if sha(x['path'])!=x['sha256']]
    origpairs=[]
    for x in read(CORE/'frozen/PROJECT_SOURCE_MANIFEST.json'):
        assert sha(x['frozen_path'])==x['sha256'];origpairs.append({'path':x['original_path'],'matches_frozen':sha(x['original_path'])==x['sha256']})
    large=read(W/'inventory/large_input_identity.json');largechecks=[]
    for x in large:
        p=Path(x['path']);largechecks.append({'key':x['key'],'path':str(p),'sha256':sha(p),'matches':sha(p)==x['sha256']})
    assert not changed and not bad and all(x['matches_frozen'] for x in origpairs) and all(x['matches'] for x in largechecks)
    iso={'timestamp_utc':now,'passed':True,'scope':'actual R04 start to current; named paths only','protected_paths':len(protected),'changed_since_R04_start':changed,'prior_R02_R03_snapshot_files_verified':len(frozen),'unexpected_prior_changes':bad,'original_source_pairs':origpairs,'large_inputs':largechecks,'R02_event_sha256':sha(W/'R02/data/R02_event_master.parquet'),'Word_unchanged':True,'LOG_note':'R04 start hash cd09ad5aea2fa42405da9e7d5b634590143d7d39e79f1eeb0730adc6af57857e unchanged. Earlier R03 documented +3916 bytes; additional log changes before R04 start are not attributed to this run. Unknown writer remains unresolved; no original log rollback or adoption as B1 evidence.'}
    put(Q/'checks/final_isolation.json',iso)
    # Finite-sample and new calendar basis evidence.
    calrows=[]
    for x in cal['checks']:
        calrows.append({'group':x['group'],'target':x['target'],'period':x['period'],'n':x['n'],'old_rank/k':f"{x['old_rank']}/{len(x['original_columns'])}",'new_rank/k':f"{x['new_rank']}/{len(x['retained_columns'])}",'removed':','.join(c for c in x['original_columns'] if c not in x['retained_columns']) or 'none','space_maxerr':x['max_space_residual'],'eta_maxerr':x['max_eta_difference']})
    calendar_doc='# R04 图10等价日历基修复：实际验收\n\n8个独立分期档案均已生成并再读校验。主/天气各E0、R0c和earlier/later均检查；核心冻结运行曾跳过后期的事实保留，图10改消费独立 periods_v2 档案。未改R03源代码或核心档案。\n\n'+markdown(pd.DataFrame(calrows))+'''
预测期为UTC [2021-04-01,2024-04-01)，later自2023-09-30。后期实际满足 I(year=2024)=I(month∈{1,2,3})，残差为0。在截距及January参考编码下，冗余涉及截距、年份及其余月份；不是阵风与客户项的删选。

固定顺序保留全部实质列和截距，按原日历列顺序逐列加入能增加秩者。秩选择时列以其欧氏范数归一化，绝对阈值1e-10；原始设计和系数未重缩放。四个后期均仅移除month_12。样本列空间双向最小二乘映射及残差、原/新条件数见 checks/calendar_equivalence.json；容许误差1e-7，实际拟合值差异最大约1.42e-14。

用原设计零空间检查所有科学协变量的参数唯一性，包括阵风一次/二次/气压交互、客户项、其他天气及区域项。原截距可与冗余日历共享零空间方向，因此不把原截距或全部原日历系数说成唯一。新基保留截距。旧广义逆仅用于均值投影核对，其日历系数不作单独解释或跨编码比较。

每个档案保存训练ID、设计列、预处理、实际year×month支持。已见组合上的再读预测逐值一致；未支持组合直接报错（2099测试已拒绝）。等价性仅在这些组合及可表达的实质变量行上成立，不扩展到缺失年月组合。

各期采用自己的ddof=1训练尺度。报告物理阵风二次项q=β2/sG²，二阶导数为2q，两者不可混称。气压参考为同一group/target全时期模型的物理均值：主组1012.074826 hPa，天气组1004.983606 hPa；再在各期自己的压力尺度上转换。该共同参考仅用于同一组内分期比较。天气E0早期的代数顶点不在p1–p99支持内，最低点返回未提供，不画作有效最低点。

CR1按有效满秩k计算 G/(G−1)·(n−1)/(n−k)，分别记录LAD、date和交集，并形成双向矩阵。实际样本与复制的statsmodels协方差实现核对。全部分期矩阵的非有限/负对角状态另见 period_covariance_acceptance.json；没有使用旧冗余列数修正因子，也没有拼接重叠CV拟合的逆方差区间。图10仅为全分期拟合的物理尺度点比较；不证明时间稳定性，不新增最低点CI。

原失败的开发期部分档案保留在 periods/；最终可消费版本为 periods_v2/，配置为 configs/period_equivalent_v1.json（run_id沿用其声明的R04_period_equivalent_v1，路径及最终生产者SHA另行绑定）。失败日志保留，不把初次截距零空间断言误写成科学变量不可识别。
'''+markdown(period.drop(columns=['period_archive','source']))
    write(Q/'CALENDAR_BASIS_REPAIR.md',calendar_doc)
    comparison='''# H0 / R1 / B1实际对照

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

'''+markdown(metrics[['version','group','target','block','n','pooled_R2','mean_fold_R2']])+'''\n## 条件增量\n\n表中单位为R²；乘100为百分点。G|K=GK−K，K|G=GK−G；另列从control加入的增量。跨主/天气总体只作点描述。\n\n'''+markdown(incs)+'''\n## 形状和物理尺度\n\n最低点条件于各档案自己的平均物理气压和支持；H0仅保留历史代数顶点，未重新认证。physical_quadratic为β2/sG²，二阶导数是其两倍。无当前最低点CI。\n\n'''+markdown(shapes[['version','group','target','n','beta_gust','beta_gust2','beta_interaction','gust_mean','gust_sd','physical_quadratic','conditional_minimum_ms','minimum_status']])+'''\n## 共同事件的预测变化（与总体评分分表）\n\n共同ID上分别按各版本目标评分；max target差异明确列出。训练成员与日期fold仍可能不同，预测差异不是纯输入的因果分解。\n\n'''+markdown(csv('common_event_prediction_comparison.csv'))+'''\n## 风暴与参考\n\nH0历史风暴8.15%/14.72%不能直接继承；当前候选/实际模型/全主表详见storm_statistics.csv。当前曲线exp(meanη)、地图exp(日历加权meanη)、图7指数网格max/min，均使用新档案。H0旧地图/曲线只作历史，不混填新图或置信区间。主B1图9唯一4452事件全部在全拟合训练内；单独OOF版本每事件由未见该日期的模型预测，仍不是留出整个风暴的验证。
'''
    write(W/'tables/H0_R1_B1_COMPARISON.md',comparison)
    # Every retained artifact, including changes of responsibility, is explicitly located.
    coverage=[
      ('正文表1 / D-T01','四列原/对数描述','R04/src/report_data.py','R02主组60436','R04/tables/Table1_current.csv','本轮重算；恢复尾部不同旧H0'),
      ('正文表2 / D-T02；附录A-T01/02','变量/原因代码/区域定义','R01/R03冻结契约和代码副本','现有来源','R03/CONTRACTS.md；contracts/DATA_CONTRACT.md','定义可复用；来源/边界限制未解决，非新数值结果'),
      ('正文表3 / 附录F A-T08/09','四组全系数、三种CR1','R03/cli.py formal；R04/src/audit_results.py','R04_primary.json；R02输入','R04/tables/Tables3_F_complete_coefficients.csv','本轮重算；p为正态Wald描述，不是稳健性证明'),
      ('正文表4 / D-T04','嵌套OOF/条件增量','R03/cli.py formal','共同日期fold；all_valid','R04/tables/core_metrics.csv；H0_R1_B1_increments.csv','本轮重算；单个条件点替代含混区间'),
      ('图1','主模型事件位置密度','R04/src/figures.py','主组60436坐标','R04/figures/figure01.png/.pdf','实际导出；新密度面板不含旧三许可区边界/GB inset；后续图注需改，原边界装饰仍未补'),
      ('图2','原尺度+log目标分布','R04/src/final_data.py','主组60436','R04/figures/figure02.png/.pdf','四面板实际导出；原尺度计数用log纵轴，尾部不裁'),
      ('图3','真实开发历史/风暴窗口','R04/src/final_data.py','冻结UTC和storm_windows','R04/figures/figure03.png/.pdf','实际导出；earlier/later，保留历史非独立性'),
      ('图4','四模型阵风参考曲线','冻结figure4数据→R04/src/figures.py','各自估计人口+均值物理气压','R04/figures/figure04.png/.pdf','实际导出；exp(meanη)，无smearing/旧CI'),
      ('图5/8','E0/R0c嵌套模型及条件增量','正式metrics/contributions→product_complete.py','各固定评估总体','R04/figures/figure05/08.png/.pdf','实际导出；图5主组两目标pooled R²，图8两目标贡献百分点'),
      ('图6','区域参考地图','正式figure6数据→figures.py','复制LAD21几何；共同日历；客户z=z²=0','R04/figures/figure06.png/.pdf','实际导出；Buck代理保留；不作因果区域差异'),
      ('图7','参考网格指数max/min比','正式figure7数据→figures.py','50点p1–p99各自网格','R04/figures/figure07.png/.pdf','实际导出；非算术均值、非端点比'),
      ('图9','训练内/OOF风暴预测','正式figure9数据→figures.py','UNIQUE_ANY主组4452/目标','R04/figures/figure09.png/.pdf','实际导出并核ID；E侧η；不等于真正过程留出'),
      ('图10 / 附录H A-T13','物理尺度分期比较','R04/src/calendar_repair.py','period_equivalent_v1；8个分期','R04/periods_v2；figures/figure10.png/.pdf','等价性通过；仅点估计；天气早期E最低点无有效支持'),
      ('VIF / D-P041','完整冻结设计VIF','R03/src/diagnostics.py','四组完整日历设计','R04/R04_B1_all_valid_v1/*/VIF.csv','本轮重算；不得保留旧最高3.76或<4未经替换'),
      ('阶段 / A-T04/05、附录D','阶段描述及raw ln(stage)控制','核心step27；final_data.py','当前全期all_valid，另列分期分布','R04/tables/AppendixD_period_stage_counts.csv；核心step27_*','描述/全期控制已重算；旧earlier截尾控制没有冒充新结果，须明确改表责任或待后续原总体重跑'),
      ('附录图D1','分层和pooled共同分箱','R04/src/artifact_acceptance.py','主/天气各总体自身公共数值分箱','R04/figures/figureD1.png/.pdf','4面板实际导出；修复CSV字符串排序；缺首阶段排除敏感性延至V'),
      ('六原因组 / A-T03、D-P038','完整系数及5折对照','R04/src/supplements.py','R02共识六组117108，all_valid','R04/supplements_v1/six_group_*.json；six_groups_OOF.csv','6次实际拟合；改为当前主方案对应物，非旧116064截尾原样复现'),
      ('GLM / D-P048、A-P094','NB2/Tweedie E，Gamma/Tweedie R','R04/src/supplements.py','冻结旧分布规格；当前60436','R04/supplements_v1；tables/supplement_summary.csv','4次实际拟合收敛；NB数值警告保留'),
      ('三阶 / MR18','预声明zG³与二次配对OOF','R04/src/supplements.py','同成员同共同fold；两目标','R04/supplements_v1/cubic_*；tables/supplement_summary.csv','12次实际拟合；保留反向线索，未做模型搜索'),
      ('残差诊断 / D-P048、附录F/H','log-OLS残差/Q-Q/分布','R04/src/final_data.py','全拟合再读预测','R04/figures/figureF1.png/.pdf；tables/residual_diagnostics.csv','实际生成；exp残差均值仅诊断，不作回变换校准'),
      ('附录G A-T10 / A-P073','阵风十分位原因比例和低阵风支持','report_data.py/final_data.py/numeric_acceptance.py','主组60436十分位；另列六组117108；main/weather低阵风支持','R04/tables/AppendixG_*.csv','本轮重算；两种十分位分母分别标记，旧负增量解释需撤回重审'),
      ('附录H A-T11','条件物理最低点','冻结minimum_interface','主E0压力−1/0/+1SD','R04/tables/AppendixH_pressure_minima.json','确定性重算；不新增拟合或CI'),
      ('附录E A-T06/07、H A-T12','历史开发样本/最低点/Bootstrap','冻结历史来源','H0历史证据','manuscript_record/evidence；R04/frozen/H0','可证明历史身份；不当B1，不跑500bootstrap，不继承旧CI'),
      ('附录B历史500事件/时长比较','历史验证及数据规则','R00–R03已冻结证据','原抽样/输入规则','contracts/；R02/checks/；manuscript_record/evidence','按历史证据复用；不冒充本轮独立重跑'),
      ('风暴数字 D-P006/102','三类总体/窗口/唯一/重叠','audit_results.py/final_data.py','UTC冻结窗口','R04/tables/storm_statistics.csv；storm_LAD_details.csv','本轮重算；27累计窗口日vs25唯一日'),
      ('最低点CI/稳健U/过程验证/工程校准','科学主张验证','尚未运行V','需后续指令','R04_WRITING_IMPACT.md','延至V；无结果，不能填0或H0'),
    ]
    covdf=pd.DataFrame(coverage,columns=['论文位置/产物','保留职责','生产者','配置/输入','当前输出','状态/边界']);table(Q/'tables/RETAINED_ANALYSIS_COVERAGE.csv',covdf)
    write(W/'tables/RETAINED_ANALYSIS_COVERAGE.md','# R04保留分析与产物覆盖\n\n所有下列当前结果依赖R02冻结SHA及B1档案；具体配置/代码/文件SHA见baseline/B1_MANIFEST.json。完成R04不表示已获R05项目复审通过。未重算的历史内容不代表获准删除。\n\n'+markdown(covdf)+'\n图1仅密度面板，旧许可区边界与全国inset尚未恢复；图件职责变化必须在后续写作中明确。附录D旧earlier+p99控制表与本轮全期all_valid控制不作一对一数值替换。现有新数字已列，逐个旧文本数字尚有未映射槽位，禁止自动回填。\n')
    # Numeric report: useful new values, not just an inventory of unbound text tokens.
    lead=[]
    def nrow(loc,old,new,unit,t,n,artifact,mr,cl):lead.append({'旧定位':loc,'旧值/说法':old,'当前值':new,'单位':unit,'目标/人群':t,'n':n,'当前来源':artifact,'MR':mr,'CL':cl})
    nrow('D-P002/039','60453/60437/59834','60436 E0；60436 R0c','events','main',60436,'core_actual_acceptance.json','MR01/09/10','CL01')
    nrow('D-P017','9.87 / 5.22','9.910222388 / 5.279979383','m/s mean/SD','main E0',60436,'main_E0/full_model.json','MR05/11','CL01/02')
    nrow('D-P030；A-P018','47.13→93.02；1.97','47.128334106→93.025729698；1.973881137','customers / ratio','lowest stage number',60436,'customer_aggregation_comparison.json','MR04','CL01')
    nrow('同上定义核查','earliest stage文字混用','31.121963730→93.025729698；2.989070050','customers / ratio','earliest record time',60436,'customer_aggregation_comparison.json','MR04','CL01')
    nrow('D-P071/073；摘要','10.69/10.7','10.807545499','m/s','main E0; mean physical pressure',60436,'conditional_minimum_no_CI.json','MR18/19','CL02')
    nrow('D-T04 weather E0','−0.15','+0.382246343','R²百分点','weather E0',9857,'contributions.json','MR12/13/18','CL03')
    nrow('D-T04 main R0c','gust0.62–0.75；customers7.73–7.87','G|K1.142120140；K|G6.141466554','R²百分点','main R0c',60436,'contributions.json','MR12/13','CL03')
    nrow('D-T04 weather R0c','gust1.43–1.71；customers1.00–1.28','G|K3.579703969；K|G1.507182044','R²百分点','weather R0c',9857,'contributions.json','MR12/13','CL03')
    nrow('D-P102','27日；8.15%；14.72%','25唯一日；7.366470316%；13.257885884%','days / events% / customers%','main unique storm',60436,'storm_statistics.csv','MR14/16','CL04')
    nrow('D-P006','1601；101LAD；376712；52.7h','见storm_LAD_details按main/weather分别取数，旧句混用群体须重写','events/LAD/customers/h','Eunice',None,'storm_LAD_details.csv','MR05/16','CL01/04')
    nrow('MR18三阶旧反证','E0 ΔR²≈0.001441','E0 +0.001931639；R0c +0.000498187','R²','main paired OOF',60436,'supplement_summary.csv','MR18','CL02')
    nrow('A-T12；A-P086','500次旧bootstrap；9.2–12.1','未运行；无合格B1最低点CI','not available','B1 minima',None,'instruction scope','MR19/20','CL02')
    head=pd.DataFrame(lead);table(Q/'tables/NUMERIC_HEADLINE_BINDINGS.csv',head)
    vif=[]
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        v=pd.read_csv(RUN/f'{g}_{t}/VIF.csv');continuous=v[~v.term.str.startswith(('year_','month_'))];top=continuous.loc[continuous.VIF.idxmax()];vif.append({'group':g,'target':t,'continuous_max_VIF':top.VIF,'term':top.term,'all_columns_max_VIF':v.VIF.max()})
    table(Q/'tables/VIF_summary.csv',pd.DataFrame(vif))
    numeric='# R04数值总账\n\n本总账绑定当前R02数据、冻结R04_primary配置与各实际生产者；基线清单给完整SHA。Word位置来自已冻结D/A索引，不改Word。空值表示未提供/未定义/未运行，绝非0。\n\n'+markdown(head)+'\n## 当前核心完整数字\n\n'+markdown(csv('core_metrics.csv'))+'\n## 物理参考、最低点与支持\n\n'+markdown(shapes[shapes.version.eq('B1')])+'\n## 风暴总体与分母\n\n'+markdown(storms[storms.window.eq('UNIQUE_ANY')])+'\n## Eunice及所有窗口群体核对\n\n'+markdown(csv('storm_LAD_details.csv'))+'\n## 当前VIF（与旧设计不可机械同口径）\n\n'+markdown(pd.DataFrame(vif))+'\n## 补充模型\n\n'+markdown(sup)+'\n## 逐槽位与逐表细账\n\n'+f'ALL_MANUSCRIPT_NUMERIC_SLOTS.csv索引了{fd["numeric_slots"]}个文字/表格数字槽位，不包含图片OCR和全部公式对象。CURRENT_NUMERIC_BINDINGS.csv提供{fd["cell_bindings"]}个表格单元格绑定，CURRENT_PARAGRAPH_NUMERIC_BINDINGS.csv另有{fd["paragraph_bindings"]}个段落绑定，图注数值也已补记。全部槽位已登记去向，但{fd["requires_sentence_rewrite_slots"]}个槽位需要整句/组合统计重写、以具名当前数据集替换，不能自动逐数回填；历史实验、引用、公式编号也单列。分类完成不等于所有旧数字均已一对一替换。原Word不动。\n\n'+'''- 表1：Table1_current.csv（28个值）；表3/F：Tables3_F_complete_coefficients.csv，含全日历列和三种CR1，p_normal_CR1_descriptive为正态Wald描述；极小p如浮点下溢须读p_log10_normal_CR1及p_status，不写成真实p=0。
- 表4：H0_R1_B1_increments.csv；六组完整系数/各折：supplements_v1/six_group_*.json；当前配对OOF见six_groups_OOF.csv。AppendixC_fold_summary.csv和AppendixC_fold_coefficients.csv提供新5折摘要；重叠训练fold显著次数不作独立重复证据。
- 附录D：AppendixD_period_stage_counts.csv、核心step27_stage_coefficients.csv、stage_composition.csv/stage_pooled.csv。旧earlier+p99与当前全期all_valid必须改标签而非按格覆盖。
- 附录G：AppendixG_main_gust_deciles.csv是主组60436的十分位，weather share从6.933842%到57.071381%；AppendixG_gust_deciles.csv另为六组117108的十分位，不能混分母。AppendixG_low_gust_support.csv分列main/weather支持；并列按qcut实际合并，CSV保留边界。
- 附录H：AppendixH_pressure_minima.json、AppendixH_period_scales.csv、period_comparison.csv；旧Bootstrap仅历史，当前无区间。
- 客户比较：customer_aggregation_comparison.json；残差及global exp(residual)仅诊断：residual_diagnostics.csv，不用于曲线校准。

尚未认证的文献引用数字、官方天气产品语义、许可区几何与未决科学机制不因有当前模型而变为已核实。每一未映射槽位都保留旧定位/值/上下文、MR/CL和状态，可在R05及后续W逐项核对；本轮不宣称全论文已可自动落稿。
'''
    write(W/'tables/NUMERIC_LEDGER.md',numeric)
    # R04 technical report and six requested answers.
    full=metrics[(metrics.version=='B1')&(((metrics.target=='E0')&(metrics.block=='G'))|((metrics.target=='R0c')&(metrics.block=='GK')))]
    report='''# R04执行报告：冻结主基线及实际产物验收

R04核心正式拟合、嵌套OOF、R1兼容诊断、等价日历分期和可恢复补充分支已运行。当前正式基线为R04_B1_all_valid_v1。R05/V/W均未执行；Word未修改。新结果并不构成最低点稳健性、完整风暴验证或工程校准结论。部分旧稿数字的逐数语义映射、旧图1装饰面板和旧分期截尾附录的等口径替换仍列明未完成，不能宣布所有旧产物一对一复现。

## 1. 四组实际n及正式OOF

'''+markdown(full[['group','target','n','pooled_R2','mean_fold_R2','SSE','SST']])+'''
主组两目标各60,436、111 LAD、1,096日期；天气组各9,857、105 LAD、1,001日期。实际n等于冻结候选，没有静默剔除。设计秩26/26与28/28。每个固定总体/目标的全部嵌套模型使用相同ID/fold及等事件权重；60个OOF模型已再读并验证预测、未见测试日期、完整测试尾部和评分分母，无失败折和缺预测。pooled与mean-fold分开，不能混用。

核心70次生产拟合=4全拟合+60嵌套OOF+4阶段控制+2原实现开发期。R1=64次；独立等价分期=8次；补充分支=22次（4 GLM、12三阶、6六原因组）。合计164次当前生产拟合；另有初次日历实现的一份已生成后废弃开发期档案保留，共165份生产拟合档案尝试结果。协方差比较额外调用32次statsmodels验证拟合（包括失败检查前已执行者），不计作独立科学实验。原设计投影/秩检查另用线性代数；不将之前smoke或H0的80次计入本轮。

R0c主组control/G/K/GK pooled R²为0.021492205/0.030601167/0.080594631/0.092015832；天气为0.192199724/0.222498892/0.201773673/0.237570713。主组G|K与K|G为1.142120140、6.141466554个百分点；天气为3.579703969、1.507182044个百分点。当前点排序仍不同，但没有排序稳定性或跨总体可比性证明。完整12块、SSE/SST及各折评分留在档案和数值总账。

## 2. 与H0相比的研究故事变化

主E0条件最低点从历史10.693754983变为10.807545499 m/s，参考压力1012.074826 hPa，p1–p99支持[2.200000048,27.5] m/s。当前四模型二次项都为正，但天气E0早期子样本的最低点不在支持内。当前R0c主/天气最低点分别10.131987833/5.952984267 m/s，均只是在各自平均压力下的拟合描述。

天气E0加入G的OOF增量从H0 −0.147848762个百分点变为B1 +0.382246343个百分点。旧“天气子样本负增量及其支持解释”不能原样保留。三阶在相同成员/fold上的E0 OOF R²为0.031553095，对二次增加0.001931639；R0c增加0.000498187。该反向线索须进入形状主张审阅，不能用GLM正二次项掩盖。

R1已真实执行，四组n为60,436/59,832/9,857/9,758（主E/主R/天气E/天气R）。R1历史p99分支保留独立折算法，四组H0折映射算法均成功再现；B1用共同UTC日期映射与完整尾部。H0→R1→B1仍含更新诱发的成员/阈值/折变动，不是纯时间修复的因果拆分。不同总体评分与共同事件预测差异已分表。备选共同训练p99未运行。

## 3. 图10和协方差

8个分期的等价基修复通过。只移除4个后期设计里的month_12，保护截距和全部科学项，主后期18/19→18/18、20/21→20/20；天气后期17/18→17/17、19/20→19/19。最大新旧η差异约1.42e-14。实质系数可识别；原截距/日历单独效应不全部唯一，未支持年月预测被拒绝。

四组核心LAD/date/双向CR1均实际检查，双向无负对角且最小特征值为正。每个群体记录有效k、LAD/date/交集数量及CR1有限样本因子；实际矩阵与复制的statsmodels实现一致。分期协方差另保存异常状态。物理尺度q=β2/sG²按各期训练尺度转换，2q才是二阶导数。不绘旧CI或重叠CV逆方差名义区间。

## 4. 图表、六原因组、GLM和附录

图1–10、附录D1及残差F1共12组PNG/PDF已实际导出并视觉检查。图2补齐原/对数尺度四面板；图3保留earlier/later和7窗口；图9分训练内与日期OOF，E侧η；D1同时给各层和pooled。图1当前仅密度图，三许可区线和GB inset未复原，不得沿用原图注。完整列表及职责变更见RETAINED_ANALYSIS_COVERAGE。

六原因组恢复原科学变量定义，在当前共识all_valid总体117,108上6次拟合完成，OOF R²=0.039923105，完整系数/各折协方差已归档。它是当前主协议的对应分析，不能装作旧116,064 p99样本原样重算。旧附录D开发期截尾控制表也不与当前全期控制逐格置换；当前阶段全期控制、分期分布、公共分箱描述均已有数据/图。

4个GLM均收敛，参数与协方差有限，正二次项保留为分布规格敏感性。NB2有4条运行警告，去重为log除零/乘法无效两类；最终收敛/有限矩阵已检查并记录，不能把警告删除。没有新增模型搜索。

## 5. 风暴、客户定义和工程边界

7窗口累计27日，UTC日期联合只有25日（占研究1096日的2.281022%）。全事件主表唯一7,300/135,025，客户1,090,242/10,196,761；主模型唯一4,452/60,436=7.366470%，客户745,372/5,622,103=13.257886%；天气模型唯一2,750/9,857=27.898955%，客户622,601/1,892,162=32.904212%。重叠事件全主表702、主模型479、天气356；逐窗口人数相加分别8,002/4,931/3,106。不能混分母或重复计数。

Eunice分群数据、LAD数及Franklin等窗口详见storm_LAD_details.csv。图9主组4452唯一事件在全拟合版全部是训练成员；OOF版全部由不含其日期的训练模型预测。这仍是日分组诊断，不能升级为未接触的完整风暴验证。

客户聚合均值93.025729698、按最小阶段编号取单阶段均值47.128334106，比例1.973881137；若按最早记录时刻取单阶段则31.121963730，比例2.989070050。原代码step38确实按阶段编号排序，原文“earliest”需要消歧。这些结果仍不是故障初期可知客户量的证明。

天气39.4数值保留为缓存匹配变量最大值，不能称已经证实的现场峰值/3秒阵风。113个LAD21码可连LAD23人口键不是边界等价证明。Buck旧4区简单均值代理仍明确保留；按LSOA重建并对照是已有作者决定，尚未执行，不能改成未选择的可选项。

## 6. 版本、失败、保护与R05前遗留

先将RV03 29项审阅增量合入本地MR-v1.2-R03，保留来源/历史/PD，再进行实际运行。当前完整台账MR-v1.3-R04，29项MR、6条CL、PD历史及逐章写作影响齐备；Word状态均未落稿。报告副本与审阅源按SHA分配来源ID，不覆盖原SRC。

冻结R03代码身份859a02e917d71b4b51333b4db452403a97f1e6c479b6faf654d79f988c553846保持不变。主配置文件SHA为6a4857760612617b21cc9fe3f0c5b237aaa8c3a198ebe80ff2eec417a125ed43；其规范JSON config_hash为4acf04e7a41e920560b4816351b5c893f16ad4d1c1d8f48cdcecef2a3db94231，二者不同。核心manifest purpose保留冻结字面B1_formal_pending_R04，但formal_B1=true且实际档案/日志完整，不改写其历史配置文字。

首次审计因CSV默认浮点解析不能严格往返而失败，改用round_trip读法后逐值通过，没有修改核心CSV。日历初次入口缺模块路径、随后截距零空间断言过宽均已记录并修复；仅排除“原截距必须唯一”的不成立要求，保留科学参数唯一性检查。初稿图2/3/D1与图8/10布局版本均归档。2D绘图成功；未复制可选3D模块导致Axes3D警告，不将该警告的可能原因当作已证实多版本冲突。

本轮开始/结束549个受保护原路径逐字节一致；R03/R02冻结文件、原代码对照和大型输入SHA检查通过。原LOG在R03前轮已有未知写入者追加，本轮起始SHA到结束未变，不回滚或把它的未绑定拟合作为R04证据。不声称整个磁盘没有外部变化。新增计算源代码及依赖均位于独立工作区，复用R03已复制运行库，只补复制绘图库/兼容fold依赖。未改Word或原研究源代码。

R05后续应审查：旧数字逐数语义映射尚未全部完成；图1许可区/inset是否保留及其来源；旧附录D开发期截尾表的保留职责；all_valid六组对照的解释范围；天气E0增量转正及三阶改进对旧故事的影响；最低点CI/形状支持/贡献排序/完整风暴依赖与工程校准的V计划。R05本轮未开始；不能据本报告直接进入V或W。
'''
    report+='\n### 实际保护检查摘要\n\n'+markdown(pd.DataFrame([{'protected_original_paths':len(protected),'unchanged':len(protected)-len(changed),'frozen_prior_files':len(frozen),'original_code_pairs':len(origpairs),'Word_modified':False}]))
    report+='\n### 产物验收补充发现\n\n附录D pooled主组数值分箱均值依次21.451355、17.639357、15.846195、11.708115小时，当前全有效样本不再显示旧稿11.65→14.19→9.87的先升后降。天气分箱均值依次28.038088、19.182336、12.839331、12.198638小时。CSV分箱标签曾按字符串排序，最终独立消费者按冻结数值边界排序并核计数/均值，失败显示版本归档；核心统计与拟合未改。恢复总体均值由旧截尾11.84h变为17.460139h，最大5547.05h，长尾对这些描述有实质影响。\n\n六组新5折zG均值0.018920305、3/5正态Wald显著；主组−0.005545842、1/5显著。zG²均值分别0.078061049/0.083502201，两组5/5正且5/5名义显著；这些重叠训练折不是独立实验。主组十分位weather share从6.933842%到57.071381%，另行保存六组十分位，绝不混分母。950数字位置全部登记去向，182个表格单元格、64个段落值及若干图注有直接当前绑定；65个旧组合数字位置需依据对应当前数据集整句重写，不是未生成结果，也不表示已修改Word。\n\n拟合次数补充口径：当前可消费生产拟合164；另1份已归档但废弃开发期拟合，以及同次失败时已求得参数、但未通过截距断言且未落档的后期拟合1次。因此按生产系数求解尝试为166次，其中165份有档案，164份当前有效。32次协方差验证拟合与VIF辅助回归/旧设计投影不计入独立生产模型次数。\n'
    write(W/'reports/R04_report.md',report)
    # Preserve full pre-update ledger, then append evidence-backed increments to every original MR.
    doc=read(M/'REVISION_ITEMS.json');assert doc['version']=='MR-v1.2-R03+RV03','Do not overwrite a later ledger'
    before=M/'stage_snapshots/R04_review_merged_before_results';before.mkdir(parents=True,exist_ok=False)
    for name in ['REVISION_ITEMS.json','MANUSCRIPT_LEDGER.md','SOURCE_MANIFEST.json','CHANGELOG.md','RV03_SOURCE_MAP.json']:shutil.copyfile(M/name,before/name)
    notes={
    'MR01':('R02冻结主表已由四组完整拟合/正式OOF消费；实际主60436、天气9857。','更新数据方法与新n；最早记录代理不升级为真实onset。','R05检查；真实onset未决'),
    'MR02':('全链采用冻结UTC；1096共同日期；唯一风暴25日，主4452事件。','保持UTC及2023-09-30分界；不将候选不变当日期fold不变。','业务日历敏感性及依赖验证待V'),
    'MR03':('主表135025唯一ID，正式模型不重新并ID；冲突资格按冻结规则。','更新当前候选/拟合状态；两ID业务身份仍未确认。','原始业务身份资料'),
    'MR04':('最小阶段编号47.128334→聚合93.025730，比例1.973881；最早时刻31.121964，比例2.989070。','D-P030/A-P018必须消歧first/earliest；分清C聚合与D跨度。','R05核对比较规则；不声称故障初期客户信息'),
    'MR05':('更新天气已正式消费；主gust均值9.910222/SD5.279979；Eunice逐总体数字已输出。','撤去未经证明的observed peak/ERA5/3-second同一性；引用缓存代理及未决语义。','天气产品响应metadata仍需来源'),
    'MR06':('区域gap列按冻结代理进入B1；完整系数已重算。','坚持LAD内LSOA极差定义，不还原全国差值旧定义。','区域来源兼容与Buck后续重建'),
    'MR07':('Moran作为现有地方指标进入新拟合；权重细节没有新来源。','保留计算层级/空间权重未决，地图不能当机制。','原始权重/LSOA重建证据'),
    'MR08':('Buck旧四区简单均值代理继续用于新模型/地图，未重建。','保留代理标签及作者已决定的LSOA重建并对照；不得降为可选。','按原始LSOA重建并与代理对照'),
    'MR09':('B1共识主60436、天气9857；六组all_valid117108，OOF0.039923105。','写明共识资格和分析组来源限制；六组全有效对应物不同旧截尾样本。','官方cause文档/六组对照范围R05审阅'),
    'MR10':('四模型all_valid正式n60436/60436/9857/9857；测试长尾全部保留；R1单独历史p99。','所有旧n/恢复分布/p99段落需更新；不按R²恢复旧截尾。','R05验收；共同训练p99待V00/V01'),
    'MR11':('四组全设计满秩，VIF/三种CR1已生成；8个分期等价基通过。','用实际训练ddof=1、物理尺度、有效k；VIF旧<4/3.76不可直接继承。','完整设计解释与分期支持R05复审'),
    'MR12':('12嵌套块pooled/mean-fold、SSE/SST/n和每折结果完整；无缺预测。','正文方法/表4写pooled主指标并分列mean-fold；不能混评分总体。','R05评分对账'),
    'MR13':('主G|K1.142120pp<K|G6.141467pp；天气3.579704pp>1.507182pp。天气E0 G增量转为+0.382246pp。','保留条件点排序但撤回负E增量故事；摘要/RQ/结果/结论同步审阅，不能宣称稳定反转。','配对贡献与跨组稳健性待V'),
    'MR14':('日期OOF无同日泄漏，风暴有跨日及窗口重叠；未留出完整过程。','保持retrospective/date-group诊断标签，不称独立风暴验证。','完整过程依赖/分组方案待V'),
    'MR15':('图9 E侧y=ln(1+C)、预测η再读一致，没有二次log1p。','替换旧图9并准确标轴；描述与OOF分面。','工程误差/校准仍待V'),
    'MR16':('主风暴UNIQUE_ANY4452，479重叠事件只计一次；全拟合全部训练内，OOF全部本折未见。','改27为25唯一日；主7.366470%事件/13.257886%客户；不得拿7300除60436。','过程验证待V'),
    'MR17':('图4为exp(meanη)，图6exp日历加权meanη；客户中心z=z²=0，图7指数网格max/min。','更换图与数学定义；非算术均值、不补旧smearing/CI。','工程参考/校准待V；图6区域限制保留'),
    'MR18':('4GLM正二次项；三阶E0配对OOF增0.001931639，R0c增0.000498187。','正曲率证据和三阶反向证据并列，不能只报支持U形的模型；旧天气E负增量不再成立。','V01形状/模型比较协议'),
    'MR19':('主E最低点10.807545 m/s，主R10.131988，天气E3.800081/R5.952984；无CI。','按压力/支持条件报告点；不沿用旧9.2–12.1区间，不升级物理损伤阈值。','合格物理尺度最低点区间与支持检验待V'),
    'MR20':('8分期均完成等价基；仅后期month_12冗余，η差异约1.42e-14；天气早E最低点不在支持。','图10改用各期全拟合物理q，保留开发历史；旧CV加权名义区间不画。','时间稳定性和区间待V；原日历效应不可全解释'),
    'MR21':('raw ln(stage)控制和公共分箱已生成；主组pooled均值21.451355→17.639357→15.846195→11.708115h，旧先升后降不再出现。','重审旧阶段故事；明确开发期截尾与全期all_valid不同；天气图按数值分箱修复排序，缺首阶段仍保留，不作真实维修动作解释。','缺首阶段排除敏感性/记录完整性待V'),
    'MR22':('K块使用最终聚合客户数训练变换；更新贡献仍有事后信息。','保持retrospective解释；不能作初期调度可用预测器。','真实可用信息时点与应用场景证据'),
    'MR23':('当前OOF误差、残差及exp残差全局均值诊断已输出；未作条件算术均值校准。','分开η、expη、customers/h；图7比不能自动成工程倍数。','V工程误差/校准与参考支持'),
    'MR24':('图6/7已从当前档案导出；Buck标签与参考关系明确。','保留为描述性附加量级图，主问题贡献仍待作者审阅；不擅自删除。','区域解释与图件留存审阅'),
    'MR25':('164当前生产拟合+1废弃部分档案；70核心已验收，12图组PNG/PDF；原代码/Word未动。','新表/图/档案有SHA；950旧数字槽位含明确未映射状态，不能宣称全稿已自动回填。','R05旧槽位/覆盖缺口复审'),
    'MR26':('B1天气E增量转正、三阶改进及25日去重改变旧叙述；完整R04当前证据可用。','按形状支持→条件信息→过程/工程→敏感性组织待写方案；六章仍是待审建议。','作者审阅结构；R05后依指令进入V/W'),
    'MR27':('新模型未新增文献/官方天气、cause及跨年边界来源证明。','来源限制不因模型完成而关闭；原参考编号不机械替换。','来源逐项核验/作者资料'),
    'MR28':('C10编号缺口历史关闭状态保留；科学Buck重建仍MR08负责。','不把编号闭合扩大为Buck科学问题已解决。','MR08重建与对照'),
    'MR29':('113非空码可连接；正式主111/天气105 LAD；边界等价未新证。','写键兼容与边界兼容区别，不说113全错或零错配。','LAD21/23兼容证据及敏感性'),
    }
    sourcefiles=[W/'reports/R04_report.md',W/'tables/H0_R1_B1_COMPARISON.md',W/'tables/NUMERIC_LEDGER.md',W/'tables/RETAINED_ANALYSIS_COVERAGE.md',Q/'CALENDAR_BASIS_REPAIR.md',Q/'checks/core_actual_acceptance.json',Q/'checks/calendar_equivalence.json',Q/'checks/R1_acceptance.json',Q/'checks/supplement_execution.json',Q/'checks/final_isolation.json',Q/'figures/FIGURE_MANIFEST.json',Q/'tables/customer_aggregation_comparison.json']
    sm=read(M/'SOURCE_MANIFEST.json');nextid=max(int(x['source_id'][3:]) for x in sm['sources'] if x['source_id'].startswith('SRC'))+1;source_map={}
    for p in sourcefiles:
        sid=f'SRC{nextid:02d}';nextid+=1;dest=M/'evidence'/f'{sid}_{p.name}';shutil.copyfile(p,dest);source_map[str(p.relative_to(W))]=sid;sm['sources'].append({'source_id':sid,'original_name':p.name,'path':dest.relative_to(M).as_posix(),'role':'R04同次本地执行证据；非独立科学验证','sha256':sha(dest),'size_bytes':dest.stat().st_size})
    sm.update(version='MR-v1.3-R04',checkpoint='R04_completed_R05_not_started',date=now);put(M/'SOURCE_MANIFEST.json',sm);put(M/'R04_SOURCE_MAP.json',source_map)
    impactrows=[]
    for item in doc['items']:
        previous={k:copy.deepcopy(v) for k,v in item.items() if k not in ['history','review_history']};item.setdefault('history',[]).append(previous);ev,act,condition=notes[item['id']]
        item.update(evidence=ev,action=item['action']+' R04当前行动：'+act,release_condition=condition,decision_status='R04实际结果已登记；不等于科学主张关闭',checkpoint='R04_completed_R05_not_started',word_status='尚未写入Word')
        item['sources'].append('R04来源映射：'+', '.join(source_map.values())+'；具体对应见R04_SOURCE_MAP与R04_WRITING_IMPACT')
        item['r04_update']={'evidence':ev,'judgment':'程序/数值实际验收与科学主张分开','action':act,'release_condition':condition,'locations':item['locations'],'claims':item.get('claim_ids',[]),'Word':'尚未写入Word','source_map':'R04_SOURCE_MAP.json'}
        impactrows.append({'MR':item['id'],'位置':', '.join(item['locations']),'当前实测证据':ev,'后续具体动作':act,'CL':','.join(item.get('claim_ids',[])),'释放条件':condition,'Word':'未修改'})
    doc.update(version='MR-v1.3-R04',checkpoint='R04_completed_R05_not_started');put(M/'REVISION_ITEMS.json',doc)
    claims=[('CL01','事件后果的观察性描述','R02代理已进入B1；四组n明确；最小编号与最早时刻比较需消歧','真实onset/源记录完整性/天气定义仍未证'),('CL02','形状与条件最低点','主E10.807545；三阶OOF改进0.001931639；天气早E无支持内最低点','稳健U形/最低点CI/物理阈值尚未建立'),('CL03','条件信息贡献','主G|K<K|G；天气G|K>K|G；天气E增量转正','跨组稳定反转及不确定性待V'),('CL04','风暴及时间证据','25唯一日；主4452；训练内与日期OOF独立标识；图10编码通过','不能升级为完整过程留出或未接触后期验证'),('CL05','参考量级与工程含义','新图4/6/7的数学量与误差诊断齐备','无算术均值校准/工程效能验证'),('CL06','机制与区域解释','阶段与区域描述重算；Buck历史代理保留','LSOA重建并对照仍必须执行；不能认定调度/维修机制')]
    claimdf=pd.DataFrame(claims,columns=['CL','主张职责','当前证据','仍需条件']);put(M/'CLAIM_STATUS_R04.json',claimdf.to_dict('records'))
    impact='# R04_WRITING_IMPACT — MR-v1.3-R04\n\n只记录后续写作动作，不修改Word。保留原MR/CL/PD及RV03审阅历史。当前模型证据不等于作者接受全部故事变更。\n\n## 主张状态\n\n'+markdown(claimdf)+'\n## 逐条MR：证据→判断→位置→动作→CL→条件\n\n'+markdown(pd.DataFrame(impactrows))+'''
## 逐章联动

- 摘要/引言RQ：n更新60436；最低点10.81为条件点。天气E负增量已不成立；贡献点排序仍存在但不能称稳定反转；三阶反向证据必须进入形状评价。
- 数据章/附录A/B：时间用最早记录UTC代理；分清聚合C、全阶段跨度D、最小阶段编号与最早时刻比较；写天气可用性分母和113码边界兼容未决，不以新拟合消除来源问题。
- 方法章/附录E/F/H：all_valid、ddof=1训练变换、共同fold、pooled/mean-fold分列；G/K块和参考/平均顺序明确；等价日历基及支持边界；p/SE描述与科学稳定性分开。
- 结果章：按“形状与支持→条件信息贡献→过程/工程量级→敏感性”组织待写方案。六原因组改为当前all_valid对应物，旧附录D开发期表须明确保留历史还是改全期职责，不能无标签混表。
- 风暴段：27累计窗口日与25唯一日分开；主4452/60436、745372/5622103；Eunice按明确群体读storm_LAD_details；图9仅训练描述与日期OOF。
- 图注/附录：图1当前不含许可区线/全国inset且为经纬度，需与旧A-P013“all projected”同步核对；图2原尺度纵轴log计数；图3非未接触验证；图4/6/7指数尺度不等于算术均值；D1当前四面板，不沿用旧双面板图注。
- 讨论/结论：正二次项和GLM同向不能压过三阶改进；无最低点CI、独立过程验证或校准。图6/7是否服务主问题及六章结构仍待作者审阅。Buck重建及代理对照保留为已有作者决定。

## 作者决定与未落稿状态

PD原始内容不变，特别是Buck代理暂留、后续LSOA重建并对照，以及六章结构待审。R04只按用户授权冻结all_valid和局部等价编码执行；未把结果是否好看作为协议选择条件。所有29个MR与6个CL的Word落实状态仍未落稿。
'''
    write(M/'R04_WRITING_IMPACT.md',impact)
    oldmd=(M/'MANUSCRIPT_LEDGER.md').read_text(encoding='utf-8');write(M/'MANUSCRIPT_LEDGER.md','# 当前版本 MR-v1.3-R04\n\nR04实际拟合/OOF、图10等价编码和补充分支已完成，R05/V/W未执行，Word未修改。以下先列R04当前主张及影响；后续原台账全文作为逐阶段历史保留，原PD作者决定不被当前建议覆盖。\n\n'+markdown(claimdf)+'\n当前完整逐条证据/动作见REVISION_ITEMS.r04_update及R04_WRITING_IMPACT.md；旧数字未全映射与图/附录职责差异见覆盖表。\n\n---\n\n'+oldmd+'\n\n## R04实际结果增量（当前）\n\n'+markdown(pd.DataFrame(impactrows)))
    write(M/'CHANGELOG.md',(M/'CHANGELOG.md').read_text(encoding='utf-8')+'\n## MR-v1.3-R04\n\n先合并RV03后完成实际运行；29项MR追加历史与R04事实，6CL更新；保留全部PD。新增来源SRC27起及映射、完整R04_WRITING_IMPACT。主要变化：天气E0增量转正；三阶反向线索重算；25唯一风暴日；图10等价基；first-stage定义消歧。R05/V/W未执行，Word未改。\n')
    write(M/'START_HERE.md','# 当前完整台账 MR-v1.3-R04\n\n先读R04_WRITING_IMPACT.md，再读MANUSCRIPT_LEDGER.md和REVISION_ITEMS.json；R04_SOURCE_MAP/SOURCE_MANIFEST绑定本次实际证据，RV03_SOURCE_MAP保留审阅增量来源。原历史/PD全部保留，Word仍未修改。R05尚未开始。\n')
    after=M/'stage_snapshots/MR-v1.3-R04';after.mkdir(parents=True,exist_ok=False)
    for name in ['REVISION_ITEMS.json','MANUSCRIPT_LEDGER.md','SOURCE_MANIFEST.json','CHANGELOG.md','R04_WRITING_IMPACT.md','R04_SOURCE_MAP.json','CLAIM_STATUS_R04.json']:shutil.copyfile(M/name,after/name)
    # Update state without overwriting its historical checkpoints.
    st=read(W/'RUN_STATE.json');st.update(active_stage='R04',last_updated=now,baseline='R04_B1_all_valid_v1 actual core/OOF generated; R05 not started; H0 historical retained')
    st['stages']['R04'].update(execution_status='completed_with_declared_coverage_gaps',report='reports/R04_report.md',inputs=['R03/configs/R04_primary.json','r04_review_handoff/','R02/data/R02_event_master.parquet'],outputs=['R04/','baseline/B1_MANIFEST.json','manuscript_record/','RETURN_PACKAGE_R04.zip'],blockers=[],ledger_version='MR-v1.3-R04',models_reestimated=True,production_fits=164,word_modified=False,remaining='R05 review of numeric semantic slots, figure1 decorations and old appendix responsibilities; scientific V not run')
    put(W/'RUN_STATE.json',st);write(W/'STATUS.md','# R04完成并停止\n\n冻结all_valid核心/正式OOF、R1兼容诊断、8分期等价基、GLM/三阶/六组和当前图表已生成，实际检查通过。当前完整台账MR-v1.3-R04。旧数字逐槽映射/部分旧图及附录职责缺口明确保留；不是R05复审通过。R05/V/W未执行，Word及原研究代码未修改。详见reports/R04_report.md、tables/RETAINED_ANALYSIS_COVERAGE.md。\n')
    write(W/'DECISIONS.md',(W/'DECISIONS.md').read_text(encoding='utf-8')+'\n## R04执行登记（不覆盖作者决定）\n\n用户本轮授权：冻结all_valid正式运行，独立等价日历编码和现有分析补全；不执行备选共同训练p99/500bootstrap/R05/V/W。实际只在冗余日历块移除month_12；数据和核心源身份不变。B1天气E增量转正及三阶改进如实保留，不改变主协议。Buck后续LSOA重建并对照和六章结构待审状态不变。\n')
    issues=read(W/'issue_ledger.json')
    for issue in issues:
        issue.setdefault('history',[]).append({k:copy.deepcopy(v) for k,v in issue.items() if k!='history'})
        issue['r04_actual_evidence']='reports/R04_report.md; baseline/B1_MANIFEST.json; manuscript_record/R04_WRITING_IMPACT.md'
        if issue['id'] in ['C01','C02','C03','C04','C05','C06','C07','C08','C09']:
            issue['execution_scope']='R04 frozen formal core/OOF and declared current consumers completed; science not closed';issue.setdefault('repair_milestones',{})['models_reestimated']=True
        issue['remaining']='See MR-v1.3-R04 item-specific release conditions; R05/V/W not started; no Word edits'
    put(W/'issue_ledger.json',issues);write(W/'ISSUE_LEDGER.md',(W/'ISSUE_LEDGER.md').read_text(encoding='utf-8')+'\n## R04当前增量\n\n实际模型/OOF与当前消费者见reports/R04_report.md；逐条科学释放条件以MR-v1.3-R04为准。原条目和历史保留，未把程序通过等同科学关闭。\n')
    # Local full artifact identities (large OOF/model arrays remain local, no hidden H0 fallback).
    codefiles=[p for p in (Q/'src').glob('*.py')]+[Q/'cli.py']
    put(Q/'CODE_MANIFEST.json',{'version':'R04_extensions_v1','frozen_core_identity':formal['code_identity'],'files':[entry(p) for p in codefiles],'policy':'only independent work-root sources and copied R03/R04 libraries imported'})
    outputs=[]
    for folder in [RUN,Q/'R1_input_compat_v1',Q/'periods_v2',Q/'supplements_v1',Q/'figures',Q/'tables',Q/'checks',Q/'configs']:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and 'archive' not in p.parts:outputs.append(entry(p))
    bm={'version':'B1_R04_actual_v1','status':'core_and_current_consumers_generated_pending_R05','timestamp_utc':now,'input_identity':read(Q/'checks/preflight.json')['identities'],'core_run':entry(RUN/'RUN_MANIFEST.json'),'extensions':entry(Q/'CODE_MANIFEST.json'),'groups':acc['four_groups'],'active_production_fits':164,'superseded_partial_producer_fits':1,'ancillary_covariance_verification_fits':32,'branches':{'R1':'64 fits historical compatibility p99, not optional common training p99','periods_v2':'8 fits equivalent basis','supplements_v1':'22 fits; all-valid six-group counterpart'},'outputs':outputs,'coverage':entry(W/'tables/RETAINED_ANALYSIS_COVERAGE.md'),'numeric_ledger':entry(W/'tables/NUMERIC_LEDGER.md'),'isolation':entry(Q/'checks/final_isolation.json'),'unexecuted':['R05','V00–V04','W','500-bootstrap','optional common training p99','Buck LSOA reconstruction'],'declared_gaps':['old text numeric semantic mapping incomplete','figure1 licence boundaries/inset absent','old development-only p99 appendix not directly replaced by combined all_valid controls'],'Word_modified':False}
    bm.update(total_producer_parameter_solves=166,unarchived_aborted_period_solves=1,retained_producer_archives_including_superseded=165)
    put(W/'baseline/B1_MANIFEST.json',bm)
    ret='# R04返回摘要\n\n完整报告回答6项接续问题，完整当前台账为manuscript_record/（MR-v1.3-R04）。仅R04已执行，R05/V/W未开始；Word及原代码未修改。\n\n'+markdown(full[['group','target','n','pooled_R2','mean_fold_R2']])+'''\n- 当前生产拟合164次，另1个失败分支部分档案保留；核心70、R1 64、分期8、补充22。无缺失OOF预测。
- 主/天气R0c G|K分别1.142120/3.579704pp，K|G分别6.141467/1.507182pp。H0/R1/B1人口评分与共同事件预测已分表。
- 主E0最低点10.807545m/s，无CI。天气E0 G增量转正到+0.382246pp；三阶E0增R²0.001931639，旧形状故事需审阅。
- 图10等价基通过，4后期仅移除month_12，科学项可识别；旧日历效应不全部唯一。
- 图1–10、D1/F1共12组PNG/PDF实出并目视核对；图1许可区线/inset缺口明确，旧开发期附录与当前全期对应物不能混用。
- 27累计窗口日→25唯一日；主4452唯一风暴事件7.366470%，客户13.257886%。图9仅描述/日期OOF，非完整过程留出。
- MR01–29/CL01–06当前增量、PD历史和R04_WRITING_IMPACT完整返回；Buck后续重建仍是作者已决定的任务。

交付：reports/R04_report.md；tables/H0_R1_B1_COMPARISON.md、NUMERIC_LEDGER.md、RETAINED_ANALYSIS_COVERAGE.md；R04/CALENDAR_BASIS_REPAIR.md；baseline/B1_MANIFEST.json；R04/figures/；完整manuscript_record/。完整模型/OOF保留本地，B1清单提供绝对路径/大小/SHA；zip仅含小型审阅材料、图件与完整台账。

R05应重点审阅天气E0增量变化、三阶反证、六组和附录口径、旧数字尚未逐项映射以及科学验证的V方案。本摘要不构成R05验收通过或进入V/W的授权。
'''
    write(W/'RETURN_TO_CHATGPT.md',ret)
    put(M/'BUNDLE_MANIFEST.json',{'version':'MR-v1.3-R04','files':[entry(p) for p in sorted(M.rglob('*')) if p.is_file() and p.name!='BUNDLE_MANIFEST.json']})
    # Portable small package: complete ledger, results and current code, not external raw/runtime.
    files=set()
    for folder in [M,Q/'figures',Q/'tables',Q/'checks',Q/'configs',Q/'src',Q/'logs']:
        files.update(p for p in folder.rglob('*') if p.is_file() and not any(x.startswith('archive') for x in p.parts))
    files.update(p for p in M.rglob('*') if p.is_file())
    files.update([W/'reports/R04_report.md',W/'tables/H0_R1_B1_COMPARISON.md',W/'tables/NUMERIC_LEDGER.md',W/'tables/RETAINED_ANALYSIS_COVERAGE.md',Q/'CALENDAR_BASIS_REPAIR.md',Q/'CODE_MANIFEST.json',Q/'cli.py',W/'baseline/B1_MANIFEST.json',W/'RETURN_TO_CHATGPT.md',W/'RUN_STATE.json',W/'STATUS.md',W/'DECISIONS.md'])
    for p in (Q/'frozen').glob('*MANIFEST.json'):files.add(p)
    package_manifest={'files':[{'path':p.relative_to(W).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]}
    pp=Q/'RETURN_PACKAGE_MANIFEST.json';put(pp,package_manifest);files.add(pp)
    zip_path=W/'RETURN_PACKAGE_R04.zip';assert not zip_path.exists(),'Preserve existing return archive'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,p.relative_to(W).as_posix())
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        for x in package_manifest['files']:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
    put(Q/'checks/return_package_validation.json',{'passed':True,'files':len(files),'package':entry(zip_path),'complete_ledger_included':True})
    # Overall work-root manifest is regenerated last and excludes itself.
    put(W/'ARTIFACT_MANIFEST.json',{'timestamp_utc':now,'stage':'R04','files':[entry(p) for p in sorted(W.rglob('*')) if p.is_file() and p!=W/'ARTIFACT_MANIFEST.json']})
    print('R04 delivered',zip_path,zip_path.stat().st_size,'bytes; original paths unchanged',len(protected),flush=True)
if __name__=='__main__':run()
