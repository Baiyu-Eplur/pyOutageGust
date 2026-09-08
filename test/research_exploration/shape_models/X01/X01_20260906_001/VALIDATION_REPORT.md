# X01 validation report

| check | status | observed | expectation |
| --- | --- | --- | --- |
| input_hash | PASS | 8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d | 8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d |
| leaderboard_27_unique_task_models | PASS | 27 | 27 unique task-model rows |
| three_tasks_nine_models | PASS | {'E': 9, 'R': 9, 'R_C': 9} | 9 models for each E/R/R_C |
| oof_row_count | PASS | 1631772 | 1631772 |
| one_oof_prediction_per_event_model | PASS | 27 | 27 task-model sets |
| oof_finite_and_full_coverage | PASS | 1631772 | 1631772 |
| outer_fit_records | PASS | 135 | 27 × 5 outer fit records |
| failure_records_retained | PASS | {'success': 160, 'warning_accepted': 2} | all status records retained regardless of success |
| paired_bootstrap_summary | PASS | 27 | 27 model-task summaries from 1,000 paired draws each |
| paired_bootstrap_draws | PASS | 27000 | 3 × 9 × 1,000 |
| six_refit_sets_200_each | PASS | {('E', 'M03'): 200, ('E', 'M05'): 200, ('R', 'M05'): 200, ('R', 'M08'): 200, ('R_C', 'M05'): 200, ('R_C', 'M08'): 200} | 6 selected task-model sets, 200 each |
| figure_pairs | PASS | {'png': 21, 'svg': 21} | 21 PNG and 21 SVG, including standardized curves and gust-support counts |
| root_documents | PASS | ['README.md', 'EXPERIMENT_CONTRACT.md', 'run_config.yaml', 'DATA_MANIFEST.json', 'DECISION_LOG.md', 'MODEL_REGISTRY.json', 'X01_REPORT.md', 'RESEARCH_STORY_LOG.md', 'RETURN_TO_CHATGPT_X01.md'] | all required nonempty documents |
| source_code_has_no_original_project_path | PASS | no original project path literal | scripts use only ROOT/frozen_sources |

Isolation audit: the model and finalization source files contain no original-project path literal; all data reads resolve from this run's `frozen_sources`. The execution record shows writes only under this run directory. The large frozen input is excluded from the return ZIP but remains locally hash-verified.
