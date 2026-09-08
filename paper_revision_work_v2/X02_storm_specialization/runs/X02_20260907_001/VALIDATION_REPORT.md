# X02 validation report

Acceptance status: **PASS**.

check,value,pass
independent_time_metric_max_abs_diff,8.881784197001252e-16,True
independent_fivefold_metric_max_abs_diff,2.6645352591003757e-15,True
time_prediction_unique_keys,0,True
fivefold_prediction_unique_keys,0,True
fivefold_complete_4452_each,"min=4452,max=4452",True
model_and_fit_id_hashes,0,True
fit_test_id_intersections,0,True
held_buffer_intersections,0,True
time_path_label_cutoff_violations,0,True
forbidden_feature_violations,0,True
X02_instruction_package_unchanged,0,True


All exported scores were independently recomputed from event predictions. Actual fit-ID tables were checked against their validation/test events and frozen process buffers. Time-path labels end before the frozen cutoff. Core feature schemas contain no final cause, stage count, end time or outcome fields; final C appears only in R_C.

F1 and rolling features were not implemented because no auditable timestamped source was available; the synthetic rolling test is therefore not applicable rather than falsely passed.

Failure and negative-result record: `evidence/FAILURE_LOG.json` (3 entries).
