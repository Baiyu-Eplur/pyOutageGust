"""Selected-appendix staging and transactional publication with scoped ownership."""
import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from contextlib import contextmanager
import uuid

from .catalog import ROOT, REQUIREMENTS, TITLES, SCOPES, MANUSCRIPT, PLAN
from .mapping import digest, write_json, write_csv, expected, materialize

OWNER='main_appendix.py'
OUTPUT=ROOT/'results/Appendix'

def now(): return datetime.now().astimezone().isoformat(timespec='seconds')

def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default

def safe_child(root, relative):
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe managed relative path: '+str(relative))
    candidate=root/p
    candidate.resolve().relative_to(root.resolve())
    return candidate

def atomic_json(path,value):
    temp=path.with_name(path.name+'.tmp')
    write_json(temp,value);os.replace(temp,path)

@contextmanager
def temporary_folder(parent,prefix):
    """Bounded creation: Windows tempfile may spin on access-denied directories.

    Raise PermissionError immediately; retry only an actual name collision.
    Cleanup applies only to this newly created, verified child directory.
    """
    parent=Path(parent).resolve()
    for _ in range(3):
        scratch=parent/(prefix+uuid.uuid4().hex)
        scratch.resolve().relative_to(parent)
        try:
            scratch.mkdir()
            break
        except FileExistsError:
            continue
    else: raise FileExistsError('Temporary name collisions in '+str(parent))
    try:
        yield scratch
    finally:
        scratch.resolve().relative_to(parent)
        shutil.rmtree(scratch)

def preflight(selected):
    frozen=load(Path(__file__).with_name('source_fingerprints.json'),{})
    required={MANUSCRIPT,PLAN,'results/new/20260909183317/run.json','scripts/final_combined_analysis/figure_style.py'}
    for r in REQUIREMENTS:
        if r['appendix'] in selected:
            required.update(r['sources'])
            if r['review']: required.add(r['review'])
    checked=[]
    for path in sorted(required):
        p=ROOT/path; actual=digest(p) if p.is_file() else None
        checked.append(dict(path=path,exists=p.is_file(),expected_sha256=frozen.get(path),actual_sha256=actual,
                            passed=bool(actual and actual==frozen.get(path))))
    # Bind deterministic summaries to the manuscript production inputs, not just
    # whichever curated CSV happens to exist today.
    authority=load(ROOT/'results/new/20260909183317/run.json',{})
    from pathlib import PureWindowsPath
    for record in authority.get('inputs',[]):
        path='review_package/data/'+PureWindowsPath(record['path']).name
        if path in required:
            actual=digest(ROOT/path) if (ROOT/path).is_file() else None
            checked.append(dict(path=path,check='matches_manuscript_run_input',expected_sha256=record['sha256'],actual_sha256=actual,passed=actual==record['sha256']))
    return checked

def publish(staged,target):
    """Replace one appendix only, retaining human files and rolling back on error.

    Temporary folders are always inside the explicitly supplied output parent.
    Recursive cleanup is restricted to this newly allocated temporary directory.
    """
    parent=target.parent.resolve();target.resolve().relative_to(parent)
    if target.is_symlink(): raise ValueError('Refuse symlink appendix target')
    previous=load(target/'manifest.json',{})
    managed=(set(previous.get('managed_files',[]))|{'manifest.json'}) if previous.get('owner')==OWNER else set()
    for rel in managed: safe_child(target,rel)
    new_files={p.relative_to(staged).as_posix() for p in staged.rglob('*') if p.is_file()}
    human=[]
    if target.exists():
        for p in target.rglob('*'):
            if p.is_symlink(): raise ValueError('Refuse symlink inside appendix: '+str(p))
            if p.is_file() and p.relative_to(target).as_posix() not in managed:
                rel=p.relative_to(target).as_posix()
                if rel in new_files: raise ValueError('Unmanaged human file conflicts with generated output: '+rel)
                human.append(rel)
    with temporary_folder(parent,'.appendix-publish-') as tmp:
        scratch=Path(tmp).resolve();scratch.relative_to(parent)
        merged=scratch/'merged';shutil.copytree(staged,merged)
        for rel in human:
            dest=safe_child(merged,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(target,rel),dest)
        manifest=load(merged/'manifest.json');manifest['preserved_unmanaged_files']=human
        manifest['removed_obsolete_managed_files']=sorted(managed-new_files)
        write_json(merged/'manifest.json',manifest)
        backup=scratch/'previous';moved=False
        try:
            if target.exists(): os.replace(target,backup);moved=True
            os.replace(merged,target)
        except BaseException:
            if moved and not target.exists(): os.replace(backup,target)
            raise
    return human

