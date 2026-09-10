"""Opt-in P03/P04 experiment. Invoke only through main_new.py.

Reads a checksummed completed project run, preserves all outcomes, acquires ERA5,
writes data diagnostics BEFORE any model fits, then evaluates both versions.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from analysis_new.runner import digest, save
from analysis_new.grid_weather import START, END, FIELD, API, WeatherFailure, boundary_centroids, acquire
from analysis_new.district_day_core import km, lad_folds
from analysis_new.grid_fragility_validation import TARGETS, paired_stats, grid_loo, evaluate, decide, plot_calibration

BOUNDARY = 'data/external/gis/LAD_DEC_2021_UK_BGC/LAD_DEC_2021_UK_BGC.shp'


def previous_run(project, name):
    base = (project/'results/new').resolve()
    path = (base/name).resolve()
    if not name or path.parent != base or not name.isdigit() or len(name) != 14:
        raise ValueError('P03 run reference must be a 14-digit results/new timestamp')
    return path, json.loads((path/'run.json').read_text(encoding='utf-8'))


def verified_output(run, manifest, relative):
    p = (run/relative).resolve()
    records = [r for r in manifest['outputs'] if r['path'] == relative]
    if not p.is_relative_to(run.resolve()) or len(records) != 1 or digest(p) != records[0]['sha256']:
        raise ValueError(f'Unverified prior output: {relative}')
    return p


def load_baseline(project, name, data):
    run, manifest = previous_run(project, name)
    if manifest['status'] != 'completed':
        raise ValueError('P03_BASE_RUN must be a completed run')
    sample = data/'combined_E0_final.csv'
    if not any(Path(x['path']).name == sample.name and x['sha256'] == digest(sample) for x in manifest['inputs']):
        raise ValueError('Baseline E0 input hash differs from current project input')
    panel_file = verified_output(run, manifest, 'results/final_models/district_day_panel.csv')
    validation_file = verified_output(run, manifest, 'results/final_models/interp_validation.json')
    panel = pd.read_csv(panel_file)
    d = pd.read_csv(sample)
    validate_panel(panel, d)
    return panel, d, dict(base_run=name, manifest_sha256=digest(run/'run.json'),
                         panel_sha256=digest(panel_file), sample_sha256=digest(sample),
                         old_interpolation_validation=json.loads(validation_file.read_text(encoding='utf-8')))


def validate_panel(panel, incidents, expected_lads=111, start=START, end=END):
    required = ['LAD21CD', 'date', 'gust', 'n_inc', 'maxc', 'wmaxc', *TARGETS]
    if not set(required).issubset(panel.columns):
        raise ValueError('Baseline panel columns incomplete')
    lads = sorted(incidents.LAD21CD.unique())
    dates = pd.date_range(start, end).strftime('%Y-%m-%d')
    expected = pd.MultiIndex.from_product([lads, dates], names=['LAD21CD', 'date'])
    actual = pd.MultiIndex.from_frame(panel[['LAD21CD', 'date']])
    if len(lads) != expected_lads or actual.has_duplicates or len(actual) != len(expected) or set(actual) != set(expected):
        raise ValueError('Baseline must contain exactly the complete LAD x UTC-date product')
    if not np.isfinite(panel.gust).all() or (panel.gust < 0).any():
        raise ValueError('Invalid baseline gust')
    # Check labels against OWN incident data, including zero-customer incidents.
    d = incidents.copy()
    d['date'] = pd.to_datetime(d.incident_date_utc, utc=True).dt.strftime('%Y-%m-%d')
    d['cust'] = d.customers_v2_event_excl_reinterruptions
    by = d.groupby(['LAD21CD', 'date'])
    aligned = panel.set_index(['LAD21CD', 'date'])
    expected_n = by.size().reindex(aligned.index, fill_value=0)
    expected_max = by.cust.max().reindex(aligned.index, fill_value=-1)
    weather_max = d[d.cause_group_official.eq('weather_natural')].groupby(['LAD21CD', 'date']).cust.max().reindex(aligned.index, fill_value=-1)
    for col, values in [('n_inc', expected_n), ('maxc', expected_max), ('wmaxc', weather_max)]:
        if not np.array_equal(aligned[col].to_numpy(), values.to_numpy()):
            raise ValueError(f'Baseline {col} does not match own incidents')
    for target in TARGETS:
        weather, threshold = target.startswith('wthr'), int(target.split('gt')[1])
        maximum = weather_max if weather else expected_max
        values = (maximum >= 0) if threshold == 0 else (maximum > threshold)
        if not np.array_equal(aligned[target].to_numpy(), values.astype(int).to_numpy()):
            raise ValueError(f'Baseline outcome mismatch: {target}')


def merge_weather(panel, grid):
    if grid.duplicated(['LAD21CD', 'date']).any():
        raise ValueError('Duplicate grid keys')
    merged = panel.merge(grid, on=['LAD21CD', 'date'], how='left', validate='one_to_one', sort=False)
    if len(grid) != len(panel) or merged.gust_grid.isna().any():
        raise ValueError('Incomplete or extra grid LAD-date coverage')
    merged['gust_proxy'] = merged['gust']
    merged['gust'] = merged.pop('gust_grid')
    # Preserve row ordering and every original non-gust field, including precipitation.
    for c in panel.columns.difference(['gust']):
        same = (np.array_equal(panel[c].to_numpy(), merged[c].to_numpy(), equal_nan=True)
                if pd.api.types.is_numeric_dtype(panel[c]) else panel[c].equals(merged[c]))
        if not same:
            raise ValueError(f'Panel field changed: {c}')
    return merged


def cache_paths(project, name):
    if not name:
        return {}
    run, manifest = previous_run(project, name)
    cache = {}
    prefix = 'results/p03_p04/weather_raw/'
    for r in manifest['outputs']:
        if r['path'].startswith(prefix) and r['path'].endswith('.json.gz'):
            p = verified_output(run, manifest, r['path'])
            cache[p.name.removesuffix('.json.gz')] = p
    if not cache:
        raise ValueError('Weather cache run has no validated raw responses')
    return cache


def data_diagnostics(panel, grid, centroids, baseline, out):
    summaries = {}
    for label, m in [('with_incident', panel.n_inc > 0), ('without_incident', panel.n_inc == 0), ('all', np.ones(len(panel), bool))]:
        summaries[label] = paired_stats(panel.loc[m, 'gust_proxy'], panel.loc[m, 'gust'])
    pd.DataFrame({k: {x: y for x, y in v.items() if not isinstance(y, dict)} for k, v in summaries.items()}).T.to_csv(out/'gust_comparison.csv', index_label='subset')
    summaries['difference_definition'] = 'ERA5 UTC daily maximum minus old incident-hour interpolation; not measurement error'
    validation = {}
    flags = []
    for name, exclude in [('leave_lad_out', False), ('leave_shared_grid_cell_out', True)]:
        try:
            loo = grid_loo(grid, centroids, exclude)
            loo.to_csv(out/f'{name}.csv', index=False)
            validation[name] = paired_stats(loo.grid_truth, loo.grid_loo)
            if validation[name]['correlation'] is None or validation[name]['correlation'] <= 0:
                flags.append(f'{name}: zero/negative spatial correlation')
        except ValueError as exc:
            flags.append(str(exc)); validation[name] = dict(error=str(exc))
    cells = grid.groupby('LAD21CD')[['grid_lat', 'grid_lon']].first().reset_index().merge(centroids, on='LAD21CD')
    cells['centroid_to_grid_km'] = km(cells.lat, cells.lon, cells.grid_lat, cells.grid_lon)
    cells.to_csv(out/'grid_cells.csv', index=False)
    if cells.centroid_to_grid_km.max() > 75:
        flags.append('At least one returned grid cell is >75 km from its centroid; verify coordinate selection')
    if grid.groupby('LAD21CD').gust_grid.std().eq(0).any():
        flags.append('At least one LAD has a constant three-year gust series')
    if (grid.gust_grid > 100).any():
        flags.append('At least one daily gust exceeds 100 m/s; inspect raw response/units')
    validation.update(old_proxy_reference=baseline['old_interpolation_validation'],
                      n_unique_returned_cells=len(cells[['grid_lat', 'grid_lon']].drop_duplicates()),
                      interpretation='Spatial continuity only. Different target/anchors/time aggregation from old LOO; not a truth-quality ranking.')
    save(out/'gust_comparison.json', summaries)
    save(out/'spatial_validation.json', validation)
    save(out/'quality.json', dict(complete=True, n=len(panel), flags=flags,
                                  notice='ERA5 reanalysis at centroid nearest cell, not station truth or LAD-wide maximum.'))
    return flags


def write_report(out, decision, settings, completed, error=None):
    labels = dict(rollback='回滚', intermediate='中间状态', promote='转正')
    lines = ['# P03/P04 实验报告', '', f'更新时间：{datetime.now().astimezone().isoformat()}',
             f'结论：**{labels[decision["status"]]}**', '', decision['reason'], '',
             f'旧面板运行：{settings.get("base_run")}', f'完成阶段：{", ".join(completed)}', '',
             '## 判断依据', '', '```json', json.dumps(decision, ensure_ascii=False, indent=2), '```', '',
             '本实验不会修改 Word、Table 7、旧面板或原始输入。达到候选门槛也必须由用户/设计方核查校准图和数据诊断后决定是否转正。',
             '回滚时建议正文不采用此实验，旧代理保留为明确注明局限的附录；此为实验建议，不是已经完成稿件移动。', '',
             '## 比较范围', '',
             '- 新变量为 ERA5、UTC、m/s 的中心点最近网格逐小时阵风之日最大值；不是逐日均值，也不是 LAD 面积最大值或地面观测真值。',
             '- 旧变量使用事件坐标均值位置与事件小时天气插值；新旧差异同时包含来源、中心点及时间聚合变化，不能单独归因于插值误差。',
             '- 面板标签不变，零客户事件仍计入任意事件；全体/天气归因各四阈值，其他协变量不参与本次单变量脆弱性拟合。',
             '- LAD 五折分组方式和种子与既有绘图一致，两版使用相同折。旧代理本身依赖事件位置/日期，仍有事件选择造成的局限；CV 不消除此来源问题。',
             '- 新网格留一区域与排除同网格邻居验证只检查空间连续性。其 RMSE 与旧事件锚点验证不是同一估计对象，不用于机械判定新源优劣。',
             '- LAD 配对 bootstrap 只量化固定折外预测误差的区域抽样不确定性；没有重新训练，也没有按风暴/日期分组。', '',
             '## 文件清单', '', '见 inventory.json（实际路径、字节与 SHA-256）；experiment.json 保存参数、阶段、边界/输入/源码指纹。',
             '模型完成时：parameters_long.csv / parameters_comparison.csv、brier_comparison.csv、cv_fold_scores.csv、oof_predictions.csv.gz、calibration_bins.csv、calibration.png、decision.json。',
             '数据层完成时：centroids.csv、grid_daily.csv、panel_grid.csv、gust_comparison.csv/json、spatial_validation.json、两种 LOO CSV、grid_cells.csv、quality.json。',
             'weather_raw/*.json.gz 保存逐小时 API 响应及请求信息；requests.jsonl 逐请求记录。未完成阶段不会生成伪造数值。']
    if error:
        lines += ['', '## 停止原因', '', error]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    from analysis_new.runtime import PROJECT, ROOT, DATA
    settings = json.loads(os.environ.get('P03_SETTINGS', '{}'))
    out = ROOT/'results/p03_p04'; out.mkdir(parents=True, exist_ok=True)
    completed = []
    record = dict(started_at=datetime.now().astimezone().isoformat(), settings=settings,
                  status='running', completed=completed, sources=[dict(path='analysis_new/'+p.name, sha256=digest(p)) for p in
                  [Path(__file__), PROJECT/'analysis_new/grid_weather.py', PROJECT/'analysis_new/grid_fragility_validation.py', PROJECT/'analysis_new/district_day_core.py']],
                  api=dict(url=API, model='era5', field=FIELD, unit='m/s', timezone='GMT', start=START, end=END),
                  criteria=dict(mean_relative_gain=settings.get('min_relative_gain', .05), negligible_gain=.01,
                                ci95_lower_above_zero=True, no_endpoint_worse_than_relative_limit=True,
                                mean_calibration_rmse_gain=settings.get('min_relative_gain', .05), visual_review_required=True))
    def step(name):
        completed.append(name); save(out/'experiment.json', record)
        print(f'[{datetime.now().astimezone().isoformat()}] P03/P04 {name}', flush=True)
    save(out/'experiment.json', record)
    try:
        if float(settings.get('request_interval', 10)) < 0 or int(settings.get('bootstraps', 1000)) < 100 or not .01 <= float(settings.get('min_relative_gain', .05)) < 1:
            raise ValueError('Invalid P03 interval/bootstrap/gain setting')
        if settings.get('base_run') == ROOT.name:
            raise ValueError('Baseline cannot be this running experiment')
        panel, incidents, provenance = load_baseline(PROJECT, settings.get('base_run', ''), DATA)
        record['baseline'] = provenance
        boundary = PROJECT/BOUNDARY
        files = [boundary.with_suffix(s) for s in ['.shp', '.shx', '.dbf', '.prj', '.cpg']]
        record['boundary'] = [dict(path=str(p.relative_to(PROJECT)), sha256=digest(p)) for p in files if p.exists()]
        centroids = boundary_centroids(boundary, sorted(panel.LAD21CD.unique()))
        centroids.to_csv(out/'centroids.csv', index=False); step('baseline_and_geometry_verified')
        grid = acquire(centroids, out/'weather_raw', interval=float(settings.get('request_interval', 10)),
                       cache=cache_paths(PROJECT, settings.get('weather_cache_run', '')))
        grid.to_csv(out/'grid_daily.csv', index=False)
        merged = merge_weather(panel, grid); merged.to_csv(out/'panel_grid.csv', index=False)
        step('complete_hourly_data_aggregated_and_aligned')
        flags = data_diagnostics(merged, grid, centroids, provenance, out)
        step('data_comparison_and_spatial_loo_saved_before_fits')
        # Use original E0 first-seen LAD order, exactly as plot_model_selection.
        mapping = dict(zip(incidents.LAD21CD, lad_folds(incidents.LAD21CD.to_numpy())))
        folds = merged.LAD21CD.map(mapping).to_numpy()
        merged[['LAD21CD']].assign(fold=folds).drop_duplicates().to_csv(out/'lad_folds.csv', index=False)
        result = evaluate(merged, folds, repeats=int(settings.get('bootstraps', 1000)), progress=lambda s: print(s, flush=True))
        for key, filename in [('parameters', 'parameters_long'), ('scores', 'brier_comparison'), ('calibration', 'calibration_bins'), ('fold_scores', 'cv_fold_scores')]:
            result[key].to_csv(out/f'{filename}.csv', index=False)
        comparison = result['parameters'].pivot(index='target', columns='version', values=['theta', 'beta', 'p0'])
        comparison.columns = ['_'.join(c) for c in comparison.columns]
        comparison.to_csv(out/'parameters_comparison.csv')
        result['oof'].to_csv(out/'oof_predictions.csv.gz', index=False, compression='gzip')
        save(out/'optimizer_diagnostics.json', result['diagnostics']); save(out/'paired_uncertainty.json', result['uncertainty'])
        plot_calibration(result['calibration'], out/'calibration.png')
        step('both_versions_fitted_and_validated')
        decision = decide(result['scores'], result['uncertainty'], flags, result['diagnostics'], float(settings.get('min_relative_gain', .05)))
        save(out/'decision.json', decision)
        record['status'] = 'completed'; write_report(out, decision, settings, completed)
    except Exception as exc:
        technical = isinstance(exc, (WeatherFailure, OSError))
        decision = dict(status='rollback' if technical else 'intermediate',
                        reason=('技术/覆盖障碍：停止实验，保留旧代理；没有用代理补齐新天气。' if technical else
                                '输入完整性、设置或模型验证未完成；不能对科学效果作转正/优劣判断。'), error=str(exc))
        record.update(status='failed', error=repr(exc))
        save(out/'decision.json', decision); write_report(out, decision, settings, completed, repr(exc))
        raise
    finally:
        record['finished_at'] = datetime.now().astimezone().isoformat(); save(out/'experiment.json', record)
        save(out/'inventory.json', dict(code=record['sources'], outputs=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=digest(p))
             for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'inventory.json']))


if __name__ == '__main__':
    main()
