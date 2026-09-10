# 附录 A：数据、变量、原因与样本

最近生成：2026-09-10T13:17:03+01:00。本文件是中文产物整理说明，不是正式附录。

复现：`python main_appendix.py --appendices A`；项目根目录以脚本位置解析。

样本/变量、固定设计VIF和既有原因十分位表可整理；正文91%端点的分箱来源仍未定位。

## 关键结果摘要

- E0 / saved_input：n=60437，LAD=111，零客户=8979。
- E0 / final：n=60437，LAD=111，零客户=8979。
- E0 / weather_final：n=9857，LAD=105，零客户=572。
- R0c / saved_input：n=59834，LAD=111，零客户=8661。
- R0c / final：n=51173，LAD=111，零客户=0。
- R0c / weather_final：n=9254，LAD=104，零客户=0。
- E0当前全设计（含虚拟变量、不含截距）最大VIF=3.75484019。
- R0c当前全设计（含虚拟变量、不含截距）最大VIF=3.83742635。
- 原因十分位表为C01 corrected WT范围60453条；最高箱57.061864%，不冒充正文未定位口径的91%端点。

## 需求、产物与适用范围

### A01 — 固定输入的样本量、原因计数和日期/LAD覆盖

已生成。正文定位：§2.1 P015; §2.4 P026–027。恢复回归剔除零客户；不能把59834称为最终恢复样本。

- [tables/A_SAMPLE_FLOW.csv](tables/A_SAMPLE_FLOW.csv)

- [tables/A_SAMPLE_FLOW.md](tables/A_SAMPLE_FLOW.md)

- [tables/A_CAUSE_COUNTS.csv](tables/A_CAUSE_COUNTS.csv)

- [tables/A_CAUSE_COUNTS.md](tables/A_CAUSE_COUNTS.md)

- [tables/A_COVARIATE_SUMMARY.csv](tables/A_COVARIATE_SUMMARY.csv)

- [tables/A_COVARIATE_SUMMARY.md](tables/A_COVARIATE_SUMMARY.md)

### A02 — 变量、单位、来源、变换、参考水平

已生成。正文定位：§2.1 P015; §3.1 P031; Table 2。正文使用变换后OLS；不是GLM log link。地区变量定义复用旧附录A，不迁移旧同字母章节的结论。

- [tables/A_VARIABLE_DICTIONARY.csv](tables/A_VARIABLE_DICTIONARY.csv)

- [tables/A_VARIABLE_DICTIONARY.md](tables/A_VARIABLE_DICTIONARY.md)

### A03 — 原始原因代码映射

已有且被明确复用。正文定位：§2.4 P026–027。复用已有原因字典，未对监管原始代码重新审计；样本实际组别见A01。

- [tables/A03_EXISTING_DEFINITION.csv](tables/A03_EXISTING_DEFINITION.csv)

- [tables/A03_EXISTING_DEFINITION.md](tables/A03_EXISTING_DEFINITION.md)

### A04 — 固定最终设计矩阵的VIF描述统计

已生成。正文定位：§2.3 P021; §2.4 P028。复用原纯设计函数的隔离适配层，不执行旧模块顶层运行/拟合。全设计VIF与仅原始连续变量的VIF不是同一口径；不据此调整模型。

- [tables/A_FINAL_DESIGN_VIF.csv](tables/A_FINAL_DESIGN_VIF.csv)

- [tables/A_FINAL_DESIGN_VIF.md](tables/A_FINAL_DESIGN_VIF.md)

### A05 — 已有固定十分位原因构成数据

已生成。正文定位：§2.4 P027; §4.2 P058。既有十分位表约6.93%至57.06%；不把它解释成因果分解，也不能替代未定位的91%端点，见A06。

- [tables/A05_APPENDIXG_TABLE_G1_CORRECTED.csv](tables/A05_APPENDIXG_TABLE_G1_CORRECTED.csv)

- [tables/A05_APPENDIXG_TABLE_G1_CORRECTED.md](tables/A05_APPENDIXG_TABLE_G1_CORRECTED.md)

### A06 — 与91%端点匹配的既有分箱/计数

有具体原因的缺失。正文定位：§2.4 P027。

已找到的固定十分位表最高箱为57.06%，正文91%所用区间/样本计数未定位；两者不能直接替换。需要人工定位该句的分箱来源或按已存十分位证据限定文字，不新增分箱或推断原因。

## 来源与呈现

每份表的CSV为可编辑数字源，Markdown为阅读版；图表候选及显示编号由根目录figure_table_register.csv统一登记。完整来源、SHA256、调用函数和需求ID见manifest.json。

未定位或缺失不代表阴性结果；成功导出不代表科学主张得到独立验证。未修改主文、历史实验或原始数据。
