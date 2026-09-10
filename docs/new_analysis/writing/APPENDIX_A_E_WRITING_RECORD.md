# APP-WRITE-AE 写作与证据记录

状态：A–E 合并英文初稿完成；供研究负责人审阅，不是投稿认证。日期：2026-09-10（Europe/London）。

## 权威来源与边界

本轮接受研究负责人对 A–E 已完成的确认。以 `results/new/20260909183317/results/paper/Extended_paper_draft.docx` 为正文术语及章节对应依据，以 `docs/new_analysis/instructions/论文整合计划_v9_附录成文与正文衔接.md` 为结构依据，以 `results/Appendix/` 的 `claim_evidence_map.csv`、`appendix_requirements.csv`、`requirement_result_map.csv`、`figure_table_register.csv` 为既有映射。最新已接受的 A–E 结果优先于旧稿中的同名附录和旧解释。

唯一人工维护稿为同目录 `Supplementary_Information_A_E_draft.md`。不写入自动生产目录。`checks/manuscript_state.json` 是 academic-writing-skills 的检查适配器，引用原登记，不替代或复制一套科学结果台账。

已实际读取 `C:/Users/haoya/.agents/skills/academic-writing-skills/SKILL.md` 及 state-and-authority、universal-integrity、prose-and-citation-editing、study-design-adapters 的相关部分、lifecycle-and-routing、reviewer-red-team-and-release。采用多章节 managed-project 模式、观察性/计算模型写作适配、逐节写作契约、四遍有限写作检查及最后候选文本检查。没有调用独立审稿 agent。

## 写作前契约：正文主张 → 读者功能 → 证据 → 解释边界 → 衔接

| 章节及段落组 | 正文对应 | 读者功能与最窄主张 | 授权证据 | 推论边界与下一段关系 |
|---|---|---|---|---|
| A.1 来源；A.2 原因分组 | §2.1、§2.4 | 说明研究地域、期段和纳入范围，定义 all 与 weather-attributed | A4、A5、当前正文来源段 | 不将纳入样本称为全部运营总体；由来源转入可测量变量 |
| A.3 变量；A.4 样本 | §2.2–2.4、§3.1–3.2 | 明确单位、标准化、缺失和四个最终样本 | A1–A4、已有样本构造方法 | 不重设原因代码、清理或填补；将事件构造细节交 B |
| A.5 分布与VIF | §2.4 | 给出实际协变量分布、设计共线性和既有原因构成分箱 | A3、A6、A7 | VIF不证明无混杂/无过拟合；分箱不等于正文另一组风速带 |
| B.1–B.2 聚合与边界 | §2.2 | 简洁算法、起止跨度和代表记录选择可复现 | B1、B2；直接相关构造代码片段 | 不从时间模式推定业务机制；转入零客户恢复定义 |
| B.3–B.4 零客户与加权时长 | §2.2–2.3 | 量化既有记录特征，区分事件跨度与客户经历 | B3、B4成熟文字 | 共享权重不构成必然伪相关证明；不重复 A 完整流转 |
| C.1 设计与候选身份 | §3.1、Table 3、§4.1–4.2 | 固定四组合，说明 H 与 F、评价尺度和训练边界 | C1、C4、C9、C README | 不跨样本排名；转入阶梯，再进入纯函数比较 |
| C.2–C.3 性能证据 | §3.1–3.2、§4.1–4.2 | 报告全部已定候选，量化当前函数与其他函数差异 | C5、C6、Figure C1 | 不称所有当前函数最优；不夸大小误差差异；结点不确定性交 D |
| C.4 地区效应 | §3.1、§3.3 | 区分样本内解释与未见LAD预测 | C7、原未见类别编码规则 | 不将置零虚拟变量写成没有截距；不自动改主模型 |
| D.1–D.2 搜索及区间 | §3.2 | 定义目标函数、网格、profile及两类bootstrap | D1、对应knot/ramp方法记录 | 点估计、系数SE和结点区间不同；转入实际定位精度 |
| D.3–D.4 识别及折内选择 | §4.1–4.2 | 逐分支解释已有区间和训练折结点 | D1、D2、Figure D1；C同控制表 | 历史59834自由恢复分支独立标记；不挪用其区间至最终恢复 |
| E.1 期段；E.2 系数；E.3 含义 | §3.3、§4.5 | 明确两期各自拟合、期内标准化和已探索历史，呈现全部已保存系数 | E1、E2、paper_extras相关方法 | 非冻结参数预测、非独立确认；与J只在内部衔接记录联系 |

以上每段按功能、窄主张、来源、解释、相邻段关系组织；不机械重复四段标题。

## 实质解释选择（写作冻结）

