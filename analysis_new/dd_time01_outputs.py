"""Time-holdout tables, figures and bounded technical checks; no adoption report."""
import json
import numpy as np
import pandas as pd
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.fragility_optimizer import Objective, probabilities
from analysis_new.temporal_fragility import PERIODS, frozen_edges, evaluate_frozen
from analysis_new.runner import save, digest, now


def plots(out,development,evaluation,development_predictions,edges,monthly,bins,fits):
    import matplotlib.pyplot as plt
    folder=out/'figures'; folder.mkdir(); axis_records=[]
    for target in TARGETS:
        f=fits[fits.target==target].iloc[0]; b=bins[bins.target==target]
        fig=plt.figure(figsize=(12,8)); gs=fig.add_gridspec(2,2,height_ratios=[3,2])
        axes=[fig.add_subplot(gs[0,i]) for i in range(2)]; table_ax=fig.add_subplot(gs[1,:]); table_ax.axis('off')
        limit=min(1.,max(.01,float(development_predictions[target].max())*1.2)) if f.valid else 1.
        outside=int(((b.n>0)&((b.mean_probability>limit)|(b.observed_frequency>limit))).sum())
        for ax,upper in zip(axes,[1.,limit]):
            ax.plot([0,upper],[0,upper],'k--',lw=1)
            if f.valid:
                ax.plot(b.mean_probability.where(b.n>=100),b.observed_frequency.where(b.n>=100),'-o',ms=4,color='tab:blue')
                sparse=b[(b.n>0)&(b.n<100)]; ax.scatter(sparse.mean_probability,sparse.observed_frequency,marker='x',s=45,color='tab:red')
            else: ax.text(.1,.5,'No valid development fit',transform=ax.transAxes)
            ax.set(xlim=(0,upper),ylim=(0,upper),xlabel='Mean frozen probability',ylabel='Evaluation event frequency')
            ax.set_aspect('equal',adjustable='box'); ax.grid(alpha=.2)
        axes[0].set_title('Full range: all nonempty bins')
        axes[1].set_title(f'Development-based zoom; {outside} point(s) outside zoom')
        rows=[]
        for r in b.itertuples():
            rows.append([r.bin,f'{r.lower:.5g} to {r.upper:.5g}',r.n,r.events,
                         f'{r.mean_probability:.5g}' if r.n else 'empty',f'{r.observed_frequency:.5g}' if r.n else 'empty',
                         'n<100' if 0<r.n<100 else ('empty' if r.n==0 else '')])
        table=table_ax.table(cellText=rows,colLabels=['Bin','Frozen probability interval','n','Events','Mean p','Frequency','Support'],loc='center',cellLoc='center',colWidths=[.06,.28,.10,.10,.14,.14,.12])
        table.auto_set_font_size(False); table.set_fontsize(8); table.scale(1,1.16)
        fig.suptitle(target+': retrospective temporal holdout; bins frozen in development; crosses n<100')
        fig.tight_layout(); fig.savefig(folder/f'calibration_{target}.png',dpi=150); plt.close(fig)
        axis_records.append(dict(target=target,zoom_upper=limit,zoom_source='1.2*maximum development fitted probability, constrained [.01,1]',points_outside_zoom=outside))
        m=monthly[monthly.target==target]; x=np.arange(len(m))
        fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
        axes[0].plot(x,m.observed_rate,'o-',label='Observed frequency')
        axes[0].plot(x,m.mean_prediction,'o-',label='Frozen model mean probability')
        axes[0].plot(x,m.baseline_probability,'--',label='Development constant rate')
        axes[0].set_ylabel('Probability / frequency'); axes[0].legend(fontsize=8)
        axes[1].plot(x,m.model_brier,'o-',label='Frozen model Brier')
        axes[1].plot(x,m.baseline_brier,'o-',label='Development constant Brier')
        axes[1].set_ylabel('Brier'); axes[1].legend(fontsize=8)
        axes[1].set_xticks(x,[f'{r.month}\nn={r.n}' for r in m.itertuples()],fontsize=8)
        for ax in axes: ax.grid(alpha=.2)
        fig.suptitle(target+': monthly evaluation summaries (2023-09 contains September 30 only)')
        fig.tight_layout(); fig.savefig(folder/f'monthly_{target}.png',dpi=150); plt.close(fig)
    save(out/'figure_axes.json',axis_records)
    fig,ax=plt.subplots(figsize=(8,5)); data=[]
    for period,frame in [('development',development),('evaluation',evaluation)]:
        g=np.sort(frame.gust.to_numpy()); cumulative=np.arange(1,len(g)+1)/len(g)
        ax.plot(g,cumulative,label=period)
        data.append(pd.DataFrame(dict(period=period,gust=g,cumulative_fraction=cumulative)))
    ax.set(xlabel='Existing incident-anchor gust proxy (m/s)',ylabel='Empirical cumulative fraction',title='Proxy distributions in the fixed two periods')
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(folder/'proxy_distributions.png',dpi=160); plt.close(fig)
    pd.concat(data,ignore_index=True).to_csv(out/'proxy_distribution_plot_data.csv.gz',index=False)


