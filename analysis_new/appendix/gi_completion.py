"""Scoped transactional G/I completion, cache validation and factual receipts."""
import copy
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
import hashlib
import numpy as np
import pandas as pd
import statsmodels
from .catalog import ROOT,MAIN,MANUSCRIPT,REQUIREMENTS
from .mapping import digest,write_json,expected
from .f02_cov import csv,read,js,token
from . import gi_core as core
from . import gi_outputs as outputs
from . import gi_storms as storms

GI_PLAN='docs/new_analysis/instructions/附录FGHIJ四步推进台账与第一步J03执行指令 (2).md'
STATE='产物完成/待研究负责人反馈分析'

def model_cache_key(config):
    """Drawing/report changes may rederive arrays without rerunning fixed OLS."""
    model_code={p:h for p,h in config['code'].items() if Path(p).name in ['gi_core.py','c_models.py','design_adapter.py','f02_cov.py']}
    return token(dict(inputs=config['inputs'],code=model_code,seed=config['seed'],software=config['software'],
        folds=config['fixed_folds'],preprocessing=config['preprocessing'],scales=config['scales']))

def core_output(rel):
    return rel in {'data/GI_PREDICTIONS.csv.gz','data/GI_COEFFICIENTS.csv','data/GI_PREPROCESSING.json',
        'data/GI_COMPONENT_STATUS.csv','data/GI_SUMMARY_ALIGNMENT.csv','data/GI_NESTED_REFERENCE.json'} or (rel.startswith('data/GI_') and rel.endswith('_COV.csv'))

