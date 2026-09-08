"""Read-only acceptance of H0. All writes confined to this work directory."""
import sys, json, csv, hashlib, shutil, platform, datetime, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'paper_revision_work_v2'
AUD=ROOT/'results/code_audit_20260905'
PARENT=ROOT.parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def save(name,obj):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    for d in ['inventory','reports','contracts','checks','code/snapshots/H0']: (OUT/d).mkdir(parents=True,exist_ok=True)
    records=[]
    expected={r['file']:r for r in csv.DictReader((AUD/'deliverable_manifest.csv').open(encoding='utf-8-sig'))}
    for p in sorted(AUD.iterdir()):
        if not p.is_file():continue
        rec={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'read':True,'evidence':'verified_from_artifact','reuse':'H0 only; input repairs invalidate current scientific use'}
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                rd=csv.DictReader(f);rec['columns']=rd.fieldnames;rec['rows']=sum(1 for _ in rd)
        elif p.suffix=='.json':
            data=json.loads(p.read_text(encoding='utf-8-sig'));rec['structure']=list(data)[:30] if isinstance(data,dict) else {'length':len(data)}
        else:rec['characters_read']=len(p.read_text(encoding='utf-8-sig'))
        rec['matches_previous_manifest']=rec['sha256']==expected[p.name]['sha256'] if p.name in expected else None
        records.append(rec)
    save('inventory/audit_acceptance.json',records)
    before=json.loads((AUD/'historical_files_before.json').read_text(encoding='utf-8-sig'))
    changed=[];current={}
    for path,h in before.items():
        p=Path(path);current[path]=sha(p) if p.exists() else None
        if current[path]!=h:changed.append({'path':path,'old':h,'current':current[path]})
    save('checks/protected_files_start.json',current)
    save('inventory/historical_changes.json',{'checked':len(before),'changes':changed})
    sources=set(Path(r['path']) for r in csv.DictReader((AUD/'script_inventory.csv').open(encoding='utf-8-sig')))
    sources.update((ROOT/'scripts/code_audit_20260905').glob('*.py'))
    sources.update((PARENT/'rebuild_v3_full_stage/scripts').glob('*.py'))
    sources.update(PARENT/n for n in ['main1.py','Buckinghamshire_combination.py','GVA_new.py','GVA_merge_with_crosswalk.py','poppulation_merge.py','filter.py','data_arrange.py'])
    snapshots=[]
    for p in sorted(sources):
        if not p.exists(): continue
        rel=p.relative_to(PARENT);dest=OUT/'code/snapshots/H0'/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        snapshots.append({'source':str(p),'snapshot':str(dest),'sha256':sha(p),'snapshot_sha256':sha(dest)})
    save('inventory/source_snapshots.json',snapshots)
    inputs=[]
    old=json.loads((AUD/'source_and_sample_checks.json').read_text())['input_sha256']
    for key,p in [('raw',PARENT/'data/ukpn-iis.csv'),('v3',PARENT/'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')]:
        h=sha(p);inputs.append({'key':key,'path':str(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'sha256':h,'matches_H0':h==old[key]})
    save('inventory/large_input_identity.json',inputs)
    versions=[]
    for name in ['Draft_revised.docx','Appendix_revised.docx']:
        lp=ROOT/'docs/0905new'/name;bp=ROOT/'paper_revision_handoff_v2/reference/supplied_manuscripts'/name
        versions.append({'name':name,'local':str(lp),'local_sha256':sha(lp),'supplied':str(bp),'supplied_sha256':sha(bp),'same':sha(lp)==sha(bp)})
        with zipfile.ZipFile(lp) as z:
            doc=ET.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            lines=[''.join(p.itertext()) for p in []]
            lines=[''.join(p.itertext()) for p in doc.findall('.//w:t',ns)]
            paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in doc.findall('.//w:p',ns)]
            (OUT/'inventory'/f'{lp.stem}_read_only_text.txt').write_text('\n'.join(paragraphs),encoding='utf-8')
    save('inventory/manuscript_versions.json',versions)
    sys.dont_write_bytecode=True;sys.path.insert(0,str(PARENT/'.venv/Lib/site-packages'))
    import numpy,pandas,scipy,statsmodels,sklearn
    rt={'executable':sys.executable,'python':sys.version,'platform':platform.platform(),'packages':{m.__name__:m.__version__ for m in [numpy,pandas,scipy,statsmodels,sklearn]},'package_path':str(PARENT/'.venv/Lib/site-packages'),'historical_modules_imported':False,'git':'No repository at branch or parents (rev-parse verified)','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save('inventory/runtime_verified.json',rt)
    print(json.dumps({'artifacts_read':len(records),'manifest_mismatches':[r['path'] for r in records if r['matches_previous_manifest'] is False],'protected_checked':len(before),'changes':changed,'source_snapshots':len(snapshots),'large_inputs':inputs,'manuscripts':versions,'runtime':rt},ensure_ascii=False))
if __name__=='__main__':main()
