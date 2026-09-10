# J03_PROXY_HISTORY_COMPARISON

需求 J03；J.2。已接受且两端优化有效的proxy/grid全八任务比较。

分析单位：LAD-day。样本：111 LAD × 1096 UTC days = 121656 rows; identical eight labels and saved five LAD folds。

模型：shared ddagg01-stable-v1 background-rate lognormal; PROXY versus GRID_MAX。指标：pooled OOF Brier/BSS; delta=PROXY-GRID_MAX; paired conditional 95% interval。

验证：48 components per source; training-only fits; fixed OOF paired LAD bootstrap B=1000 seed=20260909。

第一步仅J03；产物补齐后待研究负责人反馈分析，不自动科学关闭或进入F/GI/H。

| target | comparison | new_valid | historical_theta | stable_theta | difference_theta | historical_beta | stable_beta | difference_beta | historical_p0 | stable_p0 | difference_p0 | historical_nll | stable_nll | difference_nll | mean_probability_difference | max_abs_probability_difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| any_gt0 | full-sample descriptive, not OOF | True | 22.61788409 | 22.61801567 | 0.0001315781707 | 0.4369473537 | 0.4369554674 | 8.113652272e-06 | 0.3191421938 | 0.3191419228 | -2.709771015e-07 | 77802.69377 | 77802.69377 | -9.451468941e-08 | 2.488918994e-07 | 5.26321142e-06 |
| any_gt5 | full-sample descriptive, not OOF | True | 23.93308419 | 23.93319008 | 0.0001058835313 | 0.3622401618 | 0.3622430926 | 2.930838469e-06 | 0.1510637609 | 0.1510636747 | -8.61857028e-08 | 54215.3597 | 54215.3597 | -3.436434781e-08 | -9.086271123e-08 | 4.7864213e-06 |
| any_gt100 | full-sample descriptive, not OOF | True | 25.08159876 | 25.08161583 | 1.707074599e-05 | 0.2912776292 | 0.2912780785 | 4.493467429e-07 | 0.0531249595 | 0.05312495782 | -1.678796283e-09 | 27206.36118 | 27206.36118 | -7.930793799e-10 | -7.480711552e-10 | 9.89743219e-07 |
| any_gt1000 | full-sample descriptive, not OOF | True | 30.39841674 | 30.39825817 | -0.0001585741574 | 0.2439300396 | 0.2439244323 | -5.607275527e-06 | 0.00731295591 | 0.007313017071 | 6.11614891e-08 | 5701.566802 | 5701.566802 | -1.017479008e-07 | 1.407478979e-08 | 3.331359665e-06 |
| wthr_gt0 | full-sample descriptive, not OOF | True | 23.12473419 | 23.12474273 | 8.543743938e-06 | 0.3301007487 | 0.3301010279 | 2.791524543e-07 | 0.03356977874 | 0.03356976867 | -1.006910303e-08 | 22566.34444 | 22566.34444 | -4.365574569e-10 | -7.196782686e-09 | 5.256321162e-07 |
| wthr_gt5 | full-sample descriptive, not OOF | True | 24.24390037 | 24.24394421 | 4.384121299e-05 | 0.3212363618 | 0.3212371996 | 8.378296582e-07 | 0.02386073491 | 0.02386076219 | 2.728852732e-08 | 17494.49738 | 17494.49738 | -1.363150659e-08 | -9.863819551e-09 | 2.379427194e-06 |
| wthr_gt100 | full-sample descriptive, not OOF | True | 25.3656927 | 25.36569868 | 5.974248875e-06 | 0.2902434 | 0.2902435693 | 1.692824729e-07 | 0.01315523376 | 0.01315522956 | -4.203088022e-09 | 10993.22901 | 10993.22901 | -1.291482477e-10 | -2.759474663e-09 | 3.582014885e-07 |
| wthr_gt1000 | full-sample descriptive, not OOF | True | 31.7936854 | 31.79369036 | 4.966538715e-06 | 0.2706231565 | 0.2706232893 | 1.327583992e-07 | 0.001428751834 | 0.00142875085 | -9.838812746e-10 | 1862.890056 | 1862.890056 | -6.593836588e-11 | -4.093734672e-11 | 8.786566758e-08 |

CSV保留17位有效数字；NA为来源未提供或不适用，不填作零。来源见本附录manifest中的requirement_id。
