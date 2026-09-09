"""Complete the missing handoff between profiled hinges and final E0 plateau.

The published review overwrote selected manually. Here retain the original
selection and carry forward the independently profiled plateau as the explicit
E0 replication specification. This is a specification choice, not a new test.
"""
import json
from analysis_new.runtime import ROOT


def main():
    out = ROOT/'results/model_selection'
    path = out/'knots.json'
    knots = json.loads(path.read_text())
    ramp = json.loads((out/'ramp_model.json').read_text())
    e = knots['E0']
    e['unconstrained_selected'] = e['selected']
    e['selected'] = [ramp['all']['ramp']['k1'], ramp['all']['ramp']['k2']]
    e['form'] = 'three-segment plateau: free slope below k1, ramp k1-k2, constant above k2'
    e['final_selection_rule'] = 'Replicate advisor E0 plateau specification using its freshly profiled knots; original hinge selection retained separately.'
    e['conditional_scope'] = 'Main gust effect at mean pressure; retained gust-pressure interaction changes the high-gust slope at other pressures.'
    path.write_text(json.dumps(knots, indent=2), encoding='utf-8')
    print('Final computed knots:', {m: v['selected'] for m, v in knots.items()})