- A 使用四个最终样本 60,437 / 51,173 / 9,857 / 9,254。恢复旧输入 59,834 只在流转及明确历史比较出现。暴露保留零客户。
- A7 原十组的范围为 0.5–4.2 至 16.9–39.4 m/s，天气比例 6.9327% 至 57.0619%。与正文 0–4、>30 m/s 的另一种分箱不能互换。接受 A 完成状态，不沿用过期 A06 缺口、不启动补算。
- B 保留已有算法，明确再中断阶段不进入 C 求和，但进入跨度，现有加权时长比较也未排除这些阶段。明确一小时记录集中是观察事实，业务原因未由专门字段确认。
- C 以最终同控制表为函数比较依据；全体暴露平台最小 LAD RMSE，其余三组当前函数不是最小，全部如实保留。旧恢复比较不进入当前最终样本排名。
- D 历史自由双结点恢复 n=59,834 单列标明；最终正客户平台分支的控制项沿用其实际记录，不改称当前含阵风×降水规格。当前天气恢复主函数为单结点 11 m/s，不为它移植平台区间。
- E 只解释现有两期分别拟合。样本清理与规格曾用全期信息，标准化按各拟合期确定；不能称冻结预测或首次独立确认。

## 已读取材料范围

实际读取了上述当前正文相关数据、方法、模型、时间设计段落和参考文献，v9 的 A–E 结构；根目录五项映射/登记、manifest、result_gaps；A–E README 和 manifest；A/B/D/E 下全部表格；C 下候选定义、覆盖、样本、全部阶梯/同控制/地区效应/原比较引用表。

仅为文字定义读取了直接相关的方法片段：`scripts/code_audit_20260905/audit_pipeline.py` 的 C、D_A、D_B 构造，代表记录/最终样本构造片段，`analysis_new/model_selection.py`、最终设计与 Appendix C 实现、`analysis_new/knot_estimation.py`、平台搜索/bootstrap，以及 `analysis_new/paper_extras.py` 的期段拟合。没有重审全部代码，没有读取并重算大型逐行预测，没有重训或统计再计算。

拟用的 `C/figures/C_GUST_PERFORMANCE.png` 和 `D/figures/D_PLATEAU_PROFILE_BOOTSTRAP.png` 已通过图片工具实际打开。C 图展示四组相对二次型的 LAD pooled RMSE 差值，D 图展示全体/天气暴露平台的 profile LR 热图和结点 bootstrap 次数；图注按实际显示撰写。

复用现有参考文献 [14]、[27]、[29]，仅核实原始出版来源：ERA5 的 DOI 10.1002/qj.3803；Muggeo 的 DOI 10.1002/sim.1545；Cameron–Gelbach–Miller 的 DOI 10.1198/jbes.2010.07136。文稿不将本地网格搜索误写成 Muggeo 的迭代算法。数据来源沿用正文已核实文献，不另造引用。

## 后续正文衔接（本轮不修改）

| 位置 | 当前衔接事项 | 本稿证据与处置 |
|---|---|---|
| §2.2 加权时长解释 | “共享权重因而必然产生伪相关”过强 | B.4 写成两个不同估计对象，给出现有配对摘要；不作未提供的相关性证明 |
| §2.3 / Figure 2 时间模式 | placeholder / automatic reclosure 的机制断言 | B.3 仅写记录集中现象；需要业务依据时由作者决定措辞 |
| §2.4 60,453→60,437 | 正文把差额16归于天气/地区缺失，与现有已完整匹配WT输入后缺客户的顺序不一致 | A.4 按当前来源说明，不改数字或删除行 |
| §2.4 原因构成风速带 | 正文7%→91%是不同风速带，不能用A7十组代替而不换标签 | A.5明确真实分箱与分母，作者整合时决定正文呈现哪组已接受结果；不是新增实验请求 |
| §3.1 / Table 3 | 旧恢复样本、FE未见地区处理、所有准则均最优等措辞 | C的最终样本数和全部对照替代旧口径；保留全局截距，区分样本内/样本外 |
| §3.2、§4.1 | 500次自由与300次平台bootstrap；固定与折内结点；D恢复控制条件 | D分别说明实际分支，纯函数排名指向C.3 |
| §4.2 天气恢复及候选排序 | 天气恢复为11 m/s单结点，不能统一写恢复均二次；当前函数不全是最小CV误差 | C.3如实给出差异，不作自动换模型建议 |
| §3.3、§4.5 | 两期分别拟合不等于独立冻结验证；分期标准化 | E.1–E.3限定；与DD-TIME01的联系留待J编排，不写未登记J图号 |

## 表图与文字复用记录

