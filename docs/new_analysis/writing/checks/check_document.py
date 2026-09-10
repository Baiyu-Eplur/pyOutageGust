"""Read-only structural checks of the English draft; writes a writing QA record."""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / 'Supplementary_Information_A_E_draft.md'
text = DRAFT.read_text(encoding='utf8')
tables = re.findall(r'^\*\*(Table [A-E]\d+)\.', text, re.M)
figures = re.findall(r'^\*\*(Figure [A-E]\d+)\.', text, re.M)
with (ROOT/'results/Appendix/figure_table_register.csv').open(encoding='utf-8-sig',newline='') as f:
    register = {r['display_number']:r for r in csv.DictReader(f)}
issues=[]
if len(tables)!=len(set(tables)) or len(figures)!=len(set(figures)):
    issues.append('Duplicate displayed caption number')
for label in tables+figures:
    if label not in register:issues.append('Unregistered caption '+label)
for label in re.findall(r'\b(?:Table|Figure) [A-E]\d+\b',text):
    if label not in tables+figures:issues.append('Reference without displayed item '+label)
imgs=[]
for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text):
    resolved=(DRAFT.parent/path).resolve()
    if not resolved.is_file():issues.append('Missing image '+path)
    else:imgs.append({'path':path,'sha256':hashlib.sha256(resolved.read_bytes()).hexdigest()})
if re.search(r'\{\{\w+\}\}|[A-Z]:[\\/]|\b(?:TODO|UNRESOLVED|agent)\b',text):
    issues.append('Placeholder or internal-only content in reader draft')
if re.findall(r'^## Appendix ([A-J])\.',text,re.M)!=list('ABCDE'):
    issues.append('Incorrect chapter scope')
for opening,closing in [('\\[','\\]'),('\\(','\\)')]:
    if text.count(opening)!=text.count(closing):issues.append('Unbalanced math delimiter '+opening)
expected_columns=None
for number,line in enumerate(text.splitlines(),1):
    if line.startswith('|'):
        columns=len(re.split(r'(?<!\\)\|',line))-2
        if expected_columns is None:expected_columns=columns
        elif columns!=expected_columns:issues.append(f'Table column count at line {number}')
    else:expected_columns=None
report={'status':'PASS' if not issues else 'ISSUES','scope':'Document structure and references only; not statistical verification',
        'draft_sha256':hashlib.sha256(DRAFT.read_bytes()).hexdigest(),
        'chapters':list('ABCDE'),'editable_tables':tables,'original_figures':figures,'images':imgs,
        'issues':issues,'registration':[register[x] for x in tables+figures]}
(HERE/'document_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'tables':len(tables),'figures':len(figures),'issues':issues},ensure_ascii=False))
if issues:raise SystemExit(1)
