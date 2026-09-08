"""Minimal smoke and explicitly invoked later formal producer use the same functions."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from contracts import *
from producer import *
from prediction import reference_curve,minimum_interface,storm_event_predictions,regional_reference,physical_gust_terms,figure4_data,figure7_data
from diagnostics import vif_table,covariance_producer,stage_composition,stage_closure
from retained import figure6_data,period_comparison

def select_smoke(base,foldmap,n_per_cell):
    d=attach_folds(base,foldmap)
    # Outcome-blind selection, with every observed calendar year/month/fold represented.
    d['_pick']=d[ID].map(lambda x:__import__('hashlib').sha256(('R03_smoke_v1:'+x).encode()).hexdigest())
    return d.sort_values('_pick').groupby(['new_year','new_month','fold'],sort=True).head(n_per_cell).drop(columns=['_pick','fold']).sort_values(ID).reset_index(drop=True)
def run(config,formal=False):
    if formal and config['purpose']=='non_inferential_smoke':raise ValueError('smoke cannot be relabelled B1')
    output=Path(config['output_root']).resolve()
    if not output.is_relative_to(WORK) or output.exists():raise ValueError('output must be new and within revision work root')
    base,em=step0_build_sample(config)
    if sha(config['fold_map'])!=config['fold_map_sha256']:raise ValueError('fold map changed')
    mapping=pd.read_csv(config['fold_map'],dtype={'date_utc':str})
    if identity(base[ID])!=config['fold_base_ids_sha256']:raise ValueError('fold base membership changed')
    sample=base if formal else select_smoke(base,mapping,config['smoke_rows_per_year_month_fold'])
    output.mkdir(parents=True)
    save_json(output/'config.json',config,output);sample[[ID,'new_date_utc','new_year','new_month','LAD21CD']].to_csv(output/'selected_members.csv',index=False)
    windows=read(ROOT/'configs/storm_windows.json');runs=[];full_models={};period_count=0;blocked_products=[]
    for target_name in config['targets']:
        targetmain=sample.loc[sample['candidate_main_'+target_name]].copy()
        for group in config['groups']:
            dest=output/f'{group}_{target_name}';result=run_oof(targetmain,mapping,group,target_name,config);publish_oof(result,dest)
            training,tail=training_population(targetmain,group,target_name,'all_valid')
            prep=fit_preprocessor(training,target_name);block='G' if target_name=='E0' else 'GK'
            model=fit_ols(training,prep,block,{'run_id':config['run_id'],'purpose':config['purpose'],'input_version':config['input_version'],'config_sha256':config_hash(config),'code_identity':code_identity(),'group':group,'fit_type':'all_valid_full_sample_descriptive','tail':tail})
            file=dest/'full_model.json';save_json(file,model,output);reloaded=read(file)
            assert np.array_equal(predict_eta(training,model),predict_eta(training,reloaded))
            x=design(training,prep,block);vif,vm=vif_table(x);vif.to_csv(dest/'VIF.csv',index=False);save_json(dest/'VIF_manifest.json',vm,output)
            cov=covariance_producer(training,model);save_json(dest/'cluster_covariance.json',cov,output)
            grid=np.linspace(*np.quantile(training.gust_0h,[.01,.99],method='linear'),50)
            curve,meta=figure4_data(file,config['run_id'],training,grid,allow_smoke=not formal);curve.to_csv(dest/'figure4_curve_data.csv',index=False);save_json(dest/'figure4_reference.json',meta,output)
            gust_curve,gust_meta=figure7_data(file,config['run_id'],training,'gust_0h',grid,allow_smoke=not formal);save_json(dest/'figure7_gust_ratio.json',gust_meta,output)
            minimum=minimum_interface(model,prep['mean']['pressure_msl_0h'],[float(grid.min()),float(grid.max())]);save_json(dest/'conditional_minimum_no_CI.json',minimum,output)
            storm=storm_event_predictions(training,model,windows);storm.to_csv(dest/'figure9_descriptive_events.csv',index=False)
            fold_models={m['metadata']['fold']:m for m in result['models'] if m['block']==block}
            storm_oof=storm_event_predictions(training,model,windows,prediction_source='OOF_date_group_diagnostic',oof=result['predictions'][block],oof_models=fold_models);storm_oof.to_csv(dest/'figure9_OOF_diagnostic_events.csv',index=False)
            mapdata,mapmeta=figure6_data(file,config['run_id'],training,base,allow_smoke=not formal);mapdata.to_csv(dest/'figure6_regional_reference.csv',index=False);save_json(dest/'figure6_reference.json',mapmeta,output)
            full_models[(group,target_name)]=model
            runs.append({'target':target_name,'group':group,'sample_n':len(training),'date_groups':training.new_date_utc.nunique(),'LAD_groups':training.LAD21CD.nunique(),'columns':len(x.columns),'rank':vm['design_rank'],'OOF_fit_count':len(result['models']),'full_fit_count':1,'archive_prediction_exact':True,'non_inferential_smoke':not formal})
            if target_name=='R0c':
                tab,pool,stage=stage_composition(training);tab.to_csv(dest/'stage_composition.csv',index=False);pool.to_csv(dest/'stage_pooled.csv',index=False);save_json(dest/'stage_manifest.json',stage,output)
                customer_grid=np.expm1(np.linspace(*np.quantile(np.log1p(training[C]),[.01,.99],method='linear'),50));cc,cm=figure7_data(file,config['run_id'],training,C,customer_grid,allow_smoke=not formal);cc.to_csv(dest/'figure7_customer_curve.csv',index=False);save_json(dest/'figure7_reference.json',cm,output)
                stagecoef,stage_models,single_bins,stage_info=stage_closure(training,model['metadata']);stagecoef.to_csv(dest/'step27_stage_coefficients.csv',index=False)
                for i,stage_model in enumerate(stage_models):save_json(dest/f'step27_model_{i}.json',stage_model,output)
                if single_bins is not None:single_bins.to_csv(dest/'step27_single_stage_bins.csv',index=False)
                save_json(dest/'step27_manifest.json',stage_info,output)
            if group=='main':
                periods,period_models=period_comparison(training,target_name,model['metadata'],prep['mean']['pressure_msl_0h']);periods.to_csv(dest/'figure10_period_physical_terms.csv',index=False)
                period_count+=len(period_models)
                for row in periods.loc[periods.status.str.startswith('blocked')].to_dict('records'):blocked_products.append({'product':f'figure10_{target_name}',**row})
                for pm in period_models:save_json(dest/f"period_{pm['metadata']['period']}_model.json",pm,output)
    summary={'run_id':config['run_id'],'purpose':config['purpose'],'input_event_sha256':em['event_table']['sha256'],'config_sha256':config_hash(config),'code_identity':code_identity(),'selected_n':len(sample),'selected_dates':sample.new_date_utc.nunique(),'fold_map_sha256':config['fold_map_sha256'],'runs':runs,'formal_B1':formal,'OOF_fit_count':sum(x['OOF_fit_count'] for x in runs),'full_fit_count':sum(x['full_fit_count'] for x in runs),'stage_diagnostic_fit_count':2*sum(x['target']=='R0c' for x in runs),'period_fit_count':period_count,'isolated_blocked_products':blocked_products,'intervals_generated':0,'bootstrap_runs':0,'Word_modified':False}
    save_json(output/'RUN_MANIFEST.json',summary,output)
    assert sha(em['event_table']['path'])==em['event_table']['sha256']
    print(json.dumps(clean(summary),ensure_ascii=False),flush=True)
