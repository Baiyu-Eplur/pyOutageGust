"""Deterministic format/summary adapters. No fitting, weather calls or new scoring."""
import ast
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pandas as pd
from .catalog import ROOT

C = 'customers_v2_event_excl_reinterruptions'
D = 'duration_B_full_span_hours'
A = 'duration_A_customer_weighted_hours'

def read(path):
    return pd.read_csv(ROOT/path, float_precision='round_trip')

def js(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def docx(path):
    with zipfile.ZipFile(ROOT/path) as z:
        return ET.fromstring(z.read('word/document.xml'))

NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def words(element):
    return ''.join(t.text or '' for t in element.findall('.//w:t',NS))

def literal(path, name):
    """Read a saved literal only; never import legacy scripts that fit at import."""
    tree=ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f'Missing literal {name} in {path}')

def table(out, stem, frame, r):
    d=frame if isinstance(frame,pd.DataFrame) else pd.DataFrame(frame)
    if not len(d.columns): raise ValueError('Empty table schema: '+stem)
    path=out/'tables'/f'{stem}.csv'; path.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(path,index=False,encoding='utf-8-sig',float_format='%.17g')
    # This validates serialization, not scientific algorithms.
    got=pd.read_csv(path,float_precision='round_trip')
    if list(got.columns)!=list(d.columns) or len(got)!=len(d): raise ValueError('Table serialization changed shape')
    for col in d.select_dtypes(include='number'):
        if not np.allclose(d[col].astype(float),pd.to_numeric(got[col]).astype(float),rtol=1e-14,atol=1e-15,equal_nan=True):
            raise ValueError('Table serialization changed numbers: '+col)
    def cell(v):
        if v is None or (not isinstance(v,(list,dict)) and pd.isna(v)): return 'NA'
        if isinstance(v,float): return f'{v:.10g}'
        return str(v).replace('|','\\|').replace('\n','<br>')
    rows=['| '+' | '.join(map(str,d.columns))+' |','| '+' | '.join(['---']*len(d.columns))+' |']
    rows += ['| '+' | '.join(cell(v) for v in row)+' |' for row in d.itertuples(index=False,name=None)]
    path.with_suffix('.md').write_text(f"# {stem}\n\n需求 {r['requirement_id']}；{r['subsection']}。{r['question']}。\n\n分析单位：{r['unit']}。样本：{r['sample']}。\n\n模型：{r['model']}。指标：{r['metrics']}。\n\n验证：{r['validation']}。\n\n{r['scope_note']}\n\n"+'\n'.join(rows)+'\n\nCSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。\n',encoding='utf-8')

def distribution(d, columns, sample):
    rows=[]
    for col in columns:
        x=pd.to_numeric(d[col],errors='coerce').dropna()
        rows.append(dict(sample=sample,variable=col,n=len(d),nonmissing=len(x),missing=len(d)-len(x),
            mean=x.mean(),sd=x.std(),min=x.min(),p25=x.quantile(.25),median=x.median(),p75=x.quantile(.75),max=x.max()))
    return rows

def samples(r,out):
    flow=[]; causes=[]; distributions=[]
    for margin,path in zip(['E0','R0c'],r['sources']):
        original=read(path)
        variants={'saved_input':original,'final':original if margin=='E0' else original[original[C]>0]}
        variants['weather_final']=variants['final'][variants['final'].cause_group_official.eq('weather_natural')]
        for scope,d in variants.items():
            flow.append(dict(margin=margin,scope=scope,n=len(d),lads=d.LAD21CD.nunique(),start=d.incident_date_utc.min(),end=d.incident_date_utc.max(),zero_customers=int(d[C].eq(0).sum()),source=path))
            for cause,n in d.cause_group_official.value_counts(dropna=False).items():
                causes.append(dict(margin=margin,scope=scope,cause=cause,n=int(n),share=n/len(d)))
        distributions+=distribution(variants['final'],['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h','log_population','urban_binary','income_deprivation_rate','deprivation_gap_pct','morans_i'],margin+'_final')
    table(out,'A_SAMPLE_FLOW',flow,r);table(out,'A_CAUSE_COUNTS',causes,r);table(out,'A_COVARIATE_SUMMARY',distributions,r)