def result_synopsis(letter,out):
    """Summarize existing scores only; no thresholds or scientific adjudication."""
    import pandas as pd
    if letter=='A':
        d=pd.read_csv(out/'tables/A_SAMPLE_FLOW.csv')
        rows=[f'- {v.margin} / {v.scope}：n={v.n}，LAD={v.lads}，零客户={v.zero_customers}。' for v in d.itertuples()]
        vif=pd.read_csv(out/'tables/A_FINAL_DESIGN_VIF.csv')
        rows += [f'- {margin}当前全设计（含虚拟变量、不含截距）最大VIF={value:.8f}。' for margin,value in vif.groupby('margin').VIF.max().items()]
        rows += ['- 原因十分位表为C01 corrected WT范围60453条；最高箱57.061864%，不冒充正文未定位口径的91%端点。']
        return '\n'.join(rows)
    if letter=='B':
        d=pd.read_csv(out/'tables/B_RECOVERY_DEFINITION.csv')
        return '\n'.join(f"- {v.scope}: n={v.n}；恰好1小时={v.duration_exactly_1h}（{v.share_exactly_1h:.6%}）。" for v in d.itertuples())
    if letter=='E': return 'E_PERIOD_COEFFICIENTS保存三个时期范围的已存关键项；两期各自拟合。DD-TIME01的冻结预测另见J。'
    if letter=='C': return '全体候选24行（E0和包含零客户R0c各12项）；天气预测摘要6行（每结果3种）。平台比较另表保存；R0c平台为正客户51173/9254，不能与59834行候选梯级直接排序。'
    if letter=='D': return 'E0平台点估计全体14/25 m/s、天气11/24 m/s；既有300次bootstrap与自由分段500次分别列出。恢复自由分段和平台的样本量不同，表内保留各自n。未新增任何重采样。'
    if letter=='F':
        d=pd.read_csv(out/'tables/F_FULL_COEFFICIENTS.csv')
        return f'完整系数共{len(d)}行（含全体LAD-only与双向SE，以及天气双向SE）。四组结果均保留，不按p值筛选。'
    if letter=='J':
        d=pd.read_csv(out/'tables/J_TIME_METRICS.csv'); lines=[]
        for t in ['any_gt100','wthr_gt100']:
            v=d[d.target==t].iloc[0];lines.append(f"- DD-TIME01 {t}：BSS={v.brier_skill:.10f}；平均预测减发生率={v.bias_probability_percentage_points:.8f}概率百分点。")
        m=pd.read_csv(out/'tables/J_TIME_MONTHLY.csv')
        for t in ['any_gt100','wthr_gt100']:
            bad=m[(m.target==t)&(m.model_brier>m.baseline_brier)].month.tolist()
            lines.append(f'- {t}模型Brier劣于开发常数的月份：{", ".join(bad)}。九月只有30日一天；月度拆分并非独立重复验证。')
        lines.append('- 时间八任务BSS均为正，但所有任务总体平均预测低于实际；校准图保留所有非空既定箱。不能等同于所有风险层或月份校准准确。')
        for prefix,title in [('J04','DD-AGG01'),('J05','DD-DUR01')]:
            scores=pd.read_csv(out/f'tables/{prefix}_METRICS.csv')
            for t in ['any_gt100','wthr_gt100','any_gt1000','wthr_gt1000']:
                sub=scores[scores.target==t]
                lines.append(f'- {title} {t}，既有Brier：'+ '；'.join(f'{v.candidate}={v.brier:.10f}' for v in sub.itertuples())+'。仅作同实验同任务比较。')
        return '\n'.join(lines)
    if letter=='I':
        d=pd.read_csv(out/'tables/I_STORM_COUNTS.csv');u=d[d.storm=='UNION_DEDUPLICATED']
        return '\n'.join(f'- {v.margin}：七窗口去重并集{v.n}事件，占其固定样本{v.fraction_of_sample:.6%}。这是窗口覆盖描述，不是已完成当前模型预测验证。' for v in u.itertuples())
    return SCOPES[letter]

