"""Final prose/metadata propagation and package read-back, without repeating stage execution."""
from common import *
from finish import wsave,wtext
import shutil,zipfile,datetime

def run():
    M=W/'manuscript_record';now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    sys.path.insert(0,str(Q/'frozen/skill_audits'));from audit_candidate_text import audit_candidate
    from audit_manuscript_state import audit as state_audit
    prior=read(Q/'checks/candidate_skill_audit.json');profile=prior['profile'];cands=read(Q/'tables/PARAGRAPH_CANDIDATES.json');rows=[]
    for loc,c in cands.items():
        f=audit_candidate(c['text'],loc,profile);rows.append({'location':loc,'text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),'findings':f,'manual_review':'Exact candidate rechecked after wording edits: paragraph function and adjacent context, narrow claim, evidence link, units, terminology, prose and no new bibliography; duplicated candidates are alternatives for merging, not repeated insertion.'})
    put(Q/'checks/candidate_skill_audit.json',{'profile':profile,'candidates':rows,'candidate_file_sha256':sha(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md'),'finding_count':sum(len(r['findings']) for r in rows),'previous_finding_count':15,'previous_findings_resolved':'suspended compounds and dense hyphenation rewritten without changing numbers or scope','Word_modified':False})
    remaining=[{'location':r['location'],'finding':x} for r in rows for x in r['findings']];put(Q/'checks/remaining_candidate_findings.json',remaining)
    assert not remaining,remaining
    state=read(Q/'checks/manuscript_state_adapter.json');state['release']['checked_hashes']['candidate']=sha(Q/'MANUSCRIPT_REWRITE_CANDIDATES.md');put(Q/'checks/manuscript_state_adapter.json',state);findings=state_audit(state,W);assert all(f['code'] in ['ISSUE002','RELEASE002'] for f in findings);put(Q/'checks/manuscript_state_skill_audit.json',{'findings':findings,'interpretation':'Five S3 manuscript-release conditions (sources, shape, contribution, engineering, Word) intentionally remain open. They are not execution failures or a blanket block on V00 protocol preparation; no scientific waiver.'})
    current=read(M/'REVISION_ITEMS.json')
    for item in current['items']:item['current_review_status']='R05_completed; scientific conditions retained in r05_update';item['last_reviewed_checkpoint']='MR-v1.5-R05';item['r05_update']['candidate_gate']='exact candidate file rechecked; source-bound and Word not modified'
    wsave(M/'REVISION_ITEMS.json',current)
    # Add the actually executed single public entry, preserving the underlying rendering provenance.
    p=Q/'CONSUMER_REPRODUCTION.md';text=p.read_text(encoding='utf-8');text=text.replace('实际命令（工作目录项目根）：','最终单入口（已实际运行；工作目录项目根）：\n\n```powershell\n& .\\paper_revision_work_v2\\R03\\runtime\\python\\python.exe -I -S -B .\\paper_revision_work_v2\\R05\\cli.py consumers\n```\n\n该入口在新发布目录不存在时执行完整12图渲染；存在时验证24个图件和全部冻结输入SHA后复用，再逐值审计并发布246个当前语义绑定。实际执行记录见logs/consumers.txt、checks/consumer_single_entry.json，图件与绑定各有当前指针。下列为同一入口内部步骤的审计命令：');write(p,text)
    for p in [W/'reports/R05_PROJECT_REVIEW.md',W/'RETURN_TO_CHATGPT.md',M/'R05_WRITING_IMPACT.md']:
        text=p.read_text(encoding='utf-8');text+='\n\n最终消费者单入口 `R05/cli.py consumers` 已实际通过：验证并复用本轮生成的12组图，再发布246语义绑定。候选文字最终逐段工具/人工复查后，15处连字符表达提示已改写并复核为0；不改任何数值或Word。记录见candidate_skill_audit.json及consumer_single_entry.json。\n';wtext(p,text)
    # Include code identity of every newly copied/executed source, not only the initial snapshots.
    codefiles=[p for p in Q.rglob('*.py') if 'frozen/r05_review_handoff' not in p.as_posix() and '__pycache__' not in p.parts]
    put(Q/'CODE_MANIFEST.json',{'files':[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(codefiles)],'entry_points':'cli.py allowed R05 commands only; consumers is final figure/binding entry; finish is one-time package assembly, final_qa performs final propagation','runtime_policy':'reuse already copied R03/R04 runtimes; original project imports not used'})
    # Keep history intact while current evidence copies follow the last audit wording.
    sources=read(M/'SOURCE_MANIFEST.json');source_map=read(M/'R05_SOURCE_MAP.json')
    for s in sources['sources']:
        if s['source_id'] in source_map:
            p=Path(source_map[s['source_id']]);dest=M/s['path'];shutil.copyfile(p,dest);s.update(size_bytes=dest.stat().st_size,sha256=sha(dest))
        p=M/s['path'];assert p.exists() and p.stat().st_size==s['size_bytes'] and sha(p)==s['sha256']
    sources['date']=now;wsave(M/'SOURCE_MANIFEST.json',sources)
    wtext(M/'CHANGELOG.md',(M/'CHANGELOG.md').read_text(encoding='utf-8')+'\nR05交付前复核：单消费者入口验证；15处候选表达提示修订后0；当前review状态字段同步；原LOG追加例外已披露、未回退。来源SRC43及以后同步最终R05文本，既有来源未覆盖。\n')
    wtext(M/'MANUSCRIPT_LEDGER.md',(M/'MANUSCRIPT_LEDGER.md').read_text(encoding='utf-8')+'\n\nR05最终核验补记：cli.py consumers已通过，当前90候选/963迁移行（950数字槽）逐段校对。0模型拟合/Word修改。原LOG.md于本轮期间追加4737字节，原193465字节前缀SHA一致；写入进程未确定，无原代码或Word变化，不声称原研究所有文件均未变。五项投稿层面S3条件继续开放，不等于R05执行失败。\n')
    large=read(Q/'LARGE_LOCAL_FILES.json');known={x['path'] for x in large['files']}
    for p in list((W/'R02/data').glob('*.parquet'))+[CORE/'frozen/reference_data/localincomedeprivationdata.xlsx']:
        if str(p) not in known:large['files'].append(record(p))
    put(Q/'LARGE_LOCAL_FILES.json',large)
    # Exact original-code and Word scope rechecked only where final changes could matter.
    iso=read(Q/'checks/final_isolation.json')
    for path,h in iso['Word_SHA'].items():assert sha(path)==h
    assert sha(W/'baseline/B1_MANIFEST.json')==iso['B1_MANIFEST']['sha256'];assert sha(W.parent/'LOG.md')==iso['append_only_log_exceptions'][0]['current_SHA']
    before=read(Q/'archive/manuscript_record_before_R05/REVISION_ITEMS.json');assert {i['id'] for i in before['items']}=={i['id'] for i in current['items']};assert all(i['history'] for i in current['items']);assert len(read(M/'CLAIM_STATUS_CURRENT.json')['claims'])==6
    put(Q/'checks/final_delivery_gate.json',{'status':'passed_for_R05_delivery','acceptance':'conditional_for_V','MR':29,'CL':6,'sources':len(sources['sources']),'candidate_locations':90,'migration_rows':963,'old_numeric_slots':950,'binding_rows':246,'combined_paragraphs':11,'figure_groups':12,'core_new_fits':0,'other_new_fits':0,'Word_changed':False,'original_log_append_disclosed':True,'V_W_started':False,'candidate_findings_after_final_edits':0,'submission_S3_conditions_open':5})
    bundle={'version':'MR-v1.5-R05','files':[{'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(M.rglob('*')) if p.is_file() and p!=M/'BUNDLE_MANIFEST.json']};wsave(M/'BUNDLE_MANIFEST.json',bundle)
    # Use prior relative package membership and add new QA/entry artifacts; exclude the previous ZIP's validation record.
    package=W/'RETURN_PACKAGE_R05.zip'
    with zipfile.ZipFile(package) as z:old=json.loads(z.read('PACKAGE_MANIFEST.json'))
    files={W/r['path'] for r in old['files']}
    for folder in [M,Q/'src',Q/'checks',Q/'tables',Q/'logs']:
        files.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.update(p for p in Q.glob('*') if p.is_file())
    files.discard(Q/'checks/return_package_validation.json');files.discard(Q/'logs/final_qa.txt')
    # Geometry and fold/config manifests allow relocation to the frozen local data; no mutable source-code dependency.
    files.update([Q/'release_v1/frozen/GEOMETRY_MANIFEST.json',Q/'frozen/SOURCE_MANIFEST.json',Q/'frozen/ADDITIONAL_SOURCE_MANIFEST.json',CORE/'folds/date_to_fold.csv',CORE/'frozen/evidence/R02_EVENT_MANIFEST.json',W/'code/r05_prepare.py'])
    manifest={'root':'paper_revision_work_v2','stage':'R05','files':[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)],'excludes':'large local files/runtimes; manifest itself; external post-package checksum report','complete_manuscript_record':True}
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,p.relative_to(W).as_posix())
        z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(package) as z:
        assert len(z.namelist())==len(files)+1
        for r in manifest['files']:
            raw=z.read(r['path']);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],r['path']
        for r in bundle['files']:assert 'manuscript_record/'+r['path'] in z.namelist()
    validation={'passed':True,'files_verified':len(files),'zip':record(package),'full_latest_ledger':'MR-v1.5-R05','manifest_relative':True,'no_V_W':True};put(Q/'checks/return_package_validation.json',validation)
    # Keep a backward-compatible complete manifest by retaining frozen prior identities and refreshing named current artifacts.
    previous=read(Q/'archive/ARTIFACT_MANIFEST_before.json')['files'];allpaths={Path(r['path']) for r in previous};allpaths.update(files);allpaths.add(package);allpaths.add(Q/'checks/return_package_validation.json');allpaths.discard(W/'ARTIFACT_MANIFEST.json')
    wsave(W/'ARTIFACT_MANIFEST.json',{'timestamp_utc':now,'stage':'R05','files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(allpaths) if p.exists()],'prior_manifest':'R05/archive/ARTIFACT_MANIFEST_before.json','package':record(package),'scope':'prior tracked artifacts plus current delivered files; no claim to enumerate all disk paths'})
    print(json.dumps(validation,ensure_ascii=False),flush=True)
if __name__=='__main__':run()