def dictionary(r,out):
    definitions=[
        (C,'customers','监管阶段记录','非再中断阶段客户数求和；E0响应ln(1+C)','零保留于E0，R0最终排除'),
        (D,'h','监管阶段起止','全部阶段最迟结束减最早开始；R0响应ln(D)','恢复输入已有D>0和上端截断，最终再排C=0'),
        (A,'h','监管阶段客户/时长','客户加权时长；只作构造比较','不作为最终恢复响应'),
        ('gust_0h','m/s','匹配事件小时ERA5','训练均值/样本SD标准化；E0主效应使用原m/s截断基函数','全体E0结点14/25；天气11/24；交互仍保留'),
        ('precipitation_24h_sum','mm','已匹配事件24小时天气','训练均值/样本SD标准化','R0最终含gust×precip'),
        ('temperature_0h','deg C','事件小时ERA5','标准化后一次及平方项','最终规格'),
        ('pressure_msl_0h','hPa','事件小时ERA5','标准化','E0最终含gust×pressure'),
        ('log_population','log(persons)','ONS LAD population','人口自然对数','使用输入已保存值'),
        ('urban_binary','0/1','LAD城乡分类','文本含urban为1','参考=0'),
        ('income_deprivation_rate','source rate','English Indices of Deprivation 2019','发布的LAD收入贫困率','使用输入已保存值'),
        ('deprivation_gap_pct','source percentage','English Indices of Deprivation 2019','LAD内收入贫困差距','使用输入已保存值'),
        ('morans_i','index','English Indices of Deprivation 2019','LAD贫困空间聚集指标','使用输入已保存值'),
        ('incident_year / incident_month','calendar category','输入UTC事件日期','按训练期排序类别的虚拟变量','省略训练最小类别；当前全期year2021、month1'),
        ('customers_v2_log1p','log(1+customers)','同一事件C','R0协变量先log1p再训练标准化，含平方','不解释为因果恢复效应'),
        ('LAD21CD / cv_fold_v3','identifier','December 2021 LAD / 保存折号','区域分组 / 既定随机折','不是连续协变量'),
    ]
    table(out,'A_VARIABLE_DICTIONARY',pd.DataFrame(definitions,columns=['variable','unit','source','transform_definition','reference_scope']),r)

def vif(r,out):
    from .design_adapter import load_design_functions
    _,final_design=load_design_functions(js(r['sources'][4]));rows=[]
    for i,(margin,path) in enumerate(zip(['E0','R0c'],r['sources'][:2])):
        # Read only design inputs: no outcome response is supplied to a fit.
        columns=['gust_0h','precipitation_24h_sum','temperature_0h','pressure_msl_0h','urban_binary','log_population','income_deprivation_rate','deprivation_gap_pct','morans_i','incident_year','incident_month','LAD21CD',C]
        d=pd.read_csv(ROOT/path,usecols=columns,float_precision='round_trip')
        if margin=='R0c':
            d=d[d[C]>0].copy();d['customers_v2_log1p']=np.log1p(d[C])
        x,_=final_design(d,d,margin,margin=='R0c')
        if list(x.columns)!=read(r['sources'][5+i]).term.tolist(): raise ValueError('Saved final coefficient/design columns do not match')
        x=x.drop(columns='Intercept');corr=x.corr().to_numpy()
        if not np.isfinite(corr).all() or np.linalg.matrix_rank(corr)!=len(corr): raise ValueError('VIF design singular/nonfinite; do not silently use pseudoinverse')
        values=np.diag(np.linalg.inv(corr))
        for term,value in zip(x.columns,values):
            rows.append(dict(margin=margin,sample='final_all',n=len(d),term=term,VIF=value,controls='All saved final design columns except intercept',formula='diag(inv(correlation(X_without_intercept)))'))
    table(out,'A_FINAL_DESIGN_VIF',rows,r)

def docx_table(r,out):
    root=docx(r['sources'][0])
    if 'table' in r['config']:
        t=root.findall('w:body/w:tbl',NS)[r['config']['table']]
        rows=[[words(c) for c in row.findall('w:tc',NS)] for row in t.findall('w:tr',NS)]
        d=pd.DataFrame(rows[1:],columns=rows[0])
    else:
        paragraphs=root.findall('w:body/w:p',NS)
        d=pd.DataFrame([dict(source_paragraph=f'P{i:03}',existing_text=words(paragraphs[i-1])) for i in r['config']['paragraphs']])
    table(out,r['requirement_id']+'_EXISTING_DEFINITION',d,r)

