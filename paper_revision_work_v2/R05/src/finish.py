from common import *
import shutil,zipfile,datetime,importlib.util

def wsave(p,x):
    p=Path(p);assert p.resolve().is_relative_to(W);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def wtext(p,s):
    p=Path(p);assert p.resolve().is_relative_to(W);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')

def run():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();M=W/'manuscript_record';assert read(Q/'checks/numerical_audit.json')['passed'];assert read(Q/'checks/writing_audit.json')['passed'];assert read(Q/'checks/consumer_reproduction.json')['passed']
    # Reuse frozen tiny evidence in the actual return package, including consumer inputs.
    small=Q/'evidence_data';small.mkdir(exist_ok=True)
    for p in RUN.rglob('*'):
        if p.is_file() and p.suffix in ['.csv','.json'] and p.stat().st_size<220000 and not ('model' in p.name or p.name.startswith('oof_') or '_events' in p.name):
            dest=small/'core'/p.relative_to(RUN);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    for p in (R4/'checks').glob('*.json'):dest=small/'R04_checks'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
    # Confirm source and frozen-stage isolation against pre-R05 evidence, retaining changed work records separately.
    protected=read(Q/'checks/protected_at_start.json');original=[]
    for path,h in protected.items():p=Path(path);original.append({'path':path,'exists':p.exists(),'SHA_match':p.exists() and sha(p)==h})
    exceptions=[]
    for r in original:
        if r['SHA_match']:continue
        p=Path(r['path']);assert p.name=='LOG.md' and p.exists(),'Unexpected original code/Word difference'
        raw=p.read_bytes();prefix=None
        for i in range(len(raw)+1):
            if i==len(raw) or raw[i:i+1]==b'\n':
                for n in [i,i+1]:
                    if hashlib.sha256(raw[:n]).hexdigest()==protected[str(p)]:prefix=n;break
                if prefix is not None:break
        assert prefix is not None,'Changed log is not proven append-only'
        (Q/'evidence_data/observed_original_LOG_current.bin').write_bytes(raw);(Q/'evidence_data/observed_original_LOG_append.txt').write_bytes(raw[prefix:])
        exceptions.append({'path':str(p),'baseline_SHA':protected[str(p)],'current_SHA':sha(p),'baseline_bytes_verified_as_exact_prefix':prefix,'append_bytes':len(raw)-prefix,'modified_timestamp_local':datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),'attribution':'writer/process not established; no R05 executed code writes this path; log content belongs to separate historical cleanup','original_restored_or_modified_by_R05':False})
    table(Q/'tables/ORIGINAL_ISOLATION.csv',pd.DataFrame(original));put(Q/'checks/original_log_exception.json',exceptions)
    old=read(Q/'archive/ARTIFACT_MANIFEST_before.json')['files'];frozen=[]
    for r in old:
        p=Path(r['path'])
        if any(p.is_relative_to(W/x) for x in ['R02','R03','R04','contracts','inventory','baseline']):frozen.append({'path':str(p),'exists':p.exists(),'size_match':p.exists() and p.stat().st_size==r['bytes'],'hash_match':p.exists() and sha(p)==r['sha256']})
    assert all(x['size_match'] and x['hash_match'] for x in frozen);table(Q/'tables/FROZEN_STAGE_ISOLATION.csv',pd.DataFrame(frozen))
    put(Q/'checks/final_isolation.json',{'original_manifest_files':len(original),'original_all_hashes_match':not exceptions,'unchanged_original_files':sum(r['SHA_match'] for r in original),'append_only_log_exceptions':exceptions,'original_code_and_Word_hashes_match':True,'frozen_stage_manifest_files':len(frozen),'frozen_all_hashes_match':True,'scope':'named pre-R05 manifest paths, not an exhaustive assertion about every file on the entire disk','Word_SHA':{x['path']:sha(x['path']) for x in original if x['path'].endswith(('Draft_revised.docx','Appendix_revised.docx'))},'V_started':False,'W_started':False,'new_model_fits':0,'B1_MANIFEST':record(W/'baseline/B1_MANIFEST.json')})
    # LSOA material is present INSIDE the workbook, despite filename-only search yielding no standalone LSOA file.
    wb=read(Q/'checks/regional_workbook_extract.json');z=next(x for x in wb['extract'] if x['sheet']=='LSOA');rows=[]
    for row in z['selected_rows']:
        d={''.join(c for c in k if c.isalpha()):v for k,v in row}
        if d.get('C') in ['E07000004','E07000005','E07000006','E07000007']:rows.append({'LSOA11':d['A'],'LAD19':d['C'],'income_rate':float(d['H']),'population_mid2015_excluding_prisoners':float(d['K'])})
    lr=pd.DataFrame(rows);assert lr.LSOA11.is_unique;ls=lr.groupby('LAD19').agg(LSOA_n=('LSOA11','size'),missing_rate=('income_rate',lambda s:int(s.isna().sum())),missing_population=('population_mid2015_excluding_prisoners',lambda s:int(s.isna().sum())),nonpositive_population=('population_mid2015_excluding_prisoners',lambda s:int(s.le(0).sum()))).reset_index();table(Q/'tables/LSOA_MATERIAL_COMPLETENESS.csv',ls)
    put(Q/'checks/LSOA_material.json',{'LSOA_sheet_dimension':'A1:O32845','four_old_LAD_LSOA_rows':len(lr),'unique_LSOA_codes':lr.LSOA11.nunique(),'fields_checked':['2011 LSOA','2019 LAD','Income Score(rate)','mid2015 total population excluding prisoners'],'indicator_rebuilt':False,'Moran_rebuilt':False,'remaining':['compatible LSOA geometry','complete weights recipe','vintage and membership verification before dependent V fits'],'workbook':wb['file']})
    # Explicit T/L roadmap with shared-fit costs; design only, not a V run.
    vals=[
    ('T01','部分完成；仍必须','MR06/07/08/11/27/29; CL06; C06/C10; L01','区域定义、边界与Buck代理','工作簿LSOA底表及人口可用；旧4区proxy已核','先查边界/权重并重建指标→代理对照→输入变化清单；只重算受影响分析','V00共同区域输入冻结在依赖V拟合前；统一LSOA11/LAD19到目标边界','rate/gap/Moran差异、输入改变事件数、模型/贡献变化','材料检查0模型；如所有核心结果需新版，4 full+60 OOF；与V00新版共用，不重复计费','地区解释须在对照后定强度','作者已决定Buck重建；不是可选T12；几何和权重待补'),
    ('T02','部分完成；来源查证仍必须','MR01/02/05/27; CL01; C01; L02','时间代理和天气产品','UTC/小时/完整雨窗已核；历史product未定','找历史响应model元数据及适用字典；若确有输入错误，再派生重匹配与最小依赖重算','保留原时间/坐标/缓存身份；不可用当前默认产品替换','覆盖/缺失/值变化和小时差','先0拟合；实际输入变更才计受影响共用核心','限制ERA5、现场3秒与真实onset措辞','具体响应/官方导出字段定义'),
    ('T03','部分完成；阶段质量仍必须','MR02/03/04/21; CL01/06; C01/C09; L05','C/D、事件身份、阶段记录','原始比较135025、共同分母和并列规则已核','V01预声明缺最低stage1/边界异常的排除或分层；仍用冻结C/D','主/天气paired共同事件；不得按拟合效果改排除','保留率、形状、贡献、误差变化','每个约定敏感性场景最多复用4 full+60 folds；无需按每个MR重复拟合','只描述记录敏感性，不推断真实初始或调度','V00冻结最小场景与ID规则'),
    ('T04','仍必须','MR10/18/21; CL02/06; C03/C05; L04','长尾与形状敏感性','all_valid正式结果/原p99历史差异可用','V01固定少量尾部处理，训练内规则；共同未裁评价集对照','同fold、共同目标；测试尾部保留','paired ΔR²、曲线/导数支持、原尺度误差','与T03/V01共享场景拟合；正式60fold基准已在档案','若曲线依赖尾部则缩小形状主张','先区域输入与V00协议'),
    ('T05','部分完成；形状验证仍必须','MR18/19; CL02; L06','二次形状是否足够','已有cubic paired增量E .00193164/R .00049819；GLM仅full','V01先比较现有paired误差与支持；确需才加入预定线性/样条','同样本fold和训练内变换；不以显著性筛形式','paired loss、支持内导数、min有效率','已有档案0；新形式每主目标5fold+1full=12拟合/形式（两目标）；不默认新增','正二次项降为模型条件曲率；是否保留最低点由证据决定','作者/V00冻结形状问题与候选形式'),
    ('T06','仍必须','MR12/13/22; CL03; C02/C03; L07','贡献排序不确定性','12块配对OOF和分解已核','V02在共同独立分组下估计两条件增量及其差的不确定性','所有嵌套块/人口使用匹配分组与同次重采样；明确跨组支持','ΔG|K、ΔK|G、差的区间/稳定性','现有OOF重采样0拟合；它仅评价固定预测；若重做训练，与T07的12×K共用','未通过不得称稳定反转','V00确定过程/重采样单元和CI estimand'),
    ('T07','仍必须','MR14/16/20; CL03/04; C01/C05; L08','完整天气过程泛化','日期OOF、窗口UNIQUE_ANY和回顾期可用','V02定义整过程分组/相邻缓冲及所有事件归属，完整过程留出','先冻结过程边界；同一过程不能跨训练测试；共同块配对','过程外pooled/mean-group R²、误差、增量','12块×K外层训练，外加最终需要的4full；与T06/09复用，K由V00定','独立过程证据决定泛化叙述','不能只用7个命名窗口代替所有过程定义'),
    ('T08','条件执行','MR22/04; CL03/05; L03','故障初期可用性','K为最终聚合客户，两个比较非真值','仅作者选择初期用途时定义可获得字段并另建模型','不可把当前K泄漏进初期输入；同过程评价','初期信息缺失、误差和用途代价','未决定时0；启动后按所选目标/块×K估计','否则将全部K分析定为事后信息比较','作者需明确预测时点与用途'),
    ('T09','仍必须；规模受用途约束','MR17/23; CL05; C04/C07; L10','客户/小时尺度误差及校准','η/残差/expmeaneta可用，未校准','V03先从现有OOF给log与原尺度误差；若要均值预测则训练内学习回变换并过程外评估','与T07同预测分割；区分expη、C=expη−1和条件均值','MAE/RMSE/分位误差/校准和按支持范围分层','既有预测0拟合；有训练内校准时复用过程fold，不另跑整套','只能在误差支持的范围谈工程量级','V00先固定预测estimand，作者工程用途决定'),
    ('T10','条件执行','MR19/20; CL02; C08; L09','最低点不确定性','条件点及历史bootstrap，不是B1CI','V01形状成立且文字需位置主张时，V03用共用物理压力和每次自身尺度的重采样','记录不凸/无支持点失败率，不仅保留成功样本；与过程单元一致','有效最小点比例、物理分布/区间','B×需要的目标数拟合；B在V00精度/成本依据下定，不自动500','不成立则不报稳健最小点或区间','作者保留位置主张+形状门槛'),
    ('T11','实现大部完成；局部推断条件保留','MR11/18/20/25; CL02/04; C08/C09; L06/L09/L12','消费者与分期推断完整性','164档案、12图、8period及六非PSD已核','V00只在需要分期双向联合推断时预定有针对性的有效方法比较','禁止PSD裁剪/挑p；不为未用方向制造新检验','实际contrast方差与区间有效性','当前消费者0；可先复用scores/档案，不必重拟合','当前LADSE和点图可用，任意双向Wald不可用','限定未来真实要使用的对比'),
    ('T12','条件执行；当前无需扩展','MR24/29; CL06; L11','额外异质性','主/天气/六组合并既有描述','只有RQ和足够支持时才定义额外分组','不得从结果挑地区/组；Buck归T01必做','预定组差及不确定性','未决定0；启动后按组×块×fold计算','不新增泛化/机制主张','作者科学问题决定'),
    ('T13','当前无需扩展','MR04/22/23; CL01/05; L03/L05/L08','扩大目标','C与span定义已冻结；历史CML替代探索已记录','不默认加入CML/客户加权时长等新研究；如新增先取得合法定义','另建目标contract，不改现有C/D','新目标定义/可用性/误差','当前0；新任务另核成本','保持incident-conditioned范围','需明确新研究指令'),
    ('T14','候选已完成；W尚待执行','MR25/26/27; all CL; C04/C07/C09; L12','论文同步与最后验收','R05候选/963+迁移记录及12图，Word原SHA','V04综合证据定主张→作者决定章节→W00落实→W01全文/公式/引用/排版','单一当前结果身份；历史分开；对数单位和图注一致','CL/MR闭环、Word各位置/图OCR/公式对象检查','0模型；只重算被真实新错误影响的依赖','不将候选当已写入或论文可投','当前仅R05，V/W未启动')]
    columns=['T','status','MR_CL_C_L','scientific_question','existing_evidence','minimal_new_work','shared_constraints','metrics','cost_basis','writing_impact','prerequisites_decisions'];df=pd.DataFrame(vals,columns=columns);table(Q/'tables/REMAINING_VALIDATION.csv',df)
    validation='# R05 待补验证清单草案\n\nV/W均未启动。本清单是下一轮作者可审阅协议，不构成自动执行授权。区域输入依赖先冻结，再安排V拟合；Buck按作者既定决定必须重建并对照。\n\nV00：来源/LSOA边界权重、样本/训练内规则、过程分组、估计量与报告单位、最小场景、区间规则及用途。V01：形状、尾部、阶段质量。V02：配对贡献和完整过程。V03：工程误差/校准及有条件的最低点区间、初期信息任务。V04：统一证据与可写主张。\n\n成本以新增拟合次数而非没有测量依据的小时数估计；每场景最多4full+60fold，12块过程对照×K；共享同一组训练模型和预测，不按T/MR条目重复拟合。现有OOF上的重采样只反映固定预测的不确定性，不能冒充整训练流程的不确定性。\n\n'+md(df)+'\nLSOA材料完整性（仅盘点，没有重建地区指标）：\n\n'+md(ls)+f'\n四旧区共{len(lr)}个LSOA唯一键；工作簿有收入rate和2015人口字段。需验证年份/目标边界一致与完整权重配方，不能把简单平均Moran替代重建。\n'
    wtext(W/'REMAINING_VALIDATION.md',validation)
    figurecmp=pd.read_csv(Q/'tables/FIGURE_RELEASE_COMPARISON.csv');writingcheck=read(Q/'checks/writing_audit.json');ncan=writingcheck['candidates'];nmap=writingcheck['migration_rows']
    command='& .\\paper_revision_work_v2\\R03\\runtime\\python\\python.exe -I -S -B .\\paper_revision_work_v2\\R05\\cli.py render_release'
    write(Q/'CONSUMER_REPRODUCTION.md',f'# R05-5 最终消费者复现\n\n实际命令（工作目录项目根）：\n\n```powershell\n{command}\n& .\\paper_revision_work_v2\\R03\\runtime\\python\\python.exe -I -S -B .\\paper_revision_work_v2\\R05\\cli.py writing\n```\n\n12组图PNG/PDF已实际生成在R05/release_v1/figures；日志logs/render_release.txt，检查checks/consumer_reproduction.json。入口使用复制后的R04代码的明确绘图段：初始11→最终02/03/D1/F1→最终05/08→D1数值bin复核。截断点记录于CONSUMER_INPUTS.json；没有执行原代码拟合/全数据生产段。当前入口拒绝覆盖已存在release_v1；如需再次完整渲染应在派生副本中指定新发布目录并更新经审查的指针，不能单跑旧renderer充当新发布。\n\n图件当前身份在CURRENT_CONSUMER_RELEASE.json；源表快照位于release_v1/tables。语义绑定由writing命令逐值核查后发布到R05/tables/CURRENT_NUMERIC_BINDINGS_R05.csv、CURRENT_PARAGRAPH_BINDINGS_R05.csv及NUMERIC_BINDING_SEMANTIC_AUDIT.csv；旧表快照不是修正标签的权威。A-T10的10处six-group标签已纠正，数值未变。\n\n所有图消费相同冻结数组与参考定义；计数为整数精确比较，浮点预测/表值容差1e-12（协方差参考对照因不同线代路径用显式atol/rtol）。6个PNG与R04逐像素/字节相同；其余PNG因统一rcParams/布局执行顺序有差异，PDF元数据/版式不要求字节相同，不能把非同SHA归咎于仅时间戳。FIGURE_RELEASE_COMPARISON.csv逐文件区分字节身份和数据一致。\n\n已查看12图总览及D1单图，检查改变过的02/03/05/08/D1面板、图4四组与图10无区间；图1经纬度hexbin无许可边界和inset；图6地图有效范围；F1残差重尾明显。属于科学内容与可读性验收，不是最终期刊排版。图3密集窗口标签在总览较小，单图保留可放大。\n\n图4/6为exp(meanη)/exp(weighted meanη)，不等于mean(expη)或算术客户/小时均值。E对应1+C，未减1。图7为50点p1–p99网格max/min；图9两种预测身份、唯一4452事件及对数目标明确；图10单full分期点；D1各总体自己的数值bins，主/天气pooled均递减。图1的计数/坐标/边界缺项进入候选图注。运行标签保留供审阅，最终稿实现标签可移至复现说明。\n\n'+md(figurecmp[['figure','format','bytes','byte_identical_to_R04','pixel_equal']])+f'\n数字覆盖：950原槽位（含历史/引用/公式），246绑定逐值语义复核，{ncan}处候选位置，{nmap}行迁移表。11组合段落逐段候选；Word未修改；OCR与所有公式对象仍属W最终核查范围。\n')
    # Exact-candidate audit using copied skill tools; equivalent local ledger remains the authority.
    sys.path.insert(0,str(Q/'frozen/skill_audits'));from audit_candidate_text import audit_candidate
    from audit_manuscript_state import audit as state_audit
    profile={'terminology':[{'id':'score','preferred':'pooled OOF R²','prohibited':['causal variance shares are established']},{'id':'time','preferred':'earliest valid recorded start time','prohibited':['true initial customer counts were verified']},{'id':'span','preferred':'recorded restoration span','prohibited':['restoration span equals customer minutes lost']}],'style_profile':{'protected_terms':['pooled OOF','date-group','full-fit','reference','ln','CR1','LAD','customer','gust','covariance','stage','main','weather','R²','physical','conditional','period','model','population'],'stock_phrases':[]}}
    cands=read(Q/'tables/PARAGRAPH_CANDIDATES.json');a=[]
    for loc,c in cands.items():findings=audit_candidate(c['text'],loc,profile);a.append({'location':loc,'text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),'findings':findings,'manual_review':'candidate scoped to evidence; adjacent context included; repeated text at alternative locations is a merge option, not repeated insertion'})
    put(Q/'checks/candidate_skill_audit.json',{'profile':profile,'candidates':a,'candidate_file_sha256':sha(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md'),'no_Word_changes':True})
    # Current item-level status; all five dimensions explicit, no blanket completed label.
    detail={
    'MR01':('time chain verified','earliest-source and core identity checked','true onset unknown','source metadata','PROVENANCE_AUDIT.md'),
    'MR02':('UTC/tie rules verified','135025 earliest selections agree','time ties not initial truth','V01 stage quality','CUSTOMER_COMPARATOR_AUDIT.md'),
    'MR03':('frozen unresolved identity exclusion verified','B1 identities and n checked','cause/record semantics','V00 identity contract','PROVENANCE_AUDIT.md'),
    'MR04':('comparison selector hardened','main ratios1.973881/2.989070; common n60436','no true initial/CML interpretation','V01 record quality','CUSTOMER_COMPARATOR_AUDIT.md'),
    'MR05':('cache consumption verified','hour/UTC values inherited','historical product/3second/onset unknown','source audit before changed-input fits','PROVENANCE_AUDIT.md'),
    'MR06':('gap meaning corrected','stored0–1 within-LAD range','Buck proxy not reconstructed range','mandatory T01 rebuild','PROVENANCE_AUDIT.md'),
    'MR07':('Moran level clarified','published LAD values/proxy known','weights recipe unresolved','mandatory T01 geometry/weights','PROVENANCE_AUDIT.md'),
    'MR08':('proxy provenance verified','LSOA sheet found; four old-LAD material inventoried','merged indicator not rebuilt','author already decided rebuild and compare; V00 order','PROVENANCE_AUDIT.md'),
    'MR09':('consensus grouping verified','main/weather/six-pooled results identified','official code semantics incomplete','source verification; V01 support','PROVENANCE_AUDIT.md'),
    'MR10':('all_valid evaluation verified','60436/9857; tails retained','outcome tail quality/shape','V01 tail sensitivity','OOF_SCORE_AUDIT.md'),
    'MR11':('scaling/rank/covariance implementation verified','246 bindings; four VIFs; period physical coefficients','six period two-way nonPSD','only targeted future inference protocol','COVARIANCE_AND_PERIOD_AUDIT.md'),
    'MR12':('12 scores recomputed','weather R gap7.20255pp decomposed3.69109+3.51146','metrics differ; no selective switch','V02 process paired protocol','OOF_SCORE_AUDIT.md'),
    'MR13':('paired block differences verified','main/weather ordering differs; weather E positive','no stable cross-population reversal','V02 uncertainty and processes','OOF_SCORE_AUDIT.md'),
    'MR14':('same-date separation verified','formal OOF eta checked','multiday processes can cross folds','V02 complete process split','OOF_SCORE_AUDIT.md'),
    'MR15':('no double log in current consumer','figure09 rebuilt with log y and eta','not engineering raw-scale error','V03 error/calibration','CONSUMER_REPRODUCTION.md'),
    'MR16':('window identities deduplicated','25unique days/4452main events','date OOF not process OOF','V02 complete process grouping','CONSUMER_REPRODUCTION.md'),
    'MR17':('reference formulas and consumer verified','12figures new release; map111LAD','not arithmetic conditional means','V03 uses and source conditions','CONSUMER_REPRODUCTION.md'),
    'MR18':('archived supplements identified','cubic paired positive deltas; GLM full only','no robust/unique quadratic claim','V01 shape evidence','OOF_SCORE_AUDIT.md'),
    'MR19':('physical points/scales verified','10.807545 conditional main point','no current physical CI; old bootstrap historical','shape gate then optional physical bootstrap','COVARIANCE_AND_PERIOD_AUDIT.md'),
    'MR20':('8 full-rank period archive readbacks passed','unseen combination guard; LADSE/point figure','retrospective/nonPSD two-way restrictions','V00 only needed inference comparisons','COVARIANCE_AND_PERIOD_AUDIT.md'),
    'MR21':('numeric stage sort and bins checked','two current pooled curves decline; time ties quantified','no dispatch mechanism or sole composition cause','V01 stage-quality sensitivity','CUSTOMER_COMPARATOR_AUDIT.md'),
    'MR22':('K final-information timing declared','1.97/2.99 comparisons not initial model','no initial deployment claim','T08 only if author chooses early use','CUSTOMER_COMPARATOR_AUDIT.md'),
    'MR23':('reference diagnostics reproduced','residual F1 and archived factors available','not calibrated conditional means or engineering efficacy','V03','CONSUMER_REPRODUCTION.md'),
    'MR24':('fig06/07 retained and recreated','reference map/ratios bounded','no universal importance ranking','author may move to appendix; not delete automatically','MANUSCRIPT_REWRITE_CANDIDATES.md'),
    'MR25':('release entry and numeric semantics audited','950slots/246bindings;10labels corrected; all12figures','OCR/formula objects and Word sync outside R05','W after V04; current metadata counterpart authoritative','CONSUMER_REPRODUCTION.md'),
    'MR26':('chapter/paragraph mapping created',f'{ncan}candidate locations;11combination paragraphs','six-chapter structure only proposed','author structure decision after V synthesis','MANUSCRIPT_REWRITE_CANDIDATES.md'),
    'MR27':('source identities preserved','LSOA internal sheet confirmed; provenance table','official dictionary/product/citation particulars pending','source verification; W bibliography','PROVENANCE_AUDIT.md'),
    'MR28':('C10 numbering issue remains closed','scientific Buck issue tracked inMR08','closing code ID does not close source science','MR08 mandatory reconstruction','PROVENANCE_AUDIT.md'),
    'MR29':('regional links numerically usable','LAD21map111; LAD23 key compatibility known','boundary equivalence not established','T01 before dependent V fits','PROVENANCE_AUDIT.md')}
    current=read(M/'REVISION_ITEMS.json');claims=read(M/'CLAIM_STATUS_CURRENT.json');assert len(current['items'])==29 and len(claims['claims'])==6
    stage=M/'stage_snapshots/MR-v1.4-R04-review_before_R05_update';stage.mkdir(exist_ok=True)
    for name in ['REVISION_ITEMS.json','CLAIM_STATUS_CURRENT.json','MANUSCRIPT_LEDGER.md','SOURCE_MANIFEST.json']:shutil.copyfile(M/name,stage/name)
    itemrows=[]
    for item in current['items']:
        imp,num,lim,nxt,proof=detail[item['id']];snapshot={k:v for k,v in item.items() if k not in ['history','review_history']};item.setdefault('history',[]).append(snapshot)
        u={'implementation':imp,'current_numeric':num,'scientific_limit':lim,'next_condition_or_author_decision':nxt,'Word_status':'not_modified','evidence':'R05/'+proof,'timestamp':now}
        item.update(r05_update=u,checkpoint='R05_complete_conditional_for_V',word_status='尚未写入Word',evidence=num+'；证据R05/'+proof,action=nxt+'；逐段候选见R05/MANUSCRIPT_REWRITE_CANDIDATES.md',decision_status='实现/数值已核；科学条件与作者决定分别保留',release_condition=lim+'；'+nxt)
        itemrows.append({'MR':item['id'],'title':item['title'],**u})
    current.update(version='MR-v1.5-R05',checkpoint='R05_completed_V_W_not_started',updated_at=now);wsave(M/'REVISION_ITEMS.json',current);table(Q/'tables/MR_CURRENT_STATUS.csv',pd.DataFrame(itemrows))
    cdetails=[('CL01','C/D及记录比较可描述','字段真值、来源与记录完整性受限','MR01–10/21/27/29'),('CL02','正曲率/10.807545条件点可报告','三阶正增量；形状/位置不确定性未建立','MR11/18/19/20'),('CL03','组内配对点增量及指标分解可报告','排序稳定性/完整过程/初期用途未验证','MR12/13/14/22'),('CL04','25日/4452事件及回顾性period可描述','不能称未接触确认、整过程独立验证','MR14/15/16/20'),('CL05','expmeaneta参考曲线地图与网格比可报告','没有算术均值校准/工程效能','MR17/19/23/24'),('CL06','当前阶段pooled下降及区域proxy可描述','不识别调度机制；Buck重建必做','MR07/08/21/29')]
    for x,(cid,ok,limit,mrs) in zip(claims['claims'],cdetails):assert x['CL']==cid;x.setdefault('history',[]).append({k:v for k,v in x.items() if k!='history'});x.update(当前证据=ok,仍需条件=limit,R05结果={'MR':mrs,'status':'bounded_current_evidence','Word':'未修改'},checkpoint='R05_complete')
    claims['version']='MR-v1.5-R05';wsave(M/'CLAIM_STATUS_CURRENT.json',claims);wsave(M/'CLAIM_STATUS_R05.json',claims)
    ctable=pd.DataFrame(cdetails,columns=['CL','current_supported_scope','remaining_limit','MR']);table(Q/'tables/CL_CURRENT_STATUS.csv',ctable)
    impact=f'# R05_WRITING_IMPACT / MR-v1.5-R05\n\n仅生成候选，Word未修改；V/W未启动。\n\n主线：记录重构→条件关系→事后信息增量→适用范围。天气E负增量撤回；当前D1 pooled先升后降撤回；三阶有小幅正增量进入形状证据；1.97对应最低数字阶段、2.99对应最早时间，不称真实初始；图10改为单full物理系数点。当前12图全部复现。\n\n{ncan}处候选（若若干旧位置采用同一合并候选，不重复插入）；{nmap}行迁移表含950原数字槽；11组合段落完整。182/64绑定逐值/对象/单位检查，A-T10十个目标标签纠正。全部精确位置、上下文、MR/CL、证据行键与候选文字在R05/MANUSCRIPT_MIGRATION_MAP.csv。\n\n章节：现五章保持。六章为建议，第5讨论第6结论，待作者选择；图6/7保留，迁附录亦只建议。附录A改gap/Moran/来源，B记录选择，C合并六组全期对应，D中性标题与下降pooled，E历史不重写成验证，F当前CR1/残差及非PSD范围，G撤回负增量解释，H当前点与旧Bootstrap/分期/回变换分层。\n\n'+md(ctable)+'\n## 29项逐项状态\n\n'+md(pd.DataFrame(itemrows)[['MR','title','implementation','current_numeric','scientific_limit','next_condition_or_author_decision','Word_status']])+'\n\nBuck为既定必做，工作簿LSOA表已找到；未取得的边界和权重具体影响Moran等重建，先于依赖V模型。来源缺口不阻止已冻结当前分数的算术核对，也不能被算术通过关闭。\n\n作者待定仅：五/六章结构、图6/7位置、V00过程/用途协议，最低点主张是否保留到需新Bootstrap、是否另做初期模型及额外异质性。当前不要求再次决定是否重建Buck。\n'
    wtext(M/'R05_WRITING_IMPACT.md',impact);wtext(M/'MANUSCRIPT_LEDGER.md',(M/'MANUSCRIPT_LEDGER.md').read_text(encoding='utf-8')+'\n\n# R05当前检查点（优先于上方历史动作）\n\n'+impact)
    acceptance='# B1验收 / R05\n\n总状态：**conditional_for_V**。限定为可准备并经作者确认V00协议；不是启动V的授权，不是论文投稿结论。\n\n数据/生产链：冻结B1身份、381引用、64核心档案训练尺度与η、12块评分、8分期和所用消费者可追溯。本轮0核心/其他模型拟合，B1_MANIFEST不变，无新模型继任版本。C/D、fold、all_valid规则未改。\n\n消费者：12组PNG/PDF独立复现可用于科学审阅；原源码和Word不变。R05派生绑定修正10个A-T10目标标签；客户选择稳定源行规则明确且主数字不变。图1计数不等于密度、图4/6/7参考量、图9预测身份、图10点图、D1下降趋势均在候选中。\n\n当前可报告：限定人口的条件曲率/最低点、配对OOF分数与增量、描述性窗口/阶段/区域参考。尚不能采用：稳健U形或稳定阈值、稳定排序反转、独立完整过程验证、真实初始客户或调度用途、算术均值校准、区域/修复因果机制。六个非PSD分期双向矩阵禁用于未验证的任意方向/联合Wald；目前LAD SE和点图不受该项全面否定。\n\n进入V条件：V00先冻结Buck/来源输入前置次序、LSOA边界和空间权重、共同样本与过程分割、目标和区间估计量、最小敏感性场景及用途。Buck底表在现有workbook，必须重建并与代理对照；依赖新版输入的V拟合不得先跑后补。局部来源不确定不泛化为所有统计工作停工。\n\n范围证据：R05/checks/final_isolation.json、B1_FILE_AUDIT.csv、numerical_audit.json、writing_audit.json、CONSUMER_REPRODUCTION.md。完整问题与下一步见REMAINING_VALIDATION.md。\n'
    wtext(W/'baseline/B1_ACCEPTANCE.md',acceptance)
    report=f'# R05 项目复审报告\n\n结论：conditional_for_V，R05-0至R05-7完成；V/W未启动，Word未修改。本轮无核心数值变化、零模型重拟合，原B1身份保留。\n\n## F01–F06实际处置\n\nF01：8个分期再读，6个two-way非PSD与参考聚类实现一致。LAD+date−intersection/实际CR1因子核对通过；记录aᵀVa及AV Aᵀ，保留LAD SE和无区间图10，限制非PSD任意联合Wald。新增8个年/月分别见过但组合未见的拒绝检查通过；已见预测仅有浮点差，R05测试使用1e-12而非逐位相同，未改模型实现。\n\nF02：135025原始事件重建比较，earliest源行与R02完全一致，最小数字stage对R04主60436零值差。主最小stage ties0；earliest ties15249、客户冲突13266。主三口径共同n60436，C/minstage=1.973881，C/earliesttime=2.989070。全master C缺69而比较字段不缺，必须共同分母；细表返回。确定性比较生产者保存原行身份，未改C/D。\n\nF03：明确单渲染入口生成12最终组；图像/数据身份分表，最终派生绑定由writing入口发布，旧消费者不改变当前R05指针。六个PNG逐像素相同，其余样式差异不混称数值变更。\n\nF04：182cell+64paragraph数值逐一匹配，10个A-T10目标仍为six-group的元数据错误已在R05派生表纠正。950slots不等于950科学结论；{ncan}候选位置、{nmap}迁移记录、11完整组合段落和各章/附录职责齐备。旧开发期表建议整表更名为全期对应物或保留历史，未自动重跑。\n\nF05：12块评分再算通过。天气R0c pooled .2375707125、mean-fold .1655452058；7.20255067pp差距分为折内SST加权3.69109173pp、折间均值扩大分母3.51145894pp。两个统计量透明报告，不选分数较高者。\n\nF06：Buck旧简单平均proxy可追溯且继续保留。重要材料补充：冻结workbook内LSOA工作表有32844数据行，四旧区{len(lr)}个唯一LSOA及其rate/2015人口字段；已从“文件名未找到”推进为具体内部表盘点。尚缺匹配空间几何和完整权重/目标边界协议，不擅自展开地区重建。重建对照是作者既定必做，放在依赖V计算之前。\n\n## 原稿变化及适用范围\n\n天气E转为正增量、主客户比值口径消歧、恢复长尾均值改变、D1两总体pooled下降、三阶有正增量、分期不再混用CV汇总、12图数学量和预测身份明确。可写与待验证按6CL分开：\n\n'+md(ctable)+f'\n## 验收和隔离\n\n{len(original)}个原研究清单路径中{len(original)-len(exceptions)}个SHA一致；LOG.md另有已证实仅追加的例外，原前缀SHA完全相同，作者/进程未确定，未回退原日志（见original_log_exception.json及追加文本），{len(frozen)}个R02/R03/R04等冻结路径大小/SHA一致。不能将这个范围扩大为整块磁盘所有文件均审计。文稿候选仅在R05和台账；最新台账MR-v1.5-R05保留29MR/6CL来源/历史/作者决定。\n\n下一步V00需要确定来源前置、过程分组、共用样本/尺度、形状与尾部场景、paired不确定性、工程estimand及最小成本。五/六章、图6/7位置、初期用途、条件Bootstrap仍待作者决定。本轮在R05交付后停止。\n\nFUNCTIONAL-COMPLETENESS RETROSPECTIVE：覆盖接收/完整档案核对/数值/协方差/客户/消费者/候选/台账/待补协议。来源未知和科学验证保留开放，无科学豁免；Word最终排版/OCR/引用与V实验不在本轮完成范围。验收只针对进入V协议准备的条件，不是整篇论文最终通过。\n'
    wtext(W/'reports/R05_PROJECT_REVIEW.md',report)
    # Audit sidecar maps the existing ledger; it is not a replacement project database.
    state={'project':{'authority':'manuscript_record/REVISION_ITEMS.json','scope':'R05 candidates; paper not submission-ready'},'artifacts':[{'id':'candidate','path':'R05/MANUSCRIPT_REWRITE_CANDIDATES.md','status':'ACTIVE','role':'review_candidate','required_for_release':True}],'authority_sources':[{'id':'B1','status':'VERIFIED','path':'baseline/B1_MANIFEST.json'}],'contract':{'questions':[{'id':x} for x in ['RQ1','RQ2','RQ3']]},'alignment':[{'question_id':x,'method':me,'evidence':ev,'result':re,'interpretation':it,'limitation':li,'contribution':ct} for x,me,ev,re,it,li,ct in [('RQ1','quadratic/cubic/period','conditional minima and cubic paired OOF','conditional positive curvature','model-specific shape','V01/CI pending','bounded incident-conditioned association'),('RQ2','paired blocks','12OOF blocks','conditional point ordering differs','retrospective information','paired uncertainty/process pending','population-specific comparison'),('RQ3','period/window/source scope','8period/12fig/source inventory','scope constrained','no engineering deployment proof','V02/V03/source pending','applicability limits')]],'issues':[{'id':i,'severity':'S3','status':'OPEN','evidence_status':'CONFIRMED','description':desc} for i,desc in [('SOURCE','regional reconstruction / source conditions before dependent validation'),('SHAPE','stable shape/minimum not validated'),('CONTRIBUTION','ordering uncertainty and process validation absent'),('ENGINEERING','engineering calibration absent'),('WORD','Word/citation/layout not yet updated')]],'release':{'status':'R05_CONDITIONAL_FOR_V','candidate_artifact_ids':['candidate'],'checked_hashes':{'candidate':sha(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md')},'required_checks':['R05_numeric','R05_candidate','W_final'],'completed_checks':['R05_numeric','R05_candidate'],'visual_check':'PASSED'},**profile}
    put(Q/'checks/manuscript_state_adapter.json',state);findings=state_audit(state,W);put(Q/'checks/manuscript_state_skill_audit.json',{'findings':findings,'interpretation':'Expected manuscript-release S3 blockers retained; these are not execution errors or a blanket block on V00 protocol preparation. Existing MR/CL remain the authority.'})
    # New small evidence sources are copied, hashed and attached without replacing any prior source.
    source=read(M/'SOURCE_MANIFEST.json');maxid=max(int(r['source_id'][3:]) for r in source['sources'] if r['source_id'].startswith('SRC'))
    new_sources=[W/'reports/R05_PROJECT_REVIEW.md',Q/'PROVENANCE_AUDIT.md',Q/'OOF_SCORE_AUDIT.md',Q/'COVARIANCE_AND_PERIOD_AUDIT.md',Q/'CUSTOMER_COMPARATOR_AUDIT.md',Q/'CONSUMER_REPRODUCTION.md',Q/'MANUSCRIPT_MIGRATION_MAP.csv',Q/'MANUSCRIPT_REWRITE_CANDIDATES.md',W/'REMAINING_VALIDATION.md',Q/'tables/NUMERIC_BINDING_SEMANTIC_AUDIT.csv',Q/'checks/regional_workbook_extract.json']
    source_map={}
    for n,p in enumerate(new_sources,maxid+1):sid=f'SRC{n:02}';dest=M/'evidence'/f'{sid}_R05_{p.name}';shutil.copyfile(p,dest);source['sources'].append({'source_id':sid,'original_name':p.name,'path':dest.relative_to(M).as_posix(),'role':'R05 local audit/candidate; same-run evidence, not independent experiment','size_bytes':dest.stat().st_size,'sha256':sha(dest)});source_map[sid]=str(p)
    source.update(checkpoint='R05_completed_V_W_not_started',date=now);wsave(M/'SOURCE_MANIFEST.json',source);wsave(M/'R05_SOURCE_MAP.json',source_map)
    wtext(M/'CHANGELOG.md',(M/'CHANGELOG.md').read_text(encoding='utf-8')+f'\n\n## {now} MR-v1.5-R05\n完成R05；29MR/6CL逐项状态和{len(new_sources)}个新来源；保留MR-v1.4审阅与此前历史。零模型重拟合/Word修改，10个A-T10元数据标签修正，LSOA底表定位，条件进入V协议准备，未启动V/W。\n')
    wtext(M/'START_HERE.md',(M/'START_HERE.md').read_text(encoding='utf-8')+'\n\n## 当前优先入口：MR-v1.5-R05\n读取R05_WRITING_IMPACT.md、CLAIM_STATUS_CURRENT.json、REVISION_ITEMS.json的r05_update；上方“待R05”属历史。下一步只在收到作者指令后进入V00；Buck重建既定，先冻结来源依赖。\n')
    runstate=read(W/'RUN_STATE.json');runstate.update(active_stage='R05',last_updated=now,baseline='R04_B1_all_valid_v1 unchanged; R05 completed conditional_for_V; V/W not started');runstate['stages']['R05']={'execution_status':'completed','acceptance':'conditional_for_V','report':'reports/R05_PROJECT_REVIEW.md','new_fits':0,'Word_modified':False};wsave(W/'RUN_STATE.json',runstate)
    wtext(W/'STATUS.md','# 当前状态\n\nR00–R05完成；R05验收conditional_for_V。V00–V04及W00–W01未启动。B1模型身份保持R04_B1_all_valid_v1；最新台账MR-v1.5-R05。\n')
    wtext(W/'RETURN_TO_CHATGPT.md',f'# R05返回摘要\n\nR05-0至R05-7已执行；conditional_for_V；0模型重拟合，Word、原代码与冻结阶段SHA一致；原LOG.md出现仅追加例外，原前缀SHA一致，写入进程未确定，未回退，V/W未启动。\n\n入口：reports/R05_PROJECT_REVIEW.md → baseline/B1_ACCEPTANCE.md → R05各专项报告 → manuscript_record/R05_WRITING_IMPACT.md → REMAINING_VALIDATION.md。完整最新台账MR-v1.5-R05已含审阅增量/来源/29MR/6CL历史。\n\n重点：六个分期非PSD为当前估计量条件，LAD SE与点图可用；客户1.973881为最低stage、2.989070为最早time，ties限制明确；12最终图复现；246绑定逐值审计，A-T10十个语义标签修正；{ncan}候选位置、11完整组合段落；天气R²差7.20255pp恒等分解；LSOA底表实际在workbook且四旧区{len(lr)}行，后续必做重建仍需边界/权重。\n\n大档案在LARGE_LOCAL_FILES.json列位置/大小/SHA，回包含小统计及完整manuscript_record。包清单为相对路径，不含清单自身以避免自哈希循环。来源证据是同次执行，不重复计为独立验证。原Word存在于完整台账历史证据中但字节未变。收到下一步指令前停止。\n')
    # Full ledger verification, including all historical sources and new evidence.
    for s in source['sources']:
        p=M/s['path'];assert p.exists() and p.stat().st_size==s['size_bytes'] and sha(p)==s['sha256'],s['source_id']
    assert {x['id'] for x in current['items']}=={f'MR{i:02}' for i in range(1,30)};assert {x['CL'] for x in claims['claims']}=={f'CL{i:02}' for i in range(1,7)}
    before=read(stage/'REVISION_ITEMS.json');assert all(len(a['history'])>=len(b.get('history',[]))+1 for a,b in zip(current['items'],before['items']))
    bundle={'version':'MR-v1.5-R05','files':[{'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(M.rglob('*')) if p.is_file() and p.name!='BUNDLE_MANIFEST.json']};wsave(M/'BUNDLE_MANIFEST.json',bundle)
    put(Q/'checks/ledger_acceptance.json',{'MR':29,'CL':6,'sources_verified':len(source['sources']),'history_continuity':True,'author_Buck_decision_retained':True,'structure_not_approved':True,'new_version':'MR-v1.5-R05'})
    large=[record(Q/'data/customer_comparators_v1.parquet')]+[r for r in read(W/'baseline/B1_MANIFEST.json')['outputs'] if r['bytes']>=220000];put(Q/'LARGE_LOCAL_FILES.json',{'reason':'large event/model archives remain local, size/hash/path supplied; runtimes reused from frozen R03/R04','files':large,'runtime_source':record(R4/'checks/runtime_paths.json')})
    # Package full latest ledger + small evidence, final figures, copied execution code. No giant runtimes/raw archives.
    files=set()
    for folder in [M,Q/'src',Q/'tables',Q/'checks',Q/'logs',Q/'evidence_data',Q/'release_v1/figures',Q/'release_v1/tables',Q/'frozen/R03_src',Q/'frozen/R04_src',Q/'frozen/source_audit',Q/'frozen/skill_audits']:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not any(x.startswith('archive_before') for x in p.parts):files.add(p)
    files.update(p for p in Q.glob('*') if p.is_file());files.update([W/'REMAINING_VALIDATION.md',W/'baseline/B1_ACCEPTANCE.md',W/'baseline/B1_MANIFEST.json',W/'reports/R05_PROJECT_REVIEW.md',W/'RETURN_TO_CHATGPT.md',W/'DECISIONS.md',W/'RUN_STATE.json',W/'STATUS.md',Q/'release_v1/CONSUMER_INPUTS.json'])
    for folder in [W/'contracts',W/'R03/configs']:
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in ['.md','.json','.csv']:files.add(p)
    manifest={'root':'paper_revision_work_v2','stage':'R05','files':[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)],'excludes':'large local files and runtimes; manifest itself excluded; original evidence Word/ZIP copies inside complete ledger retained unchanged'}
    package=W/'RETURN_PACKAGE_R05.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,p.relative_to(W).as_posix())
        z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(package) as z:
        names=set(z.namelist());assert len(names)==len(files)+1
        for r in manifest['files']:raw=z.read(r['path']);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],r['path']
    # Post-package result intentionally outside ZIP, avoiding self-referential hash claims.
    put(Q/'checks/return_package_validation.json',{'passed':True,'files_verified':len(files),'zip':record(package),'manifest_relative_paths':True,'full_ledger_included':True,'stage':'R05','no_V_W':True})
    wsave(W/'ARTIFACT_MANIFEST.json',{'timestamp_utc':now,'stage':'R05','prior_manifest':'R05/archive/ARTIFACT_MANIFEST_before.json','new_or_updated_files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)],'package':record(package),'frozen_checks':record(Q/'checks/final_isolation.json')})
    print(json.dumps({'package':record(package),'file_count':len(files),'ledger_sources':len(source['sources']),'R05_complete':True,'acceptance':'conditional_for_V','candidate_findings':sum(len(x['findings']) for x in a)},ensure_ascii=False),flush=True)
if __name__=='__main__':run()

