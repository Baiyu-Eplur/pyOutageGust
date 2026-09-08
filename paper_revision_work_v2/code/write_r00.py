import json,csv,re
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent
def put(p,s):(O/p).write_text(s,encoding='utf-8')
items=json.loads((O/'inventory/audit_acceptance.json').read_text(encoding='utf-8'))
put('inventory/AUDIT_ACCEPTANCE.md','# R00 审计接收表\n\n2026-09-05；42 个文件逐一读取；CSV 全记录解析、JSON 全文解析、报告全文读取。数值结论仍属于 H0；本轮接收不冒称再次拟合。逐文件字节数、哈希、结构及完整路径见 audit_acceptance.json。旧清单所列项全部哈希一致。\n\n|文件|记录/结构|证据来源|复用范围|\n|---|---|---|---|\n'+'\n'.join(f"|{Path(x['path']).name}|{x.get('rows',x.get('characters_read','JSON'))}|verified_from_artifact|H0；修正输入后不直接用于当前结论|" for x in items)+'\n\n大数据 SHA 本轮各重算一次并与 H0 相符，之后阶段复用 large_input_identity.json，先检查大小及 mtime；如变动再哈希。当前未重跑 80 折拟合。\n')
put('inventory/VERSION_AND_RUNTIME.md','''# 版本与运行环境

实际根目录 `D:\\Pyprogramme\\STST2603\\claude_branch`；用户路径中的下划线转义/目录分隔按已存在目录解析。无适用 AGENTS.md。Git rev-parse 确认这里及父目录不是 Git 仓库；没有可报告的未提交 diff。本次建立 91 个逐文件哈希一致源码副本，源和副本映射见 source_snapshots.json；未来修复逐文件留补丁，不创建或迁移 Git。

旧审计监测的 549 个文件无变化，不代表未受监测文件也被全面审计。两份本地最新稿与交接包 supplied_manuscripts 的 SHA256 一致，详见 manuscript_versions.json。研究输入 raw/v3 与 H0 一致。

解释器：`C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe`，3.12.14。以 `-B` 启动，在任何科学库导入前令 `sys.dont_write_bytecode=True` 并前置 `D:\\Pyprogramme\\STST2603\\.venv\\Lib\\site-packages`。已实际导入 numpy 2.4.3、pandas 3.0.1、scipy 1.17.1、statsmodels 0.14.6、sklearn 1.8.0。原 .venv 启动器引用不存在的 Python，不使用该启动器、不重装。详细运行方式在 code/r00_intake.py。

只导入已知科学依赖，没有导入历史研究模块。`-B` 不能防止其他副作用。运行时/版本核验不等于全部未来地理或绘图依赖已验证。
''')
put('inventory/WRITE_SCOPE.md','''# 写入与保护范围

本轮唯一输出根：`D:\\Pyprogramme\\STST2603\\claude_branch\\paper_revision_work_v2`。code 为本轮核查代码及冻结快照，checks 为针对性数据核查，inventory/contracts/reports 为接收、规则和反馈。R00/R01不生成修正模型、派生正式样本或新天气请求。

受保护：父目录 data/、rebuild_v3_full_stage/（数据、脚本、日志）、旧天气 pkl/SQLite、分支既有 scripts/ 和 results/、docs/、所有论文 Word/Markdown、LOG.md、handoff 包。R02/R03 按后续授权将活动代码接入统一新入口；此前只保存快照。不得直接执行写死旧输出路径的历史生产者。

准备下一阶段入口：显式传入 raw/v3/cache、output_root、run_id、baseline_config；读取天气仅用 cache-only 适配器，禁止 CachedSession；统一 event table 作为所有消费者唯一样本入口；每次写入验证 resolve 后位于本轮根；保留输入 SHA/源行ID/排除理由。当前尚未实现这些修复接口。

保护证据：checks/protected_files_start.json；阶段结束增量重验相同549文件并验91源码来源/副本。原始大文件本轮已重算哈希，结束仅复核size/mtime，不重复1GB扫描；缓存针对本轮实际读取文件校验。
''')
put('inventory/ACTIVE_PIPELINE.md','''# 当前保留内容的生产链

所有相对 scripts 路径均相对于 `D:\\Pyprogramme\\STST2603\\claude_branch`；外部路径均相对于 `D:\\Pyprogramme\\STST2603`。源码绝对路径/哈希/副本见 source_snapshots.json；定位锚点见 active_source_locations.txt。以本地最新Word提取的图注和附录结构反查，并非以文件名final判定证据。

|当前内容|生产者与共享函数|输入及写入/风险|迁移要求|
|---|---|---|---|
|表1/样本流/图1–3|final_combined_analysis/combined_sample_builder.py；figure1*、figure2*、figure3*|dev clean_sample_builder→holdout build_holdout_sample→v3_validation/v3_validation_pipeline.py read/prepare/build；v3→first drop_duplicates；固定results写入|事件时间、年月、天气、成员全部依赖新输入；图3为历史流程标签|
|表2–3/附录F回归|step1_final_fit.py；v9 build_design_matrix；critical_wind_speed拟合公共函数|log1p(C)/log(B)；LAD聚类；step28两向协方差输出缺独立生产者|恢复明确协方差生产入口，禁止只复用旧表|
|图4阵风曲线/最低点|step2_critical_wind_and_variance.py、step3_dose_response_curve.py、figure4*、step43_M01_M03_M05.py|均值设计向量；旧图硬编码最低点区间；Bootstrap重标化|参考人群接口；旧区间停止回填|
|表4贡献/图8原因组比较|step2*、step17_weather_natural_subsample.py；variance_decomposition/variance_decomposition_pipeline.py|日期GroupKFold；pooled OOF R²；主/天气各自p99和fold|相同基础目标/日期fold；保留逐事件预测及逐折指标|
|图5客户曲线|step7_customers_dose_response.py、figure5*|均值设计；客户平方要连动|按同一参考人群完整设计后平均|
|图6地图/图7相对比|step4_baseline_regional_map.py、figure6*、figure7*|地图客户z及z²均置0，曲线mean(z²)不为0|地图具体情景、曲线人群平均，分别命名|
|图9风暴与指标|step10_named_storms.py、step13_storm_prediction_check.py、figure9_storm_validation.py|暴露log1p(expη)；恢复混合训练及p99外；重叠窗口|η对应log1p(C)；成员身份/重叠唯一事件|
|图10历史时段比较|dev/module_e各自fit、figure10*|后期自己拟合；各自scale/p99；旧CV汇总SE|只作回顾比较；不声称独立验证|
|附录A/B|v3 build_stage_base_v3.py→weather_cached_chunk_v3.py→combine→enrich→restore；历史重构核验|C/A/B；时区；原始source_row_number；IMD/GVA借用旧主表|数据字典与本轮contract一致|
|附录C|step36_six_group_clean_sample.py|六组独有样本/截尾/折分|保留历史身份；新对照统一配置|
|附录D/图D1|customer_duration*历史阶段分析、step42_appendixD_composition_crosstab.py、figureD1*|开发样本D1/D2和合并D1图不同；step27最终阶段结果缺独立入口|样本显式，恢复阶段诊断生产者|
|附录G/H及GLM/三阶线索|step21_causecode_gust_diagnostic.py、step40_model_form_check.py、step40_1_cubic_gust_term.py、step43*|支持范围/替代形式/Bootstrap旧输入|当前保留结果需要重新生成；不删E0三阶反向线索|

关键公共写入：v9模块顶层RAW_DIR.mkdir，read_v3_incidents/样本构建可写固定JSON；combined/dev/holdout一路调用不能当纯读取。外部weather_cached_chunk通过exec_module导入main1_v3，后者顶层CachedSession可能写父目录SQLite。大量figure脚本写旧figures路径，审查原文收窄不保证旧脚本已同步。缺少独立生产者的step26 VIF、step27阶段、step28协方差交R03补齐；本轮不伪称已恢复。
''')
loc=[]
for p in sorted((R/'scripts/final_combined_analysis').glob('*.py')):
    for i,l in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if re.search(r'^def |^from |OUT_DIR|RAW_DIR|savefig|write_text|to_csv',l):loc.append(f'{p}:{i}: {l}')
