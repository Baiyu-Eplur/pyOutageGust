"""Build inherited drafts from local code, newly computed tables and our own map.

Node and Python document dependencies may be overridden with NEW_DOC_NODE,
NEW_DOC_NODE_MODULES and NEW_DOC_PYTHON; defaults are the desktop bundled runtime.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from analysis_new.runtime import PROJECT, ROOT


def main():
    res = ROOT/'results'; paper = res/'paper'
    runtime = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
    node = os.environ.get('NEW_DOC_NODE', str(runtime/'node/bin/node.exe'))
    py = os.environ.get('NEW_DOC_PYTHON', str(runtime/'python/python.exe'))
    env = os.environ.copy()
    env['NODE_PATH'] = os.environ.get('NEW_DOC_NODE_MODULES', str(runtime/'node/node_modules'))
    draft = PROJECT/'docs/Draft.docx'
    with zipfile.ZipFile(draft) as z:
        mapdir = paper/'draft_media/media'; mapdir.mkdir(parents=True, exist_ok=True)
        (mapdir/'image1.png').write_bytes(z.read('word/media/image1.png'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns))
                      for p in ET.fromstring(z.read('word/document.xml')).findall('.//w:p', ns)]
    start = next(i for i, t in enumerate(paragraphs) if t.strip().lower() == 'references')
    refs = [t for t in paragraphs[start+1:] if re.match(r'^\[\d+\]', t)][:26]
    if len(refs) != 26:
        raise ValueError('Expected the 26 original references in docs/Draft.docx')
    (paper/'references.json').write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding='utf-8')
    for builder in ['build_doc.js', 'build_papers.js']:
        subprocess.run([node, str(PROJECT/'analysis_new'/builder)], env=env, check=True)
    subprocess.run([py, '-X', 'utf8', '-B', str(PROJECT/'analysis_new/document_plan.py'), str(ROOT)], env=env, check=True)
