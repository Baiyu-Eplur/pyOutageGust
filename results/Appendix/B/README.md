# 附录 B：事件重建与恢复样本

最近生成：2026-09-10T13:17:03+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices B`；项目根目录以脚本位置解析。

构造证据与当前固定输入描述分开保存；历史清理范围不可替代当前样本。

## 关键结果摘要

- zero_customers: n=8661；恰好1小时=5761（66.516569%）。
- positive_customers: n=51173；恰好1小时=259（0.506126%）。
- saved_R0c_input: n=59834；恰好1小时=6020（10.061169%）。

## 需求、产物与适用范围

### B01 — 事件构造规则和代表行修复证据

已生成。正文定位：§2.2 P019。C01清理计数为历史全事件构建范围，不能当作当前60437行回归样本。

- [tables/B_CONSTRUCTION_RULES.csv](tables/B_CONSTRUCTION_RULES.csv)

- [tables/B_CONSTRUCTION_RULES.md](tables/B_CONSTRUCTION_RULES.md)

- [tables/B_REPRESENTATIVE_REPAIR.csv](tables/B_REPRESENTATIVE_REPAIR.csv)

- [tables/B_REPRESENTATIVE_REPAIR.md](tables/B_REPRESENTATIVE_REPAIR.md)

### B02 — 在固定恢复输入上汇总零客户/正客户、1小时、A/B时长

已生成。正文定位：§2.2 P019; §2.3 P021。不从1小时峰直接推断自动重合闸；加权时长和跨度的差别不自动证明伪相关。

- [tables/B_RECOVERY_DEFINITION.csv](tables/B_RECOVERY_DEFINITION.csv)

- [tables/B_RECOVERY_DEFINITION.md](tables/B_RECOVERY_DEFINITION.md)

### B03 — 第一阶段对完整事件的已有比较

已生成。正文定位：§2.2 P019。仅保存既有文字证据及其历史样本说明；不把旧聚合均值直接当作当前E0重新计算结果。

- [tables/B03_EXISTING_DEFINITION.csv](tables/B03_EXISTING_DEFINITION.csv)

- [tables/B03_EXISTING_DEFINITION.md](tables/B03_EXISTING_DEFINITION.md)

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。
