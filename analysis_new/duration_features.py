"""DD-DUR01 training-only weather threshold and fixed duration proxies."""
import numpy as np
import pandas as pd

MODELS=['M0','M1','M2']
FEATURES=['G','H','I','h','J','x']
PEAK_EDGES=np.r_[np.arange(0.,65.,5.),np.inf]


def threshold(hours, train):
    x=np.asarray(hours,dtype=float); train=np.asarray(train,dtype=bool)
    if x.ndim!=2 or x.shape[1]!=24 or len(train)!=len(x) or not train.any(): raise ValueError('Invalid training hour selection')
    if not np.isfinite(x).all() or (x<0).any(): raise ValueError('Invalid hourly weather')
    tau=float(np.quantile(x[train].ravel(),.9,method='linear'))
    if tau<=0: raise ValueError('Training hourly 90th percentile must be positive; no arbitrary replacement')
    return tau


def features(hours,tau):
    x=np.asarray(hours,dtype=float)
    if x.ndim!=2 or x.shape[1]!=24 or not np.isfinite(x).all() or (x<0).any() or not np.isfinite(tau) or tau<=0:
        raise ValueError('Expected 24 finite nonnegative hourly gusts and positive tau')
    H=(x>tau).sum(axis=1).astype(float)
    I=np.maximum(x*x-tau*tau,0.).sum(axis=1)
    J=I/(24*tau*tau)
    return pd.DataFrame(dict(G=x.max(axis=1),H=H,I=I,h=H/24.,J=J,x=np.log1p(J)))


def support(frame,scope,train):
    """Weather-only summaries; peak edges fixed in the protocol, no label bins."""
    rows=[]
    subsets={'full':np.ones(len(frame),dtype=bool)} if scope=='full' else {'train':train,'test':~train}
    for role,mask in subsets.items():
        g=frame.G.to_numpy()
        for lower,upper in [(0.,np.inf),*zip(PEAK_EDGES[:-1],PEAK_EDGES[1:])]:
            m=mask & (g>=lower) & (g<upper)
            for feature in FEATURES:
                x=frame.loc[m,feature].to_numpy(); n=len(x)
                row=dict(scope=scope,role=role,peak_lower=lower,peak_upper=upper,feature=feature,n=n,
                         zero_n=int((x==0).sum()),positive_n=int((x>0).sum()),
                         zero_fraction=float(np.mean(x==0)) if n else np.nan)
                row.update(dict(zip(['min','p05','p25','p50','p75','p95','max'],np.quantile(x,[0,.05,.25,.5,.75,.95,1]) if n else [np.nan]*7)))
                row['correlation_with_G']=float(np.corrcoef(x,g[m])[0,1]) if n>1 and np.std(x)>0 and np.std(g[m])>0 else np.nan
                rows.append(row)
    return rows
