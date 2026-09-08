from common import *
import re
from candidate_text import build_candidates

def run():
    T=R4/'tables';M=W/'manuscript_record';idx={v['id']:v for f in ['D','A'] for v in read(M/f'{f}_word_index.json')};ledger=read(M/'REVISION_ITEMS.json');candidates=build_candidates();slots=pd.read_csv(T/'ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',keep_default_na=False);cells=pd.read_csv(T/'CURRENT_NUMERIC_BINDINGS.csv',keep_default_na=False);paras=pd.read_csv(T/'CURRENT_PARAGRAPH_NUMERIC_BINDINGS.csv',keep_default_na=False)
    cf=pd.read_csv(T/'Tables3_F_complete_coefficients.csv',float_precision='round_trip');desc=pd.read_csv(T/'Table1_current.csv');sc=pd.read_csv(T/'AppendixH_period_scales.csv');pm=read(T/'AppendixH_pressure_minima.json');dec=pd.read_csv(T/'AppendixG_main_gust_deciles.csv');support=pd.read_csv(T/'AppendixG_low_gust_support.csv').set_index('population');folds=pd.read_csv(T/'AppendixC_fold_summary.csv');storm=pd.read_csv(T/'storm_LAD_details.csv');res=pd.read_csv(T/'residual_diagnostics.csv');ranges=pd.read_csv(T/'regional_reference_ranges.csv');qa=[];look={}
    terms=['const','zG','zG2','zRain24','zTemp','zPressure','zG_zPressure','urban_binary','log_population','income_deprivation_rate','deprivation_gap_pct','morans_i','zK','zK2']
    def add(row,expected,key,target_name,pop,unit,kind):
        old=float(row.new_value);assert np.isclose(old,expected,atol=1e-12,rtol=1e-12),(row.old_location,old,expected)
        q={'kind':kind,'old_location':row.old_location,'cell':row.cell,'old_token':getattr(row,'old_numeric_token',''),'new_value':expected,'unit':unit,'target':target_name,'population':pop,'n':row.n,'artifact':getattr(row,'artifact',getattr(row,'current_artifact','')),'row_key':key,'numeric_check':'passed','semantic_result':'explicit target/population/unit supplied; full sentence must follow candidate','old_target':row.target};qa.append(q);look.setdefault((row.old_location,row.cell,getattr(row,'old_numeric_token','')),[]).append(q)
    for r in cells.itertuples():
        ri,ci=map(int,re.match(r'row(\d+)col(\d+)',r.cell).groups());loc=r.old_location
        if loc=='D-T01':
            tar,scale=[('E0','raw'),('E0','log'),('R0c','raw'),('R0c','log')][ci-2];st=['Mean','Median','SD','Min','25th pct.','75th pct.','Max'][ri-2];x=desc[(desc.target==tar)&(desc.scale==scale)&(desc.statistic==st)].iloc[0];val=x.value;key=f'target={tar}; scale={scale}; statistic={st}';pop='main all_valid';unit='customers' if tar=='E0' and scale=='raw' else 'hours' if scale=='raw' else 'ln(1+C)' if tar=='E0' else 'ln(D/h)'
        elif loc in ['A-T08','A-T09']:
            tar='E0' if loc=='A-T08' else 'R0c';term=terms[ri-2];cov='LAD_CR1' if ci<5 else 'LAD_date_two_way_CR1';field={2:'coefficient',3:'SE',4:'p_normal_CR1_descriptive',5:'SE',6:'p_normal_CR1_descriptive'}[ci];val=cf[(cf.group=='main')&(cf.target==tar)&(cf.term==term)&(cf.covariance==cov)].iloc[0][field];key=f'main; {tar}; {term}; {cov}; field={field}';pop='main all_valid';unit='normal-reference p (not bootstrap)' if field.startswith('p_') else field+' per design-column unit; regional rate/gap on 0–1 scale'
        elif loc=='A-T13':
            tar,per=[('E0','development'),('E0','later'),('R0c','development'),('R0c','later')][ri-2];field='gust_mean' if ci==3 else 'gust_sd';val=sc[(sc.group=='main')&(sc.target==tar)&(sc.period==per)].iloc[0][field];key=f'main;{tar};{per};{field}';pop='main '+per;unit='m/s'
        elif loc=='A-T11':
            z=pm[ri-2];tar='E0';val=(z['algebraic_vertex_ms']-z['gust_mean'])/z['gust_sd'] if ci==2 else z['minimum_ms'];key=f'pressure row index={ri-2}; '+('standardized vertex' if ci==2 else 'minimum_ms');pop='main all_valid';unit='own-fit standardized gust' if ci==2 else 'm/s'
        elif loc=='A-T10':tar='weather-group membership proportion';val=dec.iloc[ri-2].weather_pct;key=f'main decile ascending index={ri-2};weather_pct';pop='main all_valid gust bin';unit='percent within main gust bin'
        else:raise AssertionError(loc)
        add(r,val,key,tar,pop,unit,'cell')
    for r in paras.itertuples():
        loc=r.old_location;tok=r.old_numeric_token;pop='main all_valid';tar='E0/R0c descriptive';key='';val=None;unit=r.unit
        if tok in ['60,453','60,437','59,834'] and loc in ['D-P002','D-P039','A-P018','A-P065']:val=60436;key='core_metrics: main E0 G and R0c GK n'
        elif tok in ['10.7','10.694','10.69']:val=pm[1]['minimum_ms'];key='pressure row=1;minimum_ms';tar='E0 conditional minimum'
        elif loc=='D-P017':field='gust_mean' if tok=='9.87' else 'gust_sd';val=pm[1][field];key='pressure row=1;'+field;tar='gust descriptive'
        elif loc in ['D-P030','A-P018']:
            vals={'47.13':47.12833410550003,'93.02':93.02572969753128,'1.97':1.9738811367549456};val=vals[tok];key='R05 CUSTOMER_COMPARATOR_SUMMARY: main, common n60436; minimum numeric stage' if tok!='93.02' else 'R05 customer main aggregate_C common mean';tar='customer comparator';unit='ratio of means on common population' if tok=='1.97' else 'customers'
        elif loc=='D-P073':
            val=(pm[1]['minimum_ms']-pm[1]['gust_mean'])/pm[1]['gust_sd'] if tok=='0.157286' else pm[0 if tok=='9.656' else 2]['minimum_ms'];key='pressure row='+str(1 if tok=='0.157286' else 0 if tok=='9.656' else 2);tar='E0 conditional minimum'
        elif loc=='A-P076':field={'−0.032325899095631154':'beta1','0.10276170747389514':'beta2','−0.0408384359554068':'beta3_interaction','9.87229677581956':'gust_mean','5.222713076874045':'gust_sd'}[tok];val=pm[1][field];key='pressure row=1;'+field;tar='E0'
        elif loc=='D-P006':
            win='Franklin' if tok=='1,187' else 'Eunice';field={'1,601':'events','101':'LAD','376,712':'customers','52.7':'duration_mean_hours','1,187':'events','39.4':'gust_max_ms'}[tok];val=storm[(storm.population=='main')&(storm.window==win)].iloc[0][field];key=f'main;window={win};{field}';pop='main '+win;tar='event description; not weather-only'
        elif loc=='D-P102':
            vals={'27':25,'2.46':25/1096*100,'8.15':4452/60436*100,'14.72':745372/5622103*100,'3.3':(4452/60436)/(25/1096),'6':(745372/5622103)/(25/1096)};val=vals[tok];key='main UNIQUE_ANY; calendar1096; unique_days25; events4452/60436; customers745372/5622103';tar='storm union descriptive'
        elif tok=='0.15' and loc=='D-P101':m=read(RUN/'weather_E0/contributions.json');val=100*m['gust_from_control'];key='weather E0 gust_from_control ×100';tar='E0 pooled OOF increment';pop='weather all_valid'
        elif tok in ['63.70','36.83','57.8']:
            g='main' if tok=='63.70' else 'weather';val=support.loc[g,'below_pct'] if tok!='57.8' else 100*support.loc['weather','below_pct']/support.loc['main','below_pct'];key='low_gust_support '+g+' below_pct' if tok!='57.8' else 'weather/main below_pct ×100';pop=g if tok!='57.8' else 'ratio of weather/main within-group shares';tar='support description'
        elif tok in ['6.89','56.10']:val=dec.weather_pct.iloc[0 if tok=='6.89' else -1];key='main decile '+('lowest' if tok=='6.89' else 'highest')+' weather_pct';tar='weather membership proportion'
        elif loc=='A-P091':tar='E0' if tok=='10.46' else 'R0c';val=res[res.target==tar].iloc[0].mean_exp_residual_diagnostic_only;key='residual diagnostics '+tar+' mean_exp_residual_diagnostic_only';unit='full-fit diagnostic factor; not applied'
        elif loc=='D-P038':
            g='six_groups' if tok in ['0.0608','0.0257','116,064'] else 'main';term='zG2' if tok in ['0.0608','0.0792'] else 'zG';val=(117108 if g=='six_groups' else 60436) if ',' in tok else folds[(folds.group==g)&(folds.term==term)].iloc[0].mean_coefficient;key=f'{g};{term};'+('evaluation_n' if ',' in tok else 'mean_coefficient');pop=g+' all_valid';tar='R0c overlapping training-fold summary'
        elif loc=='D-P097':val=9857;key='weather E0 G and R0c GK n';pop='weather all_valid'
        elif loc=='D-P093':tar='E0' if tok=='1.96' else 'R0c';val=ranges[ranges.target==tar].iloc[0].map_max_min_ratio;key=tar+' regional_reference_ranges map_max_min_ratio';unit='ratio of exponentiated reference values;111 LAD'
        else:raise AssertionError((loc,tok))
        add(r,val,key,tar,pop,unit,'paragraph')
    assert len(qa)==246;out=pd.DataFrame(qa);out.loc[(out.old_location=='A-T10'),'semantic_result']='CORRECTED: stale six-group target label; numeric values already main deciles, no model change';table(Q/'tables/NUMERIC_BINDING_SEMANTIC_AUDIT.csv',out)
    # Correct only R05 derivative bindings; preserve original files.
    cells.loc[cells.old_location.eq('A-T10'),'target']='weather membership proportion within main gust decile'
    table(Q/'tables/CURRENT_NUMERIC_BINDINGS_R05.csv',cells);table(Q/'tables/CURRENT_PARAGRAPH_BINDINGS_R05.csv',out[out.kind.eq('paragraph')])
    baseline={'D':'196cef4abcdf4e6723b55035049c08de75613c3cc5a56314b264490f70e5926c','A':'55f5c4f30fc75473d9da354b2819d3f8298904b8be94104ca3e107276696af8c'}
    # Each old location gets a substantive candidate or a scoped preservation/disposition.
    table_sources={'D-T01':'Table1_current.csv','D-T02':'contracts/DATA_CONTRACT.md','D-T03':'Tables3_F_complete_coefficients.csv','D-T04':'H0_R1_B1_increments.csv','A-T01':'R03/CONTRACTS.md cause map','A-T02':'contracts/WEATHER_AND_REGIONAL_SOURCES.md + R05 SOURCE_DEPENDENCIES.csv','A-T03':'AppendixC_fold_summary.csv','A-T04':'AppendixD_period_stage_counts.csv','A-T05':'R04_B1_all_valid_v1/main_R0c/step27_stage_coefficients.csv','A-T06':'historical original Word table / MR18 sources','A-T07':'historical original Word table / MR19 sources','A-T08':'Tables3_F_complete_coefficients.csv','A-T09':'Tables3_F_complete_coefficients.csv','A-T10':'AppendixG_main_gust_deciles.csv','A-T11':'AppendixH_pressure_minima.json','A-T12':'historical bootstrap; MR19 sources, not B1 CI','A-T13':'AppendixH_period_scales.csv'}
    hist={'A-P020','A-P023','A-P038','A-P040','A-P057','A-P059','A-P060','A-P061','A-P063','A-P078','A-P080','A-P082','A-P086','D-P055','D-P075'}
    mapping=[]
    for i,r in enumerate(slots.itertuples(),1):
        loc=r.old_location;matches=out[(out.old_location==loc)&(out.cell==r.cell)]
        if not r.cell:matches=matches[matches.old_token==r.old_numeric_token]
        bind=matches.iloc[0] if len(matches) else None;cand=candidates.get(loc);source=cand['evidence'] if cand else table_sources.get(loc,r.current_artifact);newvalue=bind.new_value if bind is not None else r.new_value;unit=bind.unit if bind is not None else r.unit;pop=bind.population if bind is not None else 'specified in candidate/evidence; not inferred from old n';need='';targetsection=cand['section'] if cand else 'retain current location pending author structure decision'
        if cand:action='whole_paragraph_or_caption_rewrite';text=cand['text'];need=cand.get('pending','')
        elif loc in table_sources:
            if loc in ['A-T06','A-T07','A-T12']:action='retain_explicit_history';text='Historical development/Bootstrap table; retain dated source and historical population. Do not replace its values with B1 or present it as current validation.';need='W author decision on historical appendix length; no new fit required'
            elif loc in ['A-T04','A-T05']:action='propose_full_period_counterpart';text='Replace the whole table and caption with the explicitly labelled current full-period counterpart. Preserve the old development table in the ledger; population change forbids token substitution.';need='Author approval of full-period replacement in W; no automatic old-population refit'
            elif loc in ['A-T01','A-T02','D-T02']:action='definition_or_code_table';text='Keep implemented code identifiers; revise definitions: gap is within-LAD LSOA range, Moran is within-LAD LSOA clustering, rate/gap stored as proportions, Buck is proxy; source gaps remain explicit.';need='T01/T02 official source and geography conditions'
            else:action='current_table_replacement';text='Use complete current table with explicit target, population, units, covariance or OOF score definition; do not infer old p-values or historical samples.'
        elif loc in hist:action='retain_explicit_history';text='Retain this paragraph only as dated development history with its original population and source. These numbers are not current B1 evidence.';need='Historical source binding retained; no new scientific validation claimed'
        else:
            meta=idx.get(loc,{})
            if loc.startswith('D-P') and int(loc.split('P')[1])>=125:action='retain_bibliographic_metadata';text='Preserve reference numbering/year/pages as bibliography; unresolved bibliographic fields remain marked for source verification, not model-value replacement.';need='W citation verification where explicitly unverified'
            elif meta.get('math') or ('equation' in r.status) or len(r.old_context)<180:action='retain_definition_formula_or_reference';text='Retain the meaning of this formula/index/date/cross-reference; synchronize only numbering and linked caption at W. No new empirical value is asserted.'
            else:action='retain_context_with_evidence_limit';text='Retain non-numeric argument context; this old numeric token is not released as a B1 estimate. Follow linked MR source and chapter candidate before W.';need='Paragraph-level source/wording check at W'
        links=[x for x in ledger['items'] if loc in x['locations']]
        mapping.append({'slot_id':f'NS{i:04}','old_Word_baseline_SHA':baseline[loc[0]],'old_location':loc,'table_cell_or_context':r.cell or r.old_context,'MR':','.join(x['id'] for x in links) or r.MR,'CL':','.join(sorted({c for x in links for c in x.get('claim_ids',[])})) or r.CL,'old_claim':r.old_context,'old_numeric_token':r.old_numeric_token,'current_evidence_path':bind.artifact if bind is not None else source,'evidence_row_key':bind.row_key if bind is not None else (cand.get('key','whole declared source table') if cand else 'see source and disposition; not a new estimate'),'new_numeric':newvalue,'unit':unit,'population':pop,'candidate':text,'disposition':action,'missing_condition':need,'candidate_new_section':targetsection,'Word_status':'not_modified'})
    # Include candidate paragraphs and titles without numeric slots as separate addressable rows.
    have=set(slots.old_location)
    for loc,c in candidates.items():
        if loc in have:continue
        links=[x for x in ledger['items'] if loc in x['locations']];mapping.append({'slot_id':'TEXT-'+loc,'old_Word_baseline_SHA':baseline[loc[0]],'old_location':loc,'table_cell_or_context':idx[loc].get('text',''),'MR':','.join(x['id'] for x in links),'CL':','.join(sorted({k for x in links for k in x.get('claim_ids',[])})),'old_claim':idx[loc].get('text',''),'current_evidence_path':c['evidence'],'evidence_row_key':c.get('key','whole declared source table'),'candidate':c['text'],'disposition':'whole_paragraph_or_title_rewrite','missing_condition':c.get('pending',''),'candidate_new_section':c['section'],'Word_status':'not_modified'})
    table(Q/'MANUSCRIPT_MIGRATION_MAP.csv',pd.DataFrame(mapping));put(Q/'tables/PARAGRAPH_CANDIDATES.json',candidates)
    required=['A-P027','A-P044','A-P054','D-P039','D-P041','D-P084','D-P093','D-P097','D-P106','D-P111','D-P116'];assert all(k in candidates for k in required)
    intro='# R05 章节与段落候选修改（未写入Word）\n\n本文件是审阅候选，按已核实B1证据收窄论断；不是完成W或论文可投稿。当前五章保持原状。建议将讨论独立为第5章、结论为第6章；如作者保留五章，将讨论职责安排在结论前独立小节。两种选择不改变证据边界。\n\n研究主线：阶段记录→可解释的事件后果→条件阵风关系→阵风/客户事后信息增量→样本、时间、来源与工程适用范围。RQ1回答条件形状及支持范围；RQ2回答固定组内配对增量；RQ3作为建议明确提出适用范围，当前只给回顾性敏感性，完整过程评价与工程误差待V。\n\n数字语义审查：182单元格+64段落绑定逐值对账，A-T10有10处沿用“six-group membership”目标标签但数值已经是主样本decile，现仅修正R05派生标签。950槽位保持独立：包括文献年、公式号、历史和整句处置，绝不等于950个科学主张关闭。11处组合段落全部给完整候选。图像OCR和全部公式对象不在950槽位范围，W仍需最终Word检查。\n\n章节职责：摘要先更新n/最低点/回顾性边界；引言不预设U形与稳健排序；数据按单位→C/D→时间代理→天气/区域→共识与样本；方法区分目标/块/训练内尺度/OOF/物理参照/推断；结果依次形状、贡献、窗口、分期；讨论解释事后信息与观测记录局限；结论只回答已得到的条件点结果。图6/7继续保留，迁至附录仅是建议。\n\n附录A字典与来源；B两个记录比较；C六原因合并总体；D中性阶段组成；E真实历史；F协方差与残差；G支持描述及正增量；H条件点/旧Bootstrap/物理分期/回变换。\n\n'
    chunks=[intro]
    for loc,c in sorted(candidates.items()):
        n=int(loc.split('P')[1]);prefix=loc[:3];prev=idx.get(prefix+f'{n-1:03}',{}).get('text','');nxt=idx.get(prefix+f'{n+1:03}',{}).get('text','');chunks.append(f"## {loc} → {c['section']}\n\n旧段：{idx[loc]['text']}\n\n前邻：{prev}\n\n后邻：{nxt}\n\n段落职责/处理理由：{c['reason']}\n\n证据：{c['evidence']}；行键：{c.get('key','当前对应总体/目标')}。\n\n候选英文：\n\n{c['text']}\n\n衔接检查：{c.get('bridge','从本段明确的对象转入下一方法或结果；相邻旧数值应与对应候选同步，不单句粘贴。')}\n\n未决：{c.get('pending','无新增数值缺口；候选尚待作者/W采用，科学边界按本段保留。')}\n")
    chunks.append('\n## 四轮审阅与功能完整性\n\n论证轮：RQ—方法—结果—解释对齐，反向证据（三阶有正增量、天气E转正、D1 pooled下降）已进入主线。证据轮：246绑定有逐值/行键/总体/单位，11组合段落完整，历史Bootstrap不充当B1区间。文字轮：区分stage number/time、span/CML、pooled/mean-fold、curve/reference/arithmetic mean，不新增机制或外部引文事实。交付轮：候选原文与邻段并列，Word SHA锁定，所有图件明确消费者。\n\nFUNCTIONAL-COMPLETENESS RETROSPECTIVE：覆盖R05候选及现有计算，非整篇Word最终校对；项目台账为权威状态，用户的R05范围高于建议技能；observational/computational设计检查及R04-review项目增量适用。六章为reviewer preference，其余数据/运行身份为project state，配对/训练内处理为design requirement，无期刊专属overlay。当前缺口为来源、形状、贡献不确定性、完整过程和工程尺度；没有获准的科学豁免。就进入V协议准备为conditional_for_V，尚非投稿就绪。\n')
    write(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md','\n'.join(chunks))
    put(Q/'checks/writing_audit.json',{'passed':True,'cell_bindings_checked':182,'paragraph_bindings_checked':64,'numeric_slots':950,'full_combination_paragraphs':required,'candidates':len(candidates),'migration_rows':len(mapping),'corrected_metadata_A_T10':10,'new_model_fits':0,'Word_modified':False,'candidate_exact_file':record(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md'),'mapping_exact_file':record(Q/'MANUSCRIPT_MIGRATION_MAP.csv'),'remaining_W_scope':'OCR/formula objects, exact Word layout, citation verification; six-chapter proposal not decided'})
    print('Writing and semantic audit complete',len(candidates),len(mapping),flush=True)
if __name__=='__main__':run()

