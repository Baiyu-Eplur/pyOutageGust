from common import *
from prediction import physical_gust_terms,minimum_interface
from statsmodels.stats.sandwich_covariance import cov_cluster
import importlib.util

def run():
    e=events();b=read(W/'baseline/B1_MANIFEST.json');files=[]
    for x in b['outputs']:
        p=Path(x['path']);ok=p.exists();h=sha(p) if ok else None;files.append({'path':str(p),'exists':ok,'size_match':ok and p.stat().st_size==x['bytes'],'hash_match':h==x['sha256'],'sha256':h})
    assert all(x['exists'] and x['size_match'] and x['hash_match'] for x in files);table(Q/'tables/B1_FILE_AUDIT.csv',pd.DataFrame(files))
    scores=[];folds=[];decomp=[];models=[];mapping=pd.read_csv(CORE/'folds/date_to_fold.csv').set_index('date_utc').fold
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        d=members(e,g,t);m=model(g,t);assert set(d[ID])==set(m['training_ids']);eta=predict_eta(d,m);prep=fit_preprocessor(d,t);assert all(np.isclose(prep[key][c],m['preprocessor'][key][c],atol=1e-12,rtol=0) for key in ['mean','sd'] for c in prep[key]);dest=RUN/f'{g}_{t}';metrics=read(dest/'metrics.json');nested={}
        models.append({'path':str(dest/'full_model.json'),'n':len(d),'membership':True,'preprocessor':True,'finite_eta':bool(np.isfinite(eta).all()),'metadata':m['metadata']})
        for block,ms in metrics.items():
            p=pd.read_csv(dest/f'oof_{block}.csv',float_precision='round_trip').set_index(ID).loc[d[ID]].reset_index();assert p[ID].is_unique and len(p)==len(d);assert np.array_equal(p.y,target(d,t));assert np.array_equal(p.fold,d.new_date_utc.map(mapping));nested[block]=p[[ID,'fold','y']]
            fs=[]
            for f,sub in p.groupby('fold'):
                fm=read(dest/f'model_fold{f}_{block}.json');ev=d[d[ID].isin(sub[ID])];tr=d[d[ID].isin(fm['training_ids'])];assert len(tr)+len(ev)==len(d);assert not(set(tr.new_date_utc)&set(ev.new_date_utc));er=float(np.max(np.abs(predict_eta(ev,fm)-sub.set_index(ID).loc[ev[ID]].prediction_eta)));assert er<1e-12
                pp=fit_preprocessor(tr,t);assert all(np.isclose(pp[key][c],fm['preprocessor'][key][c],atol=1e-12,rtol=0) for key in ['mean','sd'] for c in pp[key]);models.append({'path':str(dest/f'model_fold{f}_{block}.json'),'n':len(tr),'membership':True,'preprocessor':True,'eta_maxerr':er,'metadata':fm['metadata']})
                ss=score(sub.y,sub.prediction_eta);row={'group':g,'target':t,'block':block,'fold':f,'n':len(sub),'mean_y':sub.y.mean(),'SSE':ss['SSE'],'SST_within':ss['SST'],'R2':ss['r2']};folds.append(row);fs.append(row)
            full=score(p.y,p.prediction_eta);mf=float(np.mean([x['R2'] for x in fs]));assert np.isclose(full['r2'],ms['pooled_oof_r2'],atol=1e-12,rtol=0) and np.isclose(mf,ms['mean_fold_r2'],atol=1e-12,rtol=0)
            scores.append({'group':g,'target':t,'block':block,**full,'mean_fold_R2':mf,'pooled_R2':full['r2'],'evaluation_identity':identity(p[ID]),'all_test_tails_retained':True,'status':'passed'})
            if block==m['block']:
                within=sum(x['SST_within'] for x in fs);between=sum(x['n']*(x['mean_y']-p.y.mean())**2 for x in fs);sse=sum(x['SSE'] for x in fs);assert np.isclose(full['SST'],within+between,atol=1e-8) and np.isclose(full['SSE'],sse,atol=1e-8);wr=1-sse/within
                decomp.append({'group':g,'target':t,'n':len(p),'SSE_total':sse,'SST_pooled':full['SST'],'sum_within_SST':within,'between_fold_mean_SST':between,'between_SST_share':between/full['SST'],'pooled_R2':full['r2'],'mean_fold_R2':mf,'within_SST_weighted_fold_R2':wr,'weighting_component_R2':wr-mf,'between_mean_denominator_component_R2':full['r2']-wr,'gap_R2':full['r2']-mf,'gap_percentage_points':100*(full['r2']-mf)})
        assert all(x.equals(next(iter(nested.values()))) for x in nested.values())
    table(Q/'OOF_SCORE_AUDIT.csv',pd.DataFrame(scores));table(Q/'OOF_FOLD_DECOMPOSITION.csv',pd.DataFrame(folds));table(Q/'tables/OOF_SST_DECOMPOSITION.csv',pd.DataFrame(decomp));put(Q/'checks/core_archive_readback.json',{'passed':True,'archives':models,'new_fits':0})
    # Cubic evaluation is paired to the frozen quadratic predictions.
    cub=[]
    for t in ['E0','R0c']:
        p=pd.read_csv(R4/f'supplements_v1/{t}_cubic_paired_OOF.csv',float_precision='round_trip');q=score(p.y,p.prediction_eta);c=score(p.y,p.cubic_eta);assert p[ID].is_unique;cub.append({'target':t,'n':len(p),'quadratic_R2':q['r2'],'cubic_R2':c['r2'],'delta_R2':c['r2']-q['r2'],'delta_pp':100*(c['r2']-q['r2'])})
    table(Q/'tables/CUBIC_PAIRED_AUDIT.csv',pd.DataFrame(cub))
    dr=pd.DataFrame(decomp);weather=dr[(dr.group=='weather')&(dr.target=='R0c')].iloc[0]
    write(Q/'OOF_SCORE_AUDIT.md','# R05-2正式OOF复核\n\n从冻结逐事件OOF重算12块；目标、ID、共同fold、测试长尾、训练内ddof=1尺度及再读预测检查通过；本轮零模型重拟合。pooled主指标不变，mean-fold透明并列。\n\n'+md(pd.DataFrame(scores)[['group','target','block','n','pooled_R2','mean_fold_R2','SSE','SST']])+'\n## 全模型折内/折间分解\n\n'+md(dr)+f'\n天气R0c差距为{weather.gap_percentage_points:.8f}个百分点。先按折内SST加权而非等权平均，贡献{100*weather.weighting_component_R2:.8f}个百分点；再由折间均值项增加pooled分母，贡献{100*weather.between_mean_denominator_component_R2:.8f}个百分点。两者相加为总差距。这是统计量恒等分解，不是模型学会折间均值的能力证明，也不能据此更换主评分。每折原始n、均值、SSE、SST、R²见OOF_FOLD_DECOMPOSITION.csv。\n\nG|K=R²(GK)−R²(K)，K|G=R²(GK)−R²(G)，百分点为差值乘100，不是比例。三阶增量见CUBIC_PAIRED_AUDIT.csv，无新拟合或强制正分。\n')
    # Covariance: compare archived one-way components to statsmodels tuple API, no OLS .fit.
    covrows=[];cons=[];periods=[];guards=[]
    spec=importlib.util.spec_from_file_location('copied_calendar',Q/'frozen/R04_src/calendar_repair.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for path in sorted((R4/'periods_v2').glob('*.json')):
        m=read(path);d=e[e[ID].isin(m['training_ids'])];x=design(d,m['preprocessor'],m['block'])[m['columns']].to_numpy();co=np.array(m['parameters']);res=target(d,m['target'])-x@co;bread=np.linalg.pinv(x.T@x);cov=m['covariance'];n,k=x.shape;g=m['metadata']['group'];t=m['target'];per=m['metadata']['period'];pressure=model(g,t)['preprocessor']['mean']['pressure_msl_0h'];prep=m['preprocessor'];sg=prep['sd']['gust_0h'];mu=prep['mean']['gust_0h'];zp=(pressure-prep['mean']['pressure_msl_0h'])/prep['sd']['pressure_msl_0h'];j=np.zeros((2,k));cols=m['columns'];j[0,cols.index('zG')]=1/sg;j[0,cols.index('zG2')]=-2*mu/sg**2;j[0,cols.index('zG_zPressure')]=zp/sg;j[1,cols.index('zG2')]=1/sg**2
        for key,group in [('LAD',d.LAD21CD),('date',d.new_date_utc),('intersection',d.LAD21CD+'|'+d.new_date_utc)]:
            ref=cov_cluster((x*res[:,None],bread),pd.factorize(group)[0],use_correction=True);assert np.allclose(ref,cov[key],atol=1e-8,rtol=1e-5)
        assert np.allclose(np.array(cov['LAD'])+cov['date']-np.array(cov['intersection']),cov['two_way'],atol=1e-12,rtol=0)
        for key,values in cov.items():
            v=np.array(values);ev=np.linalg.eigvalsh((v+v.T)/2);trans=j@v@j.T;scale=np.linalg.norm(v,ord=2);tol=max(1e-12,scale*1e-10);covrows.append({'model':path.stem,'covariance':key,'n':n,'effective_k':k,'symmetry_maxerr':np.max(np.abs(v-v.T)),'min_eigenvalue':ev.min(),'max_abs_eigenvalue':max(abs(ev)),'negative_diagonal_n':int((np.diag(v)<0).sum()),'PSD_at_scaled_tolerance':bool(ev.min()>=-tol),'scaled_tolerance':tol,'physical_linear_variance':trans[0,0],'physical_quadratic_variance':trans[1,1],'physical_2x2_min_eigenvalue':np.linalg.eigvalsh(trans).min(),'clusters_and_factors':json.dumps(m['covariance_factors'])})
        ph=physical_gust_terms(m,pressure);mi=minimum_interface(m,pressure,np.quantile(d.gust_0h,[.01,.99]));se=np.sqrt(np.diag(j@np.array(cov['LAD'])@j.T));old=pd.read_csv(R4/'tables/period_comparison.csv');row=old[(old.group==g)&(old.target==t)&(old.period==per)].iloc[0];assert np.allclose([ph['physical_linear_gust'],ph['physical_quadratic_gust'],*se],[row.physical_linear_gust,row.physical_quadratic_gust,row.physical_linear_SE,row.physical_quadratic_SE],atol=1e-12,rtol=0)
        periods.append({'model':path.stem,'n':n,'gust_mean':mu,'gust_sd':sg,'pressure_reference_hPa':pressure,**ph,'minimum_ms':mi['minimum_ms'],'minimum_status':mi['status'],'minimum_failure':mi.get('failure_reason'),'support_low':mi['support_ms'][0],'support_high':mi['support_ms'][1],'physical_linear_LAD_SE':se[0],'physical_quadratic_LAD_SE':se[1]})
        supported={tuple(v) for v in m['supported_calendar']};bad=next(((yr,mo) for yr in prep['years'] for mo in prep['months'] if (yr,mo) not in supported),None)
        assert bad is not None;test=d.iloc[:1].copy();test['new_year']=bad[0];test['new_month']=bad[1]
        try:module.predict_supported(test,m);raise AssertionError('unsupported separately-seen combination admitted')
        except ValueError:pass
        seen_error=float(np.max(np.abs(module.predict_supported(d.iloc[:2],m)-x[:2]@co)));assert seen_error<1e-12;guards.append({'model':path.stem,'year':bad[0],'month':bad[1],'both_separately_seen':True,'combination_unseen':True,'rejected':True,'seen_eta_maxerr':seen_error,'tolerance':1e-12})
        for consumer,inference in [('R04/tables/period_comparison.csv','physical linear/quadratic SE: LAD only'),('R04/figures/figure10.png/.pdf','point only; no covariance or interval'),('minimum_interface','conditional point/support only; no delta-method CI')]:cons.append({'model':path.stem,'consumer':consumer,'actual_use':inference,'two_way_matrix_used':False,'rule':'No automatic PSD repair or arbitrary-direction Wald test; inspect actual contrast before future use'})
    cv=pd.DataFrame(covrows);table(Q/'tables/PERIOD_COVARIANCE_AUDIT.csv',cv);table(Q/'tables/PERIOD_PHYSICAL_AUDIT.csv',pd.DataFrame(periods));table(Q/'COVARIANCE_CONSUMERS.csv',pd.DataFrame(cons));put(Q/'checks/calendar_combination_guard.json',guards)
    bad=cv[(cv.covariance=='two_way')&~cv.PSD_at_scaled_tolerance];assert len(bad)==6
    write(Q/'COVARIANCE_AND_PERIOD_AUDIT.md','# R05-3分期/协方差及消费者核查\n\n8个现存档案再读，零重拟合。各自尺度、固定物理气压、物理一次/二次项和LAD SE与R04逐值相符；最低点仍按各自p1–p99支持判定。新增8个“年与月分别见过、组合未见过”守卫检查全部拒绝，已见组合预测通过。\n\n## 六个非半正定双向矩阵\n\n'+md(bad[['model','min_eigenvalue','max_abs_eigenvalue','negative_diagonal_n','physical_linear_variance','physical_quadratic_variance','physical_2x2_min_eigenvalue']])+'\n三项单向CR1实际矩阵与复制statsmodels的scores/bread接口一致；双向确为LAD+date−交集。有限样本修正按实际G、n、满秩k，矩阵对称性/尺度容差均记录。没有证据指向加减或自由度实现错误；当前估计量在这些样本上的非PSD性不能由非负对角消除。未裁特征值、未按显著性换协方差。\n\n当前分期表仅用LAD物理项SE；图10仅点，无双向区间；最低点不附CI。实际保留物理线性组合aᵀVa及二维变换A V Aᵀ已列，不能因此许可整个非PSD矩阵用于任意联合Wald检验。现有科学参数SE与当前点图不因此全作废。未来若确需双向分期联合推断，V00需先冻结针对性比较和有效推断方案，不能任意挑方向制造新检验。\n\n全期四组的三类CR1另有R04实际验证记录且本轮哈希/参数身份相符，与这6个分期矩阵的结论分开。全部消费者见COVARIANCE_CONSUMERS.csv，数值详表见PERIOD_COVARIANCE_AUDIT.csv。\n')
    # Count actual producer artifacts, distinguishing returned diagnostics from archived scientific models.
    corepaths=list(RUN.glob('*/full_model.json'))+list(RUN.glob('*/model_fold*.json'))+list(RUN.glob('*/step27_model_*.json'))+list(RUN.glob('*/period_development_model.json'))
    r1paths=list((R4/'R1_input_compat_v1').glob('*/full_model.json'))+list((R4/'R1_input_compat_v1').glob('*/model_fold*.json'))
    pp=list((R4/'periods_v2').glob('*.json'));sp=list((R4/'supplements_v1').glob('*GLM.json'))+list((R4/'supplements_v1').glob('*cubic_fold*.json'))+list((R4/'supplements_v1').glob('*cubic_full.json'))+list((R4/'supplements_v1').glob('six_group_*.json'))
    counts={'core':len(corepaths),'R1':len(r1paths),'period':len(pp),'supplement':len(sp)};assert counts=={'core':70,'R1':64,'period':8,'supplement':22}
    put(Q/'checks/producer_inventory.json',{'counts':counts,'current_total':164,'superseded_archives':[record(p) for p in (R4/'periods').glob('*.json')],'unarchived_aborted_solves':1,'verification_fits_in_R04':32,'evidence_for_unarchived':'R04/logs/calendar_repair_v2.txt and preserved source, not a fabricated archive','R05_new_fits':0,'archives':[record(p) for p in corepaths+r1paths+pp+sp]})
    put(Q/'checks/numerical_audit.json',{'passed':True,'B1_files':len(files),'core_models_reloaded':len(models),'OOF_blocks':12,'periods':8,'nonPSD_period_two_way':6,'new_model_fits':0})
    print('R05 numerical and covariance audit passed; zero fits',flush=True)
if __name__=='__main__':run()
