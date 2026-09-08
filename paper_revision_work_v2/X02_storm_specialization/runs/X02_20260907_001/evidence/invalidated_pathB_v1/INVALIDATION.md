# Path B v1 invalidation

The first five-process run is invalid for model comparison because the storm-population training-mask branch restricted training to the other protected groups but did not additionally remove long events whose recorded `[start, max end]` interval intersected the held process interval expanded by 48 hours.

The pre-validation audit found three underlying crossing events. Repetition across seven storm-population models and three tasks produced 63 artifact-level violations. The all-period branch already applied the buffer rule. No fit/test event-ID overlap occurred, but the frozen protocol requires both ID separation and interval protection.

All v1 tables, predictions, optimisation logs and the v1 seal are retained in this directory as an `invalid_model` result. They must not be cited as X02 results. The local X02 training mask was corrected and only Path B is rerun. The already sealed Path A time test is not rescored or changed.
