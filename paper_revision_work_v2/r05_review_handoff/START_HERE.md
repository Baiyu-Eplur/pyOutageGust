# R05接续包：先核实项目，再设计补证

当前状态：R00–R04已执行；本包完成R04返回材料审阅，未执行R05/V/W。

把整个r05_review_handoff文件夹放在本地修复项目根目录下。历史项目根为D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2；以实际位置为准。

向本地Codex发送：

> 请读取r05_review_handoff/START_HERE.md及r05_review_handoff/R05_CODEX_INSTRUCTIONS.md，按其中R05-0至R05-7执行本轮R05。先核验并按ID合并manuscript_record_seed中的完整MR-v1.4-R04-review，保留本地更晚修改、作者决定及历史。完成项目验收、数值与推断核查、客户比较、最终消费者复现、逐章/段落候选修改和待补验证清单，交付RETURN_PACKAGE_R05.zip。只做R05，不启动V/W，不修改Word；发现影响当前结果的实际错误时在独立派生版本最小修复并重算依赖部分。

包内文件：

- R05_CODEX_INSTRUCTIONS.md：完整审阅及可执行R05任务。
- manuscript_record_seed/：完整当前29MR/6CL台账、章节/附录/段落方案、历史、Word索引及48个证据来源；不是一个空模板。
- manuscript_record_seed/R04_REVIEW_DELTA.json：本轮按ID合并增量及已知基版SHA，review_id用于避免重复导入。
- R04_PACKAGE_REVIEW_CHECKS.json和review_package.py：仅对返回包做的只读算术/哈希检查；不是R05已完成的证明。脚本需Python/pandas，参数是解压后的R04目录及检查JSON输出路径。
- manuscript_record_seed/evidence/SRC39_RETURN_PACKAGE_R04.zip：本轮输入完整包的原字节证据；大原始数据/完整OOF按B1清单在本地。
- HANDOFF_MANIFEST.json：以r05_review_handoff根目录为基准的相对路径/大小/SHA清单，不含清单自身。

导入前保存当前项目台账快照；较新本地记录不能整体覆盖。正文当前五章，候选六章待审。Buck重建对照已决定，不能降为可选。R04新结果改变天气E负增量、二次形状、阶段合并曲线及若干风暴/客户叙述，均已写进台账。
