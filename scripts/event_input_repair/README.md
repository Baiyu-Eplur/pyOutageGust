# 独立的 R02 输入修复代码

本目录为本次修复新建；不覆盖原有研究脚本，不导入旧 v9 生产链。

| 文件 | 用途 |
| --- | --- |
| r02_events.py | 全阶段事件、时间、天气窗口和资格规则；导入不写文件 |
| r02_input_pipeline.py | 当前独立输入入口；读取哈希校验的 R02 主表 |
| test_r02_events.py | 针对已识别输入问题的 15 项测试 |

显式生产器：`D:/Pyprogramme/STST2603/claude_branch/paper_revision_work_v2/code/run_r02.py`。

当前验收：使用已验证 Python 运行 `paper_revision_work_v2/code/audit_r02_isolation.py validate`。旧 `check_r02.py final` 与 `close_r02.py` 的 CLI 已标记为迁移前历史流程，不能用它们重新发布旧入口元数据。

当前输入版本和数值仍为 R02_input_20260905。本轮仅隔离入口并恢复原代码；R03 的模型生产接口尚未实现。
