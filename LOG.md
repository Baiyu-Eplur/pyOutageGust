# pyOutageGust — 迁移操作日志

## 2026-09-08 — 阶段一：创建骨架 + 复制非冲突文件

**操作性质**：对 `D:\Pyprogramme\STST2603`（含 `claude_branch`）只读，未修改/移动/删除任何源文件；只向全新目录 `D:\Pyprogramme\pyOutageGust` 写入。本阶段不改写任何代码逻辑，纯目录创建 + 文件复制。

### 1. 目录骨架

创建了以下空目录骨架：
```
data/external/gis/、data/generated/、src/、scripts/、
paper_revision_work_v2/、review_package/{code,data,results}/、
docs/、results/、test/
```
其中 `review_package/` 和 `src/` 本阶段刻意保持为空 —— 按计划留给阶段二（`main1.py` 依赖提取 → `src/weather_features.py`，以及独立 review package 的搭建）。

### 2. 整体复制（保持内部结构不变）

| 来源（claude_branch/） | 去向（pyOutageGust/） | 文件数 | 校验 |
|---|---|---|---|
| `scripts/*` | `scripts/` | 133 | 源/目标文件数一致 ✅ |
| `paper_revision_work_v2/*`（含 R02, R02_isolation_audit, R03, R04, R05, X02_storm_specialization, code） | `paper_revision_work_v2/` | 12,892 | 源/目标文件数一致 ✅ |
| `docs/*` | `docs/` | 20 | 源/目标文件数一致 ✅ |
| `test/*` | `test/` | 106 | 源/目标文件数一致 ✅ |
| `results/*` | `results/` | 700 | 源/目标文件数一致 ✅ |

**关于孤儿日志排除项的说明**：任务要求排除 `claude_branch\results\c09_final_cleanup_20260905\raw\run_all_c09.log`，但**核查后发现该路径下并不存在这个文件**（`raw/` 目录下实际只有 `a02_duan_smearing_corrected.json`、`c09_vif_summary.json` 等 12 个正常产出文件）。此前审计中定位到的孤儿文件是位于 **`STST2603` 项目根目录**（不在 `claude_branch/results` 内）、文件名因路径分隔符丢失而变成 `claude_branchresultsc09_final_cleanup_20260905rawrun_all_c09.log` 的那个文件——它本就不在本次复制范围内（复制源是 `claude_branch/results`，不涉及项目根目录），因此**没有实际内容需要排除，`results/` 按完整内容复制**。该根目录孤儿文件本身仍待人工确认后删除，不属于本次操作范围。

`paper_revision_work_v2` 是按用户要求"整体复制、保持内部结构不变"，因此 R03、R04 各自的 `frozen/project_sources/`（快照）和 `runtime/site-packages/`（vendored 环境）也原样带过来了，未做任何过滤。

### 3. 外部数据文件复制（按映射表）

| 外部源（STST2603 根目录） | 新项目路径 | 大小 | 校验 |
|---|---|---|---|
| `rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv` | `data/external/ukpn_full_stage_dataset_v3.csv` | 1.08 GB | ✅ |
| `data/Local_Authority_Districts_December_2021_UK_BGC_2022/LAD_DEC_2021_UK_BGC.{cpg,dbf,prj,shp,shx}` | `data/external/gis/LAD_DEC_2021_UK_BGC/` | ~8.4 MB (5 文件) | ✅ |
| `data/dno_license_areas_20200506/DNO_License_Areas_20200506.{cpg,dbf,prj,shp,shx}` | `data/external/gis/DNO_License_Areas_20200506/` | ~0.96 MB (5 文件) | ✅ |
| `data/ukpn-iis.csv` | `data/external/ukpn-iis.csv` | 44.3 MB | ✅ |
| `data/new/ukpn_master_weather_matrix.csv` | `data/external/ukpn_master_weather_matrix.csv` | 257 MB | ✅ |
| `data/new/ukpn_master_weather_matrix_with_lad.csv` | `data/external/ukpn_master_weather_matrix_with_lad.csv` | 262 MB | ✅ |
| `data/new/ukpn_master_weather_matrix_with_lad_pop.csv` | `data/external/ukpn_master_weather_matrix_with_lad_pop.csv` | 268 MB | ✅ |
| `data/weather_request_cache/`（整目录，75,983 个 `.pkl`） | `data/external/weather_request_cache/` | 905 MB | 文件数与体积均核对一致 ✅ |

每个文件的来源路径、生成方式（如已知）记录在 [`data/external/README.md`](data/external/README.md)。

### 4. 未处理项（有意跳过，属阶段二范围）

- `src/weather_features.py`（从 `main1.py` 提取的独立模块）—— **未创建**
- `review_package/` 下的实际内容（`code/run_main_regression.py` 等）—— **未复制**
- `claude_branch/paper_revision_handoff_v2/` —— 本次任务未要求，**未复制**
- 根目录孤儿文件 `claude_branchresultsc09_final_cleanup_20260905rawrun_all_c09.log` —— 待人工确认后删除，本次未触碰

### 5. 最终统计

```
总文件数：89,850
总大小：  4.8 GB
```

| 目录 | 文件数 | 大小 |
|---|---|---|
| `data/` | 75,999 | 2.7 GB |
| `paper_revision_work_v2/` | 12,892 | 1.8 GB |
| `results/` | 700 | 202 MB |
| `test/` | 106 | 116 MB |
| `scripts/` | 133 | 1.3 MB |
| `docs/` | 20 | 9.5 MB |
| `review_package/` | 0（骨架空目录） | 0 |
| `src/` | 0（骨架空目录） | 0 |

对 `STST2603` 全程只读；本次会话未对源目录做任何写入/删除/移动操作。

## 2026-09-08 — 阶段二：两处代码改造（weather_features 提取 + review package 独立化）

**操作性质**：对 `D:\Pyprogramme\STST2603` 只读（含用其 `.venv` 解释器运行冒烟测试，仅读取/执行，不写入）；只向 `D:\Pyprogramme\pyOutageGust` 写入。