def generate(letter,stage,source_checks):
    from .exporters import EXPORTERS
    for d in ['figures','tables','data','logs']: (stage/d).mkdir(parents=True,exist_ok=True)
    records=[];states={};messages=[]
    for r in [r for r in REQUIREMENTS if r['appendix']==letter and r['action'] not in {'j03_complete','f02_complete','gi_complete','h03_complete'}]:
        rid=r['requirement_id'];messages.append(f'{now()} {rid} {r["source_status"]}')
        if r['action']=='gap':
            states[rid]='用户已关闭' if r['source_status']=='CLOSED' else '有具体原因的缺失'
            continue
        relevant=set(r['sources'])|({r['review']} if r['review'] else set())
        failed=[x['path'] for x in source_checks if x['path'] in relevant and not x['passed']]
        if failed: raise ValueError('Source absent/changed since mapping freeze: '+str(failed))
        EXPORTERS[r['action']](r,stage)
        for rel in expected(r):
            file=safe_child(stage,rel)
            if not file.is_file() or file.stat().st_size==0: raise ValueError('Expected export missing: '+rel)
            records.append(dict(path=rel,sha256=digest(file),bytes=file.stat().st_size,requirement_id=rid,claim_id=r['claim_id'],
                source_paths=r['sources'],source_sha256={p:digest(ROOT/p) for p in r['sources']},producer=r['producer'],
                export_function='analysis_new.appendix.exporters.'+r['action'],configuration=r['config'],status='已有且被明确复用' if r['source_status']=='READY' else '已生成'))
        states[rid]='已有且被明确复用' if r['source_status']=='READY' else '已生成'
    planned={p for r in REQUIREMENTS if r['appendix']==letter and r['action'] not in {'j03_complete','f02_complete','gi_complete','h03_complete'} for p in expected(r)}
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if actual!=planned: raise ValueError(f'Unexpected export set: {actual^planned}')
    synopsis=result_synopsis(letter,stage)
    reqs=[r for r in REQUIREMENTS if r['appendix']==letter and r['action'] not in {'j03_complete','f02_complete','gi_complete','h03_complete'}]
    text=[f'# 附录 {letter}：{TITLES[letter]}',f'最近生成：{now()}。本文件是中文产物整理说明，不是正式附录。',
          f'复现：`python main_appendix.py --appendices {letter}`；项目根目录以脚本位置解析。',SCOPES[letter],
          '## 关键结果摘要',synopsis,'## 需求、产物与适用范围']
    for r in reqs:
        text += [f"### {r['requirement_id']} — {r['question']}",f"{states[r['requirement_id']]}。正文定位：{r['location']}。{r['scope_note']}"]
        if r['gap']: text.append(r['gap'])
        text += [f'- [{p}]({p})' for p in expected(r) if not p.startswith('data/')]
    text += ['## 来源与呈现','每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。',
             '未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。']
    (stage/'README.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
    (stage/'logs/execution.log').write_text('\n'.join(messages)+f'\n{now()} staged outputs verified; awaiting publication\n',encoding='utf-8')
    write_json(stage/'logs/validation.json',dict(expected_outputs=len(planned),actual_outputs=len(actual),
        expected_set_matches=True,table_numeric_serialization_checked=True,source_fingerprints_match=True,
        scope='Export and serialization only; no independent scientific validation'))
    managed=sorted(actual|{'README.md','manifest.json','logs/execution.log','logs/validation.json'})
    manifest=dict(owner=OWNER,appendix=letter,last_attempt=now(),status='success_with_gaps' if any(s=='有具体原因的缺失' for s in states.values()) else 'success',
        update_state='本次已更新',requirements=states,outputs=records,managed_files=managed)
    write_json(stage/'manifest.json',manifest)
    return manifest

def root_index(out,selected,attempts,checks,command):
    manifests={letter:load(out/letter/'manifest.json',{}) for letter in TITLES}
    states={k:('本次未更新/保留上次成功产物' if m.get('status')=='failed_preserved' and v in {'已生成','已有且被明确复用'} else v)
            for m in manifests.values() for k,v in m.get('requirements',{}).items()}
    # Scientific J03 closure is recorded in the accepted ledger/catalog; J files stay read-only.
    if states.get('J03','').startswith('产物已补齐'): states['J03']='产物已补齐/研究负责人已关闭匹配比较缺口'
    if states.get('F02','').startswith('产物已补齐'): states['F02']='产物已补齐/研究负责人已关闭推断补全缺口'
    for rid in ['G03','I02']:
        if states.get(rid,'').startswith('产物'):states[rid]='产物已补齐/研究负责人已关闭第三包结果缺口'
    materialize(out,states)
    register=[]
    for letter,m in manifests.items():
        counts=Counter()
        for v in m.get('outputs',[]):
            p=Path(v['path']);kind='Figure' if p.parent.as_posix()=='figures' and p.suffix.lower()=='.png' else 'Table' if p.suffix=='.csv' and p.parent.as_posix()=='tables' else None
            if kind:
                counts[kind]+=1
                register.append(dict(semantic_id=p.stem,display_number=f'{kind} {letter}{counts[kind]}',appendix=letter,
                    requirement_id=v['requirement_id'],claim_id=v['claim_id'],path=letter+'/'+v['path'],
                    status=m['update_state'],source_sha256=json.dumps(v['source_sha256'],ensure_ascii=False)))
    write_csv(out/'figure_table_register.csv',register,['semantic_id','display_number','appendix','requirement_id','claim_id','path','status','source_sha256'])
    gaps=['# 当前结果缺口与关闭事项','J03/F02/G03/I02已由负责人确认关闭；GI-W01至W09图文待改保留。第四包H03产物状态见下，不自动替负责人关闭。']
    j03=states.get('J03','尚未生产')
    gaps += ['## J03 — '+j03,'第一包 APP-J03-COMPARE；协议、组件、八任务配对评价及执行回传说明见 J/logs/J03_EXECUTION_REPORT.md。研究负责人本轮确认J03反馈分析已完成、匹配比较缺口关闭，保留正文PROXY；本次不改写J成果。']
    f02=states.get('F02','尚未生产')
    gaps += ['## F02 — '+f02,'第二包APP-F02-COV；见F/logs/F02_EXECUTION_REPORT.md。更新台账(2)第10节已确认关闭；原表已有se_lad，配套矩阵与区间补齐；写作待改项留既有台账。']
    for rid,letter in [('G03','G'),('I02','I')]:
        gaps += [f'## {rid} — '+states.get(rid,'尚未生产'),f'第三包见{letter}/logs/GI_EXECUTION_REPORT.md；更新台账(3)第12节已确认关闭结果缺口；图文待改仍保留，未改写G/I产物。']
    gaps += ['## H03 — '+states.get('H03','尚未生产'),'第四包APP-H03-LINK；H/logs/H03_EXECUTION_REPORT.md记录四项既定全样本GLM、正式OLS参照及事件条件证据。有效范围和例外逐项保留，产物完成待反馈。']
    if manifests.get('C',{}).get('status')=='success':
        gaps += ['## C04 — 已关闭','最终四样本原12项阶梯及原三种CV已补齐。C/README.md、C_COVERAGE_MATRIX及C/logs/technical_checks.json记录复用和新计算。兼容历史CV仅有汇总分数的逐行预测未凭空恢复，见C说明。']
    for r in REQUIREMENTS:
        if r['action']=='gap': gaps += [f"## {r['requirement_id']} / {r['claim_id']} — {r['source_status']}",f"正文：{r['location']}；附录：{r['subsection']}。",r['gap']]
    for letter,error in attempts.items():
        if error: gaps += [f'## 本次 {letter} 未更新',error]
    (out/'result_gaps.md').write_text('\n\n'.join(gaps)+'\n',encoding='utf-8')
    try: version=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError): version='unavailable'
    code={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'analysis_new/appendix').glob('*.py')}
    code['main_appendix.py']=digest(ROOT/'main_appendix.py')
    for dependency in ['scripts/final_combined_analysis/figure_style.py','analysis_new/district_day_core.py']:
        code[dependency]=digest(ROOT/dependency)
    current={letter:dict(selected=letter in selected,last_attempt_status=('failed' if attempts.get(letter) else 'updated') if letter in selected else 'not_selected',
        artifact_status=m.get('status','not_generated'),update_state=m.get('update_state','没有产物'),manifest=f'{letter}/manifest.json') for letter,m in manifests.items()}
    from importlib.metadata import version as package_version
    environment=dict(python=sys.version,executable=sys.executable,packages={p:package_version(p) for p in ['numpy','pandas','scipy','matplotlib']})
    manifest=dict(owner=OWNER,updated_at=now(),command=command,root=str(out.resolve()),git_head=version,environment=environment,
        working_source_sha256=code,catalog_sha256=digest(Path(__file__).with_name('catalog.py')),
        source_fingerprint_registry_sha256=digest(Path(__file__).with_name('source_fingerprints.json')),
        manuscript=MANUSCRIPT,accepted_plan=PLAN,configuration=dict(selected=selected,mode='fixed_output_scoped_appendix_completion',random_steps=bool(set(selected)&{'C','J','G'}),seed=20260909 if 'J' in selected else 20260908 if set(selected)&{'C','G'} else None),
        appendices=current,requirement_status_counts=dict(Counter(states.values())),
        tables=sum(v['display_number'].startswith('Table') for v in register),figures=sum(v['display_number'].startswith('Figure') for v in register))
    atomic_json(out/'manifest.json',manifest)
    readme=['# A–J 附录产物入口','本目录由main_appendix.py管理；只保留当前状态，历史研究输出仍留在原运行目录。',
        '复现：`python main_appendix.py --all`；选择：`python main_appendix.py --appendices A J`；只读检查：`python main_appendix.py --all --check-only`。',
        f'正文权威来源：`{MANUSCRIPT}`。设计依据：`{PLAN}`。段落P编号按DOCX直接body段落计数（包含空段）。',
        '三层映射依次记录主张、需求、权威产物；单一可编辑登记源为analysis_new/appendix/catalog.py。图表显示编号仅在figure_table_register.csv维护。',
        f"当前表格{manifest['tables']}张（每表CSV+MD），图片{manifest['figures']}张。缺口见[result_gaps.md](result_gaps.md)。",
        '|附录|本次选择|实际产物状态|范围|','|---|---|---|---|']
    readme += [f"|[{a}]({a}/README.md)|{a in selected}|{current[a]['artifact_status']}|{SCOPES[a]}|" for a in TITLES]
    readme += ['运行只更新选定字母；暂存通过后事务替换，成功后移除仅此前清单管理的废弃文件。未知人工文件保留；若与新生成文件同名则报错而不覆盖。失败时保留上次完整产物并明确标注未更新。',
        '科学范围：C/J03按已有授权，F02按第二包仅补天气固定模型聚类推断；其余仅整理。J03比较缺口由用户确认关闭；F02已由负责人关闭；G/I第三包结果缺口已关闭，图文待改保留；H03第四包仅既定四项GLM与条件概率整理，产物待反馈。']
    # Adjacent table rows must not be separated by blank paragraph lines.
    (out/'README.md').write_text(('\n\n'.join(readme)+'\n').replace('|\n\n|','|\n|'),encoding='utf-8')
    write_json(out/'logs/validation.json',dict(time=now(),source_checks=checks,selected=selected,failures={k:v for k,v in attempts.items() if v},
        staged_expected_outputs_and_serialization_checked=True,scope='This production interface only'))
    (out/'logs/execution.log').write_text(f'{now()} {command}\n'+ '\n'.join(f'{a}: '+(attempts[a] or 'published') for a in selected)+'\n',encoding='utf-8')
    root_files=['README.md','claim_evidence_map.csv','appendix_requirements.csv','requirement_result_map.csv','figure_table_register.csv','result_gaps.md','logs/validation.json','logs/execution.log']
    manifest['root_files']=[dict(path=p,sha256=digest(out/p)) for p in root_files]
    atomic_json(out/'manifest.json',manifest)
    return manifest

