# 附录 E：事件级分期证据

最近生成：2026-09-10T13:17:05+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices E`；项目根目录以脚本位置解析。

Table 8是两个时期各自估计；不能称为冻结模型的后续预测。

## 关键结果摘要

E_PERIOD_COEFFICIENTS保存三个时期范围的已存关键项；两期各自拟合。DD-TIME01的冻结预测另见J。

## 需求、产物与适用范围

### E01 — 两期设计及已保存关键系数完整列出

已生成。正文定位：§3.3 P038; §4.5 P077; Table 8。两个时期分别拟合，规格沿用全期选择；不是开发期冻结预测。时期此前已用于探索。没有保存完整分期系数，不补训。

- [tables/E_PERIOD_COEFFICIENTS.csv](tables/E_PERIOD_COEFFICIENTS.csv)

- [tables/E_PERIOD_COEFFICIENTS.md](tables/E_PERIOD_COEFFICIENTS.md)

- [tables/E_TEMPORAL_DESIGN.csv](tables/E_TEMPORAL_DESIGN.csv)

- [tables/E_TEMPORAL_DESIGN.md](tables/E_TEMPORAL_DESIGN.md)

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。
