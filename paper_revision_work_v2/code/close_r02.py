"""Protection audit and R02-only handoff assembly. No scientific estimation."""
import sys,json,hashlib,datetime,shutil
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;Q=O/'R02'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def protection():
    before=json.loads((Q/'checks/protected_before.json').read_text(encoding='utf-8'))
    changed=[];missing=[]
    for p,h in before.items():
        if not Path(p).exists():missing.append(p)
        elif sha(p)!=h:changed.append(p)
    allowed=R/'scripts/v3_validation/v3_validation_pipeline.py'
    assert not missing and set(map(Path,changed))=={allowed},(changed,missing)
    original=json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8'));large=[]
    for x in original:
        p=Path(x['path']);actual=sha(p)
        assert actual==x['sha256'] and p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns']
        large.append({'path':str(p),'sha256':actual,'full_hash_unchanged':True})
    pop=json.loads((Q/'checks/population_connection.json').read_text(encoding='utf-8'));assert sha(pop['path'])==pop['sha256']
    cache=R.parent/'data/weather_request_cache';cb=json.loads((Q/'checks/cache_inventory_before.json').read_text(encoding='utf-8'))
    after={p.name:[p.stat().st_size,p.stat().st_mtime_ns] for p in cache.glob('*.pkl')}
    assert cb==after,'Historical cache directory inventory changed'
    sys.dont_write_bytecode=True;sys.path.insert(0,str(R.parent/'.venv/Lib/site-packages'))
    import pandas as pd
    w=pd.read_parquet(Q/'data/weather_key_hour_audit.parquet').drop_duplicates('request_key')
    read=w[w.cache_sha256.notna()];n=0
    for row in read.itertuples(index=False):
        assert sha(row.cache_file_path)==row.cache_sha256,row.cache_file_path
        n+=1
        if n%10000==0:print(f'Post-run cache hash comparison {n}/{len(read)}',flush=True)
    oldmanifest=json.loads((Q/'archive_R00_R01/ARTIFACT_MANIFEST.json').read_text(encoding='utf-8'))
    mutable={'RUN_STATE.json','STATUS.md','DECISIONS.md','ISSUE_LEDGER.md','issue_ledger.json','RETURN_TO_CHATGPT.md'}
    untouched=[]
    for x in oldmanifest['files']:
        if x['relative_path'] not in mutable:
            assert sha(x['path'])==x['sha256'],x['path'];untouched.append(x['path'])
    evidence={'passed':True,'protected_files':len(before),'unchanged_protected_files':len(before)-len(changed),'authorized_active_source_changed':changed,'missing_protected_files':missing,'large_inputs_full_hash_verified':large,'population_full_hash_unchanged':True,'historical_cache_directory_files':len(cb),'cache_size_mtime_inventory_unchanged':True,'requested_read_cache_files_full_hash_verified':n,'prior_artifacts_unchanged_excluding_declared_state_updates':len(untouched),'new_network_requests':0,'models_run':0,'manuscripts_modified':0}
    save(Q/'checks/protection_after.json',evidence);print('All protection checks passed',flush=True)
