"""Format accepted CSV cells for the A–E draft; no statistical analysis.

Default: verify formatted blocks against the single maintained manuscript.
--insert: one-time replacement of named placeholders; never rewrites prose.
This is a writing utility, not an alternative analysis/appendix entry point.
"""
from pathlib import Path
import argparse
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent / 'Supplementary_Information_A_E_draft.md'
USED = {}


def read(letter, name):
    p = ROOT / 'results' / 'Appendix' / letter / 'tables' / f'{name}.csv'
    USED[str(p.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(p.read_bytes()).hexdigest()
    return pd.read_csv(p)


def md(headers, rows):
    def line(row):
        return '| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in row) + ' |'
    return '\n'.join([line(headers), line(['---'] * len(headers))] + [line(r) for r in rows])


def num(x, places=4):
    return '—' if pd.isna(x) else f'{float(x):.{places}f}'


def count(x):
    return f'{int(float(x)):,}'


COMB = {'E0_all': 'All-incident exposure', 'R0c_all': 'All-incident recovery',
        'E0_weather': 'Weather-attributed exposure', 'R0c_weather': 'Weather-attributed recovery'}
MARGIN = {'E0': 'Exposure', 'R0c': 'Recovery'}
PERIOD = {'development': 'Development', 'confirmation': 'Later', 'combined': 'Combined reference'}
VARS = {'gust_0h': 'Gust (m/s)', 'precipitation_24h_sum': 'Precipitation (mm)',
        'temperature_0h': 'Temperature (°C)', 'pressure_msl_0h': 'Pressure (hPa)',
        'log_population': 'Log population', 'urban_binary': 'Urban indicator',
        'income_deprivation_rate': 'Income-deprivation rate', 'deprivation_gap_pct': 'Deprivation range',
        'morans_i': "Moran’s I"}
TERMS = {'z_gust_0h': 'Standardised gust', 'z_precipitation_24h_sum': 'Standardised precipitation',
         'z_temperature_0h': 'Standardised temperature', 'z_pressure_msl_0h': 'Standardised pressure',
         'z_gust_pressure': 'Gust × pressure', 'z_gust_precip': 'Gust × precipitation',
         'z_gust_sq': 'Standardised gust squared', 'z_temperature_sq': 'Standardised temperature squared',
         'z_customers_v2_log1p': 'Standardised log(1+C)', 'z_cust_sq': 'Standardised log(1+C) squared',
         'gust_low': 'Gust low-segment basis', 'gust_ramp': 'Gust ramp basis', **VARS}


def term(t):
    if t.startswith('incident_year['):
        return 'Year ' + t.split('[')[1].rstrip(']')
    if t.startswith('incident_month['):
        return 'Month ' + t.split('[')[1].rstrip(']')
    return TERMS[t]


def tables():
    out = {}
    d = read('A', 'A03_EXISTING_DEFINITION')
    out['A5'] = md(['Cause group', 'Original codes', 'Included'],
                   [(r['Category'], r['Original codes'], 'Yes' if i < 2 else 'No') for i, r in d.iterrows()])
    d = read('A', 'A_CAUSE_COUNTS').query("scope == 'final'")
    out['A2'] = md(['Margin', 'Cause group', 'n', 'Share (%)'],
                   [(MARGIN[r.margin], {'technical_asset': 'Asset-related', 'weather_natural': 'Weather-related'}[r.cause], count(r.n), num(100*r.share)) for r in d.itertuples()])
    d = read('A', 'A_SAMPLE_FLOW')
    d = d[~((d.margin == 'E0') & (d.scope == 'saved_input'))]
    out['A1'] = md(['Margin', 'Sample', 'Incidents', 'LADs', 'Zero customers'],
                   [(MARGIN[r.margin], {'final': 'All, final', 'weather_final': 'Weather-attributed, final', 'saved_input': 'Prepared recovery input'}[r.scope], count(r.n), count(r.lads), count(r.zero_customers)) for r in d.itertuples()])
    read('A', 'A_VARIABLE_DICTIONARY')
    out['A4'] = md(['Variable', 'Unit or scale', 'Definition and use'], [
        ('Affected customers, C', 'Customers', 'Sum over non-re-interruption stages; ln(1+C) is the exposure response.'),
        ('Incident span, D_B', 'Hours', 'Latest stage end minus earliest stage start; ln D_B is the recovery response.'),
        ('Weighted duration, D_A', 'Hours', 'Customer-weighted stage duration; construction comparison only (Appendix B).'),
        ('Gust, g', 'm/s', 'Matched starting-hour gust; standardised weather term or physical-unit segment bases.'),
        ('Precipitation, P', 'mm', 'Matched 24-hour accumulation; standardised.'),
        ('Temperature, T', '°C', 'Starting-hour temperature; standardised linear and squared terms in final models.'),
        ('Pressure, p', 'hPa', 'Starting-hour mean sea-level pressure; standardised.'),
        ('Log population', 'ln(persons)', 'LAD population on the stored natural-log scale.'),
        ('Urban indicator', '0/1', 'One when the stored urban–rural classification contains “urban”; zero otherwise.'),
        ('Income-deprivation rate', 'Source proportion', 'Published district income-deprivation rate, unstandardised.'),
        ('Deprivation range', 'Stored source scale', 'Within-district income-deprivation range, unstandardised.'),
        ('Moran’s I', 'Index', 'Spatial clustering of deprivation within the district, unstandardised.'),
        ('Year and month', 'Categories', 'From UTC incident date; training-level indicators with one category omitted.'),
        ('Log customer control', 'Standardised ln(1+C)', 'Recovery predictor, with its square; not a causal effect of incident size.'),
        ('LAD and fold identifiers', 'Categories', 'December 2021 district identifier and saved random-fold assignment; not continuous predictors.')])
    d = read('A', 'A_COVARIATE_SUMMARY')
    out['A3'] = md(['Sample', 'Variable', 'Mean', 'SD', 'Median', 'Q1–Q3'],
                  [(MARGIN[r.sample.split('_')[0]], VARS[r.variable], num(r.mean), num(r.sd), num(r.median), f'{num(r.p25)}–{num(r.p75)}') for r in d.itertuples()])
    d = read('A', 'A_FINAL_DESIGN_VIF')
    rows=[]
    for t in dict.fromkeys(d.term):
        vals={r.margin:r.VIF for r in d[d.term==t].itertuples()}
        rows.append((term(t), num(vals.get('E0', float('nan')),5), num(vals.get('R0c',float('nan')),5)))
    out['A6']=md(['Design term','Exposure VIF','Recovery VIF'],rows)
    d=read('A','A05_APPENDIXG_TABLE_G1_CORRECTED')
    out['A7']=md(['Gust group','n','Observed range (m/s)','Weather-attributed (%)'],
                 [(str(i+1),count(r.n),f'{num(r.gust_min,1)}–{num(r.gust_max,1)}',num(r.pct_weather_natural)) for i,r in enumerate(d.itertuples())])
    d=read('B','B_REPRESENTATIVE_REPAIR').set_index('historical_construction_metric')['value']
    out['B2']=md(['Record feature','Count'],[(label,count(d[key])) for label,key in [
        ('Incident references','n_total_incidents_v3'),('Incidents with equal earliest starts','n_incidents_with_tie_at_min_start_time'),
        ('Representative selection differs from source selection','n_representative_row_changed'),
        ('Unparseable stage starts','n_stage_rows_unparseable_start_time'),
        ('Incidents without a parseable start','n_incidents_unresolvable_no_parseable_start')]])
    d=read('B','B_RECOVERY_DEFINITION')
    labels=['Prepared recovery input','Zero customers','Positive customers, final']
    # Scope labels are matched explicitly below after reading the accepted table.
    scope_labels={'saved_R0c_input':labels[0],'zero_customers':labels[1],'positive_customers':labels[2]}
    out['B3']=md(['Sample','n','Exactly one hour','Share (%)'],
                 [(scope_labels.get(r.scope,r.scope),count(r.n),count(r.duration_exactly_1h),num(r.share_exactly_1h*100)) for r in d.itertuples()])
    definitions=read('C','C_CANDIDATE_DEFINITIONS')
    desc=[
        ('H01','Linear weather','z_g + z_P + z_T + z_p'),
        ('H02','Gust quadratic','H01 + z_g²'),
        ('H03','Gust–pressure interaction','H02 + z_g z_p'),
        ('H04','Regional block','H03 + S'),
        ('H05','Calendar effects','H04 + K'),
        ('H06','Cubic gust','H05 + z_g³'),
        ('H07','Log gust','H05, replacing z_g + z_g² by ln(1+g)'),
        ('H08','Fixed single hinge','H05, replacing z_g² by (g−10.8)₊'),
        ('H09','Gust steps','H05, replacing z_g + z_g² by four training-quantile indicators'),
        ('H10','Full quadratic weather','H05 + z_T² + z_P² + z_g z_P'),
        ('H11','LAD fixed effects','H05 + LAD indicators'),
        ('H12','Without regional block','H03 + K'),
        ('H13','Free single knot','H05, replacing z_g² by (g−k)₊; k selected on fitting observations'),
        ('H14','Free double knot','H05, replacing z_g + z_g² by an unrestricted two-hinge gust function'),
        ('F01','Quadratic','z_g + z_g²'),('F02','Cubic','z_g + z_g² + z_g³'),
        ('F03','Log gust','ln(1+g)'),('F04','Steps','Four training-quantile indicators'),
        ('F05','Fixed single hinge','z_g + (g−10.8)₊'),('F06','Free single knot','z_g + (g−k)₊'),
        ('F07','Free double knot','Three free segment slopes; two searched knots'),
        ('F08','Plateau','Two free segment slopes, followed by zero main-function slope; two searched knots')]
    assert set(x[0] for x in desc)==set(definitions.model_id)
    out['C1']=md(['ID','Specification','Terms or change'],desc)
    for key,name in [('C6','C_HISTORICAL_LADDER'),('C5','C_GUST_FUNCTION_COMPARISON')]:
        d=read('C',name); parts=[]
        for combination,label in COMB.items():
            rows=[]; dd=d[d.combination==combination]
            for r in dd.itertuples():
                base=[r.model_id,count(r.k),num(r.aic,2),num(r.bic,2),num(r.LAD_OOF_RMSE,8)]
                if key=='C6':base += [num(r.random_OOF_RMSE,8),num(r.year_holdout_RMSE,8)]
                else:base += ['10.8 (fixed)' if r.model_id=='F05' else ('—' if r.knots=='[]' else '/'.join(f'{float(v):g}' for v in json.loads(r.knots)))]
                rows.append(base)
            headers=['ID','k','AIC','BIC','LAD RMSE']+(['Random RMSE','Year RMSE'] if key=='C6' else ['Full-sample knots'])
            parts.append(f'**{label} (n = {count(dd.iloc[0]["n"])}).**\n\n'+md(headers,rows))
        out[key]='\n\n'.join(parts)
    d=read('C','C_EXISTING_FIXED_AND_D_REFERENCES')
    d=d[d.model_id.isin(['MAIN_final','W_paper','W_hinge','W_final'])]
    out['C4']=md(['Analysis','Reference','Gust form','BIC','LAD RMSE','Knot treatment'],
                 [(COMB[r.combination],{'MAIN_final':'Final','W_paper':'Paper','W_hinge':'Hinge','W_final':'Final'}[r.model_id],r.formula,num(r.bic,2),num(r.LAD_RMSE,8),'none' if r.knots_mode=='no knots' else 'global fixed') for r in d.itertuples()])
    d=read('C','C_LAD_FE_COMPARISON')
    out['C7']=md(['Analysis','ID','Adjusted R²','LAD RMSE'],
                 [(COMB[r.combination],r.model_id,num(r.adj_r2,6),num(r.LAD_OOF_RMSE,8)) for r in d.itertuples()])
    d=read('D','D_KNOT_SUMMARY')
    out['D1']=md(['Analysis','Form','n','Knot','Estimate','Profile','B','Bootstrap low / median / high'],
                 [(MARGIN[r.margin]+', '+('weather-attributed' if r.sample=='weather' else 'all')+(' (historical)' if r.n==59834 else ''),'Free double' if r.form=='unconstrained_two_hinge' else 'Plateau',count(r.n),r.knot,num(r.estimate,0),f'{r.profile_low:g}–{r.profile_high:g}',count(r.bootstrap_B),f'{r.bootstrap_low:g} / {r.bootstrap_median:g} / {r.bootstrap_high:.3f}'.removesuffix('.000')) for r in d.itertuples()])
    d=read('D','D_NESTED_FOLD_KNOTS')
    out['D2']=md(['Analysis','n','Fold','k₁','k₂'],
                 [(MARGIN[r.margin]+(' (historical)' if r.n==59834 else ''),count(r.n),int(r.fold_order)+1,num(r.k1,0),num(r.k2,0)) for r in d.itertuples()])
    d=read('E','E_PERIOD_COEFFICIENTS')
    out['E1']=md(['Margin','Period','Term','Coefficient','SE','p'],
                 [(MARGIN[r.margin],PERIOD[r.period],term(r.term),num(r.coef,6),num(r.se,6),f'{r.p:.5g}') for r in d.itertuples()])
    dates=read('E','E_TEMPORAL_DESIGN').set_index('period')
    out['E2']=md(['Margin','Period','Start','End','n','Mean gust'],
                 [(MARGIN[r.margin],PERIOD[r.period],dates.loc[r.period,'start'],dates.loc[r.period,'end'],count(r.n),num(r.gust_mean_m_s)) for r in d.drop_duplicates(['margin','period']).itertuples()])
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--insert', action='store_true')
    args=parser.parse_args()
    blocks=tables(); text=DRAFT.read_text(encoding='utf8')
    if args.insert:
        for key,block in blocks.items():
            marker='{{'+key+'}}'
            if text.count(marker)!=1:raise ValueError(f'Expected one unfilled placeholder {key}; refusing overwrite')
            text=text.replace(marker,block)
        DRAFT.write_text(text,encoding='utf8')
    failures=[k for k,v in blocks.items() if v not in text]
    report={'operation':'Formatting/selection of accepted cells only; no statistical calculation',
            'draft_sha256':hashlib.sha256(DRAFT.read_bytes()).hexdigest(),
            'tables_checked':list(blocks),'mismatched_blocks':failures,'source_sha256':USED,
            'display_changes':['Percentage conversion only for stored proportions','A7 group 0–9 displayed 1–10','D2 fold order 0–4 displayed 1–5','Period confirmation labelled Later'],
            'limits':'Checks formatted table blocks only; prose, figures and interpretations require human reading.'}
    (HERE/'table_transfer_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'tables':len(blocks),'mismatched_blocks':failures},ensure_ascii=False))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
