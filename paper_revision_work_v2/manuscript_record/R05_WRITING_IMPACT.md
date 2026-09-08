# R05_WRITING_IMPACT / MR-v1.5-R05

仅生成候选，Word未修改；V/W未启动。

主线：记录重构→条件关系→事后信息增量→适用范围。天气E负增量撤回；当前D1 pooled先升后降撤回；三阶有小幅正增量进入形状证据；1.97对应最低数字阶段、2.99对应最早时间，不称真实初始；图10改为单full物理系数点。当前12图全部复现。

90处候选（若若干旧位置采用同一合并候选，不重复插入）；963行迁移表含950原数字槽；11组合段落完整。182/64绑定逐值/对象/单位检查，A-T10十个目标标签纠正。全部精确位置、上下文、MR/CL、证据行键与候选文字在R05/MANUSCRIPT_MIGRATION_MAP.csv。

章节：现五章保持。六章为建议，第5讨论第6结论，待作者选择；图6/7保留，迁附录亦只建议。附录A改gap/Moran/来源，B记录选择，C合并六组全期对应，D中性标题与下降pooled，E历史不重写成验证，F当前CR1/残差及非PSD范围，G撤回负增量解释，H当前点与旧Bootstrap/分期/回变换分层。

| CL | current_supported_scope | remaining_limit | MR |
| --- | --- | --- | --- |
| CL01 | C/D及记录比较可描述 | 字段真值、来源与记录完整性受限 | MR01–10/21/27/29 |
| CL02 | 正曲率/10.807545条件点可报告 | 三阶正增量；形状/位置不确定性未建立 | MR11/18/19/20 |
| CL03 | 组内配对点增量及指标分解可报告 | 排序稳定性/完整过程/初期用途未验证 | MR12/13/14/22 |
| CL04 | 25日/4452事件及回顾性period可描述 | 不能称未接触确认、整过程独立验证 | MR14/15/16/20 |
| CL05 | expmeaneta参考曲线地图与网格比可报告 | 没有算术均值校准/工程效能 | MR17/19/23/24 |
| CL06 | 当前阶段pooled下降及区域proxy可描述 | 不识别调度机制；Buck重建必做 | MR07/08/21/29 |

## 29项逐项状态

