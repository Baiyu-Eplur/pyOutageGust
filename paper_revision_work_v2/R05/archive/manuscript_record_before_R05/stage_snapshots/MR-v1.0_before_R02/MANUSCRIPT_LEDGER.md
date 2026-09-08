# 论文组织、故事与论证修订台账

版本：MR-v1.0，2026-09-05。检查点：**初步代码核查 + R00–R01反馈 + 本对话R02审阅意见**。用户所说的“S0-1”在本次记录中对应v2计划的R00–R01；不另造一次审计。

## 0. 使用范围与当前事实

这是一份已经填入具体内容的论文修订记录。它同时保存研究主线、逐章方案、主张与证据对应、具体修改条目、来源、状态和下一步。后续每阶段都需更新，而不是只保存代码报告或依靠对话记忆。

当前已接收的是本地核查报告及R00–R01返回摘要。**本环境没有本地全部contracts、工作簿、源码和审计CSV；报告中的底层核实属于“本地报告已核实”，不能改写为本对话再次独立验证。R02尚未收到完成结果，B1和V结果尚未生成。**

本轮直接对照当前正文151个段落、4张表及附录94个段落、13张表，建立固定版本的段落/表格索引。数学对象的文字抽取用于定位，分式、上下标等需以归档Word的可编辑公式为准；本轮没有重新核验所有嵌入图片像素。**两份Word未修改。**

本记录包包含来源文件快照，尤其将易被后续覆盖的RETURN_TO_CHATGPT.md固定为SRC02。来源ID、原文件名和SHA-256见SOURCE_MANIFEST.json。独立MD包含核心证据和修改计划；逐文件离线追溯请使用完整记录包。

### 0.1 三种状态分别记录

| 维度 | 当前允许的状态 | 含义 |
|---|---|---|
| 证据 | 当前Word直接核对 / 本地报告已核实 / 本地原产物待提供 / 方法推论 / 作者决定 | 说明这条判断来自哪里 |
| 决定 | 明确修正方向 / 条件于新结果 / 结构建议待审 / 已有作者决定 / 待澄清 | 不把建议冒充作者已接受的具体改法 |
| 落实 | 尚未写入Word / 已写入待复核 / 完成稿核对通过 / 被后续证据替代 | 不能将规则明确或代码已修当作文字已改 |

本轮MR01–MR28均为“尚未写入Word”。早前已经写入基线的正确修复另列保护清单；若本轮要迁移其位置，也不能恢复被撤回的错误解释。

### 0.2 定位方式

`D-Pxxx`和`D-Txx`分别表示DOC01正文顶层段落及表格；`A-Pxxx`和`A-Txx`表示DOC02附录。编号只适用于本次哈希固定的Word。章节号变化后保留旧定位，并新增完成稿定位；不能把旧编号套到新文件。每项另附原文锚点，供版本变动时检索。

## 1. 已确认的过程决定与待审设计

| 决定ID | 内容 | 依据与状态 |
|---|---|---|
| PD01 | 先修旧代码与研究流程，建立修正基线，再补证，最后改稿并全文复审 | 用户在本对话明确要求；沿用R→V→W |
| PD02 | R/V每一步同时记录正文结构、故事、论证、章节修改和来源 | 用户本轮明确要求；立即生效，不需等W阶段 |
| PD03 | Buckinghamshire暂保留显式历史代理，后续LSOA重建并对照 | SRC02转述本地作者决定；沿用，尚未收到详细决定文件 |
| PD04 | 当前定位回顾性事件条件关联，工程指标是客户影响与记录恢复跨度 | 既有计划和审阅采用的工作定位；新增初期预测/因果/部署用途需另定范围 |
| PD05 | 两个未决ID不凭极值或重复标识自动拆分/删除，保留身份和资格状态 | SRC02 + SRC03；模型是否纳入依本地冻结规则，未提供处不代填 |
| PD06 | 主文改为六章、将Discussion与Conclusion分开 | 本台账结构建议，尚未获作者单独确认；五章版本也可承载同一内容职责 |
| PD07 | 最低点与排序反转是否继续为核心 | 待修正输入和V结果；不预设旧结论必须保留 |

## 2. 论文主线与论证设计

### 2.1 当前稿件的叙事及问题

当前摘要D-P002以60,453事件、阶段聚合约1.97倍、正二次项、约10.7m/s最低点和天气子样本排序反转为主要发现。引言D-P010把最低点稳定性纳入第一研究问题；§4.1投入较多篇幅解释最低点、对称性和Bootstrap修复；§4.2–4.3依靠增量R²、地图/网格比值及风暴散点组织论证；第5章同时承担结论、讨论和未来工作。附录E/H保存较多开发和错误修复历史。

新代码证据使其中两条核心主张需要等待重算：事件时间错误影响阵风及样本/日期/风暴归属；天气子样本比较同时改变p99和折分。文字收窄不能单独补足这些输入及比较证据。另一方面，区域定义和部分实现已经核清，不应继续让过时疑点占据论文篇幅。

### 2.2 建议的工程故事

**中心问题：在一个实际配电网络中，如何从阶段报告可靠地定义事件后果，并评估阵风与客户影响、恢复跨度之间的关系，以及这些信息关系在不同事件组成和天气过程下是否稳定？**

叙事依次说明：网络后果有不同维度 → 阶段记录需要有依据的事件重构和时间对齐 → 在明确范围内描述阵风关系 → 用可比评价检验阵风/客户信息贡献 → 把有效结果解释为工程量级和适用边界。

候选标题（尚未定稿）：*Gust-related variation in customer impact and restoration spans: incident-level evidence from a UK distribution network*。

不要把“发生过多少轮审查”写成研究贡献。可能成立的贡献是数据定义与事件层面证据、共同网络中不同后果/信息关系的对照、对极端过程及组成敏感性的透明检验；新颖性仍需与原始文献逐项比较。

### 2.3 主张—证据—反例—落稿分支

| 主张ID | 拟回答的问题 | 需要的最低证据 | 当前状态 | 不获支持时的文字路线 |
|---|---|---|---|---|
| CL01 | 重构指标是否测到所声称的事件客户影响与恢复跨度 | 字段语义、身份规则、完整阶段、C/D实现、边界及新样本流 | 实现复现已有；真实onset/特殊规则仍有边界 | 使用记录跨度/时间代理，明确未决资格；不写平均客户失电或CML |
| CL02 | 阵风关系是否存在可重复的非线性/最低点 | B1后形状比较、支持量、影响过程、必要区间 | 旧二次结果与三阶反向线索并存，尚未重估 | 非线性不稳则报告不稳或简单模型；最低点不稳则撤出摘要 |
| CL03 | 阵风与最终客户规模的相对增量信息是否随原因人群改变 | 同信息条件/样本/分母的配对Δ、统一尾部/划分、共同支持及不确定性 | H0点排序可复现，跨样本口径不一致 | 贡献接近且点估计反转；或没有稳定反转，均允许 |
| CL04 | 完整天气过程中的关系与误差如何 | 过程/连续块评价、窗口合并、成员和权重、基准误差 | 原图含拟合内及未训练尾部，非独立过程验证 | 仅作描述；若泛化差，报告局限而非把相关性包装为验证 |
| CL05 | 对工程理解有多大量级和价值 | 支持内场景、明确目标/参考人群、误差或不确定性、信息时点 | 尺度及参考存在已知代码问题 | 保留可解释log或指数拟合量，不声称原尺度均值/可部署 |
| CL06 | 是否识别恢复机制或区域设施差异 | 与主张匹配的额外资产/运维/识别证据 | 当前不具备 | 描述组成与条件关联；机制留为有依据的待检假说 |

### 2.4 摘要的五句职责（结果未补齐前只作为框架）

1. 工程问题：天气下的事件客户影响和恢复跨度需要分别理解。
2. 数据与方法：用最终核实的时间范围/样本描述重构、天气匹配与评价方式；数字取最终总账。
3. 第一发现：根据CL02的实际分支写形状，不提前承诺稳定最低点。
4. 第二发现：根据CL03–CL05写配对贡献与工程量级；指出信息条件及适用范围。
5. 贡献与边界：说明对该网络已记录事件后果的认识，不扩大到故障发生概率或调度阈值。

目前不生成貌似完成的数值摘要。D-P002、D-P010、D-P012与D-P118–P124必须在最终同一次证据整合中同步更新。

### 2.5 工作范围不随故事设计自动扩大

