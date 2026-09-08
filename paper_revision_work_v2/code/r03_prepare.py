"""Single-use R03 intake and dependency freeze; never import historical producers."""
import sys,json,hashlib,shutil,datetime
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;Q=O/'R03';P=R.parent
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
assert not Q.exists(),'R03 already initialized; inspect before resuming'
manifest=read(O/'ARTIFACT_MANIFEST.json');assert all(sha(x['path'])==x['sha256'] for x in manifest['files'])
protected=read(O/'checks/protected_files_start.json');assert all(sha(p)==h for p,h in protected.items())
for sub in ['src','configs','checks','logs','acceptance','folds','smoke','frozen/project_sources','frozen/contracts','frozen/evidence','archive','runtime/site-packages']:(Q/sub).mkdir(parents=True,exist_ok=True)
for rel in ['RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','ARTIFACT_MANIFEST.json','RETURN_TO_CHATGPT.md']:
    shutil.copyfile(O/rel,Q/'archive'/rel)
instruction=Path(r'C:\Users\haoya\.codex\attachments\dcfd7796-74f3-4230-8daf-0b4a663a005e\pasted-text.txt')
shutil.copyfile(instruction,Q/'frozen/evidence/SRC11_R03_instruction.txt')
for name,source in [('SRC09_local_R02_return.md',O/'R02_isolation_audit/before/RETURN_TO_CHATGPT.md'),('SRC10_local_R02_report.md',O/'R02_isolation_audit/before/reports/R02_report.md')]:shutil.copyfile(source,Q/'frozen/evidence'/name)
sources=[]
for x in read(O/'inventory/source_snapshots.json'):
    p=Path(x['snapshot']);assert sha(p)==x['sha256'];dest=Q/'frozen/project_sources'/Path(x['source']).relative_to(P)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    sources.append({'original_path':x['source'],'copied_from':str(p),'frozen_path':str(dest),'sha256':sha(dest),'role':'reference_only_never_import'})
for p in sorted((R/'scripts/event_input_repair').glob('*.py')):
    dest=Q/'frozen/project_sources/R02'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    sources.append({'original_path':str(p),'frozen_path':str(dest),'sha256':sha(dest),'role':'reference_only_R02_definition'})
for p in (O/'contracts').iterdir():
    if p.is_file():shutil.copyfile(p,Q/'frozen/contracts'/p.name)
shutil.copyfile(O/'R02/data/EVENT_MANIFEST.json',Q/'frozen/evidence/R02_EVENT_MANIFEST.json')
shutil.copyfile(O/'R02/ISOLATED_ENTRY.json',Q/'frozen/evidence/R02_ISOLATED_ENTRY.json')
shutil.copyfile(O/'R02_isolation_audit/validation.json',Q/'frozen/evidence/R02_isolation_validation.json')
for p in sorted((O/'tables').glob('R02*')):shutil.copyfile(p,Q/'frozen/evidence'/p.name)
for rel in ['checks/buckinghamshire_lineage.json','checks/buckinghamshire_original_indicators.csv','inventory/manuscript_versions.json','inventory/ACTIVE_PIPELINE.md','R02/checks/weather_scan_summary.json','R02/checks/population_connection.json','R02/checks/R1_compatibility_caps.json']:
    shutil.copyfile(O/rel,Q/'frozen/evidence'/Path(rel).name)
save(Q/'frozen/PROJECT_SOURCE_MANIFEST.json',sources)
# Fully local interpreter and standard library; selected third-party packages and their DLLs.
host=Path(sys.executable).parent;runtime=Q/'runtime/python'
runtime.mkdir()
for p in host.iterdir():
    if p.is_file() and p.suffix.lower() in ['.exe','.dll','.txt']:shutil.copyfile(p,runtime/p.name)
for sub in ['DLLs','Lib']:
    shutil.copytree(host/sub,runtime/sub,ignore=shutil.ignore_patterns('site-packages','__pycache__','*.pyc'))
site=P/'.venv/Lib/site-packages'
prefixes=('numpy','pandas','pyarrow','scipy','statsmodels','patsy','packaging','dateutil','python_dateutil','six','tzdata')
copied=[]
for p in site.iterdir():
    if not any(p.name==x or p.name.startswith(x+'-') or p.name.startswith(x+'.') for x in prefixes):continue
    dest=Q/'runtime/site-packages'/p.name
    if p.is_dir():shutil.copytree(p,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    else:shutil.copyfile(p,dest)
    copied.append(p.name)
print('Frozen interpreter and packages: '+', '.join(copied),flush=True)
runtime_files=[{'path':p.relative_to(Q).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((Q/'runtime').rglob('*')) if p.is_file()]
save(Q/'frozen/RUNTIME_MANIFEST.json',{'source_interpreter':str(host),'source_site_packages':str(site),'execution_policy':'local copied interpreter, stdlib and dependencies; -I -S -B; no external source sys.path','packages':copied,'files':runtime_files})
em=read(Q/'frozen/evidence/R02_EVENT_MANIFEST.json');assert sha(em['event_table']['path'])==em['event_table']['sha256']
save(Q/'checks/preflight.json',{'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'previous_artifacts_verified':len(manifest['files']),'protected_files_verified':len(protected),'project_source_copies':len(sources),'runtime_files':len(runtime_files),'R02_event_sha256':em['event_table']['sha256'],'models_run':0,'instruction_sha256':sha(instruction)})
state=read(O/'RUN_STATE.json');state['active_stage']='R03';state['stages']['R03']['execution_status']='running';save(O/'RUN_STATE.json',state)
(O/'STATUS.md').write_text('# 当前状态\n\nR03 running；原研究只读；代码依赖已复制隔离；R04/V/W not_started。\n',encoding='utf-8')
with (O/'DECISIONS.md').open('a',encoding='utf-8') as f:f.write('\n## D10：R03独立生产链与依赖副本\n\n按用户本轮明确授权仅执行R03；附件第3节替代旧R03实现提示。保留D09原研究只读约束，不重新接管v9。所有项目源代码依赖/参考先复制并哈希，实际代码仅使用R03本地实现和复制的Python/第三方库。R02主表只读校验，不重跑全量天气/H0。主方案按R01明确all_valid；p99分支按主训练恢复资格共享阈值。MR-v1.1完整台账正在定位，未取得前不得杜撰MR/CL原义。\n')
print(json.dumps({'R03':'initialized','source_copies':len(sources),'runtime_files':len(runtime_files)},ensure_ascii=False))
