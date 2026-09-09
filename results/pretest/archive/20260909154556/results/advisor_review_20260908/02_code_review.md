# Step 2 — code/ 目录逐文件审查（12 个脚本）

全部脚本逐行读过。总体评价：实现质量高，方法论上没发现根本性错误；FWL（Frisch-Waugh-Lovell）partialling-out 用于结点网格搜索的写法数学上正确、SSE/BIC/LR 统计量公式正确；nested CV（district-grouped、结点在每个训练折内重新选择）确实没有用到测试集信息，"nested" 这个说法站得住。以下按脚本列出关键点和发现的问题。

## run_main_regression.py

与我们自己 `pyOutageGust/review_package/code/run_main_regression.py` **逐字节相同**——证实导师团队是直接拿我们自己 review_package 的产出（`combined_E0_final.csv`/`combined_R0c_final.csv`，同一个 `run_main_regression.py`）作为起点，不是自己另起炉灶重新构建样本。这对交叉核对是个好消息：M5 quadratic (paper) 这个基线模型两边用的是同一份代码、同一份数据，不存在"表面看着一样、其实实现细节不同"的风险。

## model_selection.py

12 个 specification 的设计矩阵构造函数。standardization 严格按训练折统计量计算（无泄漏）。`A6_M5_+LAD_FE` 正确构造了 110 个 LAD 哑变量（drop 第一个作为参照）。cross-validation 三种方案（random/LAD-grouped/leave-one-year-out）实现正确，LAD-grouped fold 划分用固定种子 `20260908`、`rng.shuffle` + mod 5，可复现。

## knot_estimation.py

profile-likelihood 结点搜索的核心实现。用 QR 分解做 FWL partialling-out（把协变量部分投影掉，只需对每个候选结点组合做一次小型最小二乘）——数学上正确且高效。LR 统计量 `n*log(sse1/sse2)`、BIC 公式 `n*log(sse/n) + p*log(n)` 都是标准的、基于 RSS 的高斯似然近似，同一样本量下做模型间比较是合法的。LAD cluster bootstrap 正确地整簇重抽样（不是按行抽样）。Nested CV 里结点在每折训练集上重新选择，测试折从未参与结点选择——"nested"的说法属实。

**发现的小问题**：README 声称 `knot_estimation.py [B]` 的默认 bootstrap 次数是 500，但脚本里硬编码的默认值是 `B_BOOT = ... else 200`（第 23 行）。核对了实际产出文件 `E0_knot_bootstrap.csv`/`R0c_knot_bootstrap.csv`，行数均为 500（含表头 501 行），说明运行时确实传了 `500` 参数，**结果本身没问题**，只是文档字符串/命令行默认值和 README 描述不一致，纯文档瑕疵。

## plateau_model.py

对暴露响应施加"customers 不能随阵风上升而下降"的物理约束（plateau），重新 profile 结点、检验约束（LR 1 自由度）、bootstrap、two-way 聚类标准误、nested CV。约束检验的 LR 统计量方向正确（plateau 是 two-hinge 的嵌套子模型，约束掉"结点2之后斜率"这一个自由度）。

**发现的两个问题**：
1. 第 98 行 print 语句里 `bic(sse_r,p0+1)` 与第 92 行实际存入 JSON 的 `bic(sse_r, p0 + 2)` 参数个数不一致——plateau 模型有 2 个自由斜率（gust_low、gust_ramp），正确的参数数应为 `p0+2`（JSON 里是对的），print 语句少算了一个，是纯粹的控制台输出笔误，**不影响任何保存的结果**。
2. **更重要的一点**（见下方"额外发现"）：脚本运行后往 `knots.json` 写入的内容，只在第 102-104 行加了一个 `KN["E0"]["ramp"]` 子键，**没有更新 `KN["E0"]["selected"]` 字段本身**，也没有写入任何 `"form"` 字段。但实际磁盘上的 `results/model_selection/knots.json` 文件里 `E0.selected` = `[14.0, 25.0]`（plateau 版结点，正确），且多出一个 `E0.form = "three-segment plateau..."` 字段——这两处都不是当前 `code/` 目录里任何脚本会写入的内容。也就是说：**`results/` 里的 `knots.json` 不能仅凭 `code/` 目录里现在这几个脚本、按 README 给的顺序重新跑出来**；产出这份 `knots.json` 用的是一个比现在打包进 `code/` 目录里更新的 `plateau_model.py` 版本（或者有一个未包含在包里的后处理步骤，手动把 "selected"/"form" 写回了 `knots.json`）。所幸最终结果本身是自洽的——`final_models.py` 读的正是这个已经正确更新过的 `knots.json`（`final_summary.json` 里记录 `E0.knots = [14.0, 25.0]`），所以**最终报出的系数、图表数字没有错**，但这是一个真实的、可验证的"代码包不能完整复现自己产出结果"的可复现性缺口，值得指出给导师团队：打包时可能漏了 `plateau_model.py` 的最终版本。

## final_models.py

