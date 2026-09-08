# R04完整包审阅：论文故事、章节与论证修订方案

版本MR-v1.4-R04-review；来源R04完整包及包内算术复核。下面是待R05核实、供W阶段落实的写作方案，未改Word，未将六章结构认定为作者已接受。

## 1. 当前故事及六项论证责任

以工程事件后果为研究对象：先证明阶段记录怎样支持事件级客户影响C和记录恢复跨度D，再研究阵风关系及事后客户信息的条件预测增量，最后限定跨人口、时间与工程解释的适用范围。阶段数不直接等于维修动作数，跨度不等于客户加权平均停电时长；回顾性关联不自动成为初期决策工具。

| CL | 论证责任 | 当前B1可用证据 | 应避免的跳步 |
| --- | --- | --- | --- |
| CL01 | 测量对象与事件后果 | 冻结重构、正式n及更新描述 | 可复现不证明真实onset/记录完全；两种客户比较需消歧 |
| CL02 | 阵风形状及条件点 | 二次项、参考曲线、条件最低点、三阶小幅改进 | 正二次项→稳健U形→物理阈值的连续跳步 |
| CL03 | 条件信息贡献 | 同组同折嵌套增量；两样本点排序不同 | 跨组R²变化→物理效应增强；最终客户数→初期信息 |
| CL04 | 时间和风暴证据 | 日期OOF、窗口去重、分期物理点估计 | 日期留出→完整过程留出；重编码通过→跨期稳定 |
| CL05 | 参考量级与工程含义 | 明确定义的exp(meanη)、地图及网格比 | 指数化对数拟合→算术均值；关联图→工程效能 |
| CL06 | 机制及区域解释 | 阶段组成、区域代理的描述 | 合并曲线→抢修机制；键连接→边界等价 |

## 2. 章节组织：现有位置与候选结构

现有Word五章：Introduction、Data and Study Setting、Empirical Framework、Results、Conclusion。候选六章在Results后增加Discussion，将原结论中的解释和限制移入，Conclusion只回答研究问题。该调整保留为PD结构建议；若保留五章，讨论职责应在现有结构中找到明确位置。

| 现有章节/锚点 | 候选职责及改写动作 | 当前证据 | 未决条件/措辞界限 |
| --- | --- | --- | --- |
| 摘要D-P002 | 给事件后果/回顾性研究定位，更新60,436与9,857、条件点10.8及信息排序 | core_metrics、shape、increments | 不写稳定阈值；客户比较待F02；三阶线索不能被摘要绝对化形状结论掩盖 |
| 引言D-P006–013 | 从网络后果测量及信息问题引出三个RQ：形状、条件增量、适用范围 | CL01–CL05 | 不以预设的U形或工程机制组织问题；39.4m/s按产品代理身份表述 |
| §2.1 D-P016–021 | 地域/时间→来源→连接→语义限制 | R02证据、R04真实消费 | 最早记录代理不是实测onset；LAD键匹配不是边界等价；Buck已决定重建 |
| §2.2 D-P023–030 | C与D分别定义；特殊/再中断处理；记录口径比较 | 事件定义、比较JSON | 1.97与2.99不同对象；F02核查后才写确定比值；不论证真实初期低报 |
| §2.3 D-P032–036 | 全有效样本的尾部、阶段组成与后果分布 | Table1、D1、stage counts | 均值17.460小时受长尾影响；不能未核实就删除最大5547.05小时记录 |
| §2.4 D-P038–041 | 原因共识→共同资格→模型人口→变量尺度/来源 | n、Table1、VIF | 主/天气VIF分列；改gap定义；不沿用全体连续VIF<4 |
| §3.1 D-P044–048 | 二次工作模型理由与可被反驳的形状检查 | 4GLM、三阶配对OOF | 已有结果不再写成完全缺材料；GLM无本轮OOF；三阶改进保留 |
| §3.2 D-P051–055 | 开发历史、固定日期分折、同人口评分及分期身份 | fold合同、core_metrics、period表 | F05解释两种R²；后期不是未接触验证；跨日过程仍可能共享 |
| §3.3 D-P057–064 | 目标尺度、G/K块、训练变换、参考量和协方差 | 已运行接口及系数 | K是事后聚合信息；F01列推断消费者；变换先后写准确 |
| §4.1 D-P066–080 | 条件曲线→支持→最低点→三阶/GLM比较 | 10.807545等点、图4 | 无新CI；天气E0低端支持有限；图4纵轴不能泛称平均客户数 |
| §4.2 D-P084–094 | 嵌套表及G\|K、K\|G；场景比作为附加解释 | 主E增量1.246442pp；主R配对增量 | 不复用旧12.7倍；避免把不同参考图的比值当通用变量重要性 |
| §4.3 D-P097–108 | 子样本信息排序→原因组成→风暴窗口描述 | 天气E增量+0.382246pp；25日、4452事件 | 删负增量故事；逐风暴相关不证明稳定反转；全拟合与OOF分别标注 |
| §4.4 D-P111–116 | 分期物理项、支持、聚类结果的条件报告 | 等价基、period表、协方差 | q变化不能概括稳定；6个双向矩阵条件待R05；全期显著性必须新表绑定 |
| 候选§5 Discussion | 对事件负担与恢复跨度的工程解释、信息可用性、误差/校准及数据限制 | CL05–06、未来V证据 | 图6/7留正文或移附录待作者；不自行删除 |
| 候选§6 Conclusion/现有§5 | 逐RQ给有限结论及应用范围 | 最终CL证据矩阵 | 不从编码修复推出验证全部完成；不把未执行验证写成通过 |

