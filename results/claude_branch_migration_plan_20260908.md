# claude_branch 独立迁移改造方案

日期：2026-09-08
范围：只读方案设计，未修改/移动/删除任何文件。基于 [external_dependency_audit_20260908.md](external_dependency_audit_20260908.md) 的结论。

已确定的两条前置决策：
1. `main1.py` 的依赖处理方式：提取 `step2_weather_reextraction.py` 实际用到的 `main1.py` 函数，做成新项目自己的独立模块（不是整体复制 main1.py）。
2. `STST2603_model_review_package/data` 处理方式：在新项目里新建一份完全独立的 review package，老的作废（不再跨项目写入）。

---

## 1. main1.py 依赖提取评估

`claude_branch/scripts/c01_repair_20260905/step2_weather_reextraction.py` 只 import 了一个函数：`build_incident_features_from_hourly`（脚本 docstring 里提到的 `summarize_window` 并非独立 import，而是被前者内部调用到的私有辅助函数）。顺着调用链往下追，完整闭包是 5 个函数，**全部是无副作用的纯函数**，只依赖 `numpy`/`pandas`，不触碰 main1.py 里的任何全局状态（`BASE_DIR`、`DATA_DIR`、`INPUT`/`OUTPUT`、`cache_session`、`openmeteo` 等一概未用到）：

```python
"""Extracted from main1.py — pure feature-computation helpers, no I/O, no globals."""
import numpy as np
import pandas as pd


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def circular_mean_deg(series_deg):
    s = pd.Series(series_deg).dropna()
    if s.empty:
        return np.nan
    rad = np.deg2rad(s)
    sin_mean = np.sin(rad).mean()
    cos_mean = np.cos(rad).mean()
    angle = np.rad2deg(np.arctan2(sin_mean, cos_mean))
    return (angle + 360) % 360


def make_empty_feature_series():
    cols = {}
    base_cols = [
        "wx_time_used_utc",
        "temperature_0h", "humidity_0h", "dewpoint_0h", "apparent_temp_0h",
        "precip_0h", "rain_0h", "snowfall_0h", "snow_depth_0h",
        "cloud_cover_0h", "cloud_low_0h", "cloud_mid_0h", "cloud_high_0h",
        "surface_pressure_0h", "pressure_msl_0h",
        "windspeed_0h", "winddir_0h", "gust_0h",
        "soil_moisture_0h", "soil_temp_0h",
        "weather_code_0h"
    ]
    for c in base_cols:
        cols[c] = np.nan

    windows = ["6h", "12h", "24h", "48h", "72h"]
    mean_max_min_vars = [
        "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
        "temperature_2m", "relative_humidity_2m", "dew_point_2m",
        "apparent_temperature", "surface_pressure", "pressure_msl",
        "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
        "soil_moisture_0_to_7cm", "soil_temperature_0_to_7cm"
    ]
    sum_max_vars = ["precipitation", "rain", "snowfall"]

    for w in windows:
        for v in mean_max_min_vars:
            if v == "wind_direction_10m":
                cols[f"{v}_{w}_circmean"] = np.nan
            else:
                cols[f"{v}_{w}_mean"] = np.nan
                cols[f"{v}_{w}_max"] = np.nan
                cols[f"{v}_{w}_min"] = np.nan
        for v in sum_max_vars:
            cols[f"{v}_{w}_sum"] = np.nan
        cols[f"incident_hour_in_window_{w}"] = np.nan

    return pd.Series(cols)


def summarize_window(df_hourly, end_time_utc, hours, prefix):
    start_time_utc = end_time_utc - pd.Timedelta(hours=hours)
    win = df_hourly[
        (df_hourly["time_utc"] > start_time_utc) &
        (df_hourly["time_utc"] <= end_time_utc)
    ].copy()

    result = {}
    if win.empty:
        result[f"incident_hour_in_window_{prefix}"] = 0
        return result

    result[f"incident_hour_in_window_{prefix}"] = len(win)

    mean_max_min_vars = [
        "wind_speed_10m", "wind_gusts_10m",
        "temperature_2m", "relative_humidity_2m",
        "dew_point_2m", "apparent_temperature",
        "surface_pressure", "pressure_msl",
        "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
        "soil_moisture_0_to_7cm", "soil_temperature_0_to_7cm"
    ]
    for v in mean_max_min_vars:
        if v in win.columns:
            result[f"{v}_{prefix}_mean"] = safe_float(win[v].mean())
            result[f"{v}_{prefix}_max"] = safe_float(win[v].max())
            result[f"{v}_{prefix}_min"] = safe_float(win[v].min())

    if "wind_direction_10m" in win.columns:
        result[f"wind_direction_10m_{prefix}_circmean"] = circular_mean_deg(win["wind_direction_10m"])

    sum_max_vars = ["precipitation", "rain", "snowfall"]
    for v in sum_max_vars:
        if v in win.columns:
            result[f"{v}_{prefix}_sum"] = safe_float(win[v].sum())
            result[f"{v}_{prefix}_max"] = safe_float(win[v].max())

    return result


def build_incident_features_from_hourly(df_hourly, target_time_utc):
    if df_hourly is None or df_hourly.empty:
        return make_empty_feature_series()

    target_hour_utc = pd.Timestamp(target_time_utc).floor("h")
    current_row = df_hourly.loc[df_hourly["time_utc"] == target_hour_utc]
    if current_row.empty:
        pos = (df_hourly["time_utc"] - target_hour_utc).abs().idxmin()
        current_row = df_hourly.loc[[pos]]
    current_row = current_row.iloc[0]

    result = {
        "wx_time_used_utc": current_row["time_utc"],
        "temperature_0h": safe_float(current_row.get("temperature_2m", np.nan)),
        "humidity_0h": safe_float(current_row.get("relative_humidity_2m", np.nan)),
        "dewpoint_0h": safe_float(current_row.get("dew_point_2m", np.nan)),
        "apparent_temp_0h": safe_float(current_row.get("apparent_temperature", np.nan)),
        "precip_0h": safe_float(current_row.get("precipitation", np.nan)),
        "rain_0h": safe_float(current_row.get("rain", np.nan)),
        "snowfall_0h": safe_float(current_row.get("snowfall", np.nan)),
        "snow_depth_0h": safe_float(current_row.get("snow_depth", np.nan)),
        "cloud_cover_0h": safe_float(current_row.get("cloud_cover", np.nan)),
        "cloud_low_0h": safe_float(current_row.get("cloud_cover_low", np.nan)),
        "cloud_mid_0h": safe_float(current_row.get("cloud_cover_mid", np.nan)),
        "cloud_high_0h": safe_float(current_row.get("cloud_cover_high", np.nan)),
        "surface_pressure_0h": safe_float(current_row.get("surface_pressure", np.nan)),
        "pressure_msl_0h": safe_float(current_row.get("pressure_msl", np.nan)),
        "windspeed_0h": safe_float(current_row.get("wind_speed_10m", np.nan)),
        "winddir_0h": safe_float(current_row.get("wind_direction_10m", np.nan)),
        "gust_0h": safe_float(current_row.get("wind_gusts_10m", np.nan)),
        "soil_moisture_0h": safe_float(current_row.get("soil_moisture_0_to_7cm", np.nan)),
        "soil_temp_0h": safe_float(current_row.get("soil_temperature_0_to_7cm", np.nan)),
        "weather_code_0h": safe_float(current_row.get("weather_code", np.nan)),
    }
    for hours, prefix in [(6, "6h"), (12, "12h"), (24, "24h"), (48, "48h"), (72, "72h")]:
        result.update(summarize_window(df_hourly, target_hour_utc, hours, prefix))
    return pd.Series(result)
```

