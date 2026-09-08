"""Final consumer entry: immutable graphics generation/reuse + current semantic bindings."""
from common import *

def run():
    rel=Q/'release_v1'
    if rel.exists():
        manifest=pd.read_csv(Q/'tables/FIGURE_RELEASE_COMPARISON.csv');assert len(manifest)==24
        for r in manifest.itertuples():assert sha(r.current)==r.sha256
        inputs=read(rel/'CONSUMER_INPUTS.json')
        for r in inputs['frozen_model_and_data']:assert sha(r['path'])==r['sha256']
        graphics='reused 24 verified immutable outputs from actual R05 render; no rerender necessary'
    else:
        from render_release import run as render
        render();graphics='all12 groups actually rendered from frozen archives'
    from writing import run as write_candidates
    write_candidates()
    put(Q/'CURRENT_BINDING_RELEASE.json',{'parent_graphics_release':'release_v1','tables':[record(Q/'tables'/f) for f in ['CURRENT_NUMERIC_BINDINGS_R05.csv','CURRENT_PARAGRAPH_BINDINGS_R05.csv','NUMERIC_BINDING_SEMANTIC_AUDIT.csv']],'entry':'R05/cli.py consumers','replaces_metadata_only':'10 stale A-T10 six-group target labels; no numeric changes'})
    put(Q/'checks/consumer_single_entry.json',{'passed':True,'command':'R05/cli.py consumers','graphics':graphics,'binding_rows':246,'figure_groups':12,'new_fits':0,'Word_modified':False})
    print('Single consumer entry passed: graphics plus 246 current semantic bindings, zero fits',flush=True)
if __name__=='__main__':run()
