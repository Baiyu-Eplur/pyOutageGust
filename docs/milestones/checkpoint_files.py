"""Stage this checkpoint's additions/modifications, never existing deletions.

Publish scope is existing Git ignore rules minus OS shortcuts. No research runs.
"""
from pathlib import Path
import argparse
import csv
import datetime
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
INVENTORY=HERE/'2026-09-10_checkpoint-files.csv'
VERIFY=HERE/'2026-09-10_checkpoint-verification.json'

def call(*args,input=None):
    p=subprocess.run(['git',*args],input=input,cwd=ROOT,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf-8',errors='replace'))
    return p.stdout

def paths(*args):return [x.decode('utf-8') for x in call(*args).split(b'\0') if x]
def sha(b):return hashlib.sha256(b).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['inspect','stage','refresh','verify']);args=parser.parse_args()
    changed=paths('diff','--name-only','--diff-filter=AM','-z')
    new=paths('ls-files','--others','--exclude-standard','-z')
    deleted=paths('ls-files','--deleted','-z')
    selected=sorted(set(changed+new+(paths('diff','--cached','--name-only','--diff-filter=AM','-z') if args.action=='refresh' else [])))
    excluded=[p for p in selected if Path(p).suffix.lower()=='.lnk']
    selected=[p for p in selected if p not in excluded and (ROOT/p).is_file()]
    oversized=[p for p in selected if (ROOT/p).stat().st_size>=100*1024**2]
    if oversized:raise RuntimeError('Files exceed publication limit: '+repr(oversized))
    if args.action=='inspect':
        print(json.dumps({'files':len(selected),'MiB':sum((ROOT/p).stat().st_size for p in selected)/1024**2,'excluded':excluded,'retained_local_deletions':len(deleted),'largest':sorted([(p,(ROOT/p).stat().st_size) for p in selected],key=lambda x:x[1],reverse=True)[:5]},ensure_ascii=False));raise SystemExit
    if args.action in ['stage','refresh']:
        if args.action=='stage' and call('diff','--cached','--name-only').strip():raise RuntimeError('Existing staged changes: inspect before replacing staging scope.')
        exclusions={INVENTORY.relative_to(ROOT).as_posix(),VERIFY.relative_to(ROOT).as_posix()}
        with INVENTORY.open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['path','bytes','sha256','scope'])
            for p in selected:
                if p not in exclusions:w.writerow([p,(ROOT/p).stat().st_size,sha((ROOT/p).read_bytes()),'addition' if p in new else 'modification'])
        selected=sorted(set(selected+[INVENTORY.relative_to(ROOT).as_posix()]))
        call('add','--pathspec-from-file=-','--pathspec-file-nul',input=b'\0'.join(p.encode() for p in selected)+b'\0')
    staged=paths('diff','--cached','--name-only','--diff-filter=AM','-z')
    staged_deleted=paths('diff','--cached','--name-only','--diff-filter=D','-z')
    mismatches=[]
    # One persistent Git process avoids hundreds of Windows process launches.
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for p in staged:
            process.stdin.write((':'+p+'\n').encode('utf-8'));process.stdin.flush()
            header=process.stdout.readline().strip().split()
            if len(header)!=3 or header[1]!=b'blob':raise RuntimeError('Unexpected blob response for '+p)
            remaining=int(header[2]);h=hashlib.sha256()
            while remaining:
                block=process.stdout.read(min(1048576,remaining))
                if not block:raise RuntimeError('Truncated blob for '+p)
                h.update(block);remaining-=len(block)
            if process.stdout.read(1)!=b'\n':raise RuntimeError('Invalid blob boundary')
            if h.hexdigest()!=sha((ROOT/p).read_bytes()):mismatches.append(p)
    finally:
        process.stdin.close();process.wait(timeout=20)
    record={'time':datetime.datetime.now().astimezone().isoformat(),'files_checked':len(staged),'staged_byte_mismatches':mismatches,'staged_deletions':staged_deleted,'existing_local_deletions_retained':len(deleted),'excluded_shortcuts':excluded,'inventory_sha256':sha(INVENTORY.read_bytes()),'scope':'Byte/staging publication check only; no new statistical validation.'}
    if mismatches or staged_deleted:raise RuntimeError(json.dumps(record,ensure_ascii=False))
    VERIFY.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    call('add','--',VERIFY.relative_to(ROOT).as_posix())
    print(json.dumps(record,ensure_ascii=False))
