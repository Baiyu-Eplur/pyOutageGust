# R02 复现与文件身份

在 D:\Pyprogramme\STST2603\claude_branch 中使用已验证 Python：

```powershell
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/run_r02.py prepare
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/run_r02.py weather
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/run_r02.py finish
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/check_r02.py shuffle
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/check_r02.py final
& 'C:\Users\haoya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B paper_revision_work_v2/code/report_r02.py
```

这是显式复现说明，当前交付已经执行完成。run_r02 自动加载父目录 .venv/Lib/site-packages；禁写 pycache，不导入原始联网天气模块。prepare/finish 会更新本 R02 版本的派生文件，开始新科学版本时应先另建 run/output 目录。weather checkpoint 与 pre_weather_events 的 SHA/小时审查函数绑定；不一致会拒绝恢复，不能混用缓存审计结果。原 R02 preflight 是单次归档，不应重复覆盖 R00/R01 快照。close_r02 protection/close 属于验收和交接，不运行模型。

主表保留所有事件；candidate_* 是按合同的全有效候选，strict_candidate_* 另限制可重验缓存，H0_* 为已接收旧成员，R1_compat_candidate_* 为旧原因/独立p99诊断。source_stage_projection 保存全237901条原始20列及所需v3列。wx/地区字段名带 old_ 为旧代表源行，earliest_v3_ 为选中源行既存值；新字段为本轮派生，delta_ 是新减旧。所有源键依赖冻结原始SHA和行号，不能先重排raw后重新生成行号。
