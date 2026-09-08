from common import *
import zipfile,xml.etree.ElementTree as ET,shutil

def run(root=None):
    root=Path(root) if root else Path('D:/Pyprogramme/STST2603')
    e=events();extra=Q/'frozen/source_audit';extra.mkdir(exist_ok=True)
    sources=[root/'scripts/inspect_imd_moran_workbook_context.py',root/'IMD_merge.py',CORE/'frozen/project_sources/Buckinghamshire_combination.py',W/'R02/code_changes/r02_events.py']
    refs=[]
    for p in sources:
        if p.exists():q=extra/p.name;shutil.copyfile(p,q);refs.append({'original':str(p),**record(q)})
    workbook=CORE/'frozen/reference_data/localincomedeprivationdata.xlsx';ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};sheets=[];extract=[]
    with zipfile.ZipFile(workbook) as z:
        ss=ET.fromstring(z.read('xl/sharedStrings.xml'));strings=[''.join(n.itertext()) for n in ss]
        wb=ET.fromstring(z.read('xl/workbook.xml'));rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));mapping={x.attrib['Id']:x.attrib['Target'] for x in rels}
        for s in wb.find('m:sheets',ns):
            path=mapping[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];path=path.lstrip('/') if path.startswith('/') else 'xl/'+path
            tree=ET.fromstring(z.read(path));dim=tree.find('m:dimension',ns);texts=[]
            for row in tree.findall('.//m:sheetData/m:row',ns):
                vals=[]
                for c in row:
                    v=c.find('m:v',ns)
                    if v is not None:val=strings[int(v.text)] if c.attrib.get('t')=='s' else v.text;vals.append((c.attrib['r'],val))
                if int(row.attrib['r'])<=8 or any('E0700000'+str(n) in v for _,v in vals for n in [4,5,6,7]) or s.attrib['name']=='Notes':texts.append(vals)
            sheets.append({'sheet':s.attrib['name'],'dimension':dim.attrib.get('ref') if dim is not None else None});extract.append({'sheet':s.attrib['name'],'selected_rows':texts})
    put(Q/'checks/regional_workbook_extract.json',{'file':record(workbook),'sheets':sheets,'extract':extract})
    buck=[]
    for g in ['event_master','main','weather']:
        d=e if g=='event_master' else members(e,g,'E0');b=d[d.LAD21CD.eq('E06000060')];buck.append({'population':g,'n':len(d),'Buck_events':len(b),'pct':100*len(b)/len(d)})
    table(Q/'tables/BUCK_CURRENT_IMPACT.csv',pd.DataFrame(buck))
    deps=[('LSOA income-domain rate, denominator and vintage','available in workbook LSOA sheet','LSOA sheet A1:O32845 contains 2011 LSOA codes, 2019 LAD codes, Income Score(rate), mid-2015 total population excluding prisoners. Freeze and validate these fields before rebuilding; direct numerator is not separately provided.','rate/gap reconstruction'),('LSOA polygons and LSOA→new Buckinghamshire membership','not located','LAD21 geometry is available; does not supply LSOA topology or matching-vintage membership.','gap and Moran support'),('Published spatial-weight recipe','incomplete','Notes give source geography but not complete neighbor/distance, normalization and island rules. Obtain recipe or explicitly predeclare a derived alternative.','Moran equivalence claim'),('2021 population long table and MYEB3 source','available','LAD23 keys lack four former districts; explains simple-average fallback. Not LSOA income-domain denominator.','proxy provenance'),('LAD21 polygons and LAD23 linkage','available; boundary equivalence unresolved','Key mapping does not establish unchanged boundaries. Record dated geometry crosswalk for all used keys.','regional map interpretation'),('Original four-LAD deprivation workbook','available','Read sheet dimensions, Notes and four codes; rate .06325, gap .1875, Moran .30 are historical simple means.','proxy reproduction'),('Historical weather product metadata','incomplete','Requests/cache values retained; historical models unspecified, attrs empty in sampled archives. Need actual response/model identity, not a new default download.','ERA5-specific/3-second/true-onset assertions'),('UKPN raw export dictionary and cause code provenance','incomplete','Source fields and implemented consensus map known; zero-C semantics, stage numbering, official code labels and true initial customers not fully documented.','initial availability and physical causation')]
    table(Q/'tables/SOURCE_DEPENDENCIES.csv',pd.DataFrame(deps,columns=['dependency','status','available_evidence_and_missing_object','affected_claim']))
    copyrefs=[record(p) for p in (R4/'checks').glob('*.json')];put(Q/'checks/reused_R04_evidence.json',copyrefs);put(Q/'frozen/ADDITIONAL_SOURCE_MANIFEST.json',refs)
    checks=[
      ('C01','Earliest valid UTC source row; weather/date/window same event key','R05/frozen/source_audit/r02_events.py','R02 frozen field audit; R05 customer rows match135025; core member/date checks','passed implementation; true onset unknown','all core/period/storm'),
      ('C02','pooled=1−sumSSE/SST; mean fold separate','R05/src/numerical_audit.py','12 blocks,64 core archives, exact fold/SST tables','passed','fig05/08, main metrics'),
      ('C03','all_valid; common held-out identities; no evaluation p99 trim','R05/frozen/R03_src/contracts.py','12 block identities and training-only ddof1 preprocessing; B1 config hash','passed; tail sensitivity remains','all core OOF'),
      ('C04','eta already log target; do not log twice','R05/frozen/R03_src/prediction.py','archived eta readback + copied final renderer axes','passed','fig09,F1'),
      ('C05','half-open UTC windows; UNIQUE_ANY deduplicates','R05/frozen/R03_src/prediction.py','R04 core_actual_acceptance and formal unique event tables; R05 consumer readback','passed; date folds not full weather processes','fig03/09, storm table'),
      ('C06','only named predictors standardized; squares after standardization','R05/frozen/R03_src/contracts.py','every core training preprocessor rederived; 8 period physical terms','passed; unscaled regional coefficients need units','tables3/F,fig04/10'),
      ('C07','exp(mean eta), scenario support and references explicit','R05/frozen/R03_src/prediction.py','R04 core acceptance reused; copied curve and regional files; fig07 grid max/min','passed; not arithmetic conditional means','fig04/06/07'),
      ('C08','single full-period estimates; own scale; point-only fig10','R05/frozen/R04_src/calendar_repair.py','8 archives; separately-seen unseen combination guard; six nonPSD matrices scoped','passed implementation; two-way arbitrary Wald barred','fig10, appendixH'),
      ('C09','no original side effects; explicit copied consumer release','R05/src/render_release.py','12 final groups in new directory; protected-file hashes and source inventory','passed within manifest scope','all figures and ledger'),
      ('C10','stable region codes separate from indicator reconstruction','R05/frozen/source_audit/Buckinghamshire_combination.py','frozen code/lookup audit; current Buck impact table; workbook Notes','code identity usable; mandatory LSOA reconstruction pending','region covariates/fig06')]
    table(Q/'tables/C01_C10_CHAIN_AUDIT.csv',pd.DataFrame(checks,columns=['issue','rule','active_copied_code','targeted_evidence','actual_result','consumers']))
    write(Q/'PROVENANCE_AUDIT.md','# R05-1 输入—生产—消费者核查\n\n381个B1引用本地大小与SHA全部通过。核心4个全拟合、60个fold档案按实际事件ID、训练日期、训练内尺度、参数、η和目标再读；12块分数重新计算。阶段4+开发2与R1 64、分期8、补充22按完整档案身份及已有验收复用；不宣称本轮全部重新拟合。当前164个生产拟合另列1废弃部分档案、1未归档中止求解、R04 32个协方差核验拟合；本轮0拟合。producer_inventory.json逐文件记录。\n\n'+md(pd.DataFrame(checks,columns=['issue','rule','active_copied_code','targeted_evidence','actual_result','consumers']))+'\n## 来源范围和重建前置\n\n'+md(pd.DataFrame(deps,columns=['dependency','status','available_evidence_and_missing_object','affected_claim']))+'\n\nBuck当前影响：\n\n'+md(pd.DataFrame(buck))+'\nWorkbook Notes与四旧区选定行见regional_workbook_extract.json。本轮进一步读取工作簿发现LSOA工作表（A1:O32845），含2011 LSOA码、2019 LAD码、收入rate与2015年中人口（不含囚犯）；底表实际已在冻结材料内，不能列为缺失。尚缺匹配LSOA边界和完整空间权重配方；本地文件名检索不是全网不存在证明。地域rate用匹配分母加权，gap应对合并LSOA集合取极差，Moran应重新构建合并空间权重；不能平均旧Moran。先取得并冻结这些材料→V00确定边界/年份/分母及权重→重建新指标并对照代理→量化主/天气样本输入变化→仅重算实际受影响模型及消费者。该任务为作者既定决定，必须排在依赖它的V拟合之前，不归入可选T12。\n\nH0/R1/B1各自人口的评分与共同事件预测比较仍分别存放在release_v1/tables/H0_R1_B1_*.csv与common_event_prediction_comparison.csv。跨版本差异含输入、人口、分折变化，不作单修复因果归因。\n\n沿用来源合同中已查证内容，本轮不将历史网页描述当作新在线核验；缓存不证明现场3秒阵风、真实故障onset或具体历史产品。R05客户比较新增的是原始记录级审查，不改变C/D规则。\n')
    print('Source inventory and C01-C10 evidence map complete',flush=True)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='R05 source inventory / C01-C10 evidence map audit.')
    parser.add_argument('--root',default='D:/Pyprogramme/STST2603',help="Old STST2603 project root, used only to snapshot-copy the two legacy audit scripts (scripts/inspect_imd_moran_workbook_context.py, IMD_merge.py) into frozen/source_audit/.")
    args=parser.parse_args()
    run(root=args.root)

