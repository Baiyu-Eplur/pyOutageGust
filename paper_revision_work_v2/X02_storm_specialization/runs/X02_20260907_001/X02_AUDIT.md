# X02-A audit

Run: `X02_20260907_001`
Started UTC: `2026-09-07T11:53:10.583882+00:00`

## Input identity

The authoritative corrected event contract is `D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R02\data\R02_event_master.parquet` (SHA256 `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`), matched to its R02 manifest. It contains 135,025 unique event rows.

The event identity is a record-level incident reference contract, not a certified physical-fault identity; two source cases remain explicitly unresolved and are excluded by the parent candidate flags.

## Outcomes

C is the sum of non-reinterruption stage customers. D is the full recorded event span in hours from the earliest stage start to latest stage end. E_log retains C=0; R_log/R_C_log require D>0. No test-outcome p99 truncation is used.

## Windows and grouping

Named windows sum to 27 days and their UTC union has 25 days. They form P1–P5; Dudley/Eunice/Franklin are one protected group P2. The storm union contains 7,300 unique events; 702 events have multiple name labels but one protected group and are counted once in primary scoring.

UTC versus same-date Europe/London calendar membership differs for 6 events. This sensitivity was not used to select windows.

## Feature-time boundary

F0 uses audited historical weather and static regional covariates plus transferable calendar encodings. These support observed-weather conditional retrospective prediction only. Final cause, stage count, end time and final C are excluded from F0; final C enters only R_C. F1 is skipped because no auditable timestamped operational/pre-forecast archive is present.

## Figure 9

R04 Figure 9 descriptive predictions are full-sample fitted values. The companion date-group OOF panel is not process-held-out. See `FIG9_PROVENANCE.md`.

## Gate

X02-A gate: **PASS**. Protocol freezing may proceed only if PASS.