def close():
    n=json.loads((Q/'checks/report_numbers.json').read_text(encoding='utf-8'));checks=json.loads((Q/'checks/targeted_checks.json').read_text(encoding='utf-8'));protection=json.loads((Q/'checks/protection_after.json').read_text(encoding='utf-8'));shuffle=json.loads((Q/'checks/full_shuffle.json').read_text(encoding='utf-8'));assert checks['passed'] and protection['passed'] and shuffle['passed']
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();c=n['all_event_changes'];scan=n['weather_scan']
    def table(rows,keys):return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(str(x[k]) for k in keys)+' |' for x in rows)+'\n'
    members=table(n['membership'],['sample','H0','R02_candidate','common','enter','exit','strict_cache_candidate','conditional_v3_only'])
    buck=table(n['Buck'],['sample','H0_Buck','R02_Buck','R02_Buck_strict'])
    c10='''C10 原编号与标题：**Buck旧区简单均值proxy**；关联 T01、L01。根因是 Buckinghamshire 合并脚本对四个旧 LAD（E07000004–E07000007）索取 2021 人口时未找到旧码行，进入简单平均分支，将旧区 rate/gap/Moran 的均值作为 E06000060 的输入。证据：`checks/buckinghamshire_lineage.json` 的 oldcode_2021_population_rows=0、`checks/buckinghamshire_original_indicators.csv`、H0 冻结 `Buckinghamshire_combination.py` 和 GVA crosswalk 源码。源工作簿 SHA256 为 `6eb516a87654078ee69d4df55c8bc749b5da5de117f996f262c0c762bc20b38f`。本轮严格保留 .06325/.1875/.30，以 `regional_proxy_flag`、`legacy_arithmetic_crosswalk` 标记；这是已授权的历史代理，尚未重建合并区真值。gap 保持比例单位，普通 LAD 的定义是区域内 LSOA rate 极差；旧极差的平均不等于合并极差，旧 Moran 的平均不等于合并区 Moran。后续以匹配年份、边界、收入分子分母及空间权重进行 LSOA 重建并对照，未执行、未关闭科学问题。'''
    unresolved='''仍未决：真实业务 onset 与日历；两个事件的版本/ID 业务关系；历史气象 model、gust 的具体时间语义及响应单位 metadata；Buckinghamshire 真值与 Moran 权重；LAD21/23 同码的完整边界兼容；停钟/视同恢复、真实客户与阶段完整性。UTC 是 R01 冻结分析日历，Europe/London 并列结果用于暴露边界差异。全量缓存可用性检查已经完成，但缺失缓存和产品证据不会因完成扫描而消失。上述限制进入后续解释和敏感性分析，不能用程序一致性替代源业务证据。'''
    report=f'''# R02 事件与时间相关输入修复报告

版本：{n['run_id']}；生成时间：{now}。本轮按用户“按该文件执行”授权，承接 R00–R01，仅完成 R02；未重跑 H0 四模型/80 折拟合，未估计 B1、未修改论文、未开始 R03/V/W。

## 1. 完成状态及关键结果

规则明确（限可执行代理口径）→代码已修→输入已重建→针对性检查通过；模型尚未重估。{n['stages']:,} 条完整阶段记录形成 {n['events']:,} 个唯一事件；代表 UTC 时刻改变 {c['UTC时刻']:,}，天气小时改变 {c['UTC小时键']:,}，UTC 日期改变 {c['UTC日期']:,}，年份改变 {c['UTC年份']}，月份改变 {c['UTC月份']}，开发/后期/窗外改变 {c['开发/后期/窗外']}，原因组改变 {c['原因组(旧首行→全阶段共识)']}，人口值或缺失状态改变 {c['人口数值或缺失状态']}。C/D 全事件容差检查零差异，不能将这些结果表述为模型或科学结论已验证。

{members}
R02_candidate 是全有效尾部的输入候选，含明确标记的 v3-only 条件来源；strict_cache_candidate 表示小时、数值及窗口已核查，仍有历史产品限制。恢复成员增加包含尾部口径改变，不能都归因于时间修复。`tables/R02_SAMPLE_FLOW.md` 另列旧首行原因/独立 p99 的 R1_compat 候选诊断、固定顺序排除、转移原因及质量标记；未生成 R1 模型。

## 2. 实际入口与可追溯字段

修改了 `scripts/v3_validation/v3_validation_pipeline.py::step0_build_sample`，这是 combined → dev/holdout → v9 的共享入口。现在读取并校验 `R02/data/EVENT_MANIFEST.json` 对应主表，不再按原行序选代表阶段；缺文件或哈希不一致会失败，不退回 H0。删除 v9 导入时 mkdir；step1 在 R02 下只核查已生成 LAD 覆盖；step2 遇到 R02 明确停止，等待 R03 修复 fold/tail 接口。本轮没有修好所有旧生产脚本或运行图表。

确定性生产者为 `scripts/event_input_repair/r02_events.py`，显式 I/O 运行器为 `code/run_r02.py`（prepare/weather/finish）。raw 原文件在任何排序前标记 1-based source_row_number；稳定源键为 raw SHA256:row。全阶段 UTC 最小时刻并列时以原源行号破同刻，不以天气是否可得选择。24,893 个事件并列，核查 Spatial Coordinates、Cause Code、licence_area、regulatory_year、substation、SiteFunctionalLocation 六项冲突均为 0；不扩大成所有业务属性均无冲突。

原始时间字符串、原偏移、UTC/London 时刻、每事件全源行列表、最早候选行、选中行和旧行均保留。时间取最早有效阶段；天气用选中位置和小时；原因取所有阶段独立共识；人口使用修正 UTC 年份和 LAD→LAD23CD/year 唯一键重关联。业务 onset 留空，首阶段存在不等于已确认真实故障时刻。

研究期为 UTC [2021-04-01 00:00,2024-04-01 00:00)，包括 2024-03-31 全天；后期自 2023-09-30 00:00Z。先用完整阶段计算再筛事件，保留跨研究终点的恢复记录。London 日期、时期和风暴结果并列，详见 `tables/R02_calendar_comparison.csv`、`tables/R02_calendar_boundary_events.csv`；重叠风暴单列 UNIQUE_ANY，不直接相加。

C=sum 非再次中断阶段客户，全部被排除时为空而非零；D=最大恢复结束−最早开始，保持 duration_B 映射；兼容 `Duration (hours)` 仍是 A 加权时长。完整 C 差异 0，D/A 仅机器浮点误差（上限分别约 6.82e−13/1.14e−13 h）。没有按代表行裁掉其他阶段。

## 3. 全量天气核查

可查询事件 {scan['eligible_event_count']:,}，不同最早查询键 {scan['distinct_query_keys']:,}，键×小时 {scan['key_hour_rows']:,}；所需现存文件 {scan['existing_files']:,}。目录原有 75,983 个文件。四天气数值完整事件 {n['weather_numeric_events']:,}，其中缓存小时/窗口检查通过 {n['strict_numeric_events']:,}，仅最早 v3 源行数值可用但窗口无法复核 {n['conditional_v3_numeric_events']:,}。不同分母在 `tables/R02_WEATHER_AVAILABILITY.md` 逐项列明。

检查精确小时唯一性，(t−24h,t] 雨量 24 个唯一完整整点、有限且非负。无 nearest 代用、不补零，不借后续阶段天气。可读缓存无效时保留失败而非用旧值遮盖；缓存缺失时仅保留键、时刻一致的最早 v3 源行，并标记条件来源。数值可用、缓存文件可得、历史产品可确认是三个独立状态。原请求 wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT 为代码依据，缓存响应单位 metadata 未核清，所有记录仍为 historical_model_unresolved；未新抓天气。

## 4. 未决事件、区域与 C10

FREP-338321-Z 与 FREP-314454-J 均完整保留，按原 ID 公式 C/D 可计算但业务身份/原因未决。全阶段原因冲突进入 unresolved，按冻结 R01 规则不进入主原因候选。前者的 4508.933333 h 不称连续 188 天失电；后者同 stage1/unique_identifier 的两记录不作完全重复行删除。天气与年度人口的实际变化及时间线见 `tables/R02_AMBIGUOUS_EVENTS.md` 与原阶段 CSV。

人口 lookup 无重复键，many_to_one 合并保持 135,025 事件。选中 LAD 缺失 5,762，其中 151 有可用查询坐标，尝试同 2021 边界唯一 within 匹配后无新增匹配；没有任意多配或静默借用另一 LAD。新旧坐标、LAD 与区域缺失影响单列。

{c10}

{buck}
## 5. 检查、保护与复现

{checks['unit_tests']} 项针对性测试通过；真实 237,901 源行全量随机重排后，{shuffle['compared_columns']} 个构造字段逐项完全一致。另通过全事件 C/D/A 一致性、两个冲突事件保留与资格、人口唯一键、Buck 精确代理值、严格天气窗口及实际入口主表等值测试。检查发现缺坐标标志和缺失 C 候选资格的 nullable 布尔处理问题，已修为明确 False/缺失原因并复测通过，见 `R02/logs/unit_tests.txt`。

保护清单 {protection['protected_files']} 文件，唯一有意修改为 v9 活动源代码，其余 {protection['unchanged_protected_files']} 哈希一致；raw/v3 再次完整 SHA256 比对一致；人口源一致；75,983 缓存目录文件 size/mtime 清单一致，已读的 {protection['requested_read_cache_files_full_hash_verified']:,} 个请求缓存文件逐一二次 SHA256 一致。稿件、只读依赖与历史结果保持原样。细目见 `R02/checks/protection_after.json`。代码差异、H0 快照和代码身份见 `R02/code_changes/`。

运行环境及包版本见 `R02/checks/runtime.json`；复现命令见 `R02/REPRODUCE.md`。manifest 固定原始/v3 输入、配置、生产者和天气审计身份。旧模型/OOF/图仍保存为 H0，依赖修正输入的结果全部需要后续重算。

## 6. 尚未解决与下一阶段边界

{unresolved}

R03 仍需统一折分/尾部/评分/变换/图形参考和缺失生产入口，R04 才产生修正模型及 OOF。此处仅提供进入下一轮审阅的输入证据，不宣布 C02–C09 或科学主张全部关闭。本轮完成 R02 后停止。
'''
    (O/'reports/R02_report.md').write_text(report,encoding='utf-8')
    ret=f'''# R02 返回摘要

已按指定文件完成 R02：规则明确（限代理口径）、代码已修、输入已重建、针对性检查通过；**模型尚未重估，文稿未修改，R03/V/W 未启动**。

237,901 阶段 → 135,025 唯一事件。UTC 代表时刻改变 {c['UTC时刻']:,}；天气小时改变 {c['UTC小时键']:,}；日期改变 {c['UTC日期']:,}；年份/月分别改变 {c['UTC年份']}/{c['UTC月份']}；时期改变 {c['开发/后期/窗外']}；任一天气值或缺失状态改变 {c['任一天气字段']:,}；原因组改变 {c['原因组(旧首行→全阶段共识)']}；人口改变 {c['人口数值或缺失状态']}。C/D 全事件一致（浮点容差内）。共同/进入/退出分开如下：

{members}
候选恢复总体保留全部有效 D，成员变化不能全部归因于时间修复。旧首行原因/独立 p99 的兼容诊断成员和分项原因另见样本流。

天气全量：{scan['eligible_event_count']:,} 可查询事件、{scan['distinct_query_keys']:,} 个键、{scan['key_hour_rows']:,} 个键×小时，所需现存缓存 {scan['existing_files']:,} 个。数值完整 {n['weather_numeric_events']:,}：缓存小时/窗口已验证 {n['strict_numeric_events']:,}，仅最早 v3 值可用、窗口未复核 {n['conditional_v3_numeric_events']:,}。缓存缺失与数值缺失分别计数；历史 model 仍未决，新请求为 0。

两个原因/身份未决事件保留全部源行及 C/D 公式值，按 R01 不纳入主原因候选，不拆分或去重。最早同刻事件 24,893，六项已检查 metadata 冲突为 0；不是对业务语义的全属性担保。Buckinghamshire 新人数如下：

{buck}
{c10}

实际入口 `scripts/v3_validation/v3_validation_pipeline.py::step0_build_sample` 已读取哈希校验后的 R02 主表；生成器 `scripts/event_input_repair/r02_events.py`。全量源行扰动等值、{checks['unit_tests']} 项针对性测试与实际入口等值检查通过。raw/v3、人口及已读缓存完整哈希保护通过；旧结果、论文未改。旧模型/OOF/图仅保留 H0 身份，修正模型待 R03/R04。

{unresolved}

交付：`reports/R02_report.md`；`tables/R02_SAMPLE_FLOW.md`；`tables/R02_OLD_NEW_SUMMARY.md`；`tables/R02_WEATHER_AVAILABILITY.md`；`tables/R02_AMBIGUOUS_EVENTS.md`；主表 `R02/data/R02_event_master.parquet`（另有 csv.gz）、`EVENT_MANIFEST.json`；四样本 H0_R02 crosswalk；`R02/code_changes/`、`R02/checks/` 与更新后的状态清单。以上相对路径均以 `{O}` 为根。
'''
    (O/'RETURN_TO_CHATGPT.md').write_text(ret,encoding='utf-8')
    ledger=json.loads((O/'issue_ledger.json').read_text(encoding='utf-8'))
    for x in ledger:
        if x['id']=='C01':x.update(execution_status='completed',execution_scope='R02 event/time input only',repair_status='targeted_checks_passed',evidence_source='reproduced_this_run',evidence=x['evidence']+'；R02/checks/active_entry.json；R02/checks/full_shuffle.json；R02/data/EVENT_MANIFEST.json',remaining='R03生成链修复、R04重估；真实onset/业务日历和两ID身份仍未决',repair_milestones={'rule_defined':True,'code_patched':True,'input_rebuilt':True,'targeted_checks_passed':True,'models_reestimated':False})
        if x['id']=='C10':x.update(execution_scope='R02 proxy flag and membership only',repair_status='targeted_checks_passed',evidence=x['evidence']+'；tables/R02_Buck_membership.csv；R02/checks/targeted_checks.json',remaining='历史代理保留已实现；LSOA真值重建与敏感性尚未执行',repair_milestones={'rule_defined':True,'proxy_code_patched':True,'input_rebuilt':True,'targeted_checks_passed':True,'LSOA_rebuilt':False,'models_reestimated':False})
        if x['id']=='C09':x['evidence']+='；R02/checks/active_entry.json（v9导入副作用/入口已处理）';x['remaining']='仅v9输入入口已修；其他旧生产脚本副作用及step26/27/28等生产者交R03，不整体关闭'
    save(O/'issue_ledger.json',ledger)
    lines=['# C/T/L问题总账','', 'R02 completed 仅指输入修复与针对性检查；没有修正模型、OOF 或科学结论已验证的含义。C10 的检查通过仅指已授权历史代理及来源标记，不是新 LAD 真值重建。','', '|编号/主题|关联|执行范围/状态|修复状态|证据|余项|','|---|---|---|---|---|---|']
    for x in ledger:lines.append('|'+ '|'.join(str(v).replace('|','/') for v in [x['id']+' '+x['title'],x['related'],x['execution_scope']+' / '+x['execution_status'],x['repair_status'],x['evidence'],x['remaining']])+'|')
    (O/'ISSUE_LEDGER.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    state=json.loads((O/'RUN_STATE.json').read_text(encoding='utf-8'));state['last_updated']=now;state['baseline']='H0 preserved; R02 input rebuilt; R1/B1 models not run'
    state['stages']['R02'].update(execution_status='completed',report='reports/R02_report.md',inputs=['R02/R00_R01审阅与R02执行指令.md','contracts/','inventory/large_input_identity.json'],outputs=['R02/data/EVENT_MANIFEST.json','R02/checks/','tables/R02_SAMPLE_FLOW.md','reports/R02_report.md'],blockers=[],repair_status='targeted_checks_passed',models_reestimated=False)
    state['invalidated_outputs'][0]['reason']='R02 inputs rebuilt; retained H0 model/OOF/figures are historical and require R03/R04 generation before use with corrected inputs'
    save(O/'RUN_STATE.json',state)
    (O/'STATUS.md').write_text('# 当前状态\n\nR00/R01/R02 completed；当前停在R02返回审阅。R03及以后not_started。规则明确（代理口径）/代码已修/输入已重建/针对性检查通过；模型尚未重估；文稿未修改。\n',encoding='utf-8')
    decisions=(O/'DECISIONS.md').read_text(encoding='utf-8')
    if '## D08：R02验收范围' not in decisions:
        with (O/'DECISIONS.md').open('a',encoding='utf-8') as f:f.write('\n## D08：R02验收范围与候选身份\n\nR02输入及检查完成，尚无B1/OOF重估。候选主恢复采用合同全有效尾部，另列R1旧first原因/独立p99成员诊断；不以恢复旧N为目标。v3-only值按D07保留并明示条件资格；strict只指缓存小时/数值/窗口，不确认历史产品或业务onset。旧下游模型流程在R02入口后停止，由R03处理，不自动启动。C10仅代理实现/来源检查通过，LSOA重建未执行。\n')
    (Q/'REPRODUCE.md').write_text('''# R02 复现与文件身份

在 D:\\Pyprogramme\\STST2603\\claude_branch 中使用已验证 Python：

```powershell
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/run_r02.py prepare
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/run_r02.py weather
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/run_r02.py finish
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/check_r02.py shuffle
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/check_r02.py final
& 'C:\\Users\\haoya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -B paper_revision_work_v2/code/report_r02.py
```

这是显式复现说明，当前交付已经执行完成。run_r02 自动加载父目录 .venv/Lib/site-packages；禁写 pycache，不导入原始联网天气模块。prepare/finish 会更新本 R02 版本的派生文件，开始新科学版本时应先另建 run/output 目录。weather checkpoint 与 pre_weather_events 的 SHA/小时审查函数绑定；不一致会拒绝恢复，不能混用缓存审计结果。原 R02 preflight 是单次归档，不应重复覆盖 R00/R01 快照。close_r02 protection/close 属于验收和交接，不运行模型。

主表保留所有事件；candidate_* 是按合同的全有效候选，strict_candidate_* 另限制可重验缓存，H0_* 为已接收旧成员，R1_compat_candidate_* 为旧原因/独立p99诊断。source_stage_projection 保存全237901条原始20列及所需v3列。wx/地区字段名带 old_ 为旧代表源行，earliest_v3_ 为选中源行既存值；新字段为本轮派生，delta_ 是新减旧。所有源键依赖冻结原始SHA和行号，不能先重排raw后重新生成行号。
''',encoding='utf-8')
    # Frozen copies make the code diff and event manifest independently reviewable.
    for p in [R/'scripts/event_input_repair/r02_events.py',R/'scripts/event_input_repair/test_r02_events.py',R/'scripts/v3_validation/v3_validation_pipeline.py',O/'code/run_r02.py',O/'code/check_r02.py',O/'code/report_r02.py',Path(__file__)]:shutil.copyfile(p,Q/'code_changes'/p.name)
    entries=[]
    for p in sorted(O.rglob('*')):
        if not p.is_file() or p==O/'ARTIFACT_MANIFEST.json':continue
        entries.append({'path':str(p),'relative_path':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'role':'R02_or_retained_prior_artifact'})
    save(O/'ARTIFACT_MANIFEST.json',{'run_id':'R02_20260905','timestamp_utc':now,'root':str(O),'self_excluded':True,'files':entries})
    print(json.dumps({'R02':'completed','manifest_files':len(entries),'models_run':0,'manuscripts_modified':0},ensure_ascii=False))
if __name__=='__main__':
    if (Q/'ISOLATED_ENTRY.json').exists():
        raise SystemExit('This pre-isolation closure is archived. It expects a patched original v9 and would publish stale entry metadata. Use the isolation audit and current RUN_STATE.')
    globals()[sys.argv[1]]()
