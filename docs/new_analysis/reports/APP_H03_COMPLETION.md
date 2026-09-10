# APP-H03-LINK 第四包完成回执

日期：2026-09-10（Europe/London；逐次执行时间见LOG.md、H03_PROTOCOL、H03_NUMERICAL_AMENDMENT及H03_LAST_EXECUTION）。状态：**产物完成，待研究负责人反馈分析**。本文件为事实回执，不替代独立科学审查。

## 已完成范围

- 全体暴露60437条，保留8979条零客户：正式固定14/25平台及原完整控制，NB2和Tweedie-log。
- 全体恢复51173条：正式正客户和既定p99清洗，二次阵风及原完整控制，Gamma-log和Tweedie-log。
- 两个正式OLS参考直接复用G/C/原final相容来源，没有重新OLS。天气GLM未纳入：实际H.1与正文该段未明确要求；天气样本仍列入既有条件概率证据的描述整理。
- 四个候选各首次求解一次；NB2原默认初始化发生alpha=0、溢出及非有限目标/score/Hessian，额外执行一次限定初值恢复后收敛。共五次候选求解调用；原NB内部另有一次Poisson初值拟合，不算候选。原失败参数/警告完整保留。恢复时另三项模型直接复用。
- 当前四候选均取得有效点估计和LAD/date两维聚类区间。NB2联合alpha=4.703206959218843；得分检查最大绝对均值约6.71545e−6。Gamma/Tweedie均使用原Pearson scale，Tweedie固定power1.5，不报告完整似然AIC/BIC。
- H.2/H.3不拟合：保留原序数/阈值logit/lognormal结果，整理样本和控制项来源；由已存lognormal参数导出曲线网格，并按原阈值/原gust箱保存当前四样本事件条件频率及旧恢复参考。

## 主要事实与待反馈事项

全部12个阵风基/交互系数对应均具备相容推断。10项同时保持符号和95%区间是否排除0的一致性；两个例外为恢复Gamma、Tweedie的线性阵风项：OLS系数略负，替代模型为正，但三者的该项区间均包含0。不能将正文改写为所有阵风系数方向均一致。完整数字见关键项对照表；这不是系数等效性或主模型优劣检验。

正文事件条件频率原句与当前底表有差异：全体暴露(12,18] m/s的>100客户频率为1680/11894=0.141247688；(23,45]为652/1601=0.407245472。原“calm”无明确边界，原首箱(0,4]为808/5544=0.145743146，仅作明确口径展示，不声称与原0.40同口径。原文数字、分子分母、闭合规则和具体句子位置均见执行报告及H03_BODY_FREQUENCY_ALIGNMENT.csv。

后续人工处理：限定§3.1“相同方向和显著性”；区分变换响应OLS与真正log-link GLM；按对应底表调整§4.4具体频率及事件条件表述；旧恢复59834/9806结果不能改称当前51173/9254。未直接修改任何论文或A–E英文稿。H03不独立验证固定在输入基中的平台或结点位置。

## 结果与证据路径

权威结果目录：[results/Appendix/H](../../../results/Appendix/H/README.md)。固定目录及稳定文件名，没有时间戳目录。

|用途|位置（相对H目录）|
|---|---|
|逐项事实回传报告|[logs/H03_EXECUTION_REPORT.md](../../../results/Appendix/H/logs/H03_EXECUTION_REPORT.md)|
|模型、响应和样本定义|tables/H03_MODEL_DEFINITIONS.csv / .md|
|完整系数与two-way SE/区间/p|tables/H03_FULL_COEFFICIENTS.csv / .md|
|12个阵风基/交互项对照|tables/H03_GUST_COMPARISON.csv / .md|
|当前样本原分箱频率|tables/H03_EVENT_CONDITIONAL_FREQUENCIES.csv / .md|
|现有H.2/H.3样本/规格/限制|data/H03_EXISTING_H2_H3_SOURCES.csv；H03_EXISTING_LIMITATIONS.json|
|已存参数派生网格|data/H03_EXISTING_LOGNORMAL_CURVES.csv.gz|
|正文粗分箱对应|data/H03_BODY_FREQUENCY_ALIGNMENT.csv|
|实际ID、完整X、响应、预处理|data/H03_*_ROWS.csv.gz、DESIGN.csv.gz、SPECIFICATION.json|
|参数、原尺度拟合均值、逐行score、完整Hessian与协方差分量|data/H03_*_PARAMETERS.csv、FITTED.csv.gz、SCORES.csv.gz、OBSERVED_INFORMATION.csv、COV_*.csv|
|NB原失败、恢复初值及规则|data/H03_E0_all_NB2_INITIAL_FAILURE_*；RECOVERY_START.csv；logs/H03_NUMERICAL_AMENDMENT.json|
|协议、数值有效状态、导出/缓存记录|logs/H03_PROTOCOL.json、H03_TECHNICAL_CHECKS.json、H03_EXPORT_PROVENANCE.json、H03_LAST_EXECUTION.json；data/H03_MODEL_STATUS.csv|

CSV保留完整精度；现有figure_table_register.csv统一登记主表编号。过程清单在data/logs，不全部作为论文排版表。无新增图形要求，未复制图库或生成ZIP。

## 入口与必要检查

项目根目录：

```powershell
python -X utf8 -B main_appendix.py --appendices H --h03-only
```

只读来源预检加`--check-only`；明确限定本包重算加`--recompute-h03`。实际解释器为`C:/Users/haoya/.conda/envs/pyoutagegust/python.exe`。代码分为analysis_new/appendix/h03_models.py、h03_evidence.py、h03_completion.py，通过原runner/catalog/mapping接入；没有第二套实验入口。

- [verify_h03_saved.py](verify_h03_saved.py)：85项保存产物必要复算全部通过。只在保存参数处重建均值、score/Hessian和聚类分量，核对SE/CI/p及样本/列序；不调用fit。记录：[APP_H03_SAVED_VERIFICATION.json](APP_H03_SAVED_VERIFICATION.json)。
- [verify_h03_cache.py](verify_h03_cache.py)：经正式入口的9项缓存/发布检查全部通过；零新增拟合，72份H数组及诊断文件保持不变，884份其他附录文件保持原指纹，H01/H02保留。记录：[APP_H03_CACHE_VERIFICATION.json](APP_H03_CACHE_VERIFICATION.json)。
- 运行30项来源预检无失败；manifest及根需求/产物/图表登记、H03缺口状态已更新。此前已关闭J03/F02/G03/I02，GI-W01至W09仍留既有推进台账。

未重新训练其他模型，没有CV、bootstrap、结点搜索、天气请求、前三包重跑、论文修改、远程提交或独立科学审查。已停在产物和事实回执，H03最终关闭由研究负责人反馈后决定。
