"""Timestamped stage execution, verified reuse and project-local write isolation."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time
from datetime import datetime

PROJECT = Path(__file__).resolve().parents[1]
STAGES = ['baseline', 'model_selection', 'hinge_search', 'knot_estimation',
          'plateau_E0', 'plateau_R0c', 'select_final_knots', 'plot_model_selection',
          'fragility_demo', 'fragility_surfaces', 'final_models', 'district_day_fragility',
          'weather_only_regression', 'paper_extras', 'report_tables', 'documents']
REQUIRES = {
    'plateau_E0': ['model_selection/knots.json'],
    'plateau_R0c': ['model_selection/knots.json'],
    'select_final_knots': ['model_selection/knots.json', 'model_selection/ramp_model.json'],
    'plot_model_selection': ['model_selection/all_model_comparison.csv', 'model_selection/knots.json', 'run_summary.json'],
    'fragility_demo': ['model_selection/knots.json'],
    'final_models': ['model_selection/knots.json'],
    'weather_only_regression': ['model_selection/knots.json', 'model_selection/ramp_model.json'],
    'paper_extras': ['model_selection/knots.json'],
    'report_tables': ['model_selection/predicted_vs_observed_summary.csv', 'final_models/table2_replacement.csv',
                      'final_models/district_day_fragility.json', 'weather_only/weather_only_summary.json'],
    'documents': ['figures/pvo_rows.json', 'figures/t2_rows.json', 'figures/frag_rows.json', 'figures/wo_rows.json',
                  'paper/paper_extras.json'],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def now():
    return datetime.now().astimezone().isoformat()


def run(switches, purpose, *, dry_run=0, reuse_run='', knot_bootstraps=500, plateau_bootstraps=300, blas_threads=1):
    if not purpose.strip() or set(switches) != set(STAGES) or any(v not in (0, 1) for v in switches.values()):
        raise ValueError('Provide a purpose and exactly the documented 0/1 stage switches')
    if min(knot_bootstraps, plateau_bootstraps, blas_threads) < 1:
        raise ValueError('Bootstrap repetitions and thread count must be positive')
    selected = [s for s in STAGES if switches[s]]
    if dry_run or not selected:
        print(json.dumps({'purpose': purpose, 'selected': selected, 'reuse_run': reuse_run}, ensure_ascii=False, indent=2))
        return 0
    base = PROJECT / 'results/new'
    base.mkdir(parents=True, exist_ok=True)
    root = base / datetime.now().strftime('%Y%m%d%H%M%S')
    root.mkdir()  # no overwriting a previous run, even within the same second
    for folder in ['results/figures', 'results/model_selection', 'results/final_models', 'results/weather_only', 'results/paper', 'logs', 'tmp', 'mpl']:
        (root / folder).mkdir(parents=True, exist_ok=True)
    sources = [PROJECT/'main_new.py', PROJECT/'pretestmain.py', PROJECT/'pretest_paths.py', PROJECT/'review_package/code/run_main_regression.py', PROJECT/'docs/Draft.docx', *sorted((PROJECT/'analysis_new').rglob('*.py')), *sorted((PROJECT/'analysis_new').rglob('*.js'))]
    inputs = [PROJECT/'review_package/data'/f'combined_{m}_final.csv' for m in ['E0', 'R0c']]
    manifest = dict(started_at=now(), purpose=purpose, status='running', switches=switches,
                    settings=dict(knot_bootstraps=knot_bootstraps, plateau_bootstraps=plateau_bootstraps, blas_threads=blas_threads),
                    inputs=[dict(path=str(p), sha256=digest(p)) for p in inputs],
                    sources=[dict(path=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in sources],
                    environment=dict(python=sys.version, executable=sys.executable,
                                     packages={k: importlib.metadata.version(k) for k in ['numpy', 'pandas', 'scipy', 'statsmodels', 'matplotlib', 'openpyxl']}),
                    reuse_run=reuse_run, steps=[], outputs=[])
    save(root/'run.json', manifest)
    try:
        if reuse_run:
            previous = (base/reuse_run).resolve()
            if previous.parent != base.resolve() or previous == root.resolve():
                raise ValueError('REUSE_RUN must name a prior results/new timestamp directory')
            old = json.loads((previous/'run.json').read_text(encoding='utf-8'))
            if old['status'] != 'completed' or old['inputs'] != manifest['inputs']:
                raise ValueError('Only a completed run with identical input hashes may be reused')
            for record in old['outputs']:
                p = previous/record['path']
                if not p.resolve().is_relative_to(previous) or digest(p) != record['sha256']:
                    raise ValueError(f'Reuse checksum/path mismatch: {p}')
                dest = root/record['path']; dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
        env = os.environ.copy()
        env.update(NEW_ANALYSIS_RUN=str(root), NEW_KNOT_BOOTSTRAPS=str(knot_bootstraps),
                   NEW_PLATEAU_BOOTSTRAPS=str(plateau_bootstraps), PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
                   MPLBACKEND='Agg', MPLCONFIGDIR=str(root/'mpl'), TEMP=str(root/'tmp'), TMP=str(root/'tmp'),
                   PRETEST_OUTPUT_ROOT=str(root/'results'), PYTHONUNBUFFERED='1')
        for k in ['OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
            env[k] = str(blas_threads)
        for stage in selected:
            step = dict(stage=stage, status='running', started_at=now())
            manifest['steps'].append(step); save(root/'run.json', manifest)
            missing = [p for p in REQUIRES.get(stage, []) if not (root/'results'/p).exists()]
            if missing:
                raise FileNotFoundError(f'{stage} needs {missing}; enable prerequisite or set REUSE_RUN')
            start = time.monotonic()
            print(f'[{now()}] {stage}', flush=True)
            with (root/'logs'/f'{stage}.log').open('w', encoding='utf-8') as log:
                result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'analysis_new.runner', '--worker', stage],
                                        cwd=PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT)
            step.update(returncode=result.returncode, seconds=round(time.monotonic()-start, 3), finished_at=now(),
                        status='completed' if result.returncode == 0 else 'failed')
            save(root/'run.json', manifest)
            if result.returncode:
                raise RuntimeError(f'{stage} failed; see {root}/logs/{stage}.log')
        manifest['status'] = 'completed'
    except BaseException as exc:
        manifest.update(status='failed', error=repr(exc))
        if manifest['steps'] and manifest['steps'][-1]['status'] == 'running':
            manifest['steps'][-1].update(status='failed', error=repr(exc))
        raise
    finally:
        manifest['finished_at'] = now()
        manifest['outputs'] = [dict(path=str(p.relative_to(root)).replace('\\', '/'), bytes=p.stat().st_size, sha256=digest(p))
                               for p in sorted((root/'results').rglob('*')) if p.is_file()]
        save(root/'run.json', manifest)
        lines = ['# 新分析运行记录', '', f'目的：{purpose}', f'开始：{manifest["started_at"]}',
                 f'结束：{manifest["finished_at"]}', f'状态：{manifest["status"]}', '', '|步骤|状态|秒|', '|---|---|---|']
        lines += [f'|{s["stage"]}|{s["status"]}|{s.get("seconds", "") }|' for s in manifest['steps']]
        (root/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        print(f'{manifest["status"]}: {root}', flush=True)
    return 0


def worker(stage):
    from analysis_new.runtime import ROOT, DATA
    from pretestmain import _write_guard
    _write_guard(ROOT, ROOT)
    save(ROOT/'logs'/f'{stage}_sources.json', dict(stage=stage, recorded_at=now(),
         sources=[dict(path=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in
                  [PROJECT/'main_new.py', PROJECT/'pretestmain.py', PROJECT/'pretest_paths.py',
                   PROJECT/'review_package/code/run_main_regression.py', PROJECT/'docs/Draft.docx',
                   *sorted((PROJECT/'analysis_new').glob('*.py')), *sorted((PROJECT/'analysis_new').glob('*.js'))]]))
    def no_reference(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(args[0])).resolve()
            if p.is_relative_to(PROJECT/'Comments') or p.is_relative_to(Path('D:/Pyprogramme/STST2603')):
                raise PermissionError(f'Independent analysis cannot read reference material: {p}')
    sys.addaudithook(no_reference)
    if stage == 'baseline':
        from review_package.code import run_main_regression as baseline
        baseline.DATA_DIR = DATA
        baseline.RESULTS_DIR = ROOT/'results'
        baseline.main()
    elif stage in ['hinge_search', 'select_final_knots', 'report_tables', 'documents']:
        module = __import__('analysis_new.'+stage, fromlist=['main'])
        module.main()
    else:
        module = 'plateau_model' if stage.startswith('plateau_') else stage
        sys.argv = [module] + ([stage.split('_')[1]] if stage.startswith('plateau_') else [])
        runpy.run_module('analysis_new.'+module, run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker' and sys.argv[2] in STAGES:
        worker(sys.argv[2])
    else:
        raise SystemExit('Use main_new.py')