T12仍为选择一项有可靠字段与明确工程目的的异质性分析；T13的客户累计负担、发生概率、部署或跨运营商泛化默认不扩展。Buckinghamshire的LSOA重建对照来自已有作者决定，不能因其出现在区域讨论中就降为一个未选择的泛泛可选项。条件任务、已决定后续任务和当前尚未执行的计算，在台账中分别保留。



## 3. 逐章组织与修改方案

以下是工作设计，不等于已经改动Word。章节编号可以调整，但各内容职责和证据依赖必须保留。

### 3.1 摘要与关键词

当前：D-P001–P004。按§2.4五句职责重写。删除或重算旧样本数、1.97倍和风暴数值；是否保留10.7与反转由CL02/CL03决定。关键词优先对应事件后果、阵风、恢复跨度、统计评价，不能用未验证阈值/部署用途吸引读者。依赖MR01/MR04/MR10/MR13/MR18/MR19/MR22/MR23。

### 3.2 引言（当前§1）

当前D-P006–P013。建议六段：

1. 用经过来源核对的风暴背景说明工程后果；D-P006中39.4m/s、事件/客户/小时数字均标H0待重算，去掉未经支持的“现场观测峰值”。
2. 解释客户影响与记录恢复跨度的区别及各自用途，避免将exposure margin误读为气象暴露或发生概率。
3. 将同类研究按分析单位、后果定义、可用信息时点及评价单元组织，说明本文补充什么证据。
4. 解释阶段记录与时间对齐为何是研究成立的前提；不在引言详细讲每个程序错误。
5. 研究问题以CL02、CL03及工程适用性组织；最低点是条件性结果而非预定核心发现。
6. 简述方法与贡献、给更新后的章节路标。三年/七个名字不能自动证明全风速支持充分或有七份独立验证。

当前D-P008/P009的构件脆弱性与已发生事件后果区分值得保留，但压缩重复。D-P011关于“full range”须由支持量说明；历史开发限制在方法集中交代，引言不再堆叠修补史。

### 3.3 数据与研究对象（当前§2）

建议顺序：2.1研究范围与报告制度 → 2.2事件身份/时间与后果构造 → 2.3天气及区域变量 → 2.4原因、质量与样本筛选 → 2.5最终描述统计。

当前§2.3在完整样本定义之前给描述统计，建议移至样本规则之后。§2.2增加时间代理及字段分别取源的简述，附录B给完整规则；公式1/2保留经核实含义，不能从“算得出”跳到“真实事件已验证”。§2.1天气产品/单位/时区与区域来源拆成易读段；gap/Moran定义及Buckinghamshire代理单列附录A来源表。§2.4把六组回归结果移到敏感性结果或附录C，主文此处只解释总体为何如此定义。

表1、图1/2及1.97倍等全部在B1/V目标确定后更新。给一个紧凑样本流，区分完整事件主表、目标可用和各模型/天气人群；训练尾部处理不混作测试总体定义。依赖MR01–MR11/MR21/MR22。

### 3.4 方法（当前§3）

建议顺序：3.1估计目标与可用信息 → 3.2模型/变换/参考条件 → 3.3评价设计与贡献比较 → 3.4推断和预定敏感性。

当前以二次式最低点开篇，建议改为工程估计目标先行。公式3/4与候选形状说明放在模型节；求导和最低点公式保留足够定义，额外代数和物理转换放附录H。准确说明天气/客户标准化、区域原尺度、年月加性效应与LAD聚类。

评价节明确合并OOF公式、共同评估事件、分母、组定义、训练内预处理及完整过程划分。用一段说明历史后期数据参与了开发；不因新的V方案冻结而恢复“未触碰确认集”说法。当前D-P055最低点历史序列移内部记录；科学必要的开发事实保留附录E。GLM、三阶/样条、阶段控制分别回答什么问题写清楚。

### 3.5 结果（当前§4.1–4.4）

建议4.1“Gust associations and empirical support”：先曲线/损失/支持，再决定是否讨论最低点；三阶反向证据和简单模型不占优的可能性不隐藏。

建议4.2“Incremental information under comparable sample definitions”：报告总体及天气人群的四模型配对比较，给Δ及不确定性；两种加入顺序另列。原“Population-level weight of wind”可更准确地命名为条件预测增量。

建议4.3“Performance across weather processes and engineering scenarios”：先明确过程成员和评价来源，再给基准误差、校准与场景量级。原图9相关性可作为补充描述，不能承担主要验证。

建议4.4“Sample and specification sensitivity”：将尾部、阶段质量、支持、替代分布、时序和协方差敏感性压成关键对照，其余完整输出在附录。不是把所有检查写成相互独立的成功验证。

图6/7去留由MR24决定；如果只重复大小排序或采用不一致参考，优先转附录或删除。最终只保留推动工程问题的图，不为保持原10图数量保留无用图。

### 3.6 讨论与结论（当前合在§5）

建议分成§5 Discussion和§6 Conclusion；若保留五章，可将当前§5分为工程解释、局限、简短结论三个子部分。六章只是建议，不是已确认排版。

讨论四段职责：数据定义对工程量的含义；阵风和客户信息的实际发现及同类研究比较；组成/天气过程/未观测运维条件可解释与不可识别的范围；集中说明来源、信息时点、历史开发和泛化限制。

结论仅保留经CL证据表支持的两三个发现与贡献范围。未来工作按仍保留主张的必需缺口和研究扩展分开；若最低点降级，不再把其Bootstrap作为所有路线必做；外部未用数据不是回顾研究完成的自动前提。

### 3.7 参考文献

当前D-P125–P151。逐条对应实际主张，核对原始来源内容和元数据。Annex F不同监管期、ONS源工作簿、天气历史接口与产品定义分别定位。旧文献支持某个3秒阵风概念，不等于证明本项目缓存产品。unverified字段在正式稿前解决或调整相关引用，不能靠删除占位词假装完成核实。

## 4. 逐附录修改方案

| 当前附录与定位 | 最终应承担的职责 | 具体动作与证据条件 |
|---|---|---|
| A（A-P001–P015） | 完整变量、原代码和来源字典 | 改gap与Moran层级；加时间/产品/代理来源；原因冲突和信息时点；不猜Moran权重与零客户含义 |
| B（A-P016–P027） | 可复现事件构造与质量规则 | 增最早记录/并列/字段取源；保留窗外阶段；两未决ID在内部留全线索，正式附录以必要匿名示例或数量说明；更新质量比例与C/D检验 |
| C（A-P028–P031） | 样本/原因/尾部定义敏感性 | 统一目标和可比评价，补当前版本生产者；旧六组各自p99/折分不能包装为只改原因人群 |
| D（A-P032–P055） | 客户—跨度与阶段组成的描述性证据 | 统一/显式标明样本、分箱、支持量；完整系数及信息时点；不识别调度、纯中介或唯一解释 |
| E（A-P056–P063） | 简明开发历史与最终评价设计 | 留事实和边界，移走以旧最低点序列/重复计数证明稳定的可能暗示；C01后起始/跨界归属重核 |
| F（A-P064–P068） | 最终完整模型及推断/诊断 | 更换受影响系数、n、SE；保留LAD与两维聚类区别；补齐仍保留GLM/诊断，不把旧数据检查拼入当前版本 |
| G（A-P069–P073） | 原因、风速支持与组成 | 重新生成分位/比例；比较共同支持，保留描述性质；不解释全部变化的唯一来源 |
| H（A-P074–P094） | 预测尺度、参考条件、可选最低点推断 | 保留必要公式/配置；删除正式文中的旧错误计算史和“材料待提供”记录；后者永久留本台账；是否保留最低点小节由V决定 |

A–H编号暂作映射，后期合并/重命名需给旧→新定位表。不能为了精简附录而抹去影响解释的开发事实或未解限制。


## 5. 逐条修订明细

下列条目把审计发现转成可执行的写作动作。局部英文句为候选措辞，须结合生效条件和完整段落整合，不是已经确认的终稿。

### MR01｜事件时间与天气来自后续阶段

关联：C01, T02, T03, T07, L02, L05, L08。决定：规则方向明确；候选完成时措辞待R02事实确认。落实：尚未写入Word。

**当前稿件定位：** `D-P017`, `D-P039`, `D-P054`, `D-P102`, `A-P060`。首个检索锚点：

> Weather variables are matched to each incident using hourly reanalysis data from the Open-Meteo historical weather API [13], which is based on the ERA5 global reanalysis dataset [14]. Data a…