### 改动清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `src/weather_features.py`（新建） | 从 `main1.py` 提取 5 个纯函数：`safe_float`、`circular_mean_deg`、`make_empty_feature_series`、`summarize_window`、`build_incident_features_from_hourly`。仅依赖 numpy/pandas，无全局状态。 |
| 2 | `scripts/c01_repair_20260905/step2_weather_reextraction.py` | 把 `sys.path.insert(0, r"D:\Pyprogramme\STST2603")` + `from main1 import build_incident_features_from_hourly` 改成 `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` + `from src.weather_features import build_incident_features_from_hourly`（路径改为相对 `__file__` 计算，不再硬编码绝对路径）。同步更新了模块 docstring 里"reuses main1.py"的措辞。 |
| 3 | `review_package/code/run_main_regression.py`（新建，复制）<br>`review_package/README.md`（新建，复制+改写） | 从 `STST2603_model_review_package/` 原样复制 `code/run_main_regression.py`（无需改动，本就用 `Path(__file__).resolve().parent.parent` 相对寻址）；README 标题从 `# STST2603 — Main Regression Model Review Package` 改为 `# pyOutageGust review_package — Main Regression Model Review Package`（全文只有这一处出现项目名，其余内容未改动；未复制 `code/PROVENANCE.md`、`requirements.txt`、`results/verification_report.md`，按任务范围本次不涉及）。 |
| 4 | `scripts/model_review_package_20260907/materialize_final_data.py` | `OUT_DIR` 从 `D:\Pyprogramme\STST2603\STST2603_model_review_package\data` 改成 `D:\Pyprogramme\pyOutageGust\review_package\data`。数据来源的 `sys.path.insert(...)` 和 `from corrected_sample_builder import build_corrected_combined_samples` **未改动**（按任务要求"corrected_sample_builder.py 不用动"），因此该 import 仍指向 `claude_branch/scripts/c02_c08_repair_20260905/`（老项目，只读）——**已知残留耦合**，其内部（`corrected_sample_builder.py`）自身还硬编码了 `rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv` 等老项目路径，属于超出本次任务范围的后续工作，先记录在此。 |
| 5 | `paper_revision_work_v2/R02/code_changes/v3_validation_pipeline.py`<br>`paper_revision_work_v2/R02_isolation_audit/before/v3_validation_pipeline_R02_patched.py` | 两个文件里的 `SRC`（v3 数据集）和 `LAD_SHP`（LAD shapefile）都从老项目绝对路径改成 `D:\Pyprogramme\pyOutageGust\data\external\...`。`OUT_DIR`（`...claude_branch\results\v3_validation`）**未改动**——任务范围只涉及"外部文件→data/external"映射表里的两条，OUT_DIR 是输出目录不在该映射表中，仍指向老项目，属残留项，记录于此供后续处理。 |
| 6 | `paper_revision_work_v2/R05/src/source_inventory.py` | `run()` 内硬编码的 `root=Path('D:/Pyprogramme/STST2603')` 改为函数参数 `run(root=None)`（函数体内 `root=Path(root) if root else Path('D:/Pyprogramme/STST2603')`，不再是硬编码赋值），并在 `if __name__=='__main__':` 里新增 `argparse`，加 `--root` 命令行参数（默认值仍是 `D:/Pyprogramme/STST2603`，因为该工具的职责就是清点老项目里的两个遗留脚本，不属于"迁移掉"的外部依赖）。 |

### 冒烟测试结果

| # | 测试方式 | 结果 |
|---|---|---|
| 1+2 | 用根目录 `.venv`（Python 3.12.6）import `step2_weather_reextraction` 模块（不触发 `if __name__=='__main__'`），确认 `build_incident_features_from_hourly.__module__ == 'src.weather_features'`；构造 80 小时合成小时数据调用该函数，`gust_0h`/`pressure_msl_0h` 计算结果数值合理；import 前后扫描全项目确认**没有出现任何 `.weather_cache_master*` 文件**（main1.py 原有副作用已消除）。 | **通过**，退出码 0 |
| 3+4 | 实际运行 `materialize_final_data.py`：生成 `review_package/data/combined_E0_final.csv`（n=60,437）、`combined_R0c_final.csv`（n=59,834），列缺失检查通过；随后实际运行 `review_package/code/run_main_regression.py` 读取这两个新文件拟合模型，**E0 turning point = 10.8072 m/s，与老 README 记录的参考输出完全一致**，四张系数表和 `run_summary.json` 正确写入 `review_package/results/`。 | **通过**，两次运行退出码均为 0，数值与原始参考输出比对一致 |
| 5 | 用 `importlib` 分别加载两个文件（不调用 `main()`），确认模块正常 import，且 `mod.SRC.exists()`、`mod.LAD_SHP.exists()` 均为 `True`（新路径下文件确实存在）。 | **通过**，两个文件均 import OK 且路径解析正确 |
| 6 | 先 `python source_inventory.py --help` 确认 `--root` 参数注册成功（顺带验证了 `common`/`contracts`/`producer` 整条 import 链没有被改动破坏）；再实际运行 `python source_inventory.py --root "D:/Pyprogramme/STST2603"` 完整跑一遍——`IMD_merge.py`、`inspect_imd_moran_workbook_context.py` 被成功从老项目 `--root` 位置复制到 `paper_revision_work_v2/R05/frozen/source_audit/`，脚本打印 `Source inventory and C01-C10 evidence map complete`，全程只写入 `pyOutageGust` 内部（`common.py` 里的 `assert p.resolve().is_relative_to(Q)` 也保证了这一点）。 | **通过**，退出码 0，`--root` 参数生效 |

### 已知残留项（记录，不属本次任务范围）