def checks(out,development,evaluation,fits,candidates,edges,development_predictions,freeze_hash,times):
    read=lambda name:pd.read_csv(out/name,float_precision='round_trip')
    predictions=read('temporal_predictions.csv.gz'); metrics=read('temporal_metrics.csv'); monthly=read('monthly_metrics.csv'); bins=read('calibration_bins.csv')
    flags=dict(no_date_overlap=not bool(set(development.date)&set(evaluation.date)),
        same_LAD_set=set(development.LAD21CD)==set(evaluation.LAD21CD),
        development_keys_unique=not development.duplicated(['LAD21CD','date']).any(),
        evaluation_keys_unique=not evaluation.duplicated(['LAD21CD','date']).any(),
        prediction_keys_unique=not predictions.duplicated(['LAD21CD','date','target']).any(),
        predictions_complete=len(predictions)==8*len(evaluation),
        development_dates_only=bool(development.date.between(*PERIODS['development']).all()),
        evaluation_dates_only=bool(evaluation.date.between(*PERIODS['evaluation']).all()),
        evaluation_labels_loaded_after_freeze=times['evaluation_labels_loaded_at']>times['development_frozen_at'],
        frozen_parameters_unchanged=digest(out/'frozen_development.json')==freeze_hash)
    for f in fits.to_dict('records'):
        t=f['target']; r=predictions[predictions.target==t].reset_index(drop=True); s=metrics[metrics.target==t].iloc[0]
        flags['keys_'+t]=r[['LAD21CD','date']].equals(evaluation[['LAD21CD','date']])
        flags['labels_'+t]=np.array_equal(r.y,evaluation[t])
        flags['baseline_'+t]=bool(np.all(r.baseline_prediction==development[t].mean()))
        flags['baseline_BS_'+t]=bool(np.isclose(np.mean((r.baseline_prediction-r.y)**2),s.baseline_brier,atol=1e-15,rtol=0))
        if f['valid']:
            p=probabilities(evaluation.gust,**{k:f[k] for k in ['theta','beta','p0']})
            flags['finite_'+t]=bool(np.isfinite([f[k] for k in ['theta','beta','p0','nll']]).all() and np.isfinite(r.prediction).all())
            flags['probability_bounds_'+t]=bool(r.prediction.between(0,1).all())
            flags['frozen_prediction_'+t]=bool(np.allclose(r.prediction,p,rtol=0,atol=1e-15))
            flags['model_BS_'+t]=bool(np.isclose(np.mean((r.prediction-r.y)**2),s.model_brier,rtol=0,atol=1e-15))
            flags['BSS_'+t]=bool(np.isclose(1-s.model_brier/s.baseline_brier,s.brier_skill,rtol=0,atol=1e-15))
            flags['development_bins_'+t]=edges[t]==frozen_edges(development_predictions[t])
            obj=Objective(development.gust,development[t]); nll=obj.nll(obj.encode(**{k:f[k] for k in ['theta','beta','p0']}))
            flags['development_NLL_'+t]=bool(abs(nll-f['nll'])<=1e-5)
            flags['development_selection_'+t]=bool(f['nll']<=candidates[candidates.target==t].nll.min()+1e-5)
            sub=monthly[monthly.target==t]
            flags['monthly_pooled_BS_'+t]=bool(np.isclose(np.average(sub.model_brier,weights=sub.n),s.model_brier,rtol=0,atol=1e-15))
        else:
            flags['invalid_not_filled_'+t]=bool(r.prediction.isna().all() and not r.valid_prediction.any() and np.isnan(s.model_brier))
    _,recalculated,re_month,re_bins=evaluate_frozen(evaluation,fits,edges)
    for name,a,b,columns in [('metrics',metrics,recalculated,['model_brier','baseline_brier','brier_skill','mean_prediction','observed_rate','prediction_minus_observed','calibration_rmse']),
                             ('monthly',monthly,re_month,['model_brier','baseline_brier','mean_prediction','observed_rate']),
                             ('bins',bins,re_bins,['lower','upper','n','events','mean_probability','observed_frequency'])]:
        flags['saved_'+name]=bool(np.allclose(a[columns],b[columns],equal_nan=True,rtol=0,atol=1e-15))
    invalid=fits[~fits.valid][['target','message']].to_dict('records')
    result=dict(checked_at=now(),checks={k:bool(v) for k,v in flags.items()},all_checks_passed=all(flags.values()),
        valid_development_tasks=int(fits.valid.sum()),invalid_development_tasks=invalid,
        scope='Only this development fit and frozen holdout; no historical model or tail audit',
        label_isolation='Only development rows supplied to fit_development; evaluation labels loaded after freeze',
        times=times)
    save(out/'technical_checks.json',result)
    if not result['all_checks_passed']: raise AssertionError('Technical checks failed: '+str([k for k,v in flags.items() if not v]))
    return result


