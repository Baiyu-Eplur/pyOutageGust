"""Quantify optimizer drift in probability space on the plotted gust domain."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm


def main():
    p = argparse.ArgumentParser(); p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); rows = []; g = np.linspace(.5, 40, 10001)
    def read(root, name):
        return json.loads((root/'results'/name).read_text())
    def curve(f, i=0):
        theta = f['theta'][i] if isinstance(f['theta'], list) else f['theta']
        beta = f['beta'][i] if isinstance(f['beta'], list) else f['beta']
        floor = f.get('p0', 0.)
        return floor+(1-floor)*norm.cdf((np.log(g)-np.log(theta))/beta)
    ref = read(args.reference, 'model_selection/fragility_lognormal.json')
    own = read(args.run, 'model_selection/fragility_lognormal.json')
    for margin in ref:
        for model in ['lognormal_all_incidents', 'lognormal_weather_common_beta', 'lognormal_weather_free_beta']:
            for i in range(3):
                error = float(np.max(np.abs(curve(ref[margin][model], i)-curve(own[margin][model], i))))
                rows.append(dict(model=f'{margin}/{model}/{i}', max_absolute_probability_difference=error))
    ref = read(args.reference, 'final_models/district_day_fragility.json')
    own = read(args.run, 'final_models/district_day_fragility.json')
    for key in ref['fits']:
        if 'lognormal' not in ref['fits'][key]:
            continue
        r, o = ref['fits'][key]['lognormal'], own['fits'][key]['lognormal']
        rows.append(dict(model=f'district_day/{key}', max_absolute_probability_difference=float(np.max(np.abs(curve(r)-curve(o)))),
                         nll_absolute_difference=abs(r['nll']-o['nll'])))
    payload = dict(gust_domain_ms=[.5, 40], grid_points=len(g),
                   probability_tolerance=1e-4, curves=rows,
                   all_within_probability_tolerance=all(r['max_absolute_probability_difference'] <= 1e-4 for r in rows))
    args.output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print('Curves:', len(rows), 'largest probability difference:', max(r['max_absolute_probability_difference'] for r in rows))
    print('All within 1e-4 probability tolerance:', payload['all_within_probability_tolerance'])


if __name__ == '__main__':
    main()
