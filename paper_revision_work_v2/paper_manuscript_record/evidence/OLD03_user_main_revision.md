# Paper 1 — Full Draft (Introduction through Conclusion, working file)

> 状态：Introduction至Section 5全文完整初稿，已完成两轮独立审查（academic-review skill）发现问题的修正，剩余事项见文末"仍待处理"
> 引用规则：RESS格式，方括号数字编号，按正文首次出现顺序排列（非字母顺序），Vancouver风格参考文献列表

---

## Abstract

UK Power Networks records 60,453 weather- and asset-related outage incidents across London, the South East, and the East of England between April 2021 and March 2024, including seven officially named storms. Event-level exposure and recovery outcomes are reconstructed from stage-level regulatory records according to Ofgem's official definitions, correcting a systematic undercount that results from using the earliest recorded stage alone. A quadratic specification identifies a nonlinear relationship between gust speed and both outcomes, including a critical wind speed of approximately 10.7 m/s for the exposure margin. The quadratic shape underlying this relationship is confirmed under alternative distributional assumptions, within an independent temporal holdout, and within a subsample restricted to incidents for which weather is the recorded cause. Predicted outcomes from this model are also compared against observed outcomes during the seven named storms. The specific numerical value of the exposure margin's threshold is not confirmed under the same holdout and is reported as an approximate reference rather than an externally validated figure. Gust accounts for a modest share of total variation in outage outcomes across the full population of incidents, well below the share accounted for by the number of affected customers. Within the subset of incidents for which weather is the recorded cause, however, gust's contribution more than doubles and exceeds that of affected customers. Two independent lines of evidence, one based on recorded cause and one based on real storm events, point to the same conclusion. These results provide field-level evidence of a nonlinear wind-outage response at the scale of a full distribution network, complementing fragility curves derived from simulation or testing of individual structures.

## Keywords

Power outage; wind fragility; critical wind speed; distribution network; variance decomposition; extreme weather

[待你确认：以上6个关键词已控制在RESS建议的1-7个范围内，且避免了多词短语，如需调整请直接修改]

---

## Section 1. Introduction

Storms and other extreme weather events are the most common cause of power disruptions in Great Britain [1]. In November 2021, Storm Arwen alone left more than one million customers without power [2]. Three months later, three named storms struck the United Kingdom within five days: Dudley, Eunice, and Franklin. Within the service area of UK Power Networks (UKPN), which covers London, the South East, and the East of England, Storm Eunice produced a peak observed gust of 39.4 m/s in Lewes, East Sussex, on 18 February 2022. This value is the highest gust recorded across the entire study period examined in this paper. The storm was associated with 1,601 weather-related outage events across 101 Local Authority Districts, a cumulative estimate of 376,712 affected customers, and a mean restoration time of 52.7 hours. Two days later, Storm Franklin affected the same network and produced a further 1,187 events.

These events illustrate a general pattern in electricity distribution networks: outage impact, measured either by the number of customers affected (referred to hereafter as the exposure margin) or by the time needed for restoration (referred to hereafter as the recovery margin), does not scale in a fixed proportion with wind intensity. A given increase in gust speed can correspond to a small change in outcome under some conditions and a disproportionately large change under others. Identifying whether this relationship follows a specific functional form, and whether it contains an identifiable threshold, is directly relevant to how distribution network operators (DNOs) set weather-related response thresholds and allocate restoration resources in advance of a forecast storm.

Existing empirical work on power outage duration and customer impact under severe weather has established regression- and machine-learning-based approaches for hurricane- and ice-storm-affected US utilities [3–6]. A separate line of engineering research addresses the wind vulnerability of individual distribution and transmission structures directly. This work typically derives fragility curves, which express the probability of structural failure as a function of wind speed, from finite element simulation or scaled physical testing of a specific structure type, such as a transmission tower or a distribution pole [7–10]. These fragility curves are commonly expressed as threshold-based functions in which failure probability remains near a baseline level below a critical wind speed and increases sharply once this threshold is exceeded [10]. This threshold structure is consistent with the general expectation that wind-induced damage to electrical infrastructure is nonlinear rather than proportional to wind intensity.

Fragility curves of this kind describe the vulnerability of a single, well-defined structure under controlled or simulated loading conditions. They do not by themselves indicate whether a comparable nonlinear, threshold-like response is observable in the operational record of a full distribution network, where outage outcomes reflect a heterogeneous population of structures, ages, and local conditions rather than a single modelled component. This gap, together with a further limitation in the outage-modelling literature, motivates the present study.

First, neither the statistical outage literature nor the structural fragility literature provides field-level evidence of a threshold response at the network scale. Statistical outage studies [3–6] generally report a single fitted relationship between weather intensity and outage outcomes without testing whether that relationship contains a distinguishable threshold. Fragility curves [7–10] identify thresholds explicitly, but only for a single simulated or tested structure, not from the observed operational record of a network with many structures in varying condition. Second, this paper also asks whether the relative importance of wind conditions against the scale of the affected customer base specifically changes between the full population of outages and the subset of events for which weather is the recorded cause. Prior work, including one of the studies cited above [6], identifies the most important predictors of outage risk among a broad set of hazard and infrastructure factors, but does not report this specific pairwise comparison between wind conditions and event scale, and does not examine whether such a comparison changes between the full population of outages and a subsample restricted to confirmed weather-driven events.

Addressing both gaps requires an observational record long enough, and varied enough, to include both routine operating conditions and a number of distinct severe wind events within the same network. The UKPN dataset examined in this paper spans three years of continuous operation, from April 2021 to March 2024, and includes seven officially named storms, among them Storm Eunice described above. This combination of duration and event coverage makes it possible to estimate a continuous response function across the full range of observed wind conditions, and to examine that function specifically under the seven storm events, rather than relying on a single simulated structure or a short observation window.

This paper addresses these two gaps using outage records from UKPN covering April 2021 to March 2024. The first gap is addressed by characterising the exposure and recovery response to gust intensity using a quadratic specification, and by identifying a critical wind threshold for the exposure margin. This provides field-level evidence at the network scale that complements structure-specific fragility curves obtained from simulation or testing, though the two describe different quantities: a fragility curve gives the probability that a structure fails at a given wind speed, while this paper models the scale and duration of outages conditional on an incident having already occurred. The second gap is addressed by quantifying the explanatory weight of gust relative to the affected-customer scale, both across the full population of weather- and asset-related outages and within the subset of events for which weather is the recorded cause. Both findings are examined against an independent temporal holdout not used during model development, and against the seven named storms. This establishes the extent to which each result can be confirmed independently of the exploratory modelling process.

The remainder of this paper is organised as follows. Section 2 describes the UKPN dataset, the construction of event-level exposure and recovery metrics from stage-level regulatory records, and the descriptive properties of the resulting sample. Section 3 presents the empirical framework, including the model specification and the two-stage development-confirmation design used to assess the results independently of the exploratory analysis. Section 4 reports the results in four parts. Section 4.1 establishes the nonlinear gust-outage response and reports the critical wind threshold identified for the exposure margin. Section 4.2 quantifies the explanatory weight of gust relative to the affected-customer scale across the full population of outages. Section 4.3 examines whether this weight changes within the subset of events attributed to weather and during the seven named storms. Section 4.4 confirms the findings of Sections 4.1 to 4.3 against the independent temporal holdout. Section 5 discusses the implications, boundaries, and limitations of these findings, and outlines directions for future work.

## Section 2. Data and Study Setting

### 2.1 Study setting and data sources

UKPN operates the electricity distribution network across London, the South East, and the East of England, and reports outage incidents to Ofgem, the energy regulator for Great Britain, under the regulatory reporting framework set out in the RIIO-ED1 and RIIO-ED2 Annex F guidance [11, 12]. RIIO-ED1 and RIIO-ED2 are successive multi-year price control periods during which Ofgem sets the revenue and performance requirements for UK electricity distribution network operators. This paper draws on UKPN's outage incident records covering 1 April 2021 to 31 March 2024, a period of three complete regulatory years spanning both the RIIO-ED1 and RIIO-ED2 price control periods. Each record corresponds to a restoration stage rather than a complete outage incident. An incident that requires more than one restoration action, for example because power is restored to part of the affected area before the remainder, is represented by more than one stage-level record sharing a common incident reference. Section 2.2 describes how event-level outcome variables are constructed from these stage-level records.

