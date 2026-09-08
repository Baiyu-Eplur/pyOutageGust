# X02 experiment contract

Frozen UTC: `2026-09-07T11:57:14.753507+00:00`. Input SHA256: `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`. Seed: `20260907`.

## Scope and estimands

This is a retrospective conditional prediction study among corrected-contract events in the pre-existing main cause population. E_log is ln(1+C); R_log is ln(D/hour); R_C_log adds final ln(1+C) and its square and is explicitly post-event conditional. All primary scores are squared error on the log target. Test outcomes are never used for trimming.

F0 contains observed historical weather at/through the proxy event hour, static regional covariates, licence/RUC categories, transferable seasonal terms and a continuous trend. Final cause, stage count, end time, final event totals and storm-name identity are not F0 predictors. F1 is skipped because no timestamped operational or forecast archive is verified.

## Path A (must finish first)

Development groups are P1 Arwen, P2 Dudley/Eunice/Franklin and P3 Babet. P4 Ciarán and P5 Henk form the fixed time test. The fitting cutoff is `2023-10-29T00:00:00+00:00`. Labels are treated as mature only when the recorded maximum stage end is before the cutoff; publication delay remains unknown. Development tuning uses leave-one-development-process-out macro-MSE. After selection is locked, one frozen fit scores P4/P5 without updating between storms.

## Path B (only after time-test sealing)

Five outer folds leave out P1–P5. Tuning is nested by leaving one of the remaining four groups out. This is retrospective cross-process validation and not forward prediction.

## Protection and preprocessing

The fitting interval [event proxy start, recorded max end] may not intersect a held process interval expanded by 48 hours. Actual fit IDs are saved per fitted model. Numeric means/scales, categorical levels, knots, optimisation and tuning are training-only. Unknown categories map to all-zero reference coding.

## Selection

Candidates and grids are exactly those in `MODEL_REGISTRY.json`. The primary criterion is protected-process macro-MSE. Within 1% of the lowest score, reliable and simpler candidates are preferred in the predeclared order B00, B01, S01/G02/S02, P00, P02, S03, S04, G05/S05. E, R and R_C are selected independently. All valid and failed candidates remain reported.

## Inference boundary

The study can evaluate conditional prediction transfer across five historical process groups under observed-weather covariates. It cannot establish onset-time forecast performance, causal damage thresholds, storm-total impact, or an independent untouched confirmation set.