**证据来源：** SRC01 §2主干、§4 C01；SRC02 第3段及时间/并列条目；SRC03 §3.1及R02提示词。

**证据及边界：** H0主E0有8199/60437事件所选时间晚于最早记录；天气小时不同7810、日期不同2225，二者不是同一数量。旧代码按原行序drop_duplicates，天气按阶段开始匹配。报告转引v3_validation_pipeline.py原第64行；本环境未读其源码。

**具体修改：** §2新增事件时间基准和逐字段来源，天气/年月/分折/风暴归属均依规定时间重新构建。附录B写规则与并列处理。摘要、表1/3/4、所有相关图、附录系数和风暴数字登记受影响待重算。A-P060“weather predictors refer to incident onset”不能沿用为已证实旧实现。

**对故事和论证的影响：** 数据重构是证据链前提；不能以旧系数能复现为输入正确证明。

**生效条件与后续：** R02实际入口修复及旧新对照；R04重估，R05基线验收；正式科学主张再经V。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> Weather covariates were indexed to the earliest recorded start time under the incident-level reconstruction rule. This timestamp serves as a proxy for event onset.


### MR02｜时区、并列和跨边界规则

关联：C01, T02, T03, T07, L02, L05, L08。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P016`, `D-P017`, `D-P051`, `A-P013`, `A-P027`, `A-P060`。首个检索锚点：

> UKPN operates the electricity distribution network across London, the South East, and the East of England, and reports outage incidents to Ofgem, the energy regulator for Great Britain, unde…

**证据来源：** SRC02 时间/并列/35跨界事件条目；SRC03 §3.1。

**证据及边界：** 所有原时间含偏移；+01为128323行、+00为109578行。最早时刻并列24893事件，6项metadata冲突为0；6字段名称未在摘要列出。35事件跨2024-04恢复边界。

**具体修改：** 方法分开定义UTC绝对时间、业务日历、天气小时和研究截止；完整阶段先重构、再按事件起始纳入。附录给稳定raw身份+原行号并列规则及6字段范围。重核原32跨时段事件等H0数量；不能把不同边界的32和35当矛盾或互相替换。

**对故事和论证的影响：** 明确事件范围和时间排序，避免读者把记录起始或日级分组当真实物理独立过程。

**生效条件与后续：** R02解析/边界/并列检查；当前源码与实际合同路径随报告补齐。


### MR03｜未决事件身份与非重复记录

关联：C01, T03, L05, L11。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P016`, `D-P023`, `D-P029`, `D-P038`, `A-P024`, `A-P025`, `A-P027`。首个检索锚点：

> UKPN operates the electricity distribution network across London, the South East, and the East of England, and reports outage incidents to Ofgem, the energy regulator for Great Britain, unde…

**证据来源：** SRC02 两个FREP事件条目；SRC03 §3.2。

**证据及边界：** FREP-338321-Z跨2022-11-04至2023-05-11，cause98/71、MEI59/41；旧ID聚合B4508.933333h/C1，最早天气缺失。FREP-314454-J两行共享stage1/unique_identifier但cause71/87不同。全源完全重复行0。

**具体修改：** 内部保留ID和完整时间线；正式方法/附录B记录身份与原因冲突、模型资格和数量。原始保留与模型纳入分开。不可称188天连续失电，不自动拆分或按unique_identifier去重。模型资格若未决则留状态，别在正文写“全部事件已验证”。

**对故事和论证的影响：** 同ID可计算跨度不等于真实单次停电；避免用异常长事件夸大极端恢复故事。

**生效条件与后续：** R02按冻结资格规则处理并记录；实质未决继续限制解释，不凭本摘要填规则。


### MR04｜客户影响与恢复跨度的构造及验证边界

关联：T03, L05, C01。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P007`, `D-P023`, `D-P025`, `D-P028`, `D-P030`, `A-P003`, `A-P018`, `A-P020`, `A-P023`, `A-P025`。首个检索锚点：

> Outage impact can be measured by the number of customers affected, referred to hereafter as the exposure margin, or by the time needed for restoration, referred to hereafter as the recovery …

**证据来源：** SRC01 §2结果变量、§3.1；SRC02 契约摘要；SRC07既有修订。

**证据及边界：** 全量C/A/B按原公式复现；C完全一致，A/B仅约1e-13h误差。模型D为B，兼容Duration(hours)列仍对应A。空有效客户集合记缺失。1.97、93.02/47.13和500样本核对属于H0证据。

**具体修改：** 保留公式1/2的已修正含义，明确D为记录首末跨度，阶段不等同维修动作。重算最终样本上聚合/最早客户对照；审查#10最早客户规则与#9继承天气的不同。500核对可保留作实现检查，但源语义/特殊停钟仍另证。不可用C×D替代实际客户累计负担。

**对故事和论证的影响：** 两后果是不同工程性能维度；方法贡献以可靠定义和可追溯重构体现，不能宣称已识别全部中断负担。

**生效条件与后续：** R02输入与字段检查；R04样本相关统计；特殊业务语义未解则保持明确限制。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> The restoration outcome is the elapsed span between the earliest recorded start and the latest recorded end within an incident. It is distinct from customer-weighted interruption duration and customer minutes lost.


### MR05｜天气产品、缓存、时间窗与39.4m/s叙事

关联：C01, T02, L02。决定：撤回过强来源说法方向明确；最终描述按R02证据。落实：尚未写入Word。

**当前稿件定位：** `D-P006`, `D-P017`, `D-P040`, `D-P103`, `D-P138`。首个检索锚点：

> Storms and other extreme weather events are the most common cause of power disruptions in Great Britain [1]. In November 2021, Storm Arwen alone left more than one million customers without …

**证据来源：** SRC01 §2天气、§5输入语义；SRC02 定向天气条目；SRC03 §3.4。

**证据及边界：** 请求wind_gusts_10m、ms、GMT、未指定models；0.1度用于请求/缓存坐标。20定向行16有缓存/14文件，4缺缓存，attrs空；不能据此确定历史产品或全量缺失率。

**具体修改：** 撤回未经项目来源支持的ERA5、现场peak observed和本项目必为3秒瞬时阵风等确定说法。可按实际证据称历史API提供的阵风变量/代理，明确产品来源限制。附录列数值/缓存/产品来源三种状态、floor与降水窗口、坐标处理。39.4和Eunice事件/客户/时长须修复匹配后重核；一般风工程引用不证明缓存产品。

**对故事和论证的影响：** 阵风作为危险性代理服务事件后果分析，不能把分辨率未明的代理最低点提升为资产损伤阈值。

**生效条件与后续：** R01已有请求定位；R02全量对齐/可用性；来源若仍无法恢复需据实限定，不能用当前默认产品补历史。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> Gust covariates were obtained from the Open-Meteo historical API. The archived request configuration does not identify a specific underlying model.


### MR06｜gap定义从全国差值改为LAD内LSOA极差

关联：C06, T01, L01。决定：定义修正方向明确；原源定位待补入证据表。落实：尚未写入Word。

**当前稿件定位：** `D-P018`, `D-P040`, `D-P041`, `D-T02`, `A-T02`。首个检索锚点：

> Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise …

**证据来源：** SRC01 §3.3矩阵秩/仿射残差；SRC02 gap条目；SRC03 §2/§3.3。

**证据及边界：** H0设计矩阵26/28列满秩，实际gap对rate仿射拟合残差最大约0.161。R01报告原gap为LAD内LSOA rate极差，比例存储，.217对应21.7个百分点。

**具体修改：** 改正文§2.1/§2.4、表2、附录A2中“local minus national”的全部定义。区分输入比例尺度与展示百分点；不要直接乘100入模而不改系数说明。关闭“实际精确共线”猜测，保留源工作簿/列/单位的证据定位要求。

**对故事和论证的影响：** 从平均剥夺程度转向区内差异两个不同描述量；不把二者当独立因果社会机制或资产测量。

**生效条件与后续：** 可以形成确定方向的文字修订；本地原源字段/工作表路径需在台账补齐。新系数仍待R04。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> The deprivation gap is the range of LSOA-level income-deprivation rates within an LAD, stored on the proportion scale.


### MR07｜Moran的计算层级与未知空间权重

关联：T01, L01。决定：层级修正方向明确；权重不能填定。落实：尚未写入Word。

**当前稿件定位：** `D-P018`, `D-T02`, `A-T02`, `A-P011`。首个检索锚点：

> Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise …

**证据来源：** SRC02 Moran条目及未决项；SRC03 §2/§3.3。

**证据及边界：** R01报告Moran指LAD内LSOA剥夺聚集；具体空间权重未核实。当前A-P011写across neighbouring districts。

**具体修改：** 改为LAD内LSOA层面的聚集指标；明确不是中断残差Moran，也不识别LAD间效应。附录列来源和权重未决范围，不能猜邻接/距离/标准化方式，不能将proxy值当新LAD重算值。

**对故事和论证的影响：** 区域量是背景描述，不能以空间术语暗示估计了网络拓扑或故障传播。

**生效条件与后续：** 层级措辞按R01已报告定义修正；权重和合并地区重建分别待证。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> The Moran statistic summarises the spatial clustering of LSOA-level income deprivation within an LAD.


### MR08｜Buckinghamshire历史代理及后续重建决定

关联：T01, T11, L01, L12。决定：已有作者决定（由SRC02转述）；重建尚未完成。落实：尚未写入Word。

**当前稿件定位：** `D-P018`, `D-P041`, `D-P087`, `D-P089`, `A-T02`, `A-P013`, `A-T08`, `A-T09`。首个检索锚点：

> Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise …

**证据来源：** SRC02 Buckinghamshire条目/作者决定；SRC03 §3.3。

**证据及边界：** 四旧区简单平均rate .06325/gap .1875/Moran .30。H0主E/R1151/1146、天气293/292受影响。作者已决定暂保留显式历史代理，后续LSOA重建对照。C10是否对应该问题未提供，不能自行编号。

**具体修改：** 主文简述存在历史地区代理，附录A2增加例外和来源；图6及区域解释注明代理范围。保留数值身份、重新统计新成员。未来rate按正式分子/分母、gap按合并LSOA极差、Moran按合并值及权重分别重建；不把旧指标平均称等价官方新LAD统计。

**对故事和论证的影响：** 控制变量实际含义和地理可比性影响解释，不能因只一地区或n比例小就忽略。

**生效条件与后续：** PD03沿用；R02标记与计数，后续按已决定路线重建/对照；若不足应收窄区域解释。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> For Buckinghamshire, the current analysis retains an explicitly labelled historical proxy formed by averaging the corresponding values for four predecessor districts.


### MR09｜原因共识、分组来源与天气归因措辞

关联：T03, T06, L11, C01。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P038`, `D-P096`, `D-P097`, `A-P005`, `A-P007`, `A-T01`, `A-P070`。首个检索锚点：

