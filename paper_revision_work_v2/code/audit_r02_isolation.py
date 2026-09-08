"""Audit and isolate R02 without executing historical producers or fitting models."""
import sys,json,hashlib,shutil,datetime,ast,io,unittest,importlib.util,os
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;A=O/'R02_isolation_audit';Q=O/'R02'
OLD=R/'scripts/v3_validation/v3_validation_pipeline.py'
NEW=R/'scripts/event_input_repair/r02_input_pipeline.py'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def prepare():
    assert not A.exists(),'Isolation preflight is single-use; do not overwrite audit history'
    previous=read(O/'ARTIFACT_MANIFEST.json')
    bad=[x['path'] for x in previous['files'] if sha(x['path'])!=x['sha256']]
    assert not bad,bad
    sources=read(O/'inventory/source_snapshots.json');src=next(x for x in sources if Path(x['source'])==OLD)
    assert sha(src['snapshot'])==src['sha256']
    current=read(Q/'checks/active_entry.json');assert sha(OLD)==current['sha256'],'Original entry has concurrent changes; do not overwrite'
    protected=read(O/'checks/protected_files_start.json');diff=[p for p,h in protected.items() if sha(p)!=h]
    assert set(map(Path,diff))=={OLD},diff
    source_diff=[x['source'] for x in sources if sha(x['source'])!=x['sha256']]
    assert set(map(Path,source_diff))=={OLD},source_diff
    A.mkdir();(A/'before').mkdir()
    for relative in ['ARTIFACT_MANIFEST.json','RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','RETURN_TO_CHATGPT.md','reports/R02_report.md','R02/REPRODUCE.md','code/check_r02.py','code/close_r02.py']:
        target=A/'before'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/relative,target)
    shutil.copyfile(OLD,A/'before/v3_validation_pipeline_R02_patched.py')
    save(A/'preflight.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_artifact_files_verified':len(previous['files']),'protected_files':len(protected),'modified_old_files':diff,'source_snapshot_count':len(sources),'modified_snapshot_sources':source_diff,'old_entry_H0_sha256':src['sha256'],'old_entry_R02_sha256':current['sha256'],'restoration_snapshot':src['snapshot'],'user_direction':'审查所有工作；基于原有工作另起炉灶，不破坏原有代码'})
    print('Preflight: prior artifacts intact; only historical v9 entry differs',flush=True)
def restore():
    before=read(A/'preflight.json');assert sha(OLD)==before['old_entry_R02_sha256']
    snapshot=Path(before['restoration_snapshot']);assert sha(snapshot)==before['old_entry_H0_sha256']
    assert NEW.exists();ast.parse(NEW.read_text(encoding='utf-8'))
    OLD.write_bytes(snapshot.read_bytes())
    assert sha(OLD)==before['old_entry_H0_sha256']
    save(A/'restoration.json',{'restored_path':str(OLD),'restored_sha256':sha(OLD),'byte_exact_H0':True,'independent_entry':str(NEW),'independent_entry_sha256':sha(NEW),'archived_R02_patch':str(A/'before/v3_validation_pipeline_R02_patched.py')})
    save(Q/'ISOLATED_ENTRY.json',{'active_revision_entry':str(NEW),'sha256':sha(NEW),'historical_entry':str(OLD),'historical_entry_status':'restored_byte_exact_H0_do_not_use_for_repaired_analysis','event_manifest':str(Q/'data/EVENT_MANIFEST.json'),'isolation_audit':str(A),'status':'validation_pending'})
    print('Historical v9 restored byte-for-byte; revision reader is independent',flush=True)
