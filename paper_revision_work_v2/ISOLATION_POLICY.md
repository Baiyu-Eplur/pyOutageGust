# 修复研究与原有研究的隔离约定

依据用户本轮要求：所有新工作基于原有研究独立推进，不破坏原有代码。该要求细化并替代旧 R02 计划中“直接修改既有活动入口”的落地方式；以后在新的修复流程内接入新入口。

- 原有 `scripts/` 中已存在的研究脚本、`results/`、稿件、父目录数据和生产者均作为只读历史基线。不得覆盖或重定向原有函数来运行新分析；保留旧缺陷与 H0 身份，不在此处偷偷修复。
- 新代码使用独立目录 `scripts/event_input_repair/` 和 `paper_revision_work_v2/code/`；新数据、报告、检查、配置和版本清单写在 `paper_revision_work_v2/`。后续 R03 可另建明确的新目录，不能复用旧生产者的固定输出路径。
- 当前新输入入口为 `scripts/event_input_repair/r02_input_pipeline.py`；原 `scripts/v3_validation/v3_validation_pipeline.py` 已恢复为 H0，并非修正分析入口。新入口不导入或调用原 v9/combined/dev/holdout 生产链。
- `run_r02.py` 的 prepare/weather/finish 是新流程的显式生产命令，本次隔离不重跑、不改动其数据。开始后续阶段时新建版本/输出位置，保留 R02 主表及其 manifest，不能静默覆盖历史结果。
- `R02/checks/active_entry.json`、旧补丁、R02 初次保护记录是迁移前历史证据；当前入口以 `R02/ISOLATED_ENTRY.json`、`R02_isolation_audit/validation.json` 和 RUN_STATE 为准。不得将旧验收记录误读为当前仍接管原入口。
- 恢复原代码的验收是与冻结源码逐字节 SHA256 一致。不会为检查“能否运行”而重跑具有固定写入副作用的旧模型/图表脚本。源码恢复不代表原研究方法缺陷被修复。
- 后续每次运行检查受保护文件、源数据与缓存身份；只有新流程的文件可以按已授权任务更新。任何未来修改原有文件的需要，必须先明确指出路径和用途，再取得针对该改动的用户授权。

本轮审查与隔离没有开始 R03，没有拟合模型、抓取新天气或修改论文。
