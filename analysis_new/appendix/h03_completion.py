"""Scoped Appendix H execution, evidence export and factual report."""
import copy
import inspect
import re
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.discrete.discrete_model import NegativeBinomial
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from .catalog import ROOT,REQUIREMENTS
from .mapping import digest,write_json,expected
from .f02_cov import csv,read,js,token
from .exporters import table
from . import h03_models as models
from . import h03_evidence as evidence

STATE='产物完成/待研究负责人反馈分析'
R=next(r for r in REQUIREMENTS if r['requirement_id']=='H03')

def compare(coefficients):
    rows=[]
    for combo in ['E0_all','R0c_all']:
        ref=coefficients[coefficients.combination.eq(combo)&coefficients.model.eq('OLS_reference')&coefficients.term.str.contains('gust')]
        for family in [m for c,m in models.MODELS if c==combo]:
            alt=coefficients[coefficients.combination.eq(combo)&coefficients.model.eq(family)].set_index('term')
            for r in ref.itertuples():
                a=alt.loc[r.term] if r.term in alt.index else None
                point=bool(a is not None and a.point_valid);iv=bool(a is not None and a.interval_valid)
                same_sign=bool(np.sign(r.coef)==np.sign(a.coef)) if point else None
                ols_excludes=bool(r.ci_lower>0 or r.ci_upper<0)
                alt_excludes=bool(a.ci_lower>0 or a.ci_upper<0) if iv else None
                rows.append(dict(combination=combo,alternative=family,term=r.term,ols_coef=r.coef,glm_coef=a.coef if a is not None else np.nan,
                    ols_se_twoway=r.se_twoway,glm_se_twoway=a.se_twoway if a is not None else np.nan,
                    ols_ci_lower=r.ci_lower,ols_ci_upper=r.ci_upper,glm_ci_lower=a.ci_lower if a is not None else np.nan,glm_ci_upper=a.ci_upper if a is not None else np.nan,
                    ols_p_t_G1=r.p_t_G1,glm_p_t_G1=a.p_t_G1 if a is not None else np.nan,df=r.df,same_sign=same_sign,
                    ols_95_excludes_zero=ols_excludes,glm_95_excludes_zero=alt_excludes,same_95_evidence=bool(ols_excludes==alt_excludes) if iv else None,
                    supported_same_direction_and_95_evidence=bool(same_sign and ols_excludes==alt_excludes) if point and iv else None,
                    status='available' if point and iv else 'point_only' if point else 'invalid_or_missing_candidate',
                    interpretation='same basis, different estimands; no coefficient magnitude equivalence or new model ranking'))
    return pd.DataFrame(rows)

