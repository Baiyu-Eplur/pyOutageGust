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

The original verification used Python 3.12.6. From the package directory:

```sh
python -m pip install -r requirements.txt
python code/run_main_regression.py
```

The script resolves paths relative to its own location, reads the two supplied
samples and overwrites the four coefficient tables and summary JSON in `results/`.
No files from the main project are required to run the regression. Construction
of the analysis samples from raw records is outside this package's scope.

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
