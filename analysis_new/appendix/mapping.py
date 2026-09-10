"""Materialize the three evidence-map views before any figure/table production."""
import csv
import hashlib
import json
from pathlib import Path
from .catalog import ROOT, REQUIREMENTS, MANUSCRIPT, PLAN

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def expected(r):
    rid, a = r['requirement_id'], r['action']
    if a == 'gap': return []
    if a == 'h03_complete':
        stems=['H03_MODEL_DEFINITIONS','H03_FULL_COEFFICIENTS','H03_GUST_COMPARISON','H03_EVENT_CONDITIONAL_FREQUENCIES']
        return [f'tables/{s}.{e}' for s in stems for e in ['csv','md']]+['logs/H03_PROTOCOL.json','logs/H03_TECHNICAL_CHECKS.json','logs/H03_EXECUTION_REPORT.md']
    if a == 'gi_complete':
        stems=['GI_PREDICTION_METRICS','GI_FINAL_GUST_RESIDUALS'] if rid=='G03' else ['GI_STORM_METRICS','GI_STORM_SAMPLES']
        figures=['GI_PREDICTION_CALIBRATION','GI_GUST_RESIDUALS','GI_RESPONSE_COMPONENTS'] if rid=='G03' else ['GI_STORM_FINAL_SCATTER']
        return [f'tables/{s}.{e}' for s in stems for e in ['csv','md']]+[f'figures/{s}.{e}' for s in figures for e in ['png','pdf']]+['logs/GI_PROTOCOL.json','logs/GI_TECHNICAL_CHECKS.json','logs/GI_EXECUTION_REPORT.md']
    if a == 'f02_complete':
        return [f'tables/F02_COEFFICIENT_COMPARISON.{e}' for e in ['csv','md']]+[
            'data/F02_SPECIFICATIONS.csv','data/F02_SOURCE_COMPARISON.csv','data/F02_MODEL_STATUS.csv',
            'logs/F02_PROTOCOL.json','logs/F02_TECHNICAL_CHECKS.json','logs/F02_EXECUTION_REPORT.md']
    if a == 'j03_complete':
        stems=['J03_FULL_PARAMETERS','J03_FOLD_FITS','J03_COMPONENT_PLAN','J03_COMPONENT_MANIFEST',
               'J03_MATCHED_SAMPLE','J03_PAIRED_METRICS','J03_FOLD_METRICS','J03_CALIBRATION',
               'J03_PAIRED_INTERVALS','J03_PROXY_HISTORY_COMPARISON']
        return [f'tables/{s}.{e}' for s in stems for e in ['csv','md']]+[
            'figures/J03_PRIMARY_CALIBRATION.png','figures/J03_BRIER_COMPARISON.png']
    if a == 'c_complete':
        stems={'C01':['C_CANDIDATE_DEFINITIONS','C_SAMPLE_DEFINITIONS'],
               'C02':['C_HISTORICAL_LADDER'],
               'C03':['C_GUST_FUNCTION_COMPARISON','C_LAD_FE_COMPARISON','C_EXISTING_FIXED_AND_D_REFERENCES'],
               'C04':['C_COVERAGE_MATRIX','C_COVERAGE_OVERVIEW','C_REFERENCE_COVERAGE']}[rid]
        return [f'tables/{s}.{e}' for s in stems for e in ['csv','md']]+(['figures/C_GUST_PERFORMANCE.png'] if rid=='C03' else [])
    names = {
        'samples':['A_SAMPLE_FLOW','A_CAUSE_COUNTS','A_COVARIATE_SUMMARY'],
        'dictionary':['A_VARIABLE_DICTIONARY'], 'vif':['A_FINAL_DESIGN_VIF'], 'docx_table':[rid+'_EXISTING_DEFINITION'],
        'grid':['J02_GUST_COMPARISON','J02_GRID_CELLS','J02_CENTROIDS','J_INDEPENDENT_WEATHER_DEFINITIONS'],
        'construction':['B_CONSTRUCTION_RULES','B_REPRESENTATIVE_REPAIR'],
        'duration':['B_RECOVERY_DEFINITION'], 'ramp':['C_PLATEAU_COMPARISON'],
        'knots':['D_KNOT_SUMMARY','D_NESTED_FOLD_KNOTS'],
        'profiles':[], 'period':['E_PERIOD_COEFFICIENTS','E_TEMPORAL_DESIGN'],
        'coefficients':['F_FULL_COEFFICIENTS'],
        'final_prediction':['G_FINAL_METRICS'],
        'ordinal':['H_ORDINAL_SUMMARY','H_CONDITIONAL_COEFFICIENTS'],
        'conditional':['H_CONDITIONAL_LOGNORMAL'],
        'storms':['I_STORM_COUNTS'], 'panel':['J_PROXY_DEFINITIONS','J_PROXY_LABELS'],
        'time':['J_TIME_METRICS','J_TIME_MONTHLY','J_TIME_SUPPORT','J_TIME_DEVELOPMENT_FIT'],
        'time_figure':['J_TIME_CALIBRATION_BINS'], 'boundaries':['J_INTERPRETATION_BOUNDARIES','J_FROZEN_EXPERIMENT_DEFINITIONS'],
    }
    if a == 'csv':
        files = r['sources'][:r.get('config',{}).get('files',len(r['sources']))]
        stems = [rid+'_'+Path(p).stem.upper() for p in files]
    else: stems = names[a]
    paths = [f'tables/{s}.{ext}' for s in stems for ext in ['csv','md']]
    if a == 'profiles':
        paths += ['figures/D_PLATEAU_PROFILE_BOOTSTRAP.png']
        paths += ['data/'+Path(p).name for p in r['sources']]
    if a == 'time_figure': paths += ['figures/J_TIME_CALIBRATION_MONTHLY.png','data/J_TIME_MONTHLY.csv']
    if a == 'conditional': paths += ['data/H_OPTIMIZER_DIAGNOSTICS.json']
    return paths

