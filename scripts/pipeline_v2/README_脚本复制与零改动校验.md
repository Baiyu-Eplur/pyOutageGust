# pipeline_v2 脚本目录说明

## Step 2：九步主链脚本复制（原样复制，暂不修改）

全部12个脚本已从只读镜像（`/mnt/user-data/uploads/STST2603/`，即命令#6已经通过设备桥拉取到云端沙箱的原始文件副本）用`cp -p`逐字节复制到本目录，文件名加`_v2`后缀。复制前后分别计算了SHA256哈希，记录在`00_LAD脚本零改动哈希校验.txt`里，复制阶段全部12个文件哈希完全一致，证明复制过程本身没有引入任何改动。

## Step 3：按命令授权范围做的后续修改

复制完成后，按工作命令#7的硬性约束3（"只修改本命令明确要求修改的部分——Cause Code筛选步骤、事件合并聚合逻辑、duration计算"），对其中**2个**文件做了有意修改：

- `filter_v2.py`：实现规则1（取消Cause Code预筛选）+ 规则2（customers_v2/duration_A/duration_B事件级聚合）。
- `data_arrange_v2.py`：不再自己计算单阶段Duration，改为透传`filter_v2.py`已聚合好的duration_A/duration_B两列，其余Hour/Month/Weekday/Daytime Indicator计算方式不变。

**其余10个文件保持零改动**，复制后未做任何编辑。

## 零改动校验（复制后再次计算哈希，确认未改动的文件确实未改动）

| 脚本 | 复制前哈希（前16位） | 修改后当前哈希（前16位） | 状态 |
|---|---|---|---|
| `match_lad_v2.py` | d393c14733a0ec51 | d393c14733a0ec51 | ✅ 零改动 |
| `Buckinghamshire_combination_v2.py` | 85301a882d318e76 | 85301a882d318e76 | ✅ 零改动 |
| `LAD_GeoMerge_v2.py` | 2c21e4d8733c399a | 2c21e4d8733c399a | ✅ 零改动 |
| `LAD_AreaSummary_v2.py` | 9c4e6f5a3cfd72f0 | 9c4e6f5a3cfd72f0 | ✅ 零改动 |
| `LAD_urban_Summary_v2.py` | 3f003a8d510378ff | 3f003a8d510378ff | ✅ 零改动 |
| `LAD_DNO_v2.py` | b1c0942395d1e104 | b1c0942395d1e104 | ✅ 零改动 |
| `main1_v2.py` | 9234c3bc6188e029 | 9234c3bc6188e029 | ✅ 零改动 |
| `poppulation_merge_v2.py` | eacea91cd7a90753 | eacea91cd7a90753 | ✅ 零改动 |
| `GVA_new_v2.py` | 7839e5b45420e870 | 7839e5b45420e870 | ✅ 零改动 |
| `GVA_merge_with_crosswalk_v2.py` | 4d7d1696d12ec09d | 4d7d1696d12ec09d | ✅ 零改动 |
| `filter_v2.py` | a8ff20df2933dcf5 | d9d3cc1a01e51a10 | ⚠️ 有意修改（规则1+规则2） |
| `data_arrange_v2.py` | 286c65d837bce1a3 | d5471c07bbcd8e94 | ⚠️ 有意修改（duration透传） |

**结论**：命令要求"原样复制、零改动"的LAD相关三处逻辑（`match_lad.py`、`Buckinghamshire_combination.py`、`LAD_GeoMerge.py`）及其依赖的LAD地理特征子链三脚本（`LAD_AreaSummary.py`、`LAD_urban_Summary.py`、`LAD_DNO.py`），以及未被命令列入改动范围的`main1.py`/`poppulation_merge.py`/`GVA_new.py`/`GVA_merge_with_crosswalk.py`，全部确认为逐字节零改动。只有命令明确授权可以修改的`filter.py`（Cause Code筛选步骤+事件合并聚合逻辑）和`data_arrange.py`（duration计算）被有意修改，改动内容详见`../../results/pipeline_v2_output/02_重建方法论与证据链.md`第3节的逐条说明。

## 路径调整说明

`filter_v2.py`/`data_arrange_v2.py`的`__main__`块中输出路径已改为指向`claude_branch/results/pipeline_v2_output/`（硬性约束2：新数据产出只能放`claude_branch/`之内），而不是原脚本硬编码的`data/new/`路径。LAD相关脚本因为本命令不要求实际跑通下游链路（见`03_下游重跑规模评估.md`），暂未调整其输入路径，仍保留原始的`data/new/...`路径字符串，留待未来真正需要跑通下游链路时再行调整（届时仍需保证只调整路径、不改动计算逻辑本身，与本命令的处理原则一致）。

## 2026-09-09 统一入口调整

上文的“零改动”及哈希表描述当时复制阶段的历史状态。当前用户已授权统一改造全部旧脚本：本目录通过 main.py / pretestmain.py 调用，输入与输出使用 pretest_paths，新增产物进入 results/pretest/data/<时间>/；统计处理公式保留。新的改动清单见 ../../docs/migration_history/pretest_source_changes_20260909.json；步骤日志见 ../../LOG.md。旧哈希记录作为历史证据保留，不能用来声称当前文件仍逐字节未修改。
