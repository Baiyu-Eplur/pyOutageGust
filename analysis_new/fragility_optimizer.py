"""DD-AGG01 shared stable Bernoulli MLE; exact grouping, no probability clipping in fit.

Coordinates: log(theta), log(beta), p0 / training event rate. The last coordinate
permits the exact p0=0 boundary. All candidates and folds share one finite budget.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import log_ndtr

RULES = dict(version='ddagg01-stable-v1', theta_bounds=[.1, 200.], beta_bounds=[.05, 5.],
             p0_bounds=[0., 1-1e-12], start_quantiles=[.75, .90, .98], start_beta=[.25,.6],
             start_background_fraction=[.25,.8], fixed_legal_start=[40.,.27,.0014],
             starts=13, maxiter=600, maxls=40, ftol=1e-13, gtol=1e-9,
             fallback='at most two Powell starts, maxiter=300, maxfev=3000',
             stationary_tolerance=1e-5, nll_tolerance=1e-5, prediction_std_min=1e-8,
             weak_id_nll_tolerance=.01, weak_id_parameter_ratio=1.25, seed=20260909)


DURATION_RULES = dict(gamma_bounds=[-20.,20.], gamma_coordinate='gamma * training feature RMS (no feature centering)',
                      starts=16, gamma_initial_scaled=[-1.,0.,1.], weak_gamma_scaled_span=.1)


def probabilities(g, theta, beta, p0, gamma=0., feature=None):
    g=np.asarray(g,dtype=float)
    if (g<0).any() or not np.isfinite(g).all(): raise ValueError('Invalid gust')
    z=np.full(g.shape,-np.inf); m=g>0
    z[m]=(np.log(g[m])-np.log(theta))/beta
    if feature is not None:
        feature=np.asarray(feature,dtype=float)
        if feature.shape!=g.shape or not np.isfinite(feature).all() or (feature<0).any() or (feature[~m]!=0).any():
            raise ValueError('Invalid duration feature or nonzero feature at zero gust')
        z[m]+=gamma*feature[m]
    return p0+(1-p0)*np.exp(log_ndtr(z))


class Objective:
    def __init__(self,g,y,feature=None):
        g=np.asarray(g,dtype=float); y=np.asarray(y,dtype=float)
        if len(g)!=len(y) or not np.isfinite(g).all() or (g<0).any() or not np.isin(y,[0,1]).all():
            raise ValueError('Invalid Bernoulli training rows')
        self.feature=None
        if feature is None:
            self.g,idx,self.n=np.unique(g,return_inverse=True,return_counts=True)
        else:
            feature=np.asarray(feature,dtype=float)
            if feature.shape!=g.shape or not np.isfinite(feature).all() or (feature<0).any() or (feature[g==0]!=0).any():
                raise ValueError('Invalid duration feature')
            pairs,idx,self.n=np.unique(np.column_stack([g,feature]),axis=0,return_inverse=True,return_counts=True)
            self.g,self.feature=pairs.T
            self.feature_scale=max(float(np.sqrt(np.mean(feature**2))),1e-6)
        self.k=np.bincount(idx,weights=y,minlength=len(self.g)); self.N=len(y)
        self.rate=float(y.mean()); self.scale=float(np.clip(self.rate,1e-6,1-1e-6))
        self.positive=self.g>0; self.lg=np.zeros_like(self.g); self.lg[self.positive]=np.log(self.g[self.positive])
        self.bounds=[(np.log(.1),np.log(200.)),(np.log(.05),np.log(5.)),(0.,(1-1e-12)/self.scale)]
        if self.feature is not None: self.bounds.append(tuple(v*self.feature_scale for v in DURATION_RULES['gamma_bounds']))

    def encode(self,theta,beta,p0,gamma=0.):
        values=[np.log(theta),np.log(beta),p0/self.scale]
        if self.feature is not None: values.append(gamma*self.feature_scale)
        return np.array(values)

    def decode(self,x):
        result=dict(theta=float(np.exp(x[0])),beta=float(np.exp(x[1])),p0=float(np.clip(x[2]*self.scale,0,1-1e-12)))
        if self.feature is not None: result['gamma']=float(x[3]/self.feature_scale)
        return result

    def value_gradient(self,x):
        f=self.decode(x); beta=f['beta']; p0=f['p0']
        z=(self.lg-x[0])/beta; z[~self.positive]=-np.inf
        base_z=z.copy()
        if self.feature is not None: z[self.positive]+=f['gamma']*self.feature[self.positive]
        lc=log_ndtr(z); ls=log_ndtr(-z)
        l0=np.log(p0) if p0>0 else -np.inf; l1=np.log1p(-p0)
        lp=np.logaddexp(l0,l1+lc); lq=l1+ls
        yes=self.k>0; no=self.n>self.k
        nll=-np.sum(self.k[yes]*lp[yes])-np.sum((self.n-self.k)[no]*lq[no])
        if not np.isfinite(nll): return 1e100,np.zeros(len(x))
        logphi=-.5*z*z-.5*np.log(2*np.pi)
        def exp_safe(v): return np.exp(np.minimum(v,650))
        a=exp_safe(l1+logphi-lp); b=exp_safe(logphi-ls)
        # At exact zero gust the CDF term is identically zero and has no theta/beta derivative.
        a[~self.positive]=0.; b[~self.positive]=0.
        dz=-self.k*a+(self.n-self.k)*b
        du=np.sum(-dz/beta)
        dv=np.sum(-dz[self.positive]*base_z[self.positive])
        ds=np.sum(-self.k*exp_safe(ls-lp)+(self.n-self.k)/(1-p0))*self.scale
        gradient=[du,dv,ds]
        if self.feature is not None: gradient.append(np.sum(dz*self.feature)/self.feature_scale)
        return float(nll/self.N),np.array(gradient)/self.N

    def nll(self,x): return self.value_gradient(x)[0]*self.N

    def diagnostics(self,x):
        f=self.decode(x); val,grad=self.value_gradient(x); projected=grad.copy(); hits=[]
        for j,(lo,hi) in enumerate(self.bounds):
            if x[j]<=lo+1e-6:
                hits.append(['theta_low','beta_low','p0_zero','gamma_low'][j])
                if projected[j]>0: projected[j]=0
            if x[j]>=hi-1e-6:
                hits.append(['theta_high','beta_high','p0_high','gamma_high'][j])
                if projected[j]<0: projected[j]=0
        pred=probabilities(self.g,**f,feature=self.feature); mu=float(np.average(pred,weights=self.n))
        sd=float(np.sqrt(np.average((pred-mu)**2,weights=self.n)))
        return dict(**f,nll=val*self.N,prediction_std=sd,projected_gradient=float(np.max(np.abs(projected))),
                    boundary=';'.join(hits),n_unique_values=len(self.g))


def fit(g,y,feature=None,baseline=None):
    obj=Objective(g,y,feature); rows=[]
    # Quantiles use THIS training predictor only. No full-sample parameters enter CV.
    scales=np.clip(np.quantile(np.asarray(g)[np.asarray(g)>0],RULES['start_quantiles']),.11,190.) if np.any(np.asarray(g)>0) else [1.,2.,3.]
    starts=[obj.encode(th,be,obj.rate*frac) for th in scales for be in RULES['start_beta'] for frac in RULES['start_background_fraction']]
    starts.append(obj.encode(*RULES['fixed_legal_start']))
    if feature is not None:
        if baseline is None: raise ValueError('Duration fit requires matched training-scope M0')
        # Same finite 16-start rule for M1/M2, using only this training scope.
        for i,x in enumerate(starts): x[3]=np.clip([-1.,0.,1.][i%3],*obj.bounds[3])
        starts=[obj.encode(**{k:baseline[k] for k in ['theta','beta','p0']},gamma=float(np.clip(v/obj.feature_scale,-20,20)))
                for v in [0.,-1.,1.]]+starts
    solutions=[]
    for i,x in enumerate(starts):
        rows.append(dict(start=i,method='initial',success=True,iterations=0,message='evaluated legal initial point',**obj.diagnostics(x)))
        result=minimize(obj.value_gradient,x,jac=True,method='L-BFGS-B',bounds=obj.bounds,
                        options={k:RULES[k] for k in ['maxiter','maxls','ftol','gtol']})
        record=dict(start=i,method='L-BFGS-B',success=bool(result.success),iterations=int(result.nit),message=str(result.message),**obj.diagnostics(result.x))
        rows.append(record); solutions.append((result.x,record))
    best=min(solutions,key=lambda x:x[1]['nll'])
    def acceptable(r):
        return r['success'] and np.isfinite(r['nll']) and r['projected_gradient']<=RULES['stationary_tolerance']
    minimum_seen=min(r['nll'] for r in rows)
    if not acceptable(best[1]) or best[1]['nll']>minimum_seen+RULES['nll_tolerance'] or best[1]['prediction_std']<RULES['prediction_std_min']:
        for i,(x,_) in enumerate(sorted(solutions,key=lambda v:v[1]['nll'])[:2]):
            result=minimize(lambda v:obj.value_gradient(v)[0],x,method='Powell',bounds=obj.bounds,
                            options=dict(maxiter=300,maxfev=3000,xtol=1e-8,ftol=1e-12))
            r=dict(start=i,method='Powell_fallback',success=bool(result.success),iterations=int(result.nit),message=str(result.message),**obj.diagnostics(result.x))
            rows.append(r); solutions.append((result.x,r))
    finite=[r for _,r in solutions if np.isfinite(r['nll'])]
    best=min(finite,key=lambda r:r['nll'])
    minimum_seen=min(r['nll'] for r in rows)
    near=[r for r in finite if r['nll']<=best['nll']+RULES['weak_id_nll_tolerance']]
    weak=(max(r['theta'] for r in near)/min(r['theta'] for r in near)>1.25 or
          max(r['beta'] for r in near)/min(r['beta'] for r in near)>1.25 or bool(best['boundary']))
    if feature is not None:
        weak=weak or (max(r['gamma'] for r in near)-min(r['gamma'] for r in near))*obj.feature_scale>DURATION_RULES['weak_gamma_scaled_span'] or np.std(feature)==0
    constant_nll=float(-obj.N*(obj.rate*np.log(obj.rate)+(1-obj.rate)*np.log1p(-obj.rate))) if 0<obj.rate<1 else 0.
    valid=bool(acceptable(best) and best['nll']<=minimum_seen+RULES['nll_tolerance'] and
               best['nll']<=constant_nll+RULES['nll_tolerance'] and best['prediction_std']>=RULES['prediction_std_min'] and 0<obj.rate<1)
    summary=dict(**best,n=obj.N,events=int(obj.k.sum()),constant_nll=constant_nll,
                 nll_improvement_vs_constant=constant_nll-best['nll'],valid=valid,weak_identification=bool(weak),
                 theta_outside_support=bool(best['theta']<np.min(g) or best['theta']>np.max(g)),
                 support_min=float(np.min(g)),support_max=float(np.max(g)),near_optimal_solutions=len(near),
                 selection_reason='minimum evaluated optimized NLL; validity separately requires convergence, projected stationarity, no better evaluated point, and nonconstant predictions')
    if feature is not None:
        baseline_nll=obj.nll(obj.encode(**{k:baseline[k] for k in ['theta','beta','p0']},gamma=0.))
        summary.update(baseline_nll=baseline_nll, nll_gain_vs_m0=baseline_nll-best['nll'],
                       gamma_coordinate_scale=obj.feature_scale,feature_min=float(np.min(feature)),feature_max=float(np.max(feature)),
                       near_optimal_gamma_span=max(r['gamma'] for r in near)-min(r['gamma'] for r in near))
        summary['valid']=bool(valid and best['nll']<=baseline_nll+RULES['nll_tolerance'])
    return summary,rows