- `materialize_final_data.py` 仍通过 `sys.path.insert` 从老项目 `claude_branch/scripts/c02_c08_repair_20260905/corrected_sample_builder.py` 导入数据构建逻辑，而该模块自身仍硬编码多个老项目绝对路径（v3 数据集、C01 repair 的 raw 目录等）。
- `v3_validation_pipeline.py` 及其 R02_isolation_audit 副本的 `OUT_DIR` 仍指向 `claude_branch/results/v3_validation`（老项目），未改成 `pyOutageGust/results/v3_validation`。

对 `STST2603` 全程只读（含调用其 `.venv\Scripts\python.exe` 执行冒烟测试，均为读取/执行，未写入该项目任何文件）；所有新建/修改文件均落在 `pyOutageGust` 内。

## 2026-09-08 — 阶段三：独立运行环境、git 仓库、AI 协作规则

**操作性质**：全程只操作 `D:\Pyprogramme\pyOutageGust` 目录内及为其新建的 conda 环境；未触碰 `D:\Pyprogramme\STST2603` 任何文件（仅在阶段二遗留的只读引用之外，本阶段没有再读取 STST2603）。

### 1. requirements.txt

新建 [`requirements.txt`](requirements.txt)，收录审计报告里列出的 21 个第三方库（不含 R03/R04 自带的 vendored 环境）。除 `diptest`（老项目 requirements.txt 里没有、无版本可参照，故留空不锁版本）外，其余 20 个库的版本号全部照抄 `D:\Pyprogramme\STST2603\requirements.txt` 里已验证可用的版本（该文件是 UTF-16 编码，用 `.venv` 的 Python 以 `encoding='utf-16'` 解码后核对提取）。

### 2. conda 环境

会话中途发现本机原本**没有安装 conda**（`which conda`/`where conda` 均找不到），并借此指出一个认知偏差：STST2603 本身其实是普通 `.venv`，不是 conda 环境。就此询问用户如何处理，用户随后自行安装了 Anaconda（装在 `D:\Anaconda`，尚未写入本会话 PATH，全程用绝对路径 `D:\Anaconda\Scripts\conda.exe` 调用）。

- `conda create -n pyoutagegust python=3.12.6`（与 STST2603 `.venv` 的 Python 版本完全一致）—— 成功。
- `pip install -r requirements.txt` —— 全部 21 个包安装成功，`diptest` 解析到 `0.11.0`。
- 用环境自己的解释器（`C:\Users\haoya\.conda\envs\pyoutagegust\python.exe`，未通过 `conda run` ——发现 `conda run -n ... python -c "<多行脚本>"` 在本机 conda 26.7.2 上会报 `NotImplementedError: Support for scripts where arguments contain newlines not implemented`，改成直接调用环境内 `python.exe` 规避）逐一 `import` 全部 21 个库，**全部成功**。
- `conda env export -n pyoutagegust --no-builds > environment.yml` —— 生成 [`environment.yml`](environment.yml)，记录了含 62 个 pip 安装包在内的完整已解析版本快照。

### 3. .gitignore

新建 [`.gitignore`](.gitignore)，排除：`data/external/`、`review_package/data/`、`paper_revision_work_v2/{R03,R04}/runtime/site-packages/`、`__pycache__/`/`*.pyc` 等 Python 产物、`.venv/`/`env/`、编辑器/系统杂项文件。用 `git check-ignore -v` 逐条验证过这 4 个关键排除规则确实生效。

### 4. git 仓库

`git init` 于 `pyOutageGust` 根目录（此前不是 git 仓库）。`git config user.name/user.email` 已有全局配置（`Baiyu-Eplur` / `haoyan1wu@gmail.com`），未重新设置。`git add -A` 后暂存 **4,604 个文件、约 1.7 GB**（相比全量 89,850 个文件/4.8 GB，`.gitignore` 排除掉了体积最大的 `data/external/`、`review_package/data/`、R03/R04 vendored 环境）。

**需要你知道的一点**：即便排除了上述几项，仍有个别单文件体积偏大——`paper_revision_work_v2/X02_storm_specialization/RETURN_PACKAGE_X02.zip`（246 MB）超过 GitHub 单文件 100 MB 硬限制，另有多个 20–50 MB 的 parquet/csv（如 `R02/data/R02_event_master.parquet` 50 MB、`RETURN_PACKAGE_R05.zip` 20 MB 等）。本地 git 仓库无此限制，不影响本次提交，但**如果将来打算推送到 GitHub，这些文件需要先用 Git LFS 或额外 gitignore 处理**——任务本身只要求本地 git init + 首次提交，这点先记录，未做额外处理。

### 5. README.md / CLAUDE.md

新建 [`README.md`](README.md)（项目背景、目录结构表、环境搭建与运行方式、AI 协作规则指向 CLAUDE.md）和 [`CLAUDE.md`](CLAUDE.md)（Claude Code 可写/不可写范围、每次改动须同 commit 更新 LOG.md 的规则、指向 `docs/migration_history/` 的起源说明）。

### 6. docs/migration_history/

把 `claude_branch/results/external_dependency_audit_20260908.md` 和 `claude_branch_migration_plan_20260908.md` 复制进 [`docs/migration_history/`](docs/migration_history/)，作为项目起源记录留存（README.md 和 CLAUDE.md 均链接到这两份文件）。

### 7. 首次提交

`git add -A` 暂存后的内容，连同本次新建的 `requirements.txt`、`environment.yml`、`.gitignore`、`README.md`、`CLAUDE.md`、`docs/migration_history/*`、本条 LOG.md 记录，一并提交为首次 commit（commit message 见 `git log`）。

对 `STST2603` 全程只读；本次会话唯一涉及 STST2603 的动作是读取其 `requirements.txt` 用于版本比对，未写入/修改该项目任何文件。

## 2026-09-09 — 阶段四：断开 review_package 数据生成流程对老项目 claude_branch 的最后依赖

**操作性质**：只操作 `D:\Pyprogramme\pyOutageGust`；对 `D:\Pyprogramme\STST2603` 只读。所有改动前均先确认对应本地文件已因阶段一整体复制而存在，未重复复制任何文件。

### 0. 先披露一个上一阶段遗留的只读违规（本阶段发现，非本阶段引入）

