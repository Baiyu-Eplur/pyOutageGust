# J_FROZEN_EXPERIMENT_DEFINITIONS

需求 J08；J.6。方法/用途/不可支持解释的简明登记。

分析单位：LAD-day。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

不声称等效、统计显著或完全校准；不自动提出模型替换。

| experiment | item | definition |
| --- | --- | --- |
| DD-AGG01 | candidates.A01_daily_max | "max(g)" |
| DD-AGG01 | candidates.A02_daily_mean | "sum(g)/24" |
| DD-AGG01 | candidates.A03_daily_q90 | ".3*sorted(g)[20]+.7*sorted(g)[21]" |
| DD-AGG01 | candidates.A04_top3_mean | "mean(sorted(g)[-3:])" |
| DD-AGG01 | candidates.A05_max_rolling3h_mean | "max(mean(g[h:h+3]) for h in range(22))" |
| DD-AGG01 | model | p0+(1-p0)*Phi((log(A)-log(theta))/beta); A=0 -> p0 |
| DD-AGG01 | calibration | common quantiles 0..1 by .1 pooled from valid five OOF predictions per task, add 0/1, unique edges; searchsorted right; n<100 isolated crosses; empty NaN; weighted RMSE |
| DD-AGG01 | target_rule | gt0 means any event including zero customers; other thresholds strictly > k; existing panel labels unchanged |
| DD-AGG01 | timezone | UTC |
| DD-AGG01 | unit | m/s |
| DD-AGG01 | folds.path | "D:\\Pyprogramme\\pyOutageGust\\results\\new\\20260909205214\\results\\p03_p04\\lad_folds.csv" |
| DD-AGG01 | folds.sha256 | "b3a557dd043cc92c1029a0b6da006231854afb118be7260b649280fe1983b303" |
| DD-AGG01 | folds.rule | "read original fold labels, never regenerate" |
| DD-AGG01 | uncertainty.repeats | 1000 |
| DD-AGG01 | uncertainty.seed | 20260909 |
| DD-AGG01 | uncertainty.unit | "paired LAD, fixed OOF" |
| DD-AGG01 | uncertainty.limitations | "No retraining, selection adjustment, or full storm/date dependence" |
| DD-DUR01 | features.G | "max hourly gust" |
| DD-DUR01 | features.H | "sum(g>tau)*1h" |
| DD-DUR01 | features.h | "H/24h" |
| DD-DUR01 | features.I | "sum(max(g^2-tau^2,0))*1h" |
| DD-DUR01 | features.J | "I/(24h*tau^2)" |
| DD-DUR01 | features.x | "log1p(J)" |
| DD-DUR01 | models.M0 | "p0+(1-p0)Phi((log G-log theta)/beta)" |
| DD-DUR01 | models.M1 | "same with z += gamma*h" |
| DD-DUR01 | models.M2 | "same with z += gamma*x" |
| DD-DUR01 | tau | 90th percentile linear of ALL training LAD-hour rows; shared grid LADs not deduplicated; full threshold never used for CV |
| DD-DUR01 | calibration | valid three-model pooled OOF deciles, add0/1 unique; side=right; empty NaN; n<100 isolated; full+supported-bin shared zoom with tail count |
| DD-DUR01 | labels | existing panel unchanged; any event includes zero-customer records; other thresholds strictly >k |
| DD-DUR01 | timezone | UTC |
| DD-DUR01 | hour_unit | m/s |
| DD-DUR01 | folds_path | D:\Pyprogramme\pyOutageGust\results\new\20260909205214\results\p03_p04\lad_folds.csv |
| DD-DUR01 | uncertainty.repeats | 1000 |
| DD-DUR01 | uncertainty.seed | 20260909 |
| DD-DUR01 | uncertainty.unit | "paired LAD fixed OOF, shared draws, row weights" |
| DD-DUR01 | uncertainty.excludes | "retraining, threshold re-estimation, model selection, shared date/storm dependence" |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
