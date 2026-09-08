import json
import os
import time
import traceback
from pathlib import Path

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from tqdm import tqdm


# =========================================================
# 0. Paths (all relative)
# =========================================================
import sys

if getattr(sys, 'frozen', False):
    # exe运行
    BASE_DIR = Path(sys.executable).parent
else:
    # 正常python运行
    BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT =  "D:\\Pyprogramme\\STST2603\\data\\new\\unplanned_incidents_clean_2.csv"
OUTPUT = "D:\\Pyprogramme\\STST2603\\data\\new\\ukpn_master_weather_matrix.csv"

UNIQUE_REQUEST_CACHE_DIR = DATA_DIR / "weather_request_cache"
FAILED_REQUEST_LOG = DATA_DIR / "weather_failed_requests.csv"
MISSING_INCIDENT_LOG = DATA_DIR / "weather_missing_incidents.csv"
CHECKPOINT_PATH = DATA_DIR / "weather_checkpoint.json"

REQUESTS_CACHE_PATH = BASE_DIR / ".weather_cache_master"


# =========================================================
# 1. API client
# =========================================================
cache_session = requests_cache.CachedSession(
    str(REQUESTS_CACHE_PATH),
    expire_after=-1
)
retry_session = retry(cache_session, retries=8, backoff_factor=0.5)
openmeteo = openmeteo_requests.Client(session=retry_session)


# =========================================================
# 2. Custom exceptions
# =========================================================
class APILimitReachedError(Exception):
    pass


# =========================================================
# 3. Utility functions
# =========================================================
def now_utc_iso():
    return pd.Timestamp.now("UTC").isoformat()


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