> UKPN records a Cause Code for each incident. This paper groups the original codes into six analytical categories, with the mapping reported in Appendix A.2. The main sample retains the weath…

**证据来源：** SRC01 §2/§5；SRC02 原因独立共识/冲突；SRC03两事件及R02规则。

**证据及边界：** 原因不应随代表天气行任意变换；两ID有原因冲突。R01称已产出原因契约，但摘要未提供完整官方代码释义及冲突规则。

**具体修改：** 表A1加入原码释义/来源/映射和冲突处理，不把表内实施代码等同官方物理原因认证。§4.3“identifies weather as the direct cause”收窄为记录代码分类；R02后报告共识、冲突、未知的数量及资格。重算原因支持分布和所有天气人群比较。

**对故事和论证的影响：** 总体与天气人群是不同观察对象；不将原因选择当随机分组，不把支持变化识别为唯一机制。

**生效条件与后续：** R02实际分类/资格；官方释义未完全提供则保持边界；R04/V02更新相关结果。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> The weather-attributed subset is defined by the prespecified analytical grouping of recorded Cause Codes; conflicting assignments are handled under the documented incident-level rule.


### MR10｜样本流、p99与极端恢复总体

关联：C03, C05, T03, T04, L04, L11。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P002`, `D-P032`, `D-T01`, `D-P038`, `D-P039`, `D-P097`, `A-T03`。首个检索锚点：

> UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven named s…

**证据来源：** SRC01 §3.2及C03；SRC02 H0样本及48条差异；SRC03 R02样本流要求。

**证据及边界：** H0基础60453，E60437/R59834、天气9857/9758；天气R比主R中的天气9806额外排48条。主/天气p99分别192.083333/142.844667h；早期后期各自p99相加比合并重算少2条有实现解释。

**具体修改：** §2.4按实际处理顺序给唯一事件与逐步排除，目标可用/尾部/原因/天气/区域分别计数。区分真实长尾、无效和右删失；新留出训练内p99与测试总体分开。表1、图2及极端叙事全部用最终声明总体。旧N与截止只作H0对照，不作为修复目标。

**对故事和论证的影响：** 研究“极端恢复”必须有真实长尾证据；筛掉最长1%之后的结论不能无条件覆盖全事件。

**生效条件与后续：** R02候选样本流；R03/R04冻结且运行比较口径；V01长尾敏感性。


### MR11｜标准化、固定效应、VIF与系数尺度

关联：C06, C09, T01, T11, L01。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P040`, `D-P041`, `D-P057`, `D-P060`, `D-P061`, `D-P064`, `A-P065`。首个检索锚点：

> The full covariate set comprises gust speed and its square, an interaction between gust speed and mean sea level pressure, 24-hour cumulative precipitation, temperature, mean sea level press…

**证据来源：** SRC01 §2模型/推断、C06/C09；SRC02保持部分标准化。

**证据及边界：** 标准化天气四列和恢复客户列；区域保留原尺度、人口取log。年月为两套加性哑变量，均值模型无LAD固定效应；LAD是协方差聚类。旧VIF未含年月哑变量，step26生产者未定位。

**具体修改：** 将Continuous predictors are standardised具体化到变量清单；表2/A2增加单位/变换。VIF说明诊断列集合、截距与编码，删去不必要的阈值辩护；不外推“所有列<4”。保留已正确写明的年月加性、协方差不改OLS系数。

**对故事和论证的影响：** 避免把不同尺度的系数直接比较成工程重要性；保留原规格便于修复对照，而非迎合旧文字改全部标准化。

**生效条件与后续：** 措辞方向明确；R03补生产者/合同，R04更新诊断和系数。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> Weather predictors were standardised, as was log(1 + affected customers) in the recovery model. Regional covariates retained their specified original or log-transformed scales.


### MR12｜合并OOF R²与平均折R²

关联：C02, T06, T07, T09, L07, L10。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P054`, `D-P084`, `D-P086`, `D-P101`, `D-T04`。首个检索锚点：

> Five-fold cross-validation groups incidents by start date, so all incidents starting on a given day enter the same fold. For each comparison, models are fitted on four folds and evaluated on…

**证据来源：** SRC01 §3.3评分表、C02；SRC02 pooled OOF契约。

**证据及边界：** 实际先拼接OOF后评分。H0天气R pooled .215581756，简单平均折 .161713733，差5.3868个百分点；主R .110536591/.107366738。不是同一指标两个名称。

**具体修改：** §3.2写明确的合并OOF定义：1−Σ(y−ŷOOF)^2/Σ(y−ȳeval)^2；所有图题/正文改相同名称。逐折评分可另报告，不冒充独立实验。对预测基准另写训练内估计；评分分母的评估均值不等于用评估均值作训练预测器。

**对故事和论证的影响：** 预测比较需要共同评分规则；不根据哪种值更大选择指标，也不将百分点误写为客户/小时变化比例。

**生效条件与后续：** R03评分接口；R04/V02产生当前预测；定义可先记录，不将H0数值替换成未经运行的新结果。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> Out-of-fold predictions were pooled across folds, and R-squared was calculated from the pooled residual sum of squares and the total sum of squares of the corresponding evaluation sample.


### MR13｜贡献排序反转的配对条件与分支

关联：C02, C03, T06, L07, L11。决定：核心结论条件于新结果。落实：尚未写入Word。

**当前稿件定位：** `D-P002`, `D-P010`, `D-P084`, `D-P094`, `D-P097`, `D-T04`, `D-P100`, `D-P108`, `D-P119`。首个检索锚点：

> UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven named s…

**证据来源：** SRC01 C02/C03；SRC05 L07；SRC06 T06。

**证据及边界：** H0同一样本内部嵌套比较已配对，但主/天气另算p99和分折。1.43对1.28个百分点来自不同加入条件，不应随意挑端点代表独有贡献差；范围是加入顺序而非区间。

**具体修改：** 主比较用共同B、完整gust组G、客户组K的四模型。G按规格包含gust、平方及gust×pressure，K包含标准化log(1+C)及平方，P主效应留在B。I_G=R²(BGK)−R²(BK)，I_K=R²(BGK)−R²(BG)，Δ=I_G−I_K。主/天气共享全局过程划分，重叠样本联合处理。表4/图5/8改为配对差与不确定性加另列顺序。摘要/结论按稳定反转、接近且点反转、无稳定反转三路写。

**对故事和论证的影响：** 研究重点是特定信息条件下的增量，而非风或客户的因果份额和普遍支配地位。

**生效条件与后续：** R03/R04口径修复后，V02配对推断和支持检查；分支由结果决定。


### MR14｜日分组与完整天气过程依赖

关联：C01, C03, C05, T07, L08。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P011`, `D-P051`, `D-P054`, `D-P102`, `D-P105`, `D-P114`, `A-P057`, `A-P060`。首个检索锚点：

