# H_CONDITIONAL_LOGNORMAL

需求 H02；H.3。已保存事件条件lognormal参数与曲线。

分析单位：incident。样本：源JSON E0全体60437/天气9857，恢复59834/天气9806，含零客户。

模型：事件条件lognormal；并非district-day背景率模型。指标：见来源字段，原单位。

验证：只读已有结果；本轮不拟合。

参数仅按既有记录导出，边界/优化诊断保留；极端theta不能当作有效物理阈值。不导出新增降水交互曲面。

| margin | spec | n | state | theta_m_s | beta | LR_common_vs_free | LR_p | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0 | lognormal_weather_common_beta | 9857 | >5 | 0.02112584071 | 14.93923057 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_weather_common_beta | 9857 | >100 | 3565.666926 | 14.93923057 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_weather_common_beta | 9857 | >1000 | 3.989190869e+12 | 14.93923057 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_weather_free_beta | 9857 | >5 | 8.680493902e-11 | 60.19252771 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_weather_free_beta | 9857 | >100 | 1242.851539 | 12.15378924 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_weather_free_beta | 9857 | >1000 | 249534.7849 | 5.563791129 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_all_incidents | 60437 | >5 | 44.26114629 | 8.434494432 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_all_incidents | 60437 | >100 | 60712.12996 | 8.434494432 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| E0 | lognormal_all_incidents | 60437 | >1000 | 387137760 | 8.434494432 | 12.62375947 | 0.001814619033 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_common_beta | 9806 | >3 h | 6.533277669 | 1.365571231 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_common_beta | 9806 | >12 h | 35.25938309 | 1.365571231 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_common_beta | 9806 | >48 h | 81.9797909 | 1.365571231 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_free_beta | 9806 | >3 h | 4.605739217 | 2.181608748 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_free_beta | 9806 | >12 h | 30.02030043 | 1.122798293 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_weather_free_beta | 9806 | >48 h | 42.54942678 | 0.8035535447 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_all_incidents | 59834 | >3 h | 0.2724521696 | 7.152558328 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_all_incidents | 59834 | >12 h | 810.2734655 | 7.152558328 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |
| R0c | lognormal_all_incidents | 59834 | >48 h | 2123015.31 | 7.152558328 | 307.7716842 | 1.473085421e-67 | Conditional on recorded incident; saved estimates only, no physical theta interpretation |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
