from common import *
from scipy import stats
import re

def run():
    e=events();main=members(e,'main','E0');weather=members(e,'weather','E0');slots=pd.read_csv(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',keep_default_na=False);slots['new_value']=slots.new_value.astype(object);notes=[]
    # Reconstruct main-population deciles as well as the already explicit six-group counterpart.
    main=main.copy();main['gust_decile']=pd.qcut(main.gust_0h,10,duplicates='drop');dec=main.groupby('gust_decile',observed=True).agg(n=(ID,'size'),weather_n=('cause_group_event',lambda s:s.eq('weather_natural').sum()));dec['weather_pct']=100*dec.weather_n/dec.n;table(Q/'tables/AppendixG_main_gust_deciles.csv',dec.reset_index())
    # Correlations are descriptive, each storm/population/prediction source explicitly stated.
    corr=[]
    windows=read(CORE/'configs/storm_windows.json')
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        d=members(e,g,t);m=model(g,t);preds={'full_fit':pd.Series(predict_eta(d,m),index=d[ID])};p=pd.read_csv(RUN/f'{g}_{t}/oof_{m["block"]}.csv').set_index(ID);preds['date_OOF']=p.prediction_eta
        for source,eta in preds.items():
          for key,w in list(windows.items())+[('ALL',None)]:
            z=d if w is None else d[d.new_time_utc.ge(pd.Timestamp(w['start']))&d.new_time_utc.lt(pd.Timestamp(w['end_exclusive']))];y=target(z,t);pp=eta.loc[z[ID]].to_numpy();value=float(np.corrcoef(y,pp)[0,1]) if len(z)>1 and np.std(y)>0 and np.std(pp)>0 else None;corr.append({'group':g,'target':t,'source':source,'window':key,'n':len(z),'pearson_r_log_target_eta':value,'independent_process_validation':False})
    table(Q/'tables/storm_prediction_correlations.csv',pd.DataFrame(corr))
    cfs=pd.read_csv(Q/'tables/Tables3_F_complete_coefficients.csv');z=np.abs(cfs.coefficient/cfs.SE);cfs['p_log10_normal_CR1']= (np.log(2)+stats.norm.logsf(z))/np.log(10);cfs['p_status']=np.where(cfs.p_normal_CR1_descriptive.eq(0),'floating_point_underflow_use_log10_p','finite_normal_Wald_descriptive');table(Q/'tables/Tables3_F_complete_coefficients.csv',cfs)
    res=pd.read_csv(Q/'tables/residual_diagnostics.csv');res['JB_log10_p_asymptotic']= -res.JB_statistic/(2*np.log(10));res['JB_p_status']='floating_point_underflow; use log10_p; asymptotic iid reference is descriptive only';table(Q/'tables/residual_diagnostics.csv',res)
    # Direct paragraph-value bindings; long source sentences can require rewriting, not blind replacement.
    def bind(locs,old,value,unit,artifact,target_name='main',n=60436,status='current_value_computed_context_requires_revision'):
        if isinstance(locs,str):locs=[locs]
        mask=slots.old_location.isin(locs)&slots.old_numeric_token.eq(old)&slots.cell.eq('');slots.loc[mask,'new_value']=value;slots.loc[mask,'unit']=unit;slots.loc[mask,'status']=status;slots.loc[mask,'current_artifact']=str(Q/'tables'/artifact)
        for row in slots.loc[mask].to_dict('records'):notes.append({**row,'target':target_name,'n':n,'producer':str(Path(__file__)),'config':str(CORE/'configs/R04_primary.json')})
    for loc in ['D-P002','D-P039','A-P018','A-P065']:
        for old in ['60,453','60,437','59,834']:bind(loc,old,60436,'events','core_metrics.csv')
    for loc in ['D-P002','D-P073','D-P118','A-P073','D-P101']:
        for old in ['10.7','10.694','10.69']:bind(loc,old,10.807545499294342,'m/s','AppendixH_pressure_minima.json')
    bind('D-P017','9.87',9.91022238832415,'m/s mean','H0_R1_B1_shape.csv');bind('D-P017','5.22',5.279979383259645,'m/s SD','H0_R1_B1_shape.csv')
    for old,val in [('47.13',47.12833410550003),('93.02',93.02572969753128),('1.97',1.9738811367549456)]:bind(['D-P030','A-P018'],old,val,'customers' if old!='1.97' else 'ratio; lowest stage number, not earliest timestamp','customer_aggregation_comparison.json')
    pm=read(Q/'tables/AppendixH_pressure_minima.json')
    bind('D-P073','0.157286',(pm[1]['minimum_ms']-pm[1]['gust_mean'])/pm[1]['gust_sd'],'standardized gust','AppendixH_pressure_minima.json')
    for old,row in [('9.656',pm[0]),('11.732',pm[2])]:bind('D-P073',old,row['minimum_ms'],'m/s','AppendixH_pressure_minima.json')
    for old,field in [('−0.032325899095631154','beta1'),('0.10276170747389514','beta2'),('−0.0408384359554068','beta3_interaction'),('9.87229677581956','gust_mean'),('5.222713076874045','gust_sd')]:bind('A-P076',old,pm[1][field],field,'AppendixH_pressure_minima.json')
    storms=pd.read_csv(Q/'tables/storm_LAD_details.csv');eu=storms[(storms.population=='main')&(storms.window=='Eunice')].iloc[0];fr=storms[(storms.population=='main')&(storms.window=='Franklin')].iloc[0]
    for old,field,unit in [('1,601','events','events'),('101','LAD','LAD'),('376,712','customers','customers'),('52.7','duration_mean_hours','hours')]:bind('D-P006',old,eu[field],unit,'storm_LAD_details.csv','main Eunice',int(eu.events),'current_main_population; old weather-related label cannot be retained')
    bind('D-P006','1,187',fr.events,'events','storm_LAD_details.csv','main Franklin',int(fr.events))
    bind('D-P006','39.4',eu.gust_max_ms,'m/s cached proxy, observed/3-second semantics unverified','storm_LAD_details.csv','main Eunice',int(eu.events))
    for old,val,unit in [('27',25,'unique UTC days; summed windows remain27'),('2.46',25/1096*100,'percent of calendar days'),('8.15',4452/60436*100,'percent events'),('14.72',745372/5622103*100,'percent customers'),('3.3',(4452/60436)/(25/1096),'event concentration ratio'),('6',(745372/5622103)/(25/1096),'customer concentration ratio')]:bind('D-P102',old,val,unit,'storm_statistics.csv')
    bind('D-P101','0.15',.382246342941095,'R² percentage points; sign changes to positive','core_metrics.csv','weather E0',9857)
    support=pd.read_csv(Q/'tables/AppendixG_low_gust_support.csv').set_index('population')
    for old,g in [('63.70','main'),('36.83','weather')]:bind(['D-P101','A-P073'],old,support.loc[g,'below_pct'],'percent within population','AppendixG_low_gust_support.csv',g,int(support.loc[g,'n']))
    bind('A-P073','57.8',support.loc['weather','below_pct']/support.loc['main','below_pct']*100,'percent ratio of within-group shares','AppendixG_low_gust_support.csv')
    for old,val in [('6.89',dec.weather_pct.iloc[0]),('56.10',dec.weather_pct.iloc[-1])]:bind(['A-P071','D-P101'],old,val,'percent; main-population deciles','AppendixG_main_gust_deciles.csv')
    # Historical A-T10 is a cause support description; provide both denominators rather than conflate them.
    for ri,row in enumerate(dec.itertuples(),2):
        mask=slots.old_location.eq('A-T10')&slots.cell.eq(f'row{ri}col2');slots.loc[mask,['new_value','unit','status','current_artifact']]=[row.weather_pct,'percent of main bin','current_main_population_counterpart; six-group deciles separately archived',str(Q/'tables/AppendixG_main_gust_deciles.csv')]
    for old,val in [('10.46',res[res.target=='E0'].iloc[0].mean_exp_residual_diagnostic_only),('2.20',res[res.target=='R0c'].iloc[0].mean_exp_residual_diagnostic_only)]:bind('A-P091',old,val,'mean exp residual; not applied correction','residual_diagnostics.csv')
    six=pd.read_csv(Q/'tables/AppendixC_fold_summary.csv')
    for old,g,t in [('0.0608','six_groups','zG2'),('0.0792','main','zG2'),('0.0257','six_groups','zG'),('0.0002','main','zG')]:bind('D-P038',old,six[(six.group==g)&(six.term==t)].iloc[0].mean_coefficient,'mean fold coefficient, overlapping training folds','AppendixC_fold_summary.csv',g,117108 if g=='six_groups' else 60436)
    bind('D-P038','116,064',117108,'events','AppendixC_fold_summary.csv','six_groups',117108);bind('D-P038','59,834',60436,'events','AppendixC_fold_summary.csv')
    for old in ['9,758','9,857']:bind('D-P097',old,9857,'events','core_metrics.csv','weather',9857)
    # Source-era findings/intervals remain historical evidence; no current intervals substituted.
    historical=['D-P055','D-P075','A-P035','A-P038','A-P050','A-P060']
    for loc in historical:slots.loc[slots.old_location.eq(loc)&slots.status.str.startswith('unmapped'),'status']='historical_scope_or_original_development_result; current counterparts separately archived; not B1 carry-forward'
    replacement={'D-P039':'core_metrics.csv','D-P041':'VIF_summary.csv','D-P084':'H0_R1_B1_increments.csv','D-P093':'regional_reference_ranges.csv','D-P097':'H0_R1_B1_increments.csv','D-P106':'storm_prediction_correlations.csv','D-P111':'period_comparison.csv','D-P116':'Tables3_F_complete_coefficients.csv','A-P027':'descriptive_statistics.csv','A-P044':'../R04_B1_all_valid_v1/main_R0c/stage_composition.csv','A-P054':'AppendixD_period_stage_counts.csv'}
    regional=[]
    for t in ['E0','R0c']:
        v=pd.read_csv(RUN/f'main_{t}/figure6_regional_reference.csv');v=v[v.status.eq('descriptive_common_calendar')];regional.append({'target':t,'LAD':len(v),'exp_reference_min':v.exp_mean_eta.min(),'exp_reference_max':v.exp_mean_eta.max(),'map_max_min_ratio':v.exp_mean_eta.max()/v.exp_mean_eta.min(),'arithmetic_mean_claim':False})
    table(Q/'tables/regional_reference_ranges.csv',pd.DataFrame(regional))
    for old,row in [('1.96',regional[0]),('1.41',regional[1])]:bind('D-P093',old,row['map_max_min_ratio'],'map exponentiated reference max/min ratio','regional_reference_ranges.csv',row['target'])
    for loc,artifact in replacement.items():
        mask=slots.old_location.eq(loc)&slots.status.str.startswith('unmapped');slots.loc[mask,'status']='old_combined_sentence_requires_rewrite; all current numerical components in named dataset; not automatic substitution';slots.loc[mask,'current_artifact']=str(Q/'tables'/artifact)
    # Remaining locations below contain mathematical indices, references, dates or stated definitions.
    metadata=['D-P002','D-P006','D-P008','D-P010','D-P011','D-P012','D-P016','D-P017','D-P018','D-P023','D-P030','D-P038','D-P040','D-P046','D-P047','D-P048','D-P050','D-P051','D-P054','D-P057','D-P058','D-P060','D-P061','D-P064','D-P067','D-P071','D-P072','D-P073','D-P076','D-P080','D-P094','D-P101','D-P102','D-P103','D-P108','D-P110','D-P121','D-P122','A-P003','A-P013','A-P015','A-P018','A-P040','A-P065','A-P071','A-P073','A-P076','A-P091','A-P092']
    for loc in metadata:slots.loc[slots.old_location.eq(loc)&slots.status.str.startswith('unmapped'),'status']='citation_date_equation_index_or_definition; no model-derived replacement; source wording limits remain in MR'
    table(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',slots);table(Q/'tables/CURRENT_PARAGRAPH_NUMERIC_BINDINGS.csv',pd.DataFrame(notes))
    fd=read(Q/'checks/final_data.json');fd.update(paragraph_bindings=len(notes),unmapped_legacy_slots=int(slots.status.str.startswith('unmapped').sum()),requires_sentence_rewrite_slots=int(slots.status.str.startswith('old_combined_sentence').sum()));save(Q/'checks/final_data.json',fd)
    print('numeric acceptance',len(notes),'paragraph bindings;',fd,flush=True)
if __name__=='__main__':run()