以下给出最终编号—文件对应与有限检查。英文重写以组织方法和结果为主，优先保留当前正文中准确的研究范围、变量名称、公式与样本定义；B 的阶段聚合/首阶段均值比较沿用成熟内容，删除无证据的机制推断。C、D、E新增的是读者连续论述，不翻译内部审查措辞，不把运行ID或绝对路径写进读者稿。


## 最终表图对应

下列编号沿用既有 figure_table_register；不因正文组织顺序不同重编号码，不改根登记。内部完成矩阵不作为读者表。文件均相对于项目根目录。

| 显示编号 | 证据ID / 主张ID / 需求ID | 实际来源 | 呈现处理 |
|---|---|---|---|
| Table A5 | A03_EXISTING_DEFINITION / CL_A03 / A03 | `results/Appendix/A/tables/A03_EXISTING_DEFINITION.csv` | 6组代码完整保留，增加既定纳入标识 |
| Table A2 | A_CAUSE_COUNTS / CL_A01 / A01 | `results/Appendix/A/tables/A_CAUSE_COUNTS.csv` | 只呈现final原因构成；天气子集身份在表注说明 |
| Table A4 | A_VARIABLE_DICTIONARY / CL_A02 / A02 | `results/Appendix/A/tables/A_VARIABLE_DICTIONARY.csv` | 15项变量字典英文转写，算法细节指向B |
| Table A1 | A_SAMPLE_FLOW / CL_A01 / A01 | `results/Appendix/A/tables/A_SAMPLE_FLOW.csv` | 删去重复的E0 saved_input行；保留四最终样本及恢复中间输入 |
| Table A3 | A_COVARIATE_SUMMARY / CL_A01 / A01 | `results/Appendix/A/tables/A_COVARIATE_SUMMARY.csv` | 18行全部呈现均值/SD/中位数/IQR；未另算描述统计 |
| Table A6 | A_FINAL_DESIGN_VIF / CL_A04 / A04 | `results/Appendix/A/tables/A_FINAL_DESIGN_VIF.csv` | 54个VIF单元转为两列；缺项使用破折号 |
| Table A7 | A05_APPENDIXG_TABLE_G1_CORRECTED / CL_A05 / A05 | `results/Appendix/A/tables/A05_APPENDIXG_TABLE_G1_CORRECTED.csv` | 10行完整保留；组0–9仅显示为1–10 |
| Table B1 | B_CONSTRUCTION_RULES / CL_B01 / B01 | `results/Appendix/B/tables/B_CONSTRUCTION_RULES.csv` | 已有规则表与直接相关代码片段归纳为7行英文规则，不新增算法 |
| Table B2 | B_REPRESENTATIVE_REPAIR / CL_B01 / B01 | `results/Appendix/B/tables/B_REPRESENTATIVE_REPAIR.csv` | 选取总数/同起点/代表变化/不可解析等5项核心计数；不放调试过程 |
| Table B3 | B_RECOVERY_DEFINITION / CL_B02 / B02 | `results/Appendix/B/tables/B_RECOVERY_DEFINITION.csv` | 3组一小时记录完整呈现；A/B配对描述移入B.4文字 |
| Table C1 | C_CANDIDATE_DEFINITIONS / CL_C01 / C01 | `results/Appendix/C/tables/C_CANDIDATE_DEFINITIONS.csv` | 88条按共同规则压缩为22规格，四组合差异在正文与表注定义 |
| Table C6 | C_HISTORICAL_LADDER / CL_C02 / C02 | `results/Appendix/C/tables/C_HISTORICAL_LADDER.csv` | 56项完整，四面板，3种评价分别显示 |
| Table C4 | C_EXISTING_FIXED_AND_D_REFERENCES / CL_C03 / C03 | `results/Appendix/C/tables/C_EXISTING_FIXED_AND_D_REFERENCES.csv` | 8项天气三模型与全体最终参考；D重复比较不重复放完整表 |
| Table C5 | C_GUST_FUNCTION_COMPARISON / CL_C03 / C03 | `results/Appendix/C/tables/C_GUST_FUNCTION_COMPARISON.csv` | 32项完整，8位RMSE，F05按已有定义显示10.8固定 |
| Table C7 | C_LAD_FE_COMPARISON / CL_C03 / C03 | `results/Appendix/C/tables/C_LAD_FE_COMPARISON.csv` | 8项完整显示调整R²/LAD RMSE；参数数和AIC/BIC交叉引用C6 |
| Table D1 | D_KNOT_SUMMARY / CL_D01 / D01 | `results/Appendix/D/tables/D_KNOT_SUMMARY.csv` | 12个结点记录完整；历史恢复标签显式保留 |
| Table D2 | D_NESTED_FOLD_KNOTS / CL_D01 / D01 | `results/Appendix/D/tables/D_NESTED_FOLD_KNOTS.csv` | 10行完整；fold_order 0–4显示1–5，未改折号归属 |
| Table E2 | E_TEMPORAL_DESIGN / CL_E01 / E01 | `results/Appendix/E/tables/E_TEMPORAL_DESIGN.csv` | 原3期设计与E1已保存n/平均gust连接成两margin六行；无新统计 |
| Table E1 | E_PERIOD_COEFFICIENTS / CL_E01 / E01 | `results/Appendix/E/tables/E_PERIOD_COEFFICIENTS.csv` | 18行完整，系数/SE六位，p保留有效数字 |
| Figure C1 | C_GUST_PERFORMANCE / CL_C03 / C03 | `results/Appendix/C/figures/C_GUST_PERFORMANCE.png` | 原图直接相对引用；明确是相对F01差值，非绝对RMSE |
| Figure D1 | D_PLATEAU_PROFILE_BOOTSTRAP / CL_D02 / D02 | `results/Appendix/D/figures/D_PLATEAU_PROFILE_BOOTSTRAP.png` | 原图直接相对引用；注明色标不同、B=300、计数连线非密度 |

