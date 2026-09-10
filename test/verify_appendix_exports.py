"""Read-only verification of the delivered appendix exports (no model fitting).

Run from any directory: python -B /path/to/project/test/verify_appendix_exports.py
Prints JSON; saving a verification receipt is the caller's explicit action.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from analysis_new.appendix.catalog import ROOT,REQUIREMENTS,AGG,DUR,TIME,MAIN
from analysis_new.appendix.mapping import digest,expected
from analysis_new.appendix.runner import preflight

def main():
    output=ROOT/'results/Appendix';checks={};all_paths=[]
    root=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    for letter in 'ABCDEFGHIJ':
        manifest=json.loads((output/letter/'manifest.json').read_text(encoding='utf-8'))
        checks[letter+'_production_success']=manifest['status'] in ['success','success_with_gaps']
        checks[letter+'_manifest_hashes']=all(digest(output/letter/v['path'])==v['sha256'] for v in manifest['outputs'])
        planned={path for r in REQUIREMENTS if r['appendix']==letter for path in expected(r)}
        produced={v['path'] for v in manifest['outputs']}
        checks[letter+'_requirement_paths_match']=(planned<=produced if letter=='C' else planned==produced)
        all_paths.extend(letter+'/'+p for p in planned)
        checks[letter+'_correct_requirement_ids']=all(
            (v['path'] in expected(next(r for r in REQUIREMENTS if r['requirement_id']==v['requirement_id']))
             or (letter=='C' and v['requirement_id'] in {'C01','C02','C03','C04'} and
                 (v['path'].startswith(('data/','logs/')) or v['path']=='README.md')))
            and v['claim_id']=='CL_'+v['requirement_id'] for v in manifest['outputs'])
    read=lambda p:pd.read_csv(p,float_precision='round_trip')
    for source,destination in [(AGG+'metrics.csv','J/tables/J04_METRICS.csv'),(DUR+'metrics.csv','J/tables/J05_METRICS.csv'),(TIME+'calibration_bins.csv','J/tables/J_TIME_CALIBRATION_BINS.csv'),(TIME+'monthly_metrics.csv','J/tables/J_TIME_MONTHLY.csv'),(MAIN+'paper/r2_decomposition.csv','F/tables/F03_R2_DECOMPOSITION.csv')]:
        a=read(ROOT/source);b=read(output/destination)
        pd.testing.assert_frame_equal(a,b,check_exact=True)
        checks[destination+'_identical_source_values']=True
    source=read(ROOT/TIME/'temporal_metrics.csv');export=read(output/'J/tables/J_TIME_METRICS.csv')
    pd.testing.assert_frame_equal(source,export[source.columns],check_exact=True)
    checks['time_all_eight_tasks']=len(export)==8 and export.target.nunique()==8
    checks['time_bias_probability_points']=bool(np.allclose(export.bias_probability_percentage_points,100*source.prediction_minus_observed,rtol=1e-14,atol=1e-15))
    for i,r in read(output/'F/tables/F_FULL_COEFFICIENTS.csv').groupby('source',sort=False):
        original=read(ROOT/i)
        pd.testing.assert_frame_equal(original,r[original.columns].reset_index(drop=True),check_exact=True)
    checks['all_six_coefficient_tables_identical_source_values']=True
    checks['source_fingerprints_match']=all(v['passed'] for v in preflight(list('ABCDEFGHIJ')))
    checks['no_final_timestamp_subdirs']=all(p.name in set('ABCDEFGHIJ')|{'logs'} for p in output.iterdir() if p.is_dir())
    register=read(output/'figure_table_register.csv')
    checks['register_ids_unique']=not register.semantic_id.duplicated().any() and not register.display_number.duplicated().any()
    checks['register_files_exist']=all((output/p).is_file() for p in register.path)
    checks['table_count']=len(list(output.glob('*/tables/*.csv')))==root['tables']
    checks['figure_count']=len(list(output.glob('*/figures/*.png')))==root['figures']
    result=dict(checks=checks,all_passed=all(checks.values()),check_count=len(checks),tables=root['tables'],figures=root['figures'],
        requirement_status_counts=root['requirement_status_counts'],scope='Serialization, source/requirement mapping and export integrity only; no scientific refit or new scoring')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(not result['all_passed'])

if __name__=='__main__':raise SystemExit(main())