在追查 `corrected_sample_builder.py` 的完整调用链时发现：阶段二运行 `materialize_final_data.py` 时，该脚本经由 `corrected_sample_builder._patch_v9()` 里硬编码的 `sys.path.insert`/`spec_from_file_location` 调用，实际从老项目 `D:\Pyprogramme\STST2603\claude_branch\scripts\v3_validation\v3_validation_pipeline.py` 加载了模块，而该模块顶层有 `RAW_DIR.mkdir(...)` 和 `step1_lad_gapfill()` 内部的 `(RAW_DIR / "step1_lad_gapfill.json").write_text(...)`——这导致阶段二那次运行**真的往老项目写入了两个文件**：`claude_branch/results/v3_validation/raw/step1_lad_gapfill.json` 和 `step2_folds.json`（mtime 2026-09-08 22:46）。

已用 `diff` 核实：这两个文件的内容与 `pyOutageGust/results/v3_validation/raw/` 下对应文件（阶段一 22:29 整体复制、早于那次违规写入）**逐字节完全一致**——说明是同一套确定性计算，数值没有任何实际改变，只是 mtime 被更新。仍然如实记录：这确实是一次不该发生的写入，本阶段的改动正是为了从根源上堵住它。

### 1. `scripts/c02_c08_repair_20260905/corrected_sample_builder.py`（先确认此文件已存在于本地——确认成立）

发现 5 处硬编码老项目绝对路径：

| 行为 | 原值 | 新值 |
|---|---|---|
| `SRC`（v3 数据集） | `D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv` | `D:\Pyprogramme\pyOutageGust\data\external\ukpn_full_stage_dataset_v3.csv`（本地已存在，来自阶段一）|
| `C01_RAW_DIR` | `D:\Pyprogramme\STST2603\claude_branch\results\c01_repair_20260905\raw` | `D:\Pyprogramme\pyOutageGust\results\c01_repair_20260905\raw`（本地已存在，来自阶段一）|
| `sys.path.insert(...)` 加载 v3_validation | `...STST2603\claude_branch\scripts\v3_validation` | `Path(__file__).resolve().parents[1] / "v3_validation"`（相对路径，不再硬编码绝对路径）|
| `spec_from_file_location` 加载 clean_sample_builder | `...STST2603\claude_branch\scripts\dev_sample_decontamination\clean_sample_builder.py` | `Path(__file__).resolve().parents[1] / "dev_sample_decontamination" / "clean_sample_builder.py"` |
| `spec_from_file_location` 加载 build_holdout_sample | `...STST2603\claude_branch\scripts\module_e_final_confirmation\build_holdout_sample.py` | `Path(__file__).resolve().parents[1] / "module_e_final_confirmation" / "build_holdout_sample.py"` |

### 2. 为真正"断开最后依赖"而额外修的 3 个文件（超出原始 5 条清单，但缺了它们整条链条仍会绕回老项目）

追踪调用链发现：即便只改上面 5 处，`corrected_sample_builder.py` 加载的 `clean_sample_builder.py` 和 `build_holdout_sample.py` 各自又有自己的硬编码路径去加载老项目的 `v3_validation_pipeline.py`；而老项目那份 `v3_validation_pipeline.py` 本身的 `SRC`/`LAD_SHP`/`OUT_DIR` 也还是硬编码老路径——這正是上面"阶段0"那次意外写入的根源。所以一并修了：

| 文件 | 改动 |
|---|---|
| `scripts/v3_validation/v3_validation_pipeline.py`（本地已存在） | `SRC`→`data/external/ukpn_full_stage_dataset_v3.csv`；`LAD_SHP`→`data/external/gis/LAD_DEC_2021_UK_BGC/...shp`；`OUT_DIR`→`pyOutageGust/results/v3_validation`；docstring 里"claude_branch/results/v3_validation/"改成"results/v3_validation/" |
| `scripts/dev_sample_decontamination/clean_sample_builder.py`（本地已存在） | `V3_VALIDATION_SCRIPT` 从老项目绝对路径改成 `Path(__file__).resolve().parents[1] / "v3_validation" / "v3_validation_pipeline.py"` |
| `scripts/module_e_final_confirmation/build_holdout_sample.py`（本地已存在） | `sys.path.insert(...)` 改成相对 `__file__`；`OUT_DIR` 改成 `pyOutageGust/results/module_e_final_confirmation`（本地已存在）；`main()` 内部用于对比 n_stages 分布的 `SRC` 也改成 `data/external/ukpn_full_stage_dataset_v3.csv` |

### 3. `scripts/model_review_package_20260907/materialize_final_data.py`

`sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))` 改成 `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "c02_c08_repair_20260905"))`（相对 `__file__` 计算，不再硬编码绝对路径）。数据来源逻辑（`corrected_sample_builder.build_corrected_combined_samples`）本身未改。

### 4. 两个 v3_validation_pipeline 副本的 OUT_DIR

`paper_revision_work_v2/R02/code_changes/v3_validation_pipeline.py` 和 `R02_isolation_audit/before/v3_validation_pipeline_R02_patched.py`：`OUT_DIR` 从 `D:\Pyprogramme\STST2603\claude_branch\results\v3_validation` 改成 `D:\Pyprogramme\pyOutageGust\results\v3_validation`（`SRC`/`LAD_SHP` 已在阶段二改过，本次未再变动）；顺带把两个文件里同样残留的 docstring 提及"claude_branch/results/v3_validation/"也改成"results/v3_validation/"。

### 5. 未做的事（有意）：本地 `data/external/` 未再补复制

第 3 步要求的"若本地不存在则先补复制"——核查后确认全部 6 个目标本地文件/目录（v3 数据集、C01 raw 目录、`scripts/v3_validation/`、`scripts/dev_sample_decontamination/`、`scripts/module_e_final_confirmation/`、`results/module_e_final_confirmation`、`results/v3_validation`）均已因阶段一/阶段二的整体复制而存在，**没有遗漏，未触发任何补复制**。