**评估：可以干净独立出来，且强烈建议这么做而不是继续 import main1.py**——原因是 `import main1` 在模块顶层会**产生真实副作用**：它会立即创建 `requests_cache.CachedSession(BASE_DIR/".weather_cache_master", expire_after=-1)` 和一个 `openmeteo_requests.Client(...)`（main1.py:36-47），也就是说哪怕你只想要一个纯函数，import 这一行就会在磁盘上打开/建立根目录的 `.weather_cache_master.sqlite`。提取成独立模块后完全消除这个隐藏耦合。

---

## 2. materialize_final_data.py 分析 + 新 review package 目录建议

该脚本本身很干净：数据来源是 `claude_branch/scripts/c02_c08_repair_20260905/corrected_sample_builder.py` 的 `build_corrected_combined_samples()`（**这是 claude_branch 内部模块，不是外部依赖**），只是写出目的地 `OUT_DIR` 硬编码指向了根目录的 `STST2603_model_review_package/data`，写了两个文件：`combined_E0_final.csv`（E0 样本，60,437 行）、`combined_R0c_final.csv`（R0c 样本，59,834 行）。

现有的根目录 `STST2603_model_review_package/` 其余部分已经做得很规范、可以直接当模板复制：`code/run_main_regression.py` 用 `Path(__file__).resolve().parent.parent` 相对路径寻址，**不含任何硬编码绝对路径**，README 里也明确写了"No files from the main project are required to run the regression"。真正的跨项目耦合只有 `materialize_final_data.py` 这一根线。

**新项目里独立 review package 建议结构**（直接照搬现有结构，只改 `materialize_final_data.py` 的 `OUT_DIR`）：

```
<新项目>/review_package/
├── README.md                      # 照搬现有 README，把 "STST2603_model_review_package" 字样替换成新项目名
├── requirements.txt                # 复制现有版本快照（记录当时验证用的包版本）
├── code/
│   ├── run_main_regression.py      # 原样复制，已是相对路径，无需改
│   └── PROVENANCE.md
├── data/
│   ├── combined_E0_final.csv       # 由新版 materialize_final_data.py 写入
│   └── combined_R0c_final.csv
└── results/
    ├── E0_corrected_lad_cluster.csv
    ├── E0_corrected_twoway_cluster.csv
    ├── R0c_corrected_lad_cluster.csv
    ├── R0c_corrected_twoway_cluster.csv
    ├── run_summary.json
    └── verification_report.md
```

