"""Existing H2/H3 evidence and descriptive bins only: never fit those models."""
import numpy as np
import pandas as pd
from scipy.stats import norm
from .catalog import ROOT,MAIN,E0,R0
from .gi_core import cm,BINS
from .f02_cov import read,js,csv
from .mapping import write_json,digest
from .exporters import table

def existing(stage,r):
    samples=cm.samples();records=[];freq=[];classrows=[]
    oldr=read(ROOT/R0);oldr['y']=oldr.log_duration_B_full_span_hours
    empirical_samples={**samples,'R0c_historical_all':oldr,'R0c_historical_weather':oldr[oldr.cause_group_official.eq('weather_natural')]}
    for combo,d in empirical_samples.items():
        recovery=combo.startswith('R0c');y=d['duration_B_full_span_hours' if recovery else cm.C]
        thresholds=[3.,12.,48.] if recovery else [.5,5.5,100.5,1000.5]
        labels=['>3h','>12h','>48h'] if recovery else ['>0 customers','>5 customers','>100 customers','>1000 customers']
        bins=pd.cut(d.gust_0h,BINS,labels=False)
        for threshold,label in zip(thresholds,labels):
            for i,(left,right) in enumerate(zip(BINS[:-1],BINS[1:])):
                m=bins.eq(i);den=int(m.sum());num=int((y[m]>threshold).sum());p=num/den if den else np.nan
                se=np.sqrt(p*(1-p)/den) if den else np.nan
                freq.append(dict(combination=combo,sample_version='historical includes zero customers' if 'historical' in combo else 'current accepted',
                    threshold_label=label,exact_numeric_threshold=threshold,operator='>',bin=i,left=left,right=right,closed='(left,right]',denominator=den,numerator=num,frequency=p,
                    mean_gust=d.loc[m,'gust_0h'].mean(),binomial_se=se,original_95_lower=p-1.96*se,original_95_upper=p+1.96*se,
                    interval_rule='original descriptive unclustered binomial +/-1.96 SE; no independence-corrected inference',excluded_gust_count=int(bins.isna().sum())))
        edges=[0,3,12,48,np.inf] if recovery else [-.5,.5,5.5,100.5,1000.5,np.inf]
        classes=pd.cut(y,edges,labels=False)
        for k in range(len(edges)-1):classrows.append(dict(combination=combo,bin=k,left=edges[k],right=edges[k+1],closed='(left,right]',n=int(classes.eq(k).sum()),total=len(d),share=float(classes.eq(k).mean())))
    freq=pd.DataFrame(freq)
    table(stage,'H03_EVENT_CONDITIONAL_FREQUENCIES',freq[~freq.combination.str.contains('historical')],r)
    csv(stage/'data/H03_HISTORICAL_FREQUENCY_REFERENCE.csv',freq[freq.combination.str.contains('historical')])
    csv(stage/'data/H03_SEVERITY_CLASS_COUNTS.csv',pd.DataFrame(classrows))
    # Body P069 coarse values: only combine existing gust bins; do not invent
    # an undocumented definition of calm wind.
    body=[]
    e=samples['E0_all']
    for label,left,right,old in [('first original bin (calm not explicitly defined)',0,4,.40),('12-18 m/s',12,18,.29),('>23 m/s within existing bins',23,45,.48)]:
        mask=e.gust_0h.gt(left)&e.gust_0h.le(right);n=int(mask.sum());num=int(e.loc[mask,cm.C].gt(100.5).sum())
        body.append(dict(location='body P069 / section4.4',label=label,left=left,right=right,closed='(left,right]',n=n,numerator=num,frequency=num/n if n else np.nan,
            quoted_value=old,frequency_minus_quote=num/n-old if n else np.nan,qualification='calm mapping unconfirmed; first original bin shown explicitly' if left==0 else 'pooled original adjacent bins, not unweighted mean of bin probabilities'))
    csv(stage/'data/H03_BODY_FREQUENCY_ALIGNMENT.csv',pd.DataFrame(body))
    summary=js(ROOT/MAIN/'model_selection/fragility_summary.json')
    lognormal=js(ROOT/MAIN/'model_selection/fragility_lognormal.json')
    opt=js(ROOT/MAIN/'model_selection/fragility_optimizer_diagnostics.json')
    curves=[]
    for margin,j in summary.items():
        records.append(dict(subsection='H.2',margin=margin,model='ordinal proportional-odds logit and separate threshold logits',
            n=60437 if margin=='E0' else 59834,weather=False,response='severity classes; right-closed original cutoffs',
            controls='M5 minus gust square and intercept, free hinges at '+str(j['knots'])+'; not fixed final controls',
            source=MAIN+'model_selection/fragility_summary.json',source_sha256=digest(ROOT/MAIN/'model_selection/fragility_summary.json'),
            converged=j['ordinal_converged'],current_compatible=margin=='E0',
            limitation='sample E0 compatible but specification historical; R0c includes zero customers. Separate-logit slope differences describe proportional-odds restriction; no new test. Full ordinal cutpoints/control parameters not saved in summary; full curve not reconstructed from gust coefficients alone.',
            figure_reference=MAIN+'figures/fig8_fragility_curves.png'))
        if j.get('negbin_glm'):
            records.append(dict(subsection='H.2 historical companion',margin=margin,model='NB GLM with Poisson residual moment alpha',n=60437,
                source=MAIN+'model_selection/fragility_summary.json',controls='same historical free14/26 hinge ordinal companion basis',
                limitation='alpha estimate='+str(j['negbin_glm']['alpha'])+' from old basis; not original H1 joint-MLE NB2 configuration, not another current candidate'))
    for margin,j in lognormal.items():
        for form in ['lognormal_weather_common_beta','lognormal_weather_free_beta','lognormal_all_incidents']:
            p=j[form];n=j['n_weather'] if 'weather' in form else j['n_all']
            diag=next((v for v in opt if v['n']==n and v['common_beta']==('free' not in form)),{})
            records.append(dict(subsection='H.3',margin=margin,model=form,n=n,weather='weather' in form,
                controls='gust only; sum of per-threshold Bernoulli objectives; common or separate beta',response='incident-conditioned severity exceedance; thresholds stored below',
                source=MAIN+'model_selection/fragility_lognormal.json',source_sha256=digest(ROOT/MAIN/'model_selection/fragility_lognormal.json'),
                converged=diag.get('success'),current_compatible=margin=='E0',
                limitation='historical parameters; very large/out-of-range theta/beta not a physical threshold; source reports optimizer convergence, so do not call it nonconvergence. Current positive-customer recovery not refitted.',
                figure_reference=MAIN+'figures/fig9_fragility_lognormal.png'))
            for k,label in enumerate(j['states']):
                theta=p['theta'][k];beta=p['beta'][k] if isinstance(p['beta'],list) else p['beta']
                for idx,g in enumerate(np.linspace(1,40,300)):
                    prob=norm.cdf((np.log(g)-np.log(theta))/beta) if theta>0 and beta!=0 else np.nan
                    curves.append(dict(margin=margin,model=form,n=n,threshold=label,grid_index=idx,gust=g,theta=theta,beta=beta,probability=prob,
                        source_version='saved historical estimate; not current recovery refit',reference='P(severity exceeds threshold | recorded incident, gust); not LAD-day incidence'))
    csv(stage/'data/H03_EXISTING_H2_H3_SOURCES.csv',pd.DataFrame(records))
    csv(stage/'data/H03_EXISTING_LOGNORMAL_CURVES.csv.gz',pd.DataFrame(curves))
    write_json(stage/'data/H03_EXISTING_LIMITATIONS.json',dict(
        ordinal='No new ordinal/logit fitting or proportional-odds test. Summary lacks full control/cutpoint parameters; original image reference is historical.',
        lognormal='All six saved optimizer statuses say success. Large beta/theta and poor empirical representation do not establish a failed optimizer or falsified physical mechanism. No optimiser repair.',
        conditional='Denominator is recorded incidents in the indicated sample/gust bin, not district-day exposure units. No restrictions on all scientific uses of the term fragility are inferred.',
        empirical='Thresholds .5/5.5/100.5/1000.5 equivalent to >0/>5/>100/>1000 for verified integer counts. Recovery strict >3/>12/>48h. Original ordinal label <3h actually includes exactly3h (right closed).',
        old_recovery='59834 all,9806 weather include zero customers; current51173/9254 frequencies separately exported; no old fitted parameters relabelled current.',
        no_new_figures='Existing referenced curves have saved parameters/grid or explicitly limited provenance. Descriptive frequency tables suffice; no new family curve gallery.'))
    return dict(empirical_counts_valid=bool((freq.numerator<=freq.denominator).all()),
        empirical_nonempty_frequencies=bool(np.allclose(freq.loc[freq.denominator>0,'frequency'],freq.loc[freq.denominator>0,'numerator']/freq.loc[freq.denominator>0,'denominator'])),
        empirical_bins_cover_each_sample=all(int(freq[(freq.combination==c)&(freq.threshold_label==freq[freq.combination==c].threshold_label.iloc[0])].denominator.sum())==len(d) for c,d in empirical_samples.items()),
        no_conditional_model_fits=True)
