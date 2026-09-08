import sys,json,shutil,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R04';R=W.parent.parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
site=R/'.venv/Lib/site-packages';dst=Q/'runtime/site-packages';dst.mkdir(parents=True,exist_ok=True)
prefix=['matplotlib','PIL','pillow','fontTools','fonttools','kiwisolver','cycler','pyparsing','contourpy','sklearn','scikit_learn','joblib','threadpoolctl']
for p in site.iterdir():
    if not any(p.name==s or p.name.startswith(s+'-') or p.name.startswith(s+'.') for s in prefix):continue
    to=dst/p.name
    if to.exists():continue
    if p.is_dir():shutil.copytree(p,to,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    else:shutil.copyfile(p,to)
manifest=[{'path':p.relative_to(Q).as_posix(),'sha256':sha(p)} for p in dst.rglob('*') if p.is_file()]
(Q/'frozen/EXTRA_RUNTIME_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
hist=W.parent/'results/code_audit_20260905';out=Q/'frozen/H0';out.mkdir(exist_ok=True);refs=[]
for p in hist.iterdir():
    if p.suffix not in ['.csv','.json','.md']:continue
    to=out/p.name;shutil.copyfile(p,to);refs.append({'original':str(p),'copy':str(to),'sha256':sha(to)})
(Q/'frozen/H0_MANIFEST.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
print('additional runtime files',len(manifest),'H0 copies',len(refs))
