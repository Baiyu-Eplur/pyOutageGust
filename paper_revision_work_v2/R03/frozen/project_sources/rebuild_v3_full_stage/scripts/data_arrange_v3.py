import pandas as pd

# ==============================
# File path
# ==============================
file_path = r"D:\Pyprogramme\STST2603\data\new\ukpn_master_with_lad_features.csv"

# ==============================
# Read CSV
# ==============================
df = pd.read_csv(file_path, low_memory=False)
df.columns = df.columns.str.strip()

# ==============================
# Column names
# ==============================
start_col = "Start Date and Time"
end_col = "End Date and Time"

# ==============================
# Datetime conversion (统一时区 + 去时区)
# ==============================
df[start_col] = pd.to_datetime(df[start_col], errors="coerce", utc=True).dt.tz_convert(None)
df[end_col] = pd.to_datetime(df[end_col], errors="coerce", utc=True).dt.tz_convert(None)

# ==============================
# 计算变量（先不写入 df）
# ==============================

# Duration (hours)
duration = (df[end_col] - df[start_col]).dt.total_seconds() / 3600
duration[duration < 0] = pd.NA

# Daytime Indicator
start_hour = df[start_col].dt.hour
daytime = ((start_hour >= 6) & (start_hour < 18)).astype("Int64")

# 时间结构变量
hour = start_hour
month = df[start_col].dt.month
weekday = df[start_col].dt.weekday  # 0=Monday, 6=Sunday

# ==============================
# 一次性写入（避免 fragmentation）
# ==============================
new_cols = pd.DataFrame({
    "Duration (hours)": duration,
    "Daytime Indicator": daytime,
    "Hour": hour,
    "Month": month,
    "Weekday": weekday
})

df = pd.concat([df, new_cols], axis=1)

# 👉 内存整理（关键）
df = df.copy()

# ==============================
# Save
# ==============================
output_path = r"D:\Pyprogramme\STST2603\data\new\ukpn_master_with_lad_features_updated.csv"
df.to_csv(output_path, index=False)

print("Finished.")
print("Added variables:")
print("- Duration (hours)")
print("- Daytime Indicator")
print("- Hour")
print("- Month")
print("- Weekday")