"""Command #36: re-check log-OLS model-form adequacy on the final corrected
samples (affected customers / restoration duration), by (1) refitting the
exposure and recovery models under alternative distributional assumptions
(Negative Binomial / Gamma / Tweedie GLM) that match the target's actual
support, and (2) running basic residual diagnostics on the log-OLS models
themselves. Read-only w.r.t. command #21's existing sample-construction
pipeline; this command only adds new comparison fits."""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from combined_sample_builder import build_combined_samples  # noqa: E402
from figure_style import apply_style  # noqa: E402

sys.path.insert(0, str(project_path('scripts/dev_sample_decontamination')))
from clean_sample_builder import v9  # noqa: E402

V11_SCRIPT = project_path('scripts/critical_wind_speed/critical_wind_speed_pipeline.py')
spec11 = importlib.util.spec_from_file_location("critical_wind_speed_pipeline", V11_SCRIPT)
v11 = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(v11)

OUT_DIR = result_path('final_combined_analysis')
RAW_DIR = OUT_DIR / "raw"
DIAG_DIR = RAW_DIR / "step40_residual_diagnostics"
DIAG_DIR.mkdir(parents=True, exist_ok=True)

GUST_TERMS = ["z_gust_0h", "z_gust_0h_sq"]


def log_step(msg):
    print(f"[step40] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        raise TypeError(str(type(o)))
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def extract_terms(params, pvalues, terms):
    rows = []
    for t in terms:
        if t not in params.index:
            rows.append({"term": t, "coefficient": None, "p_value": None, "note": "term not in model"})
            continue
        rows.append({"term": t, "coefficient": float(params[t]), "p_value": float(pvalues[t])})
    return rows


def residual_diagnostics(res, model_label, out_stub):
    resid = res.resid
    fitted = res.fittedvalues
    skew = float(stats.skew(resid, bias=False))
    kurt = float(stats.kurtosis(resid, fisher=True, bias=False))  # excess kurtosis (normal = 0)
    jb_stat, jb_p = stats.jarque_bera(resid)[:2]

    apply_style()
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.hexbin(fitted, resid, gridsize=60, cmap="viridis", mincnt=1, bins="log")
    ax.axhline(0, color="#d95f02", linewidth=1.0, linestyle="--")
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")
    ax.set_title(f"{model_label}: residuals vs. fitted", fontsize=10)
    fig.tight_layout()
    fig.savefig(DIAG_DIR / f"{out_stub}_resid_vs_fitted.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    sm.qqplot(resid, line="45", fit=True, ax=ax, markersize=1.5, alpha=0.3)
    ax.set_title(f"{model_label}: residual Q-Q plot", fontsize=10)
    fig.tight_layout()
    fig.savefig(DIAG_DIR / f"{out_stub}_qqplot.png", dpi=200)
    plt.close(fig)

    log_step(f"{model_label} residual diagnostics: n={len(resid)}, skew={skew:.4f}, "
              f"excess_kurtosis={kurt:.4f}, Jarque-Bera stat={jb_stat:.1f} (p={jb_p:.3g})")
    return {
        "model": model_label, "n": int(len(resid)),
        "skewness": skew, "excess_kurtosis": kurt,
        "jarque_bera_stat": float(jb_stat), "jarque_bera_p": float(jb_p),
        "resid_vs_fitted_png": str((DIAG_DIR / f"{out_stub}_resid_vs_fitted.png").relative_to(OUT_DIR)),
        "qqplot_png": str((DIAG_DIR / f"{out_stub}_qqplot.png").relative_to(OUT_DIR)),
    }


def main():
    log_step("Building command #21 final combined samples (read-only reuse)...")
    combined_wt, combined_e0, combined_r0cb, verification = build_combined_samples()
    log_step(f"E0 n={len(combined_e0)}, R0c n={len(combined_r0cb)}")

    results = {}

    # ---------------- E0 (exposure): log-OLS baseline ----------------
    log_step("Fitting E0 log-OLS baseline (command #21 spec, full sample)...")
    res_e0_ols, cov_e0, gust_mean_e0, gust_sd_e0, d_e0 = v11.fit_full_sample(
        combined_e0, "log1p_customers_v2", use_customers_covariate=False,
    )
    se_e0 = np.sqrt(np.maximum(np.diag(cov_e0.values), 0))
    z_e0 = res_e0_ols.params.to_numpy() / se_e0
    p_e0_clustered = 2 * stats.norm.sf(np.abs(z_e0))
    pvals_e0_clustered = pd.Series(p_e0_clustered, index=res_e0_ols.params.index)
    ols_e0_terms = extract_terms(res_e0_ols.params, pvals_e0_clustered, GUST_TERMS)
    log_step(f"E0 log-OLS gust terms (LAD-clustered p): {ols_e0_terms}")

    Xe0, _ = v9.design_train_valid(d_e0, d_e0, extra_scale_cols=None)
    groups_lad_e0 = pd.factorize(d_e0["LAD21CD"])[0]
    y_nb = d_e0["customers_v2_event_excl_reinterruptions"].astype(float)
    log_step(f"E0 raw target (customers_v2) for NB/Tweedie: min={y_nb.min()}, max={y_nb.max()}, "
              f"n_zero={(y_nb == 0).sum()}")

    # ---- Step 1: Negative Binomial GLM (NB2 MLE, log link by construction) ----
    nb_e0_result = None
    try:
        log_step("Fitting E0 Negative Binomial GLM (NB2 MLE)...")
        nb_model = sm.NegativeBinomial(y_nb, Xe0)
        nb_res = nb_model.fit(cov_type="cluster", cov_kwds={"groups": groups_lad_e0},
                               maxiter=200, disp=0, method="bfgs")
        nb_e0_terms = extract_terms(nb_res.params, nb_res.pvalues, GUST_TERMS)
        log_step(f"E0 NB GLM gust terms: {nb_e0_terms}, alpha={nb_res.params.get('alpha', np.nan):.4f}, "
                 f"converged={nb_res.mle_retvals.get('converged', 'n/a')}")
        nb_e0_result = {
            "terms": nb_e0_terms, "alpha": float(nb_res.params.get("alpha", np.nan)),
            "converged": bool(nb_res.mle_retvals.get("converged", False)),
            "llf": float(nb_res.llf), "n": int(nb_res.nobs),
        }
    except Exception as exc:
        log_step(f"E0 NB GLM FAILED: {exc!r}")
        nb_e0_result = {"error": str(exc)}

    # ---- Step 1b (optional): Tweedie GLM for E0 ----
    tw_e0_result = None
    try:
        log_step("Fitting E0 Tweedie GLM (var_power=1.5, log link)...")
        tw_model = sm.GLM(y_nb, Xe0, family=sm.families.Tweedie(
            var_power=1.5, link=sm.families.links.Log(), eql=True))
        tw_res = tw_model.fit(cov_type="cluster", cov_kwds={"groups": groups_lad_e0})
        tw_e0_terms = extract_terms(tw_res.params, tw_res.pvalues, GUST_TERMS)
        log_step(f"E0 Tweedie GLM gust terms: {tw_e0_terms}")
        tw_e0_result = {"terms": tw_e0_terms, "converged": bool(tw_res.converged), "n": int(tw_res.nobs)}
    except Exception as exc:
        log_step(f"E0 Tweedie GLM FAILED: {exc!r}")
        tw_e0_result = {"error": str(exc)}

    # ---------------- R0c (recovery): log-OLS baseline ----------------
    log_step("Fitting R0c log-OLS baseline (command #21 spec, full sample)...")
    res_r0c_ols, cov_r0c, gust_mean_r0c, gust_sd_r0c, d_r0c = v11.fit_full_sample(
        combined_r0cb, "log_duration_B_full_span_hours", use_customers_covariate=True,
    )
    se_r0c = np.sqrt(np.maximum(np.diag(cov_r0c.values), 0))
    z_r0c = res_r0c_ols.params.to_numpy() / se_r0c
    p_r0c_clustered = 2 * stats.norm.sf(np.abs(z_r0c))
    pvals_r0c_clustered = pd.Series(p_r0c_clustered, index=res_r0c_ols.params.index)
    ols_r0c_terms = extract_terms(res_r0c_ols.params, pvals_r0c_clustered, GUST_TERMS)
    log_step(f"R0c log-OLS gust terms (LAD-clustered p): {ols_r0c_terms}")

    Xr0c, _ = v9.design_train_valid(d_r0c, d_r0c, extra_scale_cols=["customers_v2_log1p"])
    groups_lad_r0c = pd.factorize(d_r0c["LAD21CD"])[0]
    y_gamma = d_r0c["duration_B_full_span_hours"].astype(float)
    log_step(f"R0c raw target (duration hours) for Gamma/Tweedie: min={y_gamma.min()}, max={y_gamma.max()}, "
              f"n_nonpositive={(y_gamma <= 0).sum()}")

    # ---- Step 2: Gamma GLM (log link) ----
    gamma_r0c_result = None
    try:
        log_step("Fitting R0c Gamma GLM (log link)...")
        gamma_model = sm.GLM(y_gamma, Xr0c, family=sm.families.Gamma(link=sm.families.links.Log()))
        gamma_res = gamma_model.fit(cov_type="cluster", cov_kwds={"groups": groups_lad_r0c})
        gamma_r0c_terms = extract_terms(gamma_res.params, gamma_res.pvalues, GUST_TERMS)
        log_step(f"R0c Gamma GLM gust terms: {gamma_r0c_terms}, converged={gamma_res.converged}")
        gamma_r0c_result = {"terms": gamma_r0c_terms, "converged": bool(gamma_res.converged), "n": int(gamma_res.nobs)}
    except Exception as exc:
        log_step(f"R0c Gamma GLM FAILED: {exc!r}")
        gamma_r0c_result = {"error": str(exc)}

    # ---- Step 2b (optional): Tweedie GLM for R0c ----
    tw_r0c_result = None
    try:
        log_step("Fitting R0c Tweedie GLM (var_power=1.5, log link)...")
        tw_model_r0c = sm.GLM(y_gamma, Xr0c, family=sm.families.Tweedie(
            var_power=1.5, link=sm.families.links.Log(), eql=True))
        tw_res_r0c = tw_model_r0c.fit(cov_type="cluster", cov_kwds={"groups": groups_lad_r0c})
        tw_r0c_terms = extract_terms(tw_res_r0c.params, tw_res_r0c.pvalues, GUST_TERMS)
        log_step(f"R0c Tweedie GLM gust terms: {tw_r0c_terms}")
        tw_r0c_result = {"terms": tw_r0c_terms, "converged": bool(tw_res_r0c.converged), "n": int(tw_res_r0c.nobs)}
    except Exception as exc:
        log_step(f"R0c Tweedie GLM FAILED: {exc!r}")
        tw_r0c_result = {"error": str(exc)}

    # ---------------- Step 3: residual diagnostics on the log-OLS models ----------------
    diag_e0 = residual_diagnostics(res_e0_ols, "E0 (log1p customers_v2)", "step40_E0")
    diag_r0c = residual_diagnostics(res_r0c_ols, "R0c (log duration_B)", "step40_R0c")

    # ---------------- assemble & save ----------------
    results = {
        "e0": {
            "n": int(len(combined_e0)),
            "log_ols_gust_terms_clustered": ols_e0_terms,
            "negative_binomial_gust_terms": nb_e0_result,
            "tweedie_gust_terms": tw_e0_result,
            "residual_diagnostics": diag_e0,
        },
        "r0c": {
            "n": int(len(combined_r0cb)),
            "log_ols_gust_terms_clustered": ols_r0c_terms,
            "gamma_gust_terms": gamma_r0c_result,
            "tweedie_gust_terms": tw_r0c_result,
            "residual_diagnostics": diag_r0c,
        },
    }
    (RAW_DIR / "step40_model_form_check.json").write_text(js(results), encoding="utf-8")
    log_step("Saved raw/step40_model_form_check.json")
    log_step("Done.")


if __name__ == "__main__":
    main()