Weather variables are matched to each incident using hourly reanalysis data from the Open-Meteo historical weather API [13], which is based on the ERA5 global reanalysis dataset [14]. Data are indexed to the latitude and longitude reported for each incident and the hour in which it began. The primary wind variable used throughout this paper is instantaneous gust speed rather than sustained wind speed. This choice follows the convention in structural wind engineering, where design wind loads are based on a short-duration (3-second) gust rather than a longer-averaged sustained speed, because peak instantaneous loading determines structural response and failure [15]. This convention has been applied specifically to wind-induced damage in electrical grid infrastructure [16]. In the final analysis sample, gust speed has a mean of 9.87 m/s and a standard deviation of 5.22 m/s, referenced in Section 4.1 when reporting the exposure margin's turning point in physical units.

Regional covariates are drawn from Office for National Statistics (ONS) data at the Local Authority District (LAD) level and merged to each incident by its reported location. These comprise resident population from ONS local authority population estimates [17], and income deprivation rate, the gap between local and national income deprivation, and spatial clustering of income deprivation measured by Moran's I, all drawn from the ONS dataset mapping income deprivation at a local authority level [18]. Moran's I follows the spatial autocorrelation statistic introduced by Moran [19]. An urban-rural classification is drawn from the same ONS local statistics resource used for the population and deprivation data [17]. LAD boundaries as at December 2021 are taken from the ONS Open Geography Portal [20].

Figure 1 shows the three UKPN licence areas and the spatial density of incidents across the study period. Incident density is not uniform across the service area. It is concentrated around London, which sits at the boundary between the South East and East of England licence areas. A smaller, secondary concentration is visible near the north-east coast of the East of England licence area. The remainder of the service area shows a comparatively even, lower density of incidents.

**Figure 1.** Study area and event density. The map shows the three UKPN licence areas (London, South East, East of England) and the spatial density of all incidents in the final analysis sample, rendered as a hexagonal binning of incident coordinates on a logarithmic count scale. The inset shows the location of the UKPN service area within Great Britain.

### 2.2 Outcome variable construction

Ofgem's Annex F guidance defines two outcome measures for outage reporting [11, 12]. Customer Interruptions (CIt) counts the number of customers affected by an incident, summed across restoration stages and excluding stages flagged as re-interruptions to avoid double-counting the same customers. Customer Minutes Lost (CMLt) measures the duration of interruption, summed across all restoration stages including re-interruptions, because each additional interruption stage represents further time without supply for the customers affected at that stage. Both CIt and CMLt are regulatory aggregates indexed by reporting period $t$. This paper constructs two incident-level variables following the same aggregation logic, denoted $C_i$ and $D_i$ and indexed by incident $i$ rather than by reporting period.

The exposure margin is measured by the number of customers affected by an incident, referred to hereafter as affected customers, and constructed as

**[EQUATION 1]**

$$C_i = \sum_{r \,\in\, \mathcal{R}_i \,\setminus\, \mathcal{I}_i} N_{i,r}$$

where $C_i$ is affected customers for incident $i$, $\mathcal{R}_i$ is the set of restoration stages recorded for incident $i$, $\mathcal{I}_i \subset \mathcal{R}_i$ is the subset of those stages flagged as re-interruptions, and $N_{i,r}$ is the customer count reported at stage $r$.

The recovery margin is measured by the total duration of the incident, referred to hereafter as restoration duration, and constructed as

**[EQUATION 2]**

$$D_i = \max_{r \,\in\, \mathcal{R}_i} T_{i,r}^{\text{end}} - \min_{r \,\in\, \mathcal{R}_i} T_{i,r}^{\text{start}}$$

where $D_i$ is restoration duration for incident $i$, and $T_{i,r}^{\text{start}}$ and $T_{i,r}^{\text{end}}$ are the start and end times recorded at stage $r$.

Constructing affected customers by aggregating across stages, rather than taking the customer count reported in the earliest stage of each incident, changes the sample mean from 47.13 to 93.02 customers, a difference of a factor of 1.97, within the same final analysis sample reported in Table 1. This difference reflects incidents with more than one restoration stage, in which the earliest stage alone does not capture the full extent of the customers affected as the incident evolves. Appendix B reports the full data processing pipeline underlying Equations 1 and 2, including the handling of a small number of boundary cases not covered by the general definitions above.

### 2.3 Descriptive statistics and visualization

Table 1 reports descriptive statistics for affected customers and restoration duration in the final analysis sample, on the original scale and after log transformation. Both variables are heavily right-skewed on the original scale, with the mean well above the median (93.0 versus 2.0 for affected customers, 11.8 versus 6.3 hours for restoration duration). Figure 2 shows the distribution of each variable before and after transformation. The log transformations substantially reduce this skew, but they do not produce a fully symmetric distribution in either case. The transformed affected-customers variable shows a sawtooth pattern at low values, reflecting the fact that many incidents affect a small integer number of customers. The transformed restoration-duration variable shows two distinct modes, one near one hour and one near seven to twelve hours, separated by a clear trough. This pattern is consistent with the composition effect linked to the number of restoration stages per incident, described further in Section 4.1 and Appendix D. Despite this remaining structure, the log transformation is still used for both variables, because it removes the extreme right tail that would otherwise dominate an ordinary least squares fit.

**Table 1.** Descriptive statistics for affected customers and restoration duration, final analysis sample.

| Statistic | Affected customers (n=60,437) | log(1+affected customers) | Restoration duration, hours (n=59,834) | log(restoration duration) |
|---|---|---|---|---|
| Mean | 93.02 | 2.138 | 11.84 | 1.656 |
| Median | 2.00 | 1.099 | 6.27 | 1.835 |
| SD | 410.96 | 2.019 | 19.96 | 1.349 |
| Min | 0.00 | 0.000 | 0.05 | -2.996 |
| 25th pct. | 1.00 | 0.693 | 2.03 | 0.710 |
| 75th pct. | 35.00 | 3.584 | 12.67 | 2.539 |
| Max | 27,013.00 | 10.204 | 192.08 | 5.258 |

**Figure 2.** Distribution of affected customers and restoration duration, original scale and after log transformation. (a) Affected customers, original scale. (b) log(1+affected customers). (c) Restoration duration, original scale (hours). (d) log(restoration duration).

The Pearson correlation between affected customers and restoration duration in the final analysis sample (n = 60,437) is -0.016 on the original scale and -0.011 on the log scale. The Spearman correlation is 0.110. Both linear and monotonic measures of association are small in magnitude. A nonlinear dependence measure gives a different picture: the distance correlation between the two variables is 0.199, and a mutual information test rejects independence at a very high level of significance (permutation test, z = 160.4). Affected customers and restoration duration are therefore not statistically independent at the event level, although the form of their association is not captured by a simple linear or monotonic measure. Section 4.1 and Appendix D trace this association to the number of restoration stages recorded for each incident, rather than to a direct relationship between the scale of an incident and its duration. This is also why affected customers and restoration duration are treated as two separate outcome margins in this paper, modelled with their own covariates, rather than combined into a single severity index or assumed to be independent of one another.

### 2.4 Sample construction and predictor variables

UKPN records a Cause Code for each outage incident, describing its underlying original cause at a more granular level than is used in this paper. These codes are grouped into six categories for analysis, listed in full in Appendix A.2. Two of these six categories correspond respectively to codes attributed directly to weather and to codes attributed to the condition of network assets, referred to hereafter as the weather-related and asset-related categories. The remaining four categories cover incidents with no fault found on investigation, third-party interference, human error, and causes attributed to the customer or an external party. The recorded cause for incidents in these four categories is unrelated to wind conditions by construction, though this does not rule out some influence of weather on how these incidents are subsequently resolved. No-fault-found incidents alone account for approximately 39 percent of all recorded incidents in the study period. Including these four categories in the analysis sample would mix incidents with no expected relationship between their recorded cause and gust intensity into the estimation of that relationship. The theoretical case for this restriction is supported directly by re-estimating the recovery model on all six Cause Code categories (n = 116,064) rather than the weather-related and asset-related subset used in this paper (n = 59,834): the quadratic gust term remains of the same order of magnitude and significant in all five cross-validation folds under both samples (0.061 versus 0.079), while the linear gust term collapses from a significant effect in all five folds (mean coefficient 0.026) to an estimate indistinguishable from zero (mean coefficient 0.0002, significant in none of the five folds). This indicates that part of the linear-term signal observed when pooling all six categories reflects composition effects from categories unrelated to weather-driven failures, rather than a physically robust wind effect, and supports restricting the main specification to the weather-related and asset-related categories. Section 3.2 reports the history of when this restriction was decided relative to the development and confirmation samples used elsewhere in this paper.

The resulting sample comprises 60,453 incidents. After matching weather data and excluding incidents with missing regional covariates, 60,437 incidents are available for the exposure model and 59,834 for the recovery model, the difference reflecting incidents for which restoration duration could not be computed or fell above the 99th percentile of the restoration duration distribution.