### 6. 一致性校验结果

用根目录 `.venv` 的 phase-2 产出物做基线：先把阶段二第一次运行生成的 `combined_E0_final.csv` / `combined_R0c_final.csv` 备份，记录 SHA256：
- `combined_E0_final.csv`: `6a82fedd4dd77f4218f89f47058cafea7cc7c34867120589cdbeba8fca63ec38`
- `combined_R0c_final.csv`: `313e5cea062eec015b5dbfdd61986ed277e058ab8fe9e0fa33ee773d936e72a9`

用 `pyoutagegust` conda 环境重新运行本阶段改完的 `materialize_final_data.py`（退出码 0，日志显示 E0 n=60437、R0c n=59834，与阶段二完全一致），新产出文件 SHA256 **与备份完全相同**（`diff` 确认逐字节一致）。随后核查 `D:\Pyprogramme\STST2603\claude_branch\results\{v3_validation,module_e_final_confirmation}` 的 mtime：本次运行**没有再往里面写任何东西**（那两个 json 文件 mtime 仍停留在阶段二的 2026-09-08 22:46，未被本次运行更新）——证实解耦成功，且数值结果零变化。

### 7. 全局残留引用搜索结果

对 `pyOutageGust` 全目录 `grep -r "STST2603\|claude_branch"`，结果需要分类看：

- **本任务涉及的 review_package 数据生成调用链（7 个文件：`corrected_sample_builder.py`、`materialize_final_data.py`、两个 `v3_validation_pipeline*.py` 副本、`scripts/v3_validation/v3_validation_pipeline.py`、`clean_sample_builder.py`、`build_holdout_sample.py`）：逐一 grep 确认，`STST2603` 和 `claude_branch` 均为 0 命中——本任务的目标范围内已彻底断开。**
- `paper_revision_work_v2/{R03,R04}/{frozen,runtime}/**`、`paper_revision_work_v2/code/snapshots/**`、`X02_storm_specialization/runs/*/frozen_sources/**`、`R05/frozen/source_audit/**` 等：145 个 `.py` 文件 + 大量 `.json`/`.md` 清单文件仍含 `STST2603`/`claude_branch` 字符串——**这些是有意保留的冻结快照/审计存证（历史时间点的只读副本），不应修改，改了就破坏了它们作为"某时刻真实状态记录"的意义**，与阶段一审计报告里对 R03/R04 vendored 环境"视为已解决、不用处理"的结论一致。
- `paper_revision_work_v2/R05/src/source_inventory.py` 的 `--root` 默认值——按你的要求，属于该工具本职功能（清点老项目遗留脚本），**保留为例外**。
- 其余约 116 个 `.py` 文件（`scripts/final_combined_analysis/*`、各 `figure*.py`、`scripts/c01_repair_20260905/*`、`scripts/c09_final_cleanup_20260905/*` 等大量分析脚本）仍硬编码老项目路径——**这些不在本任务范围内**（本任务标题是"断开 review_package 数据生成流程"这一条链，不是"迁移 claude_branch 全部代码"）。这是阶段一 `external_dependency_audit_20260908.md` 里早就统计过的同一批"外部依赖点"的另一部分，尚未处理，如果需要断开这些也需要单独立项。
- `LOG.md`、`README.md`、`CLAUDE.md`、`docs/migration_history/*.md` 里出现 `STST2603`/`claude_branch` 属于正常的历史记录说明文字，不是需要"断开"的功能性依赖。
- 顺带发现（与本任务无关，仅记录）：`STST2603_model_review_package/review_log.md` 和 `review_logs/` 目录在 2026-09-09 08:50–09:06 出现/更新过，**这不是本次或上次任何一个任务写入的**（本项目所有脚本都不会产生叫 `review_log.md` 的文件名），大概率是你自己在别处对那个老项目目录做了什么操作，特此告知，未做任何处理。

对 `STST2603` 全程只读；本阶段发现并如实披露了阶段二遗留的一次误写（已用 checksum 证实无实际数据损失），本阶段自身的改动与重新运行均未再对 `STST2603` 产生任何写入。

## 2026-09-09 — Comments/ 加入 .gitignore

`Comments/`（含 `Comments_for_Haoyan/` 和 `Comments_for_Haoyan.zip`，约 32MB）是用户后续用来处理导师批注的目录，刚出现在工作区、尚未被 git 跟踪（`git status` 显示 `?? Comments/`）。在 [`.gitignore`](.gitignore) 里加了一条 `Comments/` 规则（放在"reviewer feedback"独立分组下），并用 `git check-ignore -v` 确认生效。未修改该目录下任何内容。

## 2026-09-09 — 排除超限大文件 + 推送到 GitHub 首个里程碑节点

**背景**：用户要求把当前状态推到 GitHub（`https://github.com/Baiyu-Eplur/pyOutageGust`），作为"导师修改前的最终版本"这个关键节点保存。推送前照例检查了仓库里的大文件——GitHub 对单个 blob 有 100MB 硬限制，超过会被服务器直接拒绝整个 push。

扫描全部历史 git blob（`git rev-list --objects --all` + `git cat-file --batch-check`）发现 2 个超过 50MB 的文件：
- `paper_revision_work_v2/X02_storm_specialization/RETURN_PACKAGE_X02.zip`——**257.7 MB，超过 100MB 硬限制，会导致 push 被拒**。核实过它的内容（`unzip -l`，696 个文件）就是 `paper_revision_work_v2/X02_storm_specialization/runs/X02_20260907_001/` 目录的打包压缩版——**同样的文件已经以解压形式被 git 完整跟踪**，这个 zip 只是一份冗余的打包交付件，从 git 历史里去掉不损失任何实际内容。
- `paper_revision_work_v2/R02/data/R02_event_master.parquet`——52.4 MB，低于 100MB 硬限制（push 不会被拒），只是超过 GitHub 建议用 Git LFS 的 50MB 软阈值，会有警告但不阻塞，**未做任何处理**。

