# X02 research story log

| ID | Hypothesis / observation | Evidence | Strength | Direction change |
| --- | --- | --- | --- | --- |
| XS-01 | R04 Figure 9 is not an external storm validation. | `FIG9_PROVENANCE.md`; `tables/figure9_recalculation.csv` | Confirmed provenance | Motivates protected-process validation. |
| XS-02 | Seven storm names form five statistical protection groups. | `STORM_CATALOG.csv`; `EPISODE_MEMBERSHIP.parquet` | Confirmed under frozen UTC proxy | P2 is indivisible. |
| XS-03 | Storm-only quadratic training improves transfer over fair all-period quadratic. | `tables/predeclared_comparison_summary.csv` | Not supported; S02−G02 is positive in both time tests for every task and positive in five-process macro | Do not adopt storm-only quadratic. |
| XS-04 | A common storm level shift is sufficient. | P00−G02 rows in comparison table | Not supported consistently; especially adverse for R/R_C | Level shift does not explain a general gain. |
| XS-05 | Storm-specific quadratic interactions add stable value. | P02−P00 rows | Mixed signs across processes/tasks | No stable interaction claim. |
| XS-06 | Flexible storm curves add stable value. | S03/S04−S02; `tables/softplus_boundary_summary.csv` | Mixed; S04 width at lower bound and S03 process failure | Retain only sensitivity interpretation. |
| XS-07 | Tree interactions reveal useful information beyond quadratic. | S05−S02 and G05/S05 results | Some gain over S02, but storm-only S05 not consistently better than G05 | Flexibility matters more than storm-only population. |
| XS-08 | F1 adds operationally available information. | `FEATURE_AVAILABILITY.csv` | Skipped: source unavailable | Requires new timestamped/forecast archive. |
| XS-09 | R_C improves real-time restoration prediction. | Locked R_C results and feature contract | Prohibited interpretation; final C is post-event | Report only post-event conditional difference. |
| XS-10 | Negative and failed results are material. | `evidence/FAILURE_LOG.json`; invalidated Path-B v1 | Confirmed | Preserve in appendix/reproducibility record. |
