"""Publish/verify this explicitly authorised checkpoint using Git Credential Manager.

Credentials are read in memory, used only with api.github.com for this repository,
and never printed, written to disk, or supplied on a command line.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[2]
REPO='Baiyu-Eplur/pyOutageGust'
TAG='analysis-appendices-checkpoint-20260910'
TITLE='关键里程碑：2026-09-10 地区日验证、附录证据补全与A–J英文初稿'
DOC=ROOT/'docs/milestones/2026-09-10_analysis-appendices-checkpoint.md'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

def token():
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,encoding='utf-8',cwd=ROOT,env=env)
    if p.returncode:raise RuntimeError('Git credential retrieval unavailable; no credential output exposed.')
    values=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
    if not values.get('password'):raise RuntimeError('No GitHub credential available.')
    return values['password']

def notes():
    s=DOC.read_text(encoding='utf-8')
    def replace(m):
        path=m.group(2)
        if path.startswith('http'):return m.group(0)
        rel=(DOC.parent/path).resolve().relative_to(ROOT).as_posix()
        return '['+m.group(1)+'](https://github.com/'+REPO+'/blob/'+TAG+'/'+quote(rel,safe='/')+')'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',replace,s)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['inspect','release','verify']);args=parser.parse_args()
    secret=token()
    def api(path,method='GET',body=None):
        payload=None if body is None else json.dumps(body,ensure_ascii=False).encode()
        request=urllib.request.Request('https://api.github.com/repos/'+REPO+path,data=payload,method=method,headers={'Authorization':'Bearer '+secret,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'pyOutageGust-checkpoint','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=45) as response:return json.load(response)
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            raise RuntimeError('GitHub request failed with HTTP '+str(e.code)) from None
    repo=api('');release=api('/releases/tags/'+TAG)
    if args.action=='inspect':
        print(json.dumps({'repository':repo['full_name'],'default_branch':repo['default_branch'],'push_permission':repo.get('permissions',{}).get('push'),'release_exists':release is not None},ensure_ascii=False));raise SystemExit
    commit=git('rev-parse',TAG+'^{commit}')
    remote=api('/git/ref/tags/'+TAG)
    if remote is None:raise RuntimeError('Remote tag missing; push the annotated tag before creating its release.')
    obj=remote['object']
    resolved=api('/git/tags/'+obj['sha'])['object']['sha'] if obj['type']=='tag' else obj['sha']
    if resolved!=commit:raise RuntimeError('Remote tag does not match local checkpoint.')
    body=notes()
    if args.action=='release' and release is None:
        release=api('/releases','POST',{'tag_name':TAG,'target_commitish':commit,'name':TITLE,'body':body,'draft':False,'prerelease':False})
    if release is None:raise RuntimeError('Release has not been published.')
    release=api('/releases/tags/'+TAG)
    if release['body']!=body or release['draft'] or release['prerelease']:raise RuntimeError('Release contents/status do not match checkpoint notes; no overwrite attempted.')
    main=api('/git/ref/heads/main')['object']['sha']
    record={'repository':REPO,'tag':TAG,'milestone_commit':commit,'annotated_tag_object':remote['object']['sha'],'release_id':release['id'],'release_url':release['html_url'],'release_title':release['name'],'published_at':release['published_at'],'verified_at':datetime.datetime.now().astimezone().isoformat(),'remote_main_at_verification':main,'release_notes_match_milestone_document':True,'release_notes_sha256':hashlib.sha256(body.encode()).hexdigest(),'local_historical_deletions_not_published':469}
    (DOC.parent/'2026-09-10_checkpoint-publication.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))
