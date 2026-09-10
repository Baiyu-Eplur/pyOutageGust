"""Evidence-linked reports; no automatic manuscript adoption or Word editing."""
import json
import pandas as pd
from analysis_new.daily_aggregations import CANDIDATES
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.runner import now


def table(frame, columns):
    rows = ['|'+'|'.join(columns)+'|', '|'+'|'.join(['---']*len(columns))+'|']
    for _, r in frame.iterrows():
        cells = []
        for c in columns:
            v = r[c]
            cells.append(f'{v:.9g}' if isinstance(v, float) else str(v))
        rows.append('|'+'|'.join(cells)+'|')
    return '\n'.join(rows)


def write_report(out, protocol):
    def read(name): return pd.read_csv(out/name, float_precision='round_trip')
    metrics=read('metrics.csv'); folds=read('fold_metrics.csv'); fits=read('fit_summary.csv')
    repair=read('baseline_repair_comparison.csv'); intervals=read('paired_uncertainty.csv'); bins=read('calibration_bins.csv')
    validation=json.loads((out/'validation.json').read_text(encoding='utf-8'))
    def scored(t):
        f=metrics[metrics.target == t].merge(intervals[intervals.target == t], on=['candidate','target'])
        f['better_folds']=[int((folds[(folds.target == t) & (folds.candidate == c)].absolute_gain > 0).sum()) for c in f.candidate]
        return f
    columns=['candidate','valid_cv','brier','absolute_gain','relative_gain','brier_skill','better_folds','calibration_rmse',
             'calibration_relative_gain','absolute_gain_lo','absolute_gain_hi']
    primary=scored('any_gt100'); secondary=scored('wthr_gt100')
    invalid=fits[~fits.valid]; weak=fits[fits.weak_identification]
    best=primary[primary.valid_cv].sort_values('brier').iloc[0]
    s_best=secondary[secondary.valid_cv].sort_values('brier').iloc[0]
    summaries=[]
    for c in CANDIDATES:
        m=metrics[metrics.candidate == c]
        summaries.append(dict(candidate=c, all_8_cv_valid=bool(m.valid_cv.all()), mean_relative_gain=float(m.relative_gain.mean()),
                              positive_bss_tasks=int((m.brier_skill > 0).sum()), min_bss=float(m.brier_skill.min()),
                              max_bss=float(m.brier_skill.max()), better_brier_tasks=int((m.absolute_gain > 0).sum())))
    summary=pd.DataFrame(summaries); summary.to_csv(out/'secondary_summary.csv', index=False)
    intro=f'''# DD-AGG01：五种日度阵风聚合单因素比较报告

生成时间：{now()}。运行ID：{out.parents[1].name}。结果位置：`{out.as_posix()}`。

## 1. 先说明客观评价标准

按执行前已冻结的 [PROTOCOL.md](PROTOCOL.md) 和 [experiment.json](experiment.json) 评价。主任务为全体 >100 客户（any_gt100），重要次级为天气归因 >100 客户（wthr_gt100）；其余六任务全部保留。比较对象是本轮同一修复后优化器下的五种聚合，直接基准为 A01 日最大阵风。

首先核对实现有效性和数值有效性，再评价预测效果，最后区分参数解释与论文采用。BS=逐行OOF平均(p−y)²，越低越好；absolute_gain=BS_A01−BS_A，relative_gain=absolute_gain/BS_A01；BSS=1−BS_A/BS_训练折常数率。所有相对变化均为比例，乘100才是百分数。Brier并非纯校准误差。校准用五候选共同概率分箱的样本量加权RMSE；空箱保留，n<100不连线。

不设新的5%或其他转正门槛。结合绝对/相对量级、五折方向、配对条件区间、校准与其他任务代价判断；微小领先不自动采用，区间跨零不证明严格等效。八任务均值仅为次级摘要，若含无效比较不作为有效总体指标。1000次固定OOF整LAD配对区间不包含重训、选择及共享风暴/日期的全部不确定性。

## 2. 实现范围与输入核验

111个LAD × 1,096个UTC日 =121,656行，直接复用111份已下载ERA5小时响应，共2,919,744个小时阵风值；每日24小时，m/s。保留原返回网格、位置、原八任务标签（任意事件包含零客户）、无事件日、同一LAD折号和等权观察。禁止联网钩子在实验入口安装，未新增天气请求。原文件SHA256逐一核对；没有重新运行1106项历史整包审计。

五指标严格为：A01日最大值；A02日均小时阵风（不是平均风速）；A03 linear 90%分位数；A04不要求连续的最高3小时均值；A05日内22个连续3小时窗口的最大均值（不跨午夜）。[聚合表](daily_aggregations.csv.gz)、[分布摘要](aggregation_summary.csv)、[相关矩阵](aggregation_correlation.csv) 和 [输入核验](data_validation.json) 留存依据。A01与原日最大值最大绝对差为0。

固定天气、位置、标签、折号、模型形式后，五候选间仅改变聚合。相对历史程序同时作了必要且一致的数值修正：稳定log-CDF、不裁剪目标概率、logθ/logβ及训练率尺度p0、解析梯度、精确同值分组、13个有限初值和统一停止/备用规则。θ下限统一由2改0.1，允许p0=0，其他范围和预算同一；这属于历史基准修复，不与本轮聚合效应混为一谈。完整约束/初值与版本先于性能写入协议。

## 3. 数值修复与拟合有效性

本轮完成{len(fits)}/240个目标拟合，其中有效{int(fits.valid.sum())}，无效{len(invalid)}，保守弱识别标记{len(weak)}。弱识别与无效是不同概念；同一NLL附近不同参数或边界命中不能只凭success声称稳定θ。另有{int(fits.theta_outside_support.sum())}个θ位于该训练指标观察范围之外，参数解释须避免外推成实测损坏阈值。

已知 A01 wthr_gt1000 全样本及五训练折优于原解的合法似然点是否处理：**{validation['rare_counterexample_resolved']}**。下表保留原解、已知合法点与本轮解，非恒定预测和数值有效性同时检查。

'''+table(repair[repair.target=='wthr_gt1000'], ['scope','old_nll','known_legal_nll','repaired_nll','old_success','repaired_valid','repaired_prediction_std'])+'''

详细证据：[每个初值](optimizer_candidates.csv.gz)、[240项选中解](fit_summary.csv)、[参数表](parameters.csv)、[六项先行诊断](rare_repair_gate.json)。这些是有限数值检查，不是全局最优或完整可识别性的数学证明。

'''
    intro+='无效拟合：\n\n'+(table(invalid, ['candidate','target','scope','nll','projected_gradient','boundary','prediction_std']) if len(invalid) else '无。')+'\n\n'
    intro+='弱识别拟合：\n\n'+(table(weak, ['candidate','target','scope','theta','beta','p0','boundary','near_optimal_solutions']) if len(weak) else '本轮既定筛查未标记；这不等于参数识别已被完整证明。')+'\n\n'
    intro+='## 4. 主任务和重要次级任务\n\n主任务 any_gt100：\n\n'+table(primary, columns)+'\n\n重要次级 wthr_gt100：\n\n'+table(secondary, columns)+'\n\n'
    intro+=f'''主任务最低BS为 {best.candidate}：{best.brier:.9f}，相对修复后A01变化 {best.relative_gain*100:.4f}%，绝对改善 {best.absolute_gain:.9f}；五折中{int(best.better_folds)}折改善。次级最低BS为 {s_best.candidate}：{s_best.brier:.9f}，相对变化 {s_best.relative_gain*100:.4f}%。上述只是固定候选探索排序，并非未经选择的最终泛化估计。

### 五折对比（全部候选并列）

'''
    for t in ['any_gt100','wthr_gt100']:
        intro+=t+'：\n\n'+table(folds[folds.target==t], ['candidate','fold','n','valid','brier','absolute_gain','relative_gain','constant_brier'])+'\n\n'
    intro+='## 5. 其他六任务、常数率基准及校准\n\n'
    for t in TARGETS:
        if t in ['any_gt100','wthr_gt100']: continue
        intro+=t+'：\n\n'+table(scored(t), columns)+'\n\n'
    intro+='八任务次级摘要（不得替代主任务）：\n\n'+table(summary, list(summary.columns))+'\n\n'
    intro+=f'''相对训练折常数率，40组候选任务中{int((metrics.brier_skill > 0).sum())}组BSS>0；最小BSS={metrics.brier_skill.min():.6f}，最大={metrics.brier_skill.max():.6f}。只有有效CV结果可用于此预测信息判断。较好的BS和较好的分箱校准不必同向，完整数值均已列出，不用图形替代主评分。

共同分箱共{len(bins)}条候选/箱记录，其中空箱{int((bins.n==0).sum())}，非空但n<100的稀疏箱{int(((bins.n>0)&(bins.n<100)).sum())}。每箱样本/阳性数、精确边界、预测均值和发生频率见 [calibration_bins.csv](calibration_bins.csv)、[calibration_edges.json](calibration_edges.json)。稀疏点以叉号显示、不连接，空箱不填0；完整范围和共同放大图同时保存。输入回读采用 round_trip，复算分箱人数和频率一致。

主任务：[校准图](figures/calibration_any_gt100.png)、[发生率—聚合曲线](figures/occurrence_any_gt100.png)。次级：[校准图](figures/calibration_wthr_gt100.png)、[发生率—聚合曲线](figures/occurrence_wthr_gt100.png)。其余六任务也各有两图。发生率曲线来自全样本描述，不进入OOF校准；五种聚合的同一m/s值含义不同，不把θ位移解释成真实物理阈值变化。数据见 [occurrence_curve_data.csv](occurrence_curve_data.csv)。

## 6. 区分优化修复与聚合改变

以下只比较原程序A01与本轮A01；之后的候选表才是纯聚合对比。修复造成的变化不能记为其他聚合的收益。

'''+table(repair[repair.scope=='full'], ['target','old_nll','repaired_nll','old_oof_brier','repaired_oof_brier','repair_absolute_gain'])+'''

## 7. 客观结论与采用边界

实现范围固定、数值修复有效性、预测优势和参数解释四者须分别看待。当前主/次任务的改善量级、折间方向、校准及其他任务代价见上表；不自动用最低分替换现有日最大值。若某替代指标在主/次任务呈一致且有实际意义的优势，可将其列为下一轮定向时间验证候选；本轮不新增时间划分、不进一步扩大候选集。若收益微小或校准/折间证据不一致，保留日最大值是合理选择，而不是声称严格等效。

District-day正文章节按用户决定保留；本轮可补充固定聚合敏感性、修复后概率验证与训练率基准。不能据此声称ERA5为观测真值、解决全部IDW/网格来源差异、模型具有跨未来时间的已验证泛化，或稳定估计了物理损坏阈值。历史P03未达原门槛的记录不改写。

本轮未直接修改Word或Table7，未覆盖历史结果，未生成回传zip。具体模型采用和论文文字待人工+agent混合审查。[MANUSCRIPT_RECORD.md](MANUSCRIPT_RECORD.md) 列明正文/附录落点与待定状态。

## 8. 必要核验、代码及产物清单

'''+f"[validation.json](validation.json) 中 {len(validation['checks'])} 项本轮针对性回读检查全部通过：{validation['all_checks_passed']}。包括240项矩阵唯一性、聚合精确回读、共享标签/固定折、每LAD仅一折、训练率无测试标签、40个BS重算、共同分箱重算；原小时有效性和A01复现另存 data_validation.json。聚合常数/排序/午夜/连续性和解析梯度/原始行似然用少量单元测试验证。\n\n"
    intro+='代码：`main_new.py`（最后一个dd_agg01开关，默认0）、`analysis_new/runner.py`（独立阶段）、`analysis_new/daily_aggregations.py`、`analysis_new/fragility_optimizer.py`、`analysis_new/dd_agg01.py`、`analysis_new/dd_agg01_evaluation.py`、`analysis_new/dd_agg01_report.py`、`test/test_dd_agg01.py`。复用现有 grid_weather.parse_hourly、P03 verified_output、TARGETS及 paired_bootstrap；历史模型程序保留。永久工作规则见项目 AGENTS.md/CLAUDE.md，每步修改及测试时间见 LOG.md。\n\n'
    intro+='全部产物逐文件路径、大小、SHA256见 [inventory.json](inventory.json)，原小时文件路径与指纹同样保留，不重复下载或打包。逐阶段/逐拟合记录见 [execution.jsonl](execution.jsonl) 与 [fit_checkpoint.jsonl](fit_checkpoint.jsonl)。\n'
    (out/'REPORT.md').write_text(intro, encoding='utf-8')
    record='''# DD-AGG01 论文修订台账

本轮仅记录建议，Word、Table7和Figure8均未直接改动。District-day正文按用户决定保留，历史P03结论不改写。

|任务ID|发现|证据文件/行或图表|涉及正文位置|建议修改|建议附录内容|状态|
|---|---|---|---|---|---|---|
|DD-AGG01-01|相同小时源、标签和原折下固定五种聚合|PROTOCOL.md；data_validation.json；daily_aggregations.csv.gz|Extended §3.5|说明UTC24小时聚合定义及任意事件含零客户|原文件指纹、五指标分布/相关|待联合审查|
|DD-AGG01-02|历史稀有任务有已知合法NLL反例，统一优化修复单列|baseline_repair_comparison.csv 的 wthr_gt1000 六行；rare_repair_gate.json|§3.5、§4.4、Table7|说明稳定似然和多初值；有效参数经审查后才可替换|240拟合及全部初值诊断、边界/弱识别|计算完成；未改Word|
|DD-AGG01-03|主要/次级任务五聚合OOF数值与逐折方向|metrics.csv/paired_uncertainty.csv 中 any_gt100、wthr_gt100；fold_metrics.csv|§4.4、Figure8|如实写出绝对和相对差，不只列优胜者|其余六任务、条件LAD区间及限制|待选用，不自动采用|
|DD-AGG01-04|训练率BSS与共同箱校准补足单一分数|metrics.csv；calibration_bins.csv；figures/calibration_*.png|§4.4、Figure8|区分概率预测信息和校准，保留稀疏支持|精确边界、空箱/稀疏箱、全范围图|图表已生成；待审查|
|DD-AGG01-05|不同聚合参数不能直接解释为物理阈值|parameters.csv 的 theta_outside_support/weak_identification；figures/occurrence_*.png|Table7、§5|限定θ解释和外推范围|全样本/训练折参数、曲线数据|待文字修订|
|DD-AGG01-06|固定候选探索与LAD留出不等于未来时间验证|REPORT.md §7；paired_uncertainty.csv|§5|保留正文并说明观察性、选择和时空依赖限制|五候选完整比较；必要时仅建议下一轮定向时间核验|未新增实验；待用户判断|
'''
    (out/'MANUSCRIPT_RECORD.md').write_text(record, encoding='utf-8')
    # A self-contained text return is useful for later human/agent review; no archive.
    (out/'RETURN_TO_CHATGPT.md').write_text(intro, encoding='utf-8')