def construction(r,out):
    rows=[('C','sum(stage_customers where reinterruption is excluded)','不对再中断阶段重复计客户'),
          ('D_B','max(all_stage_end)-min(all_stage_start), in hours','再中断阶段仍计时'),
          ('representative','stable sort by stage start; existing deterministic source-row tie breaker','复用C01修复，不以输入顺序任意挑选天气/原因字段'),
          ('missing','retain undefined outcomes as missing; use existing curated samples','不把未定义结果填零'),
          ('R0_final','existing positive-duration trimmed R0c input, then C>0','现有上端截断先于此处读取；本入口不重算截断点')]
    table(out,'B_CONSTRUCTION_RULES',pd.DataFrame(rows,columns=['quantity','rule','meaning']),r)
    j=js(r['sources'][0]); flat=[]
    def walk(obj,prefix=''):
        for k,v in obj.items():
            if isinstance(v,dict): walk(v,prefix+k+'.')
            else: flat.append(dict(historical_construction_metric=prefix+k,value=json.dumps(v,ensure_ascii=False),scope='C01历史构建全事件范围，非最终回归n'))
    walk(j);table(out,'B_REPRESENTATIVE_REPAIR',flat,r)

def duration(r,out):
    d=read(r['sources'][0]); rows=[]
    for scope,m in [('zero_customers',d[C].eq(0)),('positive_customers',d[C].gt(0)),('saved_R0c_input',np.ones(len(d),dtype=bool))]:
        x=d.loc[m]; valid=x[[A,D]].dropna()
        rows.append(dict(scope=scope,n=len(x),duration_exactly_1h=int(x[D].eq(1).sum()),share_exactly_1h=x[D].eq(1).mean(),
            valid_AB=len(valid),mean_A_h=valid[A].mean(),mean_B_h=valid[D].mean(),median_A_h=valid[A].median(),median_B_h=valid[D].median(),
            mean_B_minus_A_h=(valid[D]-valid[A]).mean(),fraction_A_equal_B=np.isclose(valid[A],valid[D],rtol=1e-10,atol=1e-10).mean() if len(valid) else np.nan))
    table(out,'B_RECOVERY_DEFINITION',rows,r)

def csv(r,out):
    for path in r['sources'][:r['config'].get('files',len(r['sources']))]:
        d=read(path)
        if r['requirement_id']=='C01':
            d['sample_n']=d.model.map({'E0':60437,'R0c':59834})
            d['response']=d.model.map({'E0':'ln(1+C)','R0c':'ln(D); includes C=0'})
            definitions={
                'M1_weather_linear':'4 standardized weather terms', 'M2_+gust_sq':'M1 + gust squared',
                'M3_+gust_x_pressure':'M2 + gust x pressure', 'M4_+socio':'M3 + 5 regional covariates',
                'M5_+year_month_FE':'M4 + year/month indicators', 'A1_gust_cubic':'M5 + gust cubed',
                'A2_log_gust':'M5 gust linear/squared replaced by log1p(raw gust); gust x pressure retained',
                'A3_hinge_10.8':'M5 gust squared replaced by max(raw gust-10.8,0)',
                'A4_gust_bins':'M5 gust terms replaced by training Q50/Q75/Q90/Q97 indicators; interaction retained',
                'A5_full_quad_weather':'M5 + temperature squared + precipitation squared + gust x precipitation',
                'A6_M5_+LAD_FE':'M5 + LAD indicators', 'A7_M5_no_socio':'M5 excluding 5 regional covariates'}
            d['spec_definition']=d.spec.map(definitions)
            if d.spec_definition.isna().any(): raise ValueError('Unmapped candidate definition')
            d['recovery_customer_terms']='R0c adds standardized log1p(C) and its square to every candidate'
        table(out,r['requirement_id']+'_'+Path(path).stem.upper(),d,r)