def validate():
    sys.dont_write_bytecode=True;sys.path.insert(0,str(R.parent/'.venv/Lib/site-packages'));sys.path.insert(0,str(NEW.parent))
    import pandas as pd
    from unittest.mock import patch
    import r02_events as m
    before=read(A/'preflight.json');assert sha(OLD)==before['old_entry_H0_sha256']
    protected=read(O/'checks/protected_files_start.json');bad=[p for p,h in protected.items() if sha(p)!=h];assert not bad,bad
    sources=read(O/'inventory/source_snapshots.json');badsrc=[x['source'] for x in sources if sha(x['source'])!=x['sha256'] or sha(x['snapshot'])!=x['snapshot_sha256']];assert not badsrc,badsrc
    oldmanifest=read(A/'before/ARTIFACT_MANIFEST.json')
    data_records=[x for x in oldmanifest['files'] if x['relative_path'].startswith(('R02/data/','R02/weather_checkpoint/','tables/','contracts/','code/snapshots/'))]
    assert all(sha(x['path'])==x['sha256'] for x in data_records)
    large=read(O/'inventory/large_input_identity.json')
    for x in large:assert sha(x['path'])==x['sha256']
    pop=read(Q/'checks/population_connection.json');assert sha(pop['path'])==pop['sha256']
    cb=read(Q/'checks/cache_inventory_before.json');cache=R.parent/'data/weather_request_cache'
    after={p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in cache.glob('*.pkl')};assert after==cb
    w=pd.read_parquet(Q/'data/weather_key_hour_audit.parquet').drop_duplicates('request_key');wc=w[w.cache_sha256.notna()]
    for i,row in enumerate(wc.itertuples(index=False),1):
        assert sha(row.cache_file_path)==row.cache_sha256
        if i%20000==0:print(f'Cache content verified {i}/{len(wc)}',flush=True)
    e,em=m.load_active_events();assert sha(em['producer'])==em['producer_sha256'] and sha(em['runner'])==em['runner_sha256']
    buf=io.StringIO();suite=unittest.defaultTestLoader.discover(str(NEW.parent),pattern='test_r02_events.py');result=unittest.TextTestRunner(stream=buf,verbosity=2).run(suite)
    (A/'unit_tests.txt').write_text(buf.getvalue(),encoding='utf-8');assert result.wasSuccessful()
    spec=importlib.util.spec_from_file_location('isolated_r02_entry',NEW);entry=importlib.util.module_from_spec(spec)
    # Reject filesystem writes during reader import and execution, including third-party writes.
    def deny_writes(event,args):
        if event=='open':
            mode=args[1];flags=args[2]
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):raise AssertionError('Reader attempted file write: '+str(args[0]))
        if event in {'os.mkdir','os.remove','os.rename','os.rmdir','socket.connect','subprocess.Popen'}:raise AssertionError('Reader side effect: '+event)
    # The hook remains installed but is active only within this small reader check.
    active=[True]
    sys.addaudithook(lambda event,args:deny_writes(event,args) if active[0] else None)
    try:
        spec.loader.exec_module(entry);sample,info=entry.step0_build_sample();same,coverage=entry.step1_lad_gapfill(sample)
        pd.testing.assert_frame_equal(sample,same);pd.testing.assert_frame_equal(sample,e.loc[e.new_in_study_utc&e.weather_numeric_available].copy())
        try:entry.step2_build_folds(sample)
        except RuntimeError as ex:guard=str(ex)
        else:raise AssertionError('R02 model boundary absent')
    finally:active[0]=False
    legacy_loaded=[name for name,obj in list(sys.modules.items()) if getattr(obj,'__file__',None) and Path(obj.__file__).resolve()==OLD.resolve()];assert not legacy_loaded
    # A restored file must remain exact even after using the new reader.
    assert all(sha(p)==h for p,h in protected.items())
    save(A/'validation.json',{'passed':True,'historical_files_unchanged':len(protected),'historical_source_and_snapshot_pairs_unchanged':len(sources),'prior_data_contract_table_snapshot_artifacts_unchanged':len(data_records),'raw_and_v3_full_hash_unchanged':True,'population_hash_unchanged':True,'cache_directory_size_mtime_unchanged':len(cb),'read_cache_full_hash_unchanged':len(wc),'unit_tests_passed':result.testsRun,'new_reader_side_effect_guard_passed':True,'legacy_module_imported':False,'event_master_count':len(e),'reader_sample_count':len(sample),'event_master_sha256':em['event_table']['sha256'],'entry_summary':info,'coverage':coverage,'R02_model_boundary':guard,'models_run':0,'numeric_recomputation':False,'manuscripts_modified':0})
    print('Isolation validation passed: all baseline files exact, new input reader equivalent',flush=True)
