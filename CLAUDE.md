# CLAUDE.md — AI collaboration rules for pyOutageGust

## Origin

This project was split out of `D:\Pyprogramme\STST2603\claude_branch` on
2026-09-08. Full context on what was migrated, why, and what external
dependencies were resolved is in
[`docs/migration_history/`](docs/migration_history/):

- [`external_dependency_audit_20260908.md`](docs/migration_history/external_dependency_audit_20260908.md)
- [`claude_branch_migration_plan_20260908.md`](docs/migration_history/claude_branch_migration_plan_20260908.md)

`D:\Pyprogramme\STST2603` (the old project) should be treated as **read-only
reference material** from this project, not something to depend on for new
work. If a script here still imports from or reads paths under
`D:\Pyprogramme\STST2603`, that is a known residual coupling (see `LOG.md`
for the specific ones still outstanding) — flag it rather than silently
deepening it.

## Where Claude Code may write

- `results/pretest/` — 本轮全部旧脚本的新增分析输出及中间数据，按类别/秒级运行时间保存。archive 内迁移前结果只读；运行记录位于 runs。
- `main.py`, `pretestmain.py`, `pretest_paths.py` — 用户授权建立的统一入口及路径模块；功能开关与运行目的只在 main.py 顶部设置。
- `data/generated/`, `review_package/results/` — 旧输出位置已停用；重跑必须经 main.py 写入 results/pretest。
- `LOG.md` — every change gets an entry (see below)
- Source files under `scripts/`, `paper_revision_work_v2/`, `review_package/code/`, `test/`, `docs/` **when the task explicitly asks for a code/doc change** there

## Where Claude Code may NOT write

- `data/external/` — read-only input snapshots copied from the old STST2603 project. If a file here needs to change, it needs to be regenerated in the old project and re-copied (see `data/external/README.md`), not edited in place.
- `src/` — do not modify without the user explicitly asking for a code change here. This holds this repo's own independent modules (e.g. `weather_features.py`); treat changes here as deliberate, not incidental.
- `paper_revision_work_v2/R03/`, `paper_revision_work_v2/R04/` — these are frozen, self-contained work packages (own vendored runtime + source snapshots). Do not touch unless the task is specifically about R03/R04.
- Anything under `D:\Pyprogramme\STST2603` — this project does not own that directory. Read from it only if a script still has a documented residual dependency there (see `LOG.md`); never write to it.

## Logging requirement

2026-09-09 起，开发修改逐步记入本文件同级的 `LOG.md`；每次执行分析另在
`results/pretest/runs/<YYYYMMDDHHMMSS>/` 保存目的、开关、逐步执行状态、日志及产物校验。
本阶段只接入旧流程，不更改导师 Comments、冻结研究包或统计定义。

**Every change must get a `LOG.md` entry, and the code change + the LOG.md
entry must land in the same commit.** No exceptions for "small" changes —
the log is what lets a future session (human or AI) reconstruct why the
repo looks the way it does without re-deriving it from git blame alone.

A LOG.md entry should say: what file(s) changed, why, and — if the change
is code (not just docs) — what smoke test or verification was run and its
result (pass/fail, key output values). Follow the existing entries in
`LOG.md` as a format example.

## General

- Prefer editing existing files over creating new ones; don't restructure
  directories without being asked.
- If a task would require writing outside this repo, stop and ask instead
  of doing it.
