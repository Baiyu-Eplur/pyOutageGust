"""Freeze writing sources and initialise the task-scoped skill adapter; no analysis imports."""
from pathlib import Path
from datetime import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
WRITING = HERE.parent.parent

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

if __name__ == '__main__':
    snapshot = HERE / 'protected_sources.json'
    if snapshot.exists():
        raise SystemExit('Existing writing snapshot retained; no overwrite.')
    paths = sorted(p for p in (ROOT/'results/Appendix').rglob('*') if p.is_file())
    paths += [WRITING/'Supplementary_Information_A_E_draft.md',
              ROOT/'results/new/20260909183317/results/paper/Extended_paper_draft.docx']
    snapshot.write_text(json.dumps({str(p.relative_to(ROOT)): digest(p) for p in paths}, indent=2), encoding='utf-8')
    state = json.loads((HERE.parent/'manuscript_state.json').read_text(encoding='utf-8'))
    state['project'].update(id='APP-FJ-DRAFT', title='Appendices F–J', active_release='F–J first draft')
    state['artifacts'] = [{'id':'appendix-fj','path':str((WRITING/'Appendices_F_J_draft.md').relative_to(ROOT)).replace('\\','/'),'role':'supplement','status':'ACTIVE','required_for_release':True}]
    state['contract']['task'] = 'Draft Appendices F–J from accepted results only; no statistical execution.'
    questions = {'F':'What coefficients, clustered uncertainty and sequential OOF contributions are supported?', 'G':'What do incident predictions and residuals show on the current samples?', 'H':'What do alternative mean models and incident-conditional analyses establish?', 'I':'What do descriptive storm-window predictions show?', 'J':'What do matched weather, aggregation, duration and retrospective temporal comparisons establish?'}
    state['contract']['questions'] = [{'id':k,'text':v,'lock':'SEMANTIC'} for k,v in questions.items()]
    state['contract']['nonclaims'] = ['No new fitting, resampling, model selection or scientific audit', 'No changes to main text, A–E or scientific outputs', 'No universal model optimality or prospective warning validation', 'No uncompleted weather coarse-bin frequency alignment claimed']
    state['contract']['outcomes'] = ['One editable F–J Markdown draft','Evidence map','Chinese author notes']
    state['alignment'] = [{'question_id':k,'method':'Read accepted methods and saved results','evidence':f'results/Appendix/{k}; writing evidence map','result':v,'interpretation':'Restricted to recorded sample, estimand and prediction identity','limitation':'No new analysis; local unaligned coarse-bin frequencies excluded','contribution':f'Appendix {k} reader function','status':'COMPLETE'} for k,v in questions.items()]
    state['decisions'] = [{'id':'writing-only','text':'Latest user prompt and accepted four-step ledger govern. Preserve proxy main model; accept completed outputs.'}]
    state['issues'] = []
    state['release'].update(status='DRAFT_FOR_REVIEW',candidate_artifact_ids=['appendix-fj'],completed_checks=[],checked_hashes={},visual_check='Pending final writing checks')
    state['authority_sources'] = [x for x in state['authority_sources'] if x['id'] in ['main','plan','claims','requirements','results','register']]
    for k in 'FGHIJ':
        state['authority_sources'].append({'id':k,'kind':'accepted results','path_or_reference':f'results/Appendix/{k}/README.md','scope':['Writing evidence only'],'status':'VERIFIED','last_verified':datetime.now().astimezone().isoformat()})
    (HERE/'manuscript_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'LOG.md').open('a',encoding='utf-8') as f:
        f.write('\n\n## '+datetime.now().astimezone().isoformat()+' — APP-FJ-DRAFT 写作证据冻结\n- 目的：依据已接受 F–J 结果完成英文附录初稿，实际使用本地 academic-writing-skills；不调用分析入口。\n- 读取：当前 Extended、A–E 格式参考、v9 计划、四步台账 (4) 第14节、正文待修改记录、F–J README/manifest/结果表及相关方法片段。\n- 修改：writing/checks/fj/prepare_writing.py 与任务级 skill adapter；对全部附录结果及正文/A–E建立只读 SHA256 快照。此快照仅用于证明写作未改动来源，不是历史数值审计。\n- 已知局部限制：H03-FREQ-ALIGN 尚未形成当前天气粗分箱对齐结果；F.3 天气阶梯沿用全体函数，须与天气最终规格分开解释。\n')
    print('Protected',len(paths),'source files; writing adapter initialised.')
