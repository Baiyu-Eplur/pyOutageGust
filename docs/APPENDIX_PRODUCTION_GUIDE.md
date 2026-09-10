# A–J 附录生产接口

2026-09-10。范围：Extended 正文和已接受 v9 附录分工的证据映射与产物整理。APP-C-COMPLETE另行授权C补齐最终样本既定候选及原CV；其余附录不重训，不改论文，不撰写整套附录。

## Appendix C 补齐与复现

`python main_appendix.py --appendices C`独立执行C。四组使用正文正式输入与最终正客户恢复过滤；原12阶梯及Table 3自由结点、统一最终控制项下的既定阵风函数分表。默认复用已通过样本、规格、尺度及CV核对的历史组件，并验证C的新计算缓存；缺失组件才拟合。首次运行实际完成补算，后续输入/算法未变时从缓存重导出表图。

`python main_appendix.py --appendices C --recompute-c`忽略C的新计算缓存，重新计算缺失组件。兼容的原研究产物始终只读复用，不借此重做D的bootstrap/profile。`--check-only`仍不写入。

固定产物：`results/Appendix/C/`。`logs/protocol.json`与`logs/coverage_before.csv`在首个拟合前冻结；`data/models/<组合>/<model_id>/`保存组件结果、可用预测、折级指标、训练预处理与参数；`data/samples/`保存观测ID、标签与原折号。缓存绑定样本与来源指纹、候选、折分配、数值函数及公共源码、软件版本，文件本身另核验SHA256；纯表图文字变化不会无谓重拟合。原兼容CV如果只存汇总分数，明确标注没有新增逐行预测，不用同名文件冒充可复用。

`C_HISTORICAL_LADDER`中原12项分别保留random/LAD/year的池化RMSE；随机CV仅使用原cv_fold_v3非缺失行，不能视作全研究期的等样本评分。`C_GUST_FUNCTION_COMPARISON`是四组最终控制项下的函数比较，结点仅由各训练折选择。`C_EXISTING_FIXED_AND_D_REFERENCES`区分原固定全样本结点CV及D控制条件。C完成状态、结果差异与具体边界见其README和logs/APP_C_COMPLETE.md。

实现：`analysis_new/appendix/c_models.py`复用原纯设计和FWL求解器；`c_completion.py`处理组件复用、计算、缓存、输出与核验。直接调用原设计函数，未修改其默认行为。执行授权与必要测试结果同时记入LOG.md。

## 运行

使用项目环境（当前 Python 3.12，numpy/pandas/scipy/matplotlib 已安装）：

```powershell
& 'C:/Users/haoya/.conda/envs/pyoutagegust/python.exe' -X utf8 -B 'D:/Pyprogramme/pyOutageGust/main_appendix.py' --all
& 'C:/Users/haoya/.conda/envs/pyoutagegust/python.exe' -X utf8 -B 'D:/Pyprogramme/pyOutageGust/main_appendix.py' --appendices A J
& 'C:/Users/haoya/.conda/envs/pyoutagegust/python.exe' -X utf8 -B 'D:/Pyprogramme/pyOutageGust/main_appendix.py' --all --check-only
```

激活项目环境后也可使用 `python main_appendix.py --all`。路径由脚本定位项目根，不依赖终端当前目录。不传选择参数时只显示帮助，不写入；`--check-only` 单独使用检查全部来源，不生成、清理或追加日志。不存在随机新步骤；所引研究的原随机配置见来源协议和 J_FROZEN_EXPERIMENT_DEFINITIONS。

固定输出为 `results/Appendix/`；生产模式最近运行命令、软件版本、Git HEAD、实际工作区源码哈希、输入和产物哈希见根 manifest。Git HEAD 不代表未提交工作区，故同时记录实际源码指纹。

## 代码与登记

- `analysis_new/appendix/catalog.py`：唯一可编辑主张/需求/权威来源登记。正文P编号统计DOCX直接body段落，含空段。
- `mapping.py`：生成三层CSV视图；`source_fingerprints.json` 冻结指定版本。变更来源须先确认正确版本再更新登记，不按日期或性能自动选择，也不自动刷新失败哈希。
- `exporters.py`：已有表格式转换、固定数据描述和已有绘图数据重画；无模型估计或新评分设计。
- `design_adapter.py`：隔离加载旧源码中原样的纯 `design` / `final_design` 函数与常量，避免执行旧模块顶层目录创建或拟合。固定设计VIF使用 `diag(inv(corr(X_without_intercept)))`，并核对列顺序与已存最终系数。未改旧函数或其默认行为。
- `runner.py`：来源检查、暂存验证、按字母事务发布、清单和日志。

三层映射是主张位置→实际需求→权威来源/导出步骤。READY/FORMAT/DERIVE/LOCATE/MISSING/CLOSED是来源状态；最终完成状态单独记录。图表显示编号只在 `figure_table_register.csv` 维护，文件使用稳定语义名称。

