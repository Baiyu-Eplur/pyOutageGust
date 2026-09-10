"""Five DD-AGG01 aggregations of the SAME 24 hourly gust observations per UTC day."""
import numpy as np

CANDIDATES=['A01_daily_max','A02_daily_mean','A03_daily_q90','A04_top3_mean','A05_max_rolling3h_mean']
LABELS=['Daily maximum gust','Mean hourly gust within day','90th percentile hourly gust',
        'Mean of highest 3 hourly gusts','Maximum within-day rolling 3h mean gust']


def aggregate(hours):
    x=np.asarray(hours,dtype=float)
    if x.ndim!=2 or x.shape[1]!=24 or not np.isfinite(x).all() or (x<0).any():
        raise ValueError('Each UTC day must contain the same 24 valid nonnegative hourly gusts')
    ordered=np.sort(x,axis=1)
    return np.column_stack([x.max(axis=1),x.mean(axis=1),.3*ordered[:,20]+.7*ordered[:,21],
                            ordered[:,-3:].mean(axis=1),
                            ((x[:,:22]+x[:,1:23]+x[:,2:24])/3).max(axis=1)])