def close():
    v=read(A/'validation.json');assert v['passed'];rest=read(A/'restoration.json')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    protected=read(O/'checks/protected_files_start.json');assert all(sha(p)==h for p,h in protected.items())
    oldmanifest=read(A/'before/ARTIFACT_MANIFEST.json')
    mutable={'RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','RETURN_TO_CHATGPT.md','reports/R02_report.md','R02/REPRODUCE.md','code/check_r02.py','code/close_r02.py'}
    unexpected=[x['relative_path'] for x in oldmanifest['files'] if x['relative_path'] not in mutable and sha(x['path'])!=x['sha256']];assert not unexpected,unexpected
    reg=read(Q/'ISOLATED_ENTRY.json');reg['status']='validated';reg['validation']=str(A/'validation.json');save(Q/'ISOLATED_ENTRY.json',reg)
    counts={}
    for p in protected:
        suffix=Path(p).suffix.lower();counts[suffix]=counts.get(suffix,0)+1
    report=f'''# R00–R02 原有工作保护与独立流程审查报告

时间：{now}。本轮仅审查已完成工作、恢复原代码并隔离新入口，未推进 R03，未重估模型或修改论文。

## 结论与发现

审查前不能宣称“完全另起炉灶”：R02 按此前执行文件的活动入口要求，修改了原 `scripts/v3_validation/v3_validation_pipeline.py`。step0 被改为读新主表、导入 mkdir 被移除、step1 增加新输入分支、step2 遇到新输入会停止。这不只是新增文件，会改变旧调用链行为。此前报告说明过这个改动，但它不满足用户现在明确提出的原有代码保持原状要求。

已完成纠正：保留修改版本及原补丁作为历史证据，从已验证 H0 快照逐字节恢复该文件；新输入消费者放到独立新目录的 `scripts/event_input_repair/r02_input_pipeline.py`。原路径现在只属于旧 H0 流程，新流程不会导入或重定向它。恢复原代码也保留了原有方法缺陷，不等于这些旧缺陷已修复。

## 审查证据与范围

| 检查 | 结果 |
| --- | --- |
| 审查前 R02 交付 manifest | {read(A/'preflight.json')['prior_artifact_files_verified']} 个文件哈希一致，无交付后意外改写 |
| 恢复前原有文件差异 | 549 个受保护文件中仅原 v9 一个；91 组源码快照同样只发现这一处 |
| 恢复后原有文件 | 549/549 与基线 SHA256 一致，无删除、无残留改写 |
| 关键源码及冻结副本 | 91/91 组源文件和快照一致，包括父目录被引用的生产者 |
| raw/v3 及年度人口 | 再次完整 SHA256 比对一致 |
| 历史缓存目录 | 75,983 个文件的大小/mtime 清单一致 |
| 实际读取过的请求缓存 | 74,896 个文件再次逐一 SHA256 一致 |
| 新主表/天气审计/四样本对照/合同/表格/快照 | {v['prior_data_contract_table_snapshot_artifacts_unchanged']} 个既有产物哈希一致；未重新生成数值 |
| 独立新入口 | 全事件主表 135,025；返回 121,178 个研究期内数值天气可用事件，与迁移前逐列等值 |
| 输入规则测试 | 15 项通过 |
| 新入口副作用检查 | 导入及读取期间禁止写文件、创建/删除目录、联网、子进程；通过，未导入旧 v9 |
| 稿件、旧结果 | 保护清单内哈希一致，未改稿、未运行旧模型/图表 |

这是一项有明确基线的文件与执行隔离审查。保护清单并不是整块磁盘的历史快照，不能据此声称未登记文件在任意时期绝无变化。清单实际覆盖的路径见 `checks/protected_files_start.json`，后缀分布为 `{json.dumps(counts,ensure_ascii=False)}`；91 组源码身份见 `inventory/source_snapshots.json`。原有流程没有为了“验证能跑”而重新执行，因为它包含固定路径写入；源码保持原状由完整字节哈希证实，不把它夸大为旧环境/旧科学结果重新验证。

## 恢复与入口身份

- 恢复原文件：`{OLD}`。
- 恢复前 R02 改写哈希：`{read(A/'preflight.json')['old_entry_R02_sha256']}`。
- 恢复后 H0 哈希：`{rest['restored_sha256']}`。
- 新独立入口：`{NEW}`，SHA256 `{sha(NEW)}`。
- 新入口登记：`R02/ISOLATED_ENTRY.json`；验证记录：`R02_isolation_audit/validation.json`。
- 事件主表 SHA256 仍为 `{v['event_master_sha256']}`，135,025 事件及四候选样本人数不变。

R02 初次 `active_entry.json`、代码补丁和保护记录保留为“迁移前”证据，不静默抹去曾修改旧入口的历史。本轮在 `R02_isolation_audit/before/` 另存原交付摘要、报告、manifest、状态及两个验收辅助脚本。当前状态/摘要明确改用新入口。

## 后续执行边界

完整约定见 `ISOLATION_POLICY.md`。既有 scripts/results、父目录数据/生产者、原天气缓存、稿件均只读；新代码在独立目录，新结果写修复工作目录并保留版本。旧 `check_r02.py final`、`close_r02.py` 的 CLI 已阻止继续发布迁移前入口记录，防止旧辅助脚本误导下一阶段；它们的原始版本已归档。

可用 `code/audit_r02_isolation.py validate` 重新检查独立入口。数值生产者仍为新建的 `code/run_r02.py`，不调用原 v9。未来 R03 在独立修复流程接入共同折分、尾部和模型接口，不能回头改原有脚本来实现这些变化。本轮停止在 R02 后隔离审查完成。
'''
    (O/'reports/R02_ISOLATION_REVIEW.md').write_text(report,encoding='utf-8')
    note=f'> 隔离复核更新：原 v9 已恢复为 H0；当前修复入口为 `{NEW}`。以下 R02 首次执行记录的数值保留，涉及旧入口改写/548 个未变文件的描述属于迁移前历史。当前为 549/549 旧文件一致；详见 reports/R02_ISOLATION_REVIEW.md。\n\n'
    for relative in ['reports/R02_report.md','RETURN_TO_CHATGPT.md']:
        original=(A/'before'/relative).read_text(encoding='utf-8')
        (O/relative).write_text(note+original,encoding='utf-8')
    repro=(A/'before/R02/REPRODUCE.md').read_text(encoding='utf-8')
    repro=repro.replace('paper_revision_work_v2/code/check_r02.py final','paper_revision_work_v2/code/audit_r02_isolation.py validate')
    repro=repro.replace('close_r02 protection/close 属于验收和交接，不运行模型。','close_r02 是迁移前验收脚本，当前 CLI 已停止使用，改用隔离审查；不得据它重写旧入口元数据。')
    (Q/'REPRODUCE.md').write_text('> 当前为独立新入口，不接管原 v9。见 ISOLATED_ENTRY.json 和 ../ISOLATION_POLICY.md。\n\n'+repro,encoding='utf-8')
    state=read(O/'RUN_STATE.json');state['last_updated']=now;state['revision_entry']=str(NEW);state['historical_code_policy']='read_only_H0_restored';state['isolation_policy']='ISOLATION_POLICY.md'
    state['stages']['R02']['isolation_review']={'status':'completed','report':'reports/R02_ISOLATION_REVIEW.md','original_code_restored':True,'numeric_inputs_changed':False};save(O/'RUN_STATE.json',state)
    (O/'STATUS.md').write_text('# 当前状态\n\nR00/R01/R02 completed；R02 后隔离审查 completed。原有代码已恢复 H0，549 旧文件与 91 组源码/快照一致。新入口 scripts/event_input_repair/r02_input_pipeline.py 独立读取已冻结输入。数值未改变，模型未重估，稿件未改。R03 及以后 not_started。\n',encoding='utf-8')
    with (O/'DECISIONS.md').open('a',encoding='utf-8') as f:f.write('\n## D09：原研究只读，修复流程独立\n\n用户要求审查所有工作，确保基于原有工作另起炉灶、不破坏原有代码。R02 曾按先前文件接管原 v9，现保留修改证据、按 H0 快照逐字节恢复；修复入口迁到 scripts/event_input_repair/r02_input_pipeline.py。此决定优先于旧计划中直接修改既有入口的实施方式。新数值与模型状态不变；以后在新修复目录接入生产流程，不改原脚本、不写旧结果。见 ISOLATION_POLICY.md 和 reports/R02_ISOLATION_REVIEW.md。\n')
    ledger=read(O/'issue_ledger.json')
    for x in ledger:
        if x['id'] in ['C01','C09']:
            x['evidence']+='；R02_isolation_audit/validation.json（旧v9已恢复，新入口独立）'
            x['revision_entry']=str(NEW);x['historical_entry_status']='restored_H0'
            x['remaining']+='；R03仅在独立新流程继续，原研究代码只读'
    save(O/'issue_ledger.json',ledger)
    oldledger=(A/'before/ISSUE_LEDGER.md').read_text(encoding='utf-8')
    (O/'ISSUE_LEDGER.md').write_text('> 隔离状态更新：C01/C09 的新输入工作改接独立入口；旧 v9 已恢复 H0。旧证据路径保留历史身份；当前入口与约束见 issue_ledger.json、ISOLATION_POLICY.md 和隔离报告。\n\n'+oldledger,encoding='utf-8')
    codepaths=[NEW,NEW.parent/'r02_events.py',NEW.parent/'test_r02_events.py',O/'code/run_r02.py',O/'code/check_r02.py',O/'code/close_r02.py',Path(__file__)]
    save(A/'current_code_manifest.json',[{'path':str(p),'sha256':sha(p),'role':'new_revision_only'} for p in codepaths])
    import difflib
    for rel in ['code/check_r02.py','code/close_r02.py']:
        patch=''.join(difflib.unified_diff((A/'before'/rel).read_text(encoding='utf-8').splitlines(True),(O/rel).read_text(encoding='utf-8').splitlines(True),fromfile='pre_isolation/'+rel,tofile='isolated/'+rel))
        (A/(Path(rel).stem+'.patch')).write_text(patch,encoding='utf-8')
    # Confirm only explicit revision metadata/helper files changed from the complete R02 delivery.
    changed=[x['relative_path'] for x in oldmanifest['files'] if sha(x['path'])!=x['sha256']]
    assert set(changed)<=mutable,changed
    save(A/'revision_artifact_changes.json',{'prior_manifest_files':len(oldmanifest['files']),'changed_revision_only_files':changed,'unchanged_prior_files':len(oldmanifest['files'])-len(changed),'original_research_files_unchanged':len(protected),'all_numeric_outputs_unchanged':True})
    records=[]
    for p in sorted(O.rglob('*')):
        if p.is_file() and p!=O/'ARTIFACT_MANIFEST.json':records.append({'path':str(p),'relative_path':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'role':'revision_and_retained_history'})
    save(O/'ARTIFACT_MANIFEST.json',{'run_id':'R02_isolated_20260905','timestamp_utc':now,'root':str(O),'self_excluded':True,'files':records})
    print(json.dumps({'isolation':'completed','old_files_exact':549,'source_pairs_exact':91,'current_manifest_files':len(records),'numerical_changes':0},ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
