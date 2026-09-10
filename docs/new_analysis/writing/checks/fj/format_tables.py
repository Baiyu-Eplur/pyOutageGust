"""Format saved CSV values into editable Markdown. No model/data-analysis entry is imported.

Run without arguments to check the existing draft against these deterministic tables.
--insert replaces explicit TABLE_* placeholders once; it never replaces manuscript prose.
"""
from pathlib import Path
import argparse
import json
import re
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent.parent / 'Appendices_F_J_draft.md'
sources = {}
blocks = {}
names = {'E0_all':'All-incident exposure','R0c_all':'All-incident recovery','E0_weather':'Weather-attributed exposure','R0c_weather':'Weather-attributed recovery'}
targets = ['any_gt0','any_gt5','any_gt100','any_gt1000','wthr_gt0','wthr_gt5','wthr_gt100','wthr_gt1000']

def target(s):
    a,b=s.split('_gt');return ('All: ' if a=='any' else 'Weather: ')+('any incident' if b=='0' else '>'+b+' customers')

def read(path):
    p=ROOT/'results/Appendix'/path
    d=pd.read_csv(p)
    sources[str(p.relative_to(ROOT)).replace('\\','/')]={'rows':len(d),'columns':list(d.columns)}
    return d

def num(v, places=6):
    if pd.isna(v): return '—'
    return f'{v:.{places}f}'

def pv(v):
    if v<0.0001:return f'{v:.2e}'
    return f'{v:.4f}'

def interval(a,b,places=6):return '['+num(a,places)+', '+num(b,places)+']'

def storm_name(s):
    return {'UNION_DEDUPLICATED':'Deduplicated union','Ciaran':'Ciarán'}.get(s,s)

def table(headers,rows):
    safe=lambda x:str(x).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(safe,headers))+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(safe,row))+' |' for row in rows])

def term(s):
    simple={'Intercept':'Intercept','z_precipitation_24h_sum':'$z_P$','z_temperature_0h':'$z_T$','z_pressure_msl_0h':'$z_p$','z_gust_pressure':'$z_g z_p$','z_gust_precip':'$z_g z_P$','z_temperature_sq':'$z_T^2$','z_gust_0h':'$z_g$','z_gust_sq':'$z_g^2$','gust_low':'$L(g)$','gust_ramp':'$R(g)$','urban_binary':'Urban indicator','log_population':'Log population','income_deprivation_rate':'Income deprivation rate','deprivation_gap_pct':'Deprivation gap','morans_i':"Moran’s $I$",'z_cust':'$z_C$','z_cust_sq':'$z_C^2$','z_customers_v2_log1p':'$z_C$','gust_hinge_11':'$(g-11)_+$'}
    if s in simple:return simple[s]
    if s.startswith('incident_year['):return 'Year '+s.split('[')[1].strip(']')
    if s.startswith('incident_month['):return 'Month '+s.split('[')[1].strip(']')
    return s

