"""Copy the user-supplied MR-v1.1 bundle intact, then append R03 evidence/history."""
import json,hashlib,shutil,re,copy,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[1];Q=W/'R03';IN=W/'paper_manuscript_record';OUT=W/'manuscript_record'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
assert not OUT.exists(),'Do not overwrite an existing or later ledger; merge deliberately'
bundle=read(IN/'BUNDLE_MANIFEST.json')
assert bundle['version']=='MR-v1.1'
assert all(sha(IN/x['path'])==x['sha256'] for x in bundle['files'])
original_files=[{'path':p.relative_to(IN).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(IN.rglob('*')) if p.is_file()]
shutil.copytree(IN,OUT)
snap=OUT/'stage_snapshots/MR-v1.1_received_before_R03';snap.mkdir()
for name in ['START_HERE.md','MANUSCRIPT_LEDGER.md','REVISION_ITEMS.json','SOURCE_MANIFEST.json','CHANGELOG.md','BUNDLE_MANIFEST.json','R02_WRITING_IMPACT.md']:shutil.copyfile(IN/name,snap/name)
doc=read(OUT/'REVISION_ITEMS.json');assert len(doc['items'])==29
sources=read(OUT/'SOURCE_MANIFEST.json');assert len(sources['sources'])==17
same=[]
for sid,a,b in [('SRC09','evidence/SRC09_R02_return_20260905.md','frozen/evidence/SRC09_local_R02_return.md'),('SRC10','evidence/SRC10_R02_report_20260905.md','frozen/evidence/SRC10_local_R02_report.md'),('SRC11','evidence/SRC11_R02_review_R03_20260905.md','frozen/evidence/SRC11_R03_instruction.txt')]:same.append({'source_id':sid,'supplied_sha256':sha(IN/a),'local_sha256':sha(Q/b),'byte_identical':sha(IN/a)==sha(Q/b),'interpretation':'retain both identities; identical narrative is not independent evidence'})
save(Q/'checks/MR_intake.json',{'source_root':str(IN),'target_root':str(OUT),'source_version':'MR-v1.1','manifest_files_verified':len(bundle['files']),'items':29,'sources':17,'preserved_input_files':original_files,'source_comparison':same})
# Each tuple is fresh R03 evidence, concrete writing delta, condition, linked original claim IDs.
U={
1:('新独立入口实际校验R02 manifest/主表SHA、135025唯一ID和版本；step2已连接共同日期fold。原v9不再接管，代码引用均已复制。','数据§2和附录B登记最早记录代理与实际版本；将“下游接口待接入”改为R03实现已检查，正式结果仍待R04。','输入消费检查完成；真实onset仍未证，R04重估后才能改数字。',['CL01']),
2:('UTC/London全事件日期/研究窗/时期差异1845/2/2；主768/0/0、天气105/0/0。UNIQUE_ANY UTC7300/London7298，成员差6，重叠702；窗口总成员8002。','§2及附录B/E补UTC半开窗、风暴结束日包含全天、源时区未知的分析解释及并列差异；不将七名称当七独立过程。','定向计数已提供；业务时区/完整过程独立性仍需来源与V协议。',['CL01','CL04']),
3:('两冲突ID在R02读取后仍保留；候选主原因均排除；无新拆并、删除或业务身份认证。','沿用两ID记录保留/公式可算/候选排除/业务未决四层说明，不称188天连续失电。','资格已核对，真实ID关系仍需源证据。',['CL01']),
4:('实际目标函数E0=ln(1+C)，R0c=ln(duration_B_full_span_hours)；兼容Duration(hours)未进入恢复目标。R02聚合证据复用，不重复全阶段重算。','维持C/D/A区别及完整阶段构造；正式描述比值从R04当前总体生成，不把smoke用于表1。','实现与消费通过；客户语义/停钟限制和正式描述数值仍待。',['CL01']),
5:('现有表分解不可查询5611、缺文件事件8236、四值/窗口完整121178；可读无效0，四候选v3-only0；129414事件/82621键/122948键小时/74896所需文件分母分开。未重扫缓存或请求API。','数据来源及附录A增加可读状态分母；保留历史model/gust语义/响应单位metadata未知，不能认定3秒或特定再分析产品。','状态对账完成；产品来源和风暴正式量级待源证据/R04。',['CL01','CL02']),
6:('源工作簿副本SHA及Rankings for all indicators表/列核对；rate和gap以比例存储；Buck gap=.1875仍只是旧极差均值。','表2/附录A2区分普通LAD区内LSOA极差与Buck例外；输入尺度不乘100，展示单位单列。','源表列定位完成；新系数待R04，代理重建待MR08。',['CL01','CL05']),
7:('工作簿Moran列及Buck旧均值副本已登记；没有取得可认证空间权重的新材料。','沿用LAD内LSOA聚集层级；空间权重未知和合并区proxy例外不能删。','层级定义不变；权重及合并区重建继续待证。',['CL05','CL06']),
8:('冻结Buck工作簿/原代码引用与lineage：四旧码2021人口缺失触发简单均值；.06325/.1875/.30和标记保留；候选主各1151、天气各293。','数据/附录A及图6解释保留proxy；按用户明确决定后续匹配年份/边界/分子分母/权重重建LSOA对照。','来源/标记检查完成；LSOA重建未执行，科学问题开放。',['CL05','CL06']),
9:('R02原因共识资格由新入口消费；两冲突ID主候选排除，天气子组仍取记录共识分类。无新官方原因语义证据。','原因表保持全阶段共识/冲突规则，天气原因写记录分类；四组共同fold不等于气象因果认证。','候选检查完成；正式原因支持/比较待R04/V02。',['CL01','CL03']),
10:('互斥归因按天气→人口→原因→目标→旧截尾→其他，602/99全为旧H0尾部限制取消；重叠时间/天气改变标志各85/14。主all_valid，备选主训练R0c p99共享给天气；全部有效测试长尾保留。','样本节/表1/附录C把候选恢复、训练规则和测试总体分开，写实际互斥归因与可重叠边际数，R1_compat只作诊断。','尾部/成员/fold实现已验；R04正式人数/结果，V01长尾稳健性。',['CL01','CL03']),
11:('部分训练标准化ddof1、区域原尺度/人口log、年月加性、未知类别报错已实现。VIF重建含完整日历/平方/交互，与旧VIF列集合不同；满秩另查。','方法/表2/附录F明确列清单、尺度和VIF样本/截距；不写全部VIF<4，不把LAD聚类称固定效应。','代码和smoke通过；R04出正式诊断/系数；图10日历例外见MR20。',['CL02','CL05']),
12:('评分保存事件唯一完整OOF、n/SSE/SST/尺度/身份，pooled与五折不加权mean分别输出；负R²和常量未定义手算测试通过。','方法公式和图5/表4标题统一pooled，逐折结果另列；评分评估均值与训练均值预测基准分开。','R03实现通过；当前正式OOF点结果仍待R04，不沿用H0数值。',['CL03','CL04']),
13:('主/天气共用基础日期映射，同目标组内control/G/K/GK训练/评价配对；条件G|K和K|G及相对control增量已在小样本完整OOF输出。','方法和表4/图5/8说明G含平方/气压交互、K含平方、共同资格；组间分母不同；保持三种排序结果分支。','接口通过；R04点估计、V02配对不确定性和支持检查后决定排序主张。',['CL03']),
14:('1096日期一次固定5折，所有主/天气同日期同折；24个完整候选设计/转换通过，无拟合。风暴重叠与UTC/London差异已量化。','方法/附录E区分日期OOF诊断与过程留出；图3历史earlier/later身份不改成独立确认。','R03日期规则已实现；R04日级诊断、V00/V02过程划分与推断待执行。',['CL04']),
15:('新共同预测/图9路径直接输出η，η=0为0；不再ln(1+expη)。逐事件目标尺度和版本保存。','图9轴、误差和方法用ln(1+C)观察值与η，禁止旧H0修正小数或smoke数字冒充当前风暴结果。','代码检查通过；R04新描述数据/图，V03留出校准仍待。',['CL04','CL05']),
16:('风暴表唯一联合ID、window_list、对应fold、fit成员/尾部/阈值和full/OOF来源逐行保存并验证无日期泄漏；真正过程留出标签被拒绝。','图9图题按新运行区分全样本描述与日期OOF，UNIQUE_ANY与窗口总人数分别写；不删测试长尾伪造纯拟合内样本。','接口和smoke通过；R04当前成员图、V02/V03合格过程评价。',['CL04']),
17:('场景从raw生成平方/交互；图4逐人完整设计后平均，图6原天气/客户中心+共同日历、缺年不补；meanη/expmeanη/meanexpη独立保存。','图4/6/7图题及附录H写参考人群、气压、calendar权重和聚合顺序，允许合法参考差异而不混称平均后果。','实现/存取检查通过；R04正式产物、V03场景解释待。',['CL05']),
18:('本轮修复二次生产接口，未拟合正式GLM/三阶/样条；H0的E0三阶反向线索完整保留，生产者表列未迁移分支。','结果4.1继续先形状/支持/损失，再决定最低点地位；不因程序通过关闭二次充分性问题。','R04保留项迁移范围需明确，V01形状比较后裁决CL02。',['CL02']),
19:('最低点接口保存β1/β2/β3、gust/pressure训练均值SD、固定物理气压、曲率/支持/失败；无区间、无旧Bootstrap读取。','附录H保留条件顶点公式，图4不填9.20–12.06；曲率非正/顶点越界写不可用；摘要是否保留等科学结果。','R03接口通过；R04点估计，V01/V03决定形状地位与条件区间。',['CL02']),
20:('新增发现：later完整候选12113事件，E设计rank18/19、R20/21，年份2024与Jan–Mar月份组合精确相关。开发期48323满秩。新时期生产器隔离后期，禁旧CV逆方差区间；各期物理系数使用自身scaler。','图10后期暂不生成；方法/附录E/H记录当前编码冗余，下一步验证等价满秩日历基或保留隔离，不默删项/拼旧系数。','当前图10后期阻断；全时期核心不受影响；R04前记录参数基方案，正式时期点估计/推断未执行。',['CL02','CL04']),
21:('step27最小重建raw ln(n_stages)前后模型及单阶段分箱；step42公共客户四分位/阶段1,2,3–4,5+构成已小试。当前全量阶段科学分析未运行。','附录D说明当前同一人群/公共分箱/各格n，旧9806、47840、59834不混；阶段控制不证明机制或唯一中介。','生产接口可用；R04新描述及V01质量/组成检验仍待。',['CL01','CL06']),
22:('新恢复模型仍使用全阶段最终C，标准化在训练内估计；没有新增初期信息集或当时预报模型。','沿用回顾性最终规模条件分析命名及变量可用时间表；不将新OOF误称故障起点预测。','信息边界不变；V03用途核实，新增部署问题不自动纳入。',['CL03','CL05']),
23:('指数拟合量、η误差和训练均值基准接口已修；没有smearing、留出校准或正式工程场景不确定性实验。','方法/图4/6/7/9解释expη非经认证算术均值；工程误差与校准等V，不能用smoke展示量级。','代码层通过；R04指定量，V03留出误差/场景证据。',['CL05']),
24:('图6新共同日历/冻结人口参考与图7网格指数比生产已小试；proxy和LAD兼容未决随输出保存；地图几何与正式渲染尚未生成。','图6/7去留仍按是否推进CL05；若保留明确参考/支持/网格含义，不能拿旧地图相关/旧倍数回填。','R04产物和V03量级证据后，V04/W决定去留；本轮未替作者确定保留。',['CL05','CL06']),
25:('R02之后隔离审查已恢复原v9；本轮新CLI/src连接R02，94源引用副本和7711运行文件冻结。17测试及720事件smoke通过；step26/27/28最小重建，缺新结果明确失败；原代码/数据/Word未改。LOG同期仅追加，另有证据。','当前生产者表替换旧v9接管状态；旧H0、失败smoke、成功smoke、正式B1身份分开。Word嵌图仅后续新版本；不可说R03修了所有历史82脚本。','R03代码与隔离检查完成（LOG追加单列）；R04产物/渲染、R05与W01一致性复核。',['CL01','CL02','CL03','CL04','CL05']),
26:('R03完成输入对账/生产接口/小试但无科学验证；新增图10参数基阻断，完整原MR-v1.1已取得并保留合并。','继续事件后果→重构→可比评价→工程解释；数据方法可更新实现依据，摘要/发现仍等R04/V；六章结构仍是建议。','当前写作方案可记录，R/V不断更新，W才落稿；本轮所有MR未写Word。',['CL01','CL02','CL03','CL04','CL05']),
27:('已读本地工作簿表名/字段及DBF版本元数据并复制保存；没有新增外部文献核查，历史天气产品、空间权重/边界等价仍缺来源。','附录A/引用来源表区分直接读取本地证据、旧报告与未知官方定义；不把R03报告作最终官方来源。','本地来源已补；保留主张的原始引用核实仍需后续，不编DOI/语义。',['CL01','CL05']),
28:('C10“Buck旧区简单均值proxy”的编号/源表/代码身份再核对；不再存在标题缺口。','保留MR28已关闭的编号问题与历史；区域科学问题继续归MR08，不把编号闭合当LSOA重建完成。','编号闭合保持，科学条件仍由MR08控制。',['CL05','CL06']),
29:('113非空LAD21代码均在LAD23人口键中，候选111；本地缺明确跨版等价来源，113码全部兼容未决；已证实实际错配数量未提供。缺LAD5762/其中可用坐标151未变。','数据2.1/2.4和附录A分别写定位边界、人口键/年及跨版证据缺口；区域图收窄，不报告0错配或全错配，不强制换版。','已给定向范围；补可靠跨版证据后才判断补丁需求，代理口径代码可继续。',['CL01','CL05'])}
source_files=[('SRC12',W/'reports/R03_report.md','SRC12_R03_report.md','R03本地执行报告，同一运行的总结，不是额外独立验证'),('SRC13',W/'tables/R03_INPUT_ACCEPTANCE.md','SRC13_R03_input_acceptance.md','R02冻结产物的定向再读取/对账'),('SRC14',Q/'CONTRACTS.md','SRC14_R03_contracts.md','实际新代码实施规则，非正式模型结果'),('SRC15',Q/'PRODUCER_CONSUMER_MAP.md','SRC15_R03_producers.md','生产者定位及实现范围'),('SRC16',Q/'logs/tests_release.txt','SRC16_R03_tests.txt','17项针对性测试日志'),('SRC17',Q/'smoke/R03_smoke_v4/RUN_MANIFEST.json','SRC17_R03_smoke.json','720事件non_inferential_smoke运行清单'),('SRC18',Q/'checks/full_candidate_period_rank.json','SRC18_R03_period_rank.json','完整候选矩阵秩检查，无拟合'),('SRC19',Q/'checks/final_isolation.json','SRC19_R03_isolation.json','原文件/复制依赖哈希及LOG追加观察'),('SRC20',Q/'R04_READINESS.md','SRC20_R04_readiness.md','后续具体配置和阻断，不是执行授权'),('SRC21',W/'code/PRODUCTION_CHANGELOG.md','SRC21_R03_code_changes.md','独立实现及保留/失效状态'),('SRC22',Q/'frozen/evidence/SRC11_R03_instruction.txt','SRC22_R03_pasted_instruction.txt','用户本轮提供的原始执行指令；保留与原SRC11独立字节身份，非新实验'),('SRC23',Q/'checks/R04_design_support.json','SRC23_R04_design_support.json','24个完整总体/折设计支持检查，无拟合')]
for sid,p,name,role in source_files:
    dest=OUT/'evidence'/name;shutil.copyfile(p,dest)
    sources['sources'].append({'source_id':sid,'original_name':p.name,'path':dest.relative_to(OUT).as_posix(),'role':role,'size_bytes':dest.stat().st_size,'sha256':sha(dest)})
version='MR-v1.2-R03';checkpoint='R03_completed_before_R04';updates=[]
for item in doc['items']:
    number=int(item['id'][2:]);ev,action,condition,claims=U[number]
    previous={k:copy.deepcopy(v) for k,v in item.items() if k!='history'}
    item.setdefault('history',[]).append(previous)
    delta={'stage':'R03','source_ids':['SRC12','SRC13','SRC14','SRC15','SRC16','SRC17','SRC18','SRC19','SRC20','SRC21','SRC22','SRC23'],'evidence':ev,'judgment_change':'代码/对账层推进；科学主张未关闭' if number not in [18,22,24,27,28] else '原科学判断/限制保持，已记录本轮检查范围','locations':item['locations'],'concrete_revision':action,'claim_ids':claims,'release_condition':condition,'word_status':'尚未写入Word'}
    item.update(evidence=ev,action=item['action']+' R03增量：'+action,release_condition=condition,decision_status=delta['judgment_change'],checkpoint=checkpoint,last_reviewed_checkpoint=checkpoint,evidence_level='R03 local code/input/synthetic/smoke evidence as specified; formal_B1_and_V_not_run',claim_ids=claims,r03_update=delta,word_status='尚未写入Word')
    item['sources']+=['SRC12–SRC23 R03本地证据，具体类型见SOURCE_MANIFEST及R03_WRITING_IMPACT']
    updates.append(dict(id=item['id'],title=item['title'],**delta))
doc.update(version=version,checkpoint=checkpoint);save(OUT/'REVISION_ITEMS.json',doc)
sources.update(checkpoint=checkpoint,version=version);save(OUT/'SOURCE_MANIFEST.json',sources)
md=(IN/'MANUSCRIPT_LEDGER.md').read_text(encoding='utf-8')
current='版本：MR-v1.2-R03，2026-09-05。检查点：**R03独立生产链、定向对账、17项测试和720事件smoke完成；图10后期隔离；R04/V/W未执行。** 原29个MR与历史均保留，当前增量以各条R03检查结论及R03_WRITING_IMPACT为准。'
md=re.sub(r'版本：MR-v1.1[^\n]*',current,md,count=1)
md=md.replace('当前新增接收SRC09/SRC10：','以下为MR-v1.1接收时的历史状态，已被本轮各项R03增量更新；原报告层级保留供追溯。MR-v1.2-R03直接读取了本地R02主表/代码副本/检查产物并运行针对性测试，但未重跑全量天气、正式模型或V。\n\n历史接收SRC09/SRC10：',1)
md=md.replace('### 0.3 本轮状态与稿件影响摘要','### 0.3 R02阶段摘要（保留历史；本轮R03见新增§10）',1)
claim_states={'CL01':'R03输入消费/资格/尺度与对账检查通过；真实onset/业务语义仍有限制','CL02':'最低点/尺度接口已修；正式形状及区间仍待R04/V；图10后期编码阻断','CL03':'共同fold/尾部/配对评分接口与smoke通过；无正式增量或稳定反转证据','CL04':'唯一窗口和full/OOF身份已修；日期诊断不等于完整过程验证，V未执行','CL05':'原变量场景/参考/指数尺度实现已查；无正式工程量级或校准证据','CL06':'阶段/区域描述生产已小试；因果或机制识别仍不具备'}
lines=md.splitlines()
for i,line in enumerate(lines):
    for cid,state in claim_states.items():
        if line.startswith('| '+cid+' |'):
            cells=line.split('|');cells[4]=' '+state+' ';lines[i]='|'.join(cells)
md='\n'.join(lines)+'\n'
for u in reversed(updates):
    pattern=r'(### '+u['id']+r'｜[^\n]*\n)(.*?)(?=\n### MR\d+｜|\n## 6\.|\Z)'
    def add(m):return m.group(1)+m.group(2)+'\n\n**R03检查结论（当前）：** '+u['evidence']+'\n\n**R03判断与具体增量：** '+u['judgment_change']+'；'+u['concrete_revision']+'\n\n**主张与生效条件：** '+', '.join(u['claim_ids'])+'；'+u['release_condition']+'\n\n**本轮来源与Word状态：** SRC12–SRC23，来源类型见manifest；尚未写入Word。前述R02叙述作为历史保留，具体当前字段见REVISION_ITEMS.json。\n'
    md,n=re.subn(pattern,add,md,count=1,flags=re.S);assert n==1,u['id']
md=md.replace('## 8. R02反馈后状态、缺证与下一步','## 8. R02反馈时的状态、缺证与下一步（历史）',1)
chapter='''
## 10. R03当前检查点与逐章增量

R03已完成独立生产接口、输入定向对账、17项针对性检查、720事件smoke和保护核查；正式B1/OOF全集、V、Word均未执行。原v9已在此前隔离审查恢复，本轮保持原代码只读；原LOG的同期追加只作观察证据。SRC09/10仍是同次R02报告；SRC12–23为本轮不同类型的证据，不能将其文件数量当独立验证次数。

|章节/附录|R03当前具体变化|后续条件|
|---|---|---|
|摘要/引言/结论，D-P002/P010/P013/P118–124|仍采用事件后果→重构→可比评价→工程解释；科学发现未更新；图10不再预设后期参数可用|R04/V结果裁决；六章结构仍为PD06建议|
|数据§2，D-P016–041；表1|补主表身份、602/99互斥归因、UTC/London1845/2/2及UNIQUE_ANY7300/7298；候选/训练/测试数分开|正式统计待R04；不直接换旧系数表n|
|方法§3，D-P050–064|共同日期fold、all_valid主规则、备选主训练p99、ddof1及完整变量块、pooled/mean-fold、归档/参考已实现|可写明确方法，但不得声称正式评价已执行|
|结果§4，图4–10|图4/6/7/9数据接口可追溯；图5/8配对指标接口可用；图10后期日历编码精确冗余已隔离|正式曲线/排序/风暴量级等待R04/V；最终渲染器尚未生成|
|附录A/B|本地源表/列与比例单位已核对，天气分母/业务时间/Buck/LAD兼容限制清楚；冲突ID资格已核|不得删去真实onset/历史产品/空间权重未知|
|附录C/D/G|C区分四候选与旧六组；D公共客户分箱及raw ln(n_stages)生产者已重建；G保留原因支持职责|六组和支持/质量科学分析待后续；不混旧样本结果|
|附录E/F/H|E保留历史开发边界及日期诊断；F补VIF和CR1实际生产；H明确η/指数/参考/条件顶点，删除旧区间自动回填路径|图10参数基需单列处理；正式新系数和科学区间未生成|

PD09（用户明确授权）：所有新工作另起炉灶；源代码依赖和引用先拷贝、冻结，再使用。本轮94份源引用与复制解释器/库已实施。

PD10（本轮实现处置，非作者已选择新的日历规格）：图10后期当前编码秩亏，返回blocked，不默删项；以后须明确记录并验证等价满秩基或暂不生成该图。

R04核心运行配置见SRC20；图形导出、六原因组及GLM/三阶未迁移分支单列。所有MR仍尚未写入Word，CL02–06科学问题不因测试通过关闭。MR28编号缺口保持闭合，MR08重建任务仍开放。
'''
md+=chapter;(OUT/'MANUSCRIPT_LEDGER.md').write_text(md,encoding='utf-8')
impact=['# R03 写作与论证影响｜MR-v1.2-R03','', '日期2026-09-05；原29个MR、CL01–06及段落索引保持。证据SRC12–23；输入R02、运行R03_smoke_v4（non_inferential_smoke），无正式B1/V，无Word修改。','', '|MR / CL|本轮证据|判断变化|章节/段/图表定位|具体拟改内容|生效条件|Word状态|','|---|---|---|---|---|---|---|---|']
for u in updates:impact.append('| '+' | '.join([u['id']+' / '+','.join(u['claim_ids']),u['evidence'],u['judgment_change'],', '.join(u['locations']),u['concrete_revision'],u['release_condition'],u['word_status']]).replace('\n',' ')+' |')
impact.append(chapter);(OUT/'R03_WRITING_IMPACT.md').write_text('\n'.join(impact)+'\n',encoding='utf-8')
(OUT/'START_HERE.md').write_text('# 修订记录包｜MR-v1.2-R03\n\n先读MANUSCRIPT_LEDGER.md新增§10、R03_WRITING_IMPACT.md及evidence/SRC12_R03_report.md。当前R03完成，R04/V/W未执行；图10后期隔离。29项MR、CL01–06、旧证据/阶段快照/Word索引完整保留；用户提供的paper_manuscript_record原包未改。正式R04运行配置/阻断见SRC20。所有MR尚未写入Word。\n',encoding='utf-8')
with (OUT/'CHANGELOG.md').open('a',encoding='utf-8') as f:f.write('\n## 2026-09-05｜MR-v1.2-R03｜本地独立生产接口与小规模检查\n\n- 校验并复制用户提供MR-v1.1；29项逐一追加history和R03证据→判断→定位→修改→CL→条件→Word状态；旧ID/标题和快照不重置。\n- 新增SRC12–SRC23，区分定向输入读取、规则/方法、测试、smoke、无拟合矩阵检查、保护观察及后续配置。SRC09/10/11原件保留；原SRC11与本轮粘贴指令按各自哈希保存。\n- MR11–20/MR23–25接口状态推进；MR01/02/05/08/10/28/29定向对账完成到明确证据范围；MR20新增后期年月编码秩亏，图10后期隔离。其余MR逐条记录无新科学结论的边界。\n- 更新CL01–06当前状态、正文/附录职责和PD09隔离决定；PD10只是受阻产物处置，不冒称作者已选择新参数基。\n- 原v9此前已恢复H0，本轮不接管；LOG同期追加单列，不将其C01拟合叙述并入R03/B1。\n- 17测试、720事件最新smoke通过；正式B1/V未执行；所有MR尚未写入Word。\n')
save(OUT/'R03_DELTA.json',{'version':version,'checkpoint':checkpoint,'updates':updates,'claim_states':claim_states})
assert all(sha(IN/x['path'])==x['sha256'] for x in original_files)
print(json.dumps({'imported_items':len(doc['items']),'updated_items':len(updates),'sources':len(sources['sources']),'version':version,'source_bundle_unchanged':True,'source_comparison':same},ensure_ascii=False))
