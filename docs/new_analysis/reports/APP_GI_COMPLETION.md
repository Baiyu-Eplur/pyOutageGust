# APP-GI-PRED 第三步完成回执

完成记录：2026-09-10T19:30:17+01:00。状态：**产物完成，待研究负责人反馈分析**。

已读取更新台账(2)第10–11节，完成G03/I02的代码接入、必要固定拟合、数组导出、事实结果汇总和技术检查。J03/F02关闭仅同步既有台账与根映射；H未启动。

## 报告与结果目录

- [G：执行与回传报告](../../../results/Appendix/G/logs/GI_EXECUTION_REPORT.md)
- [I：七场风暴执行与回传报告](../../../results/Appendix/I/logs/GI_EXECUTION_REPORT.md)
- [保存结果复算回执](APP_GI_TECHNICAL_VERIFICATION.json)

## 实际完成范围

四个正式样本60437/51173/9857/9254。共享主预测在G/data/GI_PREDICTIONS.csv.gz，三类残差、10个固定模型/对照LAD-OOF、精确全样本/逐折参数及原分箱/曲线数组已保存。C家族嵌套CV单独引用，未冒充固定结点结果。

首次仅补57次必要固定OLS（50个原LAD折模型、4个无阵风控制模型、2个固定旧hinge、1个当前恢复paper全样本），13个全样本系数派生组件；四个正式final全样本均复用。后续派生导出与最后缓存重绘均新增OLS=0。没有结点搜索或候选大比较。

10/10固定OOF汇总与原值一致。七场去重并集暴露4452、正式恢复3990；另28个正客户超阈恢复事件仅展示，独立于评分。四张图均实际打开检查。

## 核验与有效边界

70个保存参数组件乘相同训练规则设计矩阵，预测最大差0；30组G评分、6条实际曲线aᵀVa、40组I评分及去重/显示规则可复算。812个其他附录文件哈希无变化。3项既有事务测试通过。最后缓存重绘的数据/表格文件55个，全部哈希不变。

正式输入外的16条上游缺客户记录无法按风暴细分，未以0冒充；该限制不影响当前正式样本的完整预测与评分。天气暴露实际导出曲线虽使用非PSD的原two-way矩阵，300个网格方差均非负，未作截零或正定化。

原Figure3/5/6的模型身份、恢复旧样本、固定/嵌套CV、响应平移与置信带含义，以及短事件高估、风暴均值/相关措辞，已按具体正文位置记录在报告中，交后续人工判断；未修改正文。

## 复现命令

在项目根目录使用：

```powershell
python -X utf8 -B main_appendix.py --appendices G I --gi-only
```

加`--recompute-gi`限定本包重算；加`--render-only-gi`仅用有效保存数组重绘。只读复算：`python -X utf8 -B test/verify_gi_outputs.py`。

## 新增接口代码

main_appendix.py复用analysis_new/appendix/runner.py调度；gi_core.py管理纯设计与共享预测，gi_outputs.py负责表图数组，gi_storms.py负责窗口与排除，gi_completion.py负责冻结/缓存/事务/报告。catalog.py及mapping.py同步G03/I02单一登记。docs/APPENDIX_PRODUCTION_GUIDE.md与LOG.md已更新。

## 实际核心表图登记

|编号|语义ID|文件|
|---|---|---|
|Figure G1|GI_GUST_RESIDUALS|G/figures/GI_GUST_RESIDUALS.png|
|Figure G2|GI_PREDICTION_CALIBRATION|G/figures/GI_PREDICTION_CALIBRATION.png|
|Figure G3|GI_RESPONSE_COMPONENTS|G/figures/GI_RESPONSE_COMPONENTS.png|
|Table G3|GI_FINAL_GUST_RESIDUALS|G/tables/GI_FINAL_GUST_RESIDUALS.csv|
|Table G4|GI_PREDICTION_METRICS|G/tables/GI_PREDICTION_METRICS.csv|
|Figure I1|GI_STORM_FINAL_SCATTER|I/figures/GI_STORM_FINAL_SCATTER.png|
|Table I2|GI_STORM_METRICS|I/tables/GI_STORM_METRICS.csv|
|Table I3|GI_STORM_SAMPLES|I/tables/GI_STORM_SAMPLES.csv|

以上4张PNG均有同源PDF，未重复登记为不同图。过程与复算文件放data/logs，不全当作论文排版表。

## 停止状态

G03/I02均标产物完成待反馈。未修改Word、其他附录科学结果或历史研究输出；没有独立科学审查、H计算、ZIP或远程提交。
