"""Finalize R03 state, evidence manifests, ledger snapshot and small return archive."""
import json,hashlib,shutil,datetime,difflib,zipfile,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R03';M=W/'manuscript_record'
sys.path.insert(0,str(W/'code'))
from r03_isolation_check import audit
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
smoke=read(Q/'smoke/R03_smoke_v4/RUN_MANIFEST.json');assert not smoke['formal_B1']
assert read(Q/'checks/test_summary.json')=={'passed':True,'tests':17,'errors':0,'failures':0}
codefiles=[Q/'cli.py',*sorted((Q/'src').glob('*.py'))]
identity=hashlib.sha256(json.dumps({p.relative_to(Q).as_posix():sha(p) for p in codefiles},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert identity==smoke['code_identity']==read(Q/'configs/R04_primary.json')['code_identity']==read(Q/'configs/R04_optional_p99.json')['code_identity']
code_manifest={'version':'R03_production_v1','code_identity':identity,'files':[{'path':p.relative_to(Q).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'change':'new_independent_implementation'} for p in codefiles],'source_references':'frozen/PROJECT_SOURCE_MANIFEST.json','runtime':'frozen/RUNTIME_MANIFEST.json','dependencies_are_copies':True}
save(Q/'CODE_MANIFEST.json',code_manifest)
patch=[]
for p in codefiles:patch.extend(difflib.unified_diff([],p.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile='b/paper_revision_work_v2/R03/'+p.relative_to(Q).as_posix()))
(Q/'code_changes').mkdir(exist_ok=True);(Q/'code_changes/new_production.patch').write_text(''.join(patch),encoding='utf-8')
save(Q/'frozen/EVIDENCE_MANIFEST.json',{'files':[{'path':p.relative_to(Q).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for sub in ['evidence','contracts'] for p in sorted((Q/'frozen'/sub).rglob('*')) if p.is_file()]})
st=read(W/'RUN_STATE.json');st.update(last_updated=now,active_stage='R03',baseline='H0 historical preserved; R02 frozen input; R03 isolated code/tests/smoke completed; formal B1/V/W not run',revision_entry=str(Q/'cli.py'))
st['stages']['R03'].update(execution_status='completed',report='reports/R03_report.md',inputs=['R03/frozen/evidence/SRC11_R03_instruction.txt','R02/data/EVENT_MANIFEST.json','paper_manuscript_record/'],outputs=['R03/','manuscript_record/','reports/R03_report.md','tables/R03_INPUT_ACCEPTANCE.md','code/PRODUCTION_CHANGELOG.md'],blockers=[],models_reestimated=False,small_fits_only=True,latest_smoke='R03_smoke_v4',tests_passed=17,ledger_version='MR-v1.2-R03',isolated_blocked_products=['figure10 later: rank deficient calendar encoding','final figure/table rendering and six-cause/GLM/cubic branches not generated'],original_log_observation='original bytes exact prefix preserved; concurrent append is not R03 evidence')
st['stages']['R04']['execution_status']='not_started';st['stages']['R04']['readiness']='R03/R04_READINESS.md';save(W/'RUN_STATE.json',st)
(W/'STATUS.md').write_text('# 当前状态\n\nR03 completed：独立生产接口/定向输入核对/17测试/720事件smoke/MR-v1.2-R03台账完成。R04/V/W not_started；没有正式B1或Word修改。\n\n图10后期日历编码秩亏已隔离；其余未生成图表分支见R03/R04_READINESS.md。原代码、输入与Word哈希保持；原LOG同期追加3916字节，旧内容精确保留，详情见R03/checks/final_isolation.json。\n',encoding='utf-8')
dec=W/'DECISIONS.md';txt=dec.read_text(encoding='utf-8')
if '## D11：R03验收' not in txt:
    txt+='\n## D11：R03验收与后续分支\n\n主配置沿用R01的all_valid，不据smoke分数选p99；备选主训练恢复p99只作为显式可选配置。日期共同fold/预处理/评分/η/参考/归档已实现并检查，R04尚未执行。图10后期完整候选年月编码秩亏，实施处置为单独blocked，不自动删项；等价满秩参数基须在后续明确记录验证，或暂不生成该图。最终渲染/六组/GLM/三阶未迁移分支另列，旧结果不回填。\n\n## D12：MR-v1.1补充接收与原LOG观察\n\n用户提供paper_manuscript_record，原包校验后复制合并至manuscript_record的MR-v1.2-R03，原29项/历史/来源/Word索引保留。原LOG在R03期间追加3916字节C01修复记录，旧185444字节完全不变；写入者未确定，不回滚，不把其拟合叙述算作R03/B1。原源码/数据/Word均通过哈希，R03继续只用冻结依赖。\n'
    dec.write_text(txt,encoding='utf-8')
issues=read(W/'issue_ledger.json')
for it in issues:
    if it['id'] in ['C02','C03','C04','C05','C06','C07','C08','C09']:
        it.setdefault('history',[]).append({k:v for k,v in it.items() if k!='history'})
        it.update(execution_status='completed',execution_scope='R03 independent code and targeted/smoke checks only; formal models not reestimated',repair_status='targeted_checks_passed_with_isolated_products',evidence_source='R03_local_execution',evidence='R03/CONTRACTS.md; R03/checks/test_summary.json; R03/smoke/R03_smoke_v4/RUN_MANIFEST.json; R03/PRODUCER_CONSUMER_MAP.md; R03/checks/final_isolation.json',remaining='R04正式产物/渲染、V科学证据；图10后期参数基阻断及未迁移分支见R03/R04_READINESS.md',models_reestimated=False)
    if it['id']=='C01':it['revision_entry']=str(Q/'cli.py');it['remaining']='R03输入消费已通过；R04正式模型、真实onset/业务日历及两ID身份仍待'
save(W/'issue_ledger.json',issues)
im=['# 问题台账｜R03当前状态','','代码项 completed 仅限其execution_scope，不是科学主张关闭。旧状态在R03/archive及各项history保留；MR/CL写作台账另见manuscript_record。','','|ID|标题|执行状态|范围/证据|仍需处理|','|---|---|---|---|---|']
for it in issues:im.append('| '+' | '.join([it['id'],it['title'],it['execution_status'],it.get('execution_scope',''),it.get('remaining','')]).replace('\n',' ')+' |')
(W/'ISSUE_LEDGER.md').write_text('\n'.join(im)+'\n',encoding='utf-8')
ret='''# R03 返回摘要｜2026-09-05

仅R03完成：独立生产代码、定向输入对账、17项检查、720事件smoke及MR-v1.2-R03台账已交付。正式四模型/OOF全集、B1、V、Bootstrap、Word修改均未执行。完整报告 reports/R03_report.md；小型包 R03/R03_RETURN_PACKAGE.zip。

## 真实入口、输入与独立性

R03/cli.py→src/run_pipeline.py→producer.step0_build_sample；step2_build_folds已在接收阶段生成共同日期映射，实际运行按SHA读取。原v9/R02阻断入口不改、不导入。输入R02_input_20260905，表内R02_20260905，135025唯一事件；主表SHA 8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d。缺文件/错SHA/错版本即失败，无H0回退。

全部94份项目源代码依赖/引用已复制；复制Python/第三方库7711文件，7份本地参考数据；运行Python模块路径全部位于R03。当前代码身份859a02e917d71b4b51333b4db452403a97f1e6c479b6faf654d79f988c553846。最新smoke_v4为720事件/536日期/110 LAD，主E/R设计26/28列满秩；30 OOF+2全拟合+2阶段+2开发期小拟合，全部non_inferential_smoke。24个完整候选/折设计检查未做拟合。

原代码、原始CSV、v3、R02主表/manifest与Word均哈希不变。549份受保护文件中548完整不变；原LOG同期追加3916字节“C01专项修复”，旧185444字节精确保留，具体写入者未确定。R03未写该路径、未回滚、未使用其声称的拟合；详细证据在R03/checks/final_isolation.json。不能称全部549字节不变。

## 602/99、时间、天气和区域

候选主E/R各60436，天气E/R各9857。主R新增602、天气R新增99按固定顺序天气→人口→原因→目标→旧截尾→其他互斥归因，全部为旧H0尾部限制取消；其他各0。时间/天气改变可重叠标志主各85、天气各14，不是新增人数。R1_compat主59832/天气9758仅成员诊断，无新模型。

UTC/London日期/研究窗/时期差异全事件1845/2/2，主768/0/0、天气105/0/0；七窗口UNIQUE_ANY为7300/7298，对称差6，702重叠事件，窗口人数相加8002。源时区未确证，UTC是冻结分析解释；各窗口起止/端点/人数见tables/R03_INPUT_ACCEPTANCE.md。

天气不可查询5611事件，缺文件8236，完整且缓存窗通过121178，可读无效实际0；可查询129414事件→82621键/122948键小时/74896所需现存文件，缺文件7725键，目录75983文件。四候选v3-only实数0。复用R02全量扫描，未重抓天气；历史model/gust语义/响应单位metadata仍未知。

113个LAD21非空码均在人口LAD23键中，候选111码；113码边界等价均缺明确证据。已证实实际错配数量未提供，不填0。缺LAD5762/其中可用坐标151未变。Buck源表/列/代码SHA已登记，.06325/.1875/.30代理和主各1151/天气各293保留；合并区LSOA真值未重建。

## 共同规则与生产修复

1096日期一次生成5折，主/天气共用；fold SHA4493523c51e67cc22e5a2636d0e4dc867861c8b2f427f64989015607ed15d876。主all_valid已由R01明确；可选main_train_p99以每折主恢复有效训练总体估计linear .99、<=，再取天气子集。测试长尾全保留。主方案没有尚待选择的尾部规则；是否运行备选以后另指令。

天气/恢复客户训练ddof1标准化、区域原尺度/人口log、年月加性编码、未知类别报错；同组嵌套成员/预处理/评分配对。pooled与mean-fold分开，SSE/SST/n和负分/常量状态明确。η直接对照ln(1+C)/ln(D)，η=0不再变ln2；原变量场景生成一致平方/交互，三个平均/反变换量分开。风暴逐行训练/OOF/尾部/版本身份保存，未冒充真正过程留出。归档前后预测完全相同。

step26 VIF、27阶段收尾、28聚类已按可核实定义最小重建；旧step21写出的step26_full_summary是gust/cause诊断，不是VIF。新VIF含年月全设计，与旧列集合不同。图4/6/7/9从指定新归档产生数据，无新结果时停止，无旧区间回填。所有最终图形渲染仍未生成，六组/GLM/三阶等未迁移分支保留待办。

图10新阻断：later完整12113事件E rank18/19、R20/21，年份2024与Jan–Mar月份组合精确共线；现有编码不能唯一归档全部参数。已隔离后期行，不默删变量/拼旧结果/用重叠CV独立区间。最小下一动作是记录并验证等价满秩日历基，或保持图10暂不生成。全时期核心设计通过，不受此分支影响。

## 台账与下一阶段

用户提供MR-v1.1原包已校验并复制合并至manuscript_record；29个MR、CL01–06、原历史/来源/MR-v1.0快照和Word索引全部保留，原解压包未改。当前MR-v1.2-R03逐项保存证据→判断→定位→具体修改→CL→条件→尚未写入Word；SRC12–23分开记录报告/规则/测试/smoke/矩阵/保护证据，旧SRC02/09/10/11不覆盖。

数据§2/附录A/B补已核身份、分母、日历和来源限制；方法§3/附录E/F/H推进到已实现规则；结果§4不填smoke，图10后期新增阻断。摘要/引言/结论仍以事件后果重构、可比统计评价、工程解释推进；最低点/排序/过程/量级/机制仍待R04/V裁决，不因测试通过关闭CL。

R04核心入口和configs/R04_primary.json可供下一步执行；本轮未开始。具体命令、各保留产物与隔离项见R03/R04_READINESS.md。当前台账已完整合并，无MR缺件阻断；图10后期、最终图表渲染及未迁移附录分支单列。
'''
(W/'RETURN_TO_CHATGPT.md').write_text(ret,encoding='utf-8')
# Recheck after state updates, then freeze the final evidence copy in the ledger.
isolation=audit()
src=read(M/'SOURCE_MANIFEST.json')
for row in src['sources']:
    if row['source_id']=='SRC19':
        dest=M/row['path'];shutil.copyfile(Q/'checks/final_isolation.json',dest);row.update(size_bytes=dest.stat().st_size,sha256=sha(dest))
save(M/'SOURCE_MANIFEST.json',src)
md=M/'MANUSCRIPT_LEDGER.md';mt=md.read_text(encoding='utf-8')
if '## 11. R03新增来源索引' not in mt:
    mt+='\n## 11. R03新增来源索引\n\n|ID|文件|类型|SHA256|\n|---|---|---|---|\n'
    for row in src['sources']:
        if row['source_id'].startswith('SRC') and int(row['source_id'][3:])>=12:mt+=f"|{row['source_id']}|[{Path(row['path']).name}]({row['path']})|{row['role']}|{row['sha256']}|\n"
    md.write_text(mt,encoding='utf-8')
snap=M/'stage_snapshots/R03_completed_MR-v1.2-R03';snap.mkdir(exist_ok=True)
for name in ['START_HERE.md','MANUSCRIPT_LEDGER.md','REVISION_ITEMS.json','SOURCE_MANIFEST.json','CHANGELOG.md','R03_WRITING_IMPACT.md','R03_DELTA.json']:shutil.copyfile(M/name,snap/name)
def manifest(root,excluded):return [{'path':p.relative_to(root).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file() and p not in excluded]
save(M/'BUNDLE_MANIFEST.json',{'version':'MR-v1.2-R03','checkpoint':'R03_completed_before_R04','self_excluded':True,'files':manifest(M,{M/'BUNDLE_MANIFEST.json'})})
# Validate all inherited evidence/history and untouched user bundle before packaging.
intake=read(Q/'checks/MR_intake.json');assert all(sha(Path(intake['source_root'])/x['path'])==x['sha256'] for x in intake['preserved_input_files'])
old=read(W/'paper_manuscript_record/REVISION_ITEMS.json')['items'];new=read(M/'REVISION_ITEMS.json')['items']
assert [x['id'] for x in old]==[x['id'] for x in new]
assert [x['title'] for x in old]==[x['title'] for x in new]
for a,b in zip(old,new):
    assert b['history'][:-1]==a.get('history',[])
    assert b['history'][-1]=={k:v for k,v in a.items() if k!='history'}
    assert b['word_status']=='尚未写入Word'
assert all(sha(M/x['path'])==x['sha256'] for x in src['sources'])
save(Q/'checks/MR_merge_validation.json',{'passed':True,'items':29,'original_ids_titles_history_preserved':True,'all_word_unmodified':True,'sources':len(src['sources']),'user_bundle_unchanged':True,'old_stage_snapshots_preserved':True,'new_snapshot':str(snap),'formal_B1':False})
save(Q/'RUN_LEDGER.json',{'latest_successful_run':'R03_smoke_v4','code_identity':identity,'runs':[{'run_id':'R03_smoke_v1','status':'success_initial_interfaces'},{'run_id':'R03_smoke_v2','status':'failed_calendar_rank; partial_outputs_do_not_use'},{'run_id':'R03_smoke_v3','status':'success_with_isolated_period_branch'},{'run_id':'R03_smoke_v4','status':'release_success_with_isolated_period_branch'}],'all_purposes':'non_inferential_smoke','formal_runs':0,'bootstrap_runs':0,'Word_modified':False})
# Small review bundle: all ledger/history/evidence, current source and readable checks; no raw data or runtime binaries.
files={W/'RETURN_TO_CHATGPT.md',W/'reports/R03_report.md',W/'tables/R03_INPUT_ACCEPTANCE.md',W/'code/PRODUCTION_CHANGELOG.md',W/'RUN_STATE.json',W/'STATUS.md',W/'DECISIONS.md',W/'ISSUE_LEDGER.md',W/'issue_ledger.json'}
for sub in [M,Q/'src',Q/'configs',Q/'checks',Q/'code_changes']:
    files.update(p for p in sub.rglob('*') if p.is_file() and p.suffix!='.bin')
files.update(p for p in Q.glob('*.md'));files.update(p for p in Q.glob('*.json'))
files.update([Q/'cli.py',Q/'folds/date_to_fold.csv',Q/'logs/tests_release.txt',Q/'logs/smoke_v4.txt',Q/'smoke/R03_smoke_v4/RUN_MANIFEST.json'])
files.update(p for p in (Q/'frozen').glob('*MANIFEST.json'))
files.update(p for p in (Q/'acceptance').glob('*') if p.is_file() and p.stat().st_size<1000000)
files.update(p for p in (W/'code').glob('r03_*.py'))
files=sorted(files)
package_manifest={'run_id':'R03_release_20260905','contains_full_ledger':True,'excluded':'large raw data, event master, runtime binaries, full OOF/model arrays; identities and local paths retained','files':[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
zpath=Q/'R03_RETURN_PACKAGE.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(W).as_posix())
    z.writestr('PACKAGE_MANIFEST.json',json.dumps(package_manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    for row in package_manifest['files']:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
save(Q/'checks/return_package_verification.json',{'passed':True,'files':len(files),'bytes':zpath.stat().st_size,'sha256':sha(zpath),'includes_latest_ledger':True})
allfiles=manifest(W,{W/'ARTIFACT_MANIFEST.json'})
save(W/'ARTIFACT_MANIFEST.json',{'run_id':'R03_release_20260905','timestamp_utc':now,'root':str(W),'self_excluded':True,'files':[{'path':str(W/x['path']),'relative_path':x['path'],'bytes':x['size_bytes'],'sha256':x['sha256'],'role':'revision_and_retained_history'} for x in allfiles]})
assert all(sha(W/x['path'])==x['sha256'] for x in allfiles)
print(json.dumps({'R03':'completed','ledger':'MR-v1.2-R03','tests':17,'smoke':smoke['run_id'],'code_identity':identity,'protected_originals_byte_identical':isolation['protected_original_files_byte_identical'],'observed_LOG_append_bytes':isolation['observed_original_changes'][0]['appended_bytes'],'R04':'not_started','package':str(zpath),'package_bytes':zpath.stat().st_size,'package_files':len(files),'work_manifest_files_verified':len(allfiles)},ensure_ascii=False))
