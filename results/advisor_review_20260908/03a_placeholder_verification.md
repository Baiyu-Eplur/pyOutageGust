# 3a — 占位符数据问题：独立复现（最高优先级）

**结论：站得住。三项子结论全部独立复现成功，且发现了导师报告没有给出的、能解释"为什么恰好是1.000h"的具体机制。**

## (1) 独立在我们自己的最终 R0c 样本上重新统计

用的是 `pyOutageGust/review_package/data/combined_R0c_final.csv`——这是我们自己项目在"断开 review_package 对 claude_branch 最后依赖"那次任务里重新独立生成的最终样本，跟导师包里 `data/combined_R0c_final.csv` **SHA256 完全一致**（`313e5cea...`），说明导师团队用的就是我们自己 pipeline 产出的同一份数据，样本构造方式没有分歧，不存在"两边样本口径不同导致数字对不上"的可能。

验证脚本：[`verification/3a_placeholder_and_signflip.py`](verification/3a_placeholder_and_signflip.py)，独立编写（未复制 `final_models.py` 的代码），运行结果：

| 指标 | 我方独立复现 | 导师报告 | 是否一致 |
|---|---|---|---|
| 样本总数 | 59,834 | 59,834 | ✅ |
| zero-customer 事件数 | 8,661 | 8,661 | ✅ |
| zero-customer 里 duration 恰好 1.000h 的占比 | **66.52%**（5761/8661） | 66.5% | ✅ |
| 非 zero-customer 里 duration 恰好 1.000h 的占比 | **0.506%**（259/51173） | 0.5% | ✅ |

三个数字全部精确复现（到小数点后两位），不是巧合式近似。

## (2) 独立核实这批"1.000小时"记录的时间戳构造方式

这是导师报告里**没有深入回答**的一点——他们判定这是"占位符"，但没有说明背后的具体生产机制。我们自己有 `rebuild_v3_full_stage` 这条数据重建管线的完整源码，可以往回追。

`duration_B_full_span_hours` 的计算方式（[`build_stage_base_v3.py:123-125`](../../paper_revision_work_v2/code/snapshots/H0/rebuild_v3_full_stage/scripts/build_stage_base_v3.py)）：

```python
duration_b = (end.groupby(key).max() - start.groupby(key).min()).dt.total_seconds() / 3600.0
```

即直接用原始 `Start Date and Time` / `End Date and Time` 两个字段相减——**这不是我们自己 pipeline 里插入的任何系统默认值**，是对原始 UKPN 记录的忠实计算。于是往回查了原始 `data/external/ukpn-iis.csv` 里这批事件的原始记录（抽取 5 个样本核对，逐条比对）：

| Incident Reference | Restoration Stage | Start | End | Number of Customers Restored | Cause Code |
|---|---|---|---|---|---|
| FREP-75814-C | 1 | 2023-08-11 15:00 | 2023-08-11 16:00 | 0 | 71 |
| FREP-13415-O | 1 | 2023-04-28 10:36 | 2023-04-28 11:36 | 0 | 71 |
| FREP-13730-O | 1 | 2023-05-09 15:00 | 2023-05-09 16:00 | 0 | 71 |
| FREP-75979-C | 1 | 2023-06-23 15:00 | 2023-06-23 16:00 | 0 | 71 |
| FREP-15193-O | 1 | 2023-09-14 15:00 | 2023-09-14 16:00 | 0 | 71 |

5/5 全部：单一 stage（无多段复杂性）、Number of Customers Restored = 0、**End - Start 恰好 1 小时**、Cause Code = 71。扩大到全部 5,761 个 placeholder 事件核查：

- **100%（5761/5761）都只有 1 个 restoration stage**。
- 原始 Cause Code 分布高度集中：**97.5%（5617/5761）是 Cause Code "71"**，其余零散分布在 25/06/19/23/A1 等code。我们自己的 cause-code 分组表（[`build_stage_base_v3.py:60-63`](../../paper_revision_work_v2/code/snapshots/H0/rebuild_v3_full_stage/scripts/build_stage_base_v3.py)）把 "71" 归入 `technical_asset` 类——与我们独立统计出的"placeholder 事件里 98.2% 是 technical_asset 类"（5656/5761）完全吻合。

**结论**：这不是我们的 pipeline 或导师的 pipeline 在处理过程中意外引入的填充值，而是**原始 UKPN 监管记录本身的一种记录惯例**——Cause Code 71（技术性资产类的某个具体子类）对应的记录里，"restoration stage"本来就只有一条、customers=0、系统给这类记录标注了一个固定 1 小时的窗口，而不是真实的现场抢修耗时。这比导师报告"判定为 placeholder"的结论更进一步：**我们现在知道了具体机制**——0 customer + 单 stage + Cause Code 71 三者高度共现，指向一个特定的记录类别（很可能是"未造成实际停电影响的技术性事件"，比如设备自检、误报或无负荷线路上的动作），不是随机噪声，也不是任何一方数据处理引入的 bug。这个发现比导师原报告更扎实，建议写进论文的数据说明部分（可以直接引用 Cause Code 71 这个具体依据，而不只是"66.5%恰好1小时"这个统计巧合式的表述）。

## (3) 独立复现"剔除后 customers 系数符号翻转"

用**我们自己独立重写**的回归代码（未复制 `final_models.py`，只是照搬 `run_main_regression.py` 里已经验证过的原始 M5 设计矩阵构造逻辑：z-score 标准化、LAD 聚类 SE），分别在"全样本（含占位符）"和"剔除 zero-customer 后"两个样本上跑同一个规格，独立得到：

| 样本 | log(1+customers) 线性项系数 | 二次项系数 |
|---|---|---|
| 全样本（n=59,834，含占位符） | **+0.3356**（p=1.6e-59） | −0.3958（p=2.8e-79） |
| 剔除 zero-customer 后（n=51,173） | **−0.1958**（p=9.4e-33） | −0.1105（p=7.8e-16） |

线性项系数从 **+0.34 变成 −0.20**，符号确实翻转，与导师报告"customer-count terms change sign"完全一致；剔除后的数值（−0.1958 / −0.1105）与导师报告 Table 2 里的最终模型系数（−0.1964 / −0.1113，用的是他们加了温度平方、去掉 gust×pressure 的"final"规格）非常接近——差异在小数点后第三位，量级上是同一个结果，差异来源是协变量集合的微小不同（我用的是原始 M5 集合，他们用的是"final"规格），不是复现失败。

**这一项审查结论：CONFIRMED，站得住**，且核实过程中额外发现了 Cause Code 71 这条更具体的证据链，建议在论文数据说明里补充这一点。
