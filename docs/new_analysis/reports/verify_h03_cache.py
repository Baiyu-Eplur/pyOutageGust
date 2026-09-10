"""One cache/publication check through the real entry; no forced refitting."""
from pathlib import Path
import sys,json,hashlib,subprocess
from datetime import datetime
ROOT=Path(__file__).resolve().parents[3];H=ROOT/'results/Appendix/H'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf8'))
before={p.relative_to(H).as_posix():digest(p) for p in H.rglob('*') if p.is_file() and (p.suffix in ['.csv','.gz'] or 'DIAGNOSTICS' in p.name or 'OPTIMIZER' in p.name)}
cmd=[sys.executable,'-X','utf8','-B','main_appendix.py','--appendices','H','--h03-only']
result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
execution=js(H/'logs/H03_LAST_EXECUTION.json');changed=[p for p,h in before.items() if not (H/p).is_file() or digest(H/p)!=h]
protected=js(Path(__file__).with_name('APP_H03_PROTECTED_SNAPSHOT.json'))
altered=[p for p,h in protected.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h]
bad=[v['path'] for v in js(H/'manifest.json')['outputs'] if digest(H/v['path'])!=v['sha256']]
checks=dict(entry_exit_zero=result.returncode==0,validated_cache=execution['cached'],no_GLM_fitting=execution['new_primary_GLM_fits']==0,
    no_OLS_fitting=execution['new_OLS_fits']==0,no_H2_H3_fitting=execution['H2_H3_fits']==0,arrays_diagnostics_unchanged=not changed,
    other_appendix_files_unchanged=not altered,manifest_output_hashes_valid=not bad,H01_H02_preserved=js(H/'logs/H03_PRESERVATION.json')['all_unchanged'])
output=dict(time=datetime.now().astimezone().isoformat(),command=subprocess.list2cmdline(cmd),all_passed=all(checks.values()),checks=checks,
    stable_H_files=len(before),protected_other_files=len(protected),changed=changed,other_changes=altered,manifest_mismatches=bad,
    stdout=result.stdout,stderr=result.stderr,scope='cache and publication only; no repeated statistical reconstruction')
p=Path(__file__).with_name('APP_H03_CACHE_VERIFICATION.json');p.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:output[k] for k in ['all_passed','checks','stable_H_files','protected_other_files']},ensure_ascii=False,indent=2))
raise SystemExit(not output['all_passed'])