def run(selected, out=OUTPUT, command=None, generator=None, recompute_c=False, j03_only=False, recompute_j03=False, f02_only=False, recompute_f02=False, gi_only=False, recompute_gi=False, render_only_gi=False, h03_only=False, recompute_h03=False):
    checks=preflight(selected);out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    command=command or subprocess.list2cmdline([sys.executable,'main_appendix.py','--appendices',*selected])
    attempts={}
    if generator is None:
        def generator(letter,stage,checks):
            if letter=='C':
                from .c_completion import generate as complete_c
                return complete_c(stage,checks,out/'C',force=recompute_c)
            if letter in ['G','I']:
                from .gi_completion import generate as complete_gi
                return complete_gi(letter,stage,checks,out/letter,force=recompute_gi,render_only=render_only_gi,base_generator=generate,command=command)
            if letter=='H':
                from .h03_completion import generate as complete_h03
                return complete_h03(stage,checks,out/'H',force=recompute_h03,base_generator=generate,command=command)
            if letter=='F':
                from .f02_cov import generate as complete_f02
                return complete_f02(stage,checks,out/'F',force=recompute_f02,only=f02_only,base_generator=generate,command=command)
            if letter=='J':
                from .j03_compare import generate as complete_j03
                return complete_j03(stage,checks,out/'J',force=recompute_j03,only=j03_only,
                                    base_generator=generate,command=command)
            return generate(letter,stage,checks)
    common_sources={MANUSCRIPT,PLAN,'results/new/20260909183317/run.json','scripts/final_combined_analysis/figure_style.py'}
    global_failures=[v['path'] for v in checks if v['path'] in common_sources and not v['passed']]
    for letter in selected:
        try:
            if global_failures: raise ValueError('Authority source changed: '+str(global_failures))
            with temporary_folder(out.parent,'.appendix-stage-') as tmp:
                stage=Path(tmp).resolve();stage.relative_to(out.parent.resolve())
                generator(letter,stage,checks);publish(stage,out/letter)
            attempts[letter]=None
        except Exception as exc:
            attempts[letter]=f'{type(exc).__name__}: {exc}'
            print(f'{letter}: {attempts[letter]}',file=sys.stderr)
            old=load(out/letter/'manifest.json',{})
            # Never overwrite an unknown human manifest after a name collision.
            if old.get('owner')==OWNER or not (out/letter/'manifest.json').exists():
                prior_success=old.get('last_successful_artifact_time',old.get('last_attempt'))
                old.update(owner=OWNER,appendix=letter,last_attempt=now(),last_successful_artifact_time=prior_success,
                    status='failed_preserved' if old.get('outputs') else 'failed_missing',error=attempts[letter],
                    update_state='本次未更新/保留上次成功产物' if old.get('outputs') else '本次未生成；缺失')
                if not old.get('outputs'):
                    old['managed_files']=['manifest.json']
                    old['requirements']={r['requirement_id']:('用户已关闭' if r['source_status']=='CLOSED' else '有具体原因的缺失' if r['action']=='gap' else '本次技术失败，未生成') for r in REQUIREMENTS if r['appendix']==letter}
                atomic_json(out/letter/'manifest.json',old)
    return root_index(out,selected,attempts,checks,command),attempts

