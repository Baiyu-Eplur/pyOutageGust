"""Bounded document checks: CSV presentation, links, source protection and manual-value copies.

This script does not assess scientific validity or import an analysis module.
"""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import re
import subprocess
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
WRITING=HERE.parent.parent
DRAFT=WRITING/'Appendices_F_J_draft.md'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

if __name__=='__main__':
    subprocess.run([sys.executable,'-X','utf8','-B',str(HERE/'format_tables.py')],cwd=ROOT,check=True)
    text=DRAFT.read_text(encoding='utf-8')
    sources=json.loads((HERE/'protected_sources.json').read_text())
    changed=[p for p,h in sources.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h]
    images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
    titles=set(re.findall(r'\*\*Table ([F-J]\d+)',text))
    refs=set(re.findall(r'Table ([F-J]\d+)',text))
    figures=set(re.findall(r'\*\*Figure ([F-J]\d+)',text))
    figrefs=set(re.findall(r'Figure ([F-J]\d+)',text))
    expected={'F':4,'G':3,'H':3,'I':3,'J':6}
    headings={k:len(re.findall(r'^### '+k+r'\.\d+ ',text,re.M)) for k in expected}
    controls=[ord(c) for c in text if ord(c)<32 and c!='\n']
    bad_rows=[]
    width=None
    for no,line in enumerate(text.splitlines(),1):
        if line.startswith('| '):
            n=len(re.split(r'(?<!\\)\|',line))
            if width is None:width=n
            elif n!=width:bad_rows.append(no)
        else:width=None
    f1=re.search(r'<!-- table:F1 start -->(.*?)<!-- table:F1 end -->',text,re.S).group(1)
    coefficient_rows=sum(1 for line in f1.splitlines() if line.startswith('| ') and not line.startswith('| Term') and not line.startswith('| ---'))
    hstatus={}
    for filename,value,label in [('H03_E0_all_NB2_DIAGNOSTICS.json',4.703206959,'alpha'),('H03_E0_all_Tweedie_DIAGNOSTICS.json',211.2479653,'scale'),('H03_R0c_all_Gamma_DIAGNOSTICS.json',1.978554568,'scale'),('H03_R0c_all_Tweedie_DIAGNOSTICS.json',6.405663818,'scale')]:
        source=json.loads((ROOT/'results/Appendix/H/data'/filename).read_text())
        hstatus[filename]=abs(source[label]-value)<5e-8 and str(value) in text
    register=pd.read_csv(ROOT/'results/Appendix/figure_table_register.csv')
    registered=set(register.display_number)
    checks={
        'five_chapters_and_19_sections':headings==expected,
        'all_112_final_coefficients_present':coefficient_rows==112,
        'all_21_table_captions':len(titles)==21,
        'five_figures_exist':len(images)==5 and all((WRITING/p).is_file() for p in images),
        'all_figure_captions':len(figures)==5 and figures==figrefs,
        'all_table_references_have_captions':refs<=titles,
        'display_numbers_match_existing_register':all('Table '+x in registered for x in titles) and all('Figure '+x in registered for x in figures),
        'table_column_counts_consistent':not bad_rows,
        'no_placeholder_markers':not re.search(r'\{\{TABLE_|\bUNION_DEDUPLICATED\b',text),
        'no_control_characters':not controls,
        'display_equations_balanced':text.count('\\[')==text.count('\\]')==9,
        'equation_tags_unique':len(re.findall(r'\\tag\{([^}]+)\}',text))==len(set(re.findall(r'\\tag\{([^}]+)\}',text))),
        'copied_H7_dispersion_values_match_saved_diagnostics':all(hstatus.values()),
        'protected_sources_unchanged':not changed,
    }
    result={'time':datetime.now().astimezone().isoformat(),'checks':checks,'protected_file_count':len(sources),'changed_protected_files':changed,'coefficient_rows':coefficient_rows,'tables':sorted(titles),'figures':sorted(figures),'image_paths':images,'headings':headings,'draft_sha256':digest(DRAFT),'scope':'Writing-only checks; no model/prediction/statistical validity audit','manual_H7_source_checks':hstatus,'bad_table_rows':bad_rows}
    (HERE/'writing_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':checks,'hash':result['draft_sha256'],'protected_files':len(sources)},ensure_ascii=False))
    if not all(checks.values()):raise SystemExit(1)