零客户样本剔除逻辑：`zero = d.customers_v2_event_excl_reinterruptions == 0` → 剔除全部这些行（不只是 duration==1.000h 的那些），`placeholder_share` 只是作为诊断统计量记录、不是剔除条件本身——这与文档叙述一致（"restoration time is undefined when nobody was interrupted"是剔除的理由，1.000h 占比是支持这个判断的证据，不是筛选条件）。两条聚类标准误（LAD-only、LAD×date two-way）计算正确，t 分布自由度 `G-1`（LAD 簇数减一）用法标准。

## district_day_fragility.py

Gaussian-kernel IDW 插值：`w = exp(-0.5*(dist/40)^2)`，距离用简单的等经纬度平面近似（`km()` 函数，纬度用 111 km/度、经度乘 `cos(51.8°)` 做修正，51.8° 大致是伦敦纬度，UKPN 服务区跨度约 2 度，这个近似在这个尺度上是合理的，不会引入明显误差）。**leave-district-out 验证**是真正意义上的"留一验证"——`interp(obs, ..., exclude_lad=l)` 在预测某个 district 当天的 gust 时，明确排除了那个 district 自己的观测点，不是用同一批数据自证自话。fallback 分支（当高斯核权重不足 5 个邻居时退化为最近 5 个反距离加权）是一个未在文档里提及的实现细节，逻辑合理但与"高斯核 40km"的表述不完全一致，属于文档描述略微简化、不算错误。Panel 构造（`any_gt{k}`/`wthr_gt{k}` 布尔阈值逻辑）核对无误，`k=0`（"至少一次事件"）和 `k>0`（具体客户数阈值）两套判断分支分别正确处理了"当天无事件"的哨兵值 -1。**没有发现类似 C01 代表行选取那类的隐患**——这个脚本完全基于已经修正过的 `incident_date_utc` 字段做分组，不涉及重新选择"代表行"。

## fragility_demo.py / fragility_surfaces.py

Proportional-odds ordinal logit + per-threshold binary logit（parallel-lines 诊断）+ NB GLM（矩估计离散参数）实现规范。`fragility_surfaces.py` 里 lognormal MLE 用 parallel-probit 参数化（`theta=exp(-a/b)`, `beta=1/b`）数学上等价于标准 lognormal fragility 形式，LR 检验 common-beta vs free-beta 的自由度设置正确（`len(thr)-1`）。**小问题**：`fragility_demo.py` 第 80 行有一段死代码（`if False else None`，McFadden 伪 R² 计算被禁用、恒为 None），不影响任何已发布数字，只是未完成/废弃的功能残留。

## weather_only_regression.py

Weather-only 子样本上重新做结点 profile-likelihood 搜索（用了 `knot_estimation.py` 里的 `KnotSolver`/`hinge_cols`，复用同一套数学实现，不是另写一遍——好的工程实践，降低了两处结果不一致的风险）。E0 的最终结点会从 `ramp_model.json` 的 `"weather"` 分支读取（第 90-91 行），这意味着这个脚本必须在 `plateau_model.py` 跑完之后才能跑——README 里的步骤顺序（2b 在 7b 之前）是对的，只是这个依赖关系是通过磁盘上的 JSON 文件隐式传递的，不是显式参数，风格上可以更清楚，不算错误。

## paper_extras.py

development/confirmation 时间切分（`split = 2023-09-30`）、按变量组分块的边际 R² 分解（district-grouped CV）、结果分布图注释——逻辑清楚，没有发现问题。

## plot_model_selection.py

出图脚本。第 17-18 行 `KNOTS = {...v["selected"]...}` 读取的正是上面提到的、已经被正确更新为 `[14,25]` 的 `knots.json`，所以图 2/3/5 里画的分段线性曲线用的是 plateau 版结点，与文档正文一致，**没有受到"代码不能完整复现结果"这个provenance缺口的影响**（因为它依赖的是磁盘上已经算好的 `knots.json`，不需要重新跑 `plateau_model.py`）。

## build_doc.js / build_papers.js

纯文档组装脚本，不做任何统计计算：图表从 `results/figures/*.json` 读取，正文段落是硬编码在 JS 里的静态字符串（与 docx 里读到的文字逐句对应）。这意味着如果哪天重新跑分析、数字变了，**这两个脚本不会自动更新正文叙述**——必须有人手动同步 JS 里的字符串和最新的统计结果，这是一个人工维护风险点，不是本次审查范围内的"错误"，但值得指出。

## 小结

12 个脚本里没有发现推翻任何核心结论的实现性 bug。发现的问题按严重程度：
1. **`knots.json` 的 `selected`/`form` 字段无法用打包进来的 `code/` 目录完整复现**（中等严重性——不影响已发布数字，但意味着包本身不是"从头跑一遍就能复现全部结果"的完整闭环，导师团队打包时可能漏了 `plateau_model.py` 的最终修订版）。
2. `plateau_model.py` 里一处 print 语句 BIC 参数数算错（纯打印，不影响保存结果）。
3. README 的 bootstrap 默认次数（500）与代码里的默认值（200）不一致（结果本身用的是 500，没问题）。
4. `fragility_demo.py` 一处死代码。
5. `build_doc.js`/`build_papers.js` 正文是手写字符串，不会随数据自动更新，是长期维护风险而非当前错误。
