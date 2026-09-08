import json,hashlib,shutil,datetime,copy,re
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R05';M=W/'manuscript_record';H=W/'r05_review_handoff';S=H/'manuscript_record_seed'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
assert not Q.exists(),'Inspect prior R05 before resume'
handoff=read(H/'HANDOFF_MANIFEST.json');assert all(sha(H/x['path'])==x['sha256'] and (H/x['path']).stat().st_size==x['bytes'] for x in handoff['files'])
for sub in ['src','checks','tables','logs','configs','archive','frozen','data']: (Q/sub).mkdir(parents=True,exist_ok=True)
shutil.copytree(M,Q/'archive/manuscript_record_before_R05');shutil.copyfile(W/'ARTIFACT_MANIFEST.json',Q/'archive/ARTIFACT_MANIFEST_before.json')
for name in ['STATUS.md','RUN_STATE.json','DECISIONS.md','RETURN_TO_CHATGPT.md','issue_ledger.json','ISSUE_LEDGER.md']:shutil.copyfile(W/name,Q/'archive'/name)
shutil.copytree(H,Q/'frozen/r05_review_handoff');shutil.copytree(W/'R04/src',Q/'frozen/R04_src');shutil.copytree(W/'R03/src',Q/'frozen/R03_src')
dep=[{'path':str(p),'sha256':sha(p)} for folder in [Q/'frozen/R04_src',Q/'frozen/R03_src'] for p in folder.rglob('*') if p.is_file()];put(Q/'frozen/SOURCE_MANIFEST.json',dep)
patch=read(S/'R04_REVIEW_DELTA.json');local=read(M/'REVISION_ITEMS.json');incoming=read(S/'REVISION_ITEMS.json');base_match=sha(M/'REVISION_ITEMS.json')==patch['base_revision_items_sha256'];sm=read(M/'SOURCE_MANIFEST.json');mapping={};nextid=max(int(x['source_id'][3:]) for x in sm['sources'] if re.fullmatch('SRC[0-9]+',x['source_id']))+1
for src in read(S/'SOURCE_MANIFEST.json')['sources']:
    assert sha(S/src['path'])==src['sha256'];same=next((x for x in sm['sources'] if x['sha256']==src['sha256']),None)
    if same:mapping[src['source_id']]=same['source_id'];continue
    sid=src['source_id']
    if any(x['source_id']==sid for x in sm['sources']):sid=f'SRC{nextid:02d}';nextid+=1
    dest=M/'evidence'/f'{sid}_R04_review_{Path(src["path"]).name}';shutil.copyfile(S/src['path'],dest);row=copy.deepcopy(src);row.update(source_id=sid,path=dest.relative_to(M).as_posix(),incoming_source_id=src['source_id']);sm['sources'].append(row);mapping[src['source_id']]=sid
def remap(obj):
    if isinstance(obj,str):return re.sub(r'SRC\d+',lambda m:mapping.get(m.group(),m.group()),obj)
    if isinstance(obj,list):return [remap(v) for v in obj]
    if isinstance(obj,dict):return {k:remap(v) for k,v in obj.items()}
    return obj
conflicts=[]
for u in patch['items']:
    item=next(x for x in local['items'] if x['id']==u['target_mr']);seed=next(x for x in incoming['items'] if x['id']==item['id'])
    if any(x.get('review_id')==patch['review_id'] for x in item.get('review_history',[])):continue
    item.setdefault('history',[]).append({k:copy.deepcopy(v) for k,v in item.items() if k not in ['history','review_history']})
    item.setdefault('review_history',[]).append({'review_id':patch['review_id'],'incoming_source_map':mapping,'delta':remap(u),'scope':'external returned-package review; actual R05 checks pending'})
    item['review_r04_update']=remap(seed.get('review_r04_update',u));item['current_review_status']=seed.get('current_review_status','R05 pending')
    if base_match:
        for k in ['evidence','action','release_condition','decision_status','checkpoint','evidence_level','last_reviewed_checkpoint']:item[k]=remap(seed[k]) if k in seed else item.get(k)
    else:conflicts.append({'MR':item['id'],'policy':'local current fields preserved; review delta separate'})
local.update(version='MR-v1.4-R04-review' if base_match else local['version']+'+RV04',checkpoint='R05_review_merged_before_audit',review_id=patch['review_id']);put(M/'REVISION_ITEMS.json',local);put(M/'SOURCE_MANIFEST.json',sm);put(M/'R04_REVIEW_SOURCE_MAP.json',mapping)
for name in ['R04_REVIEW_WRITING_IMPACT.md','R04_REVIEW_DELTA.json','CLAIM_STATUS_CURRENT.json']:
    p=S/name
    if p.exists():
        if (M/name).exists():shutil.copyfile(M/name,Q/'archive'/name)
        (M/name).write_text(json.dumps(remap(read(p)),ensure_ascii=False,indent=2) if p.suffix=='.json' else remap(p.read_text(encoding='utf-8')),encoding='utf-8')
for name in ['MANUSCRIPT_LEDGER.md','CHANGELOG.md']:
    with (M/name).open('a',encoding='utf-8') as f:f.write('\n## R05接收RV-R04-COMPLETE-PACKAGE-20260905\n\n已按29个MR ID与来源SHA合并完整MR-v1.4-R04-review。当前审阅方案见R04_REVIEW_WRITING_IMPACT，直接R04证据及全部历史/作者决定保留。R05本地实测尚待本轮，Word未改。\n')
put(Q/'checks/protected_at_start.json',{p:sha(p) for p in read(W/'R04/checks/protected_at_start.json')})
st=read(W/'RUN_STATE.json');st['active_stage']='R05';st['stages']['R05'].update(execution_status='running',inputs=['r05_review_handoff/'],outputs=['R05/']);put(W/'RUN_STATE.json',st)
(W/'STATUS.md').write_text('R05运行中：审阅台账已合并，核查与候选修改尚在执行；V/W未开始，原代码/Word只读。\n',encoding='utf-8')
result={'review_id':patch['review_id'],'manifest_files_verified':len(handoff['files']),'base_match':base_match,'base_SHA':patch['base_revision_items_sha256'],'MR_count':len(local['items']),'source_map':mapping,'conflicts':conflicts,'Word_modified':False,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(Q/'checks/handoff_acceptance.json',result)
(Q/'HANDOFF_ACCEPTANCE.md').write_text('# R05-0接收与合并\n\n交接包逐文件大小/SHA通过；本地REVISION_ITEMS与已知MR-v1.3-R04基版SHA一致，无较新字段冲突。原完整台账已快照，29个MR按ID追加审阅历史与当前审阅字段；来源按SHA复用/映射，不覆盖原SRC。原作者决定、Word索引及R04实测记录保留。\n\n完整seed保存为frozen/r05_review_handoff，当前主台账在manuscript_record。merge review_id为RV-R04-COMPLETE-PACKAGE-20260905，逐条记录可识别重复导入。审阅意见与本地实测分开；本轮仅R05，不启动V/W。\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
