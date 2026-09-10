# F03_R2_DECOMPOSITION

需求 F03；F.3。四组完整顺序增量结果。

分析单位：incident。样本：E0=60437; R0c建模前=59834，当前正客户恢复=51173；以各表明确口径为准。

模型：见需求说明；不合并不同规格排名。指标：OOF R²及增量（比例，非百分数）。

验证：固定LAD-CV顺序分解。

Regional + calendar是联合块，不能写成calendar单独贡献；顺序分解不是唯一因果分解。

| sample | margin | group | cum_r2 | marginal | n |
| --- | --- | --- | --- | --- | --- |
| all | E0 | Regional + calendar | 0.009594158174 | 0.009594158174 | 60437 |
| all | E0 | Non-gust weather | 0.01870962243 | 0.009115464256 | 60437 |
| all | E0 | Gust | 0.03357414092 | 0.01486451849 | 60437 |
| all | R0c | Regional + calendar | 0.03464932516 | 0.03464932516 | 51173 |
| all | R0c | Non-gust weather | 0.04073417851 | 0.006084853352 | 51173 |
| all | R0c | Gust | 0.04775585755 | 0.007021679038 | 51173 |
| all | R0c | Affected customers | 0.1074463669 | 0.05969050939 | 51173 |
| weather | E0 | Regional + calendar | 0.007839989726 | 0.007839989726 | 9857 |
| weather | E0 | Non-gust weather | 0.02865757267 | 0.02081758294 | 9857 |
| weather | E0 | Gust | 0.04427993137 | 0.0156223587 | 9857 |
| weather | R0c | Regional + calendar | 0.2017671242 | 0.2017671242 | 9254 |
| weather | R0c | Non-gust weather | 0.2270457033 | 0.02527857906 | 9254 |
| weather | R0c | Gust | 0.2458190391 | 0.0187733358 | 9254 |
| weather | R0c | Affected customers | 0.2812451461 | 0.03542610699 | 9254 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
