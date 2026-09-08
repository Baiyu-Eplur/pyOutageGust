"""Read-only verification of protected originals and frozen R03 dependencies."""
import json,hashlib,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R03'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def audit():
    protected=read(W/'checks/protected_files_start.json')
    bad=[p for p,h in protected.items() if not Path(p).exists() or sha(p)!=h]
    observations=[]
    for name in bad:
        p=Path(name)
        if p!=W.parent/'LOG.md':raise AssertionError(('protected original changed',name))
        content=p.read_bytes();h=hashlib.sha256();match=None;offset=0
        for line in content.splitlines(keepends=True):
            h.update(line);offset+=len(line)
            if h.hexdigest()==protected[name]:match=offset;break
        assert match is not None,('LOG baseline is not an exact unchanged prefix',name)
        snap=Q/'checks/observed_original_LOG_current.bin';snap.write_bytes(content)
        appended=Q/'checks/observed_original_LOG_append.txt';appended.write_bytes(content[match:])
        observations.append({'path':name,'status':'original_bytes_preserved_as_exact_prefix_with_append','baseline_sha256':protected[name],'current_sha256':sha(p),'baseline_prefix_bytes':match,'appended_bytes':len(content)-match,'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'writer':'not identified; R03 producers do not write this path','action':'observed and archived, original not reverted or edited','evidence_scope':'concurrent C01 repair log is not R03/B1 evidence'})
    pairs=read(W/'inventory/source_snapshots.json')
    assert all(sha(x['source'])==sha(x['snapshot'])==x['sha256'] for x in pairs)
    refs=read(Q/'frozen/PROJECT_SOURCE_MANIFEST.json')
    assert all(sha(x['original_path'])==sha(x['frozen_path'])==x['sha256'] for x in refs)
    rt=read(Q/'frozen/RUNTIME_MANIFEST.json')['files']
    assert all(sha(Q/x['path'])==x['sha256'] for x in rt)
    datarefs=read(Q/'frozen/REFERENCE_DATA_MANIFEST.json')
    assert all(sha(x['original_path'])==sha(x['frozen_path'])==x['sha256'] for x in datarefs)
    old=read(Q/'archive/ARTIFACT_MANIFEST.json')['files'];changed=[]
    allowed={'RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','RETURN_TO_CHATGPT.md'}
    for x in old:
        if sha(x['path'])!=x['sha256']:
            assert x['relative_path'] in allowed,('unexpected prior artifact modification',x['relative_path'])
            changed.append(x['relative_path'])
    large=read(W/'inventory/large_input_identity.json')
    for x in large:assert sha(x['path'])==x['sha256']
    words=read(W/'inventory/manuscript_versions.json')
    for x in words:assert sha(x['local'])==x['local_sha256']
    em=read(Q/'frozen/evidence/R02_EVENT_MANIFEST.json')
    assert sha(W/'R02/data/EVENT_MANIFEST.json')==sha(Q/'frozen/evidence/R02_EVENT_MANIFEST.json')
    assert sha(em['event_table']['path'])==em['event_table']['sha256']
    result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_with_observed_log_append':True,'protected_original_files_checked':len(protected),'protected_original_files_byte_identical':len(protected)-len(bad),'observed_original_changes':observations,'original_source_snapshot_pairs_verified':len(pairs),'frozen_project_source_original_pairs_verified':len(refs),'frozen_runtime_files_verified':len(rt),'frozen_reference_data_pairs_verified':len(datarefs),'prior_manifest_files':len(old),'prior_manifest_unchanged':len(old)-len(changed),'declared_changed_revision_state_files':changed,'unexpected_code_data_manuscript_modifications':[],'R02_event_sha256':em['event_table']['sha256'],'R02_manifest_unchanged':True,'raw_and_v3_full_SHA_rechecked':[{'key':x['key'],'sha256':x['sha256']} for x in large],'current_manuscripts_rehashed_unchanged':len(words),'weather_cache_full_scan_repeated':False,'weather_cache_identity_evidence':'R02 frozen protection evidence reused; R03 did not re-scan cache contents','runtime_module_paths':'checks/runtime_smoke.json and runtime_test.json; all Python modules inside R03','scope_limit':'hash checks cover recorded protected files, not an unsnapshotted historical filesystem; OS DLLs remain platform dependencies'}
    (Q/'checks/final_isolation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':print(json.dumps(audit(),ensure_ascii=False))
