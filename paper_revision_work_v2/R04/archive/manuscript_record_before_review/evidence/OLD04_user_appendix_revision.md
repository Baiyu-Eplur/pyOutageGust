# Paper 1 — Appendices (A–F)

> 与主文件 Paper1_Introduction_draft.md 配套的附录部分，已从主文件中拆分为独立文件。
> 引用规则与主文件一致：正文引用格式为 "Appendix A" 等，表格编号采用字母前缀（Table A1, B1...），与主文件正文的数字编号（Table 1-4）体系区分开，互不冲突。

---

## Appendix A. Variable definitions and data dictionary

### A.1 Outcome variables

Affected customers ($C_i$) and restoration duration ($D_i$) follow Equations 1 and 2 in Section 2.2. A small number of boundary cases, for which $C_i$ is undefined rather than zero, are treated as missing and excluded from the estimation sample. These cases are detailed in Appendix B.4. Restoration duration is computed from the start and end timestamps of all recorded stages, including those flagged as re-interruptions. The exclusion applied to affected customers is not applied to restoration duration, because a re-interruption stage still represents a period during which some customers are without supply, even though it is excluded from the customer count to avoid double-counting.

### A.2 Cause Code categories

UKPN records a numeric or short alphanumeric Cause Code for each incident. This paper groups these codes into six categories for analysis. Table A1 reports the original codes assigned to each category.

**Table A1.** Cause Code categories and their constituent original codes.

| Category | Original codes |
|---|---|
| Weather-related | 01, 02, 03, 04, 05, 06, 07, 10, 18, 21, 23, 24, 25, 30, 32, 33 |
| Asset-related | 14, 15, 16, 17, 19, 22, 26, 64, 67, 70, 71, 72, 73, 76, 77, 78, 90, A1, A2 |
| Third-party | 39, 40, 41, 42, 43, 44, 45, 48, 49, 50, 53, 54, 55, 56, 57, 58 |
| Human error | 60, 61, 62, 63, 65, 66, 68, 69, 81, 82, 83, 84 |
| External or customer | 74, 80, 85, 86, 87, 88, 89 |
| No fault found or unknown | 75, 97, 98, 99, D, X |

These category labels are an analytical grouping constructed for this paper. A published mapping from individual numeric codes to official descriptive names (for example, a specific meaning for code 01) was not located in the underlying project records, and is not required for the category-level analysis reported here.

### A.3 Regional covariates

Table A2 reports the source, computation, and granularity of each regional covariate.

**Table A2.** Regional covariate sources.

| Variable | Source | Computation | Granularity |
|---|---|---|---|
| Log population | ONS population estimates, detailed time series | Annual Local Authority District population estimates | LAD by year |
| Income deprivation rate | English Indices of Deprivation 2019, income deprivation domain | Official LAD-level rate, used as published | LAD, single cross-section |
| Deprivation gap | English Indices of Deprivation 2019 | Official LAD-level gap between local and national income deprivation, used as published | LAD, single cross-section |
| Moran's I | English Indices of Deprivation 2019 | Official LAD-level spatial clustering statistic for income deprivation, used as published | LAD, single cross-section |
| Urban-rural indicator | English Indices of Deprivation 2019, rural-urban classification | Binary indicator, coded 1 where the underlying text classification contains "urban" | LAD |

Moran's I, as used in this paper, is a published statistic describing the spatial clustering of income deprivation across neighbouring districts. It is not a spatial autocorrelation term computed on outage outcomes, and the two should not be conflated. Income deprivation rate, the deprivation gap, and Moran's I are all drawn from the same underlying deprivation dataset and are moderately to highly correlated with one another at the district level, as would be expected of related measures of the same underlying construct.

### A.4 Geographic boundaries

Local Authority District boundaries follow the December 2021 generalised boundary product published by the Office for National Statistics, in the British National Grid coordinate system (EPSG:27700). All geographic figures in this paper are projected to this coordinate system.

### A.5 Open items in the data dictionary