B4成熟文字被吸收入B.4末段（47.13、93.02、1.97），不重复展示文字导出表。C2/C3/C8为覆盖/完成登记，留在内部索引；C9样本信息由A1及C.1承接，不跨章重复整表。完整数值仍在原CSV，没有覆盖或重新计算。

## 四遍有限写作检查与处置

1. **结构与功能**：完整阅读A–E。A交代来源/变量/样本，B解释构造，C区分原阶梯与同控制比较，D负责结点估计及区间，E限定事件级两期各自拟合；没有写F–J。段落衔接依照前述契约，未将内部日志翻译进正文。
2. **证据与范围**：核对全部转写表的样本、尺度和编号；两图均实际打开查看。修正C1图注为相对二次型的RMSE差值；D明确自由分支不含温度平方，平台分支加入温度平方且恢复没有阵风交互，删除将两分支结点差异单归因于平台限制的句子。没有重训、重算统计或重开历史审计。已读既有[14]/[27]/[29]原始摘要或作者原文支持相应一般方法句。
3. **学术表达**：修正悬挂复合词、B3内部字段名、F05固定结点显示、步骤阈值“at or above”；保留all-incident/weather-attributed等统一术语。完整英文正文和相邻段落已重读；无超过48词的普通正文单句（简单扫描辅助，数学和表格不作该断句判断）。没有以“显著/稳健/最优”代替结果。
4. **交付完整性**：检查19个可编辑表、2幅原图的登记编号及相对路径；无占位符、绝对电脑路径或虚构J编号。数学分隔符和表格列数匹配。未制作Word/PDF，因此未宣称检查排版后的分页。

### 可独立复做的写作检查

在项目根目录、已有Python环境执行：

```powershell
python docs/new_analysis/writing/checks/format_existing_tables.py
python docs/new_analysis/writing/checks/check_document.py
python C:/Users/haoya/.agents/skills/academic-writing-skills/scripts/audit_candidate_text.py docs/new_analysis/writing/checks/manuscript_state.json docs/new_analysis/writing/Supplementary_Information_A_E_draft.md --label APP-WRITE-AE --json
```

前两个只读稿件/既有结果并更新checks内写作记录，不进入研究流程。`--insert`是初稿占位符的一次性转写选项，成稿无占位后会拒绝覆盖；后续人工只维护合并MD。

最终候选SHA-256：`bb8c72733ec15f6a3f4e6b76c092952a817cea352ca86e4c3f7b360a85da45f6`。该哈希对应最后一次文字修改后的文件。候选脚本保留11条语境提示，逐项见 `checks/candidate_findings_disposition.json`；均为表格缺项符号或保持样本/模型身份的术语，按本轮明确保留术语与完整结果要求处理。脚本状态如实为 FINDINGS，不虚报零提示或科学审查通过。18个格式化表块与来源匹配；结构检查19表/2图无问题。

### 功能完整性回顾及人工事项

- 本轮五章、可编辑表、真实图片、证据关系、正文衔接和写作记录均已交付，完成的是初稿阶段。模型、样本、范围与研究负责人锁定决策未改变。
- 观察性/计算模型适配只用于限制写作推论，没有扩展实验。纯格式检查不被当作独立数值核验；已有模型收敛与预测结果未重复审计。
- 主稿未修改；实际需要作者随后判断的是正文整合表中已有的口径衔接，尤其风速分箱、C的非统一最小误差、D各分支控制条件和E的回顾性分别拟合。没有为本稿另立待补实验清单。
- 本稿可供人工审阅，不称投稿终稿。当前任务到此停止，F–J等待另行授权。
