from common import *
from prediction import minimum_interface
from scipy import stats
import re

def run():
    e=events();main=members(e,'main','E0');metrics=pd.read_csv(Q/'tables/core_metrics.csv');r1=pd.read_csv(Q/'tables/R1_metrics.csv');h0=pd.read_csv(Q/'frozen/H0/oof_metric_comparison.csv');rows=[];paired=[];shape=[]
    for x in h0.to_dict('records'):
        if x['block']=='regional_time':continue
        g,t=x['sample'].rsplit('_',1);n=len(pd.read_csv(Q/'frozen/H0'/f'{g}_{t}_folds.csv'));rows.append({'version':'H0','group':g,'target':t,'block':{'B':'control','BG':'G','BC':'K','BGC':'GK'}[x['block']],'n':n,'pooled_R2':x['pooled_oof_r2'],'mean_fold_R2':x['mean_fold_r2']})
    combined=pd.concat([pd.DataFrame(rows),r1,metrics],ignore_index=True);table(Q/'tables/H0_R1_B1_metrics.csv',combined)
    fullsummary=pd.read_csv(Q/'frozen/H0/full_fit_summary.csv').set_index('sample');terms={'zG':'z_gust_0h','zG2':'z_gust_0h_sq','zG_zPressure':'z_gust_pressure'}
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        block='G' if t=='E0' else 'GK';hp=pd.read_csv(Q/'frozen/H0'/f'{g}_{t}_oof_predictions.csv').set_index(ID);rp=pd.read_csv(Q/'R1_input_compat_v1'/f'{g}_{t}/oof_{block}.csv').set_index(ID);bp=pd.read_csv(RUN/f'{g}_{t}/oof_{block}.csv').set_index(ID)
        for left,right,lp,rpp,lcol,rcol,ly,ry in [('H0','B1',hp,bp,'BG' if t=='E0' else 'BGC','prediction_eta','observed','y'),('H0','R1',hp,rp,'BG' if t=='E0' else 'BGC','prediction_eta','observed','y'),('R1','B1',rp,bp,'prediction_eta','prediction_eta','y','y')]:
            ids=lp.index.intersection(rpp.index);a=lp.loc[ids];b=rpp.loc[ids];paired.append({'group':g,'target':t,'comparison':left+'→'+right,'common_n':len(ids),'eta_difference_RMSE':np.sqrt(np.mean((a[lcol]-b[rcol])**2)),'left_common_R2':score(a[ly],a[lcol])['r2'],'right_common_R2':score(b[ry],b[rcol])['r2'],'target_max_difference':np.max(np.abs(a[ly]-b[ry])),'fold_same_n':int(a.fold.eq(b.fold).sum()),'interpretation':'common-event descriptive comparison; training populations and date assignment differ'})
        for ver,path in [('R1',Q/'R1_input_compat_v1'/f'{g}_{t}/full_model.json'),('B1',RUN/f'{g}_{t}/full_model.json')]:
            m=read(path);d=e.loc[e[ID].isin(m['training_ids'])];p=dict(zip(m['columns'],m['parameters']));q=m['preprocessor'];v=minimum_interface(m,q['mean']['pressure_msl_0h'],np.quantile(d.gust_0h,[.01,.99]));shape.append({'version':ver,'group':g,'target':t,'n':len(d),'beta_gust':p['zG'],'beta_gust2':p['zG2'],'beta_interaction':p['zG_zPressure'],'gust_mean':q['mean']['gust_0h'],'gust_sd':q['sd']['gust_0h'],'physical_quadratic':p['zG2']/q['sd']['gust_0h']**2,'conditional_minimum_ms':v['minimum_ms'],'minimum_status':v['status'],'CI':'not_estimated'})
        cf=pd.read_csv(Q/'frozen/H0'/f'{g}_{t}_full_coefficients.csv').set_index('term');s=fullsummary.loc[f'{g}_{t}'];shape.append({'version':'H0','group':g,'target':t,'n':s['n'],'beta_gust':cf.loc['z_gust_0h','coefficient'],'beta_gust2':cf.loc['z_gust_0h_sq','coefficient'],'beta_interaction':cf.loc['z_gust_pressure','coefficient'],'gust_mean':s.gust_mean,'gust_sd':s.gust_sd,'physical_quadratic':cf.loc['z_gust_0h_sq','coefficient']/s.gust_sd**2,'conditional_minimum_ms':s.physical_minimum_at_mean_pressure,'minimum_status':'historical_algebraic_vertex_not_recertified','CI':'historical_not_reused'})
    table(Q/'tables/common_event_prediction_comparison.csv',pd.DataFrame(paired));table(Q/'tables/H0_R1_B1_shape.csv',pd.DataFrame(shape))
    increments=[]
    for (ver,g,t),sub in combined.groupby(['version','group','target']):
        r=dict(zip(sub.block,sub.pooled_R2));row={'version':ver,'group':g,'target':t,'gust_from_control':r['G']-r['control']}
        if t=='R0c':row.update(customers_from_control=r['K']-r['control'],gust_given_customers=r['GK']-r['K'],customers_given_gust=r['GK']-r['G'])
        increments.append(row)
    table(Q/'tables/H0_R1_B1_increments.csv',pd.DataFrame(increments))
    # Reproduce the original first-stage comparator's actual stage-number rule, not earliest timestamp.
    v3=next(x for x in read(W/'inventory/large_input_identity.json') if x['key']=='v3');source=pd.read_csv(v3['path'],usecols=[ID,'Restoration Stage','Number of Customers Restored'],low_memory=False);source=source.loc[source[ID].isin(main[ID])].copy();source['source_order']=np.arange(len(source));first=source.sort_values([ID,'Restoration Stage']).drop_duplicates(ID).set_index(ID)
    vals=pd.to_numeric(first['Number of Customers Restored'].astype(str).str.replace(',',''),errors='coerce');agg=main[C].astype(float).mean();timemean=main['Number of Customers Restored'].astype(float).mean();customer={'n':len(main),'lowest_stage_number_mean':vals.mean(),'lowest_stage_nonmissing_n':vals.notna().sum(),'aggregated_customer_mean':agg,'ratio_aggregate_to_lowest_stage':agg/vals.mean(),'earliest_record_time_customer_mean':timemean,'ratio_aggregate_to_earliest_time':agg/timemean,'definitions_differ':True,'source_v3_sha256':v3['sha256'],'source_script':'frozen step38_F4_customers_mean_ratio.py','no_initial_customer_information_claim':True};save(Q/'tables/customer_aggregation_comparison.json',customer);table(Q/'data/first_stage_comparison.csv',first.reset_index())
    # Current replacements for table/appendix numerical blocks.
    description=[]
    for t in ['E0','R0c']:
        d=members(e,'main',t);raw=d[C] if t=='E0' else d[D];log=target(d,t)
        for scale,values in [('raw',raw),('log',pd.Series(log))]:
            for name,val in [('Mean',values.mean()),('Median',values.median()),('SD',values.std(ddof=1)),('Min',values.min()),('25th pct.',values.quantile(.25)),('75th pct.',values.quantile(.75)),('Max',values.max())]:description.append({'target':t,'scale':scale,'statistic':name,'value':val,'n':len(d)})
    table(Q/'tables/Table1_current.csv',pd.DataFrame(description))
    cfs=pd.read_csv(Q/'tables/full_coefficients_CR1.csv');cfs['p_normal_CR1_descriptive']=2*stats.norm.sf(np.abs(cfs.coefficient/cfs.SE));table(Q/'tables/Tables3_F_complete_coefficients.csv',cfs)
    d=members(e,'main','R0c');s=d.groupby('stage_row_count').size().rename('n').reset_index();s['pct']=100*s.n/len(d);table(Q/'tables/AppendixD_stage_counts.csv',s)
    supp=pd.read_csv(Q/'supplements_v1/six_groups_OOF.csv');six=e.loc[e[ID].isin(supp[ID])].copy();six['gust_decile']=pd.qcut(six.gust_0h,10,duplicates='drop');dec=six.groupby('gust_decile',observed=True).agg(n=(ID,'size'),weather_n=('cause_group_event',lambda s:s.eq('weather_natural').sum()));dec['weather_pct']=100*dec.weather_n/dec.n;table(Q/'tables/AppendixG_gust_deciles.csv',dec.reset_index())
    pressures=[];m=model('main','E0');p=m['preprocessor'];support=np.quantile(main.gust_0h,[.01,.99])
    for z in [-1,0,1]:pressures.append({'pressure_z':z,**minimum_interface(m,p['mean']['pressure_msl_0h']+z*p['sd']['pressure_msl_0h'],support)})
    save(Q/'tables/AppendixH_pressure_minima.json',pressures)
    # Exhaustive old-number inventory includes explicit absence/status; no silent carry-forward.
    mr=read(W/'manuscript_record/REVISION_ITEMS.json')['items'];inventory=[]
    for doc in ['D','A']:
      for item in read(W/'manuscript_record'/f'{doc}_word_index.json'):
        loc=item['id'];links=[v['id'] for v in mr if loc in v['locations']];claims=sorted({c for v in mr if loc in v['locations'] for c in v.get('claim_ids',[])})
        texts=[('',item.get('text',''))] if item['type']=='paragraph' else [(f'row{ri+1}col{ci+1}',str(cell)) for ri,row in enumerate(item['rows']) for ci,cell in enumerate(row)]
        for cell,text in texts:
          for match in re.finditer(r'(?<![A-Za-z])[-+−]?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][−+-]?\d+)?%?',text):
            status='needs_semantic_mapping_before_W';artifact=None
            if loc in ['A-T07','A-T12']:status='historical_development_or_bootstrap_only_no_new_CI'
            if doc=='D' and item['type']=='paragraph' and int(loc.split('P')[-1])>=125:status='bibliographic_metadata_not_new_result'
            amap={'D-T01':'Table1_current.csv','D-T03':'Tables3_F_complete_coefficients.csv','D-T04':'H0_R1_B1_increments.csv','A-T03':'../supplements_v1/six_group_-1.json','A-T04':'AppendixD_stage_counts.csv','A-T05':'../R04_B1_all_valid_v1/main_R0c/step27_stage_coefficients.csv','A-T08':'Tables3_F_complete_coefficients.csv','A-T09':'Tables3_F_complete_coefficients.csv','A-T10':'AppendixG_gust_deciles.csv','A-T11':'AppendixH_pressure_minima.json','A-T13':'period_comparison.csv'}
            if loc in amap:status='current_replacement_dataset_available_not_automatic_token_substitution';artifact=str(Q/'tables'/amap[loc])
            inventory.append({'old_location':loc,'cell':cell,'old_numeric_token':match.group(),'old_context':text,'new_value':None,'unit':'requires_semantic_interpretation','status':status,'current_artifact':artifact,'MR':','.join(links),'CL':','.join(claims),'Word_status':'not_modified'})
    table(Q/'tables/ALL_MANUSCRIPT_NUMERIC_SLOTS.csv',pd.DataFrame(inventory))
    save(Q/'checks/report_data.json',{'old_numeric_slots':len(inventory),'customer_comparison':customer,'all_numerical_slots_explicit_status':True,'text_token_inventory_not_formula_or_image_OCR':True,'fits':0})
    print(json.dumps(clean(customer),ensure_ascii=False),flush=True)
if __name__=='__main__':run()