def grid(r,out):
    csv({**r,'config':{'files':3}},out)
    api=js(r['sources'][3])['api'];quality=js(r['sources'][4]);cells=read(r['sources'][1])
    rows=[dict(item=k,value=str(v)) for k,v in api.items()]
    rows += [dict(item='daily_aggregation',value='Maximum of 24 hourly wind_gusts_10m values per GMT day'),
             dict(item='LAD_centroids',value=str(len(cells))),
             dict(item='distinct_returned_grid_coordinates',value=str(len(cells[['grid_lat','grid_lon']].drop_duplicates()))),
             dict(item='panel_rows',value=str(quality['n'])),dict(item='coverage_complete_record',value=str(quality['complete'])),
             dict(item='spatial_definition',value='December 2021 LAD geometric centroid queried at nearest returned ERA5 cell; differs from main incident-coordinate mean location'),
             dict(item='interpretation',value=quality['notice'])]
    table(out,'J_INDEPENDENT_WEATHER_DEFINITIONS',rows,r)

def ramp(r,out):
    rows=[]
    for margin,path in zip(['E0','R0c'],r['sources']):
        for scope,j in js(path).items():
            for form in ['ramp','two_hinge','quadratic']:
                fit=j.get(form,{})
                if not fit and form not in j.get('nested_cv',{}): continue
                rows.append(dict(margin=margin,sample=scope,n=j['n'],form=form,k1=fit.get('k1'),k2=fit.get('k2'),
                    simplified_BIC=fit.get('bic'),adj_r2=fit.get('adj_r2'),nested_cv_log_RMSE=j.get('nested_cv',{}).get(form),
                    LR_hinge_vs_ramp=j.get('lr_hinge_vs_ramp',{}).get('stat'),LR_p=j.get('lr_hinge_vs_ramp',{}).get('p_1df')))
    table(out,'C_PLATEAU_COMPARISON',rows,r)

def knots(r,out):
    rows=[];folds=[]
    for margin,j in js(r['sources'][0]).items():
        b=j['two_knot']['bootstrap']; ci=j['two_knot'].get('profile_region_95',{})
        for k in ['k1','k2']:
            vals=b[k+'_pct_2.5_50_97.5']; region=ci.get(k,[None,None])
            rows.append(dict(margin=margin,sample='all',n=j['n'],form='unconstrained_two_hinge',knot=k,estimate=j['two_knot'][k],
                profile_low=region[0],profile_high=region[1],bootstrap_B=b['B'],bootstrap_low=vals[0],bootstrap_median=vals[1],bootstrap_high=vals[2]))
        for i,ks in enumerate(j['nested_cv']['fold_knots_2']):
            folds.append(dict(margin=margin,sample='all',n=j['n'],form='unconstrained_two_hinge',fold_order=i,k1=ks[0],k2=ks[1]))
    for margin,path in zip(['E0','R0c'],r['sources'][1:]):
        for scope,j in js(path).items():
            fit=j['ramp'];b=fit.get('bootstrap',{});region=fit.get('profile_region_95',{})
            for k in ['k1','k2']:
                vals=b.get(k+'_pct',[None]*3);reg=region.get(k,[None]*2)
                rows.append(dict(margin=margin,sample=scope,n=j['n'],form='plateau',knot=k,estimate=fit.get(k),profile_low=reg[0],profile_high=reg[1],bootstrap_B=b.get('B'),bootstrap_low=vals[0],bootstrap_median=vals[1],bootstrap_high=vals[2]))
    table(out,'D_KNOT_SUMMARY',rows,r);table(out,'D_NESTED_FOLD_KNOTS',folds,r)

def plot_style():
    import matplotlib
    matplotlib.use('Agg')
    from scripts.final_combined_analysis.figure_style import apply_style
    apply_style()
    import matplotlib.pyplot as plt
    return plt

