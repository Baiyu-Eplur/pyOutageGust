# Step 2：VIF共线性检查

对命令#21 Step1最终拟合的E0、R0c两个模型规格，计算全部连续/二元协变量（不含年月固定效应哑变量，与v6论文`0519_4.1.py`及Appendix Table B1的做法一致——只报告主要连续协变量的VIF，固定效应哑变量不纳入VIF评估范围）的方差膨胀因子。

阈值参照：v6论文正文只引用O'Brien(2007)"对VIF经验法则的警示"作为方法论依据，未在正文给出具体数值阈值；本报告采用统计学常规阈值：**VIF>10需要认真关注，VIF>5建议留意，VIF<5一般视为无共线性问题**。

## E0（暴露）模型VIF

| 变量 | VIF |
|---|---|
| z_gust_0h | 1.90 |
| z_gust_0h_sq | 3.00 |
| z_precipitation_24h_sum | 1.40 |
| z_temperature_0h | 1.02 |
| z_pressure_msl_0h | 1.69 |
| z_gust_pressure（阵风×气压交互） | 2.57 |
| urban_binary | 1.16 |
| log_population | 1.34 |
| income_deprivation_rate | 2.58 |
| deprivation_gap_pct | **3.75**（全部变量中最高） |
| morans_i | 2.51 |

## R0c（恢复）模型VIF

| 变量 | VIF |
|---|---|
| z_gust_0h | 1.89 |
| z_gust_0h_sq | 3.00 |
| z_precipitation_24h_sum | 1.40 |
| z_temperature_0h | 1.03 |
| z_pressure_msl_0h | 1.69 |
| z_gust_pressure | 2.56 |
| urban_binary | 1.16 |
| log_population | 1.34 |
| income_deprivation_rate | 2.58 |
| deprivation_gap_pct | 3.76 |
| morans_i | 2.51 |
| z_log1p_customers_v2 | 1.90 |
| z_log1p_customers_v2_sq | 1.88 |

## 判断

**两个模型全部变量的VIF均远低于10，最高值（deprivation_gap_pct，约3.75-3.76）也明显低于5这一更严格的关注阈值**。E0与R0c两个模型的VIF数值几乎完全一致（因为两者共享几乎相同的自变量集合，只是R0c额外多了customers_v2两项，且customers_v2本身与其他协变量的VIF也不高），说明**当前最终模型规格不存在需要担忧的多重共线性问题**，这一结论可以直接写入论文附录B，替代/补充v6原有的Appendix Table B1（v6原表基于旧数据管线和legacy变量定义，本表基于命令#7-21确立的customers_v2/duration_B新定义和weather_natural+technical_asset主规格全量最终样本，口径已更新一致）。

完整数字见 `raw/step26_E0_vif.csv`、`raw/step26_R0c_vif.csv`。
