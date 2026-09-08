import json,hashlib,shutil,datetime
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;D=O/'R02'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
for s in ['archive_R00_R01','data','checks','logs','code_changes','weather_checkpoint']:(D/s).mkdir(parents=True,exist_ok=True)
manifest=json.loads((O/'ARTIFACT_MANIFEST.json').read_text(encoding='utf-8'))
bad=[x['path'] for x in manifest['files'] if sha(Path(x['path']))!=x['sha256']]
assert not bad,bad
large=json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8'))
for x in large:
    p=Path(x['path']);assert p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns'],x
snapshot=['RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','ARTIFACT_MANIFEST.json','RETURN_TO_CHATGPT.md']
for n in snapshot:
    dst=D/'archive_R00_R01'/n
    assert not dst.exists(),f'Refusing to overwrite pre-R02 snapshot: {dst}'
    shutil.copyfile(O/n,dst)
instruction=Path(r'C:\Users\haoya\Downloads\R00_R01审阅与R02执行指令.md')
shutil.copyfile(instruction,D/'R00_R01审阅与R02执行指令.md')
sources={p:str(sha(Path(p))) for p in json.loads((O/'checks/protected_files_start.json').read_text(encoding='utf-8'))}
cache=R.parent/'data/weather_request_cache'
cache_stats={p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in cache.glob('*.pkl')}
save(D/'checks/cache_inventory_before.json',cache_stats)
save(D/'checks/protected_before.json',sources)
save(D/'checks/preflight.json',{'prior_manifest_verified':len(manifest['files']),'changes':bad,'large_input_identity_reused':large,'cache_directory_files':len(cache_stats),'cache_directory_bytes':sum(x[0] for x in cache_stats.values()),'instruction_sha256':sha(instruction),'authorized':'User: 按该文件执行','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()})
state=json.loads((O/'RUN_STATE.json').read_text(encoding='utf-8'));state['active_stage']='R02';state['stages']['R02']['execution_status']='running'
state['last_updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(O/'RUN_STATE.json',state)
with (O/'DECISIONS.md').open('a',encoding='utf-8') as f:f.write('\n## D07：R02授权与规则细化\n\n用户明确回复“按该文件执行”，本轮按R00_R01审阅与R02执行指令.md执行R02并停止；R03及以后不执行。沿用D03 Buck proxy，无需重复批准。UTC是R01冻结分析日历，业务日历尚未核实；另存Europe/London日期/边界差异，不静默更换。v3值与缓存来源分别记录，缓存缺失不删除已存数值；未能验证窗口者保留为条件资格、另列严格已验证候选，不将未知宣称通过。\n')
(O/'STATUS.md').write_text('# 当前状态\n\nR00/R01 completed；R02 running；R03及以后not_started。模型未重估，文稿不修改。\n',encoding='utf-8')
print(json.dumps({'prior_artifacts_verified':len(manifest['files']),'cache_files':len(cache_stats),'R02':'running'}))
