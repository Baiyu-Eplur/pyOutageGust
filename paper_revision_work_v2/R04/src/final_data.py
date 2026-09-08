from common import *
from scipy import stats
from diagnostics import cluster_covariance
import matplotlib.pyplot as plt
import shutil,re

def run():
    e=events();main=members(e,'main','E0');mf=read(Q/'figures/FIGURE_MANIFEST.json');out=[]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
    def figsave(fig,name,description,source):
        old=Q/'figures/archive_before_final_panels';old.mkdir(exist_ok=True)
        for ext in ['png','pdf']:
            p=Q/'figures'/f'{name}.{ext}'
            if p.exists():shutil.copyfile(p,old/p.name)
        fig.suptitle(description);fig.tight_layout(rect=[0,.04,1,.95]);fig.text(.01,.008,'B1 all-valid | Retrospective description / date-group OOF | No process validation',fontsize=8)
        files=[]
        for ext in ['png','pdf']:
            p=Q/'figures'/f'{name}.{ext}';fig.savefig(p,dpi=180,bbox_inches='tight');files.append(str(p))
        plt.close(fig);row=next((x for x in mf if x['figure']==name),None)
        if row is None:row={'figure':name};mf.append(row)
        row.update(title=description,source=source,files=files,producer=str(Path(__file__)),visual_review='pending_final_panels',scale='explicit per axis',reference='actual frozen B1 population and archives')
    fig,axs=plt.subplots(2,2,figsize=(11,7))
    for ax,values,label in zip(axs.flat,[main[C],np.log1p(main[C]),main[D],np.log(main[D])],['Affected customers','ln(1 + affected customers)','Restoration span (hours)','ln(restoration span / hours)']):
        ax.hist(values,bins=65,color='#2878a5');ax.set(xlabel=label,ylabel='Incidents')
        if label in ['Affected customers','Restoration span (hours)']:ax.set_yscale('log');ax.set_ylabel('Incidents (log axis)')
    figsave(fig,'figure02','Outcome distributions: all 60,436 eligible events, no tail trimming','R02 candidate_main_E0 / R0c')
    windows=read(CORE/'configs/storm_windows.json');fig,ax=plt.subplots(figsize=(12,4));a=pd.Timestamp('2021-04-01');b=pd.Timestamp('2023-09-30');c=pd.Timestamp('2024-04-01')
    for left,right,color,label in [(a,b,'#2878a5','Earlier period'),(b,c,'#d87930','Later period')]:ax.barh(1,(right-left).days,left=left,height=.3,color=color);ax.text(left+(right-left)/2,1,label,ha='center',va='center',color='white')
    for i,(name,w) in enumerate(windows.items()):
        t=pd.Timestamp(w['start']);level=1.35+(i%3)*.23;ax.plot([t,t],[1.15,level],color='#555555',lw=.7);ax.scatter(t,1.15,s=12,color='#555555');ax.text(t,level,name,ha='center',fontsize=8)
    ax.set(ylim=(.55,2),yticks=[],xlabel='UTC calendar; split at 30 September 2023');ax.text(.01,.03,'Both periods contributed to historical development; later is not an untouched confirmation set.',transform=ax.transAxes,fontsize=9);fig.autofmt_xdate()
    figsave(fig,'figure03','Retrospective periods and seven named storm windows','frozen UTC contract and R03/configs/storm_windows.json')
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for i,g in enumerate(['main','weather']):
        s=pd.read_csv(RUN/f'{g}_R0c/stage_composition.csv');p=pd.read_csv(RUN/f'{g}_R0c/stage_pooled.csv')
        s=s.sort_values('customer_bin',key=lambda v:v.map(lambda z:float(z[1:].split(',')[0])));p=p.sort_values('customer_bin',key=lambda v:v.map(lambda z:float(z[1:].split(',')[0])))
        for st,z in s.groupby('stage_group'):axs[i,0].plot(z.customer_bin,z['mean'],marker='o',label=str(st))
        axs[i,0].legend(title='Stage rows');axs[i,1].plot(p.customer_bin,p['mean'],marker='o',color='#d87930')
        for j in [0,1]:axs[i,j].set(title=g+(' by stage' if j==0 else ' pooled'),xlabel='Common customer bins',ylabel='Mean recorded span (hours)');axs[i,j].tick_params(axis='x',rotation=25)
    figsave(fig,'figureD1','Stage composition and pooled means within each population','formal stage_composition.csv / stage_pooled.csv; population-specific shared bins')
    fig,axs=plt.subplots(2,2,figsize=(11,8));residuals=[]
    for i,t in enumerate(['E0','R0c']):
        d=members(e,'main',t);m=model('main',t);eta=predict_eta(d,m);res=target(d,t)-eta;axs[i,0].hexbin(eta,res,gridsize=55,mincnt=1,bins='log',cmap='viridis');axs[i,0].axhline(0,color='orange');axs[i,0].set(xlabel='Fitted eta',ylabel='Log-scale residual',title=t+' residuals')
        osm,osr=stats.probplot(res,fit=False);axs[i,1].plot(osm,osr,'.',ms=1);axs[i,1].set(xlabel='Theoretical normal quantile',ylabel='Ordered residual',title=t+' normal Q–Q')
        jb=stats.jarque_bera(res);residuals.append({'target':t,'n':len(d),'skewness':stats.skew(res),'excess_kurtosis':stats.kurtosis(res),'JB_statistic':jb.statistic,'JB_p_asymptotic_descriptive_only':jb.pvalue,'mean_exp_residual_diagnostic_only':np.exp(res).mean(),'not_applied_to_predictions':True})
    figsave(fig,'figureF1','Full-fit log-OLS residual diagnostics','four panels from two formal main model archives; no additional fits')
    table(Q/'tables/residual_diagnostics.csv',pd.DataFrame(residuals))
    # Current descriptions, not retrospective rewriting of the development history.
    rows=[]
    for g in ['main','weather']:
      for per in ['all','development','later']:
        d=members(e,g,'R0c');d=d if per=='all' else d[d.new_period.eq(per)]
        for label,mask in [('1',d.stage_row_count.eq(1)),('2',d.stage_row_count.eq(2)),('3–4',d.stage_row_count.between(3,4)),('5–9',d.stage_row_count.between(5,9)),('10+',d.stage_row_count.ge(10))]:rows.append({'population':g,'period':per,'stage_group':label,'n':int(mask.sum()),'denominator':len(d),'pct':100*mask.mean()})
    table(Q/'tables/AppendixD_period_stage_counts.csv',pd.DataFrame(rows))
    scales=[]
    for p in (Q/'periods_v2').glob('*.json'):
        m=read(p);scales.append({'group':m['metadata']['group'],'target':m['target'],'period':m['metadata']['period'],'n':m['training_n'],'gust_mean':m['preprocessor']['mean']['gust_0h'],'gust_sd':m['preprocessor']['sd']['gust_0h'],'model':str(p)})
        for cov,arr in m['covariance'].items():
            a=np.array(arr);assert np.isfinite(a).all();out.append({'archive':str(p),'covariance':cov,'negative_diagonal':bool((np.diag(a)<0).any()),'minimum_eigenvalue':np.linalg.eigvalsh(a).min()})
    table(Q/'tables/AppendixH_period_scales.csv',pd.DataFrame(scales));save(Q/'checks/period_covariance_acceptance.json',out)
    # R1 archive read-back acceptance, all 60 OOF models, no refit.
    checks=[]
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        folder=Q/'R1_input_compat_v1'/f'{g}_{t}';m=read(folder/'full_model.json');d=e[e[ID].isin(m['training_ids'])];assert np.isfinite(predict_eta(d,m)).all();metrics=read(folder/'metrics.json')
        for block,metric in metrics.items():
            p=pd.read_csv(folder/f'oof_{block}.csv',float_precision='round_trip');assert p[ID].is_unique and set(p[ID])==set(d[ID]);assert abs(score(p.y,p.prediction_eta)['r2']-metric['pooled_oof_r2'])<1e-12
            for fold in range(5):
                fm=read(folder/f'model_fold{fold}_{block}.json');ev=d[d[ID].isin(p.loc[p.fold.eq(fold),ID])];assert not(set(ev.new_date_utc)&set(fm['training_dates']));assert np.allclose(predict_eta(ev,fm),p.set_index(ID).loc[ev[ID]].prediction_eta,atol=1e-12,rtol=0)
        checks.append({'group':g,'target':t,'n':len(d),'all_archives_and_OOF_passed':True})
    save(Q/'checks/R1_archive_acceptance.json',checks)
    # Per-window LAD counts and support are derived on explicitly named populations.
    storm=[]
    for name,d in [('event_master',e),('main',main),('weather',members(e,'weather','E0'))]:
        for key,w in windows.items():
            z=d[d.new_time_utc.ge(pd.Timestamp(w['start']))&d.new_time_utc.lt(pd.Timestamp(w['end_exclusive']))];storm.append({'population':name,'window':key,'events':len(z),'LAD':z.LAD21CD.nunique(),'customers':z[C].sum(min_count=1),'duration_mean_hours':z[D].mean(),'gust_max_ms':z.gust_0h.max()})
    table(Q/'tables/storm_LAD_details.csv',pd.DataFrame(storm))
    v=model('main','E0');minimum=read(RUN/'main_E0/conditional_minimum_no_CI.json')['minimum_ms'];support=[]
    for name,d in [('main',main),('weather',members(e,'weather','E0'))]:support.append({'population':name,'n':len(d),'reference_minimum_ms':minimum,'below_n':int(d.gust_0h.lt(minimum).sum()),'below_pct':100*d.gust_0h.lt(minimum).mean()})
    table(Q/'tables/AppendixG_low_gust_support.csv',pd.DataFrame(support))
    save(Q/'figures/FIGURE_MANIFEST.json',mf)
    # Machine-readable semantic bindings for every table cell that can be matched directly.
    slots=pd.read_csv(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',keep_default_na=False);slots['new_value']=slots.new_value.astype(object);slots['unit']=slots.unit.astype(object)
    desc=pd.read_csv(Q/'tables/Table1_current.csv');cf=pd.read_csv(Q/'tables/Tables3_F_complete_coefficients.csv');sc=pd.DataFrame(scales);md=read(W/'manuscript_record/REVISION_ITEMS.json');bindings=[]
    def bind(loc,cell,value,unit,path,n,target_name,status='current_value_computed'):
        links=[v for v in md['items'] if loc in v['locations']];bindings.append({'old_location':loc,'cell':cell,'new_value':value,'unit':unit,'population':'main unless stated','target':target_name,'n':n,'artifact':str(path),'producer':'R04/src/final_data.py; upstream archives','config':str(CORE/'configs/R04_primary.json'),'status':status,'MR':','.join(v['id'] for v in links),'CL':','.join(sorted({c for v in links for c in v.get('claim_ids',[])}))})
        mask=slots.old_location.eq(loc)&slots.cell.eq(cell)
        if mask.sum()==1:slots.loc[mask,['new_value','unit','status','current_artifact']]=[value,unit,status,str(path)]
    stats_names=['Mean','Median','SD','Min','25th pct.','75th pct.','Max']
    for ri,st in enumerate(stats_names,2):
        for ci,(t,scale) in enumerate([('E0','raw'),('E0','log'),('R0c','raw'),('R0c','log')],2):
            val=desc[(desc.target==t)&(desc.scale==scale)&(desc.statistic==st)].iloc[0];bind('D-T01',f'row{ri}col{ci}',val.value,'customers' if t=='E0' and scale=='raw' else 'hours' if scale=='raw' else 'log target',Q/'tables/Table1_current.csv',60436,t)
    termmap=['const','zG','zG2','zRain24','zTemp','zPressure','zG_zPressure','urban_binary','log_population','income_deprivation_rate','deprivation_gap_pct','morans_i','zK','zK2']
    for loc,t in [('A-T08','E0'),('A-T09','R0c')]:
        for ri,term in enumerate(termmap[:12] if t=='E0' else termmap,2):
            for ci,cov,field in [(2,'LAD_CR1','coefficient'),(3,'LAD_CR1','SE'),(4,'LAD_CR1','p_normal_CR1_descriptive'),(5,'LAD_date_two_way_CR1','SE'),(6,'LAD_date_two_way_CR1','p_normal_CR1_descriptive')]:
                val=cf[(cf.group=='main')&(cf.target==t)&(cf.term==term)&(cf.covariance==cov)].iloc[0][field];bind(loc,f'row{ri}col{ci}',val,field,Q/'tables/Tables3_F_complete_coefficients.csv',60436,t)
    for ri,(t,per) in enumerate([('E0','development'),('E0','later'),('R0c','development'),('R0c','later')],2):
        row=sc[(sc.group=='main')&(sc.target==t)&(sc.period==per)].iloc[0]
        for ci,field in [(3,'gust_mean'),(4,'gust_sd')]:bind('A-T13',f'row{ri}col{ci}',row[field],'m/s',Q/'tables/AppendixH_period_scales.csv',row.n,t)
    for ri,row in enumerate(read(Q/'tables/AppendixH_pressure_minima.json'),2):
        for ci,val,unit in [(2,(row['algebraic_vertex_ms']-row['gust_mean'])/row['gust_sd'],'standardized gust'),(3,row['minimum_ms'],'m/s')]:bind('A-T11',f'row{ri}col{ci}',val,unit,Q/'tables/AppendixH_pressure_minima.json',60436,'E0')
    for ri,row in enumerate(pd.read_csv(Q/'tables/AppendixG_gust_deciles.csv').itertuples(),2):bind('A-T10',f'row{ri}col2',row.weather_pct,'percent',Q/'tables/AppendixG_gust_deciles.csv',117108,'six-group membership','current_all_valid_counterpart_population_changed')
    for loc in ['A-T01','D-T02','A-T02']:
        mask=slots.old_location.eq(loc);slots.loc[mask,'status']='definition_or_code_identifier_not_new_estimate; see R01/R03 frozen contracts'
    # Historical experiments and bootstrap are deliberately not replaced by current fits.
    for loc in ['A-P020','A-P023','A-P057','A-T06','A-T07','A-P063','A-P078','A-P080','A-T12','A-P086','A-P089']:
        slots.loc[slots.old_location.eq(loc),'status']='historical_experiment_or_formula; retain source history; not a new B1 estimate or CI'
    for loc in ['A-T04','A-T05']:
        slots.loc[slots.old_location.eq(loc),'status']='old_development_population; current_all_valid_combined_counterpart_available; no direct token substitution'
    for i,row in slots.iterrows():
        if row.status=='needs_semantic_mapping_before_W':
            if re.match(r'^\d+(?:\.\d+)*[ .]',row.old_context) or row.old_context.startswith(('Figure ','Table ','Section ','Appendix ')):slots.at[i,'status']='cross_reference_or_caption; content changes recorded in coverage'
            elif row.old_numeric_token in ['1','2','3','4','5','6','7','8','9','10','2021','2022','2023','2024'] and len(row.old_context)<150:slots.at[i,'status']='definition_date_or_cross_reference; preserve meaning; not empirical estimate'
            else:slots.at[i,'status']='unmapped_legacy_slot; not released for B1 reuse; consult MR and current replacement datasets'
    table(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',slots);table(Q/'tables/CURRENT_NUMERIC_BINDINGS.csv',pd.DataFrame(bindings))
    save(Q/'checks/final_data.json',{'fits':0,'R1_reload_checked':checks,'numeric_slots':len(slots),'cell_bindings':len(bindings),'unmapped_legacy_slots':int(slots.status.str.startswith('unmapped').sum()),'Word_modified':False})
    print('final data complete',len(bindings),'semantic cell bindings',flush=True)
if __name__=='__main__':run()
