"""R04 extensions only; frozen core was run via R03 CLI."""
import sys,runpy
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'src'))
name=sys.argv[1]
if name not in ['calendar_repair','audit_results','compatibility','supplements','figures','report_data','final_data','artifact_acceptance','numeric_acceptance','product_complete','deliver']:raise SystemExit('undeclared R04 extension')
runpy.run_path(str(root/'src'/f'{name}.py'),run_name='__main__')