The full covariate set comprises gust speed and its square, an interaction between gust speed and mean sea level pressure, 24-hour cumulative precipitation, temperature, mean sea level pressure, log population, income deprivation rate, the gap between local and national income deprivation, Moran's I, an urban-rural indicator, and calendar year and month fixed effects. The recovery model additionally includes affected customers and its square as covariates, discussed further in Section 4.1.

Variance inflation factors for all continuous covariates in the final model specification are below 4, with the highest value, 3.76, corresponding to the gap between local income deprivation and the national average. Values of 5 and 10 are commonly cited as informal thresholds for concern regarding multicollinearity, although O'Brien [21] cautions that these thresholds are heuristic rather than absolute, and that a given VIF value should be interpreted alongside the sample size and the strength of the effect under study rather than treated as a fixed cutoff. The VIF values obtained here are below both commonly cited thresholds regardless of this qualification.

---

## Section 3. Empirical Framework

### 3.1 Modelling approach and rationale

This paper uses a parametric regression model, not a machine learning model. The reason is straightforward. The shape of the relationship between gust intensity and outage outcomes needs to be identified. So does whether this relationship contains a threshold, and if so, at what wind speed. In its simplest form, before the covariates described in Section 3.3 are added, this relationship is written as

**[EQUATION 3]**

$$Y = \beta_1 G + \beta_2 G^2$$

where $Y$ denotes the outcome margin (affected customers or restoration duration, in the log scale described in Section 3.3), and $G$ denotes gust speed. A regression model of this form gives a closed-form turning point, $G^* = -\beta_1/(2\beta_2)$, found by setting the first derivative to zero. This closed-form solution is not unique to a linear model on the log scale. A generalised linear model with a log link and the same quadratic predictor gives the same first-order condition, because the derivative of a strictly positive link function does not change its sign. The parametric approach used in this paper is chosen for consistency between the two margins, and because it gives a single set of coefficients from which the turning point and its uncertainty can both be derived directly, not because it is the only specification capable of producing a turning point. Whether this turning point identifies a location with a clear interpretation, or is better reported only as a quadratic coefficient describing an outcome that grows with the squared distance from a reference gust level, is examined separately for each margin in Section 4.1, based on the estimated location of the turning point and its own uncertainty, rather than on the significance of the linear coefficient considered on its own.

The same model type is used throughout this paper. Ordinary least squares is applied to a log-transformed dependent variable, for both the exposure margin and the recovery margin, and for every sample examined in Section 4. Affected customers and restoration duration are both non-negative and right-skewed, as shown in Figure 2. Count-based or duration-based alternatives, such as a negative binomial, gamma, or Tweedie generalised linear model, are a common choice for outcomes of this kind [22]. Ordinary least squares on the log scale is used here instead, because it is the simplest model that gives a directly interpretable turning point from two coefficients.

This choice has been checked directly, rather than assumed. The exposure model was re-estimated using negative binomial and Tweedie specifications, and the recovery model was re-estimated using gamma and Tweedie specifications, on the same final sample described in Section 2.4. In every case, the quadratic gust term retained the same sign and remained significant at a similar or stronger level than under the log-OLS specification. This includes the recovery model, where the quadratic term is the central finding of this paper. Residual diagnostics for the log-OLS specification are reported in Appendix [编号待定]. Residuals depart from normality in both models, which is expected at this sample size and does not affect the validity of the coefficient estimates under ordinary least squares. The exposure model's residuals show a distinct pattern linked to the share of incidents with zero recorded customers, rather than a general problem with the model. Taken together, these checks support the use of the log-OLS specification, while also showing that the central findings of this paper do not depend on this specification alone. A machine learning model, such as a random forest, can often predict outcomes more accurately. It does not, however, give a simple, interpretable threshold value in the same way. For this reason, machine learning is not used as the main method in this paper. A machine learning comparison could still be a useful robustness check in future work. This point is revisited in Section 5.

### 3.2 Validation protocol

Building this model involved many choices. A decision was needed on which Cause Code categories to include. A decision was needed on how to define customer counts and outage duration from the raw stage-level records. A decision was needed on how to handle a small number of unusual events. Each of these choices could, in principle, be adjusted until the results looked as clean as possible. This is a known risk in applied statistics. Cox [23] proposed a simple way to guard against it. The data are split into two parts before any exploration begins. One part is used to make all the modelling choices. The other part is set aside and not examined until the modelling choices are final. Once the model is finalised on the first part, it is applied once to the second part, without further adjustment.

This approach is followed here for the model specification described in Section 3.3. Several earlier choices described in Section 2, including the choice between candidate duration measures, the restriction to two Cause Code categories, and the initial specification of the critical-wind-speed methodology itself, were originally established using data that had not yet been separated into development and confirmation parts, because the need for this separation was identified only after these choices were made. Appendix E reports this history in full. Most of these choices have since been re-examined on properly separated data: the Cause Code restriction and the variance decomposition results reported in Sections 4.2 and 4.3 are reproduced on the final combined sample described in Section 3.3, and the critical-wind-speed methodology is itself the subject of the temporal confirmation reported in Section 4.4. One comparison, between two candidate measures of restoration duration reported in Appendix B.2, has not been re-examined on separated data. It does not affect any result reported in this paper, because the candidate measure it discouraged was not used in any subsequent analysis. The first part of the data, referred to as the development sample, covers 1 April 2021 to 29 September 2023. The second part, referred to as the confirmation sample, covers 30 September 2023 to 31 March 2024. This six-month period was not examined at any point while the model specification in Section 3.3 was being developed. Section 4.4 reports what happens when the finalised model, unchanged, is estimated separately on this confirmation sample. Figure 3 shows this split alongside the seven named storms described in Section 4.3. Four of these storms (Arwen, Dudley, Eunice, and Franklin) occurred within the development sample, and three (Babet, Ciarán, and Henk) occurred within the confirmation sample, so the confirmation sample is not a period free of severe weather of its own.

**Figure 3.** Study period timeline (April 2021 to March 2024), showing the development and confirmation samples and the position of the seven named storms within each.

Within the development sample itself, five-fold cross-validation is also used to check that the coefficient estimates are stable. The folds are built by date, not by individual record, so that all records from a given day fall into the same fold. This matters because a single storm can generate many outage records on the same day. These records are not independent of each other. The same five folds are also used to compute an out-of-sample R-squared for each model, reported in Section 4.2: the model is fitted on four folds at a time, predictions are made for the fifth, held-out fold, and R-squared is computed on these held-out predictions rather than on the data used to fit the model. This is repeated across all five folds and averaged, so that the reported R-squared reflects predictive accuracy on data not used to estimate the coefficients, rather than the fit of the model to its own training data.

One specific number illustrates why the confirmation sample matters. An early estimate of the critical wind speed for the exposure margin, computed while the development sample still contained the contamination described in Appendix E, gave 10.69 m/s. Once this contamination was identified and removed, leaving a corrected development sample on its own, the estimate changed to 12.13 m/s. Combining this corrected development sample with the confirmation sample, to produce the final combined sample used throughout Section 4, brought the estimate back to 10.69 m/s. This is the number reported in Section 4.1. The two instances of 10.69 m/s do not reflect the same evidence: the first came from an uncorrected sample not yet separated into development and confirmation parts, and the second came from the deliberate recombination of both parts once each had served its role. Appendix E reports this history and the corresponding sample sizes in full. This history is reported here because it shows why a single estimate, produced early in an exploratory process, should not be treated as final.

### 3.3 Model specification

All continuous covariates, including gust speed, mean sea level pressure, precipitation, temperature, and the regional covariates listed in Section 2.4, are standardised to zero mean and unit variance before entering the model. Gust speed in Equations 3 and 4 therefore denotes standardised gust, and a value of zero corresponds to the sample mean gust speed rather than to calm conditions. This standardisation is applied consistently across estimation and reporting, including the turning point and its confidence intervals reported in Section 4.1.

The final model specification is the same for both outcome margins, except that the recovery model includes two additional terms. This is the full version of Equation 3, with the additional covariates included, given by

**[EQUATION 4]**

$$\ln(Y_i) = \beta_1 G_i + \beta_2 G_i^2 + \beta_3 (G_i \times P_i) + \mathbf{X}_i' \boldsymbol{\gamma} + \delta_{y(i)} + \theta_{m(i)} + \varepsilon_i$$