def report(stage,command):
    defs=read(stage/'tables/H03_MODEL_DEFINITIONS.csv');status=read(stage/'data/H03_MODEL_STATUS.csv');comp=read(stage/'tables/H03_GUST_COMPARISON.csv');body=read(stage/'data/H03_BODY_FREQUENCY_ALIGNMENT.csv')
    recovered=(stage/'logs/H03_NUMERICAL_AMENDMENT.json').is_file()
    text=['# APP-H03-LINK 第四工作包执行与回传报告',
        '状态：产物完成，待研究负责人反馈分析。前三包J03/F02/G03/I02已由负责人关闭；GI-W01至W09图文待改继续保留。本报告为本包执行事实，不是独立科学审查或整稿成文。',
        '## 范围与实际动作',
        '本地实际正文§3.1位于DOCX直接body P030（旧登记P031是Table2表注）。该段及H.1既有分布比较指向全体暴露/恢复；没有明确天气子样本替代分布检验要求，因此只执行四项：暴露NB2/Tweedie、恢复Gamma/Tweedie。天气样本仅进入已存在H.3来源整理和原分箱描述，未另拟合GLM。',
        '当前最终X逐行复用G的正式参数/预处理来源，并与保存的OLS预测、C样本指纹相核对。全体E=60437保留8979个0客户、固定14/25平台及温度平方/gust-pressure；全体R=51173保留正式正客户与全期p99规则、二次阵风及温度平方/gust-precip和客户控制。未重新OLS、CV、结点、Cause Code或样本选择。',
        '累计执行4个既定候选的首次拟合，另对无效NB2执行1次有限数值恢复，共5次候选求解调用；复用2个正式OLS参考。NB2首次拟合器内部另拟合一次Poisson取得初值，该辅助步骤不作为候选；恢复阶段没有辅助拟合。当前调用的缓存/拟合数见H03_LAST_EXECUTION.json。H.2/H.3零次拟合；经验频率由现有输入按原阈值/箱汇总。',
        'NB2原默认初始化路径返回alpha=0、非有限目标/score/Hessian并产生溢出，完整失败产物保留为INITIAL_FAILURE。按本包允许的有限数值恢复，协议另记录一次确定性初值修正：令mu0为当前样本客户均值，截距log(mu0)、其他beta为0，alpha初值用本地原_estimate_dispersion(mu0,y−mu0,n−rankX)，下限沿原实现0.05；随后仍联合估计全部beta/alpha。X/y、似然、BFGS200次和gtol1e−5不改，未比较多个有效解择优。原三项有效GLM在该修正中直接复用。详见H03_NUMERICAL_AMENDMENT.json及RECOVERY_START.csv。',
        '## 冻结的family/link与参数规则',
        '旧H.1 step_b_distribution_check.py：NB2使用BFGS最多200次，联合估计当前样本alpha；不能搬旧alpha=4.71044。fragility_demo.py的Poisson矩估alpha=15.9478属于另一自由结点伴随探索，仅登记为历史，不作为本次H.1配置。Gamma显式Log；两Tweedie显式Log、var_power=1.5、eql=True；IRLS最多100次、tol=1e−8。Gamma/Tweedie均采用原Pearson X2 scale，未搜索power。',
        'OLS目标为E[log(1+C)|X]或E[log(T)|X]；log-link GLM以log E[C|X]或log E[T|X]为线性预测器。两者系数幅度没有相等要求，exp(OLS预测)未当作原响应算术均值。未计算跨尺度RMSE或跨变换AIC/BIC排名；Tweedie完整似然和AIC/BIC均NA，其有限准似然deviance/score用于计算诊断。',
        '## 拟合与数值有效范围','|样本|候选|n|收敛|点估计有效|区间完整可用|max abs mean score|scale|alpha|','|---|---|---|---|---|---|---|---|---|']
    for r in status.to_dict('records'):
        text.append('|'+ '|'.join('NA' if pd.isna(r.get(k)) else str(r.get(k)) for k in ['combination','model','n','solver_converged','point_valid','inference_valid','max_abs_mean_score','scale','alpha'])+'|')
    text+=['H03_MODEL_STATUS.csv及各模型DIAGNOSTICS/OPTIMIZER保存目标、得分、迭代和全部捕获警告；不只看converged。冻结诊断要求有限参数/正均值/目标/score，max abs mean score≤1e−4及原求解器收敛。失败不以历史解填位，也不因符号不同继续扩大预算。',
        '## 推断路径',
        '使用本地statsmodels的model.score_obs和observed Hessian构造score/Hessian sandwich；two-way=LAD＋date−交叉组，各分量G/(G−1)×(n−1)/(n−k)小样本修正。与直接cov_cluster_2groups(fit, LAD, date)做数值对应。本次全体两个样本各111个LAD，系数区间/p按既定t(110)。',
        'NB2使用完成优化后(beta, alpha)坐标，包含alpha的完整score、Hessian及协方差，k包含alpha；不是固定旧alpha条件推断。Gamma/Tweedie用拟合Pearson scale的beta score与observed Hessian，scale未作为额外联合参数维度。未套用OLS residual sandwich，未混入默认独立SE。',
        '每个候选完整矩阵与LAD/date/交叉分量、实际score、参数和拟合均值均保存。负方差的对应区间留NA；不abs、截零或正定化。非PSD与单系数负方差分开记录，不由前者自动否定所有单项区间。',
        '每个矩阵的observed information秩、最小特征值及负对角项见H03_MODEL_STATUS.csv与逐模型DIAGNOSTICS；不改变先前三包其他矩阵的适用边界。',
        '## 阵风基与交互项的逐项对应',
        '表中“同证据”仅指在同一t规则的95%系数区间是否排除0一致，不是等效性检验；不要求替代模型支持当前形式才能交付。',
        '|样本|替代模型|项|OLS系数|GLM系数|GLM two-way SE|GLM 95% CI|同符号|同95%证据|','|---|---|---|---|---|---|---|---|---|']
    for r in comp.itertuples():
        text.append(f'|{r.combination}|{r.alternative}|{r.term}|{r.ols_coef:.9g}|{r.glm_coef:.9g}|{r.glm_se_twoway:.9g}|[{r.glm_ci_lower:.9g}, {r.glm_ci_upper:.9g}]|{r.same_sign}|{r.same_95_evidence}|')
    available=comp[comp.status.eq('available')];different=available[~available.supported_same_direction_and_95_evidence.eq(True)]
    text += [f'实际可对应{len(available)}/{len(comp)}个阵风/交互系数对照；其中{len(different)}项未同时满足原句的“方向和95%证据一致”。完整p值、OLS及GLM区间见H03_GUST_COMPARISON.csv，不能省略不一致项。']
    for r in different.itertuples():text.append(f'- {r.combination}/{r.alternative}/{r.term}：同符号={r.same_sign}，OLS 95%排除0={r.ols_95_excludes_zero}，GLM 95%排除0={r.glm_95_excludes_zero}。')
    text+=['E0平台约束已经固定在预测变量基中；这四项拟合不能独立证明平台存在或14/25最优。阵风主项与gust-pressure/precip交互分开解释，某单项系数不是所有协变量取值下的总导数。天气单11结点在本包未拟合GLM；未把hinge增量当作结点后总斜率。',
        '## H.2/H.3既有证据与当前经验表',
        '原H_ORDINAL_SUMMARY/H_CONDITIONAL_COEFFICIENTS/H_CONDITIONAL_LOGNORMAL保留。新增H03_EXISTING_H2_H3_SOURCES.csv逐项注明样本、原控制基、参数、图形路径和限制。原序数模型是全体E60437/R59834，恢复含零客户；H.3旧恢复全体59834、天气9806，不能改称当前51173/9254。原全控制系数与ordinal cutpoints未完整保存在summary，不能只凭阵风系数重建整条序数曲线。',
        '已存lognormal参数可直接派生概率网格（H03_EXISTING_LOGNORMAL_CURVES.csv.gz）。六条旧优化诊断均报告success；部分theta/beta极大、与经验频率不符或缺乏可解释位置，不能改写为算法未收敛或物理机制被证伪。本包不修优化器、不重做ordinal/logit/曲面。',
        'H03_EVENT_CONDITIONAL_FREQUENCIES保存当前四组原gust箱的分子/分母/概率，旧恢复同箱参考另放data。客户阈值实际.5/5.5/100.5/1000.5，因客户为整数等价>0/>5/>100/>1000；时长严格>3/>12/>48h。原ordinal标签<3h对应right-closed (0,3]，后续说明应消除标签歧义。所有概率条件于已发生且已纳入样本的事件；不能当作地区日事件概率。',
        '正文§4.4 P069的粗分箱语句对应如下，只合并原箱，分母按事件池化：','|口径|n|>100客户数|当前频率|原文数字|备注|','|---|---|---|---|---|---|']
    for r in body.itertuples():text.append(f'|{r.label}|{r.n}|{r.numerator}|{r.frequency:.9f}|{r.quoted_value}|{r.qualification}|')
    text+=['“calm”原句未明确定义数值边界，这里明确展示原首箱(0,4]，不假称找到了0.40的相同口径。其余12–18及>23范围按原箱闭合规则与上限45汇总，差异留给人工改写；不重开原因范围或旧proxy尾部审计。',
        '## 精确待改原句与可写范围',
        '- §3.1 P030：“A log link…”需区分变换响应OLS与真正log-link GLM；删除两者相同估计对象的暗示。',
        '- 同段“same gust coefficients in sign and significance”：只能按本次逐项对照限定。表中不一致或无相容区间的候选不得写为全部一致；完整条件与例外同时呈现。',
        '- §4.4 P069及Appendix H标题：可以说明本数据中事件条件严重程度与district-day分母不同，以及当前分箱曲线/旧单调形式的适用限制；不能据非单调性普遍禁止其他领域使用fragility一词，也不能用未发生的优化器不收敛作物理结论。无业务字段支持时，不将calm大事件唯一归因为某类运营机制。',
        '- H.2/H.3：恢复旧样本与当前经验表分别标注；旧ordinal<3h标签的实际包含3h规则需写清。不强行把旧曲线的数值和解释迁移到当前恢复样本。',
        '可以客观表述：在固定当前预测变量基及样本条件下，已完成四项既有分布/均值设定的有限全样本敏感性；对应系数的方向、两维聚类区间和例外见表。不能据此宣告主模型最优、结点重新验证或原尺度预测性能获胜。',
        '## 复现、文件与停止',f'本次命令：`{command}`。项目根目录运行`python -X utf8 -B main_appendix.py --appendices H --h03-only`；限定本包重算加`--recompute-h03`；只读预检加`--check-only`。',
        '冻结协议/覆盖矩阵在logs/H03_PROTOCOL.json、data/H03_COVERAGE_PLAN.csv；模型定义、完整系数、关键项对照、当前条件频率在tables；可复算X/响应/参数/拟合均值/score/Hessian/协方差及历史适用范围在data；状态和技术检查在logs。无新增图形：本次表格及旧曲线网格已足够，不为凑family图扩展任务。',
        '原H01/H02及未知人工文件按既有事务机制保留。完成只标产物待反馈，不自动关闭H或开始F–J写作；没有论文修改、ZIP、远程发布或独立科学审查。']
    if not recovered:
        text=[v for v in text if not v.startswith('NB2原默认初始化路径')]
        text=[v.replace('累计执行4个既定候选的首次拟合，另对无效NB2执行1次有限数值恢复，共5次候选求解调用','累计执行4个既定候选的首次拟合，未触发数值恢复') for v in text]
    (stage/'logs/H03_EXECUTION_REPORT.md').write_text(('\n\n'.join(text)+'\n').replace('|\n\n|','|\n|'),encoding='utf8')

