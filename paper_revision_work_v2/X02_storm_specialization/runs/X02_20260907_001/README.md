# X02_20260907_001

This isolated run completed X02-A through X02-F. It did not modify upstream data, scripts, figures, manuscripts or X01/R-stage artifacts.

## Source-data refit

Required source: `D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R02\data\R02_event_master.parquet`  
SHA256: `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`

Using the recorded environment, execute in order from `src/`: `stage_a_audit.py`, `stage_b_freeze.py`, `stage_c_develop.py`, `stage_c_time_score.py`, `stage_d_fivefold.py`, `stage_e_validate.py`, `stage_f_report_package.py`. A fresh run directory is recommended; do not overwrite this sealed evidence run. The original invalid Path-B v1 is evidence only and must not be treated as a resumable valid result.

## Prediction-only recalculation

`predictions/time_test_predictions.parquet` and `predictions/fivefold_oof_predictions.parquet` contain anonymous stable event IDs, task/model/path/split/episode, outcomes and predictions. Recompute MSE as mean((y-pred)^2), RMSE as its square root, MAE as mean absolute error and R² against the same evaluation set mean. This path does not require the source event table. Independent recalculations are already stored in `evidence/`.

## Evidence map

- Audit and provenance: `X02_AUDIT.md`, `FIG9_PROVENANCE.md`, `DATA_MANIFEST.json`.
- Frozen protocol: `EXPERIMENT_CONTRACT.md`, `run_config.yaml`, `MODEL_REGISTRY.json`, `evidence/PROTOCOL_LOCK.json`.
- Selection/time seal: `MODEL_SELECTION_LOCK.json`, `TIME_TEST_FROZEN_REPORT.md`, `evidence/TIME_TEST_SEAL.json`.
- Corrected fivefold and acceptance: `tables/`, `predictions/`, `models/`, `VALIDATION_REPORT.md`.
- Failures: `evidence/FAILURE_LOG.json`, `evidence/invalidated_pathB_v1/`.
- Interpretation: `X02_REPORT.md`, `RESEARCH_STORY_LOG.md`, `MANUSCRIPT_IMPLICATIONS.md`.