def source_paths():
    paths = {MANUSCRIPT, PLAN, 'results/new/20260909183317/run.json','scripts/final_combined_analysis/figure_style.py'}
    for r in REQUIREMENTS:
        paths.update(r['sources'])
        if r['review']: paths.add(r['review'])
    return sorted(paths)

def mapping_rows(states=None):
    states = states or {}
    claims, requirements, results = [], [], []
    for r in REQUIREMENTS:
        rid = r['requirement_id']; final = states.get(rid, '尚未生产' if r['action']!='gap' else ('用户已关闭' if r['source_status']=='CLOSED' else '有具体原因的缺失'))
        claims.append(dict(claim_id=r['claim_id'],body_location=r['location'],claim_summary=r['claim'],
            needed_evidence=r['question'],appendix_subsection=r['subsection'],body_existing=r['body_existing'],
            supplement_required=r['question'],requirement_id=rid,status=final))
        requirements.append({**{k:r[k] for k in ['requirement_id','claim_id','appendix','subsection','question','unit','sample','model','metrics','validation','duplicate_body','scope_note']},
                             'expected_outputs':';'.join(r['appendix']+'/'+p for p in expected(r))})
        results.append(dict(requirement_id=rid,claim_id=r['claim_id'],source_status=r['source_status'],final_status=final,
            authoritative_sources=';'.join(r['sources']),source_run=';'.join(sorted({p.split('/')[2] for p in r['sources'] if p.startswith('results/new/')})),
            source_sha256=';'.join(f'{p}:{digest(ROOT/p)}' for p in r['sources'] if (ROOT/p).is_file()),
            producer=r['producer'],export_function=(r['producer'] if r['action'] in {'c_complete','j03_complete','f02_complete','gi_complete','h03_complete'} else 'analysis_new.appendix.exporters:'+r['action']),configuration=json.dumps(r['config'],ensure_ascii=False),
            transformation=r['action'],dependencies='Python,pandas,numpy,matplotlib; existing frozen source files',review=r['review'],gap_and_minimal_action=r['gap']))
    return claims,requirements,results

def materialize(out, states=None):
    for name, rows in zip(['claim_evidence_map','appendix_requirements','requirement_result_map'],mapping_rows(states)):
        write_csv(out/(name+'.csv'),rows)

if __name__ == '__main__':
    materialize(ROOT/'results/Appendix')
    write_json(Path(__file__).with_name('source_fingerprints.json'),{p:digest(ROOT/p) for p in source_paths()})
    print(f'Three mapping layers and source registry refreshed: {len(REQUIREMENTS)} requirements.')