Two aspects of the underlying data could not be confirmed at the level of an official data dictionary or regulatory documentation. First, the exact meaning of incidents recorded with zero affected customers has not been confirmed. Candidate explanations, such as brief voltage disturbances or automatic reclosure events that do not correspond to a sustained loss of supply, remain plausible but unverified. This limitation is also noted in Section 5. Second, a separate field recording whether an incident was linked to an officially designated exceptional event is present in the underlying data, but is populated for only a small fraction of incidents and was not examined further in this paper.

## Appendix B. Data reconstruction: full evidence chain

### B.1 Comparison against the earliest-stage convention

Within the final analysis sample (n = 60,437), the mean of affected customers computed by aggregating across stages, following Equation 1, is 93.02. The mean computed using only the customer count reported in the earliest stage of each incident, the convention used when an incident is treated as equivalent to its first recorded stage, is 47.13. The two figures differ by a factor of 1.97 within the same sample.

### B.2 Choice of restoration duration measure

Two candidate measures of restoration duration were considered before settling on the definition used throughout this paper. The first, referred to during development as a customer-weighted average stage duration, weights each stage's duration by the number of customers affected at that stage. The second is the total incident span defined in Equation 2. Across the full reconstructed dataset (n = 135,025), the customer-weighted measure differs from the earliest-stage convention for 30.6 percent of incidents (those with more than one restoration stage), with a median relative difference of 54.3 percent among this subset.

The customer-weighted measure was found to share its underlying weighting denominator with affected customers by construction, producing a correlation between the two that is not present when a measure with a different pointwise construction is used instead. A counterfactual check, applying the same weighting logic to the current best simplified alternative, found that the coefficient collapse observed when controlling for the customer-weighted measure's construction does not occur when the shared-denominator relationship is absent. On this basis, the total incident span (restoration duration, as reported throughout this paper) was adopted in preference to the customer-weighted measure.

### B.3 Manual cross-check

A sample of 500 incidents (250 drawn from incidents with a single restoration stage and 250 from incidents with more than one stage, using a fixed random seed) was independently reconstructed directly from the underlying stage-level fields, without reference to any pre-aggregated columns in the dataset. Affected customers matched exactly for all 500 incidents. Restoration duration matched to within floating-point precision (maximum absolute difference on the order of $10^{-15}$ hours) for all 500 incidents.

### B.4 Boundary cases

Sixty-nine incidents, all with more than one recorded restoration stage, have every stage flagged as a re-interruption. For these incidents, affected customers is undefined under Equation 1 and is recorded as missing rather than zero. These incidents are excluded from both the exposure and recovery models on this basis.

### B.5 Incidents with an apparently missing first stage

Restoration stages are numbered sequentially within each incident. For 14,264 incidents (10.56 percent of the full reconstructed dataset of 135,025 incidents), the lowest recorded stage number is 2 or higher, meaning no stage numbered 1 is present in the data. This pattern is distributed evenly across the study period rather than concentrated at its boundaries, consistent with a general property of how stages are numbered in the underlying reporting system rather than a data quality problem specific to any part of the study period. These incidents are retained in the analysis sample without adjustment. A sensitivity check comparing results with and without these incidents was identified as a candidate check during data reconstruction but was not subsequently carried out.

## Appendix C. Sample restriction: full six-category comparison

A complete coefficient table, covering every covariate in the recovery model, is available for the two-category sample used as the main specification throughout this paper (Appendix F). An equivalent complete table for the full six-category sample was not produced during this project. Only the gust coefficients were compared across the two samples at the time this check was carried out. Table C1 reports this comparison.

**Table C1.** Gust coefficients, six-category sample versus the two-category main specification.