表格CSV保留17位有效数字，Markdown便于阅读。缺失保留NA；保存前后检查数字序列化，不把控制台输出充当表。当前图片采用项目 figure_style，400 dpi PNG；不另生成无用途的多格式副本。J时间四面板只重画已有分箱/月度数据，显示全部非空箱均值和每箱n/阳性，分箱与预测均未改变。

## 来源与范围

正文权威运行为 `20260909183317` 的 `results/paper/Extended_paper_draft.docx`，不是按文件时间选取。两份 curated CSV 同时核对该运行 run.json 的输入指纹。DD-AGG01、DD-DUR01、DD-TIME01分别固定至20260909231634、20260910090006、20260910104718；P03仅使用天气定义/覆盖/天气值比较，不使用含失效解的模型排名。

旧 `docs/Appendix_revised_copy.docx` 的数据字典和事件重建段落可复用，同字母的旧研究结论不自动视为当前 A–J。历史原因十分位表、包含零客户的恢复候选与当前正客户最终模型分别标明样本。E两期各自拟合，J.5才是开发期冻结预测。

缺口、最小后续动作、对应主张ID在 `results/Appendix/result_gaps.md`；它们不是自动执行的待办。用户关闭的四项单列，不作为完成门槛。不以缺文件等同阴性结果，也不把导出成功写作科学验证通过。

## 覆盖与失败

每个选中字母在独立临时目录完成全部导出和检查后发布；临时目录不留作版本。旧管理清单中已废弃文件仅在成功发布后移除。人工文件保留；与新产物同名时拒绝覆盖并说明冲突。目录替换失败自动恢复前一整套产物。

生成失败时该字母标记“本次未更新/保留上次成功产物”，没有旧产物则标记缺失；不将部分输出混入成功集。根manifest记录选中、未选中和失败。未选中字母的文件及其时间不更新。根映射、编号表、日志只保留当前状态；项目 `LOG.md` 保留各次开发、测试和生产的历史记录。

目录访问权限被拒绝时，临时目录创建立即报错，不使用Windows标准tempfile的长重试分支。路径不依赖cwd，但运行账户/工具仍需对项目输出目录有写入权限。本轮已在保留项目授权上下文后，将PowerShell当前位置切换至用户主目录，成功运行绝对路径入口；若将工具任务根本身切至其他目录，工具的文件写入权限可能变化，这不等于脚本使用相对输出路径。

## 必要测试

```powershell
python -X utf8 -B -m unittest discover -s test -p test_appendix_production.py -v
```

测试使用临时目录验证清单清理、人工文件、失败回滚/状态/重试、选择范围、稳定覆盖、路径越界拒绝；另从不同cwd运行只读模式，确认正式产物与LOG均未改变。没有重跑研究算法的全面测试。测试中 `simulated exporter failure` 是受控注入，不是正式结果失败。

## 本轮停止范围

完成独立接口、所有有输入的39项登记需求中的可执行部分、正式结果输出与必要检查后停止。没有修改Word、正文/附录文字、原始数据或历史研究结果；未生成ZIP、远程提交或新模型实验。后续由研究负责人处理已登记的实质证据缺口和论文呈现。


## APP-J03-COMPARE：第一工作包（2026-09-10）

当前用户授权覆盖上文仅C可补算的旧限制，仅增加J03两来源八任务对照。

```powershell
python -X utf8 -B main_appendix.py --appendices J --j03-only --check-only
python -X utf8 -B main_appendix.py --appendices J --j03-only
python -X utf8 -B main_appendix.py --appendices J --j03-only --recompute-j03
```

第一条只读预检；第二条复用完整且指纹匹配的本包缓存，首次缺失时复用兼容A01并拟合PROXY；第三条明确重算本包96组件，仍使用原稳定预算，不重跑DD-AGG其他聚合、DD-DUR或DD-TIME。普通`--appendices J`执行J导出及本包有效缓存整理；本轮推荐`--j03-only`逐文件保留其他J需求。所有默认研究开关不变。

关键输出：J/tables/J03_PAIRED_METRICS.csv、J03_FULL_PARAMETERS.csv、J03_FOLD_FITS.csv、J03_COMPONENT_MANIFEST.csv、J03_CALIBRATION.csv；J/data/J03_OOF_PREDICTIONS.csv.gz与相同LAD抽样记录；J/logs/J03_PROTOCOL.json、J03_TECHNICAL_CHECKS.json、J03_EXECUTION_REPORT.md。评分符号为PROXY减GRID_MAX，正差利于GRID_MAX；相对改善是百分比，不是概率百分点。

缓存同时绑定输入/样本与标签/折/配置/实际代码；同名文件存在不足以复用。全样本与折内参数分开，弱识别与无效状态分别保留。每次运行事实见J03_LAST_EXECUTION.json；源组件动作不因缓存导出而伪称新增拟合。固定目录、事务替换与人工文件保护不变。科学讨论状态在四步台账中由反馈推进，不因产物成功直接关闭或进入下一包。