`materialize_final_data.py` 唯一需要改的一行：`OUT_DIR = Path(<新项目根>) / "review_package" / "data"`。老的根目录 `STST2603_model_review_package/` 按决定直接作废，不再有任何脚本写入它。

---

## 3. 外部文件 → 新项目内部路径映射表

| 外部文件/目录（老，根目录下） | 新项目内部路径 | 引用方 |
|---|---|---|
| `rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv` | `<新项目>/data/external/ukpn_full_stage_dataset_v3.csv` | ~20 个 v3 分析脚本（`v3_validation_pipeline.py`、`step1_representative_row.py`、`step10_named_storms.py` 等） |
| `data/Local_Authority_Districts_December_2021_UK_BGC_2022/LAD_DEC_2021_UK_BGC.shp`（含 .dbf/.shx/.prj 等同名 sidecar 文件） | `<新项目>/data/external/gis/LAD_DEC_2021_UK_BGC/LAD_DEC_2021_UK_BGC.shp` | `figure1_study_area.py`、`figure6_regional_map.py` 等 ~8 个制图脚本 |
| `data/dno_license_areas_20200506/DNO_License_Areas_20200506.shp`（同上含 sidecar） | `<新项目>/data/external/gis/DNO_License_Areas_20200506/DNO_License_Areas_20200506.shp` | `figure1_study_area.py`（2 个副本） |
| `data/ukpn-iis.csv` | `<新项目>/data/external/ukpn-iis.csv` | `pipeline_v2/filter_v2.py`、`match_lad_v2.py` |
| `data/new/ukpn_master_weather_matrix*.csv` | `<新项目>/data/external/ukpn_master_weather_matrix.csv`（及其变体文件） | `pipeline_v2/match_lad_v2.py` |
| `data/weather_request_cache/*.pkl` | `<新项目>/data/external/weather_request_cache/`（原样整目录复制） | `step2_weather_reextraction.py` |
| `main1.py::build_incident_features_from_hourly` 等 5 个函数 | `<新项目>/src/weather_features.py`（新独立模块，见第 1 项） | `step2_weather_reextraction.py` |
| `STST2603_model_review_package/data`（反向写入目标） | `<新项目>/review_package/data/`（见第 2 项，老包作废） | `materialize_final_data.py` |
| 根目录整体（`root=Path('D:/Pyprogramme/STST2603')`） | **不迁移**——建议改为 CLI 参数/配置项而非硬编码，因为 `source_inventory.py` 本职就是"清点/审计老根目录"，这个工具的职责决定了它需要能指向老项目位置；迁移后把根路径做成 `--root` 参数即可，脚本本身随 R05 一起搬进新项目 | `R05/src/source_inventory.py` |
| 同 `rebuild_v3_full_stage` + shapefile 路径（重复副本） | 同上两条映射 | `R02/code_changes/v3_validation_pipeline.py`、`R02_isolation_audit/before/v3_validation_pipeline_R02_patched.py` |

---

## 4. 新项目目录结构骨架

```
<新项目>/
├── data/
│   ├── external/               # 从老 STST2603 根目录迁移进来的只读输入快照（第3项映射表的落点）
│   │   ├── ukpn_full_stage_dataset_v3.csv
│   │   ├── ukpn-iis.csv
│   │   ├── ukpn_master_weather_matrix.csv (+ 变体)
│   │   ├── weather_request_cache/
│   │   └── gis/
│   │       ├── LAD_DEC_2021_UK_BGC/
│   │       └── DNO_License_Areas_20200506/
│   └── generated/               # claude_branch 自己产出的中间/衍生数据（原 claude_branch/results/* 里的数据文件部分）
├── src/
│   └── weather_features.py      # 第1项：从 main1.py 提取出的纯函数模块
├── scripts/                     # 原 claude_branch/scripts/* 各任务文件夹整体平移
├── paper_revision_work_v2/      # R02、R02_isolation_audit、R03(自带venv)、R04(自带venv)、R05、X02_storm_specialization、code
├── review_package/              # 第2项：全新独立的审阅包
│   ├── README.md
│   ├── requirements.txt
│   ├── code/
│   └── results/
├── docs/                        # 原 claude_branch/docs
├── results/                     # 原 claude_branch/results（去掉迁移到 review_package 的那部分）
├── test/
└── requirements.txt              # 复用根 .venv 的清单 + 补一行 diptest（见外部依赖审计报告结论）
```

---

## 5. 孤儿日志文件（待删除项）

```
D:\Pyprogramme\STST2603\claude_branchresultsc09_final_cleanup_20260905rawrun_all_c09.log
```

已在外部依赖审计中确认：这是一次路径拼接失败的孤儿残留文件，内容只是一条 `FileNotFoundError` 记录，之后该脚本已被正确重跑并产出了正常结果。**标记为待删除，本次不做任何操作**，留待人工 review 通过后的第二阶段执行。

---

以上方案未修改/移动/删除任何文件，仅为设计文档。等 review 通过后再按批准范围执行实际迁移。
