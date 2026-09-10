"""Deterministic G summaries and figures from saved arrays; no fitting."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.final_combined_analysis.figure_style import apply_style, save_fig
from .gi_core import BINS, cm, knots, scores
from .f02_cov import csv,read,js
from .mapping import write_json
from .exporters import table

KEY=['combination','model_id','prediction_type']
TITLES={'E0_all':'All exposure','R0c_all':'All recovery','E0_weather':'Weather exposure','R0c_weather':'Weather recovery'}
COLORS={'final':'#238443','paper':'#c0392b','hinge':'#756bb1','control':'#222222','cubic':'#2980b9','log':'#8e44ad','legacy_hinge':'#999999'}

def summarize(stage,master,requirement):
    metrics=[];bins=[];cal=[];folds=[];checks={}
    for keys,d in master.groupby(KEY,sort=False):
        meta=dict(zip(KEY,keys));metrics.append(dict(**meta,**scores(d.y,d.prediction)))
        if keys[2]=='LAD_OOF':
            for fold,s in d.groupby('fold'):folds.append(dict(**meta,fold=fold,**scores(s.y,s.prediction)))
        cut=pd.cut(d.gust,BINS,labels=False)
        for i,(left,right) in enumerate(zip(BINS[:-1],BINS[1:])):
            s=d.loc[cut.eq(i)];n=len(s);sem=s.residual.std(ddof=1)/np.sqrt(n) if n>1 else np.nan
            bins.append(dict(**meta,bin=i,left=left,right=right,closed='(left,right]',plot_midpoint=(left+right)/2,
                n=n,mean_gust=s.gust.mean(),mean_observed=s.y.mean(),mean_prediction=s.prediction.mean(),mean_residual=s.residual.mean(),
                sem=sem,ci_lower=s.residual.mean()-1.96*sem,ci_upper=s.residual.mean()+1.96*sem,
                interval_rule='mean residual +/-1.96*sample_sd/sqrt(n); original unclustered bin interval',excluded_from_bins=int(cut.isna().sum())))
        checks['bins_count_'+'_'.join(keys)]=int(sum(v['n'] for v in bins[-13:]))+int(cut.isna().sum())==len(d)
        if keys[1] not in ['final','paper','hinge'] or keys[2]=='control_residual':continue
        q=10 if keys[0].endswith('weather') else 20
        codes,edges=pd.qcut(d.prediction,q,labels=False,retbins=True,duplicates='drop')
        for i in range(len(edges)-1):
            s=d.loc[codes.eq(i)]
            cal.append(dict(**meta,bin=i,left=float(edges[i]),right=float(edges[i+1]),first_includes_minimum=i==0,n=len(s),
                mean_prediction=s.prediction.mean(),mean_observed=s.y.mean(),bias=(s.prediction-s.y).mean(),requested_quantiles=q,actual_bins=len(edges)-1,
                rule='qcut per prediction series; duplicates=drop; first includes minimum; no label-based adjustment'))
        checks['calibration_count_'+'_'.join(keys)]=int(codes.notna().sum())==len(d)
    metric=pd.DataFrame(metrics);b=pd.DataFrame(bins);c=pd.DataFrame(cal)
    table(stage,'GI_PREDICTION_METRICS',metric,requirement)
    table(stage,'GI_FINAL_GUST_RESIDUALS',b[b.model_id.eq('final') & b.prediction_type.eq('LAD_OOF')],requirement)
    csv(stage/'data/GI_GUST_BINS.csv',b);csv(stage/'data/GI_CALIBRATION_BINS.csv',c);csv(stage/'data/GI_FOLD_METRICS.csv',pd.DataFrame(folds))
    return metric,b,c,checks

def curve_arrays(stage,samples,bins):
    preps=js(stage/'data/GI_PREPROCESSING.json');gg=np.linspace(.5,40,300);rows=[];vecs=[];diagnostics=[]
    for combo,d in samples.items():
        full=[p for p in preps if p['combination']==combo and p['fold']==-1 and p['model_id']!='control']
        control=bins[(bins.combination==combo)&bins.model_id.eq('control')].sort_values('bin')
        valid=control.n.gt(1)&control['sem'].gt(0)&np.isfinite(control['sem'])
        mu=d.gust_0h.mean();sd=d.gust_0h.std(ddof=1);z=(gg-mu)/sd
        for p in full:
            spec=p['model_id'];cols=p['columns'];beta=np.asarray(p['beta']);a=np.zeros((len(gg),len(cols)))
            for j,col in enumerate(cols):
                if col=='z_gust_0h':a[:,j]=z
                elif col=='z_gust_sq':a[:,j]=z*z
                elif col=='z_gust_cu':a[:,j]=z**3
                elif col=='log_gust':a[:,j]=np.log1p(gg)
                elif col=='gust_low':a[:,j]=np.minimum(gg,p['knots'][0])
                elif col=='gust_ramp':a[:,j]=np.clip(gg-p['knots'][0],0,p['knots'][1]-p['knots'][0])
                elif col.startswith(('hinge_','gust_hinge_')):a[:,j]=np.maximum(gg-float(col.split('_')[-1]),0)
                # Interactions zero at mean standardized pressure/precipitation;
                # only the gust main component is shown, not total predictions.
            raw=a@beta
            if combo.endswith('all') and spec in ['final','paper']:
                shift=float(raw[np.argmin(abs(gg-mu))]);rule='subtract value at grid point nearest full-sample mean gust (final_models Figure11)'
            else:
                shift=float(np.average(np.interp(control.loc[valid,'plot_midpoint'],gg,raw)-control.loc[valid,'mean_residual'],weights=1/control.loc[valid,'sem']**2))
                rule='inverse bin-SEM squared weighted mean of interpolated curve minus nongust residual means (Figures2/13); nonempty n>1 SEM>0 bins'
            line=raw-shift;variance=np.full(len(gg),np.nan);se=variance.copy()
            path=stage/f'data/GI_{combo}_{spec}_COV.csv'
            if path.exists():
                V=read(path).set_index('term').loc[cols,cols].to_numpy()
                variance=np.einsum('ij,jk,ik->i',a,V,a)
                np.sqrt(variance,out=se,where=np.isfinite(variance)&(variance>=0))
                diagnostics.append(dict(combination=combo,model_id=spec,points=len(gg),negative_variance_points=int((variance<0).sum()),nonfinite_variance_points=int((~np.isfinite(variance)).sum()),min_variance=float(variance.min()),minimum_cov_eigenvalue=float(np.linalg.eigvalsh(V).min()),clipping='none',variance_basis='uncentred gust component basis; original displayed band rule; shift not propagated'))
            for i,g in enumerate(gg):
                rows.append(dict(combination=combo,model_id=spec,grid_index=i,gust=g,raw_component=raw[i],shift=shift,curve=line[i],variance=variance[i],lower=line[i]-1.96*se[i],upper=line[i]+1.96*se[i],band_valid=bool(np.isfinite(se[i])),band_rule='original 1.96 sqrt(aVa), with unshifted a; not individual prediction interval',shift_rule=rule,reference='full-sample gust scaling; pressure/precipitation z=0; all other component coefficients multiply zero'))
            # Wide gradients are exact, compact and independently reproducible.
            csv(stage/f'data/GI_{combo}_{spec}_CURVE_DESIGN.csv',pd.DataFrame(a,columns=cols).assign(grid_index=np.arange(len(gg)),gust=gg))
    # Figure3's quadratic and Figure13's grey reference need their own
    # centring, even though their coefficients/bases are already exported.
    extra=[]
    for combo in cm.COMBOS:
        control=bins[bins.combination.eq(combo)&bins.model_id.eq('control')].sort_values('bin')
        valid=control.n.gt(1)&control['sem'].gt(0)&np.isfinite(control['sem'])
        source_combo=combo if combo.endswith('all') else combo.replace('_weather','_all')
        source_spec='paper' if combo.startswith('R0c') or combo.endswith('all') else 'final'
        source_rows=[r for r in rows if r['combination']==source_combo and r['model_id']==source_spec]
        raw=np.array([r['raw_component'] for r in source_rows])
        shift=float(np.average(np.interp(control.loc[valid,'plot_midpoint'],gg,raw)-control.loc[valid,'mean_residual'],weights=1/control.loc[valid,'sem']**2))
        for r in source_rows:
            v=dict(r);v.update(combination=combo,model_id='paper_Figure3_shift' if combo.endswith('all') else 'grey_full_Figure6_reference',
                shift=shift,curve=r['raw_component']-shift,variance=np.nan,lower=np.nan,upper=np.nan,band_valid=False,
                shift_rule='original weighted alignment to this sample nongust bins; coefficients and basis from '+source_combo+'/'+source_spec,
                reference='same raw component as '+source_combo+'/'+source_spec+'; full-sample scaling for grey reference',band_rule='no band in original comparison line')
            extra.append(v)
    rows.extend(extra)
    curves=pd.DataFrame(rows);csv(stage/'data/GI_RESPONSE_CURVES.csv',curves)
    write_json(stage/'data/GI_CURVE_VARIANCE_CHECKS.json',diagnostics)
    return curves,diagnostics

def figures(stage,master,bins,cal,curves):
    apply_style();plt.rcParams.update({'font.size':9,'axes.titlesize':10,'axes.labelsize':9})
    axes_info=[]
    # Each panel uses every eligible row; percentile display cuts from originals
    # remain explicitly recorded and do not remove observations from scoring.
    fig,axes=plt.subplots(4,2,figsize=(10,14))
    for i,combo in enumerate(cm.COMBOS):
        d=master[(master.combination==combo)&master.model_id.eq('final')&master.prediction_type.eq('LAD_OOF')]
        ax=axes[i,0];ax.hexbin(d.prediction,d.y,gridsize=40,bins='log',mincnt=1,cmap='Blues',rasterized=True)
        xlim=np.percentile(d.prediction,[.5,99.5]);ylim=np.percentile(d.y,[.2,99.8]);ax.set_xlim(xlim);ax.set_ylim(ylim)
        lo=min(*xlim,*ylim);hi=max(*xlim,*ylim);ax.plot([lo,hi],[lo,hi],'k--',lw=.8)
        cc=cal[(cal.combination==combo)&cal.model_id.eq('final')&cal.prediction_type.eq('LAD_OOF')]
        ax.plot(cc.mean_prediction,cc.mean_observed,'o-',color=COLORS['final'],ms=3)
        ax.set(xlabel='Predicted log response (LAD-OOF)',ylabel='Observed log response',title=TITLES[combo]+' — fixed final')
        axes_info.append(dict(figure='GI_PREDICTION_CALIBRATION',panel=combo+' density',n=len(d),xlim=xlim.tolist(),ylim=ylim.tolist(),outside_display=int(((d.prediction<xlim[0])|(d.prediction>xlim[1])|(d.y<ylim[0])|(d.y>ylim[1])).sum()),scoring_exclusions=0))
        ax=axes[i,1]
        for spec in (['final','paper','hinge'] if combo.endswith('weather') else ['final','paper']):
            v=cal[(cal.combination==combo)&cal.model_id.eq(spec)&cal.prediction_type.eq('LAD_OOF')]
            ax.plot(v.mean_prediction,v.mean_observed,'o-',ms=3,lw=1,color=COLORS[spec],label=spec)
        lo=min(ax.get_xlim()[0],ax.get_ylim()[0]);hi=max(ax.get_xlim()[1],ax.get_ylim()[1]);ax.plot([lo,hi],[lo,hi],'k--',lw=.8)
        ax.set(xlabel='Mean predicted log response',ylabel='Mean observed log response',title=TITLES[combo]+(' — deciles' if combo.endswith('weather') else ' — ventiles'));ax.legend(fontsize=8)
    fig.tight_layout();save_fig(fig,stage/'figures','GI_PREDICTION_CALIBRATION',dpi_png=180);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,combo in zip(axes.flat,cm.COMBOS):
        for spec,kind,color,offset,label in [('control','control_residual','#222222',-.2,'Nongust control'),('final','in_sample','#238443',0,'Final in-sample'),('final','LAD_OOF','#2980b9',.2,'Final LAD-OOF')]:
            s=bins[(bins.combination==combo)&bins.model_id.eq(spec)&bins.prediction_type.eq(kind)]
            ax.errorbar(s.plot_midpoint+offset,s.mean_residual,yerr=1.96*s['sem'],fmt='o',ms=3,capsize=2,color=color,label=label)
        s=bins[(bins.combination==combo)&bins.model_id.eq('control')]
        ax.text(.01,.01,'Bin n: '+', '.join(map(str,s.n)),transform=ax.transAxes,fontsize=6.4)
        ax.axhline(0,c='grey',lw=.8);ax.set(title=TITLES[combo],xlabel='Event gust (m/s); fixed bin midpoints',ylabel='Mean residual (observed − predicted)');ax.legend(fontsize=7)
    fig.tight_layout();save_fig(fig,stage/'figures','GI_GUST_RESIDUALS',dpi_png=180);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,combo in zip(axes.flat,cm.COMBOS):
        s=bins[(bins.combination==combo)&bins.model_id.eq('control')]
        if combo.endswith('weather'):
            ax.errorbar(s.plot_midpoint,s.mean_residual,yerr=1.96*s['sem'],fmt='o',ms=3,capsize=2,c='k',label='Nongust residual bins')
        for spec,c in curves[curves.combination.eq(combo)].groupby('model_id',sort=False):
            if spec in ['paper_Figure3_shift','grey_full_Figure6_reference']:continue
            if combo.endswith('all') and spec not in ['final','paper']:continue
            ax.plot(c.gust,c.curve,color=COLORS[spec],lw=1.5 if spec=='final' else 1,ls='-' if spec=='final' else '--',label=spec)
            if spec in ['final','hinge']:ax.fill_between(c.gust,c.lower,c.upper,color=COLORS[spec],alpha=.12)
        ax.axhline(0,c='grey',lw=.6);ax.set(title=TITLES[combo],xlabel='Gust (m/s)',ylabel='Gust component relative to mean gust' if combo.endswith('all') else 'Component shifted to control residuals');ax.legend(fontsize=7,ncol=2)
    fig.tight_layout();save_fig(fig,stage/'figures','GI_RESPONSE_COMPONENTS',dpi_png=180);plt.close(fig)
    write_json(stage/'data/GI_FIGURE_AXES.json',dict(density_panels=axes_info,all_rows_drawn=True,hexbin_aggregation='log count; no row sampling',calibration='original quantiles; connected bin means, counts saved',residual_intervals='unclustered bin SEM, not two-way curve bands',curve_bands='original uncentred component covariance; see GI_RESPONSE_CURVES.csv'))
