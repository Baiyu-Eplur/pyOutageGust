"""Seven unchanged UTC storm windows; slices of G, never storm-specific fitting."""
import numpy as np
import pandas as pd
from .gi_core import ROOT,cm,ID,C,D,design,scores
from .f02_cov import csv,read,js
from .exporters import literal,table
from .mapping import write_json,digest

STORMS=literal('scripts/c02_c08_repair_20260905/figure9_storm_validation.py','STORMS')
COLORS=literal('scripts/c02_c08_repair_20260905/figure9_storm_validation.py','STORM_COLORS')

def compute(stage,groot,requirement):
    samples=cm.samples();e=samples['E0_all'];r=samples['R0c_all'];pre=read(ROOT/cm.R0)
    # The exact combined cap is also the largest included value. C01 changes
    # dates/weather, not duration. Check the entire accepted membership instead
    # of using the rounded 192.08 in old logs or a storm-specific quantile.
    cap_source='results/pretest/archive/20260909154556/results/final_combined_analysis/raw/step0_verification.json'
    cap=js(ROOT/cap_source)['combined_p99_cap_hours_recomputed']
    assert np.isclose(cap,pre[D].max(),rtol=0,atol=1e-10)
    eligible=e[D].gt(0)&e[D].le(cap)&e[C].gt(0)
    assert set(e.loc[eligible,ID])==set(r[ID])
    master=read(groot/'data/GI_PREDICTIONS.csv.gz')
    base=master[master.combination.isin(['E0_all','R0c_all'])&master.model_id.eq('final')].copy()
    coeff=read(groot/'data/GI_COEFFICIENTS.csv')
    tail=e[e[C].gt(0)&e[D].gt(cap)].copy();tail['customers_v2_log1p']=np.log1p(tail[C]);tail['y']=np.log(tail[D])
    _,X=design(r,tail,'R0c_all','final');b=coeff[(coeff.combination=='R0c_all')&coeff.model_id.eq('final')].set_index('term').coef
    X=X.reindex(columns=b.index,fill_value=0.)
    assert np.isfinite(X).all().all()
    td=pd.DataFrame(dict(observation_id=tail[ID],combination='R0c_all',date=pd.to_datetime(tail.incident_date_utc).dt.date.astype(str),
        LAD21CD=tail.LAD21CD,gust=tail.gust_0h,y=tail.y,prediction=X.to_numpy()@b.to_numpy(),prediction_type='display_only',model_id='final',fold=-1,valid=True))
    td['residual']=td.y-td.prediction;td['response_scale']='natural_log_duration_hours';td['training_source']='G GI_PREPROCESSING.json:R0c_all/final/full; same frozen full coefficients'
    allrows=pd.concat([base,td],ignore_index=True);allrows['excluded_from_primary_metrics']=allrows.prediction_type.eq('display_only')
    allrows['display_marker']=np.where(allrows.excluded_from_primary_metrics,'open_triangle','point')
    events=e[[ID,C,D,'incident_date_utc','LAD21CD']].copy()
    events['recovery_status']=np.select([events[C].le(0),~np.isfinite(events[D])|events[D].le(0),events[D].gt(cap)],
        ['zero_or_negative_customers','nonpositive_or_missing_duration','above_formal_combined_p99'],default='included_final')
    events['exactly_one_hour']=events[D].eq(1)
    # Exactly one hour is an observed value, not an operational placeholder label.
    events['date']=pd.to_datetime(events.incident_date_utc).dt.date.astype(str)
    slices=[];flags=[];counts=[];windows=[]
    for storm,(start,end) in STORMS.items():
        windows.append(dict(storm=storm,start=start,end=end,timezone='UTC existing incident date',endpoints='inclusive date bounds',overlap='each window separately; union deduplicated by observation ID'))
        s=allrows[allrows.date.between(start,end)].copy();s['storm']=storm;slices.append(s)
        ev=events[events.date.between(start,end)].copy();ev['storm']=storm;flags.append(ev)
    rows=pd.concat(slices,ignore_index=True);flags=pd.concat(flags,ignore_index=True)
    union=rows.drop_duplicates(['combination','prediction_type','observation_id']).copy();union['storm']='UNION_DEDUPLICATED'
    rowall=pd.concat([rows,union],ignore_index=True)
    event_union=flags.drop_duplicates(ID).copy();event_union['storm']='UNION_DEDUPLICATED'
    allflags=pd.concat([flags,event_union],ignore_index=True)
    for storm,ev in allflags.groupby('storm',sort=False):
        status=ev.recovery_status.value_counts()
        counts.append(dict(storm=storm,exposure_n=len(ev),recovery_before_duration_cap_positive_customers=int((ev[C].gt(0)&ev[D].gt(0)&np.isfinite(ev[D])).sum()),
            recovery_final_n=int(status.get('included_final',0)),excluded_zero_or_negative_customers=int(status.get('zero_or_negative_customers',0)),
            excluded_duration=int(status.get('nonpositive_or_missing_duration',0)),display_only_above_cap=int(status.get('above_formal_combined_p99',0)),
            exactly_one_hour_positive_customer_included=int((ev.recovery_status.eq('included_final')&ev.exactly_one_hour).sum()),
            missing_covariates_in_exposure_source=0,source_scope='accepted complete-covariate E0 universe; upstream missing-customers rows not part of this universe',cap_hours=cap))
    metrics=[]
    for (storm,combo,kind),d in rowall.groupby(['storm','combination','prediction_type'],sort=False):
        metrics.append(dict(storm=storm,combination=combo,prediction_type=kind,excluded_from_primary_metrics=kind=='display_only',**scores(d.y,d.prediction),correlation_p_value='not calculated'))
    table(stage,'GI_STORM_SAMPLES',pd.DataFrame(counts),requirement)
    table(stage,'GI_STORM_METRICS',pd.DataFrame(metrics),requirement)
    csv(stage/'data/GI_STORM_WINDOWS.csv',pd.DataFrame(windows))
    csv(stage/'data/GI_STORM_PREDICTIONS.csv.gz',rowall);csv(stage/'data/GI_STORM_EXCLUSIONS.csv.gz',allflags)
    checks=dict(formal_recovery_ID_membership_exact=True,cap_matches_saved_combined_and_actual_max=True,
        union_prediction_keys_unique=not union.duplicated(['combination','prediction_type','observation_id']).any(),
        no_display_only_in_primary=bool(rowall.loc[rowall.prediction_type.isin(['in_sample','LAD_OOF']),'excluded_from_primary_metrics'].eq(False).all()),
        display_only_positive_customers_and_above_cap=bool(tail[C].gt(0).all() and tail[D].gt(cap).all()),
        prediction_rows_finite=bool(np.isfinite(rowall[['y','prediction']]).all().all()),
        exclusion_counts_partition_exposure=all(v['exposure_n']==v['recovery_final_n']+v['excluded_zero_or_negative_customers']+v['excluded_duration']+v['display_only_above_cap'] for v in counts))
    write_json(stage/'data/GI_STORM_SOURCE.json',dict(shared_predictions='results/Appendix/G/data/GI_PREDICTIONS.csv.gz',sha256=digest(groot/'data/GI_PREDICTIONS.csv.gz'),
        input_scope='current accepted E0 incidents; current R0c membership exactly checked; no raw event reconstruction',
        upstream_missing_customers='16 records absent from accepted E0 cannot be assigned to windows from this input; not silently counted as zero and no raw reconstruction initiated',
        formal_cap=cap,cap_source=cap_source,cap_sha256=digest(ROOT/cap_source),
        cap_rule='original combined positive-duration WT p99 before dropping missing customers; final recovery then positive customers; no storm quantile',
        current_compatibility='reconstructed membership on all E0 equals formal positive R0c IDs exactly',
        observed_one_hour='reported characteristic, not a verified operational placeholder flag',
        display_only='positive customers, finite model covariates and duration above original cap; no primary metric inclusion',
        response='natural log scales; eta directly; no exponentiation or double transform',
        prediction_identity='full-study fixed final OLS for in_sample/display_only; G fixed LAD_OOF slices supplement; not temporal holdout'))
    write_json(stage/'logs/GI_TECHNICAL_CHECKS.json',checks)
    return rowall,pd.DataFrame(metrics),pd.DataFrame(counts),checks

