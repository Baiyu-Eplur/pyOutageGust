# 本地复现与环境身份

根目录 D:\Pyprogramme\STST2603\claude_branch。生产运行只依赖 R03 的新源码、复制的 Python/第三方包、冻结参考数据以及只读 R02 主表。不从原研究或父项目 .venv 动态导入。

Python 3.12.14；numpy 2.4.3、pandas 3.0.1、scipy 1.17.1、pyarrow 25.0.1；用于数值核对的 statsmodels 0.14.6。精确文件身份见 frozen/RUNTIME_MANIFEST.json（7,711文件）。这是 Windows 本地可运行副本，仍依赖操作系统和系统 DLL，不是跨操作系统容器。

```powershell
Set-Location 'D:\Pyprogramme\STST2603\claude_branch'
& '.\paper_revision_work_v2\R03\runtime\python\python.exe' -I -S -B '.\paper_revision_work_v2\R03\cli.py' test
```

最新完整 smoke 配置为 configs/smoke_v4.json，run_id=R03_smoke_v4。该目录已存在，因此原命令重跑会有意拒绝覆盖。需要复跑时复制配置，显式给一个新的 run_id 和不存在的 output_root，保留 purpose=non_inferential_smoke、全部身份和其他参数，然后运行：

```powershell
& '.\paper_revision_work_v2\R03\runtime\python\python.exe' -I -S -B '.\paper_revision_work_v2\R03\cli.py' smoke --config '<新的smoke配置绝对路径>'
```

已有结果见 smoke/R03_smoke_v4/RUN_MANIFEST.json；最新测试日志 logs/tests_release.txt、smoke 日志 logs/smoke_v4.txt。17 项测试通过，720事件/536日期/110 LAD 的 E/R 主组小样本试跑通过（图10后期被明确隔离）。24 项完整候选设计支持检查只组装矩阵、检查秩和评价类别，拟合数为0，见 checks/R04_design_support.json。

导入测试先执行 Python 标准库 platform.uname 的 Windows 只读系统版本探测，然后开启写入/网络/子进程拦截，导入研究及数值模块；未见研究导入写旧路径或动态加载原项目代码。不能把它说成操作系统探测本身完全没有子进程。CLI 另记录全部 Python 模块 __file__，本次均位于 R03。

初始化脚本 code/r03_prepare.py 只用一次，禁止重复初始化覆盖。accept 阶段已完成，不需要重扫天气缓存；code/r03_release_checks.py 是设计支持及发布配置准备脚本，也不应为了普通复跑覆盖已冻结发布配置。R04 正式命令和阻断范围见 R04_READINESS.md，本轮未运行。
