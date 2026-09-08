"""Extracted from main1.py (STST2603 root) -- pure feature-computation
helpers, no I/O, no globals. Importing this module has no side effects
(unlike importing main1.py, which opens a requests_cache session and an
Open-Meteo client at module load time)."""
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