> Addressing both questions requires an observational record long enough, and varied enough, to include both routine operating conditions and a number of distinct severe wind events within the…

**证据来源：** SRC01 C01/C03/C05及历史#9–#19；SRC05 L08；SRC06 T07。

**证据及边界：** 旧主/天气日期折分不能对应；窗口在2月17/19重叠。七个名字不等于七个独立过程。早期开发用过后来时段，#19为后期重新拟合不是早期模型预测后期。

**具体修改：** 方法明确回顾性日期诊断与最终完整过程/块评价的区别；合并相关风暴窗口、处理跨边界恢复，报告事件/过程权重。图3统一earlier/later标签，避免保留confirmation后反复免责。保留开发事实，不能因新划分锁定就恢复独立确认身份。

**对故事和论证的影响：** 工程过程和恢复资源可能跨日，验证单元应对应问题；不强制取得全新外部数据才允许回顾性研究完成。

**生效条件与后续：** R02时间/成员；V00/V02方案与结果；历史限定可确定记录。


### MR15｜图9暴露侧多做一次log1p

关联：C04, T09, L10。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P061`, `D-P103`, `D-P105`, `D-P106`, `A-P091`。首个检索锚点：

> Year and month effects enter as separate dummy-variable sets, not year-by-month interactions. The exposure and recovery equations describe conditional log-scale responses. Let ηi denote a fi…

**证据来源：** SRC01 C04。

**证据及边界：** step13及figure9从pred=exp(η)再算log1p(pred)，得到log(1+expη)而非η。H0确定性对照相关.179335982→.179728832；log MAE1.717499382→1.690321118；平均位移.116592479。

**具体修改：** 图9横轴log(1+C)、纵轴直接η，图数据和MAE共同修代码。正文观察值分组的偏差解释需重审；旧相关接近不代表尺度正确。不要把这一步修复称smearing校准，也不把H0修正值当新事件匹配后的结果。

**对故事和论证的影响：** 先保证预测与观察同尺度，再讨论工程误差。

**生效条件与后续：** R03生产者修复、R04当前版本重生图；V03才评价留出校准。


### MR16｜图9恢复样本混合与窗口重复

关联：C05, T04, T07, T09, L04, L08, L10。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P102`, `D-P103`, `D-P105`, `D-P106`, `D-P107`, `D-P108`。首个检索锚点：

> Storm periods provide a complementary view of fitted performance. Previous outage research has used named storms for model evaluation [5], but the comparison here is descriptive because the …

**证据来源：** SRC01 C05。

**证据及边界：** 恢复风暴评价含训练时p99删掉的长事件，七窗口分别1/2/22/9/3/5/7条不在拟合样本。窗口重叠不能直接相加为独立事件数。当前图题称所有事件also contributed to fitting不准确。

**具体修改：** 先输出训练/评价成员及唯一事件数。描述图题改为拟合内与额外尾部混合的事实，最终若以V过程评价替换则按新身份写。不要通过删除长尾把现有图包装成纯训练内，也不能据部分未训练点称独立风暴留出。重算27日、8.15%、14.72%等组成。

**对故事和论证的影响：** 风暴章节的任务是过程表现及范围，不是排序反转的第二份独立证明。

**生效条件与后续：** R02成员、R03标记、R04描述更新；V02/V03替换为合格评价后再定正文地位。


### MR17｜曲线、地图与参考人群的数学含义

关联：C07, T09, L10。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P061`, `D-P077`, `D-P079`, `D-P087`, `D-P089`, `D-P093`, `A-P091`, `A-P092`。首个检索锚点：

> Year and month effects enter as separate dummy-variable sets, not year-by-month interactions. The exposure and recovery equations describe conditional log-scale responses. Let ηi denote a fi…

**证据来源：** SRC01 C07；SRC02 图参考顺序；SRC03区分参考要求。

**证据及边界：** R0c曲线客户z约0但z²均值.999983287；地图两项皆0。仅该参考差让曲线水平相对z=0情景约乘.672957。不同参考不影响同一曲线的极值比或顶点，但影响水平。

**具体修改：** 具体场景从原变量生成一致设计行；平均参考由个体一致设计行平均。图题说明固定情景或参考人群、压力和反变换顺序。不能一律把平方均值改0，也不能把平均η、exp平均η、平均expη都称平均后果。不同图若确有不同目的允许不同参考并解释。

**对故事和论证的影响：** 工程量级必须能回答“对什么事件/人群、在什么条件下”的问题。

**生效条件与后续：** R01已定参考需读取细则；R03统一接口，R04重生图，V03给场景证据。


### MR18｜二次形状、GLM与三阶反向线索

关联：T05, T11, L06。决定：条件于修正输入的形状证据。落实：尚未写入Word。

**当前稿件定位：** `D-P010`, `D-P044`, `D-P046`, `D-P048`, `D-P066`, `D-P068`, `D-P118`, `A-P094`。首个检索锚点：

> This study addresses two questions within that operational setting. First, is there a consistent nonlinear association between gust intensity and the consequences of recorded outages, and ho…

**证据来源：** SRC01历史#38–#43；SRC02 E0三阶OOF增量；SRC05 L06；SRC06 T05/T11。

**证据及边界：** 旧E0三阶项OOF增量约.001441，原代码核查明确其为反向证据。正二次项和相同二次预测子的GLM只支持指定形式内曲率，不充分验证U形或最低点稳定。

**具体修改：** §3先说估计目标与候选形状，§4.1先比较线性/二次/一种样条、损失、支持量和影响过程。读取旧三阶完整设置；修正输入上重估保留检查或用预定灵活形式回答同一形状问题。不能因输入修复就删除反向记录，也不能直接沿用旧增量为B1。

**对故事和论证的影响：** 模型形式是待检验假设，允许论文结果变成“无稳定最低点”或“简单形式足够”。

**生效条件与后续：** R04标记旧检查与重算覆盖；V01定稿；摘要主张CL02条件决策。


### MR19｜最低点与物理单位不确定性

关联：C08, T10, L09。决定：最低点地位待结果；旧区间撤回不得回归。落实：尚未写入Word。

**当前稿件定位：** `D-P002`, `D-P071`, `D-P073`, `D-P075`, `D-P079`, `D-P118`, `D-P120`, `A-P076`, `A-P080`, `A-P083`, `A-P086`。首个检索锚点：

> UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven named s…

**证据来源：** SRC01 C08；SRC04 M03/M05（解释需结合SRC07）；SRC07既有校准；SRC06 T10。

**证据及边界：** H0均压最低点10.694m/s，压力±1SD为9.656/11.732。旧Bootstrap各次重估尺度；#43仍缺β3和pressure均值/SD，不能恢复固定物理压力区间。图4脚本仍硬编码9.20–12.06。

**具体修改：** 先修脚本停止旧区间回填。若保留最低点，固定p0，每次配套β1/β2/β3及gust/pressure尺度换回物理值再汇总，并报告β2≤0/越界/失败，明确条件范围。若形状/位置不稳则撤出摘要，附录只留合格描述与必要公式，不继续论证旧Delta差异成因。

**对故事和论证的影响：** 最低点是条件拟合特征；科学投入与其最终地位一致，不能当损伤或操作阈值。

**生效条件与后续：** R03接口；V01决定地位；V03条件补区间；W用新结果。


### MR20｜分时段系数、尺度和CV汇总身份

关联：C08, T11, L08, L09。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P055`, `D-P111`, `D-P112`, `D-P114`, `D-P115`, `A-P061`, `A-P063`, `A-P089`。首个检索锚点：

