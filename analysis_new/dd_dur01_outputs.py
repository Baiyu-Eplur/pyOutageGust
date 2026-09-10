"""DD-DUR01 technical outputs only: no review or adoption decision."""
import json
import numpy as np
import pandas as pd
from analysis_new.duration_features import MODELS
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.dd_agg01_evaluation import evaluate, uncertainty
from analysis_new.runner import save, now


def evaluate_outputs(out,oof,fits,full):
    scores,folds,bins,edges=evaluate(oof,fits,candidates=MODELS)
    scores=scores.rename(columns={'brier_a01':'brier_m0'}); folds=folds.rename(columns={'brier_a01':'brier_m0'})
    # Invalid CV is retained as diagnostic output, never a complete valid comparison.
    for frame in [scores,folds]:
        valid_col='valid_cv' if frame is scores else 'valid'
        frame['diagnostic_brier']=frame.brier
        frame.loc[~frame[valid_col],['brier','absolute_gain','relative_gain']]=np.nan
        if 'brier_skill' in frame: frame.loc[~frame[valid_col],'brier_skill']=np.nan
    scores.to_csv(out/'metrics.csv',index=False); folds.to_csv(out/'fold_metrics.csv',index=False)
    intervals=uncertainty(oof,scores,candidates=MODELS)
    interval_cols=['absolute_gain_lo','absolute_gain_hi','relative_gain_lo','relative_gain_hi']
    intervals.loc[~intervals.valid_comparison,interval_cols]=np.nan
    intervals.to_csv(out/'paired_uncertainty.csv',index=False)
    bins.to_csv(out/'calibration_bins.csv',index=False); save(out/'calibration_edges.json',edges)
    plot(out,bins,full)
    return scores,folds,bins


def plot(out,bins,full):
    import matplotlib.pyplot as plt
    folder=out/'figures'; folder.mkdir()
    colors=plt.get_cmap('tab10').colors; axis_records=[]
    for target in TARGETS:
        b=bins[bins.target==target]; dense=b[b.n>=100]
        limit=min(1.,max(.005,1.15*float(dense[['mean_probability','observed_frequency']].max().max()))) if len(dense) else 1.
        outside=int(((b.n>0)&((b.mean_probability>limit)|(b.observed_frequency>limit))).sum())
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax,lim in zip(axes,[1.,limit]):
            ax.plot([0,lim],[0,lim],'k--',lw=1)
            for j,c in enumerate(MODELS):
                rows=b[b.candidate==c]
                ax.plot(rows.mean_probability.where(rows.n>=100),rows.observed_frequency.where(rows.n>=100),'-o',
                        color=colors[j],markersize=4,label=c if len(rows) else c+' (invalid CV)')
                sparse=rows[(rows.n>0)&(rows.n<100)]
                ax.scatter(sparse.mean_probability,sparse.observed_frequency,color=colors[j],marker='x',s=45)
            ax.set(xlim=(0,lim),ylim=(0,lim),xlabel='Mean OOF probability',ylabel='Observed frequency')
            ax.set_aspect('equal',adjustable='box'); ax.grid(alpha=.2)
        axes[0].set_title('Full probability range; all nonempty bins')
        axes[1].set_title(f'Supported-bin zoom; {outside} tail point(s) in full view')
        axes[1].legend(fontsize=8); fig.suptitle(target+': shared M0/M1/M2 bins; crosses n<100')
        fig.tight_layout(); fig.savefig(folder/f'calibration_{target}.png',dpi=160); plt.close(fig)
        axis_records.append(dict(target=target,zoom_upper=limit,tail_points_outside_zoom=outside))
    save(out/'figure_axes.json',axis_records)
    fig,axes=plt.subplots(1,2,figsize=(12,5)); joint=[]
    g_edges=np.arange(0.,max(40.,np.ceil(full.G.max()/5)*5)+5,5.)
    for ax,name,label in zip(axes,['h','x'],['Exceedance hourly fraction h','log(1 + dimensionless squared-excess index J)']):
        y_edges=np.linspace(0,1,21) if name=='h' else np.arange(0.,max(.1,np.ceil(full.x.max()*10)/10)+.100001,.1)
        counts,ge,fe=np.histogram2d(full.G,full[name],bins=[g_edges,y_edges])
        shown=np.ma.masked_where(counts.T==0,counts.T)
        from matplotlib.colors import LogNorm
        mesh=ax.pcolormesh(ge,fe,shown,norm=LogNorm(vmin=1,vmax=max(2,counts.max())),cmap='viridis')
        fig.colorbar(mesh,ax=ax,label='Observed LAD-days'); ax.set(xlabel='Daily maximum gust G (m/s)',ylabel=label)
        for i in range(len(ge)-1):
            for j in range(len(fe)-1):
                joint.append(dict(feature=name,G_lower=ge[i],G_upper=ge[i+1],feature_lower=fe[j],feature_upper=fe[j+1],n=int(counts[i,j])))
    fig.suptitle('Observed joint support at full-training weather threshold (no scenario extrapolation)')
    fig.tight_layout(); fig.savefig(folder/'observed_joint_support.png',dpi=160); plt.close(fig)
    pd.DataFrame(joint).to_csv(out/'joint_support_bins.csv',index=False)


