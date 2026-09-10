"""DD-AGG01: offline, timestamped, fixed five-aggregation experiment."""
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from analysis_new.runner import PROJECT, digest, save, now
from analysis_new.p03_p04_grid_weather import previous_run, verified_output
from analysis_new.grid_weather import START, END, FIELD, parse_hourly
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.daily_aggregations import CANDIDATES, LABELS, aggregate
from analysis_new.fragility_optimizer import RULES, Objective, fit, probabilities
from analysis_new.dd_agg01_evaluation import evaluate, uncertainty, plot_results


def read(path):
    return pd.read_csv(path, float_precision='round_trip')


def run_experiment(root, settings):
    out = root/'results/dd_agg01'; out.mkdir()
    def event(message, **extra):
        record = dict(time=now(), message=message, **extra)
        with (out/'execution.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str)+'\n')
        print(f'[{record["time"]}] {message}', flush=True)
    def no_network(name, args):
        if name in ('socket.connect', 'socket.getaddrinfo'):
            raise PermissionError('DD-AGG01 prohibits network requests; use verified existing hourly responses')
    sys.addaudithook(no_network)
    source, manifest = previous_run(PROJECT, settings.get('source_run', '20260909205214'))
    if manifest['status'] != 'completed': raise ValueError('Source run is not completed')
    names = ['centroids.csv', 'grid_cells.csv', 'grid_daily.csv', 'panel_grid.csv', 'lad_folds.csv',
             'optimizer_diagnostics.json', 'parameters_long.csv', 'oof_predictions.csv.gz',
             'brier_comparison.csv', 'experiment.json', 'inventory.json']
    inputs = {n: verified_output(source, manifest, 'results/p03_p04/'+n) for n in names}
    raw = sorted((source/'results/p03_p04/weather_raw').glob('*.json.gz'))
    if len(raw) != 111: raise ValueError('Expected exactly 111 cached hourly envelopes')
    for p in raw:
        verified_output(source, manifest, 'results/p03_p04/weather_raw/'+p.name)
    provenance = [dict(path=str(p), sha256=digest(p)) for p in [source/'run.json', *inputs.values(), *raw]]
    run_manifest = json.loads((root/'run.json').read_text(encoding='utf-8'))
    protocol = dict(task='DD-AGG01', frozen_at=now(), source_run=source.name, input_files=provenance,
                    start=START, end=END, days=1096, lads=111, rows=121656, unit='m/s', timezone='UTC',
                    targets=TARGETS, target_rule='gt0 means any event including zero customers; other thresholds strictly > k; existing panel labels unchanged',
                    candidates=dict(zip(CANDIDATES, ['max(g)', 'sum(g)/24', '.3*sorted(g)[20]+.7*sorted(g)[21]',
                                                     'mean(sorted(g)[-3:])', 'max(mean(g[h:h+3]) for h in range(22))'])),
                    model='p0+(1-p0)*Phi((log(A)-log(theta))/beta); A=0 -> p0', optimizer=RULES,
                    folds=dict(path=str(inputs['lad_folds.csv']), sha256=digest(inputs['lad_folds.csv']), rule='read original fold labels, never regenerate'),
                    primary='any_gt100', important_secondary='wthr_gt100',
                    metrics='row-pooled OOF Brier; absolute/relative gain vs repaired A01; BSS vs training-fold constant; no adoption threshold',
                    calibration='common quantiles 0..1 by .1 pooled from valid five OOF predictions per task, add 0/1, unique edges; searchsorted right; n<100 isolated crosses; empty NaN; weighted RMSE',
                    csv_read=dict(float_precision='round_trip'),
                    uncertainty=dict(repeats=1000, seed=20260909, unit='paired LAD, fixed OOF', limitations='No retraining, selection adjustment, or full storm/date dependence'),
                    command=os.environ.get('DD_AGG01_ENTRY_COMMAND', 'python -X utf8 -B main_new.py (STEPS[dd_agg01]=1)'),
                    sources=run_manifest['sources'], environment=run_manifest['environment'],
                    design_status='fixed-candidate exploratory comparison informed by historical results; not formal preregistration',
                    unchanged=['raw grid/hourly source', 'locations', 'labels', 'LAD folds', 'likelihood/model form', 'equal row weights'],
                    forbidden=['weather requests', 'new covariates/models/time splits', 'Word edits', 'history overwrite', 'return zip'])
    save(out/'experiment.json', protocol)
    protocol_text = f'''# DD-AGG01 冻结协议

冻结时间：{protocol['frozen_at']}。本轮为已见历史结果基础上的固定候选探索比较，不称为预注册。实际命令：`{protocol['command']}`。

## 固定输入与分析设计

输入为 P03 {source.name} 的 111 份既有 ERA5 小时响应；2021-04-01 至 2024-03-31 共 1,096 UTC 自然日，每日 24 个 m/s 阵风值。原位置、返回网格、八个标签与 LAD 折号不变。gt0 是任意事件，包含零客户；其余为严格大于相应客户阈值。所有输入路径、SHA256、折号文件指纹、源代码指纹和依赖版本见 experiment.json。

|候选|定义（Python 从0计数）|
|---|---|
'''+ '\n'.join(f'|{c}|{d}|' for c, d in protocol['candidates'].items())+'''

## 统一数值规则

模型 p=p0+(1-p0)Phi((log A-log θ)/β)，A=0 使用 p0 极限，不改标签、不删日、不加天气常数。稳定 log-CDF Bernoulli 似然，无目标概率裁剪；完全相同 A 精确分组，无四舍五入。坐标为 logθ、logβ、p0/训练事件率；均值 NLL 及解析梯度。

所有候选相同 θ∈[0.1,200]、β∈[0.05,5]、p0∈[0,1−1e−12]。相对旧 θ 下限2统一放宽到0.1以避免较小日均聚合尺度被预先截断，允许 p0=0；这不是根据排名改变范围。实际五指标支持范围在拟合前写入 aggregation_summary.csv。边界命中和 θ 超出支持区间分别标记，不能将 θ 解释为已观察到的物理阈值。

每次训练13初值：该训练正 A 的75/90/98分位数 × β(0.25,0.6) × 训练率倍数(0.25,0.8)，加固定合法点(40,0.27,0.0014)。统一 L-BFGS-B，maxiter600/maxls40/ftol1e−13/gtol1e−9。最优候选未满足收敛/投影梯度/初值似然/非退化条件时最多两次 Powell，每次 maxiter300、maxfev3000。详细数值规则见 experiment.json。先完成 A01 wthr_gt1000 全样本+五训练折六项诊断，原规则相同则直接纳入240项，不额外重算。

有效性须同时满足 success、投影梯度≤1e−5、不差于任何已评价初值/解（总NLL容差1e−5）、不差于训练常数率、预测标准差≥1e−8和训练两类存在。最小NLL为选择依据，不能仅凭 success。NLL相差≤0.01的终点若θ或β相差倍数>1.25，或命中参数边界，保守标记弱识别。该筛查不是完整识别证明。无效解保留为诊断，不用常数代填、不用于有效排名。全样本参数不进入CV。

## 评价标准先于候选性能

主任务 any_gt100，重要次级 wthr_gt100，其余六项完整报告。所有折外行等权池化 Brier；聚合比较以本轮修复后 A01 为对照，原 A01 只在修复表中另列。另报逐折方向、相对训练折事件率常数预测的 BSS。八任务相对改善等权均值只是次级摘要，任一相关无效则标明无效，不删项重定主要任务。

不设新的5%或其他采用门槛；比较绝对/相对量级、跨折方向、条件区间、校准和代价。不能因微小领先就自动采用，也不因不显著就认定等效。固定OOF、整LAD配对bootstrap1000次，种子20260909，同样抽样用于相对和绝对改善区间、保留行权重；不包括重训、候选选择或共享风暴/日期的全部不确定性。

每任务五候选有效OOF预测合并生成共同十分位边界，补0/1、去重，同值不拆箱。精确CSV round_trip回读，searchsorted(side=right)；空箱n=0、频率NaN，n<100只画散点且不连线，不删除。共同全范围坐标+共同放大坐标；加权分箱校准RMSE。发生率—聚合曲线另外输出，不将不同聚合下相同m/s数值或θ位移视作物理阈值变化。

不增加天气查询、预测器、模型形式、时间划分；不改Word、不覆盖历史，不自动撤出District-day正文章节。按用户最新指令输出普通时间戳目录，不生成回传压缩包。后续采用与文字修改交由人工和agent联合审查。
'''
    (out/'PROTOCOL.md').write_text(protocol_text, encoding='utf-8')
    event('Protocol frozen before candidate performance', sha256=digest(out/'PROTOCOL.md'))
    panel = read(inputs['panel_grid.csv']); folds = read(inputs['lad_folds.csv'])
    if len(panel) != 121656 or panel.duplicated(['LAD21CD', 'date']).any() or panel.LAD21CD.nunique() != 111:
        raise ValueError('Panel row keys invalid')
    if folds.LAD21CD.duplicated().any() or len(folds) != 111 or set(folds.fold) != set(range(5)):
        raise ValueError('Original LAD folds invalid')
    dates = pd.date_range(START, END).strftime('%Y-%m-%d')
    expected = pd.MultiIndex.from_product([sorted(panel.LAD21CD.unique()), dates], names=['LAD21CD', 'date'])
    if set(pd.MultiIndex.from_frame(panel[['LAD21CD', 'date']])) != set(expected): raise ValueError('LAD/date product mismatch')
    if not np.isin(panel[TARGETS].to_numpy(), [0, 1]).all(): raise ValueError('Non-binary labels')
    tables = []
    for p in raw:
        lad = p.name.removesuffix('.json.gz')
        with gzip.open(p, 'rt', encoding='utf-8') as f: envelope = json.load(f)
        request = envelope['request']
        if any(request[k] != v for k, v in dict(models='era5', hourly=FIELD, timezone='GMT', wind_speed_unit='ms', start_date=START, end_date=END).items()):
            raise ValueError(f'{lad}: source request definition mismatch')
        frame = parse_hourly(envelope['response'], lad)
        values = np.asarray(envelope['response']['hourly'][FIELD], dtype=float).reshape(-1, 24)
        frame[CANDIDATES] = aggregate(values); tables.append(frame)
    weather = pd.concat(tables, ignore_index=True)
    oldgrid = read(inputs['grid_daily.csv'])
    check = weather.merge(oldgrid, on=['LAD21CD', 'date'], validate='one_to_one', suffixes=('', '_original'))
    if len(check) != len(panel) or not np.allclose(check.gust_grid, check.gust_grid_original, atol=1e-12, rtol=0):
        raise ValueError('A01 does not reconstruct original daily maximum')
    for col in ['hours', 'grid_lat', 'grid_lon']:
        if not np.array_equal(check[col], check[col+'_original']): raise ValueError('Hours/grid position changed')
    daily = panel[['LAD21CD', 'date', *TARGETS]].merge(weather, on=['LAD21CD', 'date'], how='left', validate='one_to_one', sort=False)
    daily = daily.merge(folds, on='LAD21CD', how='left', validate='many_to_one', sort=False)
    if not daily[TARGETS].equals(panel[TARGETS]) or daily[CANDIDATES+['fold']].isna().any().any(): raise ValueError('Alignment/labels changed')
    if not np.allclose(daily[CANDIDATES[0]], panel.gust, atol=1e-12, rtol=0): raise ValueError('Panel daily maximum mismatch')
    daily.to_csv(out/'daily_aggregations.csv.gz', index=False)
    summary = daily[CANDIDATES].describe(percentiles=[.01, .05, .5, .9, .95, .99]).T
    summary['n_zero'] = (daily[CANDIDATES] == 0).sum()
    summary['a01_max_abs_error'] = [float(np.max(np.abs(check.gust_grid-check.gust_grid_original))), np.nan, np.nan, np.nan, np.nan]
    summary.to_csv(out/'aggregation_summary.csv', index_label='candidate')
    daily[CANDIDATES].corr().to_csv(out/'aggregation_correlation.csv', index_label='candidate')
    save(out/'data_validation.json', dict(rows=len(daily), lads=daily.LAD21CD.nunique(), days=1096, raw_files=len(raw),
         hourly_values=2919744, hours_per_day=24, a01_max_abs_error=float(np.max(np.abs(check.gust_grid-check.gust_grid_original))),
         shared_keys_labels_hours_folds=True, same_returned_grids=True, network_requests=0))
    event('Hourly validation and five aggregations completed; supports recorded before fits')
    summaries, candidates, fitted = [], [], {}
    def do_fit(c, t, scope):
        key = (c, t, scope)
        if key in fitted: return fitted[key]
        m = np.ones(len(daily), dtype=bool) if scope == 'full' else daily.fold.to_numpy() != int(scope.split('_')[1])
        f, records = fit(daily.loc[m, c].to_numpy(), daily.loc[m, t].to_numpy())
        info = dict(candidate=c, target=t, scope=scope)
        f = dict(**info, **f); fitted[key] = f; summaries.append(f)
        for r in records:
            r.update(info); r['selected'] = bool(r['method'] == f['method'] and r['start'] == f['start'])
            r['selection_reason'] = f['selection_reason']; candidates.append(r)
        with (out/'fit_checkpoint.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(dict(summary=f, candidates=records), default=str)+'\n')
        event(f'Fit {len(summaries)}/240 {c} {t} {scope}', valid=f['valid'], nll=f['nll'], weak=f['weak_identification'])
        return f
    scopes = ['full']+[f'fold_{i}' for i in range(5)]
    rare = [do_fit(CANDIDATES[0], 'wthr_gt1000', s) for s in scopes]
    save(out/'rare_repair_gate.json', dict(completed_at=now(), results=rare, all_valid=all(f['valid'] for f in rare),
         rule='Same optimizer is frozen for all targets; unsuccessful fits remain explicitly invalid and other tasks continue'))
    event('A01 rare-task six-fit repair diagnosis complete', all_valid=all(f['valid'] for f in rare))
    for c in CANDIDATES:
        for t in TARGETS:
            for scope in scopes: do_fit(c, t, scope)
    fits = pd.DataFrame(summaries); fits.to_csv(out/'fit_summary.csv', index=False); fits.to_csv(out/'parameters.csv', index=False)
    pd.DataFrame(candidates).to_csv(out/'optimizer_candidates.csv.gz', index=False)
    oof = daily[['LAD21CD', 'date', 'fold', *TARGETS]].copy()
    for t in TARGETS:
        constant = np.full(len(daily), np.nan)
        for fold in range(5):
            m = daily.fold.to_numpy() == fold; constant[m] = daily.loc[~m, t].mean()
        oof[t+'_constant'] = constant
        for c in CANDIDATES:
            p = np.full(len(daily), np.nan)
            for fold in range(5):
                m = daily.fold.to_numpy() == fold; f = fitted[c, t, f'fold_{fold}']
                p[m] = probabilities(daily.loc[m, c], **{k: f[k] for k in ['theta', 'beta', 'p0']})
            oof[t+'__'+c] = p
    oof.to_csv(out/'oof_predictions.csv.gz', index=False)
    metrics, fold_metrics, bins, edges = evaluate(oof, fits)
    metrics.to_csv(out/'metrics.csv', index=False); fold_metrics.to_csv(out/'fold_metrics.csv', index=False)
    bins.to_csv(out/'calibration_bins.csv', index=False); save(out/'calibration_edges.json', edges)
    uncertainty(oof, metrics).to_csv(out/'paired_uncertainty.csv', index=False)
    old_oof = read(inputs['oof_predictions.csv.gz']); old_params = read(inputs['parameters_long.csv'])
    old_diag = json.loads(inputs['optimizer_diagnostics.json'].read_text(encoding='utf-8'))
    if not old_oof[['LAD21CD', 'date', 'fold']].equals(oof[['LAD21CD', 'date', 'fold']]): raise ValueError('Old/new OOF row/fold mismatch')
    repair = []
    for t in TARGETS:
        if not np.array_equal(old_oof[t+'_y'], oof[t]): raise ValueError('Old/new OOF target mismatch')
        bs_old = np.mean((old_oof[t+'_era5_daily_max']-oof[t])**2)
        bs_new = metrics[(metrics.target == t) & (metrics.candidate == CANDIDATES[0])].brier.iloc[0]
        for scope in scopes:
            old = next(d for d in old_diag if d['target'] == t and d['version'] == 'era5_daily_max' and d['scope'] == scope)
            f = fitted[CANDIDATES[0], t, scope]
            m = np.ones(len(daily), dtype=bool) if scope == 'full' else daily.fold.to_numpy() != int(scope.split('_')[1])
            obj = Objective(daily.loc[m, CANDIDATES[0]], daily.loc[m, t])
            r = dict(target=t, scope=scope, old_nll=old['nll'], repaired_nll=f['nll'], old_success=old['success'],
                     repaired_valid=f['valid'], known_legal_nll=obj.nll(obj.encode(40., .27, .0014)),
                     old_oof_brier=bs_old, repaired_oof_brier=bs_new, repair_absolute_gain=bs_old-bs_new,
                     repaired_prediction_std=f['prediction_std'])
            if scope == 'full':
                op = old_params[(old_params.target == t) & (old_params.version == 'era5_daily_max')].iloc[0]
                r.update({f'old_{k}': op[k] for k in ['theta', 'beta', 'p0']})
            r.update({f'repaired_{k}': f[k] for k in ['theta', 'beta', 'p0']}); repair.append(r)
    pd.DataFrame(repair).to_csv(out/'baseline_repair_comparison.csv', index=False)
    event('Metrics, paired uncertainty, calibration bins and separate repair comparisons saved')
    plot_results(out, daily, fits, bins)
    validate_saved(out, daily, folds, fits, metrics, event)
    from analysis_new.dd_agg01_report import write_report
    write_report(out, protocol)
    event('All fixed analyses and report completed', valid_fits=int(fits.valid.sum()), total_fits=len(fits))
    save(out/'inventory.json', dict(created_at=now(), inputs=provenance, files=[dict(path=str(p.relative_to(out)).replace('\\', '/'),
         bytes=p.stat().st_size, sha256=digest(p)) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'inventory.json']))


def validate_saved(out, daily, folds, fits, metrics, event):
    """Only the experiment's required checks, not the historical whole-package audit."""
    oof = read(out/'oof_predictions.csv.gz'); saved = read(out/'daily_aggregations.csv.gz')
    checks = dict(fits_240=len(fits) == 240 and not fits.duplicated(['candidate', 'target', 'scope']).any(),
                  daily_roundtrip=np.array_equal(saved[CANDIDATES], daily[CANDIDATES]),
                  shared_labels=np.array_equal(saved[TARGETS], oof[TARGETS]),
                  lad_single_fold=bool(oof.groupby('LAD21CD').fold.nunique().eq(1).all()),
                  original_folds=np.array_equal(oof.fold, oof.LAD21CD.map(folds.set_index('LAD21CD').fold)),
                  predictions_finite=bool(np.isfinite(oof.filter(like='__').to_numpy()).all()))
    for t in TARGETS:
        for fold in range(5):
            m = oof.fold == fold
            checks[f'constant_{t}_{fold}'] = bool(np.all(oof.loc[m, t+'_constant'].to_numpy() == oof.loc[~m, t].mean()))
        for c in CANDIDATES:
            a = np.mean((oof[t+'__'+c]-oof[t])**2)
            b = metrics[(metrics.target == t) & (metrics.candidate == c)].brier.iloc[0]
            checks[f'brier_{t}_{c}'] = bool(np.isclose(a, b, atol=1e-15, rtol=0))
    _, _, recreated, _ = evaluate(oof, fits); saved_bins = read(out/'calibration_bins.csv')
    checks['calibration_counts_roundtrip'] = np.array_equal(recreated[['n', 'events']], saved_bins[['n', 'events']])
    checks['calibration_numbers_roundtrip'] = bool(np.allclose(recreated[['lower', 'upper', 'mean_probability', 'observed_frequency']],
          saved_bins[['lower', 'upper', 'mean_probability', 'observed_frequency']], equal_nan=True, atol=1e-15, rtol=0))
    repair = read(out/'baseline_repair_comparison.csv'); rare = repair[repair.target == 'wthr_gt1000']
    # A repair failure is a scientific invalidity, not a reason to hide other completed tasks.
    repair_resolved = bool(rare.repaired_valid.all() and (rare.repaired_nll <= rare.known_legal_nll+1e-5).all())
    save(out/'validation.json', dict(checked_at=now(), checks={k: bool(v) for k, v in checks.items()},
         all_checks_passed=all(checks.values()), valid_fits=int(fits.valid.sum()), invalid_fits=int((~fits.valid).sum()),
         weak_identification=int(fits.weak_identification.sum()), rare_counterexample_resolved=repair_resolved))
    if not all(checks.values()): raise AssertionError('Saved-output validation failed: '+str([k for k, v in checks.items() if not v]))
    event('Targeted saved-output validation passed', checks=len(checks), rare_counterexample_resolved=repair_resolved)


if __name__ == '__main__':
    run_experiment(Path(os.environ['NEW_ANALYSIS_RUN']), json.loads(os.environ.get('DD_AGG01_SETTINGS', '{}')))
