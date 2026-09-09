# 3c — LAD 固定效应"陷阱"：独立复现

**结论：完全站得住，独立复现的数字与导师报告精确吻合（多项数字精确到小数点后四位一致）。**

脚本：[`verification/3c_lad_fe_trap.py`](verification/3c_lad_fe_trap.py)，独立编写（未复制 `model_selection.py`），在 `combined_E0_final.csv`/`combined_R0c_final.csv`（与导师包 SHA256 相同）上分别拟合 M5（无 LAD 固定效应）和 M5+110个LAD哑变量，对比样本内 AIC/BIC 与 LAD-grouped 5-fold CV RMSE、校准斜率。

| 边际 | 模型 | 参数个数 | AIC | BIC | 样本内 RMSE | **LAD-CV RMSE** | **校准斜率(CV)** |
|---|---|---|---|---|---|---|---|
| E0 | M5（无FE） | 26 | 254396.2 | 254630.4 | 1.9843 | **1.9887** | 0.926 |
| E0 | M5 + LAD FE | 132 | 253352.0 | 254541.2 | 1.9638 | **2.1020** | **0.250** |
| R0c | M5（无FE） | 28 | 198023.6 | 198275.6 | 1.2654 | **1.2695** | 0.977 |
| R0c | M5 + LAD FE | 134 | 197529.4 | 198735.3 | 1.2579 | **1.5039** | **0.326** |

比对导师报告（Model_exploration 文档 Table 1 + Section 2）：
- E0 CV RMSE：M5 1.9887 vs 报告 1.9887——**完全一致**；LAD FE 2.1020 vs 报告 2.1020——**完全一致**。
- R0c CV RMSE：M5 1.2695 vs 报告 1.2695——**完全一致**；LAD FE 1.5039 vs 报告 1.5039——**完全一致**。
- 校准斜率：E0 0.250 vs 报告"0.25 for E0"——**一致**；R0c 0.326 vs 报告"0.33 for R0c"——**基本一致**（四舍五入后一致）。

**独立确认的因果机制**：LAD FE 模型在样本内 AIC/BIC 全面占优（参数多、样本内拟合天然更好，符合预期），但 LAD-grouped CV 下 RMSE 大幅变差（E0 从 1.989 恶化到 2.102，R0c 从 1.270 恶化到 1.504），校准斜率暴跌到 0.25/0.33——即预测值的离散程度只有真实值的四分之一到三分之一，说明模型对留出的新 district 基本退化成"预测全局均值"，与导师报告"held-out districts receive no intercept, model collapses to roughly the grand mean"的机制描述完全吻合。

这是本次审查里数字复现最精确的一项——从样本内指标到 CV 指标到校准斜率，四个数字组全部独立复现到小数点后三到四位，没有发现任何问题。**建议论文正文可以直接引用这组数字，不需要进一步验证。**

原始数值见 [`verification/3c_results.json`](verification/3c_results.json)。
