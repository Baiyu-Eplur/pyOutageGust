# APP-J03-COMPARE 第一工作包完成说明

日期：2026-09-10，Europe/London（BST）。状态：**产物已补齐，待研究负责人反馈分析；尚未科学关闭**。

本文件补充发布、可读性和缓存核验事实。八任务完整结果、方法边界与旧新PROXY参数对照，以[执行与回传报告](../../../results/Appendix/J/logs/J03_EXECUTION_REPORT.md)为准；没有另行开展科学审查。

## 完成范围与运行方式

已接入既有 `main_appendix.py`，固定输出 `results/Appendix/J/`。在项目根目录、既有pyoutagegust环境运行：

```powershell
python -X utf8 -B main_appendix.py --appendices J --j03-only
```

加 `--check-only` 只读预检；加 `--recompute-j03` 明确重算本包96个组件。普通调用检查科学缓存并重新导出图和报告，无需agent或人工交互。

- 两来源相同111 LAD、1096 UTC日、121656个地区日，八标签及既有五折逐行一致。
- 最终覆盖96个唯一组件：16组全样本参数及80个训练折参数。48个GRID_MAX兼容复用，48个PROXY采用相同稳定拟合预算补算；96/96有效，弱识别标记0。
- 已保存逐行OOF、共同训练折常数基准、八任务池化及逐折评分、1000次整LAD配对抽样及条件区间、共同校准分箱、来源/配置/诊断和旧新PROXY描述性对照。
- 206项本包必要技术检查通过；包括保存预测的评分复算、训练折参数预测对应、同抽样区间复算及分箱计数。没有扩展为历史数值审计。

## 已发布的表图

显示编号沿用根 `results/Appendix/figure_table_register.csv`；全部既有非J03表图编号保持不变。

|编号|J目录内文件|用途|
|---|---|---|
|Figure J2|figures/J03_BRIER_COMPARISON.png|八任务Brier与配对条件区间|
|Figure J3|figures/J03_PRIMARY_CALIBRATION.png|全体>100、天气>100的两来源校准|
|Table J20|tables/J03_CALIBRATION.csv|全部共同箱边界、数量、阳性、预测与观察频率|
|Table J21|tables/J03_COMPONENT_MANIFEST.csv|96组件最终动作与有效性|
|Table J22|tables/J03_COMPONENT_PLAN.csv|新增拟合前冻结的复用/补算计划|
|Table J23|tables/J03_FOLD_FITS.csv|80训练折参数及诊断|
|Table J24|tables/J03_FOLD_METRICS.csv|逐折配对结果|
|Table J25|tables/J03_FULL_PARAMETERS.csv|16全样本参数及诊断|
|Table J26|tables/J03_MATCHED_SAMPLE.csv|八任务匹配样本及阳性数|
|Table J27|tables/J03_PAIRED_INTERVALS.csv|本次固定OOF配对条件区间|
|Table J28|tables/J03_PAIRED_METRICS.csv|八任务完整评分主表|
|Table J29|tables/J03_PROXY_HISTORY_COMPARISON.csv|旧新PROXY参数及同输入概率的直接对照|

表格另有阅读版MD；完整精度保留CSV。底层文件见J/data/J03_*；冻结拟合协议、输入指纹和有效性检查见J/logs/J03_*。

## 异常与实际执行次数

前三次正式尝试每次均完成48个PROXY新拟合组件，均遵循相同预算。前两次分别在绘图后端缺少Tcl/Tk、评分复算列名映射错误处停止；事务均未发布，暂存被清理，旧结果保留。修正分别仅涉及Agg文件绘图后端和GRID_MAX评分列名。第三次于16:47:08完成评分与检查并成功发布。

因此，跨三次尝试累计发生144个PROXY组件执行；最终结果集只含48个唯一PROXY新拟合组件和48个GRID_MAX复用组件。未将失败暂存结果与最终结果混合，也未根据候选表现增加初值或预算。当前无残留计算阻塞。

实际查看两张正式图片后，对校准图作了展示修正：以相同主图范围展示常见概率区间，全范围插图保留所有非空箱，图下表逐箱列出n、阳性数、平均预测与观察频率；空箱为NA，稀疏箱仍标注。分箱边界和数值完全未变。修正后的校准PNG已再次打开查看。

该展示修正通过同一入口复用完整缓存完成，之后又执行一次普通缓存导出，两次新增拟合均为0。26个科学数据/表格文件逐一SHA256一致。原拟合代码与配置仍保留在J03_PROTOCOL.json，当前渲染代码及本次动作另记J03_LAST_EXECUTION.json。缓存的初次格式迁移只接受已知上一正式生产代码哈希并逐项核对配置及输入；不是以同名文件存在作为复用依据。

## 有限工程核验与保护范围

- 既有8项附录事务/选择/覆盖保护测试通过；新增完整合成输出流程测试通过，测试数据和图片位于自动清理的临时目录，不作为科研结果。
- A–I共721个文件的清单、大小、修改时间及各manifest SHA256与执行前一致。这里未逐一重新哈希全部大型A–I数据。
- 其他J的42个管理文件逐一哈希保留；当前J清单中的产物哈希核对通过，成功状态不再保留过期error字段。
- 原研究输入哈希保持一致；54个既有非J03表图的编号及路径保持一致。
- 核验记录：[J03_DELIVERY_CHECKS.json](J03_DELIVERY_CHECKS.json)；执行前文件记录：[J03_SCOPE_SNAPSHOT.json](J03_SCOPE_SNAPSHOT.json)；重导出前科学文件指纹：[J03_SCIENTIFIC_EXPORT_SNAPSHOT.json](J03_SCIENTIFIC_EXPORT_SNAPSHOT.json)。科学评分复算代码属于 `analysis_new/appendix/j03_compare.py:technical`，无需另外运行科学计算脚本。

新增主要代码为 `analysis_new/appendix/j03_compare.py`、`j03_report.py`；入口调度、catalog、来源指纹、映射及维护说明已同步；详细逐步记录见根LOG.md。没有修改既有稳定优化器、旧main_new开关、正文、A–I成果或原研究结果。

## 台账与停止位置

J README、J及根manifest、主张/需求/结果映射、缺口状态、图表登记均已更新。四步台账仅将第一包改为“待反馈分析”，原科学设计保留；执行时版本哈希保存在拟合协议，台账随后变更属于执行状态登记。

下一步由研究负责人审阅本包八任务对照、校准和旧新PROXY记录，决定解释与关闭状态。F02、G/I及H03均未启动；未生成ZIP、回传压缩包或远程提交。