## 3. 附录逐节方案

| 附录/当前位置 | 当前题目或论证问题 | 候选修改及证据 |
| --- | --- | --- |
| A：A-P003、008–014、A-T02 | 变量字典/区域指标及地理边界 | C/D、标准化ln(1+C)、气象代理、gap为LAD内LSOA极差分别列明。Moran权重、Buck代理和LAD21/23边界条件独立标注；地区数等不能凭旧表继承，按实际对应来源核实 |
| B.1：A-P017–018 | earliest-stage混称 | 标题建议“Comparison of customer counts under alternative record-selection rules”；分别定义最小可用阶段编号与最早时刻，F02给有效n/并列及共同人口结果 |
| B.2–B.5：A-P019–027 | 跨度、人工核对、边界及缺首阶段 | 保留真实规则；14,264/135,025是历史来源中的明确口径，R05核实当前是否同一人口，不自动以主样本比例替换；主模型缺首阶段排除敏感性尚未做 |
| C：A-P028–030、A-T03 | 六原因组比较 | 说明六组“合并人口”的一个恢复模型；当前n117,108、OOF0.039923105。不是6个各自拟合模型；全有效与旧p99人口不同；3/5、5/5折显著次数非独立重复实验 |
| D：A-P032–055、A-T04/05、D1 | 标题预设apparent non-monotonic；旧合并先升后降不成立 | 标题建议“Stage-record composition and the association between affected customers and recorded restoration span”。D.4改“Pooled and stage-stratified patterns”。D.1阶段组成；D.2–3分层；D.4合并及支持；D.5 raw ln(stage)控制；D.6记录解释边界；D.7天气子样本。全期重算与旧开发期表明确区分 |
| E：A-P056–063 | 真实开发历史及回顾性分期 | 保存历史时间线；新B1重跑不把后期改成untouched；历史CV均值/加权汇总与本期单次全拟合分开 |
| F：A-P064–068、A-T08/09 | full robustness措辞可能超过内容 | 标题可改“Coefficient estimates under single- and two-way clustering”。全期与分期矩阵分开；协方差身份、有效k、p值参考分布和非半正定限制按R05结果写；不能笼统说所有推断通过 |
| G：A-P069–073、A-T10 | 低阵风支持解释旧负增量 | 保留当前十分位原因组成和支持比例；主/六组十分位不同人口。删除由负增量推出的解释链，改为选择与支持范围讨论；不推断官方原因标签完整准确 |
| H.1：A-P075–078、A-T11 | 条件最低点 | 用自身μ/σ及固定物理p转换；主10.807545无新CI；各人口点与支持条件同时给 |
| H.2：A-P079–086、A-T12 | 旧Bootstrap可能被回填成新B1证据 | 旧区间保留在历史审计，不能写成B1区间；只有V决定保留核心最低点后做合格协议。标题/位置待最终主张决定 |
| H.3：A-P087–089、A-T13 | 分期尺度及CV汇总混合 | 替换为各期全拟合物理参数与日历等价说明；旧CV重叠和旧日历不可识别方向保留历史解释；F01推断限制显式标注 |
| H.4：A-P090–092 | exp与mean顺序及工程解释 | 写清exp(meanη)；E对应1+C，R对应D的指数化对数拟合；无smearing/条件均值校准，不以全局exp残差均值直接校准图 |
| H.5：A-P093–094 | 已完成与仍待做混在一起 | 把4GLM/三阶/现有描述由“待补材料”更新为已生成有界证据；V形状、依赖、工程误差仍待；该研究待办结构在正式稿W阶段收束 |

## 4. 65个组合数字槽位对应的11处段落处置

以下是段落级修改责任，不是逐token替换。R05应按旧Word索引写完整候选段落并绑定数据行键。