def figure(stage,rows):
    from .gi_outputs import plt,apply_style,save_fig
    apply_style();fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,combo,title in zip(axes,['E0_all','R0c_all'],['Exposure: log(1+customers)','Recovery: log(duration, h)']):
        for (storm,_),color in zip(STORMS.items(),COLORS):
            d=rows[rows.storm.eq(storm)&rows.combination.eq(combo)&rows.prediction_type.eq('in_sample')]
            ax.scatter(d.y,d.prediction,s=8,color=color,alpha=.45,label=storm,rasterized=True)
            t=rows[rows.storm.eq(storm)&rows.combination.eq(combo)&rows.prediction_type.eq('display_only')]
            ax.scatter(t.y,t.prediction,s=27,marker='^',facecolors='none',edgecolors=color,linewidths=.8)
        v=rows[rows.combination.eq(combo)&rows.prediction_type.isin(['in_sample','display_only'])]
        low=min(v.y.min(),v.prediction.min());high=max(v.y.max(),v.prediction.max());ax.plot([low,high],[low,high],'k--',lw=.8)
        ax.set(xlabel='Observed log response',ylabel='Final fitted log response',title=title+'\nIn-sample descriptive; seven fixed windows')
        if combo=='E0_all':ax.legend(fontsize=7,ncol=2)
        else:ax.scatter([],[],s=27,marker='^',facecolors='none',edgecolors='k',label='Above cap: display only');ax.legend(fontsize=7,loc='upper left')
    fig.tight_layout();save_fig(fig,stage/'figures','GI_STORM_FINAL_SCATTER',dpi_png=200);plt.close(fig)