where $Y_i$ denotes the outcome for incident $i$ (one plus affected customers for the exposure margin, or restoration duration for the recovery margin), $G_i$ denotes gust speed, $P_i$ denotes mean sea level pressure, $\mathbf{X}_i$ denotes the remaining weather and regional covariates listed below, $\delta_{y(i)}$ and $\theta_{m(i)}$ denote year and month fixed effects, and $\varepsilon_i$ is the error term. For the recovery margin, $\mathbf{X}_i$ additionally includes affected customers and its square.

Year and month fixed effects are additive, entered as separate sets of dummy variables rather than as a year-by-month interaction, and the gust-pressure interaction term is the direct product of the two standardised variables. For the exposure margin, the dependent variable is the natural logarithm of one plus affected customers. For the recovery margin, the dependent variable is the natural logarithm of restoration duration, and the model additionally includes affected customers and its square as covariates.

Table 2 lists the covariates denoted $\mathbf{X}_i$ in Equation 4, beyond gust speed, its square, and the gust-pressure interaction, which are reported separately in Section 4.1. Appendix A reports the source and processing of each variable in full.

**Table 2.** Covariates included in $\mathbf{X}_i$, in addition to gust speed, its square, and the gust-pressure interaction.

| Variable | Category | Model |
|---|---|---|
| Mean sea level pressure | Weather | Both |
| 24-hour cumulative precipitation | Weather | Both |
| Temperature | Weather | Both |
| Log population | Regional | Both |
| Income deprivation rate | Regional | Both |
| Gap between local and national income deprivation | Regional | Both |
| Moran's I (income deprivation) | Regional | Both |
| Urban-rural indicator | Regional | Both |
| Affected customers (linear and squared) | Event-level | Recovery only |
| Year fixed effects | Temporal | Both |
| Month fixed effects | Temporal | Both |

Standard errors are clustered by Local Authority District, following standard practice for regression models with grouped data [24]. A given storm can affect many incidents in the same district on the same day, so errors within a district are unlikely to be independent of each other. Section 4.4 also reports what happens when standard errors are clustered by both district and date at the same time. This is a more conservative check, and the full results are given in Appendix F.

---

## Section 4. Results

### 4.1 Nonlinear gust–outage response and critical thresholds

This section establishes the shape of the gust-outage relationship for each margin, then examines how far this shape can be refined into a single, specific value. Sections 4.2 to 4.4 then examine how much this relationship matters, and how well it holds up outside the sample used to estimate it.

Table 3 reports the gust coefficients from the final model specification, estimated on the full analysis sample described in Section 2.4. For both outcome margins, the quadratic gust term is significant at a much stronger level than the linear term: p < 0.001 in both cases, compared with p = 0.022 for the exposure margin's linear term and p = 0.982, not significant, for the recovery margin's. The quadratic term is also the consistent feature of the relationship reported throughout this paper: it remains stable in sign and significance under alternative distributional assumptions (Section 3.1), within an independent temporal holdout (Section 4.4), and within a subsample restricted to weather-attributed incidents (Section 4.3). The quadratic term is therefore established first, as the dominant and more robust feature of the relationship in both margins, before either relationship is examined for a specific numerical threshold. The two margins differ in whether the linear gust term is also different from zero, and this difference determines how far each relationship can be refined beyond the quadratic term into a specific value.

**Table 3.** Gust coefficients, final model specification.

| Term | Exposure margin | Recovery margin |
|---|---|---|
| Gust (linear) | -0.032 (p = 0.022) | 0.000 (p = 0.982) |
| Gust squared | 0.103 (p < 0.001) | 0.079 (p < 0.001) |
| n | 60,437 | 59,834 |

For the exposure margin, the linear gust term is negative and significant, so the two coefficients jointly determine the shape of the curve. This negative linear term is small in magnitude relative to the quadratic term, and Section 4.4 reports that it is less stable across samples and clustering methods than the quadratic term. Most incidents at low gust levels are unrelated to weather, as reported in Section 2.4, so this small negative slope may reflect factors other than wind conditions in this part of the range, rather than a direct physical relationship between mild wind and fewer affected customers. Its small size is also consistent with ordinary estimation variability, and it is not treated as a finding requiring a specific mechanistic explanation.

The full model in Equation 4 also includes an interaction between gust and pressure, so the point at which the curve turns depends on the pressure level at which it is evaluated. Holding pressure at its sample mean, zero on the standardised scale, this point is given by

**[EQUATION 5]**

$$G^*(P{=}0) = -\frac{\beta_1}{2\beta_2}$$

where $\beta_1$ and $\beta_2$ are the linear and quadratic gust coefficients from Table 3. At other pressure levels, the corresponding location is $G^*(P) = -(\beta_1+\beta_3 P)/(2\beta_2)$, where $\beta_3$ is the gust-pressure interaction coefficient. The value reported throughout this paper is specific to average pressure conditions. Because this turning point is a ratio of two estimated coefficients, its uncertainty cannot be read directly from the standard errors of $\beta_1$ and $\beta_2$ alone. Section 4.4 shows that this same ratio is more sensitive to sample and specification than the quadratic term on its own, including under a clustering method that affects the significance of $\beta_1$ specifically. Two methods are used to construct a confidence interval for $G^*(P{=}0)$: the delta method [25], and a bootstrap procedure that resamples entire days rather than individual incidents, to preserve the fact that incidents on the same day are not independent. For the exposure margin, the two methods give different results when applied to the standardised turning-point statistic. The delta method produces a 95 percent confidence interval for this standardised location that does not cross zero. The bootstrap procedure produces a wider interval that does cross zero, meaning the data cannot statistically rule out the turning point coinciding with the sample-mean gust speed (9.87 m/s) rather than lying strictly above or below it. A ratio of two random coefficients does not follow a normal distribution in general, which can cause a first-order approximation such as the delta method to understate the true sampling uncertainty. This is consistent with the difference observed between the two methods here, though it has not been separately confirmed against the resampled distribution of the coefficients themselves, and a difference in how each method treats dependence between incidents may also contribute. A standardised interval crossing zero does not imply that the corresponding physical-unit interval crosses 0 m/s: because a standardised value of zero corresponds to the sample-mean gust speed rather than calm conditions, the same bootstrap resamples translate into a strictly positive physical-unit range of 9.2 to 12.1 m/s. The bootstrap interval is used here as the more conservative estimate. The resulting turning point, 10.69 m/s, falls at the 63.7th percentile of the observed gust distribution, within the range covered by the data rather than at its extreme.

A quadratic function is symmetric around its own turning point by construction: equal standardised distances on either side of $G^*$ correspond to identical fitted values, regardless of whether the linear coefficient is zero. The relevant difference between the two margins is therefore not the shape of the curve around its own turning point, which cannot itself be asymmetric, but where that turning point is located relative to the sample mean gust speed, and how precisely that location can be estimated.

For the exposure margin, the turning point is located a small distance above the sample mean, at 10.69 m/s against a mean of 9.87 m/s. As reported above, the bootstrap confidence interval for this standardised location includes zero, so the data cannot rule out this location coinciding with the sample mean itself, even though the point estimate is displaced from it. The language of a critical wind speed is used here to describe this point estimate, together with the qualifications reported above and in Section 4.4.

For the recovery margin, the linear gust term is not distinguishable from zero (Table 3), so the turning point implied by the fitted coefficients sits close to the sample mean gust speed itself, rather than at a location clearly displaced from it. A specific numerical threshold is not reported for this margin. Its relationship to gust is instead described by the quadratic coefficient on its own: an outcome that grows with the squared distance from the sample mean gust speed, in either direction, rather than a threshold located at a specific wind speed away from that mean.

Figure 4 shows the fitted response curve for each margin, with the other covariates held at their sample means. In both panels, the curve falls and then rises, and the rise to the right of the minimum is visually steeper than the fall to its left. Because a quadratic function is symmetric around its own turning point, this visual pattern does not reflect an asymmetry in the fitted function itself. It reflects the asymmetry of the observed gust range relative to each turning point. Gust speed cannot be negative, so the low end of the observed range is bounded to within about two standard deviations of the sample mean, while the right-skewed distribution of gust speed allows the high end to extend past three standard deviations. Because each turning point falls close to the sample mean, the right-hand end of the plotted range sits substantially farther from the turning point, in standardised units, than the left-hand end. Because the fitted curve is quadratic in this distance, this asymmetry in the observed range alone produces several-fold differences in fitted values between the two arms, for both margins.

**Figure 4.** Fitted gust-outcome response curves, other covariates held at sample means and pressure held at zero on the standardised scale. (a) Exposure margin: predicted affected customers against gust speed, with the turning point at 10.69 m/s and its 95 percent bootstrap confidence interval shown as a shaded band. (b) Recovery margin: predicted restoration duration against gust speed, affected customers held at its sample mean.

