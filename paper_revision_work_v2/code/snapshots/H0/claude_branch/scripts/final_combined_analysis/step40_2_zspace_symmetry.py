"""Command #40 Test 2: z-space symmetry analysis of the gust quadratic curve
for R0c (recovery, linear term ~0) and E0 (exposure, linear term significant,
used as contrast), using command #21's existing full-sample no-cubic
coefficients (no new model fit -- pure post-hoc evaluation of eta(z) =
beta1*z + beta2*z^2 at z = -3..+3), and mapping z back to physical gust
speed (m/s) to quantify how much of Figure 4's "steeper right arm" is a
geometric artifact of the right-skewed, zero-bounded gust distribution."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\final_combined_analysis\raw")

# command #21 final full-sample no-cubic coefficients (step1_E0/R0c_final_full_coefs.csv,
# identical values also in step28_E0/R0c_lad_cluster.csv)
E0_BETA1, E0_BETA2 = -0.032325899095631154, 0.10276170747389514
R0C_BETA1, R0C_BETA2 = 0.0001979069022939746, 0.07923745080615863

E0_GUST_MEAN, E0_GUST_SD = 9.87229677581956, 5.222713076874045
R0C_GUST_MEAN, R0C_GUST_SD = 9.875234820350876, 5.2190180674673785

# E0 sample's observed gust distribution (step2_critical_wind_speed.json)
GUST_PCTS = {"p1": 2.2, "p50": 8.9, "p95": 19.8, "p99": 27.2, "max": 39.4}


def log_step(msg):
    print(f"[step40-2] {msg}", flush=True)


def eta(beta1, beta2, z):
    return beta1 * z + beta2 * z ** 2


def analyze(label, beta1, beta2, gust_mean, gust_sd):
    log_step(f"=== {label}: beta1={beta1:.4f}, beta2={beta2:.4f} ===")
    turning_z = -beta1 / (2 * beta2)
    log_step(f"{label}: turning point z*={turning_z:.4f} (physical: {gust_mean + turning_z*gust_sd:.2f} m/s)")

    rows = []
    for k in (1, 2, 3):
        eta_pos = eta(beta1, beta2, k)
        eta_neg = eta(beta1, beta2, -k)
        eta_0 = eta(beta1, beta2, 0)
        delta = eta_pos - eta_neg  # antisymmetric part = 2*beta1*k
        sym = (eta_pos + eta_neg) / 2 - eta_0  # symmetric part = beta2*k^2
        ratio = eta_pos / eta_neg if eta_neg != 0 else np.nan
        asym_share = abs(delta) / (2 * sym) if sym != 0 else np.nan
        gust_pos = gust_mean + k * gust_sd
        gust_neg = gust_mean - k * gust_sd
        rows.append({
            "k": k, "z_pos": k, "z_neg": -k,
            "eta_pos": eta_pos, "eta_neg": eta_neg,
            "exp_eta_pos": float(np.exp(eta_pos)), "exp_eta_neg": float(np.exp(eta_neg)),
            "delta_antisymmetric": delta, "sym_component": sym,
            "eta_pos_over_neg_ratio": ratio, "asymmetry_share_of_pure_quadratic": asym_share,
            "gust_ms_pos": gust_pos, "gust_ms_neg": gust_neg,
            "gust_neg_physically_valid": bool(gust_neg >= 0),
        })
        log_step(f"  k={k}: eta(+{k})={eta_pos:.4f} eta(-{k})={eta_neg:.4f} "
                  f"[exp: {np.exp(eta_pos):.3f} vs {np.exp(eta_neg):.3f}] "
                  f"| gust(+{k})={gust_pos:.2f}m/s gust(-{k})={gust_neg:.2f}m/s "
                  f"{'[NEGATIVE-invalid]' if gust_neg < 0 else ''}")

    z_at_zero_gust = -gust_mean / gust_sd
    log_step(f"{label}: z at which physical gust = 0 m/s: z={z_at_zero_gust:.4f} "
              f"(so z<{z_at_zero_gust:.2f} is physically impossible / never observed)")

    return {
        "label": label, "beta1": beta1, "beta2": beta2, "turning_point_z": turning_z,
        "turning_point_ms": gust_mean + turning_z * gust_sd,
        "gust_mean": gust_mean, "gust_sd": gust_sd,
        "z_at_zero_gust": z_at_zero_gust,
        "rows": rows,
    }


def main():
    e0 = analyze("E0 (exposure)", E0_BETA1, E0_BETA2, E0_GUST_MEAN, E0_GUST_SD)
    r0c = analyze("R0c (recovery)", R0C_BETA1, R0C_BETA2, R0C_GUST_MEAN, R0C_GUST_SD)

    # observed percentile context for the physical values at z=+/-2, +/-3
    log_step("Observed E0-sample gust percentiles for context: " + json.dumps(GUST_PCTS))

    result = {"E0": e0, "R0c": r0c, "observed_gust_percentiles_E0_sample": GUST_PCTS}
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "step40_2_zspace_symmetry.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    log_step("Saved raw/step40_2_zspace_symmetry.json")


if __name__ == "__main__":
    main()
