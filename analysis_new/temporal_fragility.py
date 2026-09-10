"""Pure fixed-period DD-TIME01 helpers: no historical model audit or refitting."""
import csv
import numpy as np
import pandas as pd
from analysis_new.fragility_optimizer import fit, probabilities
from analysis_new.grid_fragility_validation import TARGETS
from analysis_new.dd_agg01_evaluation import calibration

PERIODS={'development':('2021-04-01','2023-09-29'),'evaluation':('2023-09-30','2024-03-31')}


def read_period(path,period):
    """Select by the saved date string BEFORE accessing numeric labels.

    The caller loads evaluation labels only after development artifacts are frozen.
    CSV parsing visits the source bytes; no nonselected outcome value is converted,
    collected, passed to the optimizer, or used in initialization/selection.
    """
    start,end=PERIODS[period]; rows=[]
    with open(path,encoding='utf-8-sig',newline='') as handle:
        for row in csv.DictReader(handle):
            if start<=row['date']<=end:
                selected=dict(LAD21CD=row['LAD21CD'],date=row['date'],gust=float(row['gust']))
                for t in TARGETS:
                    value=float(row[t])
                    if value not in (0,1): raise ValueError(f'Invalid binary label: {t}')
                    selected[t]=int(value)
                rows.append(selected)
    data=pd.DataFrame(rows,columns=['LAD21CD','date','gust',*TARGETS])
    if data.empty or data.duplicated(['LAD21CD','date']).any(): raise ValueError('Empty period or duplicated LAD-day')
    if not np.isfinite(data.gust).all() or data.gust.lt(0).any(): raise ValueError('Invalid existing proxy input')
    return data


def frozen_edges(development_probability):
    p=np.asarray(development_probability,dtype=float)
    if not len(p) or not np.isfinite(p).all() or (p<0).any() or (p>1).any(): raise ValueError('Invalid development probabilities')
    return np.unique(np.r_[0.,np.quantile(p,np.linspace(0,1,11),method='linear'),1.]).tolist()


def fit_development(development,progress=lambda *args,**kwargs:None):
    """Only a development-period frame is accepted; no evaluation argument exists."""
    a,b=PERIODS['development']
    if not development.date.between(a,b).all(): raise ValueError('Non-development rows passed to fit')
    fits=[]; candidates=[]; edges={}; predictions=development[['LAD21CD','date']].copy()
    for target in TARGETS:
        g=development.gust.to_numpy(); y=development[target].to_numpy(); baseline=float(y.mean())
        try:
            if len(np.unique(y))!=2: raise ValueError('Development outcome has fewer than two classes')
            result,records=fit(g,y)
        except Exception as exc:
            result=dict(theta=np.nan,beta=np.nan,p0=np.nan,nll=np.nan,valid=False,success=False,message=repr(exc),
                        n=len(y),events=int(y.sum()),weak_identification=False,selection_reason='invalid development fit; no borrowed parameters')
            records=[]
        result.update(target=target,scope='development',development_rate=baseline)
        # An invalid optimizer output is diagnostic only, never an effective forecast.
        p=probabilities(g,**{k:result[k] for k in ['theta','beta','p0']}) if result['valid'] else np.full(len(g),np.nan)
        edges[target]=frozen_edges(p) if result['valid'] else []
        predictions[target]=p; fits.append(result)
        for r in records:
            r.update(target=target,scope='development',selected=bool(r['method']==result.get('method') and r['start']==result.get('start')),
                     selection_reason=result['selection_reason'])
            candidates.append(r)
        progress('Development fit '+target,valid=result['valid'],message_detail=result['message'])
    return pd.DataFrame(fits),pd.DataFrame(candidates),edges,predictions


def score(y,p,baseline,valid):
    y=np.asarray(y,dtype=float); p=np.asarray(p,dtype=float)
    baseline_brier=float(np.mean((baseline-y)**2)); actual=float(y.mean())
    valid=bool(valid and np.isfinite(p).all() and (p>=0).all() and (p<=1).all())
    mean=float(p.mean()) if valid else np.nan
    bs=float(np.mean((p-y)**2)) if valid else np.nan
    return dict(n=len(y),events=int(y.sum()),valid_prediction=valid,model_brier=bs,baseline_brier=baseline_brier,
                brier_skill=1-bs/baseline_brier if valid and baseline_brier>0 else np.nan,
                mean_prediction=mean,observed_rate=actual,prediction_minus_observed=mean-actual,
                baseline_probability=baseline,baseline_minus_observed=baseline-actual)


def evaluate_frozen(evaluation,fits,edges):
    predictions=[]; metrics=[]; monthly=[]; bins=[]
    for f in fits.to_dict('records'):
        target=f['target']; y=evaluation[target].to_numpy()
        p=probabilities(evaluation.gust.to_numpy(),**{k:f[k] for k in ['theta','beta','p0']}) if f['valid'] else np.full(len(y),np.nan)
        frame=evaluation[['LAD21CD','date','gust']].copy()
        frame['target']=target; frame['y']=y; frame['prediction']=p; frame['baseline_prediction']=f['development_rate']
        frame['valid_prediction']=bool(f['valid']); frame['status']='valid' if f['valid'] else f['message']; predictions.append(frame)
        r=dict(target=target,**score(y,p,f['development_rate'],f['valid']))
        if f['valid']:
            records,_=calibration(y,{'temporal_model':p},target,edges=edges[target])
            for b in records: b['valid_prediction']=True
            nonempty=[b for b in records if b['n']>0]
            r['calibration_rmse']=float(np.sqrt(sum(b['n']*(b['mean_probability']-b['observed_frequency'])**2 for b in nonempty)/len(y)))
            bins.extend(records)
        else:
            bins.append(dict(target=target,candidate='temporal_model',bin=-1,lower=np.nan,upper=np.nan,n=0,events=0,
                             mean_probability=np.nan,observed_frequency=np.nan,sparse=True,valid_prediction=False))
            r['calibration_rmse']=np.nan
        metrics.append(r)
        for month,part in frame.groupby(frame.date.str[:7],sort=True):
            monthly.append(dict(target=target,month=month,start=part.date.min(),end=part.date.max(),lads=part.LAD21CD.nunique(),
                                **score(part.y,part.prediction,f['development_rate'],f['valid'])))
    return pd.concat(predictions,ignore_index=True),pd.DataFrame(metrics),pd.DataFrame(monthly),pd.DataFrame(bins)


def sample_summary(data,period):
    return [dict(period=period,target=t,start=data.date.min(),end=data.date.max(),lads=data.LAD21CD.nunique(),
                 days=data.date.nunique(),district_days=len(data),events=int(data[t].sum()),event_rate=float(data[t].mean())) for t in TARGETS]


def covariate_support(development,evaluation):
    rows=[]; lo=float(development.gust.min()); hi=float(development.gust.max())
    for period,data in [('development',development),('evaluation',evaluation)]:
        g=data.gust.to_numpy(); q=np.quantile(g,[0,.05,.25,.5,.75,.95,1])
        below=int((g<lo).sum()); above=int((g>hi).sum())
        rows.append(dict(period=period,n=len(data),mean=float(g.mean()),sd=float(g.std(ddof=1)),
                         **dict(zip(['min','p05','p25','p50','p75','p95','max'],q)),
                         below_development_range=below,above_development_range=above,outside_development_range=below+above,
                         outside_fraction=(below+above)/len(g),unit='m/s',definition='existing incident-anchor interpolated gust proxy'))
    return pd.DataFrame(rows)
