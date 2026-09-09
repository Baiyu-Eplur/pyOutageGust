# 里程碑节点：导师修改前的最终版本

**日期**：2026-09-09
**Git 标签**：`pre-review-checkpoint-20260909`（分支 `main`，含本记录文件自身——用标签而非直接写死 commit hash，因为改这份文件本身就会改变它所在提交的 hash，二者会互相追不上）
**远程仓库**：https://github.com/Baiyu-Eplur/pyOutageGust

## 这个节点是什么

这是 `pyOutageGust` 第一次推送到 GitHub 的状态，标记为**导师开始修改批注之前的最终版本**。此后 `Comments/` 目录会用来存放和处理导师的批注（该目录已加入 `.gitignore`，不进入这份代码历史）。之后如果代码因应导师意见发生变动，都是在这个节点之后发生的——需要回看"导师改之前长什么样"时，回到这个 commit/tag 即可。

## 项目结构（此节点，git 跟踪的部分）

共 **4,604 个文件**被 git 跟踪（打包后约 423 MB）：

| 目录 | 文件数 | 内容 |
|---|---|---|
| `paper_revision_work_v2/` | 3,638 | 论文修订工作包：`R02`–`R05`、`X02_storm_specialization`、`code/`；`R03`/`R04` 各自带独立 vendored 运行时 |
| `results/` | 700 | 各分析任务的产出（图表、系数表、JSON 摘要），按日期/任务分子目录 |
| `scripts/` | 123 | 按日期命名的分析任务脚本（数据修复、图表、稳健性检查、pipeline 各阶段） |
| `test/` | 106 | 探索性/验证性质的临时工作 |
| `docs/` | 23 | 设计笔记、审查记录、论文草稿、迁移历史、本里程碑记录 |
| `review_package/` | 7 | 独立审阅包代码（`code/run_main_regression.py` 等；`data/`、`results/` 为生成物，已 gitignore） |
| `src/` | 1 | 本项目自己的独立模块（`weather_features.py`，从老项目 `main1.py` 提取） |
| 根目录文件 | 6 | `README.md`、`CLAUDE.md`、`LOG.md`、`requirements.txt`、`environment.yml`、`.gitignore` |

**不在 git 里但本地仍有的内容**（见 `.gitignore`）：`data/external/`（只读输入快照，见 `data/external/README.md`）、`review_package/data/`（可由脚本重新生成）、`R03`/`R04` 的 vendored `runtime/site-packages/`、`Comments/`（导师批注处理区）。

## 项目内容概述

UK Power Networks（UKPN）天气-停电统计研究项目：阵风/气压/温度/降水暴露与停电事件发生率、恢复时长的关系模型，含 LAD 级别社会经济与地理协变量。本项目于 2026-09-08 从 `D:\Pyprogramme\STST2603\claude_branch` 拆分独立而来，完整拆分背景见 [`docs/migration_history/`](../migration_history/)。

到本节点为止完成的主要工作：
1. **迁移骨架**：从 `claude_branch` 整体复制 `scripts/`、`paper_revision_work_v2/`、`docs/`、`test/`、`results/`，并把 v3 数据集、LAD/DNO shapefile、天气缓存等 6 类外部输入复制进 `data/external/`。
2. **代码解耦**：把 `main1.py` 里用到的 5 个纯函数提取成独立的 `src/weather_features.py`；把 `review_package/` 做成完全独立的审阅包；断开了 `review_package` 数据生成链路（`corrected_sample_builder.py` 及其下游 7 个文件）对老项目 `claude_branch` 的最后硬编码路径依赖，并用 SHA256 校验确认解耦前后产出数据逐字节一致。
3. **独立运行环境**：新建 conda 环境 `pyoutagegust`（Python 3.12.6，与老项目一致），锁定 21 个第三方库版本到 `requirements.txt` / `environment.yml`；`R03`/`R04` 保持各自原有的 vendored 独立运行时。
4. **仓库治理**：`README.md`、`CLAUDE.md`（AI 协作规则：可写/不可写范围、每次改动同步更新 `LOG.md` 的强制要求）、`.gitignore`（排除只读外部数据、生成物、vendored 环境、导师批注区、以及一个超过 GitHub 100MB 限制的冗余压缩包）。

完整的逐次改动记录见项目根目录 [`LOG.md`](../../LOG.md)。

## 已知的、有意保留未处理的事项（此节点仍然存在）

- `scripts/final_combined_analysis/` 等约 116 个脚本仍硬编码老项目 `D:\Pyprogramme\STST2603` 路径——不在"断开 review_package 依赖"这次任务范围内，如需处理需单独立项。
- `paper_revision_work_v2/{R03,R04}/{frozen,runtime}/`、`X02_storm_specialization/runs/*/frozen_sources/`、`R05/frozen/source_audit/` 等目录里仍有大量指向老项目的字符串——这些是有意保留的历史快照/审计存证，不应修改。
- `paper_revision_work_v2/R02/data/R02_event_master.parquet`（52.4MB）超过 GitHub 建议使用 Git LFS 的 50MB 软阈值（未超过 100MB 硬限制，push 不受影响，只是会有警告）。
