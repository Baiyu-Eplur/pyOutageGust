# 活动生产者—消费者表

版本 R03_production_v1。项目源引用均来自 frozen/project_sources；94 份源文件为参考副本，实际执行为 src 下的新实现。当前运行证据 R03_smoke_v4（non_inferential_smoke）；R04 配置已冻结、未执行。

|保留内容|输入/配置与生产函数|新输出/消费者|状态和限制|
|---|---|---|---|
|事件与候选、表1人数依据|R02 指定 manifest/SHA；producer.load_events、step0_build_sample；acceptance.run|acceptance/*.csv、tables/R03_INPUT_ACCEPTANCE.md；样本节|定向对账已跑；正式模型 n 仍从各运行产生，不能替换旧系数表 n|
|日期折分|共同候选；producer.step2_build_folds→contracts.global_date_folds|folds/date_to_fold.csv、成员表；run_oof|已冻结 5 折；所有主/天气目标共用|
|主/天气 E0、R0c 全拟合；表2–3、附录F|R04_primary；run_pipeline.run→fit_ols|各 group_target/full_model.json、cluster_covariance.json|主组小样本通过；四组合完整训练设计已检查，无正式四模型；论文表排版未生成|
|表4、图5/8 贡献|同人群 control/G/K/GK OOF；producer.run_oof/publish_oof|oof_*.csv、metrics.json、contributions.json；指定新 JSON 消费者|接口及主组 smoke 通过；主/天气分母分别声明；未生成正式图|
|图4曲线与最低点|指定 full_model.json；prediction.figure4_data、minimum_interface|figure4_curve_data.csv、figure4_reference.json、conditional_minimum_no_CI.json|新归档消费通过；无 CI，最终图形渲染未生成|
|图6地区参考|指定归档、冻结人口副本、R02 区域列；retained.figure6_data|figure6_regional_reference.csv、figure6_reference.json|新数据生产已试跑；proxy/缺年/跨版未决保留；地图几何及最终渲染未生成|
|图7范围比/客户曲线|指定归档；prediction.figure7_data|figure7_gust_ratio.json、figure7_customer_curve.csv、figure7_reference.json|50点参考网格指数比保存；最终图未生成|
|图9风暴|R03/configs/storm_windows.json、指定全拟合/OOF归档；prediction.storm_event_predictions|figure9_descriptive_events.csv、figure9_OOF_diagnostic_events.csv|版本/尺度/模型身份逐行；无真正过程留出；最终图未生成|
|图10分期|当前成员按既定分期；retained.period_comparison|figure10_period_physical_terms.csv、可用 period_*_model.json|开发期 smoke 可用；后期编码秩亏明确 blocked；无旧 CV 区间|
|step26 VIF|完整新设计；diagnostics.vif_table|VIF.csv、VIF_manifest.json|最小生产者重建并验证；旧 step21 写的 step26_full_summary.json 是 gust/cause 诊断，不是 VIF 生产者|
|step27 阶段收尾|冻结 step5_n_stages_stratification.py 与旧27报告的方法；diagnostics.stage_closure|step27_model_*.json、step27_stage_coefficients.csv、step27_single_stage_bins.csv、manifest|原独立生产者未找到；定义可恢复，明确重建；旧 n=9,806 未重现为当前事实|
|step28 聚类|旧28说明及冻结 statsmodels；diagnostics.covariance_producer|cluster_covariance.json|原独立生产者未找到；重建 LAD/date/双向 CR1；合成数值核对通过|
|附录D/图D1|当前恢复成员；diagnostics.stage_composition|stage_composition.csv、stage_pooled.csv、stage_manifest.json|公共客户箱/阶段箱描述已小试；最终图未生成|
|图1–3及正文表排版|R02 主表、R03 人数/配置；旧源码已复制供定义参考|未来独立渲染器|暂不生成；旧绘图脚本不导入，需新消费者指定版本后才能发图|
|附录A/B/C/E/F/H方法依据|冻结输入契约、R03/CONTRACTS.md、输入对账、模型/评分身份|R03_WRITING_IMPACT.md 的待写决策|未修改 Word；六原因组、附录C六组对照没有冒充四候选分析|
|附录G/H GLM、三阶、替代形式、科学形状及区间|冻结历史源码/线索|尚无合格新版本产物|本轮未迁移/未执行；在 R04 保留项审定或 V 相应实验中另建独立入口，不引用 H0 充当新结果|

原链定位：combined_sample_builder → dev clean_sample_builder / holdout build_holdout_sample → 原 v9 read/prepare/build。顶层 mkdir、固定输出路径及历史动态导入存在写入风险，因此保留原链只读，按用户授权改由以上新入口实现同研究所需接口。源位置与修改前哈希见 frozen/PROJECT_SOURCE_MANIFEST.json；旧内容反查依据是 frozen/evidence/ACTIVE_PIPELINE.md。

所有新图目前交付的是可追溯的数据/参考接口及 smoke 数据，未宣称已重画论文图。绘图需要绑定新 run_id；require_result 对缺件、错版本和未经允许的 smoke 直接停止。
