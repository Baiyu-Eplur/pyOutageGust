# claude_branch 外部依赖审计报告

日期：2026-09-08
范围：只读审计，未修改/移动/删除任何文件。

**规模**：claude_branch 共 13,896 个文件、6,457 个 `.py`；其中 `paper_revision_work_v2/R03`、`R04` 各自带有独立的 `frozen/project_sources/`（快照）+ `runtime/site-packages/`（已装好的 vendored 环境），这两块本身就是"已隔离"的，不算在下面的分析范围内。真正的 live 代码约 288 个 `.py` 文件（`paper_revision_work_v2` 163、`scripts` 120、`test` 4、`results` 1）。

## 一、外部依赖路径列表

硬编码根路径 `D:\Pyprogramme\STST2603\...` 命中 448 处 / 164 个文件，其中 **81.5%（365 处）实际指向 `claude_branch` 内部**（安全，不用管）。真正跨出 claude_branch 的、且不算"历史快照"（`paper_revision_work_v2/code/snapshots/H0/` 目录也是快照性质，已排除）的，共 **31 个 live 文件**：

| 外部目标 | 说明 | 涉及文件数 | 示例 |
|---|---|---|---|
| `rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv` | 根目录 v3 数据集重建产物，几乎所有 v3 分析脚本的主数据源 | ~20 | `claude_branch/scripts/v3_validation/v3_validation_pipeline.py`, `claude_branch/scripts/c01_repair_20260905/step1_representative_row.py`, `claude_branch/scripts/final_combined_analysis/step10_named_storms.py` |
| `data/Local_Authority_Districts_..._UK_BGC.shp` | 根目录 LAD 边界 shapefile（制图用） | ~8 | `claude_branch/scripts/final_combined_analysis/figure1_study_area.py`, `claude_branch/scripts/c02_c08_repair_20260905/figure6_regional_map.py` |
| `data/dno_license_areas_20200506/...shp` | 根目录 DNO 许可区域 shapefile | 2 | 同上两个 figure1_study_area.py |
| `data/ukpn-iis.csv`、`data/new/ukpn_master_weather_matrix*.csv` | 根目录原始/中间事故数据 | 3 | `claude_branch/scripts/pipeline_v2/match_lad_v2.py` |
| `data/weather_request_cache/` + 根目录 `main1.py`（通过 `sys.path.insert` 拉入） | 天气缓存 + 直接 import 根目录脚本 | 1 | `claude_branch/scripts/c01_repair_20260905/step2_weather_reextraction.py` |
| `STST2603_model_review_package/data`（**反向写出**，不是读取） | claude_branch 单向写数据到根目录审阅包 | 1 | `claude_branch/scripts/model_review_package_20260907/materialize_final_data.py` |
| 整个根目录（`root=Path('D:/Pyprogramme/STST2603')`） | 这是专门的源码清点工具，扫描根目录是设计意图本身，非误用 | 1 | `claude_branch/paper_revision_work_v2/R05/src/source_inventory.py` |
| 同 `rebuild_v3_full_stage` + shapefile 路径的重复副本 | R02 相关的 v3_validation_pipeline 派生副本 | 2 | `claude_branch/paper_revision_work_v2/R02/code_changes/v3_validation_pipeline.py` |

未发现有意义的 `..\..` 相对路径逃逸。**结论：外部依赖高度集中在一个 v3 数据集 + 两个 shapefile，其余是零星一次性文件和一个反向写出目标。**

## 二、反向引用列表

根目录老代码（排除 claude_branch/.venv/build/dist/__pycache__）中搜索 `claude_branch`，**仅 2 处**：

1. `claude_branchresultsc09_final_cleanup_20260905rawrun_all_c09.log`（问题文件本身，见下）
2. `rebuild_v3_full_stage/README.md`：只是一句声明"该目录独立于 claude_branch"，不构成真实依赖

根目录 `scripts/`（附录/docx 编辑脚本）和 `STST2603_model_review_package/` 与 claude_branch 同名文件夹**内容无重复**，但 `STST2603_model_review_package/data` 实际被 claude_branch 的 `materialize_final_data.py` 单向写入——这条依赖在该 package 自己的 README/PROVENANCE 里**没有留痕**，值得注意。

**关于那个诡异文件名的成因**：内容是一条失败的调用记录——`D:\Pyprogramme\STST2603\` 后面所有路径分隔符（`claude_branch\scripts\c09_final_cleanup_20260905\run_all_c09.py`）全部丢失，导致 `open()`/重定向把整段拼接结果当成了根目录下的一个平铺文件名。核对了真实脚本 `claude_branch/scripts/c09_final_cleanup_20260905/run_all_c09.py` 本身用的是规范 `pathlib.Path`，代码没问题；`LOG.md` 也记录该脚本当天被重新调用并成功产出了正常结果文件。**结论：这是一次手动拼接命令时漏加分隔符导致的失败调用留下的孤儿文件，后续已被正确重跑覆盖，只是这个空壳日志从未清理**，可以放心删除（本次审计未做任何删除操作）。

## 三、库依赖列表

Live 代码（288 个文件）实际用到的第三方库：`numpy`、`pandas`、`scipy`、`matplotlib`、`PIL`(pillow)、`statsmodels`、`patsy`、`sklearn`、`geopandas`、`shapely`、`openpyxl`、`pyarrow`、`joblib`、`tqdm`、`SALib`、`dcor`、`distfit`、`openmeteo_requests`、`requests_cache`、`retry_requests` — **全部已被根目录 `requirements.txt` 覆盖**。

唯一缺口：**`diptest`**（仅 `claude_branch/scripts/test1/test1_full_pipeline.py` 一处用到，做 Hartigan's dip test），根目录 requirements.txt 里没有。

**建议**：`scripts/`、`code/`、`R02`、`R05`、`X02_storm_specialization`、`R02_isolation_audit`、`docs` 这部分可以**直接复用 STST2603 根目录的 `.venv`**，补装一个 `pip install diptest` 即可跑通全部 live 代码，不需要单独建环境。真正已经独立的是 `R03`、`R04`——它们各自带了完整 vendored 运行时（R03: numpy/pandas/scipy/statsmodels 等；R04: matplotlib/scikit-learn 等），本来就不依赖根环境，不用处理。
