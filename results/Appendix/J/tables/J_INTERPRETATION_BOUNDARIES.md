# J_INTERPRETATION_BOUNDARIES

需求 J08；J.6。方法/用途/不可支持解释的简明登记。

分析单位：LAD-day。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

不声称等效、统计显著或完全校准；不自动提出模型替换。

| section | definition | supports | does_not_support |
| --- | --- | --- | --- |
| J.1 | Main event-anchor proxy | Includes no-event days under existing retrospective weather interpolation | Does not remove event-anchor dependence |
| J.2 | Independent ERA5 centroid daily maximum | Different location/sampling/time aggregation | No valid complete repaired proxy-vs-grid model ranking located |
| J.3 | Five aggregations on fixed ERA5 | Within-task same-sample aggregation comparison | Not a validation of main proxy; no cross-experiment raw Brier ranking |
| J.4 | G plus H/24 or log1p(square cumulative excess) | Increment of two specified duration indicators | Not top3/rolling3; not precise consecutive duration or structural damage |
| J.5 | Frozen development fit, later retrospective period | BSS versus development constant, calibration and monthly description | Not a pristine independent confirmation set, advance forecast, full calibration or significance claim |
| J.6 | Descriptive scope | Mixed/adverse results preserved; no posthoc adoption cutoff | No equivalence, replacement decision, manuscript revision or closed audit |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