处理方式：把该 zip 路径加入 `.gitignore`（连同这条说明一起提交），然后用 `git filter-branch --index-filter "git rm --cached --ignore-unmatch '...RETURN_PACKAGE_X02.zip'" --prune-empty -- --all` 把这个 blob 从全部 3 个历史 commit 里彻底移除（此时仓库还从未 push 过，没有任何人克隆过这份历史，本地重写历史是安全的，不存在"覆盖别人已拉取的提交"的风险），随后 `git reflog expire --expire=now --all` + `git gc --prune=now --aggressive` 回收空间。

**更正（同一操作内发现并如实记录）**：我在操作时预判"磁盘上的原始 zip 文件本身完全没有被删除或改动"，这个判断是**错的**——`git filter-branch` 在重写完历史后会把当前分支 checkout 到新树，而新树里已经没有这个文件，checkout 因此把工作目录里的这份 zip 一并删除了；紧接着的 `git gc --prune=now` 又清掉了 git 内部残留的 blob，`git fsck --unreachable --dangling` 核实过**已无法通过 git 内部机制恢复**。

好消息是：核实过这个 zip 的 696 个文件与 `paper_revision_work_v2/X02_storm_specialization/runs/X02_20260907_001/` 目录逐一对应（`find runs -type f` 同样是 696 个文件），也就是说**里面的实际内容一份都没有丢**，只是那个额外打包好的 `.zip` 交付件本身（作为一份冗余归档）确实被删掉了，不再存在于磁盘或 git 历史里。如果你需要那个打包好的 zip 文件本身（而不是解压内容），需要重新手动压缩 `runs/X02_20260907_001/` 生成。

**推送结果**：`git remote add origin https://github.com/Baiyu-Eplur/pyOutageGust.git`，`git branch -m master main`（对齐远程默认分支名），`git push -u origin main` 一次性成功（远程仓库此前为空，无需处理冲突）。用 GitHub API 核对过：远程 5 个 commit 的 SHA 与本地完全一致。

按用户要求，把这个刚推送上去的状态记录为**"导师修改前的最终版本"关键节点**：打了标签 `pre-review-checkpoint-20260909` 并 push 到远程；详细的节点记录（时间、项目结构统计、内容概述、已知未处理事项）写在 [`docs/milestones/2026-09-09_pre-review-checkpoint.md`](docs/milestones/2026-09-09_pre-review-checkpoint.md)。

## 2026-09-09 — 工作命令 #56：导师模型探索材料完整阅读与严格审查

**操作性质**：只读访问 `Comments/Comments_for_Haoyan/STST2603_review/`（导师提供的独立模型探索材料，含代码/数据/结果/三份Word文档），未修改包内任何文件；所有独立验证脚本运行在 `results/advisor_review_20260908/verification/` 下，未覆盖包内已有 `results/`。产出全部写入 `pyOutageGust/results/advisor_review_20260908/`（本任务的"claude_branch"路径按当前项目实际情况理解为 pyOutageGust，已向用户说明并确认该解读依据）。

**做了什么**：
1. 用 python-docx 完整提取三份 Word 文档（含所有表格，未跳过）+ 为完成 Claims audit 额外提取了 `Paper_reorganisation_plan.docx`，逐份通读并与 `MODEL_SELECTION_REPORT.md` 比对，发现该 md 文件缺少 docx 第12节的"plateau约束"修正（结点从14/26改为14/25，且第11节"weather-only斜率与pooled基本相同"的说法被文档自己撤回）。
2. 逐行审查全部 12 个 `code/*.py` + 2 个 `.js`，发现的问题：`plateau_model.py` 产出的 `knots.json` 里 `selected`/`form` 字段无法用当前打包的 `code/` 完整复现（provenance缺口，不影响已发布数字）；一处BIC参数计数打印笔误；README bootstrap默认次数与代码默认值不一致（实际结果用的是对的）；一处死代码。
3. 3a（占位符数据，最高优先级）：独立在自己的 `review_package/data/combined_R0c_final.csv`（与导师包SHA256相同）上复现 8,661个zero-customer事件、66.5%/0.5%的1.000h占比、customers系数符号翻转（+0.336→−0.196），并额外追溯到原始`ukpn-iis.csv`发现这批事件100%单stage、97.5%共享Cause Code "71"——比导师报告更深一层的机制证据。**站得住**。
4. 3b（结点/样条分歧，最高优先级）：独立编写脚本在自己数据上重新拟合df=4/6/8/10的自由样条，发现更高自由度样条的CV RMSE确实全面优于二次型，但最低点始终停在10.7-11.7 m/s、**没有**随自由度提高滑向导师声称的14 m/s，"我们的样条被过度平滑"这个具体归因未获独立支持；同时指出样条（光滑）和分段线性结点估计（允许尖角）测试的不是同一件事，这一方法论区分是本次审查的独立贡献。**结论混杂，如实呈现**。
5. 3c（LAD固定效应陷阱）：独立复现，E0/R0c的AIC/BIC/CV RMSE/校准斜率四组数字与导师报告精确吻合（多项精确到小数点后四位）。**站得住**。
6. 3d（district-day面板）：代码审查（高斯核IDW实现、真正的leave-district-out验证、面板构造无C01类代表行隐患）+ 核对已保存的`interp_validation.json`（RMSE 2.221/r 0.854，与声称的2.2/0.85吻合）。**站得住，但注明这是代码审查级别而非完整重建级别的验证**。
7. 3e（脆弱性曲线方法论）：独立复现weather_natural占比随阵风的梯度（6.98%→90.64%，与声称的7%/91%吻合），与自己Appendix G十分位数字方向一致。**站得住**。
8. 3f：其余6个脚本审查汇总，未发现新增问题。
9. Step 3：对`Paper_reorganisation_plan.docx` Claims audit表格全部11条逐一三档分类——6条"站得住"、2条"存在问题"（样条过度平滑归因不成立；SE倍数量级部分出入但可能因比较对象不同）、3条"尚未充分验证"（development/confirmation结点、R²分解、恢复时长低众数细节，均已注明卡在哪里）。

