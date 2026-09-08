# Figure 9 provenance

The currently retained Figure 9 producer is the R04 formal pipeline output, not the user screenshot.
Producer: `D:\Pyprogramme\STST2603\claude_branch\scripts\final_combined_analysis\figure9_storm_validation.py` (SHA256 `53b4deb7895b8ca5abcdede25f4897af00f540720b1694aa1065284da8e04133`).
Formal run: `D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R04\R04_B1_all_valid_v1`.

The descriptive panels use full-sample fitted values: every plotted event has `was_in_this_fit=True`.
The companion OOF panels use global date-group OOF predictions (`was_in_this_fit=False`), but are not leave-one-storm-process-out predictions.
Thus neither panel is an external storm validation. X02 creates separate protected-process evaluation.

The plotted outcome and prediction are both on the direct log target scale (`prediction_eta`); the earlier double-log transform is not used in R04.

## Recalculated values

| target | prediction_kind | path | sha256 | rows | unique_events | duplicate_event_rows | was_in_this_fit_n | pearson_y_prediction | r_squared_predictive | mean_y | mean_prediction | sd_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main_E0 | descriptive | D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R04\R04_B1_all_valid_v1\main_E0\figure9_descriptive_events.csv | 6b36fee9c58daa04455d8651db93a9a7dcb28bc3a2cb253954b2b6fa2684f36f | 4452 | 4452 | 0 | 4452 | 0.2850547 | 0.077319972 | 2.8102047 | 2.7256107 | 0.33530432 |
| main_E0 | OOF_diagnostic | D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R04\R04_B1_all_valid_v1\main_E0\figure9_OOF_diagnostic_events.csv | 0b76d302ccdd77314c5743a5ec56c589b0d9a19eec3f4b81af5962e70c0aea64 | 4452 | 4452 | 0 | 0 | 0.26792033 | 0.052754293 | 2.8102047 | 2.8128183 | 0.40585388 |
| main_R0c | descriptive | D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R04\R04_B1_all_valid_v1\main_R0c\figure9_descriptive_events.csv | f836e7b3df8dd70d4eb87eea36e33e0943a412d5da610d4704dc4d031e4432e4 | 4452 | 4452 | 0 | 4452 | 0.37739522 | 0.11835844 | 2.4209944 | 2.1615822 | 0.39491814 |
| main_R0c | OOF_diagnostic | D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2\R04\R04_B1_all_valid_v1\main_R0c\figure9_OOF_diagnostic_events.csv | d48e15caf9676f744a3755d9e1653ac7a8e3b0696c4f2f125d66288e50c75ebf | 4452 | 4452 | 0 | 0 | 0.32433733 | 0.059565172 | 2.4209944 | 2.0618176 | 0.33311229 |

The original R04 descriptive fit has complete training/plot overlap. The date-OOF diagnostic has no row in its own fitted fold, but storm processes are dispersed across its date folds.
