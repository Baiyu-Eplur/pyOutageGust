"""Full-data deterministic checks and active-reader checks; no model fitting."""
import sys,json,hashlib,datetime,difflib,importlib.util,unittest,io
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent;Q=O/'R02'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R.parent/'.venv/Lib/site-packages'));sys.path.insert(0,str(R/'scripts/event_input_repair'))
import pandas as pd
import numpy as np
import r02_events as m
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def shuffle():
    s=pd.read_parquet(Q/'data/source_stage_projection.parquet')
    rawsha=next(x['sha256'] for x in json.loads((O/'inventory/large_input_identity.json').read_text(encoding='utf-8')) if x['key']=='raw')
    gm=json.loads((O/'contracts/cause_group_map.json').read_text(encoding='utf-8'))['groups']
    a,qa=m.construct_events(s,rawsha,gm)
    b,qb=m.construct_events(s.sample(frac=1,random_state=20260905).reset_index(drop=True),rawsha,gm)
    pd.testing.assert_frame_equal(a,b,check_exact=True)
    assert qa==qb
    save(Q/'checks/full_shuffle.json',{'passed':True,'stage_rows':len(s),'events':len(a),'compared_columns':len(a.columns),'random_seed':20260905,'stable_id':'raw SHA256 + original 1-based source_row_number','comparison':'all constructed columns exact, not just selected time'})
    print('Full source-row permutation invariance passed',flush=True)
def final():
    buf=io.StringIO();suite=unittest.defaultTestLoader.discover(str(R/'scripts/event_input_repair'),pattern='test_r02_events.py')
    result=unittest.TextTestRunner(stream=buf,verbosity=2).run(suite)
    (Q/'logs/unit_tests.txt').write_text(buf.getvalue(),encoding='utf-8');assert result.wasSuccessful()
    e,manifest=m.load_active_events();assert sha(manifest['producer'])==manifest['producer_sha256']
    assert len(e)==135025 and e[m.ID].is_unique and int(e.stage_row_count.sum())==237901
    assert e.weather_query_eligible.isna().sum()==0
    assert int(e.cause_conflict.sum())==2 and int(e.event_identity_unresolved.sum())==2
    amb=e[e.event_identity_unresolved];assert set(amb[m.ID])=={'FREP-338321-Z','FREP-314454-J'}
    assert not amb.candidate_main_E0.any() and not amb.candidate_main_R0c.any()
    for c,t in [('income_deprivation_rate',.06325),('deprivation_gap_pct',.1875),('morans_i',.3)]:assert np.allclose(e.loc[e.regional_proxy_flag,c],t,rtol=0,atol=1e-12)
    readable=e.weather_cache_status.eq('readable');assert (e.loc[readable,'request_key']==e.loc[readable,'earliest_v3_request_key']).all()
    strict=e.weather_numeric_available&e.weather_validation_tier.eq('strict_cache_checked')
    assert e.loc[strict,'cache_rain_window_status'].eq('valid_24_unique_values').all()
    assert e.loc[strict,'cache_exact_hour_count'].eq(1).all()
    assert e.loc[strict,'cache_rain_valid_values'].eq(24).all()
    for s in ['main_E0','main_R0c','weather_E0','weather_R0c']:
        assert not e['candidate_'+s].isna().any()
        assert e['candidate_'+s].sum()==e['membership_'+s].isin(['common','enter']).sum()
    assert e.candidate_weather_E0.le(e.candidate_main_E0).all()
    assert e.candidate_weather_R0c.le(e.candidate_main_R0c).all()
    assert e[m.ID].eq('FREP-338321-Z').sum()==1
    from unittest.mock import patch
    path=R/'scripts/v3_validation/v3_validation_pipeline.py'
    spec=importlib.util.spec_from_file_location('r02_active_v9',path);v9=importlib.util.module_from_spec(spec)
    with patch.object(Path,'mkdir',side_effect=AssertionError('unexpected import mkdir')):spec.loader.exec_module(v9)
    with patch.object(v9.sm,'OLS',side_effect=AssertionError('model fitting outside R02')):
        matched,info=v9.step0_build_sample();same,ladinfo=v9.step1_lad_gapfill(matched)
        pd.testing.assert_frame_equal(matched,same)
        pd.testing.assert_frame_equal(matched,e.loc[e.new_in_study_utc&e.weather_numeric_available].copy())
        try:v9.step2_build_folds(matched)
        except RuntimeError as ex:guard=str(ex)
        else:raise AssertionError('Legacy fold execution was not stopped')
    save(Q/'checks/active_entry.json',{'passed':True,'path':str(path),'sha256':sha(path),'step0':info,'step1':ladinfo,'step2_guard':guard,'models_run':0,'import_mkdir_calls':0})
    snapshots=json.loads((O/'inventory/source_snapshots.json').read_text(encoding='utf-8'))
    source=next(x for x in snapshots if Path(x['source'])==path)
    diff=''.join(difflib.unified_diff(Path(source['snapshot']).read_text(encoding='utf-8').splitlines(True),path.read_text(encoding='utf-8').splitlines(True),fromfile='H0/'+path.relative_to(R).as_posix(),tofile='R02/'+path.relative_to(R).as_posix()))
    (Q/'code_changes/v3_validation_pipeline.patch').write_text(diff,encoding='utf-8')
    files=[path,R/'scripts/event_input_repair/r02_events.py',R/'scripts/event_input_repair/test_r02_events.py',O/'code/run_r02.py',Path(__file__)]
    save(Q/'code_changes/code_manifest.json',[{'path':str(p),'sha256':sha(p),'H0_snapshot':source['snapshot'] if p==path else None,'change':'modified' if p==path else 'new'} for p in files])
    save(Q/'checks/targeted_checks.json',{'passed':True,'unit_tests':result.testsRun,'full_event_count':len(e),'stage_membership_sum':int(e.stage_row_count.sum()),'C_D_A_full_comparison':'aggregation_consistency.json','full_row_shuffle':'full_shuffle.json','unresolved_events':len(amb),'Buck_proxy_exact':True,'strict_cache_rain_24_unique_finite':True,'active_input_reader':'active_entry.json','initial_test_failure_fixed':'nullable missing coordinate query flag; fillna(False), no numeric change','models_run':0})
    print(json.dumps({'checks_passed':True,'tests':result.testsRun,'active_entry_n':len(matched)},ensure_ascii=False))
if __name__=='__main__':
    if sys.argv[1]=='final' and (Q/'ISOLATED_ENTRY.json').exists():
        raise SystemExit('Historical v9 check archived after isolation. Use code/audit_r02_isolation.py validate for the independent entry; original v9 must remain untouched.')
    globals()[sys.argv[1]]()
