# R02 全量天气可用性与来源

全事件 135,025；可生成最早查询键的事件 129,414；不同查询键 82,621；键×目标小时 122,948。查询对应现存文件 74,896。目录原有 75,983 个 pkl，目录中其他日期/阶段的文件不等于本轮事件所需文件。新网络请求为 0。

| cache_file_status | requested_keys |
| --- | --- |
| readable | 74896 |
| missing_file | 7725 |

事件分母结果：

| weather_cache_status | weather_validation_tier | weather_numeric_available | events |
| --- | --- | --- | --- |
| missing_file | unavailable | False | 8236 |
| query_ineligible | unavailable | False | 5611 |
| readable | strict_cache_checked | True | 121178 |

同一键只读取并哈希一次，可服务多个事件及目标小时。精确时刻须唯一；雨量窗口为 (t−24h,t]，24 个唯一整点、全部有限且非负。未使用 nearest 小时或将 NaN 雨量补零。缓存可读但窗口无效时保留失败状态，不用旧 v3 值掩盖。缓存不可得时，仅在最早源行、坐标日期键与精确小时均匹配时保留 v3 值，标记 v3_only_window_not_reverified。

| rain_window_status | key_hours |
| --- | --- |
| valid_24_unique_values | 114791 |
| nan | 8157 |

字段变化（列名 gt_1e6 指绝对阈值 1e-6）：

| field | new_finite | old_finite | both_finite_changed_gt_1e6 | old_missing_new_finite | old_finite_new_missing | earliest_v3_both_finite_changed_gt_1e6 | earliest_v3_missing_new_finite | earliest_v3_finite_new_missing | max_abs_vs_earliest_v3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gust_0h | 121178 | 121313 | 10820 | 9 | 144 | 0 | 0 | 0 | 7.105427357601002e-15 |
| precipitation_24h_sum | 121178 | 121313 | 6477 | 9 | 144 | 0 | 0 | 0 | 7.105427357601002e-15 |
| temperature_0h | 121178 | 121313 | 10964 | 9 | 144 | 0 | 0 | 0 | 7.105427357601002e-15 |
| pressure_msl_0h | 121178 | 121313 | 10720 | 9 | 144 | 0 | 0 | 0 | 1.1368683772161603e-13 |

单位依据是冻结采集代码的 wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT；缓存自身未提供可确认的响应单位 metadata。历史请求未锁定 model，historical_model_unresolved 保留在所有事件上，不能据当前 API 默认模型追认 ERA5，也不能将缓存数值通过等同于业务/产品来源通过。缓存 attrs 与 SHA、读取错误、有效雨量计数保存在 weather_key_hour_audit.parquet；每个请求文件索引见 requested_cache_file_manifest.csv。

实际缺缓存事件 8,236 中，最早 v3 源行已存任一天气值者为 0；因此本轮没有 v3-only 条件样本，不能解释为程序一律删除此类值。其中 144 个事件旧较晚代表行有天气，新版不借用。另有 9 个事件从旧代表行缺失变为最早记录可用，四天气完整事件由 121,313 减至 121,178（−144+9）；这些 9 个最早源行本来就有 v3 数值，并非本轮新抓或从缺失 v3 恢复。所有可读缓存 attrs 为空，产品状态仍未决。