| 旧位置 | 主要旧逻辑 | 必须形成的候选改写 |
| --- | --- | --- |
| A-P027 | 缺首阶段14,264/135,025与保留 | 同人口核实该数量；分开全主表与主/天气模型；不把未做排除敏感性写成通过 |
| A-P044 | 分层稀疏格+pooled先升后降 | 以当前分箱实际n/均值重写；主pooled四均值21.451→17.639→15.846→11.708；不沿用旧22/18稀疏格计数；分层未全部单调 |
| A-P054 | 天气与主样本多阶段49.7/40.5% | 绑定当前stage counts、同一stage定义和人口；旧开发期回归另列 |
| D-P039 | 60,453→60,437/59,834及p99排除 | 用冻结样本流说明当前主60,436/天气9,857、E/R共同有效人口和保留尾部；不能将旧n差继续归为当前p99 |
| D-P041 | 全部VIF<4且gap为全国差 | 修改gap含义；当前主连续最大约3.755，天气连续约4.93、包括日历最大约5.347，按实际字段精确绑定；不以阈值机械通过 |
| D-P084 | mean-fold名下引用pooled；旧12.7比 | 方法明确pooled；新主E增量/总分和主R双顺序增量；不保留过时倍数或因果分解 |
| D-P093 | 旧地图1.96/1.41与网格比排序 | 从regional_reference_ranges及图7当前数据重写；参照不同的比不作统一变量排名 |
| D-P097 | 旧天气n、负E增量、旧12.7和双倍物理含义 | 天气E/R均9,857；E增量转正；R报告1.142/6.141及3.580/1.507条件点比较；不称物理效应翻倍 |
| D-P106 | 旧风暴相关范围及Dudley显著性 | 分清全拟合/日期OOF、目标、每窗口n；从storm_prediction_correlations重写，不能从小相关或旧p推断工程失效 |
| D-P111 | CV加权0.066与后期0.064混比 | 用period_comparison的全拟合物理q、各期μ/σ与同物理p；图10为点估计；不得据同号宣称稳定 |
| D-P116 | 旧p=5.4e−22/2.8e−36及显著性清单 | 用全期当前系数/协方差/p参考重新逐项判断；与分期F01分开；不凭旧语言预设哪些仍显著 |

## 5. 已可形成的英文候选句及采用条件

下列句子为候选文字片段，R05仍需放回上下文审查；没有写入Word。

**数据/主人口（MR10）：** “The all-valid analysis included 60,436 incidents in the combined sample and 9,857 in the weather-attributed subset, with the same eligible incidents used for the two outcome models within each population.” 来源：core_metrics及成员合同；本地R05确认对应完整档案。

**客户比较（MR04）：** “The record with the lowest available stage number and the record with the earliest recorded start time define different comparators for incident-level aggregated customer counts.” 该句不依赖尚待F02确认的精确比值。F02通过后再给各自有效n/均值之比，不称initial或真值低估。

**形状（MR18/19）：** “At the mean pressure of the combined sample, the quadratic model placed the conditional fitted minimum for the customer outcome at approximately 10.8 m/s. Adding a cubic gust term increased pooled out-of-fold R-squared by 0.00193; the quadratic representation therefore remains a working description whose shape and minimum require further assessment.” 来源：shape及supplement；最终稿末句按V结果改成已完成验证的事实。

**条件信息（MR13）：** “For restoration span, the conditional gain from adding gust after customer terms was 1.14 percentage points in the combined sample and 3.58 in the weather-attributed subset; the corresponding gains from adding customer terms after gust were 6.14 and 1.51 percentage points. These are retrospective, population-specific comparisons of point estimates.” 来源：increments；后续是否加稳定性结论由V决定。

**风暴（MR16）：** “The seven storm windows covered 25 distinct UTC dates and included 4,452 unique incidents from the combined analysis sample. Full-fit predictions describe training-sample agreement, whereas date-group out-of-fold predictions exclude the event's date from fitting; neither comparison withholds each complete storm process.” 来源：storm_statistics、图9及日期合同。

**分期（MR20）：** “Period comparisons use full-sample fits within each period, expressed in physical gust units with period-specific standardisation and equivalent full-rank calendar bases. The displayed coefficients are point estimates and do not establish temporal stability.” 来源：calendar_equivalence、period_comparison及图10；分期协方差限制另外交代。

**阶段（MR21）：** “Under the current shared bins within the combined sample, pooled mean restoration span decreases across the four customer-count bins. Stage-stratified patterns differ, and these descriptive summaries do not identify repair prioritisation or dispatch mechanisms.” 来源：artifact_acceptance和D1；不同人口/分箱的历史模式不混用。

## 6. 证据、状态及回填规则

- 新数值以R04命名数据集及行键为准，复核结果仅证明被检查的算术/文件范围；完整档案本地再读由R05承担。
- 整句、标题、图注、样本表、方法定义与结论必须同步；只换数字会留下错误叙事。
- 同一MR保存历史action，当前行动独立呈现。历史PD决定不会因重新打包而成为本轮作者新批准。
- 新Bootstrap、样条、完整过程、Buck重建及工程校准的结果未产生前，不写成通过。Buck任务已决定，新的具体执行方案待V00排序。
- R05返回`MANUSCRIPT_MIGRATION_MAP.csv`、候选改写及完整台账；W00落实Word后，W01重新逐公式、逐论证、逐图表核验。
