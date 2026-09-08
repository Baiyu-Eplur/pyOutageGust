"""Validate scoped deliverables and protected input identities; no model runs."""
import json,hashlib,math,re,datetime,csv
from pathlib import Path
O=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def clean(x):
    if isinstance(x,float) and not math.isfinite(x):return None
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list):return [clean(v) for v in x]
    return x
def save(p,x):p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
# Normalize this run's JSON missing values; H0 source files are never touched.
for p in O.rglob('*.json'):
    if 'snapshots' in p.parts:continue
    x=clean(json.loads(p.read_text(encoding='utf-8-sig')))
    if p.name=='event_semantic_checks.json':x['extreme_C_nonrepeat']=int(x['extreme_C_nonrepeat'])
    save(p,x)
before=json.loads((O/'checks/protected_files_start.json').read_text(encoding='utf-8'))
changes=[p for p,h in before.items() if not Path(p).exists() or sha(Path(p))!=h]
snap=json.loads((O/'inventory/source_snapshots.json').read_text(encoding='utf-8'))
snapbad=[x for x in snap if sha(Path(x['source']))!=x['sha256'] or sha(Path(x['snapshot']))!=x['sha256']]
large=json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8'))
largebad=[x['path'] for x in large if Path(x['path']).stat().st_size!=x['bytes'] or Path(x['path']).stat().st_mtime_ns!=x['mtime_ns']]
wx=json.loads((O/'checks/weather_cache_read_hashes.json').read_text(encoding='utf-8'))
wxbad=[p for p,h in wx.items() if sha(Path(p))!=h]
wb=json.loads((O/'checks/other_workbook_sources.json').read_text(encoding='utf-8'))
wbbad=[name for name,x in wb.items() if sha(O.parent.parent/'data'/name)!=x['sha256']]
imd=json.loads((O/'checks/buckinghamshire_lineage.json').read_text(encoding='utf-8'))
if sha(O.parent.parent/'data/localincomedeprivationdata.xlsx')!=imd['source_workbook_sha256']:wbbad.append('localincomedeprivationdata.xlsx')
req=['reports/R00_report.md','reports/R01_report.md','inventory/AUDIT_ACCEPTANCE.md','inventory/ACTIVE_PIPELINE.md','inventory/VERSION_AND_RUNTIME.md','inventory/WRITE_SCOPE.md','contracts/RESEARCH_HISTORY.md','contracts/DATA_CONTRACT.md','contracts/FIELD_PROVENANCE.md','contracts/CAUSE_RULES.md','contracts/INFORMATION_TIMING.md','contracts/BASELINE_SPEC.md','contracts/baseline_spec.json','contracts/UNRESOLVED_DEFINITIONS.md','RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','RETURN_TO_CHATGPT.md']
missing=[p for p in req if not (O/p).is_file()]
state=json.loads((O/'RUN_STATE.json').read_text(encoding='utf-8'))
stageok=all(x['execution_status']==('completed' if k in ['R00','R01'] else 'not_started') for k,x in state['stages'].items())
issues=json.loads((O/'issue_ledger.json').read_text(encoding='utf-8'));ids={x['id'] for x in issues}
expected={f'C{i:02}' for i in range(1,10)}|{f'T{i:02}' for i in range(1,15)}|{f'L{i:02}' for i in range(1,13)}
hist=(O/'contracts/RESEARCH_HISTORY.md').read_text(encoding='utf-8');hnums=set(int(x) for x in re.findall(r'^\|#(\d+)\|',hist,re.M))
wc=json.loads((O/'checks/weather_case_checks.json').read_text(encoding='utf-8'))
precip_bad=[x['source_row_number'] for x in wc if x['cached'] and (x['rain_valid_values']!=24 or x['exact_hour_rows']!=1 or abs(x['rain_strict_sum']-x['v3_precipitation24'])>1e-5)]
pres={'historical_files_checked':len(before),'historical_changes':changes,'snapshot_sources_checked':len(snap),'snapshot_mismatches':snapbad,'large_input_size_mtime_changed':largebad,'large_input_hash_policy':'R00 SHA once, final size/mtime identity check only','read_weather_caches_checked':len(wx),'weather_cache_changes':wxbad,'workbook_changes':wbbad}
save(O/'checks/final_preservation_check.json',pres)
qa={'required_files_missing':missing,'stages_correct':stageok,'required_issue_ids_missing':sorted(expected-ids),'history_1_to_43_complete':hnums==set(range(1,44)),'weather_available_case_strict_sum_mismatches':precip_bad,'protected_unchanged':not(changes or snapbad or largebad or wxbad or wbbad),'scope':'deliverable/protection verification; not repaired pipeline regression tests'}
save(O/'checks/final_delivery_checks.json',qa)
assert not missing and stageok and expected<=ids and hnums==set(range(1,44)) and not precip_bad and qa['protected_unchanged'],qa
# Append final evidence once; reruns replace this section.
for f in ['reports/R00_report.md','reports/R01_report.md','RETURN_TO_CHATGPT.md']:
    p=O/f;s=p.read_text(encoding='utf-8').split('\n## 交付结束保护复核')[0]
    p.write_text(s+'\n## 交付结束保护复核\n\n549个既有受监测文件、91个源码及快照、14个读取天气缓存均未变化；3个读取工作簿哈希一致。raw/v3在R00已核验SHA，结束size/mtime一致。所需交付齐全，#1–#43沿革与全部原C/T/L编号完整；R02及以后状态仍not_started。证据见checks/final_preservation_check.json与final_delivery_checks.json。\n',encoding='utf-8')
files=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='ARTIFACT_MANIFEST.json':
        files.append({'path':str(p),'relative_path':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'role':'H0_source_snapshot' if 'snapshots' in p.parts else 'R00_R01_output'})
save(O/'ARTIFACT_MANIFEST.json',{'run_id':'R00_R01_20260905','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(O),'self_excluded':True,'files':files})
print(json.dumps({'QA':qa,'preservation':pres,'manifest_file_count':len(files)},ensure_ascii=False))