J03的图形/报告渲染与科学缓存分开：普通命中缓存后仍重新导出图和报告，科学数据与表格保留；仅渲染文字/排版改变不会触发拟合。原拟合版本保留在J03_PROTOCOL.json，当前渲染哈希记在J03_LAST_EXECUTION.json。第一包完成回执见docs/new_analysis/reports/APP_J03_COMPLETION.md；科学反馈仍待研究负责人组织。

## APP-F02-COV：第二工作包

研究负责人已确认J03匹配比较缺口关闭并保留正文PROXY；本轮仅补天气固定final模型的聚类推断。使用 `python -X utf8 -B main_appendix.py --appendices F --f02-only`；加 `--check-only` 只读，加 `--recompute-f02` 重新计算协方差，仍优先复用兼容的全样本系数/残差，非强制拟合。普通 `--appendices F` 同样保留已有F01/F03；首次F不存在时才整理其已有产物。本轮不重算F.3。

F02冻结正式天气暴露11/24平台及天气恢复固定11单结点，调用原纯build/design，原完整控制项和温度平方不变。C保存的in_sample预测经ID、响应、固定结点和正式系数逐行兼容检查后复用；不调用其CV或搜索。协方差使用本地statsmodels的两组聚类及小样本修正，区间与p值按原t(G_LAD−1)。原final表已经有se_lad列；当前补矩阵、区间和复算来源。

主表为F/tables/F02_COEFFICIENT_COMPARISON.csv（及MD）；规格、原表差异、矩阵/设计/残差放F/data/F02_*，不全登记为论文表。F/logs/F02_EXECUTION_REPORT.md为本包事实回传报告。缓存同时验证输入、样本配置、代码、库版本与源产物哈希。完成状态为待反馈分析，G/I和H不启动。

## APP-GI-PRED：第三工作包

J03/F02已由负责人关闭（更新推进台账(2)第10节）；本轮只G/I，H未授权。正文及A–F/H/J结果保持只读。

```powershell
python -X utf8 -B main_appendix.py --appendices G I --gi-only --check-only
python -X utf8 -B main_appendix.py --appendices G I --gi-only
python -X utf8 -B main_appendix.py --appendices G I --gi-only --recompute-gi
python -X utf8 -B main_appendix.py --appendices G I --gi-only --render-only-gi
```

正常调用复用指纹匹配的缓存；限定重算仅补本包相同固定模型/原五折，不执行候选搜索。最后一条仅从有效数组重绘，失配时报错而不拟合。可单选G；单选I需要此前已完成且源指纹有效的G。G和I同时选择时按G→I执行。交付默认入口无自动开启研究步骤。

共享主预测在G/data/GI_PREDICTIONS.csv.gz，保留模型、样本、预测类型、原折、训练来源与响应尺度；I仅保存七窗口切片及必要超阈展示点。全样本、控制残差、固定LAD-OOF、C嵌套家族CV不得混称。固定结果目录、事务替换及未知人工文件保护沿用原机制；PNG/PDF为同图，显示登记以PNG为准。

G/logs和I/logs各有GI_EXECUTION_REPORT.md；技术、覆盖计划、原图身份、来源及图形数组见相应data/logs。产物成功仅标完成待反馈，不自动关闭第三包，也不自动开始H。未修改论文、生成ZIP或远程提交。

## APP-H03-LINK：第四工作包（当前授权）

更新台账(3)第12–13节已确认前三包结果补全关闭；GI-W01至W09保留至后续成文。本包只H：当前全体E60437上的NB2/Tweedie和R51173上的Gamma/Tweedie，使用正式固定X；OLS与H.2/H.3既有结果复用，不做CV、结点搜索或新的阈值模型。

```powershell
python -X utf8 -B main_appendix.py --appendices H --h03-only --check-only
python -X utf8 -B main_appendix.py --appendices H --h03-only
python -X utf8 -B main_appendix.py --appendices H --h03-only --recompute-h03
```

选择H即覆盖该包完整授权范围；`--h03-only`限制选中字母只能为H，默认无自动启动。固定输出`results/Appendix/H/`；H03前缀，暂存核验后发布；H01/H02与人工文件保留，其他附录及原研究来源只读。重算选项只作用H03四项候选，不重拟OLS或H.2/H.3。

普通运行核验输入、完整设计来源、模型/评价配置、统计计算代码、库及所有缓存产物指纹。报告/调度代码另保留完整指纹，纯文字更新不触发重新拟合；系数对照由保存系数重新导出。明确重算时，NB2先走原默认路径，无效才执行一次已记录的常数均值初值恢复；同BFGS200次/gtol1e−5、联合alpha，不修改X/y或挑选多个有效解。首次失败及恢复配置均保留。

主要表：H03_MODEL_DEFINITIONS、H03_FULL_COEFFICIENTS、H03_GUST_COMPARISON、H03_EVENT_CONDITIONAL_FREQUENCIES。过程、旧结果适用范围、X/响应/均值/score/Hessian/协方差放data与logs。回传事实报告：H/logs/H03_EXECUTION_REPORT.md；完成索引：docs/new_analysis/reports/APP_H03_COMPLETION.md。结果完成待负责人反馈，不自动关闭H或开始附录成文。
