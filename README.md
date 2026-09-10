# pyOutageGust

**关键里程碑（2026-09-10）**：完成地区日持续性/冻结时间检验、A–J附录生产与C/J03/F02/GI/H03证据补全，交付A–E和F–J两批英文初稿。见[今日更新日志](dailylog.md)、[里程碑记录](docs/milestones/2026-09-10_analysis-appendices-checkpoint.md)及[版本发布](https://github.com/Baiyu-Eplur/pyOutageGust/releases/tag/analysis-appendices-checkpoint-20260910)。初稿与局部待定事项保留人工审核状态，不宣告正文主张全部验证。

**当前入口与结果**：普通实验使用[`main_new.py`](main_new.py)的独立开关；附录使用[`main_appendix.py`](main_appendix.py)，说明见[附录生产指南](docs/APPENDIX_PRODUCTION_GUIDE.md)。已完成的P03/P04、DD-AGG01、DD-DUR01、DD-TIME01及正式J03对照均有保存结果；当前附录位于[`results/Appendix/`](results/Appendix/)，文稿位于[`docs/new_analysis/writing/`](docs/new_analysis/writing/)。

**关键里程碑：导师分析独立复现（2026-09-09）**：新增 [`main_new.py`](main_new.py) 和 [`analysis_new/`](analysis_new/)，直接使用自己的相同样本，完整运行 16 步，交付 83 个产物。学习、方法和开关说明见 [`docs/NEW_ANALYSIS_GUIDE.md`](docs/NEW_ANALYSIS_GUIDE.md)；改动、验证与范围见 [里程碑记录](docs/milestones/2026-09-09_advisor-independent-reproduction.md)。版本标签：`advisor-independent-reproduction-20260909`（[发布说明](https://github.com/Baiyu-Eplur/pyOutageGust/releases/tag/advisor-independent-reproduction-20260909)）。

**主要里程碑（2026-09-09）**：[统一分析入口与 pretest 归档](docs/milestones/2026-09-09_pretest-unified-entry.md) — 新增 main.py 顶部统一开关，接入 117 个运行步骤，归档 721 个历史输出，记录每次运行目的与分类结果；26 项测试通过，8 个验证文件与旧版逐字节一致。版本标签：`pretest-unified-entry-20260909`（[发布说明](https://github.com/Baiyu-Eplur/pyOutageGust/releases/tag/pretest-unified-entry-20260909)）。

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
| `main.py` | 旧分析统一入口；顶部设置运行目的和每一步的 0/1 开关 |
| `main_new.py`, `analysis_new/` | 导师分析独立复现入口与模块；复用自己的样本和已有主回归 |
| `pretestmain.py`, `pretest_paths.py` | 旧研究步骤调度、路径解析、分类输出和运行记录 |
| `scripts/` | Dated analysis-task folders (data repair, figures, robustness checks, pipeline stages) |
| `paper_revision_work_v2/` | Paper-revision work packages `R02`–`R05`, `X02_storm_specialization`, `code/`; `R02_isolation_audit` is an audit trail for R02 |
| `paper_revision_work_v2/R03/`, `R04/` | Self-contained: each has its own `frozen/project_sources/` (snapshotted source deps) and `runtime/site-packages/` (vendored installed packages) — **do not need this repo's environment**, see [Environment](#environment) |
| `src/` | This repo's own independent Python modules (e.g. `weather_features.py`, extracted from the old project's `main1.py`) |
| `review_package/` | 旧 E0/R0c 回归代码与静态输入；现已接入 main.py，重新生成的样本和回归结果均进入 results/pretest |
| `data/external/` | Read-only input snapshots copied from the old STST2603 project (gitignored — see [`data/external/README.md`](data/external/README.md) for provenance and how to regenerate each file) |
| `data/generated/` | 原中间数据位置；本轮旧流程新增中间数据统一进入 results/pretest/data |
| `results/pretest/` | 旧研究结果：archive 历史归档；figures/models/data/analysis/checks 分类的新结果；runs 运行目的与日志 |
| `results/new/` | 新分析：秒级运行目录、分类结果、目的/源码/数据校验和逐步日志 |
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

在根目录 `main.py` 顶部填写 `RUN_PURPOSE`，把 `PRETEST_STEPS` 中需要的步骤设为 `1`，其余保留 `0`，然后运行：

```sh
conda activate pyoutagegust
python main.py
```

默认所有步骤为 `0`。`DRY_RUN = 1` 可只检查启用清单。直接运行 `pretestmain.py` 也读取同一份 main.py 参数。

例如，只重画旧 Figure 4：将 `final_combined_analysis/figure4_dose_response` 设为 `1`。
重建最终样本并回归：开启 `model_review_package_20260907/materialize_final_data` 与 `review_package/run_main_regression`。
关闭前置步骤时复用已有成功结果或迁移归档；缺少必需结果会明确报错，不会自动重跑前置任务。

图片结果位于 `results/pretest/figures/<YYYYMMDDHHMMSS>/<步骤序号>/`，其下保留原任务内的文件层级。
每次运行的目的、开关、执行状态、控制台日志、输入来源与输出 SHA256 位于 `results/pretest/runs/<YYYYMMDDHHMMSS>/`。

旧功能完整说明见 [`docs/PRETEST_GUIDE.md`](docs/PRETEST_GUIDE.md)。`paper_revision_work_v2` 内冻结研究包保持原样。

导师分析使用 `python main_new.py`，其顶部 `STEPS` 默认完整启用。每次填写 `RUN_PURPOSE`；增量执行时填写已完成运行的 `REUSE_RUN` 并关闭不需要重算的步骤。结果进入 `results/new/<YYYYMMDDHHMMSS>/results/`，逐步记录位于同层 `run.json` 和 `logs/`。详情见 [`docs/NEW_ANALYSIS_GUIDE.md`](docs/NEW_ANALYSIS_GUIDE.md)。

## AI collaboration rules

See [`CLAUDE.md`](CLAUDE.md) for what an AI coding assistant may and may not
write in this repo, and the logging requirement for every change.
