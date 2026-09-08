# pyOutageGust

Statistical analysis codebase for a UK Power Networks (UKPN) weather-outage
study: gust/pressure/temperature/precipitation exposure vs. power-outage
incidence and recovery duration, with LAD-level socioeconomic and geographic
covariates.

## Background

This project was split out of `D:\Pyprogramme\STST2603\claude_branch` on
2026-09-08, to give the paper-revision work (fold validation, robustness
checks, the final regression models, the reviewer-facing model review
package) its own repository independent of the much larger, older STST2603
project. The full audit of what `claude_branch` depended on outside itself,
and the migration plan that was executed, are preserved in
[`docs/migration_history/`](docs/migration_history/):

- [`external_dependency_audit_20260908.md`](docs/migration_history/external_dependency_audit_20260908.md) — what pointed outside `claude_branch`, and what pointed into it from the old project
- [`claude_branch_migration_plan_20260908.md`](docs/migration_history/claude_branch_migration_plan_20260908.md) — the extraction/rewiring plan this repo's initial state follows

`paper_revision_work_v2/R03` and `R04` predate the split and already carried
their own frozen source snapshots and vendored Python runtimes at migration
time — see below.

## Directory structure

| Path | Contents |
|---|---|
| `scripts/` | Dated analysis-task folders (data repair, figures, robustness checks, pipeline stages) |
| `paper_revision_work_v2/` | Paper-revision work packages `R02`–`R05`, `X02_storm_specialization`, `code/`; `R02_isolation_audit` is an audit trail for R02 |
| `paper_revision_work_v2/R03/`, `R04/` | Self-contained: each has its own `frozen/project_sources/` (snapshotted source deps) and `runtime/site-packages/` (vendored installed packages) — **do not need this repo's environment**, see [Environment](#environment) |
| `src/` | This repo's own independent Python modules (e.g. `weather_features.py`, extracted from the old project's `main1.py`) |
| `review_package/` | Standalone, reviewer-facing package: fits the E0/R0c regression models from two static CSVs. `code/` is tracked; `data/` and `results/` are generated (`data/` is gitignored, regenerate via `scripts/model_review_package_20260907/materialize_final_data.py`) |
| `data/external/` | Read-only input snapshots copied from the old STST2603 project (gitignored — see [`data/external/README.md`](data/external/README.md) for provenance and how to regenerate each file) |
| `data/generated/` | Intermediate/derived data produced by this repo's own scripts |
| `results/` | Analysis outputs (figures, tables, JSON summaries), one dated subfolder per task |
| `docs/` | Design notes, review notes, manuscript drafts, migration history |
| `test/` | Exploratory/validation scratch work |

## Environment

Python 3.12.6, matching the old STST2603 `.venv`. A conda environment named
`pyoutagegust` is used for everything in this repo **except** `R03`/`R04`,
which are self-contained (they vendor their own `runtime/site-packages/`
and don't need any environment set up).

```sh
conda create -n pyoutagegust python=3.12.6
conda activate pyoutagegust
pip install -r requirements.txt
```

`environment.yml` (generated with `conda env export --no-builds`) records
the exact resolved versions from the environment this repo was set up with,
for reference/reproduction:

```sh
conda env create -f environment.yml
```

## How to run

Most scripts under `scripts/` and `paper_revision_work_v2/{R02,R05,X02_storm_specialization,R02_isolation_audit,code}`
are standalone, single-purpose analysis steps — read their module docstring
for what they expect as input and where they write output (usually
somewhere under `results/`).

To regenerate the review package's analysis-ready samples and refit the
main regression models:

```sh
conda activate pyoutagegust
python scripts/model_review_package_20260907/materialize_final_data.py
python review_package/code/run_main_regression.py
```

This writes `review_package/data/combined_E0_final.csv` /
`combined_R0c_final.csv`, then `review_package/results/*.csv` and
`run_summary.json`. Expected reference output (E0 gust turning point =
10.8072 m/s) is documented in `review_package/README.md`.

`R03` and `R04` are run using their own vendored interpreters/packages under
`paper_revision_work_v2/{R03,R04}/runtime/`; see each folder's own docs
under `checks/`, `configs/`, `acceptance/` for how they're invoked.

## AI collaboration rules

See [`CLAUDE.md`](CLAUDE.md) for what an AI coding assistant may and may not
write in this repo, and the logging requirement for every change.