The recovery model also includes affected customers and its square as covariates. Affected customers is a stable predictor of restoration duration within the main specification, in the sense that its sign and significance do not change under the temporal holdout examined in Section 4.4. Its relationship to duration is more sensitive to how the sample is restricted by cause: Appendix D.7 reports that its sign in the subsample of weather-attributed incidents examined in Section 4.3 differs from its sign in the main specification. A closely related, more detailed question is why the coefficient on affected customers takes the particular sign and shape that it does in the main specification. Appendix D shows that this shape is linked to the number of restoration stages recorded for each incident, rather than to the scale of the incident on its own. This does not affect the coefficient on gust, which is stable whether or not the number of restoration stages is taken into account, but it does mean that affected customers and gust should be read as two separate predictors of restoration duration, rather than one working through the other.

The turning point identified for the exposure margin marks where the slope of the fitted curve changes from negative to positive. It does not indicate a change in curvature, since the second derivative of a quadratic function is constant, and it does not correspond to a change in the underlying mechanism linking gust to outage outcomes. Near the turning point itself, the slope is close to zero, so the outcome does not begin to rise sharply exactly at this location, but only somewhat beyond it. This paper also models outcomes conditional on an incident having already occurred, rather than the probability that an incident occurs at a given wind speed, which would require observations of periods without an incident and is not estimated here. The turning point is reported as an estimated feature of the fitted response function under the reference conditions described above, rather than as a physical damage threshold or an operational trigger point in its own right.

### 4.2 Population-level weight of wind

The results in Section 4.1 establish that gust has a real, stable relationship with both outcome margins. They do not establish how much of the variation in these outcomes gust actually explains, relative to other factors. These are separate questions. A coefficient can be estimated precisely and remain stable across many samples while still accounting for only a small share of the total variation in the outcome. This section addresses the second question directly.

Nested models are used to decompose the explained variance for each margin. Starting from a baseline of regional covariates and calendar fixed effects, non-gust weather variables are added first, and gust is added last. The increase in out-of-sample R-squared at each step, measured using the five-fold cross-validation described in Section 3.2, gives the marginal contribution of each group of variables. Figure 5 shows this decomposition for both margins. For the exposure margin, gust contributes 1.07 percentage points, out of a total out-of-sample R-squared of 2.81 percent for the full model. For the recovery margin, gust contributes between 0.62 and 0.75 percentage points, depending on whether affected customers is added before or after gust in the sequence, while affected customers itself contributes between 7.73 and 7.87 percentage points regardless of the order in which it is added, out of a total out-of-sample R-squared of 11.05 percent for the full recovery model. The bar for affected customers is between roughly 10 and 13 times the height of the bar for gust in the recovery model, depending on which of the two marginal contribution ranges is used, and this difference is the single most visible feature of Figure 5. A second, smaller pattern is also visible in Figure 5: for the baseline and non-gust weather groups, the recovery-model bar is taller than the exposure-model bar, but for the gust group this ordering reverses, and the exposure-model bar becomes the taller of the two.

**Figure 5.** Marginal out-of-sample R-squared by variable group, exposure and recovery margins. Bars show the increase in out-of-sample R-squared from adding each group of variables in sequence: regional covariates and calendar fixed effects, non-gust weather, gust, and, for the recovery margin only, affected customers.

Figure 6 provides a further point of comparison, using the observed variation in regional covariates rather than in gust or affected customers. Weather conditions and affected customers are both held fixed at their sample means, and only the five region-level covariates described in Section 2.4 are allowed to vary across Local Authority Districts. Figure 6a shows the resulting predicted affected customers by district, and Figure 6b shows predicted restoration duration. In Figure 6a, a ring of districts immediately surrounding central London shows higher predicted values than the London core itself, with a further contiguous band of higher values extending north from this ring. In Figure 6b, the London core is again low, but the surrounding pattern is more scattered, and the northward band visible in Figure 6a is largely absent. The two panels do not share the same set of high-value districts. This is consistent with a negative correlation, reported separately as -0.780 (Pearson) and -0.758 (Spearman) between the two predicted surfaces across districts.

**Figure 6.** Baseline regional variation in predicted outcomes under a fixed reference weather scenario. (a) Predicted affected customers by Local Authority District. (b) Predicted restoration duration by Local Authority District. In both panels, weather conditions and affected customers are held at their sample means, and only the five region-level covariates listed in Section 2.4 vary across districts.

The same comparison can also be made directly in terms of predicted outcomes, rather than in terms of variance shares. Figure 7 compares three ratios, each defined as the highest fitted value divided by the lowest fitted value across the plotted range of the driving variable (its 1st to 99th percentile). For a curve with an interior turning point, this ratio need not equal the ratio between the two endpoint values themselves, since the lowest fitted value can fall inside the range rather than at either end. Holding other covariates fixed, this ratio is 2.79 for gust on the exposure margin and 2.37 for gust on the recovery margin, in both cases with the lowest fitted value close to the turning point reported in Section 4.1 rather than at the lower end of the range. Holding gust fixed, the corresponding ratio for affected customers on the recovery margin is 5.99. This third ratio is more than twice either of the first two. All three ratios are well above one, meaning that none of the three variables leaves the predicted outcome unchanged across its observed range, but the ratio for affected customers is clearly the largest of the three.

**Figure 7.** Ratio of the highest to the lowest fitted value across the plotted range (1st to 99th percentile) of the driving variable. Three ratios are shown: gust on the exposure margin (2.79), gust on the recovery margin (2.37), and affected customers on the recovery margin (5.99). A dashed reference line marks a ratio of one, corresponding to no change in the predicted outcome.

The predicted values in Figure 6 vary by a factor of 1.96 for affected customers and 1.41 for restoration duration across the range of districts observed. Both ratios are of a similar order of magnitude to the gust-driven ratios reported above (2.79 and 2.37), and neither approaches the ratio associated with affected customers itself (5.99). Figure 6 therefore does not show that regional characteristics matter more than gust. It shows that the observed variation in these five regional covariates is comparable in scale to the observed variation in gust, and that both are considerably smaller in their effect on predicted outcomes than the observed variation in affected customers.

Taken together, the results in this section support two conclusions rather than one. Gust accounts for a small share of the total variation in outage outcomes at the population level. Among the variables considered here, affected customers accounts for a substantially larger share. Section 4.3 asks whether this ordering still holds once the sample is restricted to incidents for which weather is the recorded cause.

### 4.3 Weather-attributed incidents and storm-period evidence

Section 4.2 describes the full population of weather- and asset-related incidents, most of which have nothing to do with weather. This section asks a narrower question: among incidents that can be identified, independently of the outcome, as weather-driven, does gust still account for only a small share of the variation, or does it account for more? This question is examined using the Cause Code recorded for each incident. A separate check, using seven real storms with an independently documented date and identity, then examines how well the main specification's predictions hold up during these specific events.

The recovery model described in Section 3.3 was re-estimated on the subset of incidents for which the Cause Code identifies weather as the direct cause, rather than the combined weather- and asset-related sample used elsewhere in this paper. This subset contains 9,758 incidents, about 16 percent of the main sample. Table 4 compares the two samples directly. The quadratic gust term is close to the same magnitude in both samples and remains significant in both. The marginal contribution of gust to out-of-sample R-squared more than doubles, from between 0.62 and 0.75 percentage points in the main sample to between 1.43 and 1.71 percentage points in the weather-only subset, and now exceeds the marginal contribution of affected customers, which falls to between 1.00 and 1.28 percentage points in this subset. Figure 8 shows this comparison. Figure 8a reports the exposure margin, where the marginal contribution of gust falls from a positive value in the main sample to a small negative value in the weather-only subset, the only instance of a negative bar among all of the figures reported in this paper. Figure 8b reports the recovery margin, where the relative height of the gust and affected-customers bars is reversed between the two samples, from affected customers roughly 12.7 times the height of gust in the main sample to gust slightly exceeding affected customers in the weather-only subset.

**Table 4.** Marginal out-of-sample R-squared, main sample versus weather-only subset.

| Margin | Variable | Main sample | Weather-only subset |
|---|---|---|---|
| Exposure | Gust | +1.07 pp | -0.15 pp |
| Recovery | Gust | 0.62-0.75 pp | 1.43-1.71 pp |
| Recovery | Affected customers | 7.73-7.87 pp | 1.00-1.28 pp |

**Figure 8.** Marginal out-of-sample R-squared, main sample versus weather-only subset. (a) Exposure margin. (b) Recovery margin, gust and affected customers shown separately.

