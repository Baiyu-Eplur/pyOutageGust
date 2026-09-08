# 生产代码变更记录｜R03

本轮新实现版本R03_production_v1，完整身份见R03/CODE_MANIFEST.json；不是对原研究脚本的原地补丁。修改前原代码身份及冻结副本见R03/frozen/PROJECT_SOURCE_MANIFEST.json。旧源码与新源码的职责映射见R03/PRODUCER_CONSUMER_MAP.md。

|新增实际代码|具体改变及目的|
|---|---|
|R03/cli.py|本地复制解释器/依赖校验；accept/test/smoke/formal显式入口；R04需额外执行开关和匹配代码身份；记录实际模块路径|
|src/producer.py|R02 manifest/表SHA与版本验证；step0候选、step2共同fold；共享OOF训练/评价；版本化模型发布；无H0回退|
|src/contracts.py|UTC日期5折、all_valid/备选主训练p99、部分标准化、加性日历、共同变量块、满秩OLS档案、η预测、pooled/mean-fold和配对增量|
|src/prediction.py|取消double-log；原变量先行的场景/参考平均；最低点条件字段且无旧区间；风暴联合成员与逐事件预测身份；图4/7指定归档消费者|
|src/diagnostics.py|重建完整设计VIF、LAD/date/双向CR1、公共分箱阶段组成与raw ln(n_stages)收尾|
|src/retained.py|图6共同日历与冻结人口数据；图10各期自身尺度/物理气压转换，秩亏分支隔离|
|src/run_pipeline.py|smoke和未来formal共用的真实执行链；目标盲选smoke；归档再读取后生成图4/7数据；独立输出，无旧图回填|
|src/acceptance.py|复用R02证据的输入接收、互斥样本归因、时区/风暴、LAD来源、冻结fold和配置；不是新天气扫描|
|src/test_pipeline.py|17项针对性合成/输入/小样本检查；保存失败及通过日志|
|code/r03_prepare.py、r03_release_checks.py、r03_isolation_check.py|一次性复制依赖与初始化；仅矩阵的完整候选支持检查/配置冻结；原文件、运行库和状态差异审查。不是正式分析入口|

新增代码从无到有，发布patch文件R03/code_changes/new_production.patch记录所有新生产源的完整新增文本。冻结历史源码不执行；R02独立代码保持原样。旧combined→dev/holdout→v9及旧figures/raw目录均不接管。

修复过程记录：smoke_v1为初始核心连通成功；扩展stage/period后的v2在后期年月秩亏停止；v3显式隔离后成功；v4补齐归档消费者和逐行版本、时期训练身份后重跑17项测试与720事件smoke成功。它们是同一开发工作的迭代，不是重复独立科学验证。旧的失败日志不删除。

导入测试的早期失败来自Windows标准库平台探测，修订了测试范围说明后通过；未靠允许研究模块写旧文件解决。原LOG同期追加另见final_isolation.json，原日志内容保留，未自动回滚。

保留的H0数值输出不再满足修正输入身份，继续作为历史。当前smoke也不是B1。正式图表/附录所有保留数值必须从后续指定版本生成，暂缺新生产者的分支保持未生成。
