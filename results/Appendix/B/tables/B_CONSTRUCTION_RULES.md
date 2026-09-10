# B_CONSTRUCTION_RULES

需求 B01；B.1–B.2。事件构造规则和代表行修复证据。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

C01清理计数为历史全事件构建范围，不能当作当前60437行回归样本。

| quantity | rule | meaning |
| --- | --- | --- |
| C | sum(stage_customers where reinterruption is excluded) | 不对再中断阶段重复计客户 |
| D_B | max(all_stage_end)-min(all_stage_start), in hours | 再中断阶段仍计时 |
| representative | stable sort by stage start; existing deterministic source-row tie breaker | 复用C01修复，不以输入顺序任意挑选天气/原因字段 |
| missing | retain undefined outcomes as missing; use existing curated samples | 不把未定义结果填零 |
| R0_final | existing positive-duration trimmed R0c input, then C>0 | 现有上端截断先于此处读取；本入口不重算截断点 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
