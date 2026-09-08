"""Produce R02 descriptive reports from frozen event inputs; no estimation."""
import sys,json,hashlib,datetime
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;Q=O/'R02';T=O/'tables'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R.parent/'.venv/Lib/site-packages'));sys.path.insert(0,str(R/'scripts/event_input_repair'))
import pandas as pd
import numpy as np
import r02_events as m
S=['main_E0','main_R0c','weather_E0','weather_R0c']
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else str(v)),encoding='utf-8')
def md(d):
    d=d.copy().fillna('NA')
    def esc(x):return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(map(esc,d.columns))+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(map(esc,row))+' |' for row in d.itertuples(index=False,name=None))+'\n'
def frame(rows,name):
    d=pd.DataFrame(rows);d.to_csv(T/(name+'.csv'),index=False);return d
def changed(a,b,tol=None):
    missing=a.isna()!=b.isna()
    if tol is None:return missing|(a.notna()&b.notna()&a.ne(b)).fillna(False)
    return missing|(a.notna()&b.notna()&(pd.to_numeric(a)-pd.to_numeric(b)).abs().gt(tol))
def main():
    e,manifest=m.load_active_events();w=pd.read_parquet(Q/'data/weather_key_hour_audit.parquet');scan=json.loads((Q/'checks/weather_scan_summary.json').read_text());T.mkdir(exist_ok=True)
    # Group sizes and member transitions are identities, independent of outcome fitting.
    transitions=[];change_rows=[];buck=[];quality=[];reason_rows=[]
    changes={
        '代表源行':e.selected_source_row.ne(e.old_source_row),
        'UTC时刻':changed(e.new_time_utc,e.old_time_utc),
        'UTC小时键':changed(e.new_weather_hour_utc,e.old_weather_hour_utc),
        'UTC日期':changed(e.new_date_utc,e.old_date_utc),
        'UTC年份':changed(e.new_year,e.old_year),
        'UTC月份':changed(e.new_month,e.old_month),
        '开发/后期/窗外':changed(e.new_period,e.old_period),
        '研究期成员UTC':changed(e.new_in_study_utc,e.old_in_study_utc),
        '任一风暴成员':pd.concat([changed(e['new_storm_'+n],e['old_storm_'+n]) for n in m.STORMS],axis=1).any(axis=1),
        '原因组(旧首行→全阶段共识)':changed(e.cause_group_event,e.old_cause_group),
        '人口数值或缺失状态':changed(e.population,e.old_population,1e-8),
        'LAD代码':changed(e.LAD21CD,e.old_LAD21CD),
        '坐标数值':changed(e.lat,e.old_lat,1e-10)|changed(e.lon,e.old_lon,1e-10),
        'C公式':changed(e[m.C],e['old_'+m.C],1e-8),
        'D公式':changed(e[m.D],e['old_'+m.D],1e-8),
    }
    for c in m.WX:changes['天气_'+c]=changed(e[c],e['old_'+c],1e-6)
    changes['任一天气字段']=pd.concat([changes['天气_'+c] for c in m.WX],axis=1).any(axis=1)
    for scope,mask in [('all_events',pd.Series(True,index=e.index))]+[(s,e['H0_'+s]) for s in S]+[(s+'_common',e['membership_'+s].eq('common')) for s in S]+[(s+'_enter',e['membership_'+s].eq('enter')) for s in S]+[(s+'_exit',e['membership_'+s].eq('exit')) for s in S]:
        for name,c in changes.items():change_rows.append({'scope':scope,'denominator':int(mask.sum()),'field':name,'changed_events':int((mask&c).sum())})
    changesdf=frame(change_rows,'R02_field_changes')
    for s in S:
        counts=e['membership_'+s].value_counts()
        transitions.append({'sample':s,'H0':int(e['H0_'+s].sum()),'R02_candidate':int(e['candidate_'+s].sum()),'common':int(counts.get('common',0)),'enter':int(counts.get('enter',0)),'exit':int(counts.get('exit',0)),'strict_cache_candidate':int(e['strict_candidate_'+s].sum()),'conditional_v3_only':int((e['candidate_'+s]&e.weather_validation_tier.eq('v3_only_window_not_reverified')).sum()),'R1_compat_candidate':int(e['R1_compat_candidate_'+s].sum())})
        buck.append({'sample':s,'H0_Buck':int((e['H0_'+s]&e.regional_proxy_flag).sum()),'R02_Buck':int((e['candidate_'+s]&e.regional_proxy_flag).sum()),'R02_Buck_strict':int((e['strict_candidate_'+s]&e.regional_proxy_flag).sum())})
        for base,col in [('H0','H0_'+s),('R02_candidate','candidate_'+s)]:
            mask=e[col];quality.append({'version':base,'sample':s,'N':int(mask.sum()),'min_stage_ge2':int((mask&e.min_stage_ge2).sum()),'tie_earliest':int((mask&e.earliest_tie_count.gt(1)).sum()),'identity_unresolved':int((mask&e.event_identity_unresolved).sum()),'cross_study_recovery':int((mask&e.recovery_crosses_study_end).sum())})
        for value,n in e.loc[e['membership_'+s].eq('exit'),'membership_reason_'+s].value_counts().items():reason_rows.append({'sample':s,'transition':'exit','reason':value,'events':int(n)})
        entering=e['membership_'+s].eq('enter')
        old_wx=np.isfinite(e[['old_'+c for c in m.WX]]).all(axis=1)
        flags={'old_four_weather_incomplete':~old_wx,'new_population_available_old_missing':e.old_population.isna()&e.population.notna(),'old_outside_UTC_study':~e.old_in_study_utc,'R1_compat_would_exclude':~e['R1_compat_candidate_'+s],'new_time_changed':changes['UTC时刻'],'new_weather_changed':changes['任一天气字段']}
        for label,mask in flags.items():reason_rows.append({'sample':s,'transition':'enter_multi_flag','reason':label,'events':int((entering&mask).sum())})
        subset=e.loc[e['H0_'+s]|e['candidate_'+s]].copy()
        subset.to_parquet(Q/f'data/H0_R02_{s}_crosswalk.parquet',index=False)
        # Portable, focused record-level table alongside the full provenance parquet.
        cols=[m.ID,'old_source_row','selected_source_row','old_start_raw','selected_start_raw','old_time_utc','new_time_utc','time_lag_removed_hours','old_weather_hour_utc','new_weather_hour_utc','old_year','new_year','old_month','new_month','old_period','new_period','old_cause_group','cause_group_event','old_population','population','LAD21CD','min_stage_ge2','regional_proxy_flag','event_identity_status','weather_numeric_available','weather_cache_status','weather_validation_tier',m.C,m.D,'H0_'+s,'candidate_'+s,'R1_compat_candidate_'+s,'membership_'+s,'membership_reason_'+s,*[a for c in m.WX for a in ['old_'+c,c,'delta_'+c]],*[a for n in m.STORMS for a in ['old_storm_'+n,'new_storm_'+n]]]
        subset[cols].to_csv(Q/f'data/H0_R02_{s}_crosswalk.csv.gz',index=False,compression='gzip')
    tr=frame(transitions,'R02_membership_transitions');bk=frame(buck,'R02_Buck_membership');qu=frame(quality,'R02_stage_quality');rr=frame(reason_rows,'R02_transition_reasons')
    # Sequential flow plus non-exclusive reasons: the order is declared, never added as marginal exclusions.
    masks=[('全事件',pd.Series(True,index=e.index)),('研究期UTC',e.new_in_study_utc),('身份无未决标志',~e.event_identity_unresolved),('原因共识属于主组',e.cause_in_main),('四天气有限且gust/rain非负',e.weather_numeric_available),('区域与人口完整',e.region_numeric_complete),('C有限且≥0',np.isfinite(e[m.C])&e[m.C].ge(0)),('D有限且>0',np.isfinite(e[m.D])&e[m.D].gt(0))]
    current=pd.Series(True,index=e.index);flow=[]
    for label,mask in masks:
        prior=int(current.sum());current&=mask
        flow.append({'step':label,'remaining':int(current.sum()),'removed_this_step':prior-int(current.sum())})
    fl=frame(flow,'R02_sequential_flow')
    storms=[]
    for scope,mask in [('all_events',pd.Series(True,index=e.index)),('main_E0_candidate',e.candidate_main_E0),('main_R0c_candidate',e.candidate_main_R0c)]:
        for n in m.STORMS:
            old=e['old_storm_'+n];new=e['new_storm_'+n]
            storms.append({'scope':scope,'storm':n,'old_members':int((mask&old).sum()),'new_members':int((mask&new).sum()),'enter':int((mask&new&~old).sum()),'exit':int((mask&old&~new).sum()),'UTC_London_diff_new':int((mask&new.ne(e['new_storm_london_'+n])).sum())})
        storms.append({'scope':scope,'storm':'UNIQUE_ANY','old_members':int((mask&e.old_storm_count.gt(0)).sum()),'new_members':int((mask&e.new_storm_count.gt(0)).sum()),'enter':int((mask&e.new_storm_count.gt(0)&e.old_storm_count.eq(0)).sum()),'exit':int((mask&e.old_storm_count.gt(0)&e.new_storm_count.eq(0)).sum()),'UTC_London_diff_new':None})
    st=frame(storms,'R02_storm_membership')
    calendar=[]
    for scope,mask in [('all_events',pd.Series(True,index=e.index))]+[(s,e['candidate_'+s]) for s in S]:
        calendar.append({'scope':scope,'N':int(mask.sum()),'UTC_London_date_diff':int((mask&e.UTC_London_date_diff).sum()),'UTC_London_study_diff':int((mask&e.UTC_London_study_diff).sum()),'UTC_London_period_diff':int((mask&e.UTC_London_period_diff).sum()),'old_new_period_diff':int((mask&changes['开发/后期/窗外']).sum()),'recovery_crosses_study_end':int((mask&e.recovery_crosses_study_end).sum())})
    cal=frame(calendar,'R02_calendar_comparison')
    e.loc[e.UTC_London_date_diff|e.UTC_London_period_diff|changes['开发/后期/窗外']|e.recovery_crosses_study_end,[m.ID,'old_start_raw','selected_start_raw','old_time_utc','new_time_utc','new_time_london','new_date_utc','new_date_london','old_period','new_period','new_period_london','new_in_study_utc','new_in_study_london','max_stage_end_utc','recovery_crosses_study_end']].to_csv(T/'R02_calendar_boundary_events.csv',index=False)
    causes=frame(e.groupby(['old_cause_group','cause_group_event'],dropna=False).size().rename('events').reset_index().to_dict('records'),'R02_cause_transitions')
    raw=pd.read_parquet(Q/'data/source_stage_projection.parquet')
    frame(raw['Cause Code'].value_counts(dropna=False).rename_axis('raw_cause_code').reset_index(name='stage_rows').to_dict('records'),'R02_raw_cause_counts')
    e.loc[changes['人口数值或缺失状态'],[m.ID,'old_start_raw','selected_start_raw','old_year','new_year','old_LAD21CD','LAD21CD','old_population','population','population_join_status']].to_csv(T/'R02_population_changes.csv',index=False)
    # Full weather coverage: distinct event, key-hour, and file denominators remain separate.
    ws=frame(e.groupby(['weather_cache_status','weather_validation_tier','weather_numeric_available'],dropna=False).size().rename('events').reset_index().to_dict('records'),'R02_weather_event_status')
    present=w.drop_duplicates('request_key')
    present[['request_key','cache_file_path','cache_status','cache_sha256','cache_bytes','cache_error','cache_attrs_json','product_status','units_basis','units_response_metadata_available']].to_csv(Q/'data/requested_cache_file_manifest.csv',index=False)
    wrows=[]
    for c in m.WX:
        a=e[c];old=e['old_'+c];both=np.isfinite(a)&np.isfinite(old)
        earliest=e['earliest_v3_'+c];bothfirst=np.isfinite(a)&np.isfinite(earliest)
        wrows.append({'field':c,'new_finite':int(np.isfinite(a).sum()),'old_finite':int(np.isfinite(old).sum()),'both_finite_changed_gt_1e6':int((both&(a-old).abs().gt(1e-6)).sum()),'old_missing_new_finite':int((~np.isfinite(old)&np.isfinite(a)).sum()),'old_finite_new_missing':int((np.isfinite(old)&~np.isfinite(a)).sum()),'earliest_v3_both_finite_changed_gt_1e6':int((bothfirst&(a-earliest).abs().gt(1e-6)).sum()),'earliest_v3_missing_new_finite':int((~np.isfinite(earliest)&np.isfinite(a)).sum()),'earliest_v3_finite_new_missing':int((np.isfinite(earliest)&~np.isfinite(a)).sum()),'max_abs_vs_earliest_v3':float((a-earliest).abs().max())})
    wx=frame(wrows,'R02_weather_field_changes')
    any_oldnew=changes['任一天气字段']
    amb=e[e.event_identity_unresolved].copy();amb.to_csv(T/'R02_ambiguous_event_master.csv',index=False)
    raw.loc[raw[m.ID].isin(amb[m.ID])].sort_values([m.ID,'source_row_number']).to_csv(T/'R02_ambiguous_source_stages.csv',index=False)
    cols=[m.ID,'source_rows','old_source_row','selected_source_row','old_time_utc','new_time_utc','max_stage_end_utc','cause_codes_all',m.C,m.D,'weather_cache_status','weather_numeric_available','weather_validation_tier','old_population','population','candidate_main_E0','E0_exclusion_reasons']
    ambmd='# R02 两个未决事件\n\n'+md(amb[cols])+'\n两事件完整阶段保留，未拆分、未作为完全重复行删除；主表公式值不等于已核实的连续失电或客户真值。FREP-338321-Z 的跨度为 ID 公式 4508.933333 h；FREP-314454-J 的两条 stage 1/同 unique_identifier 记录存在原因差异，C=2 仍是暂定 ID 加总。原因采用所有阶段共识，冲突进入 unresolved，按 R01 CAUSE_RULES 不进入主原因候选。原 MEI、监管年度、起止原字符串见 R02_ambiguous_source_stages.csv。\n'
    (T/'R02_AMBIGUOUS_EVENTS.md').write_text(ambmd,encoding='utf-8')
    flowmd='# R02 修正输入候选样本流\n\n这些是输入资格与成员，B1 模型和最终 OOF 均未产生。R02_candidate 采用合同的全有效尾部，不应用分组 p99；规则允许明确标记的 v3-only 条件来源，本轮实际为零。strict_cache_candidate 只表示缓存时刻/数值/24小时窗已核查，仍不能确认历史产品。R1_compat_candidate 只按旧首行原因和分别 p99 生成输入诊断成员，没有拟合或折分。\n\n'+md(tr)+'\n固定顺序排除如下，最后一行为主 R0c；倒数第二行为主 E0。天气子集从同一主总体派生。\n\n'+md(fl)+'\n退出原因（互斥组合）及进入者标志见 R02_transition_reasons.csv；进入标志可重叠，不相加为人数。\n\n'+md(rr)+'\n缺首阶段质量标记：\n\n'+md(qu)+'\nBuckinghamshire 代理人数：\n\n'+md(bk)
    compat_rows=[];compat_events=[]
    for s in S:
        old=e['H0_'+s];new=e['R1_compat_candidate_'+s]
        compat_rows.append({'sample':s,'H0':int(old.sum()),'R1_compat_input':int(new.sum()),'common':int((old&new).sum()),'enter':int((~old&new).sum()),'exit':int((old&~new).sum())})
        sub=e.loc[old.ne(new),[m.ID,m.C,m.D,'old_time_utc','new_time_utc','weather_numeric_available','event_identity_status']].copy();sub['sample']=s;sub['transition']=np.where(old.loc[sub.index],'exit','enter');compat_events.append(sub)
    cf=frame(compat_rows,'R02_R1_compat_transitions');ce=pd.concat(compat_events,ignore_index=True);ce.to_csv(T/'R02_R1_compat_changed_members.csv',index=False)
    caps=json.loads((Q/'checks/R1_compatibility_caps.json').read_text(encoding='utf-8'))['p99_hours']
    flowmd+='\nR1 输入兼容诊断（仍不是 B1）：\n\n'+md(cf)+'\n'+md(ce)+f'\n当前兼容主恢复 p99={caps["main"]:.12f} h（H0 为 192.083333333333 h），天气 p99={caps["weather"]:.12f} h。主组极端事件失去最早天气后，重新计算旧式 p99 又使两条原 H0 恢复成员落到阈值外；这是保留旧缺陷的诊断结果，不用于裁剪 R02 全有效候选。\n'
    (T/'R02_SAMPLE_FLOW.md').write_text(flowmd,encoding='utf-8')
    oldnew='# R02 旧新输入变化\n\n旧值来自原始行序代表阶段及其 v3 字段；新值来自 UTC 最早记录、独立原因共识和年度人口重关联。数值差异阈值：天气绝对 1e-6（原始差值仍保留）、C/D 1e-8。缺失状态变化也计入。完整表另列 all、H0 四样本、共同、进入、退出各分母。不能将 H0→R02 的全部成员变化只归因于时间修复，因为候选恢复总体已遵循全有效尾部。\n\n'+md(changesdf[changesdf.scope.isin(['all_events','main_E0_common','main_R0c_common','weather_E0_common','weather_R0c_common'])])+'\nUTC 是冻结分析日历，业务日历尚未核实；Europe/London 为并列敏感性计数，不作为默认替换。UTC 研究期为 [2021-04-01 00:00Z,2024-04-01 00:00Z)，后期自 2023-09-30 00:00Z 起。\n\n'+md(cal)+'\n风暴分别列成员；UNIQUE_ANY 为去重后的事件数，重叠风暴不能直接相加。\n\n'+md(st)+'\n原因转移：\n\n'+md(causes)+'\n人口逐事件差异见 R02_population_changes.csv；所有源行与下游字段见事件主表及四份 H0_R02_*_crosswalk。\n'
    (T/'R02_OLD_NEW_SUMMARY.md').write_text(oldnew,encoding='utf-8')
    weather='# R02 全量天气可用性与来源\n\n'+f'全事件 {len(e):,}；可生成最早查询键的事件 {scan["eligible_event_count"]:,}；不同查询键 {scan["distinct_query_keys"]:,}；键×目标小时 {scan["key_hour_rows"]:,}。查询对应现存文件 {scan["existing_files"]:,}。目录原有 75,983 个 pkl，目录中其他日期/阶段的文件不等于本轮事件所需文件。新网络请求为 0。\n\n'+md(pd.DataFrame([{'cache_file_status':k,'requested_keys':v} for k,v in scan['cache_status_by_file'].items()]))+'\n事件分母结果：\n\n'+md(ws)+'\n同一键只读取并哈希一次，可服务多个事件及目标小时。精确时刻须唯一；雨量窗口为 (t−24h,t]，24 个唯一整点、全部有限且非负。未使用 nearest 小时或将 NaN 雨量补零。缓存可读但窗口无效时保留失败状态，不用旧 v3 值掩盖。缓存不可得时，仅在最早源行、坐标日期键与精确小时均匹配时保留 v3 值，标记 v3_only_window_not_reverified。\n\n'+md(pd.DataFrame([{'rain_window_status':k,'key_hours':v} for k,v in scan['rain_status_by_key_hour'].items()]))+'\n字段变化（列名 gt_1e6 指绝对阈值 1e-6）：\n\n'+md(wx)+'\n单位依据是冻结采集代码的 wind_speed_unit=ms、precipitation_unit=mm、timezone=GMT；缓存自身未提供可确认的响应单位 metadata。历史请求未锁定 model，historical_model_unresolved 保留在所有事件上，不能据当前 API 默认模型追认 ERA5，也不能将缓存数值通过等同于业务/产品来源通过。缓存 attrs 与 SHA、读取错误、有效雨量计数保存在 weather_key_hour_audit.parquet；每个请求文件索引见 requested_cache_file_manifest.csv。\n'
    (T/'R02_WEATHER_AVAILABILITY.md').write_text(weather,encoding='utf-8')
    missing=e.weather_cache_status.eq('missing_file');old_any=e[['old_'+c for c in m.WX]].notna().any(axis=1);earliest_any=e[['earliest_v3_'+c for c in m.WX]].notna().any(axis=1)
    wxcases={'cache_missing_events':int(missing.sum()),'cache_missing_earliest_v3_any_numeric':int((missing&earliest_any).sum()),'cache_missing_old_later_weather_present':int((missing&old_any).sum()),'old_four_weather_complete':int(np.isfinite(e[['old_'+c for c in m.WX]]).all(axis=1).sum()),'new_four_weather_complete':int(e.weather_numeric_available.sum()),'all_readable_attrs_empty':bool(w.loc[w.cache_status.eq('readable'),'cache_attrs_json'].eq('{}').all())}
    save(Q/'checks/weather_source_cases.json',wxcases)
    with (T/'R02_WEATHER_AVAILABILITY.md').open('a',encoding='utf-8') as f:f.write(f'\n实际缺缓存事件 {wxcases["cache_missing_events"]:,} 中，最早 v3 源行已存任一天气值者为 {wxcases["cache_missing_earliest_v3_any_numeric"]}；因此本轮没有 v3-only 条件样本，不能解释为程序一律删除此类值。其中 {wxcases["cache_missing_old_later_weather_present"]} 个事件旧较晚代表行有天气，新版不借用。另有 9 个事件从旧代表行缺失变为最早记录可用，四天气完整事件由 121,313 减至 121,178（−144+9）；这些 9 个最早源行本来就有 v3 数值，并非本轮新抓或从缺失 v3 恢复。所有可读缓存 attrs 为空，产品状态仍未决。\n')
    summary={'run_id':manifest['run_id'],'events':len(e),'stages':int(e.stage_row_count.sum()),'all_event_changes':{k:int(v.sum()) for k,v in changes.items()},'membership':transitions,'Buck':buck,'calendar':calendar,'weather_scan':scan,'weather_numeric_events':int(e.weather_numeric_available.sum()),'strict_numeric_events':int((e.weather_numeric_available&e.weather_validation_tier.eq('strict_cache_checked')).sum()),'conditional_v3_numeric_events':int((e.weather_numeric_available&e.weather_validation_tier.eq('v3_only_window_not_reverified')).sum()),'unresolved_events':len(amb),'models_run':0}
    save(Q/'checks/report_numbers.json',summary)
    print(json.dumps(summary,ensure_ascii=False,default=str),flush=True)
if __name__=='__main__':main()
