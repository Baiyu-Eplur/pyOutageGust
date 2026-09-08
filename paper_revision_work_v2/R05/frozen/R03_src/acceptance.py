"""Targeted intake from existing R02 artifacts; never rescan hourly weather."""
import json,shutil,zipfile,struct,xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import numpy as np
from contracts import *
from producer import ROOT,WORK,sha,read,save_json,load_events,step2_build_folds
def md(frame):
    d=frame.astype(object).where(pd.notna(frame),'NA')
    return '| '+' | '.join(map(str,d.columns))+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row)+' |' for row in d.itertuples(index=False,name=None))+'\n'
def copy_evidence(path):
    src=Path(path);dest=ROOT/'frozen/reference_data'/src.name;dest.parent.mkdir(exist_ok=True)
    if not dest.exists():shutil.copyfile(src,dest)
    if sha(src)!=sha(dest):raise ValueError('reference copy identity mismatch')
    return dest,{'original_path':str(src),'frozen_path':str(dest),'sha256':sha(dest),'role':'local evidence only'}
def dbf_columns(path):
    with Path(path).open('rb') as f:
        header=f.read(32);n=struct.unpack('<I',header[4:8])[0];hlen=struct.unpack('<H',header[8:10])[0];fields=[]
        for i in range((hlen-33)//32):
            b=f.read(32);fields.append({'name':b[:11].split(b'\x00')[0].decode('ascii'),'type':chr(b[11]),'width':b[16]})
    return {'rows':n,'fields':fields}
def build_config():
    manifest=ROOT/'frozen/evidence/R02_EVENT_MANIFEST.json'
    config={'schema':'R03_production_v1','run_id':'R04_B1_all_valid_v1','purpose':'B1_formal_pending_R04','input_version':'R02_input_20260905','input_manifest':str(manifest),'input_manifest_sha256':sha(manifest),'output_root':str(WORK/'R04/R04_B1_all_valid_v1'),'n_splits':5,'fold_policy':'global candidate union; descending date group size, date ascending ties, least-loaded fold then smallest fold index','fold_map':str(ROOT/'folds/date_to_fold.csv'),'training_tail':'all_valid','optional_tail':'main_train_p99; shared main training R0c reference, numpy linear .99, <=; all test retained','groups':['main','weather'],'targets':['E0','R0c'],'weights':'event_equal','calendar':'UTC additive training years/months; unseen error','full_fit_tail':'all_valid_descriptive','reference_contract':str(ROOT/'frozen/contracts/FIGURE_REFERENCE_CONTRACT.md'),'formal_execution_authorized_this_R03':False}
    save_json(ROOT/'configs/R04_primary.json',config,ROOT)
    return config
def run():
    config=build_config();e,em=load_events(config);base=e.loc[e.candidate_main_E0|e.candidate_main_R0c].copy();mapping=step2_build_folds(base,config);mapping.to_csv(ROOT/'folds/date_to_fold.csv',index=False)
    members=attach_folds(base,mapping);members[[ID,'new_date_utc','fold','candidate_main_E0','candidate_main_R0c','candidate_weather_E0','candidate_weather_R0c']].to_csv(ROOT/'folds/event_membership.csv',index=False)
    config['fold_map_sha256']=sha(ROOT/'folds/date_to_fold.csv');config['fold_base_ids_sha256']=identity(base[ID]);save_json(ROOT/'configs/R04_primary.json',config,ROOT)
    optional=dict(config,run_id='R04_optional_train_p99_v1',training_tail='main_train_p99',purpose='optional_training_tail_diagnostic_pending_authorization',output_root=str(WORK/'R04/R04_optional_train_p99_v1'))
    save_json(ROOT/'configs/R04_optional_p99.json',optional,ROOT)
    smoke=dict(config,run_id='R03_smoke_v1',purpose='non_inferential_smoke',groups=['main'],output_root=str(ROOT/'smoke/R03_smoke_v1'),smoke_rows_per_year_month_fold=4)
    save_json(ROOT/'configs/smoke.json',smoke,ROOT)
    assert len(e)==135025 and len(base)==60436 and set(e.loc[e.event_identity_unresolved,ID])=={'FREP-338321-Z','FREP-314454-J'}
    assert not e.loc[e.event_identity_unresolved,'candidate_main_E0'].any()
    acceptance=[];decomp=[];marginal=[];enterrows=[]
    for s in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        counts=e['membership_'+s].value_counts();acceptance.append({'sample':s,'H0':int(e['H0_'+s].sum()),'R02':int(e['candidate_'+s].sum()),'common':int(counts.get('common',0)),'enter':int(counts.get('enter',0)),'exit':int(counts.get('exit',0)),'v3_only':int((e['candidate_'+s]&e.weather_validation_tier.eq('v3_only_window_not_reverified')).sum())})
    for s,cap in [('main_R0c',192.08333333333334),('weather_R0c',142.84466666666685)]:
        d=e.loc[e['membership_'+s].eq('enter')].copy();remaining=pd.Series(True,index=d.index)
        tests=[('旧四天气不完整→新可用',~np.isfinite(d[['old_'+c for c in WX]].astype(float)).all(axis=1)),('旧年份人口缺失→新完整',d.old_population.isna()&d.population.notna()),('旧原因不符→新共识符合',~d.old_cause_group.isin(['technical_asset','weather_natural'])),('旧目标无效→新有效',~np.isfinite(d['old_'+D].astype(float))|d['old_'+D].le(0)),('旧H0截尾→完整有效尾部',d[D].gt(cap)),('其他待解释',pd.Series(True,index=d.index))]
        for reason,mask in tests:
            chosen=remaining&mask;decomp.append({'sample':s,'exclusive_reason_in_order':reason,'events':int(chosen.sum())});d.loc[chosen,'exclusive_reason']=reason;remaining&=~chosen
        assert not remaining.any();assert decomp[-1]['events']==0
        for label,mask in [('时间改变',d.selected_source_row.ne(d.old_source_row)),('任一天气变化',pd.concat([(d[c]-d['old_'+c]).abs().gt(1e-6)|(d[c].isna()!=d['old_'+c].isna()) for c in WX],axis=1).any(axis=1)),('R1兼容阈值也会排除',~d['R1_compat_candidate_'+s])]:marginal.append({'sample':s,'overlapping_flag':label,'events':int(mask.sum())})
        d['sample']=s;enterrows.append(d[[ID,'sample','exclusive_reason',D,'selected_source_row','old_source_row']])
    pd.concat(enterrows).to_csv(ROOT/'acceptance/entrants_exclusive.csv',index=False)
    # Frozen date windows are analysis assumptions, never promoted to verified business calendars.
    stormdates={'Arwen':('2021-11-25','2021-11-28'),'Dudley':('2022-02-15','2022-02-17'),'Eunice':('2022-02-17','2022-02-19'),'Franklin':('2022-02-19','2022-02-22'),'Babet':('2023-10-17','2023-10-22'),'Ciaran':('2023-10-31','2023-11-03'),'Henk':('2024-01-01','2024-01-03')}
    windows={};storm=[]
    for name,(start,end) in stormdates.items():
        stop=(pd.Timestamp(end,tz='UTC')+pd.Timedelta(days=1)).isoformat();windows[name]={'start':pd.Timestamp(start,tz='UTC').isoformat(),'end_exclusive':stop,'calendar':'UTC_declared_proxy','date_source':'frozen R01/old step10 dates, business timezone not independently confirmed','endpoint':'start inclusive/end next-day exclusive','London_alternative':True}
        u=e['new_storm_'+name];l=e['new_storm_london_'+name]
        storm.append({'window':name,'date_start':start,'date_end_inclusive':end,'UTC_events':int(u.sum()),'London_events':int(l.sum()),'membership_difference':int(u.ne(l).sum()),'main_candidates_UTC':int((u&e.candidate_main_E0).sum()),'weather_candidates_UTC':int((u&e.candidate_weather_E0).sum())})
    u=e[['new_storm_'+x for x in windows]].sum(axis=1);l=e[['new_storm_london_'+x for x in windows]].sum(axis=1)
    union={'UTC_UNIQUE_ANY':int(u.gt(0).sum()),'UTC_overlap_events_ge2':int(u.gt(1).sum()),'UTC_summed_window_memberships':int(u.sum()),'UTC_overlap_extra_memberships':int((u-1).clip(lower=0).sum()),'London_UNIQUE_ANY':int(l.gt(0).sum()),'London_overlap_events_ge2':int(l.gt(1).sum()),'UTC_London_union_difference':int(u.gt(0).ne(l.gt(0)).sum())}
    save_json(ROOT/'configs/storm_windows.json',windows,ROOT)
    pd.DataFrame(storm).to_csv(ROOT/'acceptance/storm_windows.csv',index=False);save_json(ROOT/'acceptance/storm_union.json',union,ROOT)
    copies=[];pop,pmeta=copy_evidence(WORK.parent.parent/'data/population_lad_long.csv');copies.append(pmeta);p=pd.read_csv(pop)
    book,bmeta=copy_evidence(WORK.parent.parent/'data/localincomedeprivationdata.xlsx');copies.append(bmeta)
    with zipfile.ZipFile(book) as z:
        doc=ET.fromstring(z.read('xl/workbook.xml'));sheets=[v.attrib['name'] for v in doc.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
    assert bmeta['sha256']=='6eb516a87654078ee69d4df55c8bc749b5da5de117f996f262c0c762bc20b38f'
    dataroot=WORK.parent.parent/'data';metadata=[]
    for dbf in sorted(dataroot.rglob('*.dbf')):
        cp,info=copy_evidence(dbf);copies.append(info);metadata.append({'path':str(dbf),**dbf_columns(cp)})
    save_json(ROOT/'acceptance/local_geography_metadata.json',metadata,ROOT)
    codes=sorted(e.LAD21CD.dropna().unique());pcodes=set(p.LAD23CD.dropna());rows=[]
    for code in codes:
        rows.append({'LAD21CD':code,'exists_as_LAD23_population_code':code in pcodes,'all_events':int(e.LAD21CD.eq(code).sum()),'main_candidates':int((e.LAD21CD.eq(code)&e.candidate_main_E0).sum()),'weather_candidates':int((e.LAD21CD.eq(code)&e.candidate_weather_E0).sum()),'geographic_equivalence':'unresolved_no_local_explicit_2021_to_2023_boundary_crosswalk'})
    geo=pd.DataFrame(rows);geo.to_csv(ROOT/'acceptance/LAD21_LAD23_compatibility.csv',index=False)
    save_json(ROOT/'frozen/REFERENCE_DATA_MANIFEST.json',copies,ROOT)
    weather=e.groupby(['weather_cache_status','weather_numeric_available']).size().rename('events').reset_index()
    numbers={'events':len(e),'candidate_base':len(base),'samples':acceptance,'exclusive_entrants':decomp,'overlapping_entrant_flags':marginal,'date_groups':len(mapping),'fold_events':members.fold.value_counts().sort_index().to_dict(),'fold_date_groups':mapping.fold.value_counts().sort_index().to_dict(),'storm_union':union,'calendar_all':{c:int(e[c].sum()) for c in ['UTC_London_date_diff','UTC_London_study_diff','UTC_London_period_diff']},'LAD_codes':len(codes),'LAD_codes_in_population':int(geo.exists_as_LAD23_population_code.sum()),'candidate_LAD_codes':int(geo.main_candidates.gt(0).sum()),'confirmed_geography_error_codes':[],'geography_identity_unresolved_codes':len(codes),'geography_scope':'no local explicit LAD21-to-LAD23 compatibility source found; same-code membership only','Buck_workbook_sha256':bmeta['sha256'],'Buck_sheets':sheets,'weather_event_states':weather.to_dict('records'),'input_sha256':em['event_table']['sha256']}
    save_json(ROOT/'acceptance/summary.json',numbers,ROOT)
    report='# R03 输入接收与定向对账\n\n基于已冻结 R02 主表及其可读报告，本轮没有重跑天气扫描或 H0 拟合。原 v9 已恢复，实际新入口是 R03/src/producer.py::step0_build_sample/step2_build_folds，经 R03/cli.py 运行。全部项目代码参考来自本地冻结副本，不导入原生产者。\n\n'+f'135,025 个事件；主表 SHA256 `{numbers["input_sha256"]}`。两未决 ID 仍保留且不纳入主原因候选；候选身份如下。\n\n'+md(pd.DataFrame(acceptance))+'\n602/99 的互斥归因采用固定顺序：天气数值资格→年度人口→原因→目标有效性→旧 H0 尾部限制→其他；前项命中后不再重复计入后项。旧 cap 是 H0 描述身份，不是新拟合阈值。\n\n'+md(pd.DataFrame(decomp))+'\n可重叠边际标志不能相加：\n\n'+md(pd.DataFrame(marginal))+'\nR1_compat 是成员诊断：main_R0c=59,832、weather_R0c=9,758，无 R1 模型。主阈值由 192.083333 变为 191.913333 h 另影响两条旧成员，详见冻结 R02 表。\n\nUTC/London 全事件日期/研究期/时期差异为 1,845/2/2；主候选为 768/0/0，天气候选为 105/0/0。风暴日期来源是冻结 R01 与旧 step10 约定；UTC 为明确分析解释，源业务时区未确证；结束日期包含全天，实际使用次日零时开区间，不随结果调整。\n\n'+md(pd.DataFrame(storm))+'\n'+md(pd.DataFrame([union]))+'\n天气事件数：\n\n'+md(weather)+'\n129,414 可查询事件对应 82,621 键、122,948 键×小时；74,896 可读文件、7,725 缺文件键；75,983 是整个目录文件数。121,178 四值完整事件全部缓存小时/窗口通过；可读但数值/小时/窗口失败实数0；不可查询5,611，缺文件事件8,236，其最早v3数值也缺。四候选v3-only实数0；历史model仍未决，不将数据值通过等同来源确定。\n\n'+f'区域：{len(codes)} 个非空 LAD21 代码中 {int(geo.exists_as_LAD23_population_code.sum())} 个出现在 LAD23 人口长表，候选涉及 {int(geo.main_candidates.gt(0).sum())} 个代码。同码只确认连接覆盖，不证明边界相同。本地 DBF/lookup 元数据见 local_geography_metadata.json，未发现可明确验证 2021→2023 边界等价的来源；没有已证实需改值的错误，保留全部相关代码的未决标志。5,762缺LAD和其中151可用坐标但未新增匹配沿用R02，不强行补区。\n\n'+f'Buck：工作簿 localincomedeprivationdata.xlsx SHA `{bmeta["sha256"]}`，Rankings for all indicators 的 Income deprivation rate、Deprivation gap (percentage points)、Moran\'s I；比例存储不乘100。普通LAD gap为LSOA rate极差，Buck四旧码简单均值保留 .06325/.1875/.30 及proxy。主候选各1,151、天气各293。原脚本真实路径及SHA已复制登记于 frozen/PROJECT_SOURCE_MANIFEST.json，详证来自 frozen/evidence/buckinghamshire_lineage.json。LSOA重建不在本轮。\n'
    (WORK/'tables/R03_INPUT_ACCEPTANCE.md').write_text(report,encoding='utf-8')
    print(json.dumps({'base':len(base),'dates':len(mapping),'geography_codes':len(codes),'fold_events':numbers['fold_events']},ensure_ascii=False))
