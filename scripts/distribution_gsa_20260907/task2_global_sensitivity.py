"""Command #53, Task 2: global sensitivity analysis (Sobol' + PAWN) of the
fitted E0/R0c regression equations (Equation 4), using SALib. This is a
SEPARATE, INDEPENDENT analysis from Task 1 (distribution fitting) -- no
numbers or conclusions are shared between the two.

Tool choice: SALib (pip-installable, actively maintained, implements both
Sobol' and PAWN) is used instead of the SAFE Toolbox Python port, because
`safepython` is not available as a standard pip package in this environment
and SALib is functionally equivalent for the methods requested (Sobol'
first-/total-order indices, PAWN as a cross-check).

Design (read-only w.r.t. all fitted coefficients -- NO model refitting):
  - The regression equation's ALREADY-FITTED coefficients are read directly
    from the existing corrected LAD-clustered coefficient tables
    (E0_corrected_lad_cluster.csv / R0c_corrected_lad_cluster.csv, produced
    by command #45 on the C01+C02-C08 corrected final sample).
  - Focus inputs (varied in the GSA): standardized gust (z_gust_0h) and
    standardized pressure (z_pressure_msl_0h) for BOTH models; standardized
    log1p(affected customers) (z_log1p_customers_v2) ADDITIONALLY for R0c.
    The quadratic and interaction terms (z_gust_0h_sq, z_gust_pressure,
    z_log1p_customers_v2_sq) are NOT sampled as separate independent
    factors -- they are deterministic functions of the sampled gust/
    pressure/customers values, computed inside the model function itself.
    This is the statistically correct way to run Sobol' analysis on a model
    with polynomial/interaction structure: sampling the quadratic term as
    an "independent" input would violate Sobol's independence assumption
    and is a common implementation error, avoided here.
  - All remaining covariates (precipitation, temperature, log population,
    income deprivation rate, deprivation gap, Moran's I, urban/rural,
    year/month fixed effects) are FIXED as background at a constant value
    (same treatment for both models, as required). Because Sobol' variance
    decomposition is invariant to additive constants, the specific constant
    chosen for this fixed background does not affect any reported index --
    it is therefore omitted from the deterministic function entirely
    (equivalent to fixing it, since it only shifts the output by a constant
    that contributes zero variance).
  - Input sampling: SALib's Sobol' quasi-random [0,1] sequence is mapped to
    each focus variable's OWN EMPIRICAL marginal distribution via the
    inverse empirical CDF (quantile transform) computed from the observed
    z-scale values in the corrected combined sample -- this uses the
    "observed marginal distribution" option explicitly permitted by the
    command, rather than assuming a parametric shape.
  - Caveat (disclosed): standard Sobol' assumes independent inputs. The
    empirical correlation between the sampled variables is reported; if
    non-negligible, the reported indices should be read as computed under
    an independence approximation, not as a claim that the true inputs are
    independent.
"""
from __future__ import annotations

# Shared pretest paths; all execution is dispatched from main.py.
import sys as _pretest_sys
from pathlib import Path as _PretestPath
_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))
from pretest_paths import project_path, result_path, external_path, data_path, read_input


import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from SALib.sample.sobol import sample as sobol_sample
from SALib.analyze import sobol as sobol_analyze
from SALib.analyze import pawn as pawn_analyze

sys.path.insert(0, str(project_path('scripts/c02_c08_repair_20260905')))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

sys.path.insert(0, str(project_path('scripts/final_combined_analysis')))
from figure_style import apply_style, mm_to_in, save_fig, SINGLE_COL_MM  # noqa: E402

C0208_RAW = result_path('c02_c08_repair_20260905/raw')
RAW_DIR = result_path('distribution_gsa_20260907/raw')
FIG_DIR = result_path('distribution_gsa_20260907/figures')
RAW_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SOBOL_N = 8192  # power of 2, per SALib's recommendation for the Sobol' sequence
SEED = 20260907


def log_step(msg):
    print(f"[task2] {msg}", flush=True)


def js(obj):
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return str(o)
    return json.dumps(obj, ensure_ascii=False, indent=2, default=default)


def read_coef(csv_path, term):
    df = pd.read_csv(read_input(csv_path))
    return float(df.loc[df["term"] == term, "coef"].iloc[0])