| Term | Six categories (n = 116,064) | Main specification (n = 59,834) |
|---|---|---|
| Linear term, same sign across folds | 5/5 | 5/5 |
| Linear term, significant folds | 5/5 | 0/5 |
| Linear term, mean coefficient | 0.0257 | 0.0002 |
| Quadratic term, same sign across folds | 5/5 | 5/5 |
| Quadratic term, significant folds | 5/5 | 5/5 |
| Quadratic term, mean coefficient | 0.0608 | 0.0792 |
| Quadratic term, coefficient of variation | 19.82% | 12.5% |

Restricting the sample from six categories to the two used as the main specification leaves the quadratic term essentially unchanged in magnitude and fold-level significance, while the linear term collapses from a stable, significant effect to one indistinguishable from zero.

## Appendix D. The apparent non-monotonic relationship between affected customers and restoration duration

Section 2.3 reports that affected customers and restoration duration are close to independent under linear and monotonic measures of association, but not under a nonlinear dependence measure. This appendix reports the investigation behind that finding and behind the treatment of affected customers as a covariate in the recovery model.

### D.1 Number of restoration stages

Restoration stages per incident, denoted $n_{stages}$, range from a single stage to several hundred. The investigation in Sections D.1 to D.6 was carried out on the development sample described in Section 3.2 (n = 47,840), a subset of the final combined sample (n = 59,834) used elsewhere in this paper. Table D1 reports the distribution of restoration stages within this development sample.

**Table D1.** Distribution of restoration stages per incident.

| Stages | n | Share |
|---|---|---|
| 1 | 28,328 | 59.2% |
| 2 | 7,563 | 15.8% |
| 3–4 | 6,361 | 13.3% |
| 5–9 | 4,786 | 10.0% |
| 10+ | 802 | 1.7% |

### D.2 Relationship within incidents with a single stage

Among incidents with exactly one restoration stage (59.2 percent of the sample), affected customers and restoration duration show a monotonic negative relationship: mean restoration duration falls from 11.45 hours in the lowest range of affected customers to 3.80 hours in the highest range, with the two lowest ranges close to one another and the decline concentrated at higher values of affected customers.

### D.3 Relationship within incidents with more than one stage

Among incidents with more than one restoration stage, the same relationship is also monotonically negative, both pooled across all such incidents and within each stratum defined by the exact number of stages (two stages, three to four stages, and five or more stages). No individual stratum shows a rise followed by a fall.

### D.4 Source of the apparent non-monotonic pattern in the pooled sample

When affected customers and restoration duration are examined without separating incidents by the number of restoration stages, the relationship between them appears to rise and then fall. This pattern arises because incidents with more restoration stages both tend to have higher affected customers, by construction, and tend to have longer restoration durations, for reasons unrelated to affected customers itself. As affected customers increases, the pooled sample contains a growing share of multi-stage incidents, which carries longer typical restoration durations into the middle of the affected-customers range. This composition shift, not a direct effect of affected customers on duration, accounts for the rising portion of the pooled pattern.

Figure D1 illustrates this directly. Affected customers is divided into four quartile bins computed on the full sample (n = 59,834), a common set of bins applied across all four restoration-stage strata so that the two panels can be compared on the same horizontal axis. These bins differ from the subset-specific quantile bins used in Sections D.1 and D.3, which were computed separately within each subset and are not comparable to one another on a shared axis. Figure D1a shows mean restoration duration by this shared customer bin, separately for each stratum. Figure D1b shows the same relationship without separating by stratum.

In Figure D1a, three of the four strata (single-stage, two-stage, and three-to-four-stage incidents) decline from the first bin onward, with the three-to-four-stage stratum showing the steepest decline, from 40.6 hours in the lowest bin to 9.4 hours in the highest. The stratum of five or more stages does not show a clean decline under this shared binning: mean duration rises from the lowest to the second bin before levelling off and then declining slightly. The lowest two bins for this stratum contain only 22 and 18 incidents respectively, because multi-stage incidents rarely fall into the lowest customer bins, and this pattern is treated as a small-sample artefact of the shared binning rather than as a systematic feature of this stratum, which shows a mild decline under its own subset-specific bins in Section D.3. In Figure D1b, the pooled relationship rises from 11.65 hours in the lowest bin to a peak of 14.19 hours in the second bin, before declining to 9.87 hours in the highest bin. No stratum in Figure D1a shows a comparable rise over the same two bins, other than the small-sample pattern noted above.

