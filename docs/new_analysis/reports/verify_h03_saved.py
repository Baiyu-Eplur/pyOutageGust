"""Limited read-only H03 reconstruction; never calls a fitting method.

Run from any directory with the project Python. Writes only this report's JSON.
Reconstructs score/Hessian at saved parameters, not another model estimate.
"""
from pathlib import Path
import sys,json,hashlib
from datetime import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
H=ROOT/'results/Appendix/H'
def read(p):return pd.read_csv(p,float_precision='round_trip')
def js(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
def close(name,a,b,atol=1e-8,rtol=1e-8):
    check(name,np.allclose(a,b,atol=atol,rtol=rtol,equal_nan=True),dict(max_abs_difference=float(np.nanmax(abs(np.asarray(a)-np.asarray(b)))) if np.isfinite(np.asarray(a)-np.asarray(b)).any() else None,atol=atol,rtol=rtol))
coeff=read(H/'tables/H03_FULL_COEFFICIENTS.csv');records=[]
for combo,family in [('E0_all','NB2'),('E0_all','Tweedie'),('R0c_all','Gamma'),('R0c_all','Tweedie')]:
    prefix=f'H03_{combo}_{family}';d=js(H/f'data/{prefix}_DIAGNOSTICS.json');records.append(d)
    row=read(H/f'data/H03_{combo}_ROWS.csv.gz');X=read(H/f'data/H03_{combo}_DESIGN.csv.gz');spec=js(H/f'data/H03_{combo}_SPECIFICATION.json')
    check(prefix+'/rows',len(row)==spec['n'] and row.observation_id.is_unique and row.observation_id.equals(X.observation_id))
    check(prefix+'/legal response',((row.raw_response>=0)&row.raw_response.eq(np.floor(row.raw_response))).all() if combo.startswith('E0') else row.raw_response.gt(0).all())
    X=X.drop(columns='observation_id');check(prefix+'/column order',list(X)==spec['full_design']['columns'])
    candidate=coeff[coeff.combination.eq(combo)&coeff.model.eq(family)]
    if not d['point_valid']:
        check(prefix+'/unavailable disclosed',not candidate.interval_valid.any(),d.get('error',d.get('covariance_error','invalid point diagnostic')))
        continue
    pars=read(H/f'data/{prefix}_PARAMETERS.csv');beta=pars.coef.to_numpy();columns=pars.term.tolist();fit=read(H/f'data/{prefix}_FITTED.csv.gz')
    check(prefix+'/fitted row IDs',fit.observation_id.equals(row.observation_id))
    close(prefix+'/mean from saved design',np.exp(X.to_numpy()@beta[:X.shape[1]]),fit.mu)
    if family=='NB2':
        model=sm.NegativeBinomial(row.raw_response,X,loglike_method='nb2');model._transparams=False
        score=model.score_obs(beta);info=-model.hessian(beta)
        check(prefix+'/joint alpha',columns==[*X.columns,'alpha'] and beta[-1]>0)
    else:
        fam=sm.families.Gamma(link=sm.families.links.Log()) if family=='Gamma' else sm.families.Tweedie(var_power=1.5,link=sm.families.links.Log(),eql=True)
        model=sm.GLM(row.raw_response,X,family=fam)
        score=model.score_obs(beta,scale=d['scale']);info=-model.hessian(beta,scale=d['scale'],observed=True)
        close(prefix+'/Pearson scale',model.estimate_scale(fit.mu.to_numpy()),d['scale'])
    saved=read(H/f'data/{prefix}_SCORES.csv.gz');check(prefix+'/score row IDs',saved.observation_id.equals(row.observation_id))
    close(prefix+'/scores',score,saved[columns].to_numpy())
    def matrix(s):return read(H/f'data/{prefix}_{s}.csv').set_index('term').loc[columns,columns].to_numpy()
    close(prefix+'/observed information',info,matrix('OBSERVED_INFORMATION'))
    if d['covariance_status']=='unavailable':
        check(prefix+'/unavailable intervals',not candidate.interval_valid.any(),d.get('covariance_error'));continue
    bread=np.linalg.inv(info);cov={};n=len(row);k=len(columns)
    for label,key in [('LAD','lad_code'),('DATE','date_code'),('INTERSECTION','intersection_code')]:
        # Independent grouped score sum, not another fitting/covariance method.
        groups=row[key].to_numpy();ng=len(np.unique(groups));s=np.zeros((ng,k));np.add.at(s,groups,score)
        cov[label]=bread@(s.T@s)@bread.T*(ng/(ng-1)*(n-1)/(n-k))
        close(prefix+'/'+label+' covariance',cov[label],matrix('COV_'+label))
    both=cov['LAD']+cov['DATE']-cov['INTERSECTION'];savedv=matrix('COV_TWO_WAY')
    close(prefix+'/two-way covariance',both,savedv)
    check(prefix+'/finite symmetric',np.isfinite(savedv).all() and np.allclose(savedv,savedv.T))
    close(prefix+'/coefficient order',candidate.coef,beta)
    valid=candidate.interval_valid.to_numpy();diag=np.diag(savedv)
    check(prefix+'/negative variance disclosure',candidate.loc[diag<0,'se_twoway'].isna().all())
    close(prefix+'/SE squared',candidate.loc[valid,'se_twoway'].to_numpy()**2,diag[valid])
    se=candidate.loc[valid,'se_twoway'].to_numpy();df=spec['LAD_clusters']-1;critical=stats.t.ppf(.975,df)
    close(prefix+'/CI lower',beta[valid]-critical*se,candidate.loc[valid,'ci_lower'])
    close(prefix+'/CI upper',beta[valid]+critical*se,candidate.loc[valid,'ci_upper'])
    close(prefix+'/p t reference',2*stats.t.sf(abs(beta[valid]/se),df),candidate.loc[valid,'p_t_G1'])
freq=read(H/'tables/H03_EVENT_CONDITIONAL_FREQUENCIES.csv');valid=freq.denominator>0
close('empirical numerator/denominator',freq.loc[valid,'numerator']/freq.loc[valid,'denominator'],freq.loc[valid,'frequency'])
check('empty bins are NA',freq.loc[~valid,'frequency'].isna().all())
protected=js(ROOT/'docs/new_analysis/reports/APP_H03_PROTECTED_SNAPSHOT.json')
changed=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
check('A-G and I-J prior outputs unchanged',not changed,dict(files=len(protected),changed=changed))
check('H01/H02 preserved',js(H/'logs/H03_PRESERVATION.json')['all_unchanged'])
manifest=js(H/'manifest.json');bad=[v['path'] for v in manifest['outputs'] if sha(H/v['path'])!=v['sha256']]
check('managed output hashes',not bad,bad)
result=dict(time=datetime.now().astimezone().isoformat(),command=f'{sys.executable} -X utf8 -B docs/new_analysis/reports/verify_h03_saved.py',
    scope='limited saved-result arithmetic reconstruction, no fitting/CV/historical audit or scientific review',
    all_passed=all(c['passed'] for c in checks),checks=checks,candidate_status=[{k:d.get(k) for k in ['combination','model','point_valid','inference_valid']} for d in records])
out=Path(__file__).with_name('APP_H03_SAVED_VERIFICATION.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
print(json.dumps(dict(checks=len(checks),all_passed=result['all_passed'],failures=[c for c in checks if not c['passed']],output=str(out)),ensure_ascii=False,indent=2))
raise SystemExit(not result['all_passed'])