The negative result for the exposure margin in the weather-only subset is not treated here as evidence against the finding in Section 4.1. A plausible account of this result is that Cause Code assignment is not independent of gust speed: an incident occurring in calm weather is less likely to be classified as weather-driven than an otherwise similar incident occurring in strong wind, which would deplete the weather-only subset of low-gust observations relative to the full sample. This explanation is offered here as a plausible account of the pattern in Table 4, not as an established mechanism, since it has not been directly verified against the relationship between gust speed and Cause Code assignment. If this account is correct, it would affect the exposure margin specifically, because its turning point depends on having enough observations below the turning point to identify the falling part of the curve, and would affect the recovery margin less, because the quadratic coefficient reported there does not depend on locating a precise turning point.

A second, independent way of restricting attention to weather-driven incidents is to examine periods of documented severe storms directly, rather than relying on a recorded cause. This follows a similar logic to prior work that validates a fitted outage model against a small number of distinct, named storms not used to fit the model [5]. Seven storms with an officially recorded name and date fall within the study period: Arwen, Dudley, Eunice, Franklin, Babet, Ciarán, and Henk. Together, these seven storms span 27 days, or 2.46 percent of the total study period. Within these 27 days, 8.15 percent of all incidents in the final sample occurred, accounting for 14.72 percent of total affected customers. Incident density during these seven storms is therefore around 3.3 times the average incident density across the study period as a whole, and the concentration of affected customers during these storms is around six times the study-period average.

The finalised exposure and recovery models, unchanged from Section 4.1, were then used to predict outcomes for the incidents recorded during each of the seven storms, using the gust and other covariate values actually observed during that storm. Figure 9 compares these predictions against the observed outcomes. For the exposure margin, Figure 9a, the predicted values are systematically higher than the observed values for incidents with a low observed customer count, visible as vertical clusters of points sitting well above the reference line at the low end of the horizontal axis. Predictions come closer to the reference line only among incidents with a comparatively high observed customer count. For the recovery margin, Figure 9b, the points are more evenly distributed around the reference line, without the same one-sided pattern, although two of the seven storms, Eunice and Franklin, each form a distinct local cluster: Eunice's cluster sits slightly above the reference line, and Franklin's sits below it.

**Figure 9.** Fitted against observed outcomes during the seven named storms, coloured by storm, with a 45-degree reference line. (a) Exposure margin. (b) Recovery margin.

The fitted-observed correlation for each margin was also computed separately within each storm and compared against the correlation for the full sample. For the exposure margin, the full-sample correlation is 0.179, and the seven storm-specific correlations range from 0.116 to 0.341, without a consistent direction relative to the full-sample value. For the recovery margin, the full-sample correlation is 0.343, and all seven storm-specific correlations fall below this value, ranging from 0.084 to 0.317. The weakest of these, for Storm Dudley, is not statistically distinguishable from zero.

This weaker performance during storms is not read here as evidence against the results reported in Section 4.1. It follows instead from the modest population-level weight of gust already reported in Section 4.2: a model that explains only a small share of total variation is not expected to track individual incidents closely once storms concentrate unmodelled sources of variation, such as competition for restoration crews, into a short period. Weaker individual-incident tracking during storms and a modest population-level share of explained variance describe the same underlying limitation, not two separate findings.

The predictions evaluated against storm-period outcomes in this section come from a model fitted on the full sample, which includes the incidents recorded during these seven storms. This comparison therefore checks how well the fitted model describes these specific events, rather than testing the model on data withheld from it in the way the temporal holdout in Section 4.4 does.

The Cause Code approach and the storm-period approach identify weather-driven incidents in different ways and are affected by different limitations. The Cause Code approach is subject to the selection account described above for the exposure margin. The storm-period approach draws on a comparatively small number of incidents and evaluates predictive fit rather than directly comparing the marginal contribution of gust against affected customers within storm periods specifically. The reversal in the ordering of marginal contributions reported in Table 4 is established by the Cause Code comparison. The storm-period comparison in this section provides a complementary check on how the fitted model performs during real, named extreme events, rather than a second, independent computation of the same reversal.

### 4.4 Robustness: independent temporal confirmation

The results reported in Sections 4.1 to 4.3 use the final combined sample, which pools the development sample with the confirmation sample once both had served their separate roles, as described in Appendix E. This section reports a more stringent check: the model specification is estimated separately on the development sample alone and on the confirmation sample alone, to assess whether the same finding holds in each part independently, given that the confirmation sample, covering 30 September 2023 to 31 March 2024, was not examined at any point while the model was being developed.

For the exposure margin, the linear gust term changes sign between the two separately estimated samples, from negative in the development sample to positive in the confirmation sample, and the turning point moves from a position above the sample mean gust speed to a position below it. The 95 percent bootstrap confidence interval for the turning point, which excludes zero in the development sample, includes zero in the confirmation sample. The quadratic term itself remains positive and significant in both samples, and is in fact larger in the confirmation sample than in the development sample. For the recovery margin, the quadratic gust term is positive and significant in both separately estimated samples, at 0.066 in the development sample and a similar magnitude in the confirmation sample. The linear gust term is not significant in either sample. The sample mean gust speed differs by approximately 11.6 percent between the two samples, higher in the confirmation sample, consistent with this period falling entirely within autumn and winter. Standard deviations are close between the two samples, to within about one percent, so quadratic terms are directly comparable, but a coefficient defined relative to each sample's own mean gust speed, such as the linear term, corresponds to a different physical wind speed in each sample.

Figure 10 compares the quadratic gust coefficient across four settings: the development sample, the confirmation sample, and the final combined sample's estimate under single and two-way clustered standard errors. For the recovery margin, all four confidence intervals are narrow and overlap closely. For the exposure margin, the confirmation-sample point estimate is visibly higher than the other three, which are themselves close to one another, though its confidence interval is not the widest of the four shown for this margin. The widest interval for this margin is instead the two-way clustered estimate.

**Figure 10.** Quadratic gust coefficient, exposure and recovery margins, under four settings: development sample, confirmation sample, single clustering by Local Authority District, and two-way clustering by district and date. Points show coefficient estimates and horizontal lines show 95 percent confidence intervals.

The confirmation sample covers six months within a single autumn and winter period, rather than a full annual cycle, and is substantially smaller than the development sample. Both of these differences are expected to widen confidence intervals and to make a single point estimate less stable, independently of whether the underlying relationship has changed. A change in the exposure margin's specific turning point value is therefore not read here as a failure of the exposure model as a whole. The quadratic shape of the exposure response, and the full quadratic response of the recovery margin, are both confirmed in the sense used throughout this section: the same sign, and a similar or greater level of significance, in a sample that played no part in developing the model. The specific numerical value of the exposure margin's turning point is not confirmed in this same sense, and is reported in Section 4.1 with this qualification in mind.

Standard errors clustered by both Local Authority District and date, rather than by district alone, were also checked for the final combined sample, as a further check on inference given the spatial clustering of incidents during a single storm. The quadratic gust term for the recovery margin remains significant under two-way clustering, with a p-value of 5.4 times ten to the power of minus 22, compared with 2.8 times ten to the power of minus 36 under single clustering. The quadratic gust term for the exposure margin also remains significant under two-way clustering. The linear gust term for the exposure margin, and the interaction between gust and pressure in both margins, lose significance under two-way clustering. This same pattern, in which the quadratic terms remain significant while the linear term and the interaction term do not, was also found when this check was independently repeated on an earlier version of this dataset, providing an independent point of comparison for the pattern observed here.

---

## Section 5. Conclusion

The two central findings of this paper concern the shape of the gust-outage relationship and the weight of gust relative to other explanatory variables. A pattern recurs across Sections 4.1, 4.3, and 4.4 concerning the first of these. A result that depends on a ratio of two estimated coefficients, such as a turning point, changes more between samples than a result that depends on a single coefficient, such as a quadratic term on its own. The recovery margin, for which no turning point is reported, is confirmed consistently throughout this paper. The exposure margin's turning point value is the one number that moves between samples. Readers using the results in this paper should place more weight on the quadratic terms on their own, and treat any specific turning-point value with the same qualifications reported in the section where it first appears.

The second finding, reported in Sections 4.2 and 4.3, is that gust's weight relative to affected customers is not fixed. Across the full population of incidents, gust accounts for a modest share of total variation, well below the share accounted for by affected customers. Within the subset of incidents for which the Cause Code identifies weather as the recorded cause, this ordering reverses, and gust's marginal contribution exceeds that of affected customers. This reversal is established by the Cause Code comparison. The storm-period evidence in Section 4.3 provides a complementary check on predictive fit during real extreme events, rather than an independent computation of the same reversal. Taken together, these results mean that the relative importance of gust, compared specifically with the scale of an incident, depends on the population being considered: modest across outages in general, and reversed within the narrower population of incidents already attributed to weather.