> The exposure minimum was first estimated as 10.69 m/s before temporal separation. Restricting the analysis to the earlier-period exposure sample (n = 48,323) changed the estimate to 12.13 m/…

**证据来源：** SRC01 历史#19/C08；SRC04时段核实；SRC07既有修订。

**证据及边界：** H0开发R点.0660是重叠CV逆方差汇总，后期约.064、合并.079237不同估计身份；旧名义.0587–.0732不可当独立拟合区间。后期#19是重新拟合，独有样本内贡献。

**具体修改：** 保留正式时间比较需同目标/规格的早晚完整拟合及共同物理参考；标准化二次系数的物理曲率β2/sv²另行说明。原CV汇总若保留只作历史描述，不和其余三行组成四份独立验证。图10旧区间生成代码同步禁用。

**对故事和论证的影响：** 区分样本稳定性与真正未来泛化，避免一正一不显著证明不同或多次同号证明独立重复。

**生效条件与后续：** R03生产规则；R04可比拟合，后续过程推断V；不保留图则内部归档。


### MR21｜阶段组成、缺首阶段与客户—跨度关系

关联：T03, T11, L05, L11。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P032`, `D-P036`, `D-P080`, `D-P121`, `A-P027`, `A-P035`, `A-P044`, `A-P048`, `A-P050`, `A-P052`, `A-P054`, `A-P055`。首个检索锚点：

> Table 1 reports descriptive statistics for affected customers and restoration duration in the final analysis sample, on the original scale and after log transformation. Both variables are he…

**证据来源：** SRC01 §5其余科学实验；SRC02契约及未决；SRC05 L05/L11；SRC07既有修订。

**证据及边界：** 缺首阶段H0 E8817/60437、R8671/59834、天气2593/9857和2578/9758；不是全源10.56%。附录D混有开发n47840与合并n59834，阶段数又不等同维修动作且最终值事后形成。

**具体修改：** 更新最终样本阶段质量比例；排除/单列质量敏感性依据合同。D表、图、分箱用同一目标或清楚区分；给稀疏格n和完整导数/范围判断。保留非单调与组成关联，不把线性项符号等同全域单调，不把阶段控制当必然正确的因果调整。

**对故事和论证的影响：** 阶段数据解释工程流程的边界要真实；不能把分层结果写成优先调度或唯一中介机制。

**生效条件与后续：** R02质量标记；R04当前保留材料；V01质量敏感性、V03补工程解释。


### MR22｜最终客户数与可用信息时点

关联：T08, L03。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P007`, `D-P012`, `D-P040`, `D-P058`, `D-P080`, `D-P094`, `D-P119`, `D-P124`, `A-P003`, `A-P052`。首个检索锚点：

> Outage impact can be measured by the number of customers affected, referred to hereafter as the exposure margin, or by the time needed for restoration, referred to hereafter as the recovery …

**证据来源：** SRC02最终C/原因契约；SRC05 L03；SRC06 T08。

**证据及边界：** C沿完整阶段聚合，阶段数和原因可能事后形成；最早阶段客户记录也不自动是故障开始时已知初始客户估计。

**具体修改：** 方法新增变量可用时间表；恢复模型命名为以最终规模为条件的回顾性分析。明确天气历史数据也不等于当时预报。只有另选初期预测目标且有可信输入才拟合新信息集；贡献差不能推成预部署资源变量优先级。

**对故事和论证的影响：** 同一公式在事后解释和初期预测中承担不同任务，工程用途由信息时点限定。

**生效条件与后续：** R01已产时间表需补路径细则；V03核实用途；候选命名无需等显著结果。

**英文候选措辞：** 下句为修订草案，只有对应定义/实施证据满足后才能以完成时写入正式稿；本轮未落稿。

> The recovery analysis conditions on final reconstructed customer impact and is therefore retrospective; it does not evaluate a forecast available at incident onset.


### MR23｜工程量级、误差与校准

关联：C04, C05, C07, T09, L10。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P061`, `D-P077`, `D-P090`, `D-P103`, `D-P106`, `D-P107`, `D-P122`, `A-P091`, `A-P092`。首个检索锚点：

> Year and month effects enter as separate dummy-variable sets, not year-by-month interactions. The exposure and recovery equations describe conditional log-scale responses. Let ηi denote a fi…

**证据来源：** SRC01 C04/C05/C07；SRC05 L10；SRC06 T09。

**证据及边界：** 原图4/6为expη无反变换校正；暴露不减1。按真实值分组的收缩和相关系数不能替代校准；全样本残差因子10.46/2.20不证明条件均值校正。

**具体修改：** 用V留出预测给训练基准、同尺度误差、按预测值分组校准和支持内场景。若声称原尺度算术均值，使用训练内且经检验的反变换/均值模型；否则明确exp拟合log量。不能让corr小差异掩盖C04尺度错误，或用观测值分组证明低风险失准。

**对故事和论证的影响：** 统计发现应提供读者可理解的量级，同时承认误差与后果定义；不强制复杂决策优化。

**生效条件与后续：** R03/R04修尺度；V03工程表和校准；W据实际目标写。


### MR24｜图6/7是否推进主问题

关联：T09, T14, L10, L12。决定：结构建议待审，数值条件于重算。落实：尚未写入Word。

**当前稿件定位：** `D-P087`, `D-P089`, `D-P090`, `D-P092`, `D-P093`。首个检索锚点：

> Figure 6 compares regional variation in exponentiated fitted log responses, holding the non-regional predictors at the reference settings used in the original map calculation. The exposure a…

**证据来源：** SRC01 C07；SRC05 L10/L12；SRC07图尺度修复。

**证据及边界：** 当前地图拟合面相关−.780/−.758及网格max/min2.79/2.37/5.99均依参考/样本。网格比不是端点比、因果重要性或原尺度均值倍数，地图又含历史区域代理。

**具体修改：** 先判断是否推动CL05。若保留，更新来源/场景/支持及当前数值，图题精确定义；若只重复重要性排名或引出不必要机制推测，移附录或删除。保留内部图数据与旧解释变更史。

**对故事和论证的影响：** 主文图表围绕工程问题；不为原有图数与外观保留无法支撑论证的对照。

**生效条件与后续：** R04当前图；V03量级证据；V04/W作者定去留。


### MR25｜生产者、旧图回填与数字单一来源

关联：C08, C09, T11, T14, L12。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P041`, `D-P048`, `D-P079`, `D-P114`, `A-P065`, `A-P094`。首个检索锚点：

> Variance inflation factors for all continuous covariates in the final model specification are below 4, with the highest value, 3.76, corresponding to the gap between local income deprivation…

**证据来源：** SRC01 C08/C09；SRC02环境/保护复核；SRC08 R03–R05。

**证据及边界：** 旧读取/构建函数有覆盖副作用，图4/10会回填撤回内容；step26/27/28生产者缺口；旧.venv失效而审计环境可用。当前Word像素未在新审计核对。

**具体修改：** 修订台账登记每图表的活动生产者、输入/模型版本与最终Word嵌入身份。旧图/系数禁自动回填。保留结果若缺生产者就重建可证实方法或暂撤；不在论文中罗列路径/环境修复史，正式附录给当前可复现配置。

**对故事和论证的影响：** 正文正确措辞必须与再次运行能生成的内容一致，技术修复服务科学可复现。

**生效条件与后续：** R03代码、R04产物、R05复审，W01再核代码—图表—Word一致。


### MR26｜主线、章节及修复历史分工

关联：T14, L12。决定：记录规则已获明确授权；具体重组为待审建议。落实：尚未写入Word。

**当前稿件定位：** `D-P002`, `D-P010`, `D-P013`, `D-P048`, `D-P055`, `D-P074`, `D-P075`, `D-P118`, `D-P123`, `A-P056`, `A-P078`, `A-P086`, `A-P094`。首个检索锚点：

> UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven named s…

**证据来源：** SRC05 L12/建议叙事；SRC08工作定位；USER-PD02本轮记录要求。

**证据及边界：** 当前多次解释旧错误、未提供材料与非独立，摘要仍押最低点和反转。修复史有内部追溯价值，但不能代替工程发现与最终方法。

**具体修改：** 按本台账§2–§4重排职责。正式方法集中交代真实开发限制；结果接受CL分支；内部保存旧百分比、复现误差、旧区间和缺材料历史。正式附录用最终合格证据替换“supplied revision/still required”等过程句，不以删除过程句隐藏仍保留主张的缺证。