**Figure D1.** Mean restoration duration by affected-customers quartile bin (computed on the full sample). (a) By number of restoration stages. (b) Pooled across all incidents, without separating by stage count.

### D.5 Regression evidence

Table D2 reports the coefficients on affected customers in the recovery model, with and without a control for the logarithm of the number of restoration stages, estimated on the development sample described in Section D.1 (n = 47,840). These coefficients differ from the corresponding uncontrolled coefficients reported for the final combined sample in Table F2 (n = 59,834, affected customers coefficients of 0.339 and -0.396), because the two tables use different samples under an otherwise identical specification, not because of any difference in method.

**Table D2.** Affected-customers coefficients, with and without a restoration-stages control.

| Term | Without control | With control for log(stages) |
|---|---|---|
| Linear term | +0.307 (p < 0.001) | -0.236 (p < 0.001) |
| Quadratic term | -0.381 (p < 0.001) | -0.301 (p < 0.001) |
| log(stages) | — | +0.971 (p < 0.001) |

Controlling for the number of restoration stages reverses the sign of the linear term and reduces the magnitude of the quadratic term by approximately one fifth, while the quadratic term remains negative and highly significant. The turning point implied by the controlled coefficients falls at a low value of affected customers, close to the dense part of its observed distribution, rather than above the sample mean as in the uncontrolled specification. Across the range of affected customers actually observed, the controlled relationship is close to monotonically declining rather than showing a rise followed by a fall.

### D.6 Interpretation

The rising portion of the uncontrolled relationship between affected customers and restoration duration is attributable to the number of restoration stages. It does not appear within incidents with a single stage, nor within any stratum of incidents by stage count. It also does not appear once the number of stages is controlled for in the pooled regression, at which point the coefficient on affected customers reverses in sign. The declining portion of the relationship persists in reduced form after this control, and the number of restoration stages is itself a strong positive predictor of duration. This association is not a strict logical consequence of how stages are counted, since multiple stages recorded within an unchanged overall time window would not by themselves lengthen that window, but it holds consistently across the data examined here. The number of restoration stages is also not necessarily a pre-existing characteristic of an incident independent of its development: it may itself reflect the complexity of the fault or the sequencing of restoration work, rather than a simple external confounder. On this basis, the apparent non-monotonic relationship between affected customers and restoration duration reported in Section 2.3 is treated as a composition effect linked to the number of restoration stages, rather than as an independent effect of the scale of an incident on its own. Controlling for the number of stages changes the coefficient on affected customers, which is consistent with this composition effect, but does not on its own identify a specific mechanism, such as restoration-crew prioritisation, as the reason for the association. The gust coefficients reported throughout this paper are stable whether or not this control is included.

### D.7 The same investigation within the weather-attributed subsample

This section uses the weather-attributed subsample drawn from the final combined sample, as examined in Section 4.3, rather than the development-sample-only basis of Sections D.1 to D.6 above. The subsample restricted to incidents for which weather is the recorded cause contains a higher share of multi-stage incidents (49.7 percent) than the main specification (40.7 percent). Within this subsample, the relationship between affected customers and restoration duration among single-stage incidents is again monotonically negative, consistent with the main specification.

The regression evidence in this subsample does not fully match the pattern described above. Without controlling for the number of restoration stages, the coefficient on affected customers is already negative in this subsample, rather than positive as in the main specification. Controlling for the number of restoration stages makes this coefficient more negative still, rather than reversing its sign. The number of restoration stages remains a strong positive predictor of duration in this subsample, as in the main specification. This pattern is consistent in direction with the interpretation given above, in that the coefficient becomes more negative once restoration stages are accounted for in both cases, but it does not reproduce the specific mechanism described in Section D.6, under which the composition effect is what produces a positive coefficient in the first place. This is reported here as an open question. It does not affect the gust coefficients reported for this subsample in Section 4.3.

