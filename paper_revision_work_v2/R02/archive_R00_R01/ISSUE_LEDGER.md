# C/T/L问题总账

执行completed仅指表中本轮范围完成；repair_status=rule_defined不是code_patched或recomputed。未关闭科学问题。C01–C09/T01–T14/L01–L12完整保留，C10为本轮新增。逐行结构见issue_ledger.json。

|编号/主题|关联|执行范围/状态|修复状态|证据来源|证据/余项|
|---|---|---|---|---|---|
|C01 代表阶段时间|T02/T03/T07/T08；L02/L03/L05/L08|R00/R01 definition/intake only / completed|rule_defined|reproduced_this_run|checks/event_semantic_checks.json；contracts/DATA_CONTRACT.md；R02/R04重算|
|C02 pooled与mean-fold|T06/T07/T09/T14；L07/L10/L12|R00/R01 definition/intake only / not_started|rule_defined|verified_from_artifact|H0 oof_metric_comparison.csv；BASELINE_SPEC；R03/R04评分与图件|
|C03 独立p99/成员/fold|T04/T06/T07；L04/L07/L08/L11|R00/R01 definition/intake only / not_started|rule_defined|verified_from_artifact|H0 source_and_sample_checks.json；BASELINE_SPEC；R03/R04共同口径|
|C04 暴露多log1p|T09/T14；L10/L12|R00/R01 definition/intake only / not_started|rule_defined|verified_from_artifact|H0 storm_exposure_scale_audit.csv；BASELINE_SPEC；R03修代码/R04重算|
|C05 风暴训练成员与窗口|T04/T07/T09；L04/L08/L10|R00/R01 definition/intake only / not_started|open|verified_from_artifact|H0 storm_recovery_membership_audit.csv；R03/R04成员接口；V过程留出|
|C06 部分标准化|T01/T11/T14；L01/L12|R00/R01 definition/intake only / completed|rule_defined|verified_from_artifact|H0 full_fit_summary.csv；FIELD_PROVENANCE；R03统一变换字典|
|C07 图形参考与反变换|T09/T14；L10/L12|R00/R01 definition/intake only / completed|rule_defined|verified_from_artifact|H0 curve_reference_audit.json；FIGURE_REFERENCE_CONTRACT；R03/R04实际接入|
|C08 旧区间/标签回填|T10/T11/T14；L09/L12|R00/R01 definition/intake only / not_started|open|verified_from_artifact|冻结figure4/figure10/step43源码与H0报告；R03关闭旧回填；V03条件区间|
|C09 副作用/环境/缺生产者|T01/T03/T11/T14；L01/L05/L12|R00/R01 definition/intake only / completed|rule_defined|reproduced_this_run|inventory/runtime_verified.json；ACTIVE_PIPELINE；运行边界已定义，R03补生产者|
|C10 Buck旧区简单均值proxy|T01；L01|R00/R01 definition/intake only / completed|rule_defined|reproduced_this_run|checks/buckinghamshire_lineage.json；D03；按作者保留代理、后续LSOA重建对照|
|T01 区域源定义及VIF|C06,C09,C10|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|T02 气象产品/时间匹配|C01|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|T03 事件与特殊阶段|C01,C09|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|T04 长尾敏感性|C03,C05|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T05 非线性形状||future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T06 配对贡献稳定性|C02,C03|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T07 完整过程留出|C01,C02,C03,C05|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T08 信息时点|C01|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|T09 工程场景/误差|C02,C04,C05,C07|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T10 条件最低点区间|C08|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T11 诊断及既有材料|C06,C08,C09|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T12 可选异质性增强||future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T13 可选扩大用途||future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|T14 文稿整合|C02,C04,C06,C07,C08,C09|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L01 区域变量矛盾|C06,C09,C10|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|L02 气象/结构风解释|C01|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|L03 事后客户信息|C01|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|L04 最长1%与极端叙事|C03,C05|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L05 后果工程语义|C01,C09|R01 definition part only / completed|rule_defined|verified_from_artifact|contracts/ + H0 artifacts；科学缺口未整体关闭；按R/V/W阶段执行|
|L06 二次充分性||future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L07 排序反转稳定性|C02,C03|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L08 风暴依赖|C01,C03,C05|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L09 最低点区间条件|C08|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L10 风暴误差/校准|C02,C04,C05,C07|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L11 原因/支持/异质性|C03|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|
|L12 全文证据一致性|C02,C04,C06,C07,C08,C09|future experiment/review / not_started|open|reported_by_local_audit|handoff ISSUE_MAP and historical review; not a new experiment；科学缺口未整体关闭；按R/V/W阶段执行|

全局缺失清单见UNRESOLVED_DEFINITIONS；这些源真值的证据来源为not_available，不能用程序一致替代。T01精确共线旧猜测已排除，不删除该历史问题，也不预设删gap。
