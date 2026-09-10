# J_INDEPENDENT_WEATHER_DEFINITIONS

需求 J02；J.2。既有覆盖和天气数值比较。

分析单位：LAD-day / LAD centroid。样本：111 LAD，2021-04-01至2024-03-31。

模型：见需求说明；不合并不同规格排名。指标：天气差值m/s、RMSE m/s、相关（不是概率评分）。

验证：只读已有结果；本轮不拟合。

覆盖/天气数据可复用；不导入P03历史模型排名或旧置信区间。再分析值不是气象站真值，也非LAD全域最大。

| item | value |
| --- | --- |
| url | https://archive-api.open-meteo.com/v1/archive |
| model | era5 |
| field | wind_gusts_10m |
| unit | m/s |
| timezone | GMT |
| start | 2021-04-01 |
| end | 2024-03-31 |
| daily_aggregation | Maximum of 24 hourly wind_gusts_10m values per GMT day |
| LAD_centroids | 111 |
| distinct_returned_grid_coordinates | 52 |
| panel_rows | 121656 |
| coverage_complete_record | True |
| spatial_definition | December 2021 LAD geometric centroid queried at nearest returned ERA5 cell; differs from main incident-coordinate mean location |
| interpretation | ERA5 reanalysis at centroid nearest cell, not station truth or LAD-wide maximum. |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
