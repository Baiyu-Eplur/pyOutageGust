# pyOutageGust review_package — Main Regression Model Review Package

This package fits the exposure margin (E0) and recovery margin (R0c) models
for the UK Power Networks weather-outage analysis. Both use a quadratic gust
specification with LAD-clustered and LAD-by-date two-way-clustered standard
errors. The script also calculates the E0 gust turning point at mean pressure.

The supplied samples incorporate the C01–C08 corrections. C01 changed event
representative-row selection from raw file order to earliest actual start time,
affecting matched weather values for 13.57%/13.56% of the exposure/recovery
samples. C02–C08 addressed reference-scenario, double-log-transform,
sample-truncation and related display or validation issues. The covariates,
functional form and estimation method were retained.

## Files

2026-09-09 入口调整后，下表中的 `results/` 路径为历史路径，已有文件已归档到
`../results/pretest/archive/20260909154556/review_package/results/`。
新的回归结果进入 `../results/pretest/models/<YYYYMMDDHHMMSS>/<步骤序号>/review_package/regression/`。

| Path | Contents |
|---|---|
| `code/run_main_regression.py` | Model fitting and output |
| `code/PROVENANCE.md` | Source references, adaptations and recorded code comparisons |
| `requirements.txt` | Package versions recorded for the original verification |
| `data/combined_E0_final.csv` | Exposure sample, 60,437 observations |
| `data/combined_R0c_final.csv` | Recovery sample, 59,834 observations |
| `results/E0_corrected_lad_cluster.csv` | E0 coefficients with LAD-clustered standard errors |
| `results/E0_corrected_twoway_cluster.csv` | E0 coefficients with LAD-by-date standard errors |
| `results/R0c_corrected_lad_cluster.csv` | R0c coefficients with LAD-clustered standard errors |
| `results/R0c_corrected_twoway_cluster.csv` | R0c coefficients with LAD-by-date standard errors |
| `results/run_summary.json` | Sample sizes, E0 gust coefficients and turning point |
| `results/verification_report.md` | Recorded comparison with archived results and draft-table discrepancy |

## Run

在项目根目录 `main.py` 中填写运行目的，开启 `review_package/run_main_regression`，然后运行：

```sh
conda activate pyoutagegust
python main.py
```

若需要重新构造样本，同时开启 `model_review_package_20260907/materialize_final_data`。
否则读取最近成功生成的样本，或复用这里现有的两份静态 CSV。当前代码通过主项目的
pretest 路径模块运行；不再直接覆盖此目录下的旧结果。原独立交付版本可从
`pre-review-checkpoint-20260909` Git 标签查阅。

## Reference output

Selected rows from the LAD-clustered coefficient tables:

| Model | Term | Coefficient | Std. error | p-value |
|---|---|---|---|---|
| E0 | z_gust_0h (linear) | -0.036014 | 0.013974 | 0.009958 |
| E0 | z_gust_0h_sq (quadratic) | 0.105997 | 0.008348 | 6.08e-37 |
| R0c | z_gust_0h (linear) | -0.000993 | 0.009089 | 0.913032 |
| R0c | z_gust_0h_sq (quadratic) | 0.084954 | 0.006127 | 1.01e-43 |

The E0 turning point is **10.8072 m/s**. Sample sizes are 60,437 (E0) and
59,834 (R0c). The recorded comparison with archived results found a maximum
absolute coefficient-table difference of 3.51e-13; details are in
`results/verification_report.md`.

## Source and manuscript alignment

Source functions and adaptations are listed in `code/PROVENANCE.md`. The package
reads exported analysis samples, uses local function references and writes to
its own results directory. Comments and documentation have been edited.

At package preparation, the paper draft's Table 2 still contained pre-C01
coefficients. Those values differ from the corrected output above. The recorded
discrepancy and both sets of values are retained in `results/verification_report.md`;
the manuscript table needs to be reconciled before comparison with this package.
