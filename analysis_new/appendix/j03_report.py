"""Figures and factual execution feedback for APP-J03-COMPARE."""
from datetime import datetime
import numpy as np
import pandas as pd

from scripts.final_combined_analysis.figure_style import apply_style
from analysis_new.grid_fragility_validation import TARGETS


def figures(stage,paired,bins):
    import matplotlib
    matplotlib.use('Agg')  # File production must not depend on a desktop Tcl/Tk installation.
    import matplotlib.pyplot as plt
    apply_style()
    colors={'PROXY':'#2166ac','GRID_MAX':'#b35806'}
    fig=plt.figure(figsize=(14,14))
    outer=fig.add_gridspec(2,2,hspace=.30,wspace=.24)
    for i,t in enumerate(['any_gt100','wthr_gt100']):
        subset=bins[(bins.target==t)&(bins.n>=100)]
        lim=min(1.,max(.02,float(subset[['mean_probability','observed_frequency']].max().max())*1.25)) if len(subset) else 1.
        for j,v in enumerate(['PROXY','GRID_MAX']):
            inner=outer[i,j].subgridspec(2,1,height_ratios=[3.6,2.3],hspace=.30)
            ax=fig.add_subplot(inner[0]);ta=fig.add_subplot(inner[1]);ta.axis('off')
            b=bins[(bins.target==t)&(bins.candidate==v)]
            inset=ax.inset_axes([.07,.57,.33,.36])
            inset.plot([0,1],[0,1],ls='--',color='.6',lw=.7)
            inset.set(xlim=(0,1.03),ylim=(0,1.03),xticks=[0,.5,1],yticks=[0,.5,1],title='Full range: all bins')
            inset.tick_params(labelsize=6);inset.title.set_fontsize(7)
            ax.plot([0,lim],[0,lim],ls='--',color='.45',lw=1)
            for row in b[b.n>0].itertuples():
                ax.scatter(row.mean_probability,row.observed_frequency,color=colors[v],marker='x' if row.sparse else 'o',s=27)
                inset.scatter(row.mean_probability,row.observed_frequency,color=colors[v],marker='x' if row.sparse else 'o',s=12)
            ax.set(xlim=(0,lim),ylim=(0,lim),xlabel='Mean OOF probability',ylabel='Observed frequency',title=f'{t}: {v}')
            ax.grid(alpha=.15)
            if b.empty:ax.text(.5,.5,'No valid OOF predictions',transform=ax.transAxes,ha='center')
            cells=[[str(r.bin),f'{r.n:,}',f'{r.events:,}',f'{r.mean_probability:.5f}' if r.n else 'NA',
                    f'{r.observed_frequency:.5f}' if r.n else 'NA','sparse' if 0<r.n<100 else 'empty' if not r.n else ''] for r in b.itertuples()]
            if cells:
                tab=ta.table(cellText=cells,colLabels=['Bin','n','Positives','Mean p','Observed',''],loc='center',cellLoc='right',bbox=[0,0,1,1])
                tab.auto_set_font_size(False);tab.set_fontsize(7)
                for (rr,cc),cell in tab.get_celld().items():
                    cell.set_edgecolor('#dddddd');cell.set_linewidth(.35)
                    if rr==0:cell.set_facecolor('#eeeeee')
    fig.suptitle('Shared bins; same main limits within each task; crosses: n < 100\nMain view covers non-sparse bins; inset and tables retain every nonempty bin; empty bins shown as NA',fontsize=11,y=.98)
    fig.subplots_adjust(top=.93,bottom=.035,left=.07,right=.97)
    fig.savefig(stage/'figures/J03_PRIMARY_CALIBRATION.png',dpi=300);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6),sharey=True)
    p=paired.set_index('target').reindex(TARGETS);y=np.arange(len(TARGETS))
    axes[0].scatter(p.proxy_brier,y-.10,label='PROXY',color=colors['PROXY'])
    axes[0].scatter(p.grid_brier,y+.10,label='GRID_MAX',color=colors['GRID_MAX'])
    axes[0].set_xscale('log');axes[0].set_xlabel('Pooled OOF Brier (log axis; lower is better)');axes[0].legend()
    axes[1].axvline(0,color='.45',ls='--')
    for k,row in enumerate(p.itertuples()):
        if row.valid_comparison:
            axes[1].plot([row.delta_brier_lo,row.delta_brier_hi],[k,k],color='black')
            axes[1].scatter(row.delta_brier,k,color='black',s=25)
    axes[1].set_xlabel('Brier PROXY − GRID_MAX (positive favours GRID_MAX)')
    axes[1].set_title('Paired 95% conditional intervals; fixed OOF, whole LAD')
    axes[0].set_yticks(y,TARGETS);axes[0].invert_yaxis()
    for ax in axes:ax.grid(axis='x',alpha=.15)
    fig.tight_layout();fig.savefig(stage/'figures/J03_BRIER_COMPARISON.png',dpi=300);plt.close(fig)