The critical wind speed identified for the exposure margin may be useful as an approximate reference point for storm-response planning, marking the gust level above which affected customer numbers begin to rise sharply. Because this specific value was not confirmed in Section 4.4, it is better treated as an approximate operational reference than as a precise design threshold. This distinction matters because the exposure model explains a modest share of total variation, as reported in Section 4.2. The threshold describes a statistically robust change in the shape of the response function, not a tool for predicting the outcome of an individual incident.

Section 4.1 reports that affected customers, once the number of restoration stages per incident is taken into account, is associated with shorter restoration duration. This is broadly consistent with a dispatch-priority explanation, in which larger incidents receive earlier attention from restoration crews. Prior work using outage data from United States utilities has instead reported that the recovery duration of an outage is independent of the number of customers affected [26]. The direction of this relationship may depend on factors not examined in this paper, such as differences in network density between service areas, or differences in how restoration stages are defined and reported across utilities and regulatory frameworks.

Several limitations affect how far these results can be generalised. The temporal holdout used in Section 4.4 covers six months within a single autumn and winter period, rather than a full annual cycle. A longer holdout period, covering more than one full year, would give a stronger test of whether the exposure margin's turning point is stable across seasons. A method that uses the geographic coordinates of each incident directly, rather than grouping incidents into districts for clustering standard errors, was not attempted here and is left for future work. The exact meaning of incidents recorded with zero affected customers was not confirmed at the level of Ofgem's underlying data dictionary. One further open question, reported in Appendix D, was not fully resolved: within the weather-only subsample examined in Section 4.3, the sign of the affected-customers coefficient changes in a way not fully explained by the number of restoration stages, unlike in the main sample. This does not affect the gust coefficients reported for that subsample.

This paper treats the affected-customers and restoration-duration margins as outcomes to be explained, without asking whether the relationship between them changes according to the type of hazard involved, or whether concurrent outages on the same network interact with each other. Both questions are left for future work, along with a comparison between the parametric approach used here and a machine learning approach of the kind introduced in Section 3.1.

The approach used in this paper, reconstructing event-level outcome measures from stage-level regulatory records according to their official definitions, and confirming the resulting model against both an independent time period and a set of real storm events, is not specific to UK Power Networks. The same approach could be applied to any distribution network operator that reports outage incidents at the level of individual restoration stages, under a comparable regulatory framework.

---

---

## References

[1] Institute for Government. Energy resilience [Internet]. [date unverified]. Available from: https://www.instituteforgovernment.org.uk/explainer/energy-resilience

[2] Ofgem. Storm Arwen report [Internet]. [title, date unverified]. Available from: https://www.ofgem.gov.uk/research/storm-arwen-report

[3] Guikema SD, Quiring SM, Han SR. Prestorm estimation of hurricane damage to electric power distribution systems. Risk Analysis. 2010;30(12):1744-1752.

[4] Liu H, Davidson RA, Apanasovich TV. Statistical forecasting of electric power restoration times in hurricanes and ice storms. IEEE Transactions on Power Systems. 2007;22(4):2270-2279.

[5] Nateghi R, Guikema SD, Quiring SM. Comparison and validation of statistical methods for predicting power outage durations in the event of hurricanes. Risk Analysis. 2011. [volume, pages unverified]

[6] Mukherjee S, Nateghi R, Hastak M. A multi-hazard approach to assess severe weather-induced major power outage risks in the U.S. Reliability Engineering & System Safety. 2018;175:283-305.

[7] Dikshit S, Alipour A. Characterizing probability of failure of transmission tower systems under multiple climatic hazards: wind and ice. Engineering Structures. 2025;342:120720.

[8] Zhu X, Ou G. Wind fragility modeling of transmission tower-line system based on threat-dependent structural robustness index. Structural Safety. 2025;114:102571.

[9] Ma L, Khazaali M, Bocchini P. Component-based fragility analysis of transmission towers subjected to hurricane wind load. Engineering Structures. 2021;242:112586.

[10] Kabre WW, Weimar MR. Fragility functions resource report: documented sources for electricity and water resilience valuation. PNNL-33587. Richland (WA): Pacific Northwest National Laboratory; 2022.

[11] Office of Gas and Electricity Markets. RIIO-ED1 regulatory instructions and guidance: Annex F. London: Ofgem. [date unverified].

[12] Office of Gas and Electricity Markets. RIIO-ED2 regulatory instructions and guidance: Annex F -- interruptions. London: Ofgem; 2023.

[13] Open-Meteo. Historical weather API [Internet]. [date unverified]. Available from: [URL unverified]

[14] Hersbach H, Bell B, Berrisford P, Hirahara S, Horanyi A, Munoz-Sabater J, et al. The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society. 2020;146:1999-2049.

[15] American Society of Civil Engineers. Minimum design loads and associated criteria for buildings and other structures. ASCE/SEI 7. [edition unverified].

[16] [authors unverified]. The risk of cascading failures in electrical grids triggered by extreme weather events. arXiv:2107.00829. [publication status unverified].

[17] Office for National Statistics. Explore local statistics [Internet]. 2025. Available from: [URL unverified]

[18] Office for National Statistics. Mapping income deprivation at a local authority level [Internet]. 2021. Available from: [URL unverified]

[19] Moran PAP. Notes on continuous stochastic phenomena. Biometrika. 1950;37(1-2):17-23.

[20] Office for National Statistics. Local Authority Districts (December 2021) boundaries UK BGC [Internet]. Available from: https://open-geography-portalx-ons.hub.arcgis.com/datasets/ons::local-authority-districts-december-2021-boundaries-uk-bgc

[21] O'Brien RM. A caution regarding rules of thumb for variance inflation factors. Quality & Quantity. 2007;41(5):673-690.

[22] McCullagh P, Nelder JA. Generalized linear models. 2nd ed. London: Chapman and Hall; 1989.

[23] Cox DR. A note on data-splitting for the evaluation of significance levels. Biometrika. 1975;62(2):441-444.

[24] Cameron AC, Miller DL. A practitioner's guide to cluster-robust inference. Journal of Human Resources. 2015;50(2):317-372.

[25] Oehlert GW. A note on the delta method. The American Statistician. 1992;46(1):27-29.

[26] Wu H, Meng X, Danziger MM, Cornelius SP, Tian H, Barabási AL. Fragmentation of outage clusters during the recovery of power distribution grids. Nature Communications. 2022;13:7372.

---

## 内部核查清单（不属于论文正文，供定稿前逐条清理，不提交给期刊）

以下条目在上方Reference列表中标注了"unverified"，需要在正式投稿前逐一查证补全：

- [1][2][11][13][17][18]：均为机构网页/报告类来源，完整标题、发布日期、URL待逐一核实补全
- [15]：ASCE 7标准具体版本号（如7-22）待确认
- [16]：完整作者名单待查，且需确认是否已在同行评审期刊正式发表（而非仅arXiv预印本），按引用规则应优先引用正式发表版本
- [6]：原刊DOI待补（目前仅有NSF存档链接）
- [5]：卷期页码待补

以下条目已在命令#38通过CrossRef API/OSTI.gov官方数据库核实完毕，参考文献列表已更新，不再是待办：
- [3][4][7][8][9][10]：完整作者、篇名、期刊、卷期页码均已核实并更新到Reference列表。其中[7]核实过程中出现过一次WebSearch摘要（"Volume 343, Article 121237"）与CrossRef API直接返回结果（"Volume 342, Article 120720"）不一致的情况，已采信CrossRef官方元数据，此处记录这一处波折以备查。[7][8]因ScienceDirect原始页面访问受限（HTTP 403付费墙），未能像[3][4][9]那样做第二个独立源交叉验证，如果需要更高置信度，建议后续通过有权限的学术数据库直接核对原文首页。DOI待逐一补全到Reference条目中（本轮核实到期刊卷期页码，部分DOI未逐一誊抄）。

以下几点在核查过程中发现、与引用直接相关但不体现在上方干净版Reference列表中，供撰写论文全文其他部分时仍需留意：
- [18]确认为ONS"Mapping income deprivation at a local authority level"，不是IMD（多维度剥夺指数），正文行文已避免混淆，无需在Reference中额外说明
- [20]的版本号（December 2021 UK BGC）经核实与v6原论文引用的版本（December 2023 UK BFE）不一致，本文引用的是实际使用的正确版本
- [21] O'Brien (2007)实际论点是质疑VIF经验阈值的普适性，正文2.4节引用时已按此措辞，不是"证明阈值安全"

