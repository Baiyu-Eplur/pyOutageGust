# 版本与运行环境

实际根目录 `D:\Pyprogramme\STST2603\claude_branch`；用户路径中的下划线转义/目录分隔按已存在目录解析。无适用 AGENTS.md。Git rev-parse 确认这里及父目录不是 Git 仓库；没有可报告的未提交 diff。本次建立 91 个逐文件哈希一致源码副本，源和副本映射见 source_snapshots.json；未来修复逐文件留补丁，不创建或迁移 Git。

旧审计监测的 549 个文件无变化，不代表未受监测文件也被全面审计。两份本地最新稿与交接包 supplied_manuscripts 的 SHA256 一致，详见 manuscript_versions.json。研究输入 raw/v3 与 H0 一致。

解释器：`C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`，3.12.14。以 `-B` 启动，在任何科学库导入前令 `sys.dont_write_bytecode=True` 并前置 `D:\Pyprogramme\STST2603\.venv\Lib\site-packages`。已实际导入 numpy 2.4.3、pandas 3.0.1、scipy 1.17.1、statsmodels 0.14.6、sklearn 1.8.0。原 .venv 启动器引用不存在的 Python，不使用该启动器、不重装。详细运行方式在 code/r00_intake.py。

只导入已知科学依赖，没有导入历史研究模块。`-B` 不能防止其他副作用。运行时/版本核验不等于全部未来地理或绘图依赖已验证。