def report(stage,paired,components,history):
    import json
    protocol=json.loads((stage/'logs/J03_PROTOCOL.json').read_text(encoding='utf8'))
    counts=components.action.value_counts().to_dict()
    valid=int(components.valid.sum());weak=int(components.weak_identification.sum())
    text=['# APP-J03-COMPARE 第一工作包执行与回传报告',
        '完成记录：'+datetime.now().astimezone().isoformat(timespec='seconds')+'。状态：产物已输出，待研究负责人反馈分析；未科学关闭。',
        '## 任务与实际执行',
        '本包只比较正文同日事件锚点PROXY与既下载ERA5小时阵风的日最大GRID_MAX。二者是天气暴露构造方案的整体对照；不把任何一方称为真值，不分解位置/聚合/获取方式的独立作用。',
        '两来源按同一LAD-day键逐一对应：111 LAD、1096 UTC日、121656行、八标签，五折直接复用DD-AGG01保存分配。没有静默取交集、填零、换标签、换时区或请求天气。gt0为任意事件并保留零客户，其他阈值严格>，不是当天客户求和。',
        f'目标96组件全部有记录：16全样本、80训练折。该结果集来源动作：{counts}；有效{valid}/96，弱识别标记{weak}。GRID_MAX复用前核对RULES、训练行数/阳性数、稳定目标函数、梯度及已评价初值/终点最小值；不是仅检查success。',
        '全样本参数仅用于附录描述；OOF概率逐折由对应训练参数生成，常数概率是该训练折发生率。未使用全样本参数生成OOF。当前每次调用是否命中缓存和新拟合次数另记logs/J03_LAST_EXECUTION.json；复用导出不重新计算科学结果。',
        '## 评价口径',
        'Brier按地区日等权池化。ΔBS=BS_PROXY−BS_GRID_MAX，正值表示GRID_MAX误差更低；相对改善=100×ΔBS/BS_PROXY，单位是相对百分比，不是概率百分点。BSS相对于两方案共同的训练折常数预测。',
        '配对区间重新使用当前OOF：整LAD有放回抽样1000次、seed=20260909，两来源和八任务共享抽样，按每次抽中地区日数量池化。它是固定OOF的条件区间，不包含重训、选择和跨LAD共享风暴日期的全部不确定性；没有拼接旧P03区间。',
        '共同校准规则在拟合前冻结：每任务两来源有效OOF概率合并取0–1十分位数，补0/1并去重；规则不读标签决定箱边界，side=right。每箱保存n和阳性，空箱频率为NA，n<100标为稀疏；没有事后调箱。',
        '## 八任务完整结果',
        '|任务|PROXY Brier|GRID_MAX Brier|ΔBS|相对改善 %|配对ΔBS 95%条件区间|PROXY BSS|GRID_MAX BSS|',
        '|---|---|---|---|---|---|---|---|']
    for r in paired.itertuples():
        text.append(f'|{r.target}|{r.proxy_brier:.10f}|{r.grid_brier:.10f}|{r.delta_brier:.10f}|{r.relative_improvement_pct:.6f}|[{r.delta_brier_lo:.10f}, {r.delta_brier_hi:.10f}]|{r.proxy_bss:.8f}|{r.grid_bss:.8f}|')
    text+=['主要任务为any_gt100，重要次级为wthr_gt100。其余六项全部列出；表格记录差异方向和幅度，不设置通过/失败或主模型更换门槛。总体发生率、平均预测及偏差见J03_PAIRED_METRICS；逐折n/阳性/常数/差异见J03_FOLD_METRICS。',
           '## 与正文已存PROXY结果的直接对照',
           '仅对照本轮同一全样本的新参数与正文已存lognormal参数，并比较二者在同批输入上的描述性概率；不重新拟合旧模型、不审计旧支持上限/g50。下表中变化供研究负责人判断对原参数和文字的影响，未自动改写正文。',
           '|任务|旧θ→新θ|旧β→新β|旧p0→新p0|新NLL−旧NLL|最大绝对概率差|',
           '|---|---|---|---|---|---|']
    for r in history.itertuples():
        text.append(f'|{r.target}|{r.historical_theta:.8g} → {r.stable_theta:.8g}|{r.historical_beta:.8g} → {r.stable_beta:.8g}|{r.historical_p0:.8g} → {r.stable_p0:.8g}|{r.difference_nll:.8g}|{r.max_abs_probability_difference:.8g}|')
    text+=['## 必要技术检查与异常',
           'logs/J03_TECHNICAL_CHECKS.json保存匹配、训练/测试边界、合法概率、有效拟合诊断、逐行评分复算、同抽样区间复算及分箱计数检查；logs/J03_PRESERVATION.json记录其他J管理文件的逐文件保留。有效性与弱识别分别保存，不把运行完成解释为科学结论成立。',
           '无效组件：'+('无。' if valid==96 else '请按J03_COMPONENT_MANIFEST.valid=false定位；对应无效OOF保留缺失，不用于完整比较。'),
           '此前发布尝试错误：'+(protocol.get('previous_attempt_error') or '本次协议未记录前次错误。')+'。此前失败未发布的拟合不计入上表当前结果集的组件动作；跨尝试执行事实见项目LOG.md。',
           '## 复现、文件与回传用途',
           '项目根目录执行：`python -X utf8 -B main_appendix.py --appendices J --j03-only`。普通运行核验有效缓存；强制本包重算：增加`--recompute-j03`，仍使用同一96组件和冻结预算。只读预检：增加`--check-only`。',
           '固定目录：results/Appendix/J/。tables/J03_*为完整精度CSV和阅读版；data/J03_MATCHED_PANEL.csv.gz、J03_FIT_COMPONENTS.jsonl、J03_OOF_PREDICTIONS.csv.gz、J03_BOOTSTRAP_DRAWS.csv.gz及LAD顺序保存底层结果。figures/J03_PRIMARY_CALIBRATION.png为两个重点任务校准图，J03_BRIER_COMPARISON.png为八任务评分/配对区间图。',
           'logs/J03_PROTOCOL.json为冻结协议和来源/代码指纹；J03_INPUT_MATCH.json为匹配记录；J03_LAST_EXECUTION.json区分实际本次新拟合与缓存；本报告可直接用于人工回传，不生成ZIP或回传包。',
           '## 停止与人工事项',
           '第一包执行到结果交付为止。研究负责人随后组织反馈分析，讨论差异方向、量级、条件区间、校准及新PROXY参数对正文的具体影响，再决定是否关闭J03。这里不代写独立科学审核报告，不更换主模型，也不自动进入F02、G/I或H03。']
    # Preserve adjacent Markdown table rows; all other items are paragraphs.
    rendered=('\n\n'.join(text)+'\n').replace('|\n\n|','|\n|')
    (stage/'logs/J03_EXECUTION_REPORT.md').write_text(rendered,encoding='utf8')
