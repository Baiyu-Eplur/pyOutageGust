"""Build all four formerly missing document-table inputs from this run's results."""
import json
import math
import pandas as pd
from analysis_new.runtime import ROOT, DATA

RES = ROOT/'results'


def read(name):
    return json.loads((RES/name).read_text(encoding='utf-8'))


def write(name, value):
    (RES/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def markdown(frame):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    rows = [list(frame.columns), ['---']*len(frame.columns), *frame.itertuples(index=False, name=None)]
    return '\n'.join('| '+' | '.join(cell(v) for v in row)+' |' for row in rows)


def label(term, knots):
    a = f'{knots[0]:g}'
    names = {'z_temperature_0h': 'Temperature (z)', 'z_gust_pressure': 'Gust × pressure',
             'z_temperature_sq': 'Temperature squared (z²)', 'z_gust_0h': 'Gust (linear, z)',
             'z_gust_sq': 'Gust squared (z²)', 'z_customers_v2_log1p': 'log(1+customers) (z)',
             'z_cust_sq': 'log(1+customers) squared', 'z_gust_precip': 'Gust × precipitation',
             'gust_low': f'Gust below {a} m/s (per m/s)'}
    if len(knots) == 2:
        b = f'{knots[1]:g}'
        names['gust_ramp'] = f'Gust ramp {a}–{b} m/s (per m/s; constant above {b})'
        names['low'] = names['gust_low']; names['ramp'] = names['gust_ramp']
    if term.startswith('hinge_'):
        return f'Gust hinge above {term[6:]} m/s (per m/s)'
    if term.startswith('gust_single_'):
        return f'Gust hinge above {term[12:]} m/s (per m/s)'
    if term.startswith('gust_hinge_'):
        return f'Gust hinge above {term[11:]} m/s (per m/s)'
    return names.get(term, term)


def main():
    kn = read('model_selection/knots.json')
    t2 = pd.read_csv(RES/'final_models/table2_replacement.csv')
    rows = [[r.margin, label(r.term, kn[r.margin]['selected']), f'{r.coef:.4f}', f'{r.se_lad:.4f}',
             f'{r.se_twoway:.4f}', f'{r.p_twoway_tG1:.3g}'] for r in t2.itertuples()]
    write('figures/t2_rows.json', rows)
    wo = read('weather_only/weather_only_summary.json')
    rows = []
    for margin in ['E0', 'R0c']:
        table = pd.read_csv(RES/f'weather_only/{margin}_weather_final_twoway.csv')
        knots = wo[margin]['knots']['selected']
        for r in table[table.term.str.contains('gust|temperature|cust')].itertuples():
            rows.append([margin, label(r.term, knots), f'{r.coef:.4f}', f'{r.se:.4f}', f'{r.p_t_G1:.3g}'])
    write('figures/wo_rows.json', rows)
    dd = read('final_models/district_day_fragility.json')
    rows = []
    for key, f in dd['fits'].items():
        if 'lognormal' not in f:
            continue
        ln = f['lognormal']
        rows.append([f['label'], 'any cause' if key.startswith('any_') else 'weather-attributed',
                     f'{f["base_rate"]:.3f}', f'{ln["p0"]:.3f}', f'{ln["theta"]:.1f}', f'{ln["beta"]:.2f}'])
    write('figures/frag_rows.json', rows)
    pvo = pd.read_csv(RES/'model_selection/predicted_vs_observed_summary.csv')
    rows = []
    for (margin, spec), frame in pvo.groupby(['model', 'spec'], sort=False):
        ins = frame[frame.kind == 'in-sample'].iloc[0]
        cv = frame[frame.kind == 'LAD-CV out-of-fold'].iloc[0]
        rows.append([margin, spec, f'{ins.rmse:.4f}', f'{ins.r2:.4f}', f'{cv.rmse:.4f}',
                     f'{cv.r2:.4f}', f'{cv["corr"]:.3f}', f'{cv.slope:.2f}'])
    write('figures/pvo_rows.json', rows)
    # Data-driven descriptives replace hand-entered values in the long-paper template.
    e = pd.read_csv(DATA/'combined_E0_final.csv'); r = pd.read_csv(DATA/'combined_R0c_final.csv')
    r = r[r.customers_v2_event_excl_reinterruptions > 0]
    columns = [e.customers_v2_event_excl_reinterruptions, e.log1p_customers_v2,
               r.duration_B_full_span_hours, r.log_duration_B_full_span_hours]
    desc = [[stat]+[f'{getattr(c, method)():.3f}' for c in columns]
            for stat, method in [('Mean', 'mean'), ('Median', 'median'), ('SD', 'std'), ('Min', 'min'), ('Max', 'max')]]
    write('paper/descriptive_rows.json', desc)
    comparisons = pd.read_csv(RES/'model_selection/all_model_comparison.csv')
    metrics = {}
    for margin in ['E0', 'R0c']:
        base = comparisons[comparisons.model == margin].set_index('spec')
        k = kn[margin]
        gaussian_constant = k['n']*(1+math.log(2*math.pi))
        values = [(float(base.loc[s, 'bic']), float(base.loc[s, 'cv_lad'])) for s in
                  ['M5_+year_month_FE', 'A1_gust_cubic', 'A2_log_gust', 'A4_gust_bins']]
        values += [(k['one_knot']['bic']+gaussian_constant, k['nested_cv']['rmse_one_knot']),
                   (k['two_knot']['bic']+gaussian_constant, k['nested_cv']['rmse_two_knot'])]
        if margin == 'E0':
            ramp = read('model_selection/ramp_model.json')['all']
            values.append((ramp['ramp']['bic']+gaussian_constant, ramp['nested_cv']['ramp']))
        else:
            values.append(None)  # plateau R0c uses a different, positive-customer sample
        best = min(v[0] for v in values if v is not None)
        values.append((float(base.loc['A6_M5_+LAD_FE', 'bic']), float(base.loc['A6_M5_+LAD_FE', 'cv_lad'])))
        metrics[margin] = [([f'{v[0]-best:+.1f}', f'{v[1]:.4f}'] if v else ['different sample', '—']) for v in values]
    spec_labels = ['Quadratic gust (M5)', 'Cubic gust', 'Log gust', 'Gust percentile steps',
                   'One free hinge (nested knot CV)', 'Two free hinges (nested knot CV)',
                   'E0 plateau plus temperature squared (nested knot CV)', 'Quadratic plus LAD fixed effects']
    write('paper/specification_rows.json', [[name, *metrics['E0'][i], *metrics['R0c'][i]] for i, name in enumerate(spec_labels)])
    lines = ['# 本次独立计算结果', '', '数值来自本次运行；模板论文中的手填文字不作为计算依据。', '',
             f'- E0 样本：{len(e):,}；最终 R0c 正客户数样本：{len(r):,}。',
             f'- E0 平台主效应结点：{kn["E0"]["selected"]} m/s；R0c 探索单结点：{kn["R0c"]["selected"]} m/s。',
             f'- district-day 面板：{dd["n_district_days"]:,} 行。', '', '## 最终回归', '', markdown(t2),
             '', '## 区域日脆弱性', '', markdown(pd.DataFrame(read('figures/frag_rows.json'), columns=['阈值','归因','发生率','p0','theta','beta'])),
             '', '## 结果路径', '', '- model_selection/：模型比较、结点、bootstrap、条件脆弱性。',
             '- final_models/：最终回归、区域日面板与脆弱性。', '- weather_only/：天气归因子样本回归。',
             '- figures/：重新计算的图表。', '- paper/：分解、时间分样、论文草稿。']
    (RES/'COMPUTED_RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (RES/'MODEL_SELECTION_REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