**对故事和论证的影响：** 每轮增加台账与变更历史，不把主文叠成审查日志。六章方案/图去留需作者审阅，不能冒称已决定。

**生效条件与后续：** 当前可记录方案；R/V持续更新，V04作结果裁决，W落实。


### MR27｜文献、数据来源及术语引用

关联：T01, T02, T03, T14, L02, L11, L12。决定：明确修正方向；结果部分待重算。落实：尚未写入Word。

**当前稿件定位：** `D-P006`, `D-P008`, `D-P016`, `D-P017`, `D-P018`, `D-P136`, `D-P138`, `D-P142`, `A-P007`, `A-T02`。首个检索锚点：

> Storms and other extreme weather events are the most common cause of power disruptions in Great Britain [1]. In November 2021, Storm Arwen alone left more than one million customers without …

**证据来源：** SRC01未核实源定义；SRC02未决model/权重/业务语义；SRC05来源边界。

**证据及边界：** 本轮源报告有实际工作簿/请求线索，但未收到全部原产物；Word参考文献仍有date/URL unverified，官方代码释义/天气产品/权重部分未明。

**具体修改：** 建立主张—原始来源表，不把审计报告当最终官方来源。文献对照记录分析单位、后果、信息时点、验证单元、工程目的，避免无依据“首次”。引用核实到内容及元数据；取不到来源则明确收窄对应主张，不编引文。

**对故事和论证的影响：** 研究贡献靠与同类问题的实质比较，不靠数学复杂度或数据来自英国自动成立。

**生效条件与后续：** R阶段补实际来源路径；W前完成保留主张引用核实；本轮未新增外部文献核查。


### MR28｜C10及本地细则尚未回传

关联：C10, T14, L12。决定：待澄清；候选定位不可直接用于改稿。落实：尚未写入Word。

**当前稿件定位：** `D-P018`, `A-T02`。首个检索锚点：

> Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise …

**证据来源：** SRC02末段C01–C10表述；SRC03提示词A项。

**证据及边界：** 摘要提C01–C10，但没有C10标题、根因和证据。contracts/UNRESOLVED_DEFINITIONS.md与R00/R01详报未附。本条Word位置仅为若C10涉及区域时的候选，不是已确定影响。

**具体修改：** 下一份本地报告附C10原条目、所有未决定义的最低缺件及合同索引；不能擅自将C10命名为Buckinghamshire问题。本台账先保留未定映射槽，收到证据再追加入具体章节改法。

**对故事和论证的影响：** 避免跨上下文时把猜测变成一个已确认问题，保留信息缺口本身。

**生效条件与后续：** R02返回补齐后更新；不阻止其他已确定修复。



## 6. 图表、公式与旧数值的联动清单

| 对象 | 当前定位 | 本轮决定/依赖 |
|---|---|---|
| 图1/图2/表1 | D-P021/P035、D-T01 | 随修正样本重生成；说明分母和恢复总体；MR01/MR10 |
| 图3 | D-P053 | 更新时段及过程标签；七名字不等于七独立过程；MR02/MR14 |
| 表2/附录A2 | D-T02、A-T02 | 改gap/Moran、列单位/变换/代理/来源；MR05–MR11 |
| 表3/附录F1/F2 | D-T03、A-T08/T09 | 全部受时间/输入影响，待当前模型重算；不能只改表头 |
| 图4/附录H1/H2 | D-P079、A-T11/T12 | 修参考、停旧区间；最低点条件于V；MR17–MR19/MR25 |
| 图5/图8/表4 | D-P086/P100、D-T04 | pooled OOF名称、统一比较、配对Δ和区间；MR12/MR13 |
| 图6 | D-P089 | 代理、参考与指数拟合量；当前地图相关需重算；去留待审 |
| 图7 | D-P092 | max/min网格定义保持，数值/参考需新证据；去留待审 |
| 图9 | D-P105 | 暴露η尺度、恢复成员、唯一过程、误差/校准；MR15/MR16/MR23 |
| 图10 | D-P114 | 可比时段拟合与尺度；不得重生旧CV名义区间；MR20 |
| 附录C1/D1/D2/图D1/G1 | A-T03/T04/T05、A-P046、A-T10 | 样本/分箱/原因/时点受影响，重算保留项并标支持 |
| 公式1/2 | D-P025/P028 | 保留C与跨度定义，补身份/空集合/边界；不要因聚合复现就认证业务语义 |
| 公式3/4 | D-P045/P059 | 区分log目标、预测子、标准化/其他原尺度列；形状为候选而非既定真值 |
| 公式5及附录H转换 | D-P072、A-P084/P085 | 条件压力与物理尺度配套；若最低点降级可缩短，公式正确部分不倒退 |

### 6.1 H0数值登记：可追溯，不是新终稿数字

| 历史量 | 来源 | 当前用途 |
|---|---|---|
| 基础60453；主E/R60437/59834；天气9857/9758 | SRC01 §3.2；DOC01 | 修复前对照，等待新样本 |
| p99早期194.795833、后期167.365333、主192.083333、天气142.844667h | SRC01 §3.2/C03 | 解释旧配置；不当新截止默认值 |
| E0最低点10.694，压力±1SD时9.656/11.732m/s | SRC04/SRC07、DOC02 H1 | H0拟合描述；非已验证损伤阈值 |
| E0旧三阶OOF增量约.001441 | SRC02 | 反向线索，模型/协议需原产物补齐；非B1验证 |
| pooled OOF主E/R .028123975/.110536591；天气 .020103347/.215581756 | SRC01 §3.3 | 历史评分身份；当前不能混称平均折R² |
| 天气R平均折 .161713733 | SRC01 §3.3 | 指标差异示例；不据较大数值选择标准 |
| 93.02/47.13与1.97倍 | DOC01 §2.2；DOC02 B1 | 需在新最终样本重算 |
| 39.4m/s、Eunice1601事件/376712客户/52.7h | DOC01 D-P006 | 待新匹配、成员和来源核查，不保留现场实测断言 |
| 七窗口27日、8.15%事件、14.72%客户 | DOC01 D-P102 | 唯一日/事件口径与新风暴成员重核 |
| 2.79/2.37/5.99及地图−.780/−.758 | DOC01 D-P087/P090 | 条件拟合量；数值待重算，图去留待审 |

以上不是最终全部数字总账。后续本地总账应覆盖每个保留表/图/主张，记录完整数值、单位、样本、模型、配置、生产者、时间及替代历史值。

### 6.2 已修复内容保护清单

二次式关于自身顶点对称；19%–48%的gust-only η比不能称后果百分比；一次项不显著不否定数学最低点；压力交互进入条件最低点；β₂所有抽样为正不等于都显著；分子近零不独自证明重尾成因；每次重估尺度不自动更保守；图4/6 expη不自动是条件算术均值；暴露减1与比例不能随意交换；图7是网格极值比；旧CV汇总区间已撤回；历史后期数据参与开发事实保留。依据SRC07和当前Word对应段落。

这些内容可在最终结构中压缩或移动，不能在精简、重新生成图表或更新模型时恢复旧错误。R02输入修复也不会自动证明上述已明确的限制不再需要。



## 7. 后续每阶段同步记录的固定流程

### 7.1 单一工作记录与阶段快照

本地规范位置：`paper_revision_work_v2/manuscript_record/`。首次从本记录包初始化；如果已存在更新版本，只合并新增来源与变更，不覆盖当前台账。完整包中的MANUSCRIPT_LEDGER.md是主入口，REVISION_ITEMS.json保存同一批MR条目便于检查和更新。

每阶段结束都做：

1. 将新返回报告/配置/必要结果作为新来源登记，保存原文件名、唯一快照名和哈希；SRC02这样的旧RETURN快照不被下一次同名报告覆盖。
2. 按MR条目更新新证据、旧结论是否变化、影响哪项CL、哪一章/段/图/表、具体替换/迁移/删除方案、生效条件和状态。
3. 更新主线与逐章职责：如果新证据改变最低点/排序/工程用途，明确摘要、RQ、结果、讨论、结论要如何联动；不是只在一条issue里改“已完成”。
4. 记录决定来源：作者确认、已有本地决定、分析建议、条件分支分开。反例和被否定方案保留历史，不因新结果不利而删掉来源。
5. 追加CHANGELOG并生成`stage_snapshots/<stage>_<run_id>/`快照；各阶段报告新增“对稿件的影响”部分，返回包同时含最新台账、变更摘要和必要新增来源。