def profiles(r,out):
    plt=plot_style();fig,axes=plt.subplots(2,2,figsize=(7.28,6.8),layout='constrained')
    for i,scope in enumerate(['all','weather']):
        prof,boot=[read(p) for p in r['sources'][i*2:i*2+2]]
        p=prof.pivot(index='k2',columns='k1',values='lr')
        image=axes[i,0].pcolormesh(p.columns,p.index,p.values,shading='nearest',cmap='viridis_r')
        fig.colorbar(image,ax=axes[i,0],label='Saved profile LR')
        axes[i,0].set(xlabel='First knot (m/s)',ylabel='Second knot (m/s)')
        axes[i,0].text(.02,.98,f'({chr(97+2*i)}) E0 {scope}',transform=axes[i,0].transAxes,va='top',color='black',bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
        # These are counts of the existing 1 m/s search locations, not a new analysis binning.
        for k in ['k1','k2']:
            counts=boot[k].value_counts().sort_index();axes[i,1].plot(counts.index,counts.values,'o-',label=k,markersize=3)
        axes[i,1].set(xlabel='Saved bootstrap knot (m/s)',ylabel='Replicate count')
        axes[i,1].text(.02,.98,f'({chr(98+2*i)}) E0 {scope}; B={len(boot)}',transform=axes[i,1].transAxes,va='top')
        axes[i,1].legend(loc='center right')
    fig.savefig(out/'figures/D_PLATEAU_PROFILE_BOOTSTRAP.png',dpi=400);plt.close(fig)
    for p in r['sources']: shutil.copyfile(ROOT/p,out/'data'/Path(p).name)

def period(r,out):
    rows=[]
    for margin,j in js(r['sources'][0]).items():
        for phase,s in j.items():
            for term,v in s.items():
                if isinstance(v,dict): rows.append(dict(margin=margin.replace('_dev_conf',''),period=phase,n=s['n'],gust_mean_m_s=s['gust_mean'],term=term,**v))
    table(out,'E_PERIOD_COEFFICIENTS',rows,r)
    table(out,'E_TEMPORAL_DESIGN',[dict(period=p,start=a,end=b,fit='Each period fitted separately; full-period selected specification',information_history='Later period previously explored',prediction_test='No frozen development prediction in this incident analysis') for p,a,b in [('development','2021-04-01','2023-09-29'),('confirmation','2023-09-30','2024-03-31'),('combined','2021-04-01','2024-03-31')]],r)

def coefficients(r,out):
    rows=[]
    for p in r['sources']:
        d=read(p); d.insert(0,'margin',Path(p).name.split('_')[0]);d.insert(1,'sample','weather' if '/weather_only/' in p else 'all')
        d.insert(2,'SE_method','two_way_LAD_date' if 'twoway' in p else 'LAD_only');d['source']=p;rows.append(d)
    table(out,'F_FULL_COEFFICIENTS',pd.concat(rows,ignore_index=True),r)

def final_prediction(r,out):
    rows=[]
    for margin,j in js(r['sources'][0]).items():
        for scheme,key in [('LAD-CV','final_cv_lad'),('year-CV','final_cv_year')]:
            rows.append(dict(margin=margin,sample='all',n=j['n'],spec='final',validation=scheme,log_RMSE=j[key],OOF_R2=None,calibration_slope=None))
    for s in read(r['sources'][1]).to_dict('records'):
        rows.append(dict(margin=s['model'],sample='weather',n=s['n'],spec=s['spec'],validation='LAD-CV',log_RMSE=s['rmse_cv'],OOF_R2=s['r2_cv'],calibration_slope=s['cal_slope']))
    table(out,'G_FINAL_METRICS',rows,r)

def ordinal(r,out):
    summaries=[];coefs=[]
    for margin,j in js(r['sources'][0]).items():
        for cl,share in zip(j['classes'],j['class_shares']):
            summaries.append(dict(margin=margin,category=cl,share=share,knots_m_s=str(j['knots']),ordinal_llf=j['ordinal_llf'],ordinal_converged=j['ordinal_converged'],McFadden_R2=j['ordinal_pseudoR2_McFadden']))
        groups={'ordinal':j['ordinal_gust_coefs'],**{'logit_'+k:v for k,v in j['per_threshold_binary_logit_gust_coefs'].items()}}
        if j.get('negbin_glm'): groups['negative_binomial']=j['negbin_glm']
        for model,values in groups.items():
            for term,value in values.items(): coefs.append(dict(margin=margin,model=model,term_or_diagnostic=term,value=value,knots_m_s=str(j['knots'])))
    table(out,'H_ORDINAL_SUMMARY',summaries,r);table(out,'H_CONDITIONAL_COEFFICIENTS',coefs,r)

def conditional(r,out):
    rows=[]
    for margin,j in js(r['sources'][0]).items():
        for form in ['lognormal_weather_common_beta','lognormal_weather_free_beta','lognormal_all_incidents']:
            p=j[form]
            for i,state in enumerate(j['states']):
                rows.append(dict(margin=margin,spec=form,n=j['n_weather'] if 'weather' in form else j['n_all'],state=state,theta_m_s=p['theta'][i],beta=p['beta'][i] if isinstance(p['beta'],list) else p['beta'],LR_common_vs_free=j['lr_common_vs_free_beta']['stat'],LR_p=j['lr_common_vs_free_beta']['p'],interpretation='Conditional on recorded incident; saved estimates only, no physical theta interpretation'))
    table(out,'H_CONDITIONAL_LOGNORMAL',rows,r)
    shutil.copyfile(ROOT/r['sources'][1],out/'data/H_OPTIMIZER_DIAGNOSTICS.json')

def storms(r,out):
    windows=literal(r['sources'][2],'STORMS');rows=[]
    for margin,path in zip(['E0','R0c'],r['sources']):
        d=read(path)
        if margin=='R0c': d=d[d[C]>0]
        dates=pd.to_datetime(d.incident_date_utc,utc=True).dt.strftime('%Y-%m-%d');union=np.zeros(len(d),bool)
        for storm,(start,end) in windows.items():
            mask=dates.between(start,end).to_numpy();union|=mask;x=d.loc[mask]
            rows.append(dict(margin=margin,storm=storm,start=start,end=end,n=len(x),customers_sum=x[C].sum(),fraction_of_sample=len(x)/len(d),overlap_rule='Inclusive windows; overlapping dates appear in both named rows'))
        rows.append(dict(margin=margin,storm='UNION_DEDUPLICATED',start='',end='',n=int(union.sum()),customers_sum=d.loc[union,C].sum(),fraction_of_sample=union.mean(),overlap_rule='Each incident counted once across all windows'))
    table(out,'I_STORM_COUNTS',rows,r)

def panel(r,out):
    # No optimizer or historical proxy score is read here.
    d=read(r['sources'][0]);rows=[]
    for t in ['any_gt0','any_gt5','any_gt100','any_gt1000','wthr_gt0','wthr_gt5','wthr_gt100','wthr_gt1000']:
        rows.append(dict(target=t,n=len(d),events=int(d[t].sum()),rate=d[t].mean(),lads=d.LAD21CD.nunique(),days=d.date.nunique(),start=d.date.min(),end=d.date.max()))
    table(out,'J_PROXY_LABELS',rows,r)
    from analysis_new.district_day_core import BW_KM,KMIN
    rows=[('unit','LAD-day including no-event days'),('location','Mean incident lat/lon per LAD in main production, not polygon geometric centroid'),
          ('gust','Same-day event-hour gust observations; normalized exp(-0.5*(distance/BW)^2) weights'),('bandwidth_km',str(BW_KM)),('minimum_neighbours',str(KMIN)),
          ('fallback','If fewer than KMIN weights > 0.001, nearest KMIN with weight 1/(distance_km+1), then normalize'),
          ('any_gt0','n_inc>0, including zero-customer incidents'),('wthr_gt0','wmaxc>=0, including zero-customer weather incidents'),
          ('gt5_gt100_gt1000','At least one qualifying incident with customers strictly > threshold; no daily customer sum'),
          ('weather','cause_group_official == weather_natural'),('model','p0+(1-p0)*Phi((ln(g)-ln(theta))/beta)'),
          ('availability','Same-day event anchors: retrospective proxy, not advance weather-only outage forecasting')]
    table(out,'J_PROXY_DEFINITIONS',pd.DataFrame(rows,columns=['item','definition']),r)

def time(r,out):
    metrics,samples,monthly,support,fits=[read(p) for p in r['sources'][:5]]
    dev=samples[samples.period.eq('development')][['target','event_rate']].rename(columns={'event_rate':'development_rate'})
    d=metrics.merge(dev,on='target',validate='one_to_one')
    d['bias_probability_percentage_points']=100*d.prediction_minus_observed
    table(out,'J_TIME_METRICS',d,r);table(out,'J_TIME_MONTHLY',monthly,r);table(out,'J_TIME_SUPPORT',support,r);table(out,'J_TIME_DEVELOPMENT_FIT',fits,r)

def time_figure(r,out):
    bins,monthly=[read(p) for p in r['sources'][:2]]
    table(out,'J_TIME_CALIBRATION_BINS',bins,r)
    monthly.to_csv(out/'data/J_TIME_MONTHLY.csv',index=False,float_format='%.17g')
    plt=plot_style();fig,axes=plt.subplots(2,2,figsize=(7.28,7.0),layout='constrained')
    for i,(target,label) in enumerate([('any_gt100','All >100 customers'),('wthr_gt100','Weather >100 customers')]):
        b=bins[(bins.target==target)&(bins.n>0)]; ax=axes[i,0]
        limit=min(1.0,max(.05,np.ceil(1.15*b[['mean_probability','observed_frequency']].to_numpy().max()/.05)*.05))
        ax.plot([0,limit],[0,limit],color='.6',ls='--',lw=1)
        for row in b.itertuples():
            ax.scatter(row.mean_probability,row.observed_frequency,marker='x' if row.n<100 else 'o',s=24,color='#2166ac')
            if row.bin==b.bin.max(): ax.annotate(str(row.bin),(row.mean_probability,row.observed_frequency),xytext=(3,2),textcoords='offset points',fontsize=7)
        ax.set(xlim=(0,limit),ylim=(0,limit),xlabel='Mean frozen probability',ylabel='Observed frequency')
        ax.text(.03,.97,f'({chr(97+2*i)}) {label}',transform=ax.transAxes,va='top',fontsize=9)
        counts=ax.table(cellText=[[int(v.bin),int(v.n),int(v.events)] for v in b.itertuples()],colLabels=['Bin','n','Events'],cellLoc='right',bbox=[.03,.43,.42,.45])
        counts.auto_set_font_size(False);counts.set_fontsize(7)
        m=monthly[monthly.target==target];x=np.arange(len(m));ax=axes[i,1]
        for col,style,title in [('observed_rate','o-','Observed'),('mean_prediction','s-','Frozen model'),('baseline_probability','--','Development constant')]: ax.plot(x,m[col],style,label=title,markersize=3)
        ax.set_xticks(x,[s[2:]+('*' if s=='2023-09' else '') for s in m.month],rotation=35)
        ax.set(xlabel='Evaluation month (* Sep 30 only)',ylabel='Probability / frequency')
        ax.text(.03,.97,f'({chr(98+2*i)}) {label}',transform=ax.transAxes,va='top',fontsize=9)
        ax.legend(loc='best',fontsize=7)
    fig.savefig(out/'figures/J_TIME_CALIBRATION_MONTHLY.png',dpi=400);plt.close(fig)

def boundaries(r,out):
    rows=[('J.1','Main event-anchor proxy','Includes no-event days under existing retrospective weather interpolation','Does not remove event-anchor dependence'),
          ('J.2','Independent ERA5 centroid daily maximum','Different location/sampling/time aggregation','No valid complete repaired proxy-vs-grid model ranking located'),
          ('J.3','Five aggregations on fixed ERA5','Within-task same-sample aggregation comparison','Not a validation of main proxy; no cross-experiment raw Brier ranking'),
          ('J.4','G plus H/24 or log1p(square cumulative excess)','Increment of two specified duration indicators','Not top3/rolling3; not precise consecutive duration or structural damage'),
          ('J.5','Frozen development fit, later retrospective period','BSS versus development constant, calibration and monthly description','Not a pristine independent confirmation set, advance forecast, full calibration or significance claim'),
          ('J.6','Descriptive scope','Mixed/adverse results preserved; no posthoc adoption cutoff','No equivalence, replacement decision, manuscript revision or closed audit')]
    table(out,'J_INTERPRETATION_BOUNDARIES',pd.DataFrame(rows,columns=['section','definition','supports','does_not_support']),r)
    methods=[]
    for experiment,path,keys in [
        ('DD-AGG01',r['sources'][4],['candidates','model','calibration','target_rule','timezone','unit','folds','uncertainty']),
        ('DD-DUR01',r['sources'][5],['features','models','tau','calibration','labels','timezone','hour_unit','folds_path','uncertainty']),
    ]:
        protocol=js(path)
        for key in keys:
            value=protocol[key]
            if isinstance(value,dict):
                for sub,definition in value.items(): methods.append(dict(experiment=experiment,item=key+'.'+sub,definition=json.dumps(definition,ensure_ascii=False)))
            else: methods.append(dict(experiment=experiment,item=key,definition=str(value)))
    table(out,'J_FROZEN_EXPERIMENT_DEFINITIONS',methods,r)

EXPORTERS={name:globals()[name] for name in ['samples','dictionary','vif','docx_table','construction','duration','csv','grid','ramp','knots','profiles','period','coefficients','final_prediction','ordinal','conditional','storms','panel','time','time_figure','boundaries']}
