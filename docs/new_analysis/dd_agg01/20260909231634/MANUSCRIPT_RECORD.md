# DD-AGG01 论文修订台账

本轮仅记录建议，Word、Table7和Figure8均未直接改动。District-day正文按用户决定保留，历史P03结论不改写。

|任务ID|发现|证据文件/行或图表|涉及正文位置|建议修改|建议附录内容|状态|
|---|---|---|---|---|---|---|
|DD-AGG01-01|相同小时源、标签和原折下固定五种聚合|PROTOCOL.md；data_validation.json；daily_aggregations.csv.gz|Extended §3.5|说明UTC24小时聚合定义及任意事件含零客户|原文件指纹、五指标分布/相关|待联合审查|
|DD-AGG01-02|历史稀有任务有已知合法NLL反例，统一优化修复单列|baseline_repair_comparison.csv 的 wthr_gt1000 六行；rare_repair_gate.json|§3.5、§4.4、Table7|说明稳定似然和多初值；有效参数经审查后才可替换|240拟合及全部初值诊断、边界/弱识别|计算完成；未改Word|
|DD-AGG01-03|主要/次级任务五聚合OOF数值与逐折方向|metrics.csv/paired_uncertainty.csv 中 any_gt100、wthr_gt100；fold_metrics.csv|§4.4、Figure8|如实写出绝对和相对差，不只列优胜者|其余六任务、条件LAD区间及限制|待选用，不自动采用|
|DD-AGG01-04|训练率BSS与共同箱校准补足单一分数|metrics.csv；calibration_bins.csv；figures/calibration_*.png|§4.4、Figure8|区分概率预测信息和校准，保留稀疏支持|精确边界、空箱/稀疏箱、全范围图|图表已生成；待审查|
|DD-AGG01-05|不同聚合参数不能直接解释为物理阈值|parameters.csv 的 theta_outside_support/weak_identification；figures/occurrence_*.png|Table7、§5|限定θ解释和外推范围|全样本/训练折参数、曲线数据|待文字修订|
|DD-AGG01-06|固定候选探索与LAD留出不等于未来时间验证|REPORT.md §7；paired_uncertainty.csv|§5|保留正文并说明观察性、选择和时空依赖限制|五候选完整比较；必要时仅建议下一轮定向时间核验|未新增实验；待用户判断|

## 本轮判读后的建议

主、次任务均保留A01日最大阵风作为当前基准；全体/天气 >1000的历史优化修复单列。62个θ超支持范围和n=1尾部箱敏感性必须保留说明。以上为计算证据建议，Word及Table7/Figure8未改；等待人工+agent联合审查。全部表格文件路径均相对于 `D:/Pyprogramme/pyOutageGust/results/new/20260909231634/results/dd_agg01`。
