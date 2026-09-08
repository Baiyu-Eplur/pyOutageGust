from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import SplineTransformer


RUN = Path(__file__).resolve().parents[1]
X02 = RUN.parents[1]
CLAUDE = X02.parents[1]
EVENTS = CLAUDE / "paper_revision_work_v2" / "R02" / "data" / "R02_event_master.parquet"
SEED = 20260907
TASKS = ["E_log", "R_log", "R_C_log"]
MODELS = ["B00", "B01", "G02", "P00", "P02", "S01", "S02", "S03", "S04", "G05", "S05"]
STORM_MODELS = {"B00", "B01", "S01", "S02", "S03", "S04", "S05"}
ALL_MODELS = set(MODELS) - STORM_MODELS
DEV_GROUPS = ["P1", "P2", "P3"]
ALL_GROUPS = ["P1", "P2", "P3", "P4", "P5"]
NUM_CONTROL = ["pressure_msl_0h", "temperature_0h", "precipitation_24h_sum", "log_population",
               "urban_binary", "deprivation_gap_pct", "morans_i", "income_deprivation_rate",
               "season_sin", "season_cos", "time_trend"]
CAT_CONTROL = ["licence_area", "rural_urban_classification"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(s: str) -> str:
    return hashlib.sha256(("X02|" + str(s)).encode()).hexdigest()[:20]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_data(before_cutoff_only: bool = False, test_only: bool = False) -> pd.DataFrame:
    cols = ["Incident Reference", "event_time_proxy_utc", "max_stage_end_utc",
            "customers_v2_event_excl_reinterruptions", "duration_B_full_span_hours",
            "gust_0h", "pressure_msl_0h", "temperature_0h", "precipitation_24h_sum",
            "licence_area", "rural_urban_classification", "urban_binary", "deprivation_gap_pct",
            "morans_i", "income_deprivation_rate", "log_population", "candidate_main_E0", "candidate_main_R0c"]
    d = pd.read_parquet(EVENTS, columns=cols)
    mem = pd.read_parquet(RUN / "EPISODE_MEMBERSHIP.parquet", columns=["Incident Reference", "storm_names", "protected_group", "episode_id"])
    d = d.merge(mem, on="Incident Reference", validate="one_to_one")
    d["event_time_proxy_utc"] = pd.to_datetime(d.event_time_proxy_utc, utc=True)
    d["max_stage_end_utc"] = pd.to_datetime(d.max_stage_end_utc, utc=True)
    cfg = json.loads((RUN / "run_config.yaml").read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(cfg["time_path"]["fit_cutoff_utc"])
    if before_cutoff_only:
        d = d[d.event_time_proxy_utc.lt(cutoff)].copy()
    if test_only:
        d = d[d.protected_group.isin(["P4", "P5"])].copy()
    t = d.event_time_proxy_utc
    doy = t.dt.dayofyear + (t.dt.hour + t.dt.minute / 60) / 24
    year_days = np.where(t.dt.is_leap_year, 366.0, 365.0)
    d["season_sin"] = np.sin(2 * np.pi * (doy - 1) / year_days)
    d["season_cos"] = np.cos(2 * np.pi * (doy - 1) / year_days)
    d["time_trend"] = (t - pd.Timestamp("2021-04-01T00:00:00Z")).dt.total_seconds() / (365.2425 * 86400)
    d["storm_flag"] = d.protected_group.ne("NONE").astype(float)
    c = pd.to_numeric(d.customers_v2_event_excl_reinterruptions, errors="coerce").astype(float)
    dur = pd.to_numeric(d.duration_B_full_span_hours, errors="coerce").astype(float)
    d["target_E_log"] = np.log1p(c)
    d["target_R_log"] = np.log(dur.where(dur.gt(0)))
    d["target_R_C_log"] = d["target_R_log"]
    d["final_C_log"] = np.log1p(c)
    d["final_C_log_sq"] = d.final_C_log ** 2
    d["eligible_E_log"] = d.candidate_main_E0.astype(bool) & c.ge(0)
    d["eligible_R_log"] = d.candidate_main_R0c.astype(bool) & dur.gt(0)
    d["eligible_R_C_log"] = d["eligible_R_log"] & c.ge(0)
    d["anon_event_id"] = d["Incident Reference"].map(stable_id)
    return d.reset_index(drop=True)


def target_col(task: str) -> str:
    return "target_" + task


def eligible_mask(d: pd.DataFrame, task: str) -> pd.Series:
    return d["eligible_" + task].astype(bool)


@dataclass
class Encoder:
    numeric: list[str]
    categorical: list[str]
    means: dict[str, float] | None = None
    scales: dict[str, float] | None = None
    levels: dict[str, list[str]] | None = None
    feature_names: list[str] | None = None

    def fit(self, d: pd.DataFrame) -> "Encoder":
        self.means, self.scales, self.levels, self.feature_names = {}, {}, {}, []
        for c in self.numeric:
            x = pd.to_numeric(d[c], errors="coerce").astype(float)
            mean = float(x.mean()) if x.notna().any() else 0.0
            sd = float(x.std(ddof=0)) if x.notna().any() else 1.0
            if not np.isfinite(sd) or sd <= 1e-12:
                sd = 1.0
            self.means[c], self.scales[c] = mean, sd
            self.feature_names.append(c)
        for c in self.categorical:
            lv = sorted(d[c].fillna("<missing>").astype(str).unique().tolist())
            self.levels[c] = lv
            for x in lv[1:]:
                self.feature_names.append(f"{c}={x}")
        return self

    def transform(self, d: pd.DataFrame) -> np.ndarray:
        arrays = []
        for c in self.numeric:
            x = pd.to_numeric(d[c], errors="coerce").astype(float).fillna(self.means[c]).to_numpy()
            arrays.append(((x - self.means[c]) / self.scales[c])[:, None])
        for c in self.categorical:
            x = d[c].fillna("<missing>").astype(str).to_numpy()
            lv = self.levels[c]
            if len(lv) > 1:
                arrays.append(np.column_stack([(x == z).astype(float) for z in lv[1:]]))
        return np.column_stack(arrays) if arrays else np.empty((len(d), 0))


def add_gust_columns(d: pd.DataFrame, model: str) -> tuple[pd.DataFrame, list[str]]:
    x = d.copy()
    extra: list[str] = []
    if model in {"S01"}:
        extra = ["gust_0h"]
    elif model in {"G02", "S02", "P00", "P02"}:
        x["gust_sq"] = pd.to_numeric(x.gust_0h, errors="coerce") ** 2
        extra = ["gust_0h", "gust_sq"]
    if model in {"P00", "P02"}:
        extra += ["storm_flag"]
    if model == "P02":
        x["storm_gust"] = x.storm_flag * x.gust_0h
        x["storm_gust_sq"] = x.storm_flag * x.gust_sq
        extra += ["storm_gust", "storm_gust_sq"]
    return x, extra


def task_controls(task: str) -> list[str]:
    return NUM_CONTROL + (["final_C_log", "final_C_log_sq"] if task == "R_C_log" else [])


def penalized_fit(X: np.ndarray, y: np.ndarray, lam: float, penalty: np.ndarray | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    A = np.column_stack([np.ones(len(X)), X])
    rank = int(np.linalg.matrix_rank(A))
    if penalty is None:
        penalty = np.ones(A.shape[1]); penalty[0] = 0
    if lam == 0 and np.allclose(penalty[1:], 1):
        beta, _, _, s = np.linalg.lstsq(A, y, rcond=None)
        cond = float(s.max()/s.min()) if len(s) and s.min() > 0 else math.inf
    else:
        P = np.diag(penalty) if penalty.ndim == 1 else penalty
        beta = np.linalg.pinv(A.T @ A / len(A) + lam * P) @ (A.T @ y / len(A))
        cond = float(np.linalg.cond(A.T @ A / len(A) + lam * P))
    return beta, {"rank": rank, "columns": int(A.shape[1]), "condition_number": cond}


def fit_model(train: pd.DataFrame, task: str, model: str, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    y = train[target_col(task)].to_numpy(float)
    logs: list[dict[str, Any]] = []
    if model == "B00":
        return {"model": model, "task": task, "mean": float(np.mean(y)), "training_n": len(train)}, logs
    if model in {"B01", "G02", "P00", "P02", "S01", "S02"}:
        z, extra = add_gust_columns(train, model)
        enc = Encoder(task_controls(task) + extra, CAT_CONTROL).fit(z)
        X = enc.transform(z)
        beta, diag = penalized_fit(X, y, float(cfg["lambda"]))
        return {"model": model, "task": task, "cfg": cfg, "encoder": enc, "beta": beta, "diag": diag, "training_n": len(train)}, logs
    if model == "S03":
        enc = Encoder(task_controls(task), CAT_CONTROL).fit(train)
        C = enc.transform(train)
        spl = SplineTransformer(n_knots=int(cfg["n_knots"]), degree=3, knots="quantile", include_bias=False, extrapolation="linear")
        B = spl.fit_transform(train[["gust_0h"]].to_numpy(float))
        bmean = B.mean(axis=0); bscale = B.std(axis=0); bscale[bscale <= 1e-12] = 1
        Bs = (B-bmean)/bscale
        X = np.column_stack([C, Bs])
        p = 1 + X.shape[1]
        P = np.zeros((p,p))
        P[1:1+C.shape[1],1:1+C.shape[1]] = np.eye(C.shape[1]) * float(cfg["control_lambda"])
        nb = Bs.shape[1]
        if nb >= 3:
            D2 = np.diff(np.eye(nb), n=2, axis=0)
            P[1+C.shape[1]:,1+C.shape[1]:] = float(cfg["difference_penalty"]) * (D2.T@D2)
        A = np.column_stack([np.ones(len(X)), X])
        beta = np.linalg.pinv(A.T@A/len(A)+P)@(A.T@y/len(A))
        diag = {"rank": int(np.linalg.matrix_rank(A)), "columns": int(A.shape[1]), "basis_functions": int(nb),
                "knots": spl.bsplines_[0].t.tolist(), "condition_number": float(np.linalg.cond(A.T@A/len(A)+P)),
                "training_gust_min": float(train.gust_0h.min()), "training_gust_max": float(train.gust_0h.max())}
        return {"model": model, "task": task, "cfg": cfg, "encoder": enc, "spline": spl, "basis_mean": bmean, "basis_scale": bscale, "beta": beta, "diag": diag, "training_n": len(train)}, logs
    if model == "S04":
        enc = Encoder(task_controls(task), CAT_CONTROL).fit(train)
        C = enc.transform(train)
        A0 = np.column_stack([np.ones(len(C)), C])
        g = train.gust_0h.to_numpy(float)
        q = np.quantile(g, [.01,.10,.50,.75,.90,.99])
        lo, hi = float(q[0]), float(q[-1])
        lam = float(cfg["control_lambda"])
        P0 = np.diag(np.r_[0., np.repeat(lam, C.shape[1])])
        def phi(tau: float, h: float, gg: np.ndarray = g) -> np.ndarray:
            return h*np.logaddexp(0, (gg-tau)/h) - h*np.logaddexp(0, (9.-tau)/h)
        def profile(tau: float, h: float) -> tuple[float, np.ndarray]:
            ph = phi(tau,h)
            A = np.column_stack([A0, ph])
            P = np.zeros((A.shape[1], A.shape[1])); P[:-1,:-1] = P0
            beta = np.linalg.pinv(A.T@A/len(A)+P)@(A.T@y/len(A))
            if beta[-1] < 0:
                b0 = np.linalg.pinv(A0.T@A0/len(A0)+P0)@(A0.T@y/len(A0))
                beta = np.r_[b0, 0.]
            pred = A@beta
            obj = float(np.mean((y-pred)**2)+lam*np.sum(beta[1:1+C.shape[1]]**2))
            return obj,beta
        starts = [(float(t),h) for t in np.unique(q[[1,2,3,4]]) for h in [.5,2.,5.]]
        best = None
        for tau0,h0 in starts:
            def objective(v: np.ndarray) -> float:
                return profile(float(v[0]), float(np.exp(v[1])))[0]
            res = minimize(objective, np.array([tau0,np.log(h0)]), method="L-BFGS-B", bounds=[(lo,hi),(np.log(.05),np.log(20.))], options={"maxiter":80,"ftol":1e-10})
            tau,h = float(res.x[0]),float(np.exp(res.x[1])); obj,beta=profile(tau,h)
            item={"start_tau":tau0,"start_h":h0,"tau":tau,"h":h,"b":float(beta[-1]),"objective":obj,"success":bool(res.success),"status":int(res.status),"message":str(res.message),"iterations":int(res.nit),"tau_at_bound":bool(abs(tau-lo)<1e-6 or abs(tau-hi)<1e-6),"h_at_bound":bool(abs(h-.05)<1e-6 or abs(h-20)<1e-6),"b_at_bound":bool(beta[-1]<=1e-10)}
            logs.append(item)
            if best is None or obj < best[0]: best=(obj,tau,h,beta,item)
        assert best is not None
        _,tau,h,beta,item=best
        return {"model":model,"task":task,"cfg":cfg,"encoder":enc,"beta":beta,"tau":tau,"h":h,"diag":item,"training_n":len(train),"training_gust_min":float(g.min()),"training_gust_max":float(g.max())},logs
    if model in {"G05", "S05"}:
        enc = Encoder(task_controls(task)+["gust_0h"], CAT_CONTROL).fit(train)
        X = enc.transform(train)
        est = HistGradientBoostingRegressor(loss="squared_error", learning_rate=.05, max_iter=200, early_stopping=False,
                                            l2_regularization=1, max_leaf_nodes=int(cfg["max_leaf_nodes"]),
                                            min_samples_leaf=int(cfg["min_samples_leaf"]), random_state=SEED)
        est.fit(X,y)
        return {"model":model,"task":task,"cfg":cfg,"encoder":enc,"estimator":est,"training_n":len(train),"diag":{"n_iter":int(est.n_iter_)}},logs
    raise ValueError(model)


def predict_model(fit: dict[str, Any], test: pd.DataFrame) -> np.ndarray:
    model=fit["model"]
    if model=="B00": return np.repeat(fit["mean"],len(test))
    if model in {"B01","G02","P00","P02","S01","S02"}:
        z,_=add_gust_columns(test,model); X=fit["encoder"].transform(z); return np.column_stack([np.ones(len(X)),X])@fit["beta"]
    if model=="S03":
        C=fit["encoder"].transform(test); B=fit["spline"].transform(test[["gust_0h"]].to_numpy(float)); Bs=(B-fit["basis_mean"])/fit["basis_scale"]
        return np.column_stack([np.ones(len(C)),C,Bs])@fit["beta"]
    if model=="S04":
        C=fit["encoder"].transform(test); g=test.gust_0h.to_numpy(float); tau,h=fit["tau"],fit["h"]
        ph=h*np.logaddexp(0,(g-tau)/h)-h*np.logaddexp(0,(9.-tau)/h)
        return np.column_stack([np.ones(len(C)),C,ph])@fit["beta"]
    if model in {"G05","S05"}: return fit["estimator"].predict(fit["encoder"].transform(test))
    raise ValueError(model)


def model_grid(model: str) -> list[dict[str, Any]]:
    return json.loads((RUN/"MODEL_REGISTRY.json").read_text(encoding="utf-8"))[model]["grid"]


def group_bounds(d: pd.DataFrame, group: str) -> tuple[pd.Timestamp,pd.Timestamp]:
    # Frozen process intervals, not observed event extrema.
    bounds={"P1":("2021-11-25","2021-11-29"),"P2":("2022-02-15","2022-02-23"),"P3":("2023-10-17","2023-10-23"),"P4":("2023-10-31","2023-11-04"),"P5":("2024-01-01","2024-01-04")}
    lo,hi=bounds[group]; return pd.Timestamp(lo,tz="UTC"),pd.Timestamp(hi,tz="UTC")


def interval_intersects(d: pd.DataFrame, groups: list[str]) -> pd.Series:
    out=pd.Series(False,index=d.index)
    for g in groups:
        lo,hi=group_bounds(d,g); lo-=pd.Timedelta(hours=48); hi+=pd.Timedelta(hours=48)
        out |= d.event_time_proxy_utc.lt(hi) & d.max_stage_end_utc.ge(lo)
    return out


def training_mask(d: pd.DataFrame, task: str, model: str, train_groups: list[str], held_groups: list[str], time_path: bool) -> pd.Series:
    ok=eligible_mask(d,task)
    if model in STORM_MODELS:
        m=ok & d.protected_group.isin(train_groups) & ~interval_intersects(d,held_groups)
    else:
        m=ok & ~interval_intersects(d,held_groups)
    if time_path:
        cutoff=pd.Timestamp(json.loads((RUN/"run_config.yaml").read_text(encoding="utf-8"))["time_path"]["fit_cutoff_utc"])
        m &= d.max_stage_end_utc.lt(cutoff)
    return m


def validation_mask(d: pd.DataFrame, task: str, group: str) -> pd.Series:
    return eligible_mask(d,task) & d.protected_group.eq(group)


def metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float | int | None]:
    e=y-pred; sse=float(np.sum(e**2)); sst=float(np.sum((y-y.mean())**2)); n=len(y)
    pear=float(pearsonr(y,pred).statistic) if n>2 and np.std(pred)>1e-12 and np.std(y)>1e-12 else None
    spear=float(spearmanr(y,pred).statistic) if n>2 and np.std(pred)>1e-12 and np.std(y)>1e-12 else None
    slope=float(np.cov(pred,y,ddof=0)[0,1]/np.var(pred)) if np.var(pred)>1e-12 else None
    intercept=float(y.mean()-slope*pred.mean()) if slope is not None else None
    return {"n":n,"mse":float(np.mean(e**2)),"rmse":float(np.sqrt(np.mean(e**2))),"mae":float(np.mean(np.abs(e))),"r2":float(1-sse/sst) if sst>1e-15 else None,
            "mean_y":float(y.mean()),"mean_pred":float(pred.mean()),"residual_mean":float(e.mean()),"sd_ratio":float(np.std(pred,ddof=1)/np.std(y,ddof=1)) if n>1 and np.std(y,ddof=1)>0 else None,
            "pearson":pear,"spearman":spear,"calibration_intercept":intercept,"calibration_slope":slope,
            "sse":sse,"sse_between_process_mean":float(n*e.mean()**2),"sse_within_process":float(np.sum((e-e.mean())**2))}


def save_fit(fit: dict[str,Any], path: Path, train: pd.DataFrame) -> dict[str,str]:
    path.parent.mkdir(parents=True,exist_ok=True); joblib.dump(fit,path)
    ids=path.with_suffix(".fit_ids.parquet")
    train[["anon_event_id","Incident Reference","event_time_proxy_utc","max_stage_end_utc","protected_group"]].to_parquet(ids,index=False)
    return {"model_sha256":sha256(path),"fit_ids_sha256":sha256(ids),"model_path":str(path),"fit_ids_path":str(ids)}
