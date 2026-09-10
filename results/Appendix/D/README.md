# 附录 D：结点估计与已有不确定性

最近生成：2026-09-10T13:17:05+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices D`；项目根目录以脚本位置解析。

只整理既有结点profile/bootstrap/nested结果；不新增稳定性结论。

## 关键结果摘要

E0平台点估计全体14/25 m/s、天气11/24 m/s；既有300次bootstrap与自由分段500次分别列出。恢复自由分段和平台的样本量不同，表内保留各自n。未新增任何重采样。

## 需求、产物与适用范围

### D01 — 结点区间和训练折结点摘要

已生成。正文定位：§3.2 P035; §4.1 P049–051。自由双结点500次与平台300次bootstrap分别标注；R0c自由分段59834含零客户，平台51173/9254为正客户；平台是候选，不是正文最终二次恢复模型的结点。

- [tables/D_KNOT_SUMMARY.csv](tables/D_KNOT_SUMMARY.csv)

- [tables/D_KNOT_SUMMARY.md](tables/D_KNOT_SUMMARY.md)

- [tables/D_NESTED_FOLD_KNOTS.csv](tables/D_NESTED_FOLD_KNOTS.csv)

- [tables/D_NESTED_FOLD_KNOTS.md](tables/D_NESTED_FOLD_KNOTS.md)

### D02 — E0全体及天气平台profile与bootstrap补充图及最小数据

已生成。正文定位：§4.1 P049–051; P097。使用已保存profile网格和bootstrap样本；不重新搜索或bootstrap。

- [figures/D_PLATEAU_PROFILE_BOOTSTRAP.png](figures/D_PLATEAU_PROFILE_BOOTSTRAP.png)

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。