def build():
    f=read('F/tables/F_FULL_COEFFICIENTS.csv');fw=read('F/tables/F02_COEFFICIENT_COMPARISON.csv')
    hc=read('H/tables/H03_FULL_COEFFICIENTS.csv')
    panels=[]
    for label,(margin,sample,n,df) in zip('abcd',[('E0','all',60437,110),('R0c','all',51173,110),('E0','weather',9857,104),('R0c','weather',9254,103)]):
        rows=[]; comb=margin+'_'+sample
        d=f[(f.margin==margin)&(f['sample']==sample)&(f.SE_method=='two_way_LAD_date')]
        for _,r in d.iterrows():
            if sample=='weather':
                q=fw[(fw.model==comb+'_final')&(fw.term==r.term)].iloc[0]
                sl=q.se_lad; lo=q.ci_twoway_lower;hi=q.ci_twoway_upper; ll=q.ci_lad_lower;lh=q.ci_lad_upper
            else:
                q=hc[(hc.combination==comb)&(hc.model=='OLS_reference')&(hc.term==r.term)].iloc[0]
                sl=f[(f.margin==margin)&(f['sample']==sample)&(f.SE_method=='LAD_only')&(f.term==r.term)].iloc[0].se
                lo=q.ci_lower;hi=q.ci_upper;ll=r.coef-t.ppf(.975,df)*sl;lh=r.coef+t.ppf(.975,df)*sl
            rows.append([term(r.term),num(r.coef),num(sl),num(r.se),interval(ll,lh),interval(lo,hi),pv(r.p_t_G1)])
        panels.append(f'**Table F1({label}). {names[comb]}: $n={n:,}$; reference $t_{{{df}}}$.**\n\n'+table(['Term','Coefficient','SE: LAD','SE: two-way','95% CI: LAD','95% CI: two-way','Two-way $p$'],rows))
    blocks['F1']='\n\n'.join(panels)
    d=fw[fw.term.str.contains('gust')]
    blocks['F3']=table(['Sample','Term','LAD SE','Two-way SE','SE ratio'],[[names[r.model.replace('_final','')],term(r.term),num(r.se_lad),num(r.se_twoway),num(r.se_ratio,4)] for _,r in d.iterrows()])
    d=read('F/tables/F03_R2_DECOMPOSITION.csv')
    blocks['F2']=table(['Sample','Response','Added block','Cumulative OOF $R^2$','Sequential increment'],[[r['sample'].capitalize(), 'Exposure' if r.margin=='E0' else 'Recovery',r['group'],num(r.cum_r2),num(r.marginal)] for _,r in d.iterrows()])
    d=read('G/tables/GI_PREDICTION_METRICS.csv');panels=[]
    for key,subset in [('a',d[d.model_id=='final']),('b',d[(d.model_id.isin(['paper','hinge']))&(d.prediction_type=='LAD_OOF')])]:
        panels.append('**Table G4('+key+'). '+('Final specifications.' if key=='a' else 'Existing comparison specifications, LAD-OOF only.')+'**\n\n'+table(['Combination','Model / predictions','$n$','RMSE','MAE','Mean prediction','Bias','$R^2$','Correlation'],[[names[r.combination],r.model_id+' / '+r.prediction_type.replace('_',' '),f'{r.n:,}',num(r.rmse),num(r.mae),num(r.mean_prediction),num(r.bias),num(r.r2),num(r.correlation)] for _,r in subset.iterrows()]))
    blocks['G4']='\n\n'.join(panels)
    d=read('H/tables/H03_GUST_COMPARISON.csv')
    panels=[]
    for key in ['E0_all','R0c_all']:
        rows=[]
        for _,r in d[d.combination==key].iterrows():
            rows.append([r.alternative,term(r.term),num(r.ols_coef),interval(r.ols_ci_lower,r.ols_ci_upper),num(r.glm_coef),interval(r.glm_ci_lower,r.glm_ci_upper),pv(r.glm_p_t_G1)])
        panels.append('**'+names[key]+'.**\n\n'+table(['Alternative','Term','OLS coefficient','OLS 95% CI','Alternative coefficient','Alternative 95% CI','Alternative $p$'],rows))
    blocks['H6']='\n\n'.join(panels)
    d=read('H/tables/H_ORDINAL_SUMMARY.csv')
    cats=['0','1–5','6–100','101–1000','>1000','$(0,3]$ h','$(3,12]$ h','$(12,48]$ h','>48 h']
    blocks['H1']=table(['Analysis','Category','$n$','Share (%)','Knots (m s$^{-1}$)'],[['Exposure' if r.margin=='E0' else 'Historical recovery',cats[i],'60,437' if r.margin=='E0' else '59,834',num(100*r.share,4),r.knots_m_s] for i,(_,r) in enumerate(d.iterrows())])
    d=read('H/tables/H_CONDITIONAL_COEFFICIENTS.csv');rows=[]
    for (margin,model),g in d[d.model!='negative_binomial'].groupby(['margin','model'],sort=False):
        vals=g.set_index('term_or_diagnostic').value
        lab={'logit_>= 1-5':'Binary: C>0','logit_>= 6-100':'Binary: C>5','logit_>= 101-1000':'Binary: C>100','logit_>= >1000':'Binary: C>1000','logit_>= 3-12 h':'Binary: duration>3 h','logit_>= 12-48 h':'Binary: duration>12 h','logit_>= >48 h':'Binary: duration>48 h','ordinal':'Ordered logit'}[model]
        rows.append(['Exposure' if margin=='E0' else 'Historical recovery',lab,num(vals['z_gust_0h']),num(vals.get('hinge_14',vals.get('hinge_17'))),num(vals.get('hinge_26',float('nan')))])
    blocks['H2']=table(['Analysis','Model','$z_g$ coefficient','First raw-gust hinge','Second raw-gust hinge'],rows)
    d=read('H/tables/H_CONDITIONAL_LOGNORMAL.csv')
    blocks['H3']=table(['Analysis','Sample / dispersion','$n$','Exceedance',r'$\theta$ (m s$^{-1}$)',r'$\beta$'],[['Exposure' if r.margin=='E0' else 'Historical recovery',r.spec.replace('lognormal_','').replace('_',' '),f'{r.n:,}',r.state,f'{r.theta_m_s:.7g}',f'{r.beta:.7g}'] for _,r in d.iterrows()])
    d=read('H/tables/H03_EVENT_CONDITIONAL_FREQUENCIES.csv'); panels=[]
    for prefix,threshold in [('E0','>100 customers'),('R0c','>12 hours')]:
        sel=d[(d.combination.str.startswith(prefix))&(d.threshold_label==threshold)]
        if sel.empty and prefix=='R0c':
            sel=d[(d.combination.str.startswith(prefix))&(d.exact_numeric_threshold==12)]
        rows=[]
        for b in sorted(sel.bin.unique()):
            a=sel[(sel.bin==b)&(sel.combination==prefix+'_all')].iloc[0]
            w=sel[(sel.bin==b)&(sel.combination==prefix+'_weather')].iloc[0]
            rows.append([f'({a.left:g}, {a.right:g}]',int(a.denominator),int(a.numerator),num(a.frequency,5),int(w.denominator),int(w.numerator),num(w.frequency,5)])
        panels.append('**'+('Exposure: $C>100$.' if prefix=='E0' else 'Current recovery: $D_B>12$ h.')+'**\n\n'+table(['Gust band (m s$^{-1}$)','All $n$','All exceedances','All frequency','Weather $n$','Weather exceedances','Weather frequency'],rows))
    blocks['H4']='\n\n'.join(panels)
    d=read('I/tables/GI_STORM_SAMPLES.csv');windows=read('I/data/GI_STORM_WINDOWS.csv').set_index('storm')
    blocks['I3']=table(['Window','Inclusive UTC dates','Exposure $n$','Recovery $n$','Zero/non-positive C excluded','Positive-C above cap (display only)'],[[storm_name(r.storm),windows.loc[r.storm,'start']+' to '+windows.loc[r.storm,'end'] if r.storm in windows.index else 'Deduplicated union',int(r.exposure_n),int(r.recovery_final_n),int(r.excluded_zero_or_negative_customers),int(r.display_only_above_cap)] for _,r in d.iterrows()])
    d=read('I/tables/GI_STORM_METRICS.csv');panels=[]
    for comb in ['E0_all','R0c_all']:
        g=d[(d.combination==comb)&(d.prediction_type=='in_sample')&(~d.excluded_from_primary_metrics)]
        panels.append('**'+names[comb]+'.**\n\n'+table(['Window','$n$','RMSE','MAE','Mean observed','Mean fitted','Bias','Correlation'],[[storm_name(r.storm),int(r.n),num(r.rmse),num(r.mae),num(r.mean_observed),num(r.mean_prediction),num(r.bias),num(r.correlation)] for _,r in g.iterrows()]))
    blocks['I2']='\n\n'.join(panels)
    d=read('J/tables/J_PROXY_LABELS.csv')
    blocks['J2']=table(['Outcome','$n$ LAD-days','Positive LAD-days','Frequency (%)'],[[target(r.target),f'{r.n:,}',f'{r.events:,}',num(100*r.rate,4)] for _,r in d.iterrows()])
    d=read('J/tables/J03_PAIRED_METRICS.csv').set_index('target')
    blocks['J28']=table(['Outcome','Proxy Brier','Grid-maximum Brier','Proxy minus grid Brier','Paired 95% interval'],[[target(k),num(d.loc[k,'proxy_brier'],9),num(d.loc[k,'grid_brier'],9),num(d.loc[k,'delta_brier'],9),interval(d.loc[k,'delta_brier_lo'],d.loc[k,'delta_brier_hi'],9)] for k in targets])
    for file,tab,ci,base in [('J04','J7','J8','A01'),('J05','J10','J11','M0')]:
        d=read('J/tables/'+file+'_METRICS.csv');u=read('J/tables/'+file+'_PAIRED_UNCERTAINTY.csv');candidates=list(d.candidate.unique())
        labels=[c.split('_')[0] for c in candidates]
        blocks[tab]=table(['Outcome']+labels,[[target(k)]+[num(d[(d.target==k)&(d.candidate==c)].iloc[0].brier,9) for c in candidates] for k in targets])
        rows=[]
        for k in targets:
            for c in candidates[1:]:
                r=d[(d.target==k)&(d.candidate==c)].iloc[0];q=u[(u.target==k)&(u.candidate==c)].iloc[0]
                rows.append([target(k),c.split('_')[0],num(r.absolute_gain,9),interval(q.absolute_gain_lo,q.absolute_gain_hi,9)])
        blocks[ci]=table(['Outcome','Candidate',base+' minus candidate Brier','Paired 95% interval'],rows)
    d=read('J/tables/J_TIME_METRICS.csv').set_index('target')
    blocks['J13']=table(['Outcome','Development rate (%)','Evaluation rate (%)','Mean prediction (%)','Bias (pp)','Model Brier','Constant Brier','BSS (%)'],[[target(k),num(d.loc[k,'development_rate']*100,5),num(d.loc[k,'observed_rate']*100,5),num(d.loc[k,'mean_prediction']*100,5),num(d.loc[k,'bias_probability_percentage_points'],5),num(d.loc[k,'model_brier'],9),num(d.loc[k,'baseline_brier'],9),num(d.loc[k,'brier_skill']*100,5)] for k in targets])
    d=read('J/tables/J_TIME_MONTHLY.csv');rows=[]
    for k in ['any_gt100','wthr_gt100']:
        for _,r in d[d.target==k].iterrows():
            rows.append([target(k),r.month+('*' if r.month=='2023-09' else ''),int(r.n),int(r.events),num(100*r.observed_rate,4),num(100*r.mean_prediction,4),num(r.model_brier,8),num(r.baseline_brier,8)])
    blocks['J14']=table(['Outcome','Month','$n$','Positives','Observed (%)','Predicted (%)','Model Brier','Constant Brier'],rows)
    d=read('J/tables/J_TIME_SUPPORT.csv')
    blocks['J15']=table(['Period','$n$','Mean','SD','Median','95th percentile','Outside development range'],[[r.period.capitalize(),f'{r.n:,}',num(r['mean'],4),num(r.sd,4),num(r.p50,4),num(r.p95,4),'—' if r.period=='development' else str(int(r.outside_development_range))] for _,r in d.iterrows()])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--insert',action='store_true');args=parser.parse_args()
    build();text=DRAFT.read_text(encoding='utf-8')
    if args.insert:
        for key,val in blocks.items():
            marker='{{TABLE_'+key+'}}'
            if text.count(marker)!=1:raise ValueError('Expected one marker: '+marker)
            text=text.replace(marker,'<!-- table:'+key+' start -->\n'+val+'\n<!-- table:'+key+' end -->')
        DRAFT.write_text(text,encoding='utf-8')
    checks={}
    for key,val in blocks.items():
        found=re.search(r'<!-- table:'+key+r' start -->\n(.*?)\n<!-- table:'+key+r' end -->',text,re.S)
        checks[key]=bool(found and found.group(1)==val)
    (HERE/'table_sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    (HERE/'table_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks))
    if not all(checks.values()):raise SystemExit(1)