## Appendix E. Discovery and correction of development-sample contamination

An earlier version of the development sample used to establish the model specification in Sections 2 and 3 was found to include a portion of the period later designated as the confirmation sample. The confirmation sample, covering 30 September 2023 to 31 March 2024 (184 consecutive days), was subsequently separated out and excluded from all specification decisions. Table E1 reports the extent of this overlap across three stages of sample construction.

**Table E1.** Extent of development-sample contamination before correction.

| Stage | Contaminated sample | Corrected sample | Removed | Share removed |
|---|---|---|---|---|
| Full reconstructed dataset | 135,025 | 109,250 | 25,775 | 19.09% |
| After Cause Code restriction | 66,079 | 53,114 | 12,965 | 19.63% |
| After weather matching | 62,927 | 50,345 | 12,582 | 20.00% |

The share of contamination remains close to one fifth of the sample at each stage of construction.

A small number of incidents (32, or 0.03 percent of the corrected development sample) begin within the development period but extend into the confirmation period. These incidents were retained in the development sample on the basis of their start date, because the weather covariates used throughout this paper are constructed from conditions at and before the start of each incident and do not depend on how the incident subsequently resolves.

Table E2 reports the effect of this correction on the exposure margin's critical wind speed, alongside the final estimate reported in Section 4.1.

**Table E2.** Critical wind speed for the exposure margin, before and after correction.

| Sample | n | Point estimate (m/s) | Coefficient of variation across folds | Bootstrap interval crosses zero (standardised scale)? |
|---|---|---|---|---|
| Contaminated development sample | approx. 60,453 | 10.69 | 38.6% | Yes |
| Corrected development sample | 48,323 | 12.13 | 22.0% | No |
| Final combined sample (development and confirmation) | 60,437 | 10.69 | — | Yes |

The point estimate for the final combined sample coincides numerically with the estimate from the contaminated sample, but this reflects a different underlying sample composition: the contaminated sample mixed development and confirmation data without separating them for validation purposes, whereas the final combined sample deliberately pools the corrected development sample with the confirmation sample after both have served their separate roles in model development and confirmation.

## Appendix F. Full robustness results under single and two-way clustering

Section 4.4 reports the two-way clustering result for the core gust coefficients. Tables F1 and F2 report the full coefficient set for both models, comparing standard errors clustered by Local Authority District alone against standard errors clustered by both district and date. Point estimates are identical under both clustering methods, because clustering affects only the standard errors, not the coefficients themselves.

**Table F1.** Exposure model, full coefficient set under single and two-way clustering.

| Term | Coefficient | SE (LAD) | p (LAD) | SE (two-way) | p (two-way) |
|---|---|---|---|---|---|
| Intercept | 3.321 | 1.045 | 0.0015 | 1.049 | 0.0015 |
| Gust (linear) | -0.032 | 0.014 | 0.022 | 0.022 | 0.142 |
| Gust (squared) | 0.103 | 0.009 | <0.001 | 0.031 | <0.001 |
| Precipitation | 0.049 | 0.011 | <0.001 | 0.016 | 0.003 |
| Temperature | -0.009 | 0.020 | 0.660 | 0.041 | 0.829 |
| Pressure | -0.084 | 0.011 | <0.001 | 0.022 | <0.001 |
| Gust × pressure | -0.041 | 0.009 | <0.001 | 0.025 | 0.102 |
| Urban indicator | -0.158 | 0.077 | 0.039 | 0.077 | 0.040 |
| Log population | -0.079 | 0.089 | 0.375 | 0.089 | 0.375 |
| Income deprivation rate | -3.203 | 0.905 | <0.001 | 0.916 | <0.001 |
| Deprivation gap | 0.178 | 0.548 | 0.745 | 0.545 | 0.743 |
| Moran's I | -0.027 | 0.241 | 0.909 | 0.240 | 0.909 |
| Year and month fixed effects | (26 terms, see project data files) | | | | |

