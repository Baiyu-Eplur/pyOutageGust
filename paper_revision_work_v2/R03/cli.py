"""Isolated R03 CLI. Invoke with runtime/python/python.exe -I -S -B."""
import sys,os,json,argparse,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'runtime/site-packages'));sys.path.insert(0,str(ROOT/'src'))
def dependency_check():
    for file in ['PROJECT_SOURCE_MANIFEST.json','RUNTIME_MANIFEST.json']:
        doc=json.loads((ROOT/'frozen'/file).read_text(encoding='utf-8'));rows=doc if isinstance(doc,list) else doc['files']
        for row in rows:
            p=Path(row['frozen_path']) if 'frozen_path' in row else ROOT/row['path']
            with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            if actual!=row['sha256']:raise ValueError('Frozen code dependency changed: '+str(p))
def imported_paths():
    paths=sorted({str(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and not str(m.__file__).startswith('<')})
    bad=[p for p in paths if not Path(p).is_relative_to(ROOT)]
    if bad:raise ValueError('Code loaded from outside isolated R03: '+str(bad))
    return paths
def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['accept','test','smoke','formal']);parser.add_argument('--config');parser.add_argument('--execute-formal',action='store_true');args=parser.parse_args()
    dependency_check()
    from producer import read,save_json
    if args.command=='accept':
        from acceptance import run;run()
    elif args.command=='test':
        import unittest
        suite=unittest.defaultTestLoader.discover(str(ROOT/'src'),pattern='test_pipeline.py');result=unittest.TextTestRunner(verbosity=2).run(suite)
        save_json(ROOT/'checks/test_summary.json',{'passed':result.wasSuccessful(),'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures)},ROOT)
        if not result.wasSuccessful():raise SystemExit(1)
    else:
        if args.command=='formal' and not args.execute_formal:raise SystemExit('Formal R04 needs an explicit later execution request; this R03 turn runs smoke only')
        from run_pipeline import run
        from producer import code_identity
        config=read(args.config or ROOT/'configs/smoke.json')
        if args.command=='formal' and config.get('code_identity')!=code_identity():raise ValueError('R04 code identity differs from released configuration; review/release new version first')
        if args.command=='smoke' and config['purpose']!='non_inferential_smoke':raise ValueError('smoke must use marked configuration')
        run(config,formal=args.command=='formal')
    import numpy,pandas,scipy,pyarrow,platform
    save_json(ROOT/f'checks/runtime_{args.command}.json',{'python':sys.version,'executable':sys.executable,'packages':{'numpy':numpy.__version__,'pandas':pandas.__version__,'scipy':scipy.__version__,'pyarrow':pyarrow.__version__},'platform':platform.platform(),'loaded_code_paths':imported_paths(),'code_load_outside_R03':False,'formal_run':args.command=='formal','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},ROOT)
if __name__=='__main__':main()
