# Upstream issues (read-only sources)

## U-01 — X01 cause indicator mismatch

Status: confirmed in `D:\Pyprogramme\STST2603\claude_branch\test\research_exploration\shape_models\X01\X01_20260906_001\src\x01_run.py`.

The event contract uses `technical_asset`, whereas X01 searched for `asset`; the resulting indicator was all zero. X02 excludes final cause from F0, so this issue is detected but not used to expand the information set.

Evidence lines:

- `controls = ["pressure_msl_0h","temperature_0h","precipitation_24h_sum","log_population","income_deprivation_rate","deprivation_gap_pct","morans_i","urban_binary","calendar_sin","calendar_cos","calendar_trend","cause_asset"]`
- `raw["cause_asset"]=(raw["cause_group_event"].astype(str).str.lower()=="asset").astype(float)`

## U-02 — Business onset/time zone

The verified contract supplies `event_time_proxy_utc=earliest_available_stage_start`; business onset and business calendar timezone remain unverified. X02 uses the frozen UTC proxy and reports a London-calendar sensitivity only.

## U-03 — Weather availability

Historical cached observations are auditable as retrospective covariates, but their real-time publication/forecast availability is not. F1 is therefore skipped rather than inferred.
