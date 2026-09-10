# 附录生产执行回执

完成时间：2026-09-10T13:16:01+01:00。本回执记录实现和导出，不是科学审核报告。

已按用户附件和v9完成三层映射→独立入口→实际全量运行→必要核验。正文固定20260909183317 Extended；全部原实验、原数据和Word保持原样。

入口：`main_appendix.py`。固定目录：`results/Appendix/`。39项需求：27项已生成、1项明确复用、7项具体缺口、4项按用户决定关闭。共45张表（CSV+Markdown）及2张400dpi图。

## 实际运行

```powershell
& "C:/Users/haoya/.conda/envs/pyoutagegust/python.exe" -X utf8 -B "D:/Pyprogramme/pyOutageGust/main_appendix.py" --all
```

选择运行可将 `--all` 改为 `--appendices A J`；检查使用 `--all --check-only`。默认不选字母时不写入。

## A–J 状态

|附录|表|图|有具体原因的缺口|
|---|---:|---:|---|
|A|7|0|A06|
|B|4|0|无|
|C|3|0|C04|
|D|2|1|无|
|E|2|0|无|
|F|2|0|F02|
|G|2|0|G03|
|H|3|0|H03|
|I|1|0|I02|
|J|19|1|J03|

## 核验

8项接口测试通过；54项只读导出核验通过。核验重点是文件/来源/需求对应、序列化数值、现成系数/指标/分箱不变，不重新审计研究算法。D/J两图实际查看。

实际从C:/Users/haoya运行J（保留项目工具授权上下文）成功；A–I共94文件内容和mtime未变；J共40表/图/数据文件哈希稳定。正式目录无时间版本目录；废弃文件/人工文件/回滚采用临时测试验证。

首次A导出因非必要tabulate依赖失败，已移除；目录权限拒绝曾使Windows tempfile长重试，已改为立即报错。外部工具任务根更换导致的写权限变化仍需运行者保留项目写入授权；授权上下文中所有附录已最终全量运行成功，无未解决的正式导出失败。提前于进程完成的快照未作为通过证据，已用完成后比对替代。

详细记录：APPENDIX_PRODUCTION_VERIFICATION.json；独立核验脚本：test/verify_appendix_exports.py。每次变更/测试/运行过程见LOG.md。

## 需要人工处理的证据缺口

A06：正文91%天气份额的分箱来源；C04：天气完整候选及正客户恢复完整梯级；F02：天气最终模型LAD-only SE；G03：最终OOF/分箱残差数值；H03：匹配当前最终规格的Gamma/Tweedie证据；I02：当前最终模型风暴预测；J03：已修复且口径匹配的proxy/ERA5全八任务公平对照。

各项对应的具体正文位置、证据不足原因和最小后续动作见results/Appendix/result_gaps.md；需要人工决定定位既有证据或限定写作，不自动重训。关闭事项不作为缺口待办。

## 文件入口

结果总览与逐附录README：results/Appendix/README.md；三层CSV映射及figure_table_register.csv在同目录；代码/覆盖说明：docs/APPENDIX_PRODUCTION_GUIDE.md。全部文件来源、输入/源码/输出SHA256及本次命令在各级manifest.json。

到此停止；未生成回传包、未同步GitHub、未撰写完整附录或修改正文。