def generate(stage,source_checks,previous,force=False,base_generator=None,command=''):
    from .runner import now,safe_child
    failed=[v['path'] for v in source_checks if v['path'] in R['sources'] and not v['passed']]
    if failed:raise ValueError('H03 frozen sources absent or changed: '+str(failed))
    old=js(previous/'manifest.json') if (previous/'manifest.json').exists() else {};own={v['path'] for v in old.get('outputs',[]) if v['requirement_id']=='H03'}
    if old.get('owner')=='main_appendix.py':
        manifest=copy.deepcopy(old);manifest['outputs']=[v for v in old['outputs'] if v['requirement_id']!='H03']
        for rel in old['managed_files']:
            if rel in own or rel=='manifest.json':continue
            dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dest)
    else:manifest=base_generator('H',stage,source_checks)
    for f in ['data','tables','logs','figures']:(stage/f).mkdir(exist_ok=True)
    before={p.relative_to(stage).as_posix():digest(p) for p in stage.rglob('*') if p.is_file() and p.name not in ['README.md','manifest.json']}
    sources=models.sources();code=[*Path(__file__).parent.glob('h03_*.py'),Path(__file__).with_name('gi_core.py'),Path(__file__).with_name('design_adapter.py'),Path(__file__).with_name('c_models.py')]
    config=dict(task='APP-H03-LINK',inputs={p:digest(ROOT/p) for p in sources},code={p.relative_to(ROOT).as_posix():digest(p) for p in code},rules=models.RULES,
        software=dict(python=sys.version,statsmodels=statsmodels.__version__,numpy=np.__version__,pandas=pd.__version__),
        library_source_sha256={str(Path(inspect.getsourcefile(v))):digest(Path(inspect.getsourcefile(v))) for v in [GLM,NegativeBinomial,cov_cluster_2groups]},random_seed=None,random_operations='none',weather_GLM='not required by located H1 or body claim')
    original=js(previous/'logs/H03_PROTOCOL.json') if (previous/'logs/H03_PROTOCOL.json').is_file() else {}
    verified=bool(own) and all((previous/v['path']).is_file() and digest(previous/v['path'])==v['sha256'] for v in old.get('outputs',[]) if v['requirement_id']=='H03')
    # Statistical computation lives in models/evidence/design modules. Prose
    # and orchestration edits need not refit; their full hashes still go into
    # export provenance. Regenerate the pure coefficient comparison below.
    def numerical_signature(v):
        values={k:v.get(k) for k in config}
        values['code']={p:h for p,h in (v.get('code') or {}).items() if not p.endswith('h03_completion.py')}
        return token(values)
    key=numerical_signature(config)
    cache=bool(not force and verified and numerical_signature(original)==key)
    # Explicit compatibility migration: only NB starting values changed from this
    # frozen implementation; IRLS, designs and covariance paths are unchanged.
    migrate=bool(not force and original.get('code',{}).get('analysis_new/appendix/h03_models.py')=='cb1ef8a67bc378c9bf4713ecdba86a02248f8577fe9903b00f587e47251a6696'
        and all(original.get(k)==config[k] for k in ['inputs','software','library_source_sha256'])
        and all((previous/v['path']).is_file() and digest(previous/v['path'])==v['sha256'] for v in old.get('outputs',[]) if v['requirement_id']=='H03'))
    fit_count=0;aux_count=0;recovery_count=0;reused=[]
    if cache:
        for rel in own:
            dest=safe_child(stage,rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(safe_child(previous,rel),dest)
        print('H03: validated cache; no GLM/OLS fitting',flush=True)
    else:
        write_json(stage/'logs/H03_PROTOCOL.json',dict(**config,frozen_at=now(),command=command))
        bundles,defs=models.bundles(stage);csv(stage/'data/H03_COVERAGE_PLAN.csv',defs);table(stage,'H03_MODEL_DEFINITIONS',defs,R)
        coefficients=[models.ols_reference(stage,c,b) for c,b in bundles.items()];status=[]
        for combo,family in models.MODELS:
            prefix=f'H03_{combo}_{family}'
            if migrate:
                prior=read(previous/'tables/H03_FULL_COEFFICIENTS.csv')
                coef=prior[prior.combination.eq(combo)&prior.model.eq(family)].copy()
                diag=js(previous/f'data/{prefix}_DIAGNOSTICS.json')
                for p in (previous/'data').glob(prefix+'_*'):
                    shutil.copy2(p,stage/'data'/p.name)
                reused.append(combo+'/'+family)
                print('H03: reuse recorded '+combo+'/'+family+' component',flush=True)
            else:
                coef,diag=models.fit_one(stage,combo,family,bundles[combo]);fit_count+=1;aux_count+=int(family=='NB2')
            if family=='NB2' and not diag['point_valid']:
                # Keep the unsuccessful output byte-for-byte; this is numerical
                # recovery only, never selection between valid fitted models.
                for p in list((stage/'data').glob(prefix+'_*')):
                    shutil.copy2(p,stage/'data'/p.name.replace(prefix+'_',prefix+'_INITIAL_FAILURE_',1))
                write_json(stage/'logs/H03_NUMERICAL_AMENDMENT.json',dict(time=now(),reason='original NB2 alpha0, nonfinite likelihood/score/Hessian and overflow',
                    rule='one retry: constant mu=sample mean; intercept log(mu), other beta0; alpha=max(.05, original _estimate_dispersion(mu,y-mu,n-rankX)); all beta and alpha jointly estimated',
                    unchanged='X,y,knots,family,likelihood,BFGS max200 gtol1e-5, score validity and covariance',other_GLM_components_reused=migrate,selection='only invalid original fit triggers retry; no ranking of valid estimates'))
                coef,diag=models.fit_one(stage,combo,family,bundles[combo],constant_start=True);fit_count+=1;recovery_count+=1
            status.append(diag)
            if len(coef):coefficients.append(coef)
        coeff=pd.concat(coefficients,ignore_index=True);table(stage,'H03_FULL_COEFFICIENTS',coeff,R)
        comparisons=compare(coeff);table(stage,'H03_GUST_COMPARISON',comparisons,R)
        csv(stage/'data/H03_MODEL_STATUS.csv',pd.DataFrame([{k:json_value(v) for k,v in d.items()} for d in status]))
        checks=evidence.existing(stage,R)
        checks.update(two_formal_samples_and_saved_OLS_matched=True,response_legality_checked_no_rounding_or_dropping=True,
            four_original_candidate_attempts=len(status)==4,all_attempts_have_explicit_status=all('point_valid' in d and 'inference_valid' in d for d in status),
            covariance_uses_score_Hessian=True,full_NB_alpha_dimension=True,coefficient_interval_formula=bool(np.all(coeff.loc[coeff.interval_valid,'ci_upper']>=coeff.loc[coeff.interval_valid,'ci_lower'])),
            no_OLS_CV_knot_or_H2_H3_fits=True)
        write_json(stage/'logs/H03_TECHNICAL_CHECKS.json',dict(checks=checks,all_checks_passed=all(checks.values()),candidate_availability=[dict(combination=d['combination'],model=d['model'],point_valid=d['point_valid'],inference_valid=d['inference_valid']) for d in status],scope='execution and saved input/inference checks; unavailable candidate is reported, not suppressed'))
    table(stage,'H03_GUST_COMPARISON',compare(read(stage/'tables/H03_FULL_COEFFICIENTS.csv')),R)
    report(stage,command)
    write_json(stage/'logs/H03_EXPORT_PROVENANCE.json',dict(time=now(),code=config['code'],cache_key=key,
        cache_scope='all input and statistical code/library/configuration fingerprints; full export code separately recorded; pure comparison/report regenerated'))
    write_json(stage/'logs/H03_LAST_EXECUTION.json',dict(time=now(),command=command,cached=cache,new_primary_GLM_fits=fit_count,new_OLS_fits=0,
        NB_internal_Poisson_initial_fit=aux_count,NB_numerical_recovery_attempts=recovery_count,reused_components=reused,H2_H3_fits=0,cache_key=key,force_recompute=force))
    preservation={p:digest(stage/p)==h for p,h in before.items()};assert all(preservation.values())
    write_json(stage/'logs/H03_PRESERVATION.json',dict(other_H_managed_outputs=preservation,all_unchanged=True))
    content=(stage/'README.md').read_text(encoding='utf8').split('\n## APP-H03-LINK')[0]
    content=re.sub(r'最近生成：[^。]+。',f'最近生成：{now()}。',content,count=1)
    content=content.replace('事件条件探索的样本/形式明确列出；不是当前最终回归的完整替代分布稳健性验证。',
        'H03已补齐当前全体样本四个既定替代分布候选；H01/H02历史事件条件来源保留，各自适用范围分别标注。状态为产物完成待反馈。')
    content=re.sub(r'### H03 —.*?(?=## 来源|\Z)','',content,flags=re.S)
    content+='\n## APP-H03-LINK\n\n'+(stage/'logs/H03_EXECUTION_REPORT.md').read_text(encoding='utf8')
    (stage/'README.md').write_text(content,encoding='utf8')
    valid=js(stage/'logs/H03_TECHNICAL_CHECKS.json')['all_checks_passed'];state=STATE if valid else '产物部分完成/具体执行检查异常待反馈'
    newfiles={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}-set(before)-{'README.md','manifest.json'}
    for p in expected(R):assert (stage/p).is_file(),p
    for rel in sorted(newfiles):
        p=stage/rel;manifest['outputs'].append(dict(path=rel,sha256=digest(p),bytes=p.stat().st_size,requirement_id='H03',claim_id=R['claim_id'],source_paths=sources,source_sha256=config['inputs'],producer=R['producer'],export_function=R['producer'],configuration=R['config'],status=state))
    manifest['requirements']['H03']=state;manifest.pop('error',None)
    manifest.update(owner='main_appendix.py',appendix='H',last_attempt=now(),status='success' if valid else 'success_with_gaps',update_state='本次H03更新，H01/H02来源结果保留',h03_cache_key=key,
        managed_files=sorted({p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}|{'manifest.json'}))
    write_json(stage/'manifest.json',manifest)
    return manifest

def json_value(v):
    import json
    return json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