def validate(out,panel,folds,hours,feature_tables,fit_summary,baseline_checks,scores):
    from analysis_new.duration_features import threshold, features
    from analysis_new.fragility_optimizer import probabilities
    read=lambda name:pd.read_csv(out/name,float_precision='round_trip')
    oof=read('oof_predictions.csv.gz'); features_saved=read('features_by_fold.csv.gz')
    checks=dict(target_matrix_144=len(fit_summary)==144 and not fit_summary.duplicated(['candidate','target','scope']).any(),
                oof_keys_unique=not oof.duplicated(['LAD21CD','date']).any(),
                preserved_labels=np.array_equal(oof[TARGETS],panel[TARGETS]),
                preserved_keys=oof[['LAD21CD','date']].equals(panel[['LAD21CD','date']]),
                fixed_folds=np.array_equal(oof.fold,folds),one_fold_per_lad=bool(oof.groupby('LAD21CD').fold.nunique().eq(1).all()))
    thresholds=read('thresholds.csv')
    for scope,table in feature_tables.items():
        train=np.ones(len(panel),dtype=bool) if scope=='full' else folds!=int(scope.split('_')[1])
        tau=threshold(hours,train); row=thresholds[thresholds.scope==scope].iloc[0]
        checks['train_threshold_'+scope]=bool(tau==row.tau and train.sum()*24==row.training_hours)
        saved=features_saved[features_saved.scope==scope].reset_index(drop=True)
        rec=features(hours,tau)
        checks['features_'+scope]=bool(np.array_equal(saved[['G','H','I','h','J','x']],rec) and np.all(saved.tau==tau))
    for t in TARGETS:
        for fold in range(5):
            m=folds==fold
            checks[f'train_rate_{t}_{fold}']=bool(np.all(oof.loc[m,t+'_constant']==panel.loc[~m,t].mean()))
        for c in MODELS:
            p=oof[t+'__'+c].to_numpy(); row=scores[(scores.target==t)&(scores.candidate==c)].iloc[0]
            bs=np.mean((p-panel[t].to_numpy())**2)
            checks[f'BS_{t}_{c}']=bool(np.isclose(bs,row.diagnostic_brier,atol=1e-15,rtol=0,equal_nan=True))
            for fold in range(5):
                f=fit_summary[(fit_summary.candidate==c)&(fit_summary.target==t)&(fit_summary.scope==f'fold_{fold}')].iloc[0]
                if not np.isfinite(f.theta): continue
                m=folds==fold; ft=feature_tables[f'fold_{fold}']
                pred=probabilities(ft.loc[m,'G'],theta=f.theta,beta=f.beta,p0=f.p0,gamma=f.gamma,
                                   feature=None if c=='M0' else ft.loc[m,'h' if c=='M1' else 'x'])
                checks[f'prediction_{t}_{c}_{fold}']=bool(np.allclose(p[m],pred,atol=1e-15,rtol=0))
    _,_,recreated,_=evaluate(oof,fit_summary,candidates=MODELS); saved=read('calibration_bins.csv')
    checks['calibration_counts']=np.array_equal(recreated[['n','events']],saved[['n','events']])
    checks['calibration_values']=bool(np.allclose(recreated[['lower','upper','mean_probability','observed_frequency']],saved[['lower','upper','mean_probability','observed_frequency']],atol=1e-15,rtol=0,equal_nan=True))
    candidates=read('optimizer_candidates.csv.gz'); selection_checks=[]
    for f in fit_summary[fit_summary.candidate!='M0'].itertuples():
        r=candidates[(candidates.candidate==f.candidate)&(candidates.target==f.target)&(candidates.scope==f.scope)]
        legal=float(r.nll.min()) if len(r) else np.nan
        selection_checks.append(dict(candidate=f.candidate,target=f.target,scope=f.scope,valid=bool(f.valid),
                                     no_better_evaluated_point=bool(f.nll<=legal+1e-5),no_better_m0=bool(f.nll<=f.baseline_nll+1e-5)))
    checks['all_valid_fits_pass_legal_points']=all(r['no_better_evaluated_point'] and r['no_better_m0'] for r in selection_checks if r['valid'])
    result=dict(checked_at=now(),checks={k:bool(v) for k,v in checks.items()},all_checks_passed=all(checks.values()),
                valid_fits=int(fit_summary.valid.sum()),invalid_fits=int((~fit_summary.valid).sum()),
                weak_identification=int(fit_summary.weak_identification.sum()),selection_checks=selection_checks)
    save(out/'validation.json',result)
    if not result['all_checks_passed']: raise AssertionError([k for k,v in checks.items() if not v])
    return result


