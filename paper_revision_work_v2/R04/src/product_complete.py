from common import *
import matplotlib.pyplot as plt
import shutil

def run():
    metrics=pd.read_csv(Q/'tables/core_metrics.csv');mf=read(Q/'figures/FIGURE_MANIFEST.json');ar=Q/'figures/archive_before_E0_panels';ar.mkdir(exist_ok=True);plt.rcParams.update({'pdf.fonttype':42,'font.family':'DejaVu Sans'})
    def finish(fig,name,title,reference):
        fig.suptitle(title);fig.tight_layout(rect=[0,.06,1,.95]);fig.text(.01,.008,'B1 all-valid | Frozen date-group OOF | Point estimates; no independent-process validation',fontsize=8)
        for ext in ['png','pdf']:
            p=Q/'figures'/f'{name}.{ext}';shutil.copyfile(p,ar/p.name);fig.savefig(p,dpi=180,bbox_inches='tight')
        plt.close(fig);r=next(x for x in mf if x['figure']==name);r.update(title=title,producer=str(Path(__file__)),source='formal metrics.json / contributions.json',reference=reference,visual_review='pending_E0_panels')
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,t,blocks in [(axs[0],'E0',['control','G']),(axs[1],'R0c',['control','G','GK'])]:
        z=metrics[(metrics.group=='main')&(metrics.target==t)].set_index('block').loc[blocks];ax.bar(blocks,z.pooled_R2,color=['#888888','#2878a5','#d87930'][:len(blocks)]);ax.set(title='Main '+t,xlabel='Control → +G → +G+K (where applicable)',ylabel='Pooled OOF R²');ax.axhline(0,color='black',lw=.5)
    finish(fig,'figure05','Nested predictive fit for both main outcomes','pooled R2; declared control includes nongust weather+region+calendar; no unfitted regional-only baseline')
    fig,axs=plt.subplots(1,2,figsize=(11,4));xp=np.arange(2)
    axs[0].bar(['Main','Weather'],[100*read(RUN/f'{g}_E0/contributions.json')['gust_from_control'] for g in ['main','weather']],color=['#2878a5','#d87930']);axs[0].set(title='E0: G added to control',ylabel='Δ pooled R² (percentage points)')
    for dx,key,label,color in [(-.17,'gust_given_customers','G | K','#2878a5'),(.17,'customers_given_gust','K | G','#d87930')]:axs[1].bar(xp+dx,[100*read(RUN/f'{g}_R0c/contributions.json')[key] for g in ['main','weather']],width=.34,label=label,color=color)
    axs[1].set(title='R0c: conditional contributions',xticks=xp,xticklabels=['Main','Weather'],ylabel='Δ pooled R² (percentage points)');axs[1].legend();finish(fig,'figure08','Information contributions in main and weather populations','E0 gust increment and R0c conditional G/K; paired within each population, cross-population descriptive')
    save(Q/'figures/FIGURE_MANIFEST.json',mf)
    # Bind numerical captions and main-decile counterparts without pretending headings are estimates.
    slots=pd.read_csv(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',keep_default_na=False);slots['new_value']=slots.new_value.astype(object);bindings=pd.read_csv(Q/'tables/CURRENT_NUMERIC_BINDINGS.csv');bindings['new_value']=bindings.new_value.astype(object)
    dec=pd.read_csv(Q/'tables/AppendixG_main_gust_deciles.csv')
    for ri,row in enumerate(dec.itertuples(),2):
        mask=bindings.old_location.eq('A-T10')&bindings.cell.eq(f'row{ri}col2');bindings.loc[mask,'new_value']=row.weather_pct;bindings.loc[mask,'n']=60436;bindings.loc[mask,'artifact']=str(Q/'tables/AppendixG_main_gust_deciles.csv');bindings.loc[mask,'status']='current_main_population_counterpart; six-group separate';bindings.loc[mask,'population']='main'
    table(Q/'tables/CURRENT_NUMERIC_BINDINGS.csv',bindings)
    a=pd.read_csv(RUN/'main_E0/figure6_regional_reference.csv').set_index('LAD21CD');b=pd.read_csv(RUN/'main_R0c/figure6_regional_reference.csv').set_index('LAD21CD');a=a[a.status.eq('descriptive_common_calendar')];b=b.loc[a.index];corr={'Pearson':a.exp_mean_eta.corr(b.exp_mean_eta),'Spearman':a.exp_mean_eta.corr(b.exp_mean_eta,method='spearman'),'LAD':len(a)};save(Q/'tables/regional_reference_correlations.json',corr)
    def bind(locs,old,val,artifact,unit):
        mask=slots.old_location.isin(locs)&slots.old_numeric_token.eq(old);slots.loc[mask,'new_value']=val;slots.loc[mask,'unit']=unit;slots.loc[mask,'current_artifact']=str(artifact);slots.loc[mask,'status']='current_caption_number_computed; caption wording/scale must be revised'
    bind(['D-P087'],'-0.780',corr['Pearson'],Q/'tables/regional_reference_correlations.json','Pearson r');bind(['D-P087'],'-0.758',corr['Spearman'],Q/'tables/regional_reference_correlations.json','Spearman rho')
    for old,t,filename in [('2.79','E0','figure7_gust_ratio.json'),('2.37','R0c','figure7_gust_ratio.json'),('5.99','R0c','figure7_reference.json')]:
        p=RUN/f'main_{t}'/filename;bind(['D-P090','D-P092'],old,read(p)['exponentiated_grid_max_min_ratio'],p,'exponentiated reference grid max/min')
    mask=slots.old_location.eq('D-P112')&slots.old_numeric_token.isin(['9.65','10.77','5.21','5.17']);slots.loc[mask,'status']='sample-specific scale tuple; current values in AppendixH_period_scales.csv; not a shared scale';slots.loc[mask,'current_artifact']=str(Q/'tables/AppendixH_period_scales.csv')
    table(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',slots)
    print('E0 figure panels and numerical-caption bindings complete',flush=True)
if __name__=='__main__':run()