def index(out,protocol,result,coverage):
    invalid=result['invalid_development_tasks']
    text=f'''# DD-TIME01 输出索引

生成：{now()}。仅说明复现、字段、完成状态和技术异常，不作科学审核、模型采用或论文结论。

## 运行

在项目根目录main_new.py中仅将最后的dd_time01设为1，运行 `python -X utf8 -B main_new.py`。当前交付开关仍为0；普通Python程序独立完成全部步骤，无agent/LLM依赖。

本次确切命令：`{protocol['command']}`。输入由DD_TIME01_SOURCE_RUN指定为正文生产运行20260909183317的final_models/district_day_panel.csv；无需REUSE_RUN、无需其他阶段开启。每次写新的秒级目录。

## 冻结范围

开发期2021-04-01至2023-09-29，后续评估期2023-09-30至2024-03-31，日期直接使用原面板保存口径，不换时区。只在开发期拟合八项背景率lognormal，复用稳定13初值和既定有限备用策略。模型有效后先冻结参数、开发率、开发期概率十分位箱，再读取评估期标签进行直接预测。无评估期重拟合/重校准/调参，无新的时间/空间划分，无bootstrap、显著性检验或独立样本误差条。

proxy沿用当日事件位置与当日事件天气插值。本检验是相同事后proxy规则下关系的跨时期迁移，不是提前预测故障，也不消除事件锚点依赖。评估期此前已用于探索，属于固定规格回顾性留出，不是从未使用过的独立确认集。没有改为开发期天气代替评估期天气。

## 文件用途

|文件|用途|
|---|---|
|protocol.json / run_manifest.json|设计、来源选择链、输入/源码SHA256、模型配置、随机种子、命令和执行时间|
|input_coverage.json / sample_summary.csv|原键与日期完整性、缺失记录、实际时期/LAD/地区日/各任务阳性数量|
|development_fit.csv / optimizer_candidates.csv.gz|八项开发期参数/有效性/既有诊断及全部初值，不读取历史全样本或LAD折内拟合|
|frozen_development.json / development_probabilities.csv.gz|评估标签加载前冻结的模型、开发常数率、箱边界及开发期概率|
|temporal_predictions.csv.gz|长表LAD/date/target；gust为原proxy(m/s)，y为原二元标签；prediction为开发期冻结模型概率，baseline_prediction为开发期阳性率|
|temporal_metrics.csv|每任务等权池化模型/基准BS，BSS=1−模型BS/基准BS，平均预测、实际率、预测减实际及固定箱校准RMSE；BSS不是准确率/R²/概率百分点|
|calibration_edges.json / calibration_bins.csv|开发概率十分位边界补0/1去重；right归箱。每箱n、events、平均预测和实际频率；空箱频率NaN，n<100保留孤立标记|
|monthly_metrics.csv|同一预测的评估期各月摘要，不重训；2023-09仅包含9月30日，按实际n解读|
|covariate_support.csv|开发/评估gust分布、评估期低于/高于开发范围的数量及比例，不做历史上限、g50或尾部曲线审计|
|figures/ / figure_axes.json|每任务校准全范围+开发概率决定的放大图及箱n/阳性表；月度率与BS图；两期proxy经验分布图|
|technical_checks.json / execution.jsonl / inventory.json|本轮必要复算、训练信息隔离顺序、逐阶段状态、产物清单与指纹|

CSV浮点回读使用 `float_precision='round_trip'`。any_gt0为至少一个事件，保留零客户；wthr_gt0为至少一个天气归因事件（含零客户）；其余标签按地区日内至少一事件客户数严格>5/>100/>1000，不按客户数日和。

## 技术完成状态

有效开发期任务{result['valid_development_tasks']}/8。无效任务及原因：{json.dumps(invalid,ensure_ascii=False)}。无效任务的正式模型预测、评分与校准留空；开发期常数率基准仍保留，不用全样本或评估标签补救。全部技术检查通过：{result['all_checks_passed']}，共{len(result['checks'])}项。

缺失LAD-day数：{coverage['missing_keys_count']}；超出固定研究期的原记录数：{coverage['outside_study_rows']}。如存在日期缺失，保存在input_coverage.json，不填造观测。两时期区域集合一致，不另造空间留出。既有边界、弱识别等拟合诊断按原值保留；成功运行不代表科学采用或参数解释已得到确认。

本轮未重算全研究期模型、历史LAD拟合、旧proxy上限/g50、incident结点联系、锚点剔除、ERA5/持续性比较或降水曲面；没有新天气请求、ZIP、独立审核报告、论文/附录/修订台账修改。到结果交付处停止。
'''
    (out/'OUTPUT_INDEX.md').write_text(text,encoding='utf-8')
