import json,hashlib,shutil,datetime,copy
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R04';M=W/'manuscript_record';H=W/'r04_review_handoff'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
assert not Q.exists(),'Inspect existing R04 before resume'
old=read(W/'ARTIFACT_MANIFEST.json');assert all(sha(x['path'])==x['sha256'] for x in old['files'])
for x in read(H/'SOURCE_MANIFEST.json')['sources']:assert sha(H/x['path'])==x['sha256']
for sub in ['archive','src','checks','logs','configs','data','figures','tables','frozen']: (Q/sub).mkdir(parents=True,exist_ok=True)
for name in ['RUN_STATE.json','STATUS.md','DECISIONS.md','RETURN_TO_CHATGPT.md','issue_ledger.json','ISSUE_LEDGER.md','ARTIFACT_MANIFEST.json']:shutil.copyfile(W/name,Q/'archive'/name)
shutil.copytree(M,Q/'archive/manuscript_record_before_review')
shutil.copytree(H,Q/'frozen/review_handoff')
doc=read(M/'REVISION_ITEMS.json');patch=read(H/'REVISION_REVIEW_PATCH.json');sm=read(M/'SOURCE_MANIFEST.json');mapping={}
assert len(doc['items'])==29
nextid=max(int(x['source_id'][3:]) for x in sm['sources'] if x['source_id'].startswith('SRC'))+1
for row in read(H/'SOURCE_MANIFEST.json')['sources']:
    existing=next((x for x in sm['sources'] if x['sha256']==row['sha256']),None)
    if existing:mapping[row['source_key']]=existing['source_id'];continue
    sid=f'SRC{nextid:02d}';nextid+=1;dest=M/'evidence'/f'{sid}_{Path(row["path"]).name}';shutil.copyfile(H/row['path'],dest)
    sm['sources'].append({'source_id':sid,'original_name':row['original_name'],'path':dest.relative_to(M).as_posix(),'sha256':sha(dest),'size_bytes':dest.stat().st_size,'role':row['role'],'review_source_key':row['source_key']});mapping[row['source_key']]=sid
for u in patch['updates']:
    item=next(x for x in doc['items'] if x['id']==u['target_mr']);assert item['title']==u['title_for_matching']
    item.setdefault('review_history',[]).append({'review_id':patch['patch_id'],'source_map':mapping,'review_delta':u,'relationship':'review opinions retained separately from direct R03 measurements'})
doc['checkpoint']='R04_review_merged_before_formal';doc['version']='MR-v1.2-R03+RV03';save(M/'REVISION_ITEMS.json',doc);save(M/'SOURCE_MANIFEST.json',sm);save(M/'RV03_SOURCE_MAP.json',mapping)
with (M/'MANUSCRIPT_LEDGER.md').open('a',encoding='utf-8') as f:f.write('\n## R04前审阅增量已合并\n\n用户授权运行冻结all_valid核心、正式OOF及图10等价日历基/消费者修复；不执行备选训练p99、R05/V/W或Word修改。29项审阅意见逐条保存在REVISION_ITEMS.review_history，保持原实测证据/作者决定/历史。RV03来源映射见RV03_SOURCE_MAP.json，完整审阅MD/JSON见新增evidence。图10代数推论待本轮实际矩阵验证。\n')
with (M/'CHANGELOG.md').open('a',encoding='utf-8') as f:f.write('\n## R04启动：合并RV-R03-20260905\n\n先保存MR-v1.2-R03完整快照，再按原29项合并审阅增量，不覆盖原本地事实或作者决定；来源按SHA复用/分配新ID，未落稿。正式数值尚待本轮运行。\n')
cfg=read(W/'R03/configs/R04_primary.json');assert cfg['training_tail']=='all_valid' and cfg['groups']==['main','weather'] and cfg['targets']==['E0','R0c'];assert not Path(cfg['output_root']).exists()
ids={'event_sha':sha(W/'R02/data/R02_event_master.parquet'),'manifest_sha':sha(cfg['input_manifest']),'fold_sha':sha(cfg['fold_map']),'formal_config_file_sha':sha(W/'R03/configs/R04_primary.json'),'formal_config_canonical_sha':hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'code_identity':cfg['code_identity']}
assert ids['event_sha']=='8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d';assert ids['manifest_sha']==cfg['input_manifest_sha256'];assert ids['fold_sha']==cfg['fold_map_sha256']
protected=read(W/'checks/protected_files_start.json');current={p:sha(p) for p in protected};save(Q/'checks/protected_at_start.json',current)
save(Q/'checks/preflight.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'previous_artifacts_verified':len(old['files']),'source_map':mapping,'review_items_merged':len(patch['updates']),'identities':ids,'R03_core_reuse':'frozen local copied source/runtime; do not recopy libraries','no_models_yet':True})
st=read(W/'RUN_STATE.json');st['active_stage']='R04';st['stages']['R04']['execution_status']='running';save(W/'RUN_STATE.json',st)
(W/'STATUS.md').write_text('R04 running：审阅已合并，冻结all_valid主配置已核对，正式输出尚待运行。原代码/Word只读；不进入R05/V/W。\n',encoding='utf-8')
shutil.copyfile(W/'R03/PRODUCER_CONSUMER_MAP.md',W/'tables/RETAINED_ANALYSIS_COVERAGE.md')
with (W/'tables/RETAINED_ANALYSIS_COVERAGE.md').open('a',encoding='utf-8') as f:f.write('\nR04启动覆盖声明：上表为R03接收状态；本轮核心/OOF、VIF/阶段/CR1、分期、图1–10均纳入重算/消费者。六原因组/GLM/三阶将先恢复原定义，缺件才列阻断/延期，暂不生成不代表删除授权。R04完成时用实际覆盖替换此启动表。\n')
print(json.dumps(ids))
