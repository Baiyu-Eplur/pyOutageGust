# 主要里程碑：统一分析入口与 pretest 归档

日期：2026-09-09

标签：`pretest-unified-entry-20260909`

分支：`main`

仓库：[Baiyu-Eplur/pyOutageGust](https://github.com/Baiyu-Eplur/pyOutageGust)

发布记录：[GitHub Release](https://github.com/Baiyu-Eplur/pyOutageGust/releases/tag/pretest-unified-entry-20260909)

本节点完成导师代码迁入前的工程整理：全部 `scripts` 旧功能通过统一入口执行，历史结果收束到 `results/pretest`，后续研究可以按步骤开启功能，并追溯每次运行的目的、输入和产物。

## 主要改动

1. **统一主入口**：新增根目录 `main.py`，直接在文件顶部设置运行目的和功能开关，不引入 config 文件。共 117 个独立步骤开关，默认全部关闭；另支持预演、失败后继续和选择 Python 解释器。
2. **旧流程统一调度**：新增 `pretestmain.py`，接入 `scripts` 的 116 个运行步骤及 4 个公共模块，并接入 `review_package` 主回归。每步在独立进程执行，保留执行顺序、退出状态和控制台日志。
3. **结果路径统一与复用**：新增 `pretest_paths.py`，修正旧 Windows/Linux 硬编码路径及相对输出。关闭前置步骤时可读取已有成功结果；新结果不写回历史归档。缺少输入或父目录的兼容问题已修正，失败产物不进入可复用索引。
4. **历史归档**：721 个已有输出迁至 `results/pretest/archive/20260909154556/`，逐文件核对移动前后的 SHA256，保留旧新路径清单。根目录 `results` 现在仅含 `pretest`。
5. **分类与运行记录**：新结果按 `figures`、`models`、`data`、`analysis`、`checks` 分类，以年月日时分秒命名运行目录。`runs/<时间>/` 保存目的、开关、源码校验、逐步状态、输入来源及输出 SHA256；`latest.json` 维护成功结果索引。
6. **文档与维护**：更新 README、协作规则与旧目录说明；新增使用指南、完整步骤目录、迁移/验收清单和入口测试。新增 `.gitattributes` 原样保存 pretest 产物及活动源码，避免 Git 自动换行转换破坏 SHA256 记录。所有开发步骤逐项记录在根目录 `LOG.md`。

## 验证结果

| 检查 | 结果 |
|---|---|
| 入口、开关、结果复用、失败隔离、写入边界等框架测试 | 11 项通过 |
| 原有 R02 事件/天气规则测试 | 15 项通过 |
| 归档完整性 | 721 个文件 SHA256 一致 |
| 活动源码检查 | 121 个文件函数集合及函数内数值常量保持一致，语法检查通过 |
| 最终样本重建 | E0 60,437 条；R0c 59,834 条，两份 CSV 与旧版逐字节一致 |
| 主回归复现 | 4 份系数表及汇总 JSON 与旧版逐字节一致 |
| 单独重新绘图 | 前置拟合关闭时 Figure 4 成功生成，PNG 与旧版逐字节一致 |
| V2 全量事件聚合 | 237,901 个阶段 → 135,025 个事件，3 份 CSV 成功输出 |
| 其他实际执行 | LAD 面积输出、R02 只读输入检查与默认全关闭入口通过 |

共 8 个样本/回归/图片文件与旧版逐字节一致。V2 首次因新时间目录缺少父目录而失败，修复后的全量运行 `20260909155522` 成功；失败日志保留在 `20260909154903`，用于追溯。

## 使用方式

激活 `pyoutagegust` 环境，在 `main.py` 顶部填写 `RUN_PURPOSE`，把需要的 `PRETEST_STEPS` 项设为 `1`，其余保留 `0`，然后运行：

```sh
python main.py
```

## 本节点的范围与保留事项

- 导师 `Comments` 代码尚未迁入；`src`、`paper_revision_work_v2` 及原有独立/冻结研究包保持原始状态。
- 本次整理保留既有模型公式、筛样规则和统计定义；未批量重跑全部 bootstrap、天气下载及所有历史分析。
- 少数早期原始输入仍使用旧 `STST2603` 项目的只读副本。`data/external`、原 `review_package/data`、导师材料与已忽略的环境文件仍不纳入 Git；本次重新生成并保存在 pretest 下的验证结果随节点保存。
- 此节点位于原 `pre-review-checkpoint-20260909` 之后；同步也包含此前本地已有的导师材料只读审查提交，不能据此理解为导师算法已迁入。

## 详细记录

- [逐步更新日志](../../LOG.md)
- [使用指南](../PRETEST_GUIDE.md)与[完整步骤目录](../PRETEST_TASKS.md)
- [综合验收](../migration_history/pretest_acceptance_20260909.json)
- [历史结果迁移清单](../migration_history/pretest_archive_20260909.json)
- [数值与图片一致性验证](../migration_history/pretest_numerical_verification_20260909.json)
- [最终源码检查](../migration_history/pretest_source_verification_20260909.json)
- [旧输入依赖清单](../migration_history/pretest_input_dependencies_20260909.json)

标签指向包含本记录的提交；以标签定位版本，避免在自身文件内写入会随提交而变化的提交号。