put('inventory/active_source_locations.txt','\n'.join(loc))
put('reports/R00_report.md','''# R00 完成报告

日期：2026-09-05。执行状态 completed；证据接收通过，修复尚未开始。用户本轮同时指定R00–R01，因此完成本阶段后按依赖进入R01，不进入R02。

42份旧审计产物已实际读取；旧manifest列项全部哈希一致。549个受监测历史文件无变化。原始237901阶段/135025事件及1.084GB v3文件本轮分别计算一次SHA，与H0完全一致。最新稿两份Word与交接包版本一致。91个相关源码逐文件快照并核验；无Git，不推断是否存在更早未保存编辑。科学依赖环境已实际导入成功，没有import历史研究模块。

复用H0：主E0 60437、主R0c 59834；天气E0 9857、天气R0c 9758。原C/A/B计算一致、旧系数和OOF可复现、主矩阵满秩均接受为旧证据。本轮没有重新拟合。C01旧主E0代表时间较晚8199例（13.566%）；C03天气恢复独立p99多排48例；C04暴露风暴显示尺度多做log1p；C06只标准化天气/客户；C07两类参考设计不同；C08旧图会回填撤回内容；C09存在导入副作用/缺生产者。

交付：inventory/AUDIT_ACCEPTANCE.md、ACTIVE_PIPELINE.md、VERSION_AND_RUNTIME.md、WRITE_SCOPE.md及对应机器清单。C/T/L导入ISSUE_LEDGER；状态区分证据、执行、修复。R01需要处理源时间/业务起始、4506.37小时极端记录、并列和原因冲突、天气有效值/产品来源、区域crosswalk、恢复总体及图形情景。

限制：哈希一致说明版本相同，不是再次独立科学验证；未运行旧80拟合、Bootstrap、天气请求或修正模型。受保护范围外的历史脚本不作全面正确性认证。R00所需前置条件已具备。
''')
state=json.loads((R/'paper_revision_handoff_v2/templates/RUN_STATE.json').read_text(encoding='utf-8-sig'))
state.update(active_stage='R01',baseline='H0_verified_from_artifact',project_root=str(R),last_updated='2026-09-05')
state['stages']['R00'].update(execution_status='completed',report='reports/R00_report.md',inputs=['results/code_audit_20260905'],outputs=['inventory/'])
state['stages']['R01']['execution_status']='running'
put('RUN_STATE.json',json.dumps(state,ensure_ascii=False,indent=2))
put('STATUS.md','# 当前状态\n\nR00 completed；R01 running；R02及之后not_started。H0冻结；未生成R1/B1。\n')
print('R00 reports and state written')