def ensure_parent_dir(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def append_rows_to_csv(df_append, csv_path):
    csv_path = Path(csv_path)
    if df_append is None or df_append.empty:
        return
    ensure_parent_dir(csv_path)
    header = not csv_path.exists()
    df_append.to_csv(csv_path, mode="a", index=False, header=header)


def write_json(obj, path):
    path = Path(path)
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def read_json_if_exists(path):
    path = Path(path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def round_coordinates(df, lat_col="lat", lon_col="lon", decimals=1):
    df = df.copy()
    df["lat_r"] = df[lat_col].round(decimals)
    df["lon_r"] = df[lon_col].round(decimals)
    return df


def build_hourly_dataframe(response, hourly_vars):
    hourly = response.Hourly()
    times = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    data = {"time_utc": times}
    for i, var_name in enumerate(hourly_vars):
        data[var_name] = hourly.Variables(i).ValuesAsNumpy()

    return pd.DataFrame(data)


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
            cols[f"{v}_{w}_max"] = np.nan

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


def parse_spatial_coordinates(series):
    coords = (
        series.astype(str)
        .str.replace('"', "", regex=False)
        .str.split(",", expand=True)
    )
    lat = pd.to_numeric(coords[0].str.strip(), errors="coerce")
    lon = pd.to_numeric(coords[1].str.strip(), errors="coerce")
    return lat, lon


def prepare_incident_time(df, time_col, assume_local_london_time=False):
    df = df.copy()
    s = df[time_col].astype(str).str.strip()

    try:
        parsed = pd.to_datetime(s, errors="coerce")
    except ValueError:
        parsed = None

    if parsed is None:
        parsed_utc = pd.to_datetime(s, errors="coerce", utc=True)
        df["clean_start"] = parsed_utc
        return df

    if hasattr(parsed.dt, "tz") and parsed.dt.tz is not None:
        df["clean_start"] = parsed.dt.tz_convert("UTC")
        return df

    if assume_local_london_time:
        df["clean_start"] = (
            parsed
            .dt.tz_localize("Europe/London", ambiguous="infer", nonexistent="shift_forward")
            .dt.tz_convert("UTC")
        )
    else:
        df["clean_start"] = pd.to_datetime(s, errors="coerce", utc=True)

    return df


def has_required_weather_values(row_dict):
    required_cols = [
        "windspeed_0h",
        "gust_0h",
        "temperature_0h",
        "humidity_0h",
        "cloud_cover_0h"
    ]
    vals = [row_dict.get(c, np.nan) for c in required_cols]
    return pd.notna(pd.Series(vals)).sum() >= 3


def load_processed_ids(output_path, id_col):
    output_path = Path(output_path)
    processed_ids = set()
    if output_path.exists():
        try:
            existing = pd.read_csv(output_path, usecols=[id_col], dtype={id_col: str})
            processed_ids = set(existing[id_col].dropna().astype(str).unique())
        except Exception as e:
            print(f"[警告] 读取已有输出表失败，将视为未完成。错误：{e}")
    return processed_ids


def get_cached_request_keys(cache_dir):
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return set()
    return {
        p.stem for p in cache_dir.glob("*.pkl")
    }


# =========================================================
# 4. Weather fetch
# =========================================================
def fetch_weather_for_request(lat, lon, req_date, debug=False, sleep_sec=0.25):
    hourly_vars = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "snowfall",
        "snow_depth",
        "cloud_cover",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "surface_pressure",
        "pressure_msl",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "soil_moisture_0_to_7cm",
        "soil_temperature_0_to_7cm",
        "weather_code"
    ]

    start_date = (pd.Timestamp(req_date) - pd.Timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = (pd.Timestamp(req_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": hourly_vars,
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timezone": "GMT"
    }

    try:
        responses = openmeteo.weather_api(
            "https://archive-api.open-meteo.com/v1/archive",
            params=params
        )
        response = responses[0]
        df_hourly = build_hourly_dataframe(response, hourly_vars)
        if sleep_sec > 0:
            time.sleep(sleep_sec)
        return df_hourly

    except Exception as e:
        msg = str(e)
        if (
            "Daily API request limit exceeded" in msg
            or "Hourly API request limit exceeded" in msg
        ):
            raise APILimitReachedError(msg)

        if debug:
            print(f"\n[ERROR] fetch_weather_for_request failed")
            print(f"lat={lat}, lon={lon}, req_date={req_date}")
            print(repr(e))
            traceback.print_exc()

        return None


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


# =========================================================
# 5. Incremental incident writer
# =========================================================
def process_incidents_and_flush(
    incidents_df,
    weather_request_store,
    processed_ids,
    output_path,
    missing_incident_log_path,
    checkpoint_path,
    coord_round_decimals,
    save_every=50,
    status="running"
):
    """
    只处理那些 request_key 已经有可用小时天气数据的事故。
    没有成功抓到 request_key 的事故，不会写入 output.csv，从而保证可安全续传。
    """
    if incidents_df.empty:
        return 0

    id_col = "Incident Reference"
    batch_rows = []
    missing_rows = []
    written_count = 0

    writable_mask = incidents_df["request_key"].isin(weather_request_store.keys())
    writable_df = incidents_df[writable_mask].copy()

    if writable_df.empty:
        return 0

    for i, (_, row) in enumerate(
        tqdm(writable_df.iterrows(), total=len(writable_df), desc="生成并写出事故级天气特征")
    ):
        request_key = row["request_key"]
        df_hourly = weather_request_store.get(request_key, None)

        # 保险起见：None 不写最终输出，留待后续重试
        if df_hourly is None:
            continue

        feat = build_incident_features_from_hourly(
            df_hourly=df_hourly,
            target_time_utc=row["clean_start"]
        )

        combined = {
            **row.to_dict(),
            **feat.to_dict()
        }
        batch_rows.append(combined)

        if not has_required_weather_values(combined):
            missing_rows.append({
                id_col: row[id_col],
                "request_key": request_key,
                "clean_start": str(row["clean_start"]),
                "lat": row["lat"],
                "lon": row["lon"],
                "lat_r": row["lat_r"],
                "lon_r": row["lon_r"],
                "reason": "missing_required_weather_values"
            })

        if (i + 1) % save_every == 0 or (i + 1) == len(writable_df):
            batch_df = pd.DataFrame(batch_rows)
            if not batch_df.empty:
                append_rows_to_csv(batch_df, output_path)
                processed_ids.update(batch_df[id_col].astype(str).tolist())
                written_count += len(batch_df)
            batch_rows = []

            if missing_rows:
                append_rows_to_csv(pd.DataFrame(missing_rows), missing_incident_log_path)
                missing_rows = []

            write_json({
                "status": status,
                "processed_incidents_in_output": len(processed_ids),
                "last_saved_time_utc": now_utc_iso(),
                "coord_round_decimals": coord_round_decimals
            }, checkpoint_path)

    return written_count


# =========================================================
# 6. Main pipeline
# =========================================================
def run_power_outage_weather_pipeline(
    input_path,
    output_path,
    unique_request_cache_path,
    failed_request_log_path,
    missing_incident_log_path,
    checkpoint_path,
    is_test_mode=True,
    test_n=20,
    assume_local_london_time=False,
    coord_round_decimals=1,
    debug=True,
    save_every=50,
    sleep_sec_formal=0.25
):
    print("=" * 70)
    print(f"开始运行：{'测试模式' if is_test_mode else '正式模式'}")
    print("=" * 70)

    input_path = Path(input_path)
    output_path = Path(output_path)
    unique_request_cache_path = Path(unique_request_cache_path)
    failed_request_log_path = Path(failed_request_log_path)
    missing_incident_log_path = Path(missing_incident_log_path)
    checkpoint_path = Path(checkpoint_path)

    unique_request_cache_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"错误：找不到输入文件 -> {input_path}")
        return

    TIME_COL = "Start Date and Time"
    COORD_COL = "Spatial Coordinates"
    ID_COL = "Incident Reference"

    # -----------------------------
    # A. Read and clean
    # -----------------------------
    df = pd.read_csv(input_path)

    required_cols = [TIME_COL, COORD_COL, ID_COL]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"错误：缺少必要字段 -> {missing_cols}")
        return

    df = prepare_incident_time(df, TIME_COL, assume_local_london_time=assume_local_london_time)
    df["lat"], df["lon"] = parse_spatial_coordinates(df[COORD_COL])

    df = df.dropna(subset=["clean_start", "lat", "lon"]).copy()
    df = df[df["lat"].between(49, 61) & df["lon"].between(-9, 3)].copy()

    if is_test_mode:
        df = df.head(test_n).copy()

    df["incident_date_utc"] = df["clean_start"].dt.date.astype(str)
    df = round_coordinates(df, lat_col="lat", lon_col="lon", decimals=coord_round_decimals)

    df[ID_COL] = df[ID_COL].astype(str)

    df["request_key"] = (
        df["lat_r"].astype(str) + "_" +
        df["lon_r"].astype(str) + "_" +
        df["incident_date_utc"].astype(str)
    )

    # -----------------------------
    # B. Resume
    # -----------------------------
    processed_ids = load_processed_ids(output_path, ID_COL)
    if processed_ids:
        print(f"检测到已有输出表，已完成事故数：{len(processed_ids)}")

    checkpoint_info = read_json_if_exists(checkpoint_path)
    if checkpoint_info:
        print("检测到断点信息：")
        print(json.dumps(checkpoint_info, ensure_ascii=False, indent=2))

    df_to_process = df[~df[ID_COL].isin(processed_ids)].copy()

    print(f"当前待处理事故数：{len(df_to_process)}")
    if df_to_process.empty:
        print("没有需要处理的新事故。")
        return

    req_df = df_to_process[["request_key", "lat_r", "lon_r", "incident_date_utc"]].drop_duplicates().copy()
    req_df = req_df.rename(columns={
        "lat_r": "req_lat",
        "lon_r": "req_lon",
        "incident_date_utc": "req_date"
    })

    print(f"待处理事故总条数：{len(df_to_process)}")
    print(f"唯一天气请求数：{len(req_df)}")
    print(f"请求压缩率：{len(req_df) / len(df_to_process):.4f}")
    print("\n唯一请求示例：")
    print(req_df.head(10))

    weather_request_store = {}
    failed_requests = []
    stop_reason = None
    written_after_stop = 0

    # 先把已有缓存注册进 store
    cached_keys = get_cached_request_keys(unique_request_cache_path)
    common_cached_keys = set(req_df["request_key"]) & cached_keys
    if common_cached_keys:
        print(f"已发现可复用缓存 request_key 数：{len(common_cached_keys)}")

    # -----------------------------
    # C. Fetch unique requests
    # -----------------------------
    try:
        for _, r in tqdm(req_df.iterrows(), total=len(req_df), desc="抓取唯一天气请求"):
            request_key = r["request_key"]
            req_lat = r["req_lat"]
            req_lon = r["req_lon"]
            req_date = r["req_date"]

            pkl_path = unique_request_cache_path / f"{request_key}.pkl"

            if pkl_path.exists():
                try:
                    weather_request_store[request_key] = pd.read_pickle(pkl_path)
                    continue
                except Exception:
                    # 坏缓存就重抓
                    pass

            try:
                df_hourly = fetch_weather_for_request(
                    lat=req_lat,
                    lon=req_lon,
                    req_date=req_date,
                    debug=debug,
                    sleep_sec=0.0 if is_test_mode else sleep_sec_formal
                )
            except APILimitReachedError as e:
                msg = str(e)
                if "Hourly API request limit exceeded" in msg:
                    stop_reason = "hourly_limit_exceeded"
                else:
                    stop_reason = "daily_limit_exceeded"

                print(f"\n[停止抓取] Open-Meteo 配额已耗尽：{stop_reason}")
                print(msg)

                failed_requests.append({
                    "request_key": request_key,
                    "req_lat": req_lat,
                    "req_lon": req_lon,
                    "req_date": req_date,
                    "reason": stop_reason
                })

                write_json({
                    "status": f"stopped_due_to_{stop_reason}",
                    "last_request_key": request_key,
                    "last_req_lat": req_lat,
                    "last_req_lon": req_lon,
                    "last_req_date": str(req_date),
                    "processed_incidents_in_output": len(processed_ids),
                    "last_saved_time_utc": now_utc_iso(),
                    "coord_round_decimals": coord_round_decimals
                }, checkpoint_path)

                break

            if df_hourly is None:
                failed_requests.append({
                    "request_key": request_key,
                    "req_lat": req_lat,
                    "req_lon": req_lon,
                    "req_date": req_date,
                    "reason": "other_error"
                })
                # 注意：None 不放入 store，避免把未成功抓取的 request_key 误写入最终结果
            else:
                weather_request_store[request_key] = df_hourly
                df_hourly.to_pickle(pkl_path)

    except KeyboardInterrupt:
        stop_reason = "manual_interrupt"
        print("\n[手动中止] 检测到 KeyboardInterrupt，正在保存当前已抓取进度...")

        write_json({
            "status": "stopped_due_to_manual_interrupt",
            "processed_incidents_in_output": len(processed_ids),
            "cached_request_keys_available": len(weather_request_store),
            "last_saved_time_utc": now_utc_iso(),
            "coord_round_decimals": coord_round_decimals
        }, checkpoint_path)

    finally:
        # 无论自动停止还是手动停止，都先落失败日志
        if failed_requests:
            append_rows_to_csv(pd.DataFrame(failed_requests), failed_request_log_path)

        # 关键改动：
        # 即使在抓取阶段中止，也把“当前已经有小时天气数据的事故”立即生成并写出到最终 CSV
        if stop_reason is not None:
            print("\n正在将当前已成功抓取的数据输出到事故级 CSV ...")
            written_after_stop = process_incidents_and_flush(
                incidents_df=df_to_process[~df_to_process[ID_COL].isin(processed_ids)].copy(),
                weather_request_store=weather_request_store,
                processed_ids=processed_ids,
                output_path=output_path,
                missing_incident_log_path=missing_incident_log_path,
                checkpoint_path=checkpoint_path,
                coord_round_decimals=coord_round_decimals,
                save_every=save_every,
                status=f"partial_{stop_reason}"
            )
            print(f"已在中止前额外写出事故级结果条数：{written_after_stop}")

    # 如果中止了，到这里直接结束；下次自动续传
    if stop_reason is not None:
        write_json({
            "status": f"partial_{stop_reason}",
            "processed_incidents_in_output": len(processed_ids),
            "last_saved_time_utc": now_utc_iso(),
            "coord_round_decimals": coord_round_decimals,
            "written_after_stop": written_after_stop
        }, checkpoint_path)

        print("=" * 70)
        print("任务已中止，但当前可写结果已保存")
        print(f"输出文件：{output_path}")
        print(f"缺失日志：{missing_incident_log_path}")
        print(f"失败请求日志：{failed_request_log_path}")
        print(f"断点文件：{checkpoint_path}")
        print("=" * 70)
        return

    # -----------------------------
    # D. Full incident-level build
    # -----------------------------
    print("\n开始生成全部可写事故级天气特征...")
    written_count = process_incidents_and_flush(
        incidents_df=df_to_process,
        weather_request_store=weather_request_store,
        processed_ids=processed_ids,
        output_path=output_path,
        missing_incident_log_path=missing_incident_log_path,
        checkpoint_path=checkpoint_path,
        coord_round_decimals=coord_round_decimals,
        save_every=save_every,
        status="running"
    )

    # -----------------------------
    # E. Final checkpoint
    # -----------------------------
    write_json({
        "status": "completed",
        "processed_incidents_in_output": len(processed_ids),
        "last_saved_time_utc": now_utc_iso(),
        "coord_round_decimals": coord_round_decimals,
        "written_this_run": written_count
    }, checkpoint_path)

    print("=" * 70)
    print("任务结束")
    print(f"输出文件：{output_path}")
    print(f"缺失日志：{missing_incident_log_path}")
    print(f"失败请求日志：{failed_request_log_path}")
    print(f"断点文件：{checkpoint_path}")
    print("=" * 70)

    if output_path.exists():
        try:
            final_df = pd.read_csv(output_path)
            weather_cols = [
                "windspeed_0h", "gust_0h", "temperature_0h",
                "precip_0h", "humidity_0h", "cloud_cover_0h"
            ]
            existing_weather_cols = [c for c in weather_cols if c in final_df.columns]

            print("\n关键天气变量非空率：")
            for c in existing_weather_cols:
                non_null_rate = final_df[c].notna().mean()
                print(f"{c}: {non_null_rate:.2%}")
        except Exception as e:
            print(f"[警告] 输出文件统计失败：{e}")


# =========================================================
# 7. Entry
# =========================================================
if __name__ == "__main__":
    TEST_MODE = False

    run_power_outage_weather_pipeline(
        input_path=INPUT,
        output_path=OUTPUT,
        unique_request_cache_path=UNIQUE_REQUEST_CACHE_DIR,
        failed_request_log_path=FAILED_REQUEST_LOG,
        missing_incident_log_path=MISSING_INCIDENT_LOG,
        checkpoint_path=CHECKPOINT_PATH,
        is_test_mode=TEST_MODE,
        test_n=20,
        assume_local_london_time=False,
        coord_round_decimals=1,
        debug=True,
        save_every=20 if TEST_MODE else 50,
        sleep_sec_formal=0.25
    )