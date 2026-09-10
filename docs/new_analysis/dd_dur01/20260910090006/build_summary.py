"""Build a bounded result summary from existing DD-DUR01 tables, without refitting."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SOURCE=PROJECT/'results/new/20260910090006/results/dd_dur01'
NAMES={'any_gt0':'全体：任意事件','any_gt5':'全体：>5','any_gt100':'全体：>100','any_gt1000':'全体：>1000',
       'wthr_gt0':'天气归因：任意事件','wthr_gt5':'天气归因：>5','wthr_gt100':'天气归因：>100','wthr_gt1000':'天气归因：>1000'}


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name): return pd.read_csv(SOURCE/name,float_precision='round_trip')
def link(name,label=None): return f'[{label or name}]({(SOURCE/name).as_posix()})'
def md(headers,rows):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|',*['|'+'|'.join(map(str,row))+'|' for row in rows]])


def main():
    m=read('metrics.csv'); folds=read('fold_metrics.csv'); u=read('paired_uncertainty.csv')
    fits=read('fit_summary.csv'); bins=read('calibration_bins.csv'); support=read('feature_support.csv')
    inv=json.loads((SOURCE/'inventory.json').read_text(encoding='utf-8'))
    assert all(digest(SOURCE/r['path'])==r['sha256'] for r in inv['files'])
    assert len(m)==24 and len(fits)==144 and m.valid_cv.all() and fits.valid.all()
    by=m.set_index(['target','candidate']); ui=u.set_index(['target','candidate'])
    def better(t,c): return int((folds[(folds.target==t)&(folds.candidate==c)].absolute_gain>0).sum())
    def performance(targets):
        rows=[]
        for t in targets:
            for c in ['M0','M1','M2']:
                r=by.loc[t,c]; ci=ui.loc[t,c]
                rows.append([NAMES[t],c,f'{r.brier:.10f}',f'{r.absolute_gain:.6g}',f'{100*r.relative_gain:.6f}',
                             '—' if c=='M0' else f'[{ci.absolute_gain_lo:.6g}, {ci.absolute_gain_hi:.6g}]',
                             '—' if c=='M0' else f'{better(t,c)}/5',f'{100*r.brier_skill:.4f}'])
        return md(['任务','模型','OOF Brier','ΔBS','相对下降 %','ΔBS 条件95%区间','改善折数','BSS %'],rows)
    text=f'''# DD-DUR01 客观结果总结

报告时间：{datetime.now().astimezone().isoformat()}。结果运行：20260910090006。

本报告在用户告知已完成审阅后，根据保存的实验结果整理。用户尚未提供具体审阅意见或主模型决定，本报告不代述这些意见。范围为客观结果总结，未重新拟合、增加实验、修改论文或改写历史运行。

## 一、评价标准与结论边界

按执行前的 {link('PROTOCOL.md','冻结协议')} 和 {link('protocol.json','机器配置')}，主要任务为**全体 >100 客户**，重要次级为**天气归因 >100 客户**；其余六任务完整呈现。

1. **先看数值有效性。** 需保留相同数据、标签、原LAD折号，并确认增量拟合不劣于其合法嵌套M0点和其他已评价初值。收敛成功或训练NLL降低单独不构成样本外优势。
2. **主评分为逐行池化OOF Brier。** BS=mean[(p−y)²]，越低越好；ΔBS=BS_M0−BS_Mj，正值表示增量模型改善；相对下降=100×ΔBS/BS_M0。它是Brier的相对百分比，不是事件概率百分点。
3. **同时看逐折方向、幅度与条件区间。** 五折BS不作无权简单平均替代总BS；配对区间来自1000次整LAD重采样，固定当前OOF预测及同一抽样。它不涵盖重训、阈值重估、模型选择、共享日期/风暴的全部不确定性。区间跨零不证明严格等效，也不证明物理持续时间无效。
4. **查看训练率基准与校准。** BSS=1−BS模型/BS训练折常数率。校准RMSE=sqrt[Σ箱 n(平均预测−实际频率)²/N]；它依赖分箱及样本支持，不与BS等同，也不替代主评分。
5. **不增设采用门槛。** 不事后增加5%等规则、不因γ为正或样本内NLL更低自动采用。客观结论限定于当前数据、预定τ、背景率lognormal形式和LAD留出设计；主模型与论文修改仍由用户决定。

## 二、实验范围与完成状态

本轮是三个预先固定候选的探索性比较，不是选出模型后再进行的独立确认。

研究期为2021-04-01至2024-03-31，共111个LAD、1096个UTC自然日、121,656个地区日，复用2,919,744条LAD小时阵风记录。原ERA5位置与网格、八标签、无事件日、观察权重、LAD折号均不变。任意事件包括零客户记录；其他客户阈值均为严格大于。

|模型|线性预测部分 z|自由参数|
|---|---|---|
|M0 日最大阵风|(ln G−ln θ)/β|θ、β、p₀|
|M1 日最大阵风＋超阈小时比例|z₀＋γH/24|θ、β、p₀、γ|
|M2 日最大阵风＋超阈值阵风平方累计指标|z₀＋γ ln(1＋J)|θ、β、p₀、γ|

令G=maxₕ gₕ，gₕ为小时阵风（m/s），p₀为背景率参数。三者均为 p=p₀+(1−p₀)Φ(z)。H=Σ1(gₕ>τ)小时；I=Σ(gₕ²−τ²)₊小时；J=I/(24τ²)，无量纲。M1/M2独立重估全部四参数，γ允许正负，γ=0时回到M0。没有同时加入两项的M3。

τ只用各训练范围全部LAD小时天气的linear90%分位数，八任务共用，测试天气和标签不参与。共享网格按LAD小时观察权重保留。full τ=13.6 m/s；fold_0..4依次为13.6、13.6、13.6、13.5、13.7 m/s。它是数据尺度参考，不是物理损坏阈值。见 {link('thresholds.csv')}。

**144/144个目标拟合有效**：48个M0由已修复DD-AGG01 A01匹配复用，96个M1/M2新增。M0重算NLL、OOF概率和BS与保存值的最大差均为0。29项运行前测试、205项程序内技术核验通过；无无效拟合、无边界命中、无既定弱识别标记。有限多初值检查不等于全局最优或完整可识别性证明。证据：{link('baseline_match.json')}、{link('fit_summary.csv')}、{link('validation.json')}。

## 三、主要任务与重要次级任务

'''+performance(['any_gt100','wthr_gt100'])+f'''

**两个增量模型在主、次任务的池化Brier均略高于M0。** 主任务M1增加8.61318×10⁻⁷（相对0.001538%），M2增加8.37217×10⁻⁶（0.014948%）；次级M1增加3.17849×10⁻⁷（0.001674%），M2增加2.72209×10⁻⁶（0.014338%）。绝对差很小，不宜将其写成大幅性能退化；但方向并非增量改善，四个ΔBS条件区间均跨零。

M1主任务5/5折均略差，次级4/5折略差。M2主、次任务都在fold_0、fold_1、fold_4改善，在fold_2、fold_3退化；退化幅度足以抵消其余折的收益，因此不能用“多数折改善”代替池化BS。折方向与LAD条件区间是不同摘要，M1主任务五折同向但LAD区间跨零并不矛盾。

### 各折绝对变化

下表单位为 **10⁻⁶ Brier**，正值为改善；列出增量而非重复全量概率评分。

'''
    rows=[]
    for t in ['any_gt100','wthr_gt100']:
        for fold in range(5):
            r=folds[(folds.target==t)&(folds.fold==fold)].set_index('candidate')
            rows.append([NAMES[t],fold,f'{r.loc["M1","absolute_gain"]*1e6:.4f}',f'{r.loc["M2","absolute_gain"]*1e6:.4f}'])
    text+=md(['任务','测试折','M1 ΔBS×10⁶','M2 ΔBS×10⁶'],rows)+f'\n\n来源：{link("metrics.csv")}、{link("fold_metrics.csv")}、{link("paired_uncertainty.csv")}。\n\n'
    text+='## 四、其余六任务的完整结果\n\n'+performance([t for t in NAMES if t not in ['any_gt100','wthr_gt100']])+'''

M1八任务的池化BS均略高于M0，没有任何任务给出池化BS改善。M2在六任务略差，仅在两个 >1000 客户任务略好：

- 全体 >1000：ΔBS=3.17181×10⁻⁶，相对改善0.038523%，4/5折改善，条件95%区间[−4.62896×10⁻⁶, 1.08795×10⁻⁵]。
- 天气归因 >1000：ΔBS=1.72725×10⁻⁶，相对改善0.069792%，5/5折改善，条件95%区间[−7.41429×10⁻⁷, 4.21575×10⁻⁶]。

这两个方向为正的结果需要保留，尤其天气稀有任务五折均有微小改善；但两项区间均跨零，幅度也很小，不能据此宣称增量模型对全部任务具有稳定优势。M2在主、次任务以及其他四项的轻微代价同样不能隐藏。部分非主任务的区间完全位于负侧，也不能把这种很小的退化自动放大为工程重要性结论。

## 五、相对训练折常数率的预测信息

24/24组模型任务的BSS为正，范围约0.9337%–5.2277%。M0主任务BSS=1.5769%，次级=4.6330%；M1分别为1.5754%、4.6314%，M2分别为1.5622%、4.6193%。

因此三个模型相对于仅用训练折事件率的常数预测都有一定信息，但这一共同优点不能被归功于新增持续性项。当前主要和重要次级结果没有显示，H或J在已知日最大阵风后进一步提高这一评分。

## 六、校准与样本支持

### 1. 本轮共同分箱结果

'''
    rows=[]
    for t in NAMES:
        a,b,c=[by.loc[t,k] for k in ['M0','M1','M2']]
        rows.append([NAMES[t],f'{a.calibration_rmse:.8f}',f'{b.calibration_rmse:.8f}',f'{c.calibration_rmse:.8f}',
                     f'{100*b.calibration_relative_gain:.3f}',f'{100*c.calibration_relative_gain:.3f}'])
    text+=md(['任务','M0 RMSE','M1 RMSE','M2 RMSE','M1相对下降 %','M2相对下降 %'],rows)+f'''

主任务M1/M2的校准RMSE分别增加5.763%/11.636%；次级增加3.899%/101.860%。本轮两个重点任务未出现“BS改善且校准同步改善”的组合。其他任务存在不同向现象，例如M2天气任意事件的校准RMSE降低23.730%，其BS却略差；M2两个稀有任务的BS略好，分箱校准反而更差。

这些校准比较只在本轮三模型共同边界内成立。**不能把本轮M0校准RMSE与DD-AGG01直接同比**：M0的OOF预测并未改变，但候选集合由五种聚合变为三个模型，共同边界改变足以改变分箱RMSE。

### 2. 尾部箱的支持限制

共有288条模型/任务/箱记录，其中41个空箱、8个非空但n<100的稀疏箱；8个稀疏箱均是M2各任务中n=1的最高概率箱。原结果完整保留这些点，空箱不填0，稀疏点不连成趋势线。见 {link('calibration_bins.csv')}、{link('calibration_edges.json')}。

按原箱n权重计算，这个单样本尾部箱贡献M2分箱平方校准误差的比例为：主任务9.50%、重要次级19.90%、全体 >1000为67.95%、天气 >1000为96.83%。天气稀有任务M2 RMSE相对M0增加561.534%，不能直接写成整体校准同等幅度恶化；该比例主要由一个样本的尾部箱放大。不过也不能将该箱删除后重新宣称校准改善。本报告只解释支持度，未改箱、重算删样本得分或隐去不利结果。

'''
    for t in ['any_gt100','wthr_gt100','wthr_gt1000']:
        text+=f'![{NAMES[t]}校准完整范围及支持区间]({(SOURCE/"figures"/("calibration_"+t+".png")).as_posix()})\n\n'
    text+='## 七、新指标是否存在可区分的观察变化\n\n'
    text+='full τ=13.6 m/s下，H=0（同时I/J/x=0）的地区日为88,380，占72.6475%；H>0为33,276，占27.3525%。H范围0–24小时，95%分位数15小时；J最大2.49976，x最大1.25269。G与h相关0.79385，与x相关0.73870。这些指标与峰值关系较强，但并非在所有峰值范围都恒定。\n\n'
    rows=[]
    for lo in [15.,20.,25.,30.,35.]:
        subset=support[(support.scope=='full')&(support.role=='full')&(support.peak_lower==lo)&(support.peak_upper==lo+5)].set_index('feature')
        h=subset.loc['H']; x=subset.loc['x']
        rows.append([f'[{lo:g},{lo+5:g})',int(h.n),f'{h.p25:g} / {h.p50:g} / {h.p75:g}',f'{x.p25:.4f} / {x.p50:.4f} / {x.p75:.4f}'])
    text+=md(['G箱 m/s','地区日数','H：25/50/75%分位（小时）','x：25/50/75%分位'],rows)+f'''

相近峰值的箱内存在持续性差异，例如G∈[15,20) m/s时H的四分位区间为5–12小时。这排除了“新变量在所有相关单元都近似常数”这一简单解释，但5 m/s粗分箱本身不能证明给定精确G时的独立效应。极端G∈[35,40)只有2个地区日，不能支持丰富的高风速联合情景外推。

证据：{link('feature_support.csv')}、{link('features_by_fold.csv.gz')}。H是小时阵风指标超阈的小时计数，不是连续风速真实超阈时长的精确测量；J同时包含强度和持续性，不能称为结构损伤、风能耗散或已测风荷载积分。

![已观察的联合支持]({(SOURCE/'figures/observed_joint_support.png').as_posix()})

## 八、参数与训练拟合的解释限制

下表为全样本γ、五训练折γ范围和全样本NLL下降；该范围不是置信区间，NLL下降只用于说明训练拟合变化。

'''
    rows=[]
    for c in ['M1','M2']:
        for t in NAMES:
            full=fits[(fits.candidate==c)&(fits.target==t)&(fits.scope=='full')].iloc[0]
            train=fits[(fits.candidate==c)&(fits.target==t)&(fits.scope!='full')]
            rows.append([c,NAMES[t],f'{full.gamma:.6f}',f'[{train.gamma.min():.6f}, {train.gamma.max():.6f}]',f'{full.nll_gain_vs_m0:.6f}'])
    text+=md(['模型','任务','γ full','γ 五训练折范围','full NLL下降'],rows)+f'''

M1主、次任务γ在五折之间跨正负，full NLL改善分别仅0.001774和0.056764。M2主、次任务γ在五折均为正，full NLL也降低，但这些并未转化为池化OOF BS改善。参数符号一致、样本内拟合更好和样本外增益必须分开陈述。本轮没有提供γ的正式置信区间或采用检验，不能使用“γ显著”之类表述。

M1与M2使用不同尺度的h和x，γ大小不能直接横向比较。M1部分负γ也不能解释为持续强风有保护作用；在当前相关预测器与受限函数形式下，它只是条件模型系数。

144目标中43个θ超出该训练G的观察范围：M0 12个、M1 12个、M2 19个，其中全样本分别2、2、4个。这不自动等于数值失败，但要求限制工程解释。特别是M1/M2的θ为持续项取0时的数学参考；若G>τ则H=0不可能，不能用这个不可实现组合解释高风速阈值。形式中点θexp(−βγfeature)对应概率(1+p₀)/2，而非一般总体50%故障概率；只可在有联合数据支持的条件下解释。

完整θ、β、p₀、γ及折内诊断见 {link('parameters.csv')}、{link('optimizer_candidates.csv.gz')}；有限近优解检查未标记弱识别，不等于所有参数已被精确或因果识别。

## 九、客观结论

1. **实现和数值层面已完成。** 原始范围与M0基线保持一致，三个模型全部144目标有效，没有已记录的技术失败可用来解释本轮评分差异。
2. **在预定主、次任务中，未显示持续性增量的明确样本外收益。** M1/M2的BS均略高于M0、差异极小、条件区间跨零，重点任务校准RMSE也未改善。M2虽在3/5折改善，仍不能据此忽略池化结果。
3. **池化Brier的正向增量仅见于M2的两个稀有任务。** 它们有很小的BS改善，天气 >1000五折同向，但条件区间仍跨零，且校准存在尾部单样本支持限制。这不足以推广为三个模型之间稳定且普遍的优劣关系。
4. **当前结果没有给出以稳定预测增益为由替换M0的明确证据。** 这是对本轮证据强度的总结，不替用户作主模型决定；也不证明三个模型严格等效、持续时间没有物理作用，或其他τ、模型形式及未来时间范围不会产生增益。

本报告不据结果反推累积损伤机制。新增项可能与峰值相关，也可能补偿函数形式近似；本轮设计没有分离这些解释。没有增加时间留出，LAD条件区间不覆盖共享风暴依赖及候选选择的全部不确定性。用户的具体采用决定和论文修改应另行明确记录；本报告未修改Word、Table7/Figure8或历史P03/DD-AGG01结论。

## 十、证据与报告产物

原实验文件保持只读：{link('inventory.json','原结果清单及指纹')}，{link('RESULTS_README.md','字段与实际复现命令')}。本次报告写入 `{HERE.as_posix()}`；`build_summary.py`仅读取已有机器表、整理表格与描述性箱支持，不拟合、请求天气或开展新的模型比较。

全部八任务、三个候选的BS、BSS、区间、折间方向和校准均已覆盖；未隐去负面或稀有任务的正面结果。报告按当前明确数值写作，没有借用用户未提供的审阅意见。源文件指纹匹配及报告链接/表格检查记录见 `summary_manifest.json`。
'''
    destination=HERE/'RESULTS_SUMMARY.md'
    with destination.open('x',encoding='utf-8') as f: f.write(text)
    metadata=dict(created_at=datetime.now().astimezone().isoformat(),source=str(SOURCE),source_inventory_sha256=digest(SOURCE/'inventory.json'),
                  source_hashes_match=True,summary_sha256=digest(destination),script_sha256=digest(Path(__file__)),
                  source_files=[dict(path=r['path'],sha256=r['sha256']) for r in inv['files']],
                  coverage=dict(models=3,tasks=8,metric_rows=len(m),fit_rows=len(fits),fold_metric_rows=len(folds)),
                  no_refit=True,no_weather_requests=True,no_manuscript_edits=True)
    (HERE/'summary_manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(destination)


if __name__=='__main__': main()