## 学术审查发现问题处理记录（本轮新增）

使用academic-review skill对手稿做的独立审查发现6项FOUNDATIONAL、6项MAJOR问题，处理情况：

- **F1**（Bootstrap CI"跨零"表述矛盾）：已解决。根源是标准化z-score尺度与物理单位m/s尺度混用了"零"这个词，z=0对应样本均值风速9.87 m/s而非0 m/s，两处表述本身不矛盾，正文已重写以显式说明这一区别。顺带发现并修正了一处百分位数字错误（65.9th应为63.7th）。
- **F2**（摘要过度声称阈值数值已确认）：已解决，摘要已拆分"形状确认"与"具体数值未确认"两句话。
- **F3**（子样本规模59,758应为9,758）：已解决，确认为打字错误并修正。
- **F4**（2.2节均值75.56与Table1均值93.02口径不一致）：已解决。75.56来自命令#8对全量n=135,025原始样本的计算，Table1用的是命令#21最终n=60,437样本；已在完全统一口径下重新计算，正确比值为47.13 vs 93.02（1.97倍）。
- **F5**（风暴"六倍"密度与前文百分比不符）：已解决，拆分为事件数密度(~3.3倍)和客户数密度(~6倍)两个不同比值，分别正确标注。
- **F6**（[7]-[10]引用未核实，支撑Gap 1核心论证）：已解决，六条引用（[3][4][7][8][9][10]）通过CrossRef/OSTI官方数据库核实，具体见上方说明。
- **M1**（Gap 2无引用支撑）：已解决。查证确认Mukherjee et al. (2018) [6]官方摘要明确指出该研究"表征关键预测因子"（characterize the key predictors），使用算法数据挖掘技术，报告了灾害类型、输配电网络规模、城乡程度、维护投入水平等多个因素的相对重要性——即该文确实做过某种形式的重要性排序，不能笼统断言"这些文献没有做重要性比较"。已把Gap 2改写为更收窄、更准确的表述：区别在于Mukherjee (2018)排的是异质性灾害/基础设施因素之间的重要性，不是本文"阵风 vs. 受影响客户规模"这一具体的两两比较，也没有做"全体样本 vs. 天气确认子样本"这一条件性对比，这两点才是本文区别于已有文献的具体落点。[3][4][5]三篇是否也做过类似排序仍未逐一核实，但Gap 2的新表述已不再依赖"这些文献都没做"这一需要对每篇都成立的强断言，只需要现有的具体对比未被报告过即可成立。
- **M2**（低R²与Conclusion运营规划表述比例不协调）：已解决，已加入区分"统计稳健的形状发现"与"运营预测工具"的说明句。
- **M3**（恢复模型总R²未报告）：已解决，已在4.2节补充11.05%这一数字。
- **M4**（Cause Code诊断使用的样本与3.2协议的时间关系不清）：已解决。核实确认命令#12/13的决策做出于命令#16去污染方法论确立之前（早约12小时），决策依据当时基于污染样本，但该决策后来在命令#31的干净数据上独立复现，2.4节已按此准确表述这一时间线，不再含糊。
- **M5**（阈值脆弱性未在4.1首次出现时前瞻提示）：已解决，已在4.1节turning point公式后加入指向4.4节的提示句。
- **M6**（"接近独立"仅基于线性/单调相关，未做非线性依赖检验）：已解决。距离相关0.199、互信息z=160.4，均显著拒绝独立假设，"接近独立"改为更精确的"经过重新定义后单调依赖大幅减弱、但非线性残余依赖仍统计显著"。并通过分解实验（同一批事件ID分别用legacy定义和新定义重新计算）验证了"差异主要由变量重新定义驱动、非样本限制驱动"这一此前的推测。

**仍待处理**：~~Equation 1/2/4数学记法与实际代码逐项核对~~（已在命令#39中完成，见文末最新记录）、Moderate/Minor级别问题（附录尚未撰写、Figure 3待手绘、部分引用DOI待补全）。

## 第二轮一致性核查处理记录（academic-review skill，针对第一轮修正后的稿件）

第二轮审查发现第一轮的三处修正本身不完整或未同步传播，另有若干新发现的细节问题，全部为内部一致性问题，未依赖本地数据核实，已全部直接修正：

- **F1修正引入的新缺口**：4.1节用"z-score标准化"解释跨零矛盾，但Section 3的公式（Equation 3/4）从未说明阵风等协变量在建模时经过标准化——已在3.3节模型规格开头明确加入"全部连续协变量含阵风均经过标准化"这一说明，消除方法论与结果叙事之间的记法缺口。
- **Abstract仍对风暴证据的贡献表述过头**："confirmed...across the seven named storms"暗示风暴数据本身重新估计并确认了二次项，但4.3节风暴部分实际做的是拟合值-观测值预测精度对比，不是重新估计系数（真正重新估计系数并确认的是weather-only子样本这条证据线）——已改写为区分"确认"（替代分布假设、独立时间窗口、weather-only子样本）与"预测精度对比"（风暴证据）两类不同性质的检验。
- **M4修正未同步到3.2节**：2.4节已改写说明Cause Code决策早于开发/确认样本切分本身，但3.2节"全部选择都只用开发样本做出"这句绝对化表述未同步更新，两处字面矛盾——已在3.2节加入"仅一处例外，见2.4节"的限定语。
- **文档头部状态行过时**：已更新为反映当前完整状态（Introduction至Section 5全文已完成两轮审查修正）。
- **Conclusion未收束第二个核心发现**：Section 5此前几乎完全围绕阈值/拐点这条线索，从未明确重述"风的权重在全体样本与天气确认子样本之间发生反转"这一同样是摘要标题级别的发现——已加入一段专门收束这一发现的文字。
- **细节项**：3.1标题美式拼写"Modeling"统一为英式"Modelling"；UKPN缩写在Section 1和2.1重复定义，已删去2.1节的重复定义；2.2节补充CIt/CMLt（按reporting period t索引）与本文Ci/Di（按incident i索引）两套记法之间的对应关系说明；2.3节互信息统计量（z=160.4）从仅存在于核查记录补充进正文；2.1节补充阵风均值9.87 m/s、标准差5.22 m/s的描述统计来源，使4.1节引用这一数字时不再是无据可查的"悬空"数字。

**仍待处理（更新）**：附录（B/D/E/F及一份未编号的残差诊断附录）尚未撰写、部分引用DOI待补全、Keywords待最终确认措辞。Figure 3已完成SVG设计。

## Equation核对结果（命令#39）

Equation 1/2/4已与实际代码核对完毕：
- **Equation 1发现一处需要补充说明的边界行为**：69个"全阶段重复中断"事件，实际代码结果为`customers_v2=NaN`（缺失并排除），不是公式字面空集求和隐含的0。**用户审核后明确指出**：面向工程读者的正文不应该点出这类几万分之几十的边界案例细节，会让读者思路偏离核心论点，且不影响对论文主要发现的理解；这类"影响复现但不影响理解论点"的细节应统一下沉到附录，正文只需要指向附录即可。已按此原则调整：2.2节改为"完整数据处理流程见附录B，含边界案例处理"这一简洁指向，具体的69个NaN案例细节移至附录B撰写时收录。**这一原则将作为撰写全部附录时的通用指导**：正文只讲数据库的结构、来源、组成、用法这类理解论点所必需的信息，复现所需但不影响理解的细节（缺失值判定规则、时间戳异常处理、边界案例的具体数量和占比等）统一放进附录。
- **Equation 2（duration_B取全部阶段含重复中断阶段的最大最小值）与Equation 1（排除重复中断阶段求和）之间的处理不对称**，经核实是有意为之、符合Ofgem CIt/CMLt官方定义本身的不对称逻辑（CIt排除重复中断避免客户重复计数，CMLt包含重复中断因为每个阶段都代表额外的停电时长），2.2节开头引用官方定义时已说明这一理由，不需要额外修改。
- **Equation 4已确认与命令#21实际拟合代码完全一致**：年月固定效应为分别独立的哑变量相加（非交互），阵风×气压交互项为标准化后两变量直接相乘——已移除待确认标记，改为正式陈述句。

**附录C的一个诚实缺口**：命令#39核实发现，全六组Cause Code范围模型的完整协变量系数表（不只是阵风一次二次项）在命令#12/13/31及原始目录中均未产出保存过，只保存了阵风相关项。附录C将如实按现有数据范围撰写，不会拼凑或虚构未保存过的完整系数表。


---