def empirical_quantile_transform(u: np.ndarray, observed: np.ndarray) -> np.ndarray:
    """Map uniform [0,1] draws to the empirical distribution of `observed`
    via inverse-ECDF (linear interpolation on sorted observed values)."""
    sorted_obs = np.sort(observed)
    n = len(sorted_obs)
    positions = u * (n - 1)
    return np.interp(positions, np.arange(n), sorted_obs)


def run_gsa_for_model(model_name: str, coef_csv: Path, coefs_needed: dict, sample_df: pd.DataFrame,
                       z_cols: dict, extra_names: list):
    """coefs_needed: dict of term->coefficient value (already read).
    z_cols: dict mapping GSA variable name -> underlying z-scale column name in sample_df.
    extra_names: order of variable names for the SALib problem."""
    observed = {name: sample_df[z_cols[name]].astype(float).to_numpy() for name in extra_names}

    corr_matrix = pd.DataFrame(observed).corr()
    log_step(f"{model_name}: empirical correlation among focus inputs (z-scale):\n{corr_matrix.to_string()}")

    problem = {
        "num_vars": len(extra_names),
        "names": extra_names,
        "bounds": [[0.0, 1.0]] * len(extra_names),
    }

    param_values_unit = sobol_sample(problem, SOBOL_N, calc_second_order=True, seed=SEED)
    log_step(f"{model_name}: total model evaluations = {param_values_unit.shape[0]}")

    # empirical quantile transform, one variable at a time
    param_values = np.zeros_like(param_values_unit)
    for j, name in enumerate(extra_names):
        param_values[:, j] = empirical_quantile_transform(param_values_unit[:, j], observed[name])

    def model_func(X):
        gust_z = X[:, extra_names.index("gust_z")]
        pressure_z = X[:, extra_names.index("pressure_z")]
        eta = (coefs_needed["z_gust_0h"] * gust_z
               + coefs_needed["z_gust_0h_sq"] * gust_z ** 2
               + coefs_needed["z_pressure_msl_0h"] * pressure_z
               + coefs_needed["z_gust_pressure"] * gust_z * pressure_z)
        if "customers_z" in extra_names:
            cust_z = X[:, extra_names.index("customers_z")]
            eta = eta + coefs_needed["z_log1p_customers_v2"] * cust_z \
                + coefs_needed["z_log1p_customers_v2_sq"] * cust_z ** 2
        return eta

    Y = model_func(param_values)
    log_step(f"{model_name}: output eta -- mean={Y.mean():.4f}, std={Y.std(ddof=1):.4f}, "
              f"min={Y.min():.4f}, max={Y.max():.4f}")

    sobol_result = sobol_analyze.analyze(problem, Y, calc_second_order=True, print_to_console=False, seed=SEED)

    # PAWN cross-check (moment-independent, CDF-based)
    pawn_result = pawn_analyze.analyze(problem, param_values, Y, S=10, print_to_console=False, seed=SEED)

    summary_rows = []
    for i, name in enumerate(extra_names):
        summary_rows.append({
            "model": model_name, "variable": name,
            "S1": float(sobol_result["S1"][i]), "S1_conf": float(sobol_result["S1_conf"][i]),
            "ST": float(sobol_result["ST"][i]), "ST_conf": float(sobol_result["ST_conf"][i]),
            "ST_minus_S1": float(sobol_result["ST"][i] - sobol_result["S1"][i]),
            "PAWN_median": float(np.median(pawn_result["median"][i]))
            if hasattr(pawn_result["median"], "__len__") else float(pawn_result["median"][i]),
        })

    second_order_rows = []
    idx = 0
    for i in range(len(extra_names)):
        for j2 in range(i + 1, len(extra_names)):
            s2 = sobol_result["S2"][i, j2]
            s2c = sobol_result["S2_conf"][i, j2]
            second_order_rows.append({"model": model_name, "pair": f"{extra_names[i]} x {extra_names[j2]}",
                                        "S2": float(s2), "S2_conf": float(s2c)})

    log_step(f"{model_name} Sobol' summary:\n" + pd.DataFrame(summary_rows).to_string(index=False))
    log_step(f"{model_name} Sobol' second-order interactions:\n" + pd.DataFrame(second_order_rows).to_string(index=False))

    return summary_rows, second_order_rows, corr_matrix