**Table F2.** Recovery model, full coefficient set under single and two-way clustering.

| Term | Coefficient | SE (LAD) | p (LAD) | SE (two-way) | p (two-way) |
|---|---|---|---|---|---|
| Intercept | 1.678 | 0.259 | <0.001 | 0.268 | <0.001 |
| Gust (linear) | 0.000 | 0.009 | 0.982 | 0.017 | 0.991 |
| Gust (squared) | 0.079 | 0.006 | <0.001 | 0.008 | <0.001 |
| Precipitation | 0.050 | 0.006 | <0.001 | 0.009 | <0.001 |
| Temperature | -0.073 | 0.010 | <0.001 | 0.018 | <0.001 |
| Pressure | -0.039 | 0.008 | <0.001 | 0.015 | 0.009 |
| Gust × pressure | 0.025 | 0.009 | 0.007 | 0.016 | 0.105 |
| Urban indicator | 0.136 | 0.037 | <0.001 | 0.037 | <0.001 |
| Log population | 0.014 | 0.023 | 0.525 | 0.023 | 0.527 |
| Income deprivation rate | 0.160 | 0.541 | 0.768 | 0.543 | 0.769 |
| Deprivation gap | -0.176 | 0.466 | 0.706 | 0.462 | 0.704 |
| Moran's I | 0.262 | 0.126 | 0.037 | 0.124 | 0.034 |
| Affected customers (linear) | 0.339 | 0.020 | <0.001 | 0.023 | <0.001 |
| Affected customers (squared) | -0.396 | 0.021 | <0.001 | 0.023 | <0.001 |
| Year and month fixed effects | (26 terms, see project data files) | | | | |

Standard errors are generally wider under two-way clustering than under single clustering. The quadratic gust term remains significant beyond conventional thresholds under both clustering methods, for both models. The linear gust term and the gust-pressure interaction term lose significance under two-way clustering for the exposure margin. For the recovery margin, the gust-pressure interaction term likewise loses significance, while the linear gust term, already not significant under single clustering, remains not significant. This is the only systematic pattern of weakening observed across the full covariate set. The same pattern, in which the linear and interaction terms lose significance while the quadratic terms remain significant, was also found when this check was independently repeated on an earlier version of this dataset.

## Appendix G. Cause Code assignment and gust speed

Section 4.3 reports that gust's marginal contribution to the exposure margin becomes negative within the subsample restricted to incidents for which weather is the recorded cause. This appendix reports the evidence behind the proposed explanation, that Cause Code assignment is not independent of gust speed.

Incidents in the final combined sample were grouped into ten equally sized bins by gust speed, and the share assigned to the weather-related Cause Code category was computed within each bin. This share rises from 6.89 percent in the lowest bin to 56.10 percent in the highest bin, increasing at every one of the nine steps between adjacent bins.

**Table G1.** Share of incidents assigned to the weather-related Cause Code category, by gust decile.

| Gust decile | Share weather-related |
|---|---|
| Lowest | 6.89% |
| 2nd | 8.07% |
| 3rd | 9.55% |
| 4th | 9.74% |
| 5th | 10.64% |
| 6th | 11.05% |
| 7th | 12.78% |
| 8th | 15.74% |
| 9th | 23.30% |
| Highest | 56.10% |

An incident occurring in calm weather is therefore markedly less likely to be classified as weather-related than an otherwise similar incident occurring in strong wind. As a consequence, the subsample of weather-attributed incidents is disproportionately drawn from higher-gust conditions. Of the incidents below the exposure margin's turning point (10.69 m/s), 63.70 percent fall within the full combined sample, compared with only 36.83 percent within the weather-attributed subsample. This selective depletion of low-gust observations is consistent with the negative marginal contribution reported for the exposure margin in Table 4, and with the recovery margin being less affected, since its quadratic coefficient does not depend on locating a precise turning point.