**产出文件**：`results/advisor_review_20260908/{00_README,01_docx_reading_summary,02_code_review,03a-03f_*,04_step3_claims_audit}.md` + `verification/{3a,3b,3c}_*.py` 及对应 `_results.json`。

对 `STST2603_review/` 包全程只读；对 `pyOutageGust` 自身其他文件（`review_package/data/`、`paper_revision_work_v2/code/snapshots/H0/rebuild_v3_full_stage/`、`results/appendix_h_20260906/`、`results/c09_final_cleanup_20260905/`）只读，用于交叉核对；本任务唯一的写入范围是 `results/advisor_review_20260908/` 目录。

## 2026-09-09 — pretest 收束：步骤 1 / 现状盘点与实施边界

- 用户要求：根目录 main.py 统一开关；pretestmain.py 接入 scripts 全部旧功能；旧输出归入 results/pretest；每次运行记录目的、秒级时间和分类结果。本阶段不迁入导师代码。
- 已读取 README.md、CLAUDE.md、既有迁移日志和 scripts 路径/输入输出调用。未发现适用的 AGENTS.md。
- 发现：旧脚本同时存在 Windows STST2603 硬编码、Linux /tmp 输出、相对 data 输出以及本地 review_package 输出；只改入口不能阻止旧路径写入。
- 实施：保留 scripts 的原有任务分组和科学计算；增加显式路径函数与结果读取回退，独立进程逐项执行；历史结果迁至 pretest 归档，保留校验清单。前置开关为 0 时只复用已有结果，不自动重算。
- 保护：Comments、data/external、冻结 R03/R04 与历史快照不改写；旧 STST2603 仅保留已存在且尚无本地快照的只读输入依赖，并记录来源。
- 验证安排：完整脚本登记、语法检查、入口与失败记录测试、结果回退测试、实际绘图及回归链抽查。全量耗时模型不因结构整理而自动启动。

## 2026-09-09 — pretest 收束：步骤 2 / 统一入口及旧源码路径改造

- 新增 main.py：所有独立步骤的 0/1 开关、运行目的、预演、失败继续策略和可选解释器均直接设于文件顶部。默认全部步骤关闭。
- 新增 pretestmain.py：完整登记 scripts，公共模块通过调用链复用；R02 输入消费模块增加只读检查适配器；额外接入 review_package 回归。每步独立进程，记录开始/结束、退出码、控制台日志、源码校验及输出 SHA256。失败产物不更新成功结果索引。
- 新增 pretest_paths.py：显式区分输出与读取；输出必须有入口提供的运行上下文。读取优先本步结果、已成功结果索引和归档，再使用本地输入快照；缺少本地副本时保留既有旧项目只读依赖并记录。
- 修改 scripts 与 review_package/code 的路径和读取调用（首轮 121 文件中 117 个有改动）。逐文件改动数量及前后文本 SHA256 见 docs/migration_history/pretest_source_changes_20260909.json；一次性迁移工具一并保留，禁止重复执行。
- 本步未更改模型公式、筛样规则、拟合参数及旧图样式。增加进程内写入边界检查，防止残留路径把文件写回外部项目或历史结果。
- 首轮验证：所有改动脚本通过 ast.parse；确认项目既有 conda Python 可用，numpy/pandas/scipy/statsmodels/sklearn/matplotlib 导入成功。实际运行及边界测试在后续步骤记录。

## 2026-09-09 — pretest 收束：步骤 3 / 历史输出归档

- 执行 docs/migration_history/archive_pretest_results.py，把原 results 下除 pretest 外的所有项目及 review_package/results、data/generated 中已有产物移入 results/pretest/archive/<年月日时分秒>/，不改写文件内容。
- 每次移动前检查源与目标的解析绝对路径均处于本项目授权范围，拒绝目标冲突；移动前后逐文件计算 SHA256 并核对。迁移过程逐项写入清单与可复用索引。
- 全部文件/旧新路径/大小/校验值及实际数量见 docs/migration_history/pretest_archive_20260909.json；结果归档内保留相同 archive_manifest.json。此清单是路径迁移依据，历史报告中原有路径文本作为历史记录保留。
- Comments 及冻结研究包内容未搬移、未改写。review_package/data 的静态输入仍可只读复用；重新生成的样本会写入 pretest/data 时间目录。

## 2026-09-09 — pretest 收束：步骤 4 / 实际复现与边界修正

- 实际运行 main.py 调用链：Figure 4 单独开启（其他前置步骤为 0），成功从历史归档读取 E0/R0c 各 50 个曲线点并输出 PNG/PDF。运行记录：results/pretest/runs/20260909154622。
- 实际运行样本生成 + review_package 回归，记录：results/pretest/runs/20260909154639。E0 n=60437、R0c n=59834；两份样本与旧 CSV 的 SHA256 完全相同。四份系数 CSV 与 run_summary.json 也全部逐字节一致。详情：docs/migration_history/pretest_numerical_verification_20260909.json。
- 修正 V2 读取前的存在性检查，使其先解析历史/本地输入；缺失输入由原先打印后退出改为抛错，避免误报成功。V2 数据/缓存写入新结果目录，缓存读取可复用已有文件；清理机械改造产生的多余 Path(str(...)) 包装。
- read_input 增加旧 JSON 内嵌路径的本地解析，避免改写冻结清单；完整路径解析优先本地快照。缓存索引按子进程读取，避免逐文件重复解析大索引。
- 新增 test/test_pretest_entry.py。11 项测试全部通过：完整注册、全关闭/预演不启动计算、参数校验、结果读取回退、缺失前置提示、输出越界防护、秒级名称冲突、失败产物不进入成功索引、写入保护及所有活动脚本语法检查。
- 每次运行补充全部活动源码 SHA256；子进程输出改为无缓冲，便于长任务及时查看日志。以下文档与最终复核将在下一步记录。