def main():
    v9, _, _ = _patch_v9()
    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    # ---- read already-fitted coefficients (LAD-clustered, corrected data) ----
    e0_terms = ["z_gust_0h", "z_gust_0h_sq", "z_pressure_msl_0h", "z_gust_pressure"]
    e0_coefs = {t: read_coef(C0208_RAW / "E0_corrected_lad_cluster.csv", t) for t in e0_terms}
    log_step(f"E0 coefficients read from E0_corrected_lad_cluster.csv: {e0_coefs}")

    r0c_terms = e0_terms + ["z_log1p_customers_v2", "z_log1p_customers_v2_sq"]
    r0c_coefs = {t: read_coef(C0208_RAW / "R0c_corrected_lad_cluster.csv", t) for t in r0c_terms}
    log_step(f"R0c coefficients read from R0c_corrected_lad_cluster.csv: {r0c_coefs}")

    # ---- build the z-scale columns exactly as design_train_valid does (full-sample standardization) ----
    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    e0_sample_z = pd.DataFrame({"gust_z": Xe0["z_gust_0h"], "pressure_z": Xe0["z_pressure_msl_0h"]})

    r0c_df = combined_r0cb.copy()
    r0c_df["customers_v2_log1p"] = np.log1p(r0c_df["customers_v2_event_excl_reinterruptions"].astype(float))
    Xr0c, _ = v9.design_train_valid(r0c_df, r0c_df, extra_scale_cols=["customers_v2_log1p"])
    r0c_sample_z = pd.DataFrame({"gust_z": Xr0c["z_gust_0h"], "pressure_z": Xr0c["z_pressure_msl_0h"],
                                   "customers_z": Xr0c["z_log1p_customers_v2"]})

    all_summary, all_second_order = [], {}

    s1, so1, corr1 = run_gsa_for_model(
        "E0 (exposure)", C0208_RAW / "E0_corrected_lad_cluster.csv", e0_coefs,
        e0_sample_z, {"gust_z": "gust_z", "pressure_z": "pressure_z"}, ["gust_z", "pressure_z"])
    all_summary += s1
    all_second_order["E0"] = so1

    s2, so2, corr2 = run_gsa_for_model(
        "R0c (recovery)", C0208_RAW / "R0c_corrected_lad_cluster.csv", r0c_coefs,
        r0c_sample_z, {"gust_z": "gust_z", "pressure_z": "pressure_z", "customers_z": "customers_z"},
        ["gust_z", "pressure_z", "customers_z"])
    all_summary += s2
    all_second_order["R0c"] = so2

    summary_df = pd.DataFrame(all_summary)
    summary_df.to_csv(RAW_DIR / "task2_sobol_summary.csv", index=False)
    log_step("Saved task2_sobol_summary.csv")

    with open(RAW_DIR / "task2_second_order.json", "w", encoding="utf-8") as f:
        f.write(js(all_second_order))

    with open(RAW_DIR / "task2_input_correlations.json", "w", encoding="utf-8") as f:
        f.write(js({"E0": corr1.to_dict(), "R0c": corr2.to_dict()}))

    # ---- figure: grouped bar chart of S1 vs ST for both models ----
    apply_style()
    fig_w = mm_to_in(SINGLE_COL_MM) * 1.9
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w * 0.42))
    # NOTE: summary_df's "model" column uses internal labels ("E0 (exposure)" /
    # "R0c (recovery)") -- fine for a data CSV, but the FIGURE must not render
    # "E0"/"R0c" (per command #52's finding), so we map to formal names here.
    display_map = {"E0 (exposure)": "Exposure margin", "R0c (recovery)": "Recovery margin"}
    for ax, internal_name in zip(axes, ["E0 (exposure)", "R0c (recovery)"]):
        model_name = display_map[internal_name]
        sub = summary_df[summary_df["model"] == internal_name]
        x = np.arange(len(sub))
        width = 0.35
        ax.bar(x - width / 2, sub["S1"], width, label="First-order (S1)", color="#1b9e77")
        ax.bar(x + width / 2, sub["ST"], width, label="Total-order (ST)", color="#d95f02")
        ax.set_xticks(x)
        display_names = {"gust_z": "Gust", "pressure_z": "Pressure", "customers_z": "Affected\ncustomers"}
        ax.set_xticklabels([display_names[v] for v in sub["variable"]])
        ax.set_ylabel("Sobol' index")
        ax.set_title(model_name, fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    plt.tight_layout()
    save_fig(fig, FIG_DIR, "FigureI1_sobol_indices")
    plt.close(fig)
    log_step("Saved FigureI1_sobol_indices")


if __name__ == "__main__":
    main()