### 7.2 每阶段最小正文影响表

| MR/CL | 新证据及版本 | 对原判断的影响 | 章节/段落/图表 | 具体拟改内容 | 生效条件 | Word状态 |
|---|---|---|---|---|---|---|
| 实际填写 | 实际填写 | 保留/收窄/删除/改方法/无变化 | 旧定位+拟新定位 | 不写笼统“以后修改” | 具体结果或决定 | 未落稿/待复核/已核对 |

没有影响也要列出检查过哪些相关MR及“无变化”的理由；不能把所有阶段机械写成整篇重写。

### 7.3 阶段对应的写作记录重点

| 阶段 | 台账必须同步的内容 |
|---|---|
| R02 | 事件/时间/天气/原因/人口/代理/样本变化；§2和附录A/B方案；C10真实条目 |
| R03 | 评分/参考/图件生成/模型契约；§3、图题和可复现附录方案 |
| R04 | 新旧n/系数/预测/诊断；全部受影响结果段和图表；不能将B1当V结论 |
| R05 | 输入/生产链是否闭合；对故事与后续补证优先级的影响 |
| V00 | 冻结估计目标、信息集、评价和推断；方法与限制的拟定结构 |
| V01 | 形状/长尾/阶段质量分支，CL02与最低点地位 |
| V02 | 配对贡献/过程稳定性，CL03/CL04、表4/摘要/结论分支 |
| V03 | 工程量级/校准/信息时点及条件实验，CL05/CL06 |
| V04 | 对所有主张作证据裁决，记录作者决定与最终逐章改法 |
| W00 | 按台账落实Word；记录新定位、图表版本与逐项差异 |
| W01 | 从完成稿回查每条MR/CL；未关闭问题进入最终待补清单 |

### 7.4 本地Codex追加提示词

```text
请在执行当前研究阶段时同步维护论文修订记录。
先读paper_revision_work_v2/manuscript_record/MANUSCRIPT_LEDGER.md和最新CHANGELOG；
若尚未初始化，从本次paper_manuscript_record记录包或交接包的manuscript_record_seed复制，
不得覆盖本地更晚的台账。

当前阶段仍按R/V/W原范围执行；R/V更新修订计划不等于修改Word。
每个新发现都登记来源快照/哈希、MR与CL、旧判断、新证据、具体章节与段落/图表改法、
论证影响、生效条件和状态。没有原产物时保持“报告已核实/本环境未读”的证据层级。
读取本地已存在但本对话未收到的contracts/结果时，补齐准确来源，不猜文件名或C10含义。
新结果否定旧主张时保留反向证据与修订历史；作者决定与建议分开。
更新正文故事、各章职责及所有联动位置，不只改变issue完成状态。
生成阶段“稿件影响表”、最新主台账及阶段快照，随RETURN_TO_CHATGPT一并返回。
R/V期间Word状态继续为未落稿；只有W实际修改且复核后才更新落实状态。
```

## 8. 待补来源与本次记录变更

尚未收到：R00/R01详报、contracts及UNRESOLVED_DEFINITIONS、C10正式条目、原工作簿/列名/空间权重、天气缓存及原请求元数据、事件/折分/图件审计CSV、代码版本与实际修改文件。它们已由报告指向本地，不应再被默认为不存在；后续回传最小支撑材料或可读摘要，并补进来源表。

本次已记录但尚未实施：MR01–MR28全部；CL01–CL06证据分支；当前正文/附录组织图；图表与旧数字联动；PD01–PD07决定身份；R02及以后每阶段的更新规则。R02未运行、Word未改、外部文献未新增核查。


## 9. 来源索引与固定版本

| ID | 原文件 | 包内快照 | 证据角色 | SHA-256 |
|---|---|---|---|---|
| SRC01 | 代码流程核查与研究推进脉络.md | [evidence/SRC01_code_audit_20260905.md](evidence/SRC01_code_audit_20260905.md) | 初步代码核查；已读报告，未在本环境读取其全部本地底层产物 | `2479a2d139045dfdcc3f7a52909682e61bca1fb74617c645e57bc6c31f505b55` |
| SRC02 | RETURN_TO_CHATGPT.md | [evidence/SRC02_R00_R01_return_20260905.md](evidence/SRC02_R00_R01_return_20260905.md) | R00–R01返回摘要；本轮S0-1按上下文对应R00–R01，不作为另一次独立审计 | `0da24b04b188f17f7451528fe759dd56d81d7711d25faad951997639c5c37850` |
| SRC03 | R00_R01审阅与R02执行指令.md | [evidence/SRC03_R00_R01_review_R02.md](evidence/SRC03_R00_R01_review_R02.md) | 本对话已给出的R00–R01审阅与下一步指令；是分析意见，不是新实验 | `2edead79992d5b25ad08ea42b464fa82d350be50a514c50455422c41992b2f45` |
| SRC04 | 50_数学审查本地核实.md | [evidence/SRC04_local_mathematical_audit.md](evidence/SRC04_local_mathematical_audit.md) | 早期本地数值核实；其中部分数学解释已被后续审查纠正 | `866310ac63024196065780e7715369be23b7b6065b300d9025d50424906daf17` |
| SRC05 | 最终逻辑审查_工程统计视角.md | [evidence/SRC05_logic_review.md](evidence/SRC05_logic_review.md) | L01–L12原逻辑审查；部分疑点已由SRC01/SRC02更新 | `5424932ffa934adcf46dd6c81b9910fbd36e09f759ddf304c639be56b76cd59d` |
| SRC06 | 补充实验与计算_人工确认清单.md | [evidence/SRC06_validation_worklist.md](evidence/SRC06_validation_worklist.md) | T01–T14原补证清单 | `8cf39a22f47a4518b114ae76648d0628c2fd1d7fe63d175e3833953bd145f267` |
| SRC07 | 修订审查与待补分析.md | [evidence/SRC07_previous_revision_log.md](evidence/SRC07_previous_revision_log.md) | 原Word→用户Markdown→当前Word的既有修订记录 | `6c0a485a7b5ef6447f392cd15ec5c639803f7b909c4b9ea928c03926437599ae` |
| SRC08 | 本地Codex接管_分步计划与提示词.md | [evidence/SRC08_execution_plan_before_ledger.md](evidence/SRC08_execution_plan_before_ledger.md) | 加入本台账前的v2执行计划快照 | `41c5158b05bdb74f8720861fb88870feb657f868bc9f85fa919f236fac209241` |
| DOC01 | Draft_revised.docx | [evidence/DOC01_main_baseline.docx](evidence/DOC01_main_baseline.docx) | 当前正文基线；本轮只读、未修改 | `196cef4abcdf4e6723b55035049c08de75613c3cc5a56314b264490f70e5926c` |
| DOC02 | Appendix_revised.docx | [evidence/DOC02_appendix_baseline.docx](evidence/DOC02_appendix_baseline.docx) | 当前附录基线；本轮只读、未修改 | `55f5c4f30fc75473d9da354b2819d3f8298904b8be94104ca3e107276696af8c` |
| OLD01 | Draft(2).docx | [evidence/OLD01_original_main.docx](evidence/OLD01_original_main.docx) | 最初正文，用于历史追溯 | `bd9169585a1e894610b17b8ecfc82f2eb3021a6b889716f62072a989cbb199e7` |
| OLD02 | Appendix(6).docx | [evidence/OLD02_original_appendix.docx](evidence/OLD02_original_appendix.docx) | 最初附录，用于历史追溯 | `317459a9d4e93cf399e03ccea688a053e02af0c522c469376956c953fb62bc5b` |
| OLD03 | Paper1_Introduction_draft (6).md | [evidence/OLD03_user_main_revision.md](evidence/OLD03_user_main_revision.md) | 用户前期措辞修改稿 | `bbd8afd44085dde4c3c8c9a086e106b1c8c6fa199b300cc478f8d0997d8ace46` |
| OLD04 | Paper1_Appendices (1).md | [evidence/OLD04_user_appendix_revision.md](evidence/OLD04_user_appendix_revision.md) | 用户前期措辞修改附录 | `366477c8751d95150e6ae54fa175f6f4a408a046db7a783611957e59da1146b8` |

USER-PD02为用户本轮在本对话明确提出的同步记录要求，已转写到PD02；该来源不被伪造为一个上传文件。所有SRC编号只属于本记录包，不是期刊参考文献编号。
