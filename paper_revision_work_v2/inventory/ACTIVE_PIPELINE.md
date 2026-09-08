# 当前保留内容的生产链

所有相对 scripts 路径均相对于 `D:\Pyprogramme\STST2603\claude_branch`；外部路径均相对于 `D:\Pyprogramme\STST2603`。源码绝对路径/哈希/副本见 source_snapshots.json；定位锚点见 active_source_locations.txt。以本地最新Word提取的图注和附录结构反查，并非以文件名final判定证据。

|当前内容|生产者与共享函数|输入及写入/风险|迁移要求|
|---|---|---|---|
|表1/样本流/图1–3|final_combined_analysis/combined_sample_builder.py；figure1*、figure2*、figure3*|dev clean_sample_builder→holdout build_holdout_sample→v3_validation/v3_validation_pipeline.py read/prepare/build；v3→first drop_duplicates；固定results写入|事件时间、年月、天气、成员全部依赖新输入；图3为历史流程标签|
|表2–3/附录F回归|step1_final_fit.py；v9 build_design_matrix；critical_wind_speed拟合公共函数|log1p(C)/log(B)；LAD聚类；step28两向协方差输出缺独立生产者|恢复明确协方差生产入口，禁止只复用旧表|
|图4阵风曲线/最低点|step2_critical_wind_and_variance.py、step3_dose_response_curve.py、figure4*、step43_M01_M03_M05.py|均值设计向量；旧图硬编码最低点区间；Bootstrap重标化|参考人群接口；旧区间停止回填|
|表4贡献/图8原因组比较|step2*、step17_weather_natural_subsample.py；variance_decomposition/variance_decomposition_pipeline.py|日期GroupKFold；pooled OOF R²；主/天气各自p99和fold|相同基础目标/日期fold；保留逐事件预测及逐折指标|
|图5贡献分解|figure5_variance_decomposition.py；step2_critical_wind_and_variance.py|嵌套顺序增量与pooled OOF，标签仍称mean|统一评分成员/分母与命名|
|客户曲线及图7客户范围|step7_customers_dose_response.py|均值设计；客户平方要连动|按同一参考人群完整设计后平均|
|图6地图/图7相对比|step4_baseline_regional_map.py、figure6*、figure7*|地图客户z及z²均置0，曲线mean(z²)不为0|地图具体情景、曲线人群平均，分别命名|
|图9风暴与指标|step10_named_storms.py、step13_storm_prediction_check.py、figure9_storm_validation.py|暴露log1p(expη)；恢复混合训练及p99外；重叠窗口|η对应log1p(C)；成员身份/重叠唯一事件|
|图10历史时段比较|dev/module_e各自fit、figure10*|后期自己拟合；各自scale/p99；旧CV汇总SE|只作回顾比较；不声称独立验证|
|附录A/B|v3 build_stage_base_v3.py→weather_cached_chunk_v3.py→combine→enrich→restore；历史重构核验|C/A/B；时区；原始source_row_number；IMD/GVA借用旧主表|数据字典与本轮contract一致|
|附录C|step36_six_group_clean_sample.py|六组独有样本/截尾/折分|保留历史身份；新对照统一配置|
|附录D/图D1|customer_duration*历史阶段分析、step42_appendixD_composition_crosstab.py、figureD1*|开发样本D1/D2和合并D1图不同；step27最终阶段结果缺独立入口|样本显式，恢复阶段诊断生产者|
|附录G/H及GLM/三阶线索|step21_causecode_gust_diagnostic.py、step40_model_form_check.py、step40_1_cubic_gust_term.py、step43*|支持范围/替代形式/Bootstrap旧输入|当前保留结果需要重新生成；不删E0三阶反向线索|

关键公共写入：v9模块顶层RAW_DIR.mkdir，read_v3_incidents/样本构建可写固定JSON；combined/dev/holdout一路调用不能当纯读取。外部weather_cached_chunk通过exec_module导入main1_v3，后者顶层CachedSession可能写父目录SQLite。大量figure脚本写旧figures路径，审查原文收窄不保证旧脚本已同步。缺少独立生产者的step26 VIF、step27阶段、step28协方差交R03补齐；本轮不伪称已恢复。
