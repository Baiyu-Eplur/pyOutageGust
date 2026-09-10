# J_PROXY_DEFINITIONS

需求 J01；J.1。构造定义与现有面板标签数量。

分析单位：LAD-day。样本：111 LAD × 1096日期。

模型：p0+(1-p0)Phi((ln g-ln theta)/beta)。指标：八标签阳性数、比例。

验证：只读已有结果；本轮不拟合。

当天事件坐标均值中心、40km Gaussian/distance插值，非ERA5日最大；任意事件包含零客户，其他阈值严格>且为至少一个事件。只读定义和标签，不审计历史拟合。

| item | definition |
| --- | --- |
| unit | LAD-day including no-event days |
| location | Mean incident lat/lon per LAD in main production, not polygon geometric centroid |
| gust | Same-day event-hour gust observations; normalized exp(-0.5*(distance/BW)^2) weights |
| bandwidth_km | 40.0 |
| minimum_neighbours | 5 |
| fallback | If fewer than KMIN weights > 0.001, nearest KMIN with weight 1/(distance_km+1), then normalize |
| any_gt0 | n_inc>0, including zero-customer incidents |
| wthr_gt0 | wmaxc>=0, including zero-customer weather incidents |
| gt5_gt100_gt1000 | At least one qualifying incident with customers strictly > threshold; no daily customer sum |
| weather | cause_group_official == weather_natural |
| model | p0+(1-p0)*Phi((ln(g)-ln(theta))/beta) |
| availability | Same-day event anchors: retrospective proxy, not advance weather-only outage forecasting |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