def figure_mapping(stage):
    figures=[('Figure 3','P045/P047','fig2_gust_response.png','plot_model_selection.py: Figure2 block',
        'M5 nongust control; quadratic/cubic/log/free hinges. E0 60437; historical R0c 59834 includes zero customers.',
        'control residual / shifted gust component; not final residual',
        'Current G R0c counterpart uses final positive-customer 51173; cannot claim exact old recovery figure reproduction.'),
        ('Figure 5','P054/P055','fig11_final_models.png','final_models.py:main',
         'E0 final fixed14/25; R0c final quadratic; current final controls and samples; same-sample M5 comparison',
         'full-fit gust component and fixed LAD-OOF ventiles','Full-sample-selected fixed knots in CV; not nested family CV.'),
        ('Figure 6','P059/P061','fig13_weather_only.png','weather_only_regression.py: plotting block',
         'Black nongust control; green weather hinge (not final), red paper; grey full E0 final but full R0c paper',
         'control residual / shifted component with two-way band','Weather R0c green is a single11 hinge, not three-segment plateau; no added temperature square in hinge.'),
        ('not embedded in accepted body','supplementary diagnostic source','fig14_weather_predicted_observed.png','weather_only_regression.py: OOF diagnostic block',
         'weather paper/hinge/final, fixed knots; 9857 and9254','fixed LAD-OOF hexbin and predicted deciles','Not a partial-residual figure.')]
    # Actual filename can be read from the producer, not inferred from a figure number.
    paths=list((ROOT/MAIN/'figures').glob('fig14*'))
    if paths:figures[-1]=(figures[-1][0],figures[-1][1],paths[0].name,*figures[-1][3:])
    embedded={};ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
    with zipfile.ZipFile(ROOT/MANUSCRIPT) as z:
        rel={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
        doc=ET.fromstring(z.read('word/document.xml'))
        for i,p in enumerate(doc.findall('w:body/w:p',ns)):
            for b in p.findall('.//a:blip',ns):
                target=rel[b.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed']]
                embedded[hashlib.sha256(z.read('word/'+target)).hexdigest()]=i
    rows=[]
    for caption,loc,filename,func,model,kind,note in figures:
        path=MAIN+'figures/'+filename;h=digest(ROOT/path)
        rows.append(dict(manuscript_caption=caption,body_location=loc,source_figure=path,sha256=h,embedded_image_paragraph=embedded.get(h),
            drawing_function='analysis_new/'+func,model_sample=model,prediction_identity=kind,interpretation_note=note,
            arrays='G/data/GI_PREDICTIONS.csv.gz; GI_GUST_BINS.csv; GI_CALIBRATION_BINS.csv; GI_RESPONSE_CURVES.csv'))
    rows.append(dict(manuscript_caption='storm description; Appendix I required evidence',body_location='P076/P101',
        source_figure='results/pretest/archive/20260909154556/results/c02_c08_repair_20260905/figures/Figure_9_storm_validation.png',
        drawing_function='scripts/c02_c08_repair_20260905/figure9_storm_validation.py',model_sample='old quadratic model; recovery59834 includes zero customers',
        prediction_identity='full-fit descriptive',interpretation_note='New I uses accepted final E0/R0c positive-customer model; old predictions not reused as final',arrays='I/data/GI_STORM_PREDICTIONS.csv.gz'))
    csv(stage/'data/GI_FIGURE_SOURCE_MAP.csv',pd.DataFrame(rows))

def summarize_short(stage,master,samples):
    result=[]
    for combo in ['R0c_all','R0c_weather']:
        d=samples[combo].set_index(core.ID)
        for kind in ['in_sample','LAD_OOF']:
            v=master[master.combination.eq(combo)&master.model_id.eq('final')&master.prediction_type.eq(kind)]
            duration=d.loc[v.observation_id,core.D].to_numpy()
            for label,mask in [('T<=1h',duration<=1),('T=1h',duration==1),('T>1h',duration>1)]:
                s=v.loc[mask];result.append(dict(combination=combo,prediction_type=kind,observed_duration_group=label,**core.scores(s.y,s.prediction)))
    csv(stage/'data/GI_SHORT_DURATION_DESCRIPTION.csv',pd.DataFrame(result))

def report_g(stage,command):
    m=read(stage/'tables/GI_PREDICTION_METRICS.csv');align=read(stage/'data/GI_SUMMARY_ALIGNMENT.csv');states=read(stage/'data/GI_COMPONENT_STATUS.csv')
    c=read(stage/'data/GI_CALIBRATION_BINS.csv');b=read(stage/'data/GI_GUST_BINS.csv');short=read(stage/'data/GI_SHORT_DURATION_DESCRIPTION.csv')
    text=['# APP-GI-PRED 第三工作包执行与回传报告（G主索引）',
        '状态：产物完成/待研究负责人反馈分析。J03与F02已由负责人关闭；本报告为执行事实汇总，不代替反馈科学审查。I的七场完整评分、排除与样本汇总见 ../I/logs/GI_EXECUTION_REPORT.md。',
        '## 运行及完成范围',f'实际命令：`{command}`。正常重导出使用同命令；`--recompute-gi`只重算本包缺失组件；有效缓存不拟合。`--render-only-gi`依据已保存数组重绘，缓存失效时报错，不偷偷拟合。',
        '四个正式样本分别为60437、51173、9857、9254。全体恢复保留正式正客户清洗；weather恢复固定11单结点、温度平方和gust×precip，不是全体恢复二次式。完整设计、训练ID指纹、固定结点、均值/样本SD、参考水平和fold beta见data/GI_PREPROCESSING.json。',
        f'首次组件完成记录：{int(states.new_fits.sum())}次固定OLS（包括逐折模型），{int(states.action.eq("DERIVE_SAVED_COEFFICIENTS").sum())}个全样本系数派生组件；具体计数见GI_COMPONENT_STATUS.csv，当前调用是否缓存另见GI_LAST_EXECUTION.json。无结点搜索、bootstrap、新验证切分。',
        '四个final全样本系数及预测与C对齐；两天气final设计/残差和曲线协方差复用F02。旧组件只有汇总RMSE时没有假称已存OOF。C的R0c_weather/F06逐折选结点预测作为独立家族参考路径保存，不进入固定11的评分。',
        '## G总体结果（原拟合尺度）','偏差=预测−观测，残差=观测−预测。R²=1−SSE/Σ(y−本评价集均值)²；不是相关系数平方。不同样本间不作模型胜负排名。',
        '|组合|预测身份|n|RMSE|MAE|偏差|R²|','|---|---|---|---|---|---|---|']
    for r in m[m.model_id.eq('final')].itertuples():text.append(f'|{r.combination}|{r.prediction_type}|{r.n}|{r.rmse:.9f}|{r.mae:.9f}|{r.bias:.9f}|{r.r2:.9f}|')
    text+=['全部有限旧模型对照及控制残差评分见tables/GI_PREDICTION_METRICS.csv，不能把控制模型残差与final残差混为一项。',
        f'原固定五折汇总对齐：{int(align.within_numeric_tolerance.sum())}/{len(align)}组件在冻结数值容差内，最大RMSE绝对差={align.difference.abs().max():.12g}。不与C nested家族汇总追数。',
        '## 已保存分箱的直接描述','gust箱沿用(0,4]…(30,45]；空箱NA，图上小幅水平偏移仅区分三个系列；n与真实平均gust均在表中。1.96×SEM箱内区间未处理聚类，不能用作two-way曲线置信带。']
    for combo in core.cm.COMBOS:
        cb=c[c.combination.eq(combo)&c.model_id.eq('final')&c.prediction_type.eq('LAD_OOF')]
        gb=b[b.combination.eq(combo)&b.model_id.eq('final')&b.prediction_type.eq('LAD_OOF')]
        text.append(f'{combo}：既定预测分箱的预测−观测均值范围{cb.bias.min():.7f}至{cb.bias.max():.7f}；阵风箱final OOF平均残差范围{gb.mean_residual.min():.7f}至{gb.mean_residual.max():.7f}。逐箱n与区间完整保留，不将非零偏差或稀疏箱作为新增拟合触发器。')
    text+=['## 具体图注与文字衔接事项',
        '1. P047/Figure3对应磁盘fig2。其R0c原样本59834含零客户；本次当前R0c形状数据使用51173。原稿引用的箱均值不能无说明移植到当前样本。E0旧四条函数的基、参数和加权平移已导出；全体final与paper图5基于平均阵风平移，与图3按控制残差加权平移是不同基准。',
        '2. P054/Figure5对应fig11；CV固定正式结点，而非训练折重新选择。P059/Figure6对应fig13：绿色是weather hinge规格，未含final新增温度平方；恢复是单11结点。灰色全体恢复实际paper M5，不是当前final。当前final与旧hinge分别保存，需据此调整图注身份。',
        '3. 原响应图将曲线平移，但置信带宽仍由未平移的gust基计算。本次保留真实a和aᵀVa、原1.96常数与平移规则；不能将其描述为已经传播参考点不确定性的差值置信带，也不是单事件预测区间。具体受影响为Figure5/6左响应图的区间解释，不影响逐行预测及其评分。',
        '4. P055“清洗后短事件高估完全消除/完全由占位符造成”不能由本包直接确认。正式保留的正客户短时长记录仍有下列预测偏差；恰好1小时仅是数据值，没有业务字段即可确认占位符的依据。']
    for r in short[short.prediction_type.eq('LAD_OOF')&short.observed_duration_group.eq('T<=1h')].itertuples():text.append(f'{r.combination}，T≤1h，n={r.n}，OOF预测−观测={r.bias:.8f}，RMSE={r.rmse:.8f}。这是对同一预测的条件描述，按观测筛组本身也会产生回归均值特征，不能单据该值推断运营机制。')
    for d in js(stage/'data/GI_CURVE_VARIANCE_CHECKS.json'):
        text.append(f"{d['combination']}/{d['model_id']}实际300网格：负方差{d['negative_variance_points']}点，非有限{d['nonfinite_variance_points']}点，最小aᵀVa={d['min_variance']:.12g}；无截零/正定化。")
    text+=['## 文件与必要检查',
        'data/GI_FIGURE_SOURCE_MAP.csv以DOCX内嵌图片字节哈希核对正文3/5/6；fig14是另存的OOF图，不是该正文中的偏残差图。GI_COVERAGE_PLAN.csv和GI_PROTOCOL.json在本轮新增拟合前保存；GI_COMPONENT_STATUS.csv记录实际动作。',
        'GI_PREDICTIONS.csv.gz是G/I唯一共享主预测；GI_PREPROCESSING.json和GI_COEFFICIENTS.csv可独立复算；GI_GUST_BINS.csv、GI_CALIBRATION_BINS.csv、GI_RESPONSE_CURVES.csv及CURVE_DESIGN是图形来源。tables为论文候选，data/logs为支持记录。PNG和PDF共享同一保存数组。',
        'logs/GI_TECHNICAL_CHECKS.json为本包检查，不重做历史审计。图形目视检查另记GI_VISUAL_CHECK.md；若尚未记录，不能把自动保存当作已查看。',
        '未完成的范围：没有重现旧59834恢复图作为当前样本结果；未计算新相关显著性、时间留出、重变换校正或新的区间。这些均未授权/不适用，不以不利结果补实验。I源范围限制与排除见I报告。停止于本包事实产物，不启动H。']
    (stage/'logs/GI_EXECUTION_REPORT.md').write_text(('\n\n'.join(text)+'\n').replace('|\n\n|','|\n|'),encoding='utf8')

def report_i(stage,command):
    m=read(stage/'tables/GI_STORM_METRICS.csv');s=read(stage/'tables/GI_STORM_SAMPLES.csv')
    text=['# APP-GI-PRED：I七场风暴执行与回传报告',
        '产物完成/待反馈分析。共享模型与G事实报告见../G/logs/GI_EXECUTION_REPORT.md。',f'命令：`{command}`；G已完成时也可`python -X utf8 -B main_appendix.py --appendices I --gi-only`，从已核验G缓存切片。',
        '## 当前结果','以下是固定最终模型在全研究样本拟合后的窗口描述，不是新风暴留出或提前预测。LAD-OOF补充单列在完整CSV。',
        '|风暴|模型|n|RMSE|MAE|平均观测|平均预测|偏差|描述相关|','|---|---|---|---|---|---|---|---|---|']
    for r in m[m.prediction_type.eq('in_sample')].itertuples():text.append(f'|{r.storm}|{r.combination}|{r.n}|{r.rmse:.8f}|{r.mae:.8f}|{r.mean_observed:.8f}|{r.mean_prediction:.8f}|{r.bias:.8f}|{r.correlation:.8f}|')
    text+=['## 窗口、样本与排除',
        '原七窗口UTC日期包含两端；Dudley/Eunice及Eunice/Franklin存在重叠，逐风暴分别保留，并集按事件ID与预测身份去重。并集RMSE来自逐行误差，未平均七个RMSE。',
        '恢复使用正式combined p99=192.0833333333333h；来源规则为全期WT正时长p99先定阈值、随后客户完整性和最终正客户清洗。本轮不在风暴内重估，已核对由接受E0重建的正式恢复ID集合与51173逐项完全一致。',
        '|窗口|暴露n|正客户正时长（截断前）|正式恢复n|零/负客户排除|无效时长排除|超阈仅展示|','|---|---|---|---|---|---|---|']
    for r in s.itertuples():text.append(f'|{r.storm}|{r.exposure_n}|{r.recovery_before_duration_cap_positive_customers}|{r.recovery_final_n}|{r.excluded_zero_or_negative_customers}|{r.excluded_duration}|{r.display_only_above_cap}|')
    text+=['空心三角仅表示可计算、正客户且超出正式时长阈值的事件；另标display_only且不进入主评分。合法短时长点保留。恰好1小时不自动认定为业务占位符。',
        '源覆盖限制：该计数从当前正式E0的60437条事件出发。上游WT有16条缺客户未进入E0，当前正式输入不提供这些记录的日期；本包不能给出其逐风暴数量，不将其写为0，也不重开原始事件重构。该限制影响上游缺客户细分计数，不影响当前正式暴露/恢复模型的完整窗口评分。',
        '## 文字需要据结果限定的具体位置',
        'P076“暴露追踪均值”应对应本表各窗口平均观测、预测及偏差，不等同于个体准确预测；有高估或低估的窗口不得删除。',
        'P076“恢复相关显著”本包仅计算描述相关，无相关p值或独立样本检验，不以正相关自动确认显著。较晚发生的风暴也参与全样本拟合，不能由日期将散点改称时间样本外。恢复预测仍使用客户规模等事后输入。',
        '## 输出与检查','tables/GI_STORM_SAMPLES、GI_STORM_METRICS为核心表；data/GI_STORM_PREDICTIONS.csv.gz含逐风暴及去重并集、in_sample/LAD_OOF/display_only身份；GI_STORM_EXCLUSIONS保存逐事件原因；GI_STORM_WINDOWS保存冻结窗口，GI_STORM_SOURCE记录共享预测哈希及阈值来源。',
        'figures/GI_STORM_FINAL_SCATTER.png/.pdf为当前final两面板，空心三角与主评分分离。logs/GI_TECHNICAL_CHECKS.json保存会员集合、阈值、去重、预测有限及排除加总检查。没有新增风暴模型拟合。',
        '完成本包产物后停止，待人工＋agent反馈；未启动H，不修改论文或其他附录。']
    (stage/'logs/GI_EXECUTION_REPORT.md').write_text(('\n\n'.join(text)+'\n').replace('|\n\n|','|\n|'),encoding='utf8')

def generate(letter,stage,source_checks,previous,force=False,render_only=False,base_generator=None,command=''):
    from .runner import now,safe_child
    rid='G03' if letter=='G' else 'I02';req=next(r for r in REQUIREMENTS if r['requirement_id']==rid)
    old=js(previous/'manifest.json') if (previous/'manifest.json').exists() else {}
    own={r['path'] for r in old.get('outputs',[]) if r['requirement_id']==rid}
    manifest=copy.deepcopy(old)
    if old.get('owner')=='main_appendix.py':
        for rel in old['managed_files']:
            if rel in own or rel=='manifest.json':continue
            dst=safe_child(stage,rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dst)
        manifest['outputs']=[r for r in old['outputs'] if r['requirement_id']!=rid]
    else:manifest=base_generator(letter,stage,source_checks)
    for f in ['figures','tables','data','logs']:(stage/f).mkdir(exist_ok=True)
    before={p.relative_to(stage).as_posix():digest(p) for p in stage.rglob('*') if p.is_file() and p.name not in ['README.md','manifest.json']}
    files=core.source_files()+[GI_PLAN,MANUSCRIPT]
    deps=[p.relative_to(ROOT).as_posix() for p in Path(__file__).parent.glob('gi_*.py')]+['analysis_new/appendix/design_adapter.py','analysis_new/appendix/f02_cov.py','analysis_new/appendix/c_models.py','scripts/final_combined_analysis/figure_style.py']
    config=dict(task='APP-GI-PRED',seed=core.cm.SEED,inputs={p:digest(ROOT/p) for p in files},code={p:digest(ROOT/p) for p in deps},software=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,statsmodels=statsmodels.__version__),
        fixed_folds='original first-encounter unique LAD shuffle seed20260908, modulo5; verified C row IDs and folds',
        preprocessing='train mean/sample SD ddof1 and calendar levels; fixed production knots, no search',
        scales='natural log1p(customers), natural log(duration hours)',gust_bins=core.BINS,calibration='qcut duplicates drop; all20/weather10, per prediction series',
        binned_intervals='original 1.96 SEM, unclustered',curve_intervals='actual original uncentred gust basis aVa then1.96; curve shift held constant',
        metrics='pooled equal incident weights; bias=pred-y; R2 denominator about evaluation mean; no significance tests',
        stop='J03/F02 closed by researcher; GI pending feedback; H not started')
    if letter=='I':
        groot=previous.parent/'G';gm=js(groot/'manifest.json')
        needed=[v for v in gm['outputs'] if v['requirement_id']=='G03']
        if not needed or not all(digest(groot/v['path'])==v['sha256'] for v in needed):raise ValueError('I requires intact published G predictions; run G first')
        gconfig=js(groot/'logs/GI_PROTOCOL.json')
        if model_cache_key(gconfig)!=model_cache_key(config):raise ValueError('G model sources/configuration changed; run G before I')
        config['G_cache_key']=gm['gi_cache_key'];config['G_predictions_sha256']=digest(groot/'data/GI_PREDICTIONS.csv.gz')
    key=token(config);cache=not force and old.get('gi_cache_key')==key and bool(own) and all((previous/v['path']).is_file() and digest(previous/v['path'])==v['sha256'] for v in old['outputs'] if v['requirement_id']==rid)
    oldconfig=js(previous/'logs/GI_PROTOCOL.json') if (previous/'logs/GI_PROTOCOL.json').exists() else None
    core_reused=bool(letter=='G' and not force and oldconfig and model_cache_key(oldconfig)==model_cache_key(config)
        and (previous/'data/GI_PREDICTIONS.csv.gz').exists() and all(digest(previous/v['path'])==v['sha256'] for v in old.get('outputs',[]) if core_output(v['path'])))
    if render_only and not cache:raise ValueError('--render-only-gi requires valid source/code/output cache; normal run needed after changes')
    if cache:
        for rel in own:
            dst=safe_child(stage,rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dst)
        print(f'{letter}: validated GI cache; no model fitting',flush=True)
    else:
        write_json(stage/'logs/GI_PROTOCOL.json',dict(**config,frozen_at=now(),command=command,letter=letter))
        if letter=='G':
            samples=core.cm.samples();csv(stage/'data/GI_COVERAGE_PLAN.csv',core.coverage(samples));figure_mapping(stage)
            if core_reused:
                for rel in own:
                    if core_output(rel):
                        dst=safe_child(stage,rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dst)
                master=read(stage/'data/GI_PREDICTIONS.csv.gz')
                prior_checks=js(previous/'logs/GI_TECHNICAL_CHECKS.json')
                checks={k:v for k,v in prior_checks.items() if 'sample_and_folds' in k or k in ['unique_prediction_keys','all_fixed_oof_match_original_summary']}
                print('G: fixed-model component cache validated; rederive tables/curves only, zero new OLS',flush=True)
            else:master,checks=core.compute(stage,samples)
            metric,bins,cal,ch=outputs.summarize(stage,master,req);checks.update(ch)
            curves,diag=outputs.curve_arrays(stage,samples,bins);summarize_short(stage,master,samples)
            # Independent saved-row score check, without re-fitting or rebinning.
            saved=read(stage/'data/GI_PREDICTIONS.csv.gz')
            checks['saved_rows_score_recalculation']=all(np.isclose(core.scores(v.y,v.prediction)['rmse'],metric[(metric.combination==k[0])&(metric.model_id==k[1])&(metric.prediction_type==k[2])].rmse.iloc[0],rtol=1e-12,atol=1e-12) for k,v in saved.groupby(outputs.KEY))
            checks['all_curve_variances_nonnegative']=all(v['negative_variance_points']==0 and v['nonfinite_variance_points']==0 for v in diag)
            write_json(stage/'logs/GI_TECHNICAL_CHECKS.json',checks)
        else:storms.compute(stage,groot,req)
    if letter=='G':
        outputs.figures(stage,read(stage/'data/GI_PREDICTIONS.csv.gz'),read(stage/'data/GI_GUST_BINS.csv'),read(stage/'data/GI_CALIBRATION_BINS.csv'),read(stage/'data/GI_RESPONSE_CURVES.csv'))
        report_g(stage,command)
    else:
        storms.figure(stage,read(stage/'data/GI_STORM_PREDICTIONS.csv.gz'));report_i(stage,command)
    write_json(stage/'logs/GI_LAST_EXECUTION.json',dict(time=now(),command=command,cached=cache,recomputed=not cache,model_components_reused=cache or core_reused,
        new_ols_fits=0 if letter=='I' or cache or core_reused else int(read(stage/'data/GI_COMPONENT_STATUS.csv').new_fits.sum()),
        force=force,render_only=render_only,cache_key=key))
    preserve={p:digest(stage/p)==h for p,h in before.items()}
    assert all(preserve.values())
    write_json(stage/'logs/GI_PRESERVATION.json',dict(other_managed_outputs=preserve,all_unchanged=True))
    # Retain prior non-GI appendix text, remove superseded gap paragraphs only.
    content=(stage/'README.md').read_text(encoding='utf8').split('\n## APP-GI-PRED')[0]
    content=re.sub(r'### '+rid+r' —.*?(?=### |## 来源|\Z)','',content,flags=re.S)
    content=content.replace('最终残差数值表仍需定位。','G03已由本包补齐。').replace('当前最终规格风暴预测未定位，不能用旧二次模型补位。','I02已按当前final补齐，旧图仅作为来源。')
    content+='\n## APP-GI-PRED\n\n'+(stage/'logs/GI_EXECUTION_REPORT.md').read_text(encoding='utf8')
    (stage/'README.md').write_text(content,encoding='utf8')
    checks=js(stage/'logs/GI_TECHNICAL_CHECKS.json');valid=all(checks.values())
    state=STATE if valid else '产物部分可用/技术异常待反馈'
    newfiles={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}-set(before)-{'README.md','manifest.json'}
    for rel in expected(req):
        if not (stage/rel).is_file():raise ValueError('Missing required GI output '+rel)
    for rel in sorted(newfiles):
        p=stage/rel;manifest['outputs'].append(dict(path=rel,sha256=digest(p),bytes=p.stat().st_size,requirement_id=rid,claim_id=req['claim_id'],source_paths=files,source_sha256=config['inputs'],producer=req['producer'],export_function=req['producer'],configuration=req['config'],status=state))
    manifest['requirements'][rid]=state;manifest.pop('error',None)
    manifest.update(owner='main_appendix.py',appendix=letter,last_attempt=now(),status='success' if valid else 'success_with_gaps',update_state='本次仅G/I任务产物更新，其余保留',gi_cache_key=key,
        managed_files=sorted({p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}|{'manifest.json'}))
    write_json(stage/'manifest.json',manifest)
    return manifest