def main(argv=None):
    parser=argparse.ArgumentParser(description='A–J fixed appendix production; C authorized candidate completion')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--appendices',nargs='+',choices=list(TITLES))
    group.add_argument('--all',action='store_true',help='生成全部A–J已有输入需求')
    parser.add_argument('--check-only',action='store_true',help='只读来源/哈希检查，不写日志或产物')
    parser.add_argument('--recompute-c',action='store_true',help='忽略C计算缓存，重算缺失组件；兼容历史结果仍复用')
    parser.add_argument('--j03-only',action='store_true',help='仅选择J03；J其他已存产物逐文件保留')
    parser.add_argument('--recompute-j03',action='store_true',help='明确重算本包96个组件；不重跑其他聚合/持续性/时间实验')
    parser.add_argument('--f02-only',action='store_true',help='仅F02推断补全；F其他结果保留')
    parser.add_argument('--recompute-f02',action='store_true',help='重新计算F02协方差；优先复用兼容残差，不强制OLS拟合')
    parser.add_argument('--gi-only',action='store_true',help='仅选择G/I第三包；其他G/I管理输出保留')
    parser.add_argument('--recompute-gi',action='store_true',help='重算本包必要固定模型/折输出；不重跑C/D')
    parser.add_argument('--render-only-gi',action='store_true',help='仅从有效缓存的保存数组重绘，不拟合；源或代码失配则报错')
    parser.add_argument('--h03-only',action='store_true',help='仅选择H03第四包，保留H01/H02和人工文件')
    parser.add_argument('--recompute-h03',action='store_true',help='明确重算H03四个既定候选；不启动CV/结点/H2/H3拟合')
    args=parser.parse_args(argv)
    selected=list(TITLES) if args.all or (args.check_only and not args.appendices) else list(dict.fromkeys(args.appendices or []))
    if not selected: parser.print_help();return 0
    if args.h03_only and selected!=['H']:parser.error('--h03-only requires --appendices H')
    if args.recompute_h03 and 'H' not in selected:parser.error('--recompute-h03 requires H')
    if args.gi_only and not set(selected).issubset({'G','I'}): parser.error('--gi-only requires G and/or I')
    if (args.recompute_gi or args.render_only_gi) and not set(selected).intersection({'G','I'}): parser.error('GI option requires G or I')
    if args.recompute_gi and args.render_only_gi: parser.error('recompute and render-only are mutually exclusive')
    if 'G' in selected and 'I' in selected and selected.index('I')<selected.index('G'): selected.remove('I');selected.insert(selected.index('G')+1,'I')
    if args.f02_only and selected!=['F']: parser.error('--f02-only requires --appendices F')
    if args.recompute_f02 and 'F' not in selected: parser.error('--recompute-f02 requires F')
    if args.j03_only and selected!=['J']: parser.error('--j03-only requires --appendices J')
    if args.recompute_j03 and 'J' not in selected: parser.error('--recompute-j03 requires J')
    if args.check_only:
        checks=preflight(selected)
        print(json.dumps(dict(selected=selected,requirements=len([r for r in REQUIREMENTS if r['appendix'] in selected]),
            source_status_counts=dict(Counter(r['source_status'] for r in REQUIREMENTS if r['appendix'] in selected)),
            checked_sources=len(checks),source_failures=[c for c in checks if not c['passed']],writes=False),ensure_ascii=False,indent=2))
        return int(any(not c['passed'] for c in checks))
    command=subprocess.list2cmdline([sys.executable,str(ROOT/'main_appendix.py'),*(argv if argv is not None else sys.argv[1:])])
    try:
        manifest,attempts=run(selected,command=command,recompute_c=args.recompute_c,
                              j03_only=args.j03_only,recompute_j03=args.recompute_j03,f02_only=args.f02_only,recompute_f02=args.recompute_f02,gi_only=args.gi_only,recompute_gi=args.recompute_gi,render_only_gi=args.render_only_gi,h03_only=args.h03_only,recompute_h03=args.recompute_h03)
        print(json.dumps({k:manifest[k] for k in ['root','tables','figures','requirement_status_counts','appendices']},ensure_ascii=False,indent=2))
        return int(any(attempts.values()))
    finally:
        with (ROOT/'LOG.md').open('a',encoding='utf-8') as f:
            f.write(f'\n## {now()} — 附录生产执行\n- 命令：`{command}`。目的：生成选定附录{selected}；C/J03/F02/GI/H03按各自明确授权补齐，其余只读整理；J03-only={args.j03_only}，F02-only={args.f02_only}。\n- 输出：results/Appendix；本次状态、失败/缺口、源码/输入SHA256见manifest.json与logs。原研究输出不变。\n')

if __name__=='__main__': raise SystemExit(main())