def readme(out,protocol,validation):
    text=f'''# DD-DUR01 运行与结果字段说明

生成：{now()}。运行结果：`{out.as_posix()}`。

本文件仅说明实现、字段、复现方法及技术状态，不作独立科学审查或主模型采用判断。

## 实际运行方式

当前环境执行命令：`{protocol['command']}`。

常规独立运行：在项目根目录 main_new.py 将最后的 `STEPS['dd_dur01']` 改为1，其余研究阶段保持0，运行 `python -X utf8 -B main_new.py`。只依赖普通Python程序和本地文件，无agent、LLM或对话单元依赖。默认交付的阶段开关仍为0。无需开启DD-AGG01或P03阶段、无需REUSE_RUN。基准/天气运行号分别在DD_DUR01_BASE_RUN和DD_DUR01_WEATHER_RUN设置；只读校验后复用。每次输出新的秒级目录，不覆盖旧运行。

## 固定定义与文件

- protocol.json / PROTOCOL.md：冻结输入指纹、单位、范围、模型、优化/评价/图形规则、源码与环境版本。
- thresholds.csv：scope=full或fold_0..4；tau为该训练范围全部LAD小时阵风的linear90%分位，单位m/s；training_hours按LAD小时等权（共享网格不去重），training_lads与held_out_fold可追踪。
- features_by_fold.csv.gz：六个scope各包含完整121,656行；role=train/test或full，fold为原LAD折号。G单位m/s；H为严格g>tau的小时数，h=H/24；I为sum(max(g²−tau²,0))，单位(m/s)²·小时；J=I/(24tau²)，x=log1p(J)无量纲。模型使用h或x，不额外标准化/中心化。full表仅供描述，不进入OOF。
- feature_support.csv：各训练/测试范围，全部G及固定5m/s箱内的H/I/h/J/x/G分布、零/正值数、相关；空箱n=0且统计NaN，不删除。joint_support_bins.csv及观察支持图只展示已有天气组合，不创建G>tau且H=0的预测情景。
- baseline_match.json：与DD-AGG01有效A01的数据、标签、折号、范围、全部48项NLL/参数预测和BS匹配。M0复用48项，不新增重拟合。
- fit_summary.csv / parameters.csv：144目标；candidate=M0/M1/M2，scope全样本或训练折；M1/M2各重新估计theta/beta/p0/gamma，M0 gamma=0。origin标识复用或新拟合；valid是数值检查，weak_identification与theta_outside_support另列，不能等同采用结论。所有参数和gamma正负照实保留。
- optimizer_candidates.csv.gz：M0原诊断导入，M1/M2各16初值及全部优化终点、状态/梯度/边界/离散度/选择原因；同范围M0 gamma=0是合法候选。baseline_nll与nll_gain_vs_m0仅为拟合诊断。gamma物理范围[-20,20]；仅优化坐标用训练特征RMS缩放，回存物理gamma。
- oof_predictions.csv.gz：原键、fold、8标签，训练折tau及G/H/I/h/J/x；每任务 `target__M0/M1/M2` 为折外概率，`target_constant` 为训练标签事件率。没有使用full参数或full阈值。full_predictions.csv.gz仅保存观察到组合的全样本描述预测，不用于评分或校准。
- metrics.csv / fold_metrics.csv：逐行池化BS、M0基准、绝对/相对下降、训练常数BSS；positive gain表示BS降低。valid_cv/valid=false时正式BS/增量/BSS为NaN，diagnostic_brier可保留算法输出但不能用作有效比较，不删坏折重算。
- paired_uncertainty.csv：M1/M2相对M0的1000次整LAD配对固定OOF条件区间，三模型同抽样、同种子、保留行数权重。不覆盖重训、模型选择、阈值重新估计及共享风暴/日期的全部不确定性。
- calibration_bins.csv / calibration_edges.json：本轮M0/M1/M2有效OOF概率共同十分位边界，补0/1去重，searchsorted(right)，n<100稀疏标记、空箱NaN，不改箱或删尾部。它与DD-AGG01候选集合不同，不能将两轮校准RMSE直接当同比进步。CSV须 `float_precision='round_trip'` 回读。
- figures：每任务全范围+主要支持区间放大校准图，范围外尾部数注明且全图保留；无效模型在图例注明；观察联合支持图无模型胜出标题。figure_axes.json记录显示范围。
- validation.json / execution.jsonl / inventory.json：必要实现核验、逐目标执行状态、输入/产物指纹。invalid/error如存在需按目标定位，不能静默填常数；程序completed表示文件流程完成，不代表每项拟合有效或科学采用。

## 技术完成范围

144个目标记录：48个M0复用，96个M1/M2新增。有效{validation['valid_fits']}，无效{validation['invalid_fits']}，弱识别标记{validation['weak_identification']}。本轮必要核验{len(validation['checks'])}项，全部通过={validation['all_checks_passed']}。具体无效、边界或超观察支持记录见参数表，不在此给科学裁决。

tau是数据尺度参考；H是小时阵风指标超过阈值的小时计数；J混合超阈强度与持续性，不是纯时长、损伤或能量测量。gamma可正可负，不能把负系数直接解释为保护机制。固定持续性值下数学中点为theta exp(−beta gamma feature)，概率(1+p0)/2，不能无视联合支持当作一般50%物理阈值。没有增加时间验证、天气源、M3、其他阈值/幂次。未改论文、未生成回传包；本轮在技术结果交付处停止。
'''
    (out/'RESULTS_README.md').write_text(text,encoding='utf-8')
