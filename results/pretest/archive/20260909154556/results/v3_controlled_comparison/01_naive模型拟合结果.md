# Step 2：用naive变量重新拟合 E0_naive、R0_naive、R0c_naive

规格与命令#9的E0'/R0'_A/R0c'_A完全一致（协变量集合、标准化方式、5折LAD聚类稳健标准误），仅将因变量/customers协变量替换为Step1构造的naive版本。

## 样本量

| 模型 | n | 说明 |
|---|---|---|
| E0_naive | 117,298 | customers_naive无缺失，全部117,298个事件入选 |
| R0_naive | 116,125 | duration_naive>0且≤p99（102.70小时）截尾后 |
| R0c_naive | 116,125 | 与R0_naive相同（customers_naive无缺失，不产生额外排除） |

## 逐折稳定性结果

### E0_naive（log1p(customers_naive)，n=117,298）

| 项 | 5折同号 | 5折显著 | 均值系数 | CV% |
|---|---|---|---|---|
| 阵风一次项 | 5/5 | 5/5 | -0.0303 | 19.30% |
| 阵风二次项 | 5/5 | 5/5 | 0.0646 | 13.54% |

### R0_naive（log(duration_naive)，n=116,125，未控制customers）

| 项 | 5折同号 | 5折显著 | 均值系数 | CV% |
|---|---|---|---|---|
| 阵风一次项 | 5/5 | 5/5 | 0.0317 | 13.26% |
| 阵风二次项 | 5/5 | 5/5 | 0.0433 | 22.77% |

### R0c_naive（log(duration_naive)，控制log1p(customers_naive)后，n=116,125）

| 项 | 5折同号 | 5折显著 | 均值系数 | CV% |
|---|---|---|---|---|
| 阵风一次项 | 5/5 | **5/5** | 0.0247 | 18.88% |
| 阵风二次项 | 5/5 | 5/5 | 0.0681 | 13.26% |
| customers_naive一次项 | 5/5 | 5/5 | -0.3749 | 1.12% |
| customers_naive二次项 | 5/5 | 5/5 | -0.1399 | 2.12% |

完整逐折系数见 `raw/E0_naive_fold_coefs.csv`、`raw/R0_naive_fold_coefs.csv`、`raw/R0c_naive_fold_coefs.csv`。

## 初步观察（详细对比与判断见 `02` 及 `05`）

**关键现象：R0c_naive控制customers_naive后，阵风一次项依然5/5折显著（未消失/未弱化）**，这与legacy R0c（控制后0/5折显著）以及命令#9的R0c'_A（控制后0/5折显著）的模式**不同**，反而与命令#9的R0c'_B（控制后5/5折显著）的模式相似。这一发现对Step5判断"duration_A效应消失是否为构造性关联"至关重要。