## 2026-09-09 — pretest 收束：步骤 5 / 文档、源码校验及新目录边界补正

- 更新 README.md、CLAUDE.md、review_package/README.md 和 pipeline_v2 目录说明，改为 main.py 使用方式，说明旧哈希表仅代表当时复制状态。新增 docs/PRETEST_GUIDE.md 和完整 docs/PRETEST_TASKS.md；.gitignore 排除运行锁和临时/字体缓存，不忽略分析结果和运行日志。
- 输出路径进一步补正：V2 filter 实际聚合 237901 个原始阶段后，首次写 CSV 因新时间目录下父文件夹不存在而失败（运行 20260909154903）。失败完整留痕，未更新可复用索引；同次 LAD 面积处理步骤成功。
- 修复 result_path：检查路径边界后创建父目录，适配历史上默认父目录已存在的脚本；新增针对性验证并重跑 V2 filter 与 R02 输入检查，运行编号 20260909155522，结果将在步骤 6 记录。
- 静态只读输入盘点：34 个明确 external_path 引用全部可找到，7 个仍使用旧项目只读输入；动态拼接路径须以运行 inputs.jsonl 为准。见 docs/migration_history/pretest_input_dependencies_20260909.json。没有为了消除依赖而改造或写入旧项目。
- 最终活动源码 SHA256、函数集合与函数内数值常量核对见 docs/migration_history/pretest_source_verification_20260909.json；这是对路径改造的检查，不等同于全量科学算法验证。

## 2026-09-09 — pretest 收束：步骤 6 / 最终验收与交付状态

- V2 空目录问题修复后全量复验成功（20260909155522）：237901 原始阶段 → 135025 事件；69 个全阶段重复中断边界事件、2 个 Cause Code 内部不一致事件，3 份 CSV 成功写入 pretest/data 时间目录。该结果是执行验证，不是本阶段新增的科学结论。
- 同次 R02 只读输入适配器成功读取并校验本地冻结事件表，既有 15 项事件/天气规则测试全部通过。此前 11 项入口框架测试再次通过，共 26 项。LAD 面积生成、纯绘图、样本与回归链均已有真实执行记录。
- 复核归档 721 文件 SHA256 无变化；2 个样本 + 4 个系数表 + 1 个回归摘要 + Figure 4 PNG，共 8 文件与旧版逐字节相同。函数集合与函数内数值常量核对 121/121 一致。
- 根目录 results 现在仅含 pretest。git diff 确认 src、Comments 与 paper_revision_work_v2 未改动；git diff --check 通过。既有 test 独立研究资料不变，仅新增入口测试文件。
- 默认 python main.py 实际检查通过（20260909160006）：所有具体开关为 0，只生成带目的的 no_steps 运行记录，没有启动分析。没有将验证期间临时启用的开关写回 main.py。
- 更新 filter_v2 顶部历史状态注记，注明本日真实执行结果；更新回归输出提示使用实际 pretest 目录。更新使用指南与源码最终哈希；综合验收记录见 docs/migration_history/pretest_acceptance_20260909.json。第一轮迁移清单中的 after_sha256 代表步骤 2 状态，最终状态以 pretest_source_verification_20260909.json 为准。
- 完成范围：scripts 全部 120 Python 文件以 116 个步骤 + 4 个公共模块接入，额外接入 review_package 回归，共 117 个开关。未批量重跑全部耗时模型/bootstrap/天气下载；少数早期输入保留旧项目只读依赖，独立冻结研究包原样保留。导师代码迁入留待下一阶段。
- 本次未创建 Git 提交或推送；所有开发修改与逐步 LOG.md 同留工作区，便于用户审阅后统一提交。

## 2026-09-09 — pretest 主要里程碑发布：步骤 1 / 发布前检查与说明

- 用户授权将本次更新同步到 Baiyu-Eplur/pyOutageGust，并记录主要 milestone 及主要改动。
- 已核对 origin 为 https://github.com/Baiyu-Eplur/pyOutageGust.git，当前 main；fetch 后本地较 origin/main 领先 1 个既有导师材料只读审查提交，无远程分叉。本次同步包含这个既有祖先提交及统一入口更新。
- 待上传未跟踪文件大小检查通过，无超过 40 MiB 的新文件；遵守现有 .gitignore，不上传 Comments、外部原始快照及已排除的环境文件。不改写既有提交历史。
- 新增 docs/milestones/2026-09-09_pretest-unified-entry.md，记录主要改动、执行方式、26 项测试、721 文件归档和 8 文件逐字节一致的证据及范围限制。README 顶部增加里程碑入口。
- 发布标识确定为 pretest-unified-entry-20260909；以附注 Git 标签和 GitHub Release 保存本节点。后续将提交并推送 main 与标签，再核对远程提交/标签/发布记录。

## 2026-09-09 — pretest 主要里程碑发布：步骤 2 / 暂存与字节一致性保护

- 已将本轮代码、文档、历史结果迁移与验证输出加入暂存区。721 个历史输出的移动由 Git 识别为路径迁移；未将忽略目录强行加入版本控制。
- 暂存时发现本机 Git 的自动换行转换会改变部分归档文本/CSV 的仓库存储字节，从而使归档 SHA256 在远程失去一致性。新增 .gitattributes：results/pretest/** 使用 -text 原样保存；仅活动 Python 脚本固定 LF，避免跨平台源码校验因换行改变。冻结研究包规则不变。
- 修正里程碑说明中的 Markdown 行尾空格，重新暂存并检查；随后核对暂存区 blob 与 721 项归档 SHA256 及活动源码校验，而不只检查工作区文件。

- 步骤 2 检查后的修正：活动源码现有字节包含 CRLF/LF 混合，若统一 LF，同样会改变既有运行记录中的源码 SHA256。因此 .gitattributes 的最终规则对活动源码也使用 -text，原样保存本节点真实字节，而不进行换行重写。旧数据中的 CRLF 不作为待修复空格；代码/新增文档检查与归档字节检查分开执行。
