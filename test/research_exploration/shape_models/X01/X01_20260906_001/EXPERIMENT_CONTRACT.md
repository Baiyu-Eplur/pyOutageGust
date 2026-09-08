# X01 experiment contract

This independent run is frozen before any candidate leaderboard is read. It uses the copied event snapshot in `frozen_sources/input/R02_event_master.parquet` (SHA-256 `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`) and never writes outside this run directory.

## Estimands and samples

- **E:** recorded event-level arithmetic mean customers, `C_id_formula`, including valid zeros, Poisson working-mean loss.
- **R:** recorded event-level arithmetic mean recovery span in hours, `D_id_formula > 0`, Gamma-type working-mean loss.
- **R_C:** R conditional on final `log1p(C)` and its square; it is an after-the-event conditional analysis, not a planning or causal estimand.

All models within task use the same rows, controls, groups and folds. Controls are: `pressure_msl_0h, temperature_0h, precipitation_24h_sum, log_population, income_deprivation_rate, deprivation_gap_pct, morans_i, urban_binary, calendar_sin, calendar_cos, calendar_trend, cause_asset`. The common new specification has pressure as a main effect and **no gust × pressure interaction**.

## Model and scoring contract

The shared mean model is `mu=exp(alpha+x gamma) r(g)`, with the training-fold median gust as `g_ref` and `r(g_ref)=1`. E uses `mu-y log(mu)`; R/R_C use `log(mu)+y/mu`. The primary score is the corresponding mean OOF deviance, then raw-scale RMSE, MAE, bias, total prediction/observation and pooled OOF R². These are working mean losses, not a claim that the whole outcome distribution is Poisson or Gamma; no AIC or likelihood-ratio inference is used.

M00–M08 are the nine formulas specified in the frozen X01 instruction. The CDF families use baseline 1 plus an overall intercept, preventing `a`, `A` and intercept scale non-identifiability. Baseline 1 is a parameterization device, not one customer or one hour. M03 is an unrestricted cubic B-spline; M04 is a cubic B-spline with nondecreasing coefficients, which guarantees a nondecreasing spline. M03/M04 tune only `n_basis in {6,10}` and smoothing penalty `lambda in {0.005,0.05}` using inner protected group folds. Nonlinear candidates use no more than ten deterministic starts and pre-registered finite parameter bounds.

## Validation and uncertainty

Outer evaluation uses five deterministic, balanced folds of 14-day UTC blocks. Blocks touching the same named storm window are unioned. Training observations within 48 hours of any test block are purged. It is therefore called **time-block CV with known-storm protection and buffers**, not full weather-process isolation or a future confirmation set. Inner selection uses three grouped folds with the same purge rule.

A 1,000-resample paired group bootstrap is conditional on fixed OOF predictions. Two competitive curve candidates per task receive 200 group-bootstrap refits with the full-data selected spline hyperparameter held fixed. Neither procedure includes all tuning or model-selection uncertainty.
