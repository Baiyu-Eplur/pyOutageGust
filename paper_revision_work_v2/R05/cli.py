import sys,runpy
from pathlib import Path
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'src'))
allowed=['numerical_audit','customer_audit','render_release','source_inventory','writing','finish','consumers','final_qa']
if len(sys.argv)<2 or sys.argv[1] not in allowed:raise SystemExit('R05 only: '+', '.join(allowed))
runpy.run_path(str(root/'src'/f'{sys.argv[1]}.py'),run_name='__main__')
