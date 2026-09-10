"""Bounded post-run checks and supplementary views of saved DD-AGG01 results.

No model fitting, new split, changed bins, weather access, or historical writes.
Run with the project Python from the project root. Files go beside this script.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
OUT=PROJECT/'results/new/20260909231634/results/dd_agg01'


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name): return pd.read_csv(OUT/name,float_precision='round_trip')


def main():
    inventory=json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
    hash_ok=all(digest(OUT/r['path'])==r['sha256'] for r in inventory['files'])
    fits=read('fit_summary.csv'); candidates=read('optimizer_candidates.csv.gz'); bins=read('calibration_bins.csv')
    keys=['candidate','target','scope']
    legal_min=candidates.groupby(keys).nll.min()
    selected=fits.set_index(keys).nll.reindex(legal_min.index)
    best_ok=bool((selected<=legal_min+1e-5).all())
    checks=dict(output_inventory_hashes_match=hash_ok, inventory_files=len(inventory['files']),
                target_fits=len(fits), candidate_rows=len(candidates), selected_rows=int(candidates.selected.sum()),
                min_evaluated_legal_nll_not_better=best_ok,
                all_fit_groups_have_13_initials=bool(candidates[candidates.method=='initial'].groupby(keys).size().eq(13).all()),
                max_projected_gradient=float(fits.projected_gradient.max()),
                full_theta_outside_support=int(fits[fits.scope=='full'].theta_outside_support.sum()))
    contributions=[]
    for (target,candidate), b in bins.groupby(['target','candidate']):
        terms=b.n*(b.mean_probability-b.observed_frequency)**2
        contributions.append(dict(target=target,candidate=candidate,sparse_nonempty_bins=int(((b.n>0)&(b.n<100)).sum()),
                                  sparse_share_of_calibration_squared_error=float(terms[b.n<100].sum()/terms.sum())))
    pd.DataFrame(contributions).to_csv(HERE/'calibration_support_review.csv',index=False)
    # Original full-range figures stay immutable. These supplementary views zoom
    # only the well-supported bins, retaining a full-range companion and counts.
    plot_records=[]
    for target in ['any_gt100','wthr_gt100','wthr_gt1000']:
        b=bins[bins.target==target]; dense=b[b.n>=100]
        limit=min(1.,1.15*float(dense[['mean_probability','observed_frequency']].max().max()))
        fig,axes=plt.subplots(1,2,figsize=(12,5)); colors=plt.get_cmap('tab10').colors
        outside=((b.n>0)&((b.mean_probability>limit)|(b.observed_frequency>limit))).sum()
        for ax,lim in zip(axes,[1.,limit]):
            ax.plot([0,lim],[0,lim],'k--',lw=1)
            for j,c in enumerate(b.candidate.unique()):
                r=b[b.candidate==c]
                ax.plot(r.mean_probability.where(r.n>=100),r.observed_frequency.where(r.n>=100),'-o',
                        color=colors[j],markersize=4,label=c)
                sparse=r[(r.n>0)&(r.n<100)]
                ax.scatter(sparse.mean_probability,sparse.observed_frequency,marker='x',s=60,color=colors[j])
                if lim==1.:
                    for x in sparse.itertuples(): ax.annotate(f'n={x.n}',(x.mean_probability,x.observed_frequency),xytext=(5,-16),textcoords='offset points',fontsize=8)
            ax.set(xlim=(0,lim),ylim=(0,lim),xlabel='Mean OOF probability',ylabel='Observed frequency')
            ax.grid(alpha=.2); ax.set_aspect('equal',adjustable='box')
        axes[0].set_title('Full range; all nonempty bins retained')
        axes[1].set_title(f'Supported-bin zoom; {outside} tail point(s) in left panel')
        axes[1].legend(fontsize=7)
        fig.suptitle(target+': same saved bins; crosses denote n<100; no refit')
        fig.tight_layout(); fig.savefig(HERE/f'calibration_{target}_supported_view.png',dpi=160); plt.close(fig)
        plot_records.append(dict(target=target,zoom_upper=limit,tail_points_outside_zoom=int(outside),bins_unchanged=True))
    checks.update(checked_at=datetime.now().astimezone().isoformat(),supplementary_views=plot_records,
                  original_source_inventory_sha256=digest(OUT/'inventory.json'),no_refit=True,no_weather_requests=True)
    (HERE/'review_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    if not hash_ok or not best_ok or not checks['all_fit_groups_have_13_initials']: raise AssertionError(checks)
    print(json.dumps(checks,indent=2))


if __name__=='__main__': main()