| MR | title | implementation | current_numeric | scientific_limit | next_condition_or_author_decision | Word_status |
| --- | --- | --- | --- | --- | --- | --- |
| MR01 | 事件时间与天气来自后续阶段 | time chain verified | earliest-source and core identity checked | true onset unknown | source metadata | not_modified |
| MR02 | 时区、并列和跨边界规则 | UTC/tie rules verified | 135025 earliest selections agree | time ties not initial truth | V01 stage quality | not_modified |
| MR03 | 未决事件身份与非重复记录 | frozen unresolved identity exclusion verified | B1 identities and n checked | cause/record semantics | V00 identity contract | not_modified |
| MR04 | 客户影响与恢复跨度的构造及验证边界 | comparison selector hardened | main ratios1.973881/2.989070; common n60436 | no true initial/CML interpretation | V01 record quality | not_modified |
| MR05 | 天气产品、缓存、时间窗与39.4m/s叙事 | cache consumption verified | hour/UTC values inherited | historical product/3second/onset unknown | source audit before changed-input fits | not_modified |
| MR06 | gap定义从全国差值改为LAD内LSOA极差 | gap meaning corrected | stored0–1 within-LAD range | Buck proxy not reconstructed range | mandatory T01 rebuild | not_modified |
| MR07 | Moran的计算层级与未知空间权重 | Moran level clarified | published LAD values/proxy known | weights recipe unresolved | mandatory T01 geometry/weights | not_modified |
| MR08 | Buckinghamshire历史代理及后续重建决定 | proxy provenance verified | LSOA sheet found; four old-LAD material inventoried | merged indicator not rebuilt | author already decided rebuild and compare; V00 order | not_modified |
| MR09 | 原因共识、分组来源与天气归因措辞 | consensus grouping verified | main/weather/six-pooled results identified | official code semantics incomplete | source verification; V01 support | not_modified |
| MR10 | 样本流、p99与极端恢复总体 | all_valid evaluation verified | 60436/9857; tails retained | outcome tail quality/shape | V01 tail sensitivity | not_modified |
| MR11 | 标准化、固定效应、VIF与系数尺度 | scaling/rank/covariance implementation verified | 246 bindings; four VIFs; period physical coefficients | six period two-way nonPSD | only targeted future inference protocol | not_modified |
| MR12 | 合并OOF R²与平均折R² | 12 scores recomputed | weather R gap7.20255pp decomposed3.69109+3.51146 | metrics differ; no selective switch | V02 process paired protocol | not_modified |
| MR13 | 贡献排序反转的配对条件与分支 | paired block differences verified | main/weather ordering differs; weather E positive | no stable cross-population reversal | V02 uncertainty and processes | not_modified |
| MR14 | 日分组与完整天气过程依赖 | same-date separation verified | formal OOF eta checked | multiday processes can cross folds | V02 complete process split | not_modified |
| MR15 | 图9暴露侧多做一次log1p | no double log in current consumer | figure09 rebuilt with log y and eta | not engineering raw-scale error | V03 error/calibration | not_modified |
| MR16 | 图9恢复样本混合与窗口重复 | window identities deduplicated | 25unique days/4452main events | date OOF not process OOF | V02 complete process grouping | not_modified |
| MR17 | 曲线、地图与参考人群的数学含义 | reference formulas and consumer verified | 12figures new release; map111LAD | not arithmetic conditional means | V03 uses and source conditions | not_modified |
| MR18 | 二次形状、GLM与三阶反向线索 | archived supplements identified | cubic paired positive deltas; GLM full only | no robust/unique quadratic claim | V01 shape evidence | not_modified |
| MR19 | 最低点与物理单位不确定性 | physical points/scales verified | 10.807545 conditional main point | no current physical CI; old bootstrap historical | shape gate then optional physical bootstrap | not_modified |
| MR20 | 分时段系数、尺度和CV汇总身份 | 8 full-rank period archive readbacks passed | unseen combination guard; LADSE/point figure | retrospective/nonPSD two-way restrictions | V00 only needed inference comparisons | not_modified |
| MR21 | 阶段组成、缺首阶段与客户—跨度关系 | numeric stage sort and bins checked | two current pooled curves decline; time ties quantified | no dispatch mechanism or sole composition cause | V01 stage-quality sensitivity | not_modified |
| MR22 | 最终客户数与可用信息时点 | K final-information timing declared | 1.97/2.99 comparisons not initial model | no initial deployment claim | T08 only if author chooses early use | not_modified |
| MR23 | 工程量级、误差与校准 | reference diagnostics reproduced | residual F1 and archived factors available | not calibrated conditional means or engineering efficacy | V03 | not_modified |
| MR24 | 图6/7是否推进主问题 | fig06/07 retained and recreated | reference map/ratios bounded | no universal importance ranking | author may move to appendix; not delete automatically | not_modified |
| MR25 | 生产者、旧图回填与数字单一来源 | release entry and numeric semantics audited | 950slots/246bindings;10labels corrected; all12figures | OCR/formula objects and Word sync outside R05 | W after V04; current metadata counterpart authoritative | not_modified |
| MR26 | 主线、章节及修复历史分工 | chapter/paragraph mapping created | 90candidate locations;11combination paragraphs | six-chapter structure only proposed | author structure decision after V synthesis | not_modified |
| MR27 | 文献、数据来源及术语引用 | source identities preserved | LSOA internal sheet confirmed; provenance table | official dictionary/product/citation particulars pending | source verification; W bibliography | not_modified |
| MR28 | C10编号缺口已闭合，科学问题转由MR08跟踪 | C10 numbering issue remains closed | scientific Buck issue tracked inMR08 | closing code ID does not close source science | MR08 mandatory reconstruction | not_modified |
| MR29 | LAD21定位与LAD23人口/区域连接的边界兼容 | regional links numerically usable | LAD21map111; LAD23 key compatibility known | boundary equivalence not established | T01 before dependent V fits | not_modified |


Buck为既定必做，工作簿LSOA表已找到；未取得的边界和权重具体影响Moran等重建，先于依赖V模型。来源缺口不阻止已冻结当前分数的算术核对，也不能被算术通过关闭。

作者待定仅：五/六章结构、图6/7位置、V00过程/用途协议，最低点主张是否保留到需新Bootstrap、是否另做初期模型及额外异质性。当前不要求再次决定是否重建Buck。


最终消费者单入口 `R05/cli.py consumers` 已实际通过：验证并复用本轮生成的12组图，再发布246语义绑定。候选文字最终逐段工具/人工复查后，15处连字符表达提示已改写并复核为0；不改任何数值或Word。记录见candidate_skill_audit.json及consumer_single_entry.json。
