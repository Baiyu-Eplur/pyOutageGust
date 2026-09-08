"""Command #46 (C09 final cleanup): run A02 (Duan smearing), Appendix G
recompute, and C09 VIF-with-FE recompute all in ONE process, so the expensive
build_corrected_combined_samples() step (full corrected sample construction)
only runs once instead of three times."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\c02_c08_repair_20260905")))
from corrected_sample_builder import build_corrected_combined_samples, _patch_v9  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c09_final_cleanup_20260905\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

TURNING_POINT_MS = 10.80715790164296


def log_step(tag, msg):
    print(f"[{tag}] {msg}", flush=True)


def compute_vif(X: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in X.columns if c != "Intercept"]
    Xv = X[cols].astype(float)
    vifs = [{"variable": c, "VIF": variance_inflation_factor(Xv.values, i)} for i, c in enumerate(cols)]
    return pd.DataFrame(vifs)


def main():
    import statsmodels.api as sm

    log_step("SETUP", "Patching v9 and building corrected combined samples (once)...")
    v9, _, _ = _patch_v9()
    combined_wt, combined_e0, combined_r0cb, verification = build_corrected_combined_samples()
    combined_wt["incident_date_utc"] = pd.to_datetime(combined_wt["incident_date_utc"], errors="coerce")
    log_step("SETUP", f"combined_wt n={len(combined_wt)}, combined_e0 n={len(combined_e0)}, "
                       f"combined_r0cb n={len(combined_r0cb)}")

    # build shared design matrices / fits once, reused below
    Xe0, _ = v9.design_train_valid(combined_e0, combined_e0, extra_scale_cols=None)
    ye0 = combined_e0["log1p_customers_v2"].astype(float)
    res_e0 = sm.OLS(ye0, Xe0.astype(float)).fit()

    s = combined_r0cb.copy()
    s["customers_v2_log1p"] = np.log1p(s["customers_v2_event_excl_reinterruptions"].astype(float))
    Xr0c, _ = v9.design_train_valid(s, s, extra_scale_cols=["customers_v2_log1p"])
    yr0c = s["log_duration_B_full_span_hours"].astype(float)
    res_r0c = sm.OLS(yr0c, Xr0c.astype(float)).fit()

    # ================= A02: Duan smearing =================
    smear_e0 = float(np.mean(np.exp(res_e0.resid)))
    smear_r = float(np.mean(np.exp(res_r0c.resid)))
    log_step("A02", f"E0 (corrected) Duan smearing factor = {smear_e0:.6f}, "
                     f"implied naive-exp underestimate = {(1-1/smear_e0)*100:.2f}%")
    log_step("A02", f"R0c (corrected) Duan smearing factor = {smear_r:.6f}, "
                     f"implied naive-exp underestimate = {(1-1/smear_r)*100:.2f}%")
    a02_result = {
        "E0_smearing_factor": smear_e0, "E0_pct_underestimate": (1 - 1 / smear_e0) * 100,
        "R0c_smearing_factor": smear_r, "R0c_pct_underestimate": (1 - 1 / smear_r) * 100,
        "E0_residual_std": float(res_e0.resid.std()),
        "R0c_residual_std": float(res_r0c.resid.std()),
        "E0_n": int(len(ye0)), "R0c_n": int(len(yr0c)),
    }
    (RAW_DIR / "a02_duan_smearing_corrected.json").write_text(json.dumps(a02_result, indent=2), encoding="utf-8")
    log_step("A02", "Saved a02_duan_smearing_corrected.json")

    # ================= Appendix G =================
    df = combined_wt.copy()
    df["gust_decile"] = pd.qcut(df["gust_0h"], 10, labels=False, duplicates="drop")
    decile_stats = df.groupby("gust_decile").apply(
        lambda g: pd.Series({
            "n": len(g),
            "gust_min": g["gust_0h"].min(), "gust_max": g["gust_0h"].max(),
            "pct_weather_natural": (g["cause_group_official"] == "weather_natural").mean() * 100,
        }), include_groups=False
    )
    decile_stats.to_csv(RAW_DIR / "appendixG_table_G1_corrected.csv")
    log_step("AppendixG", "Table G1 (corrected):\n" + decile_stats.to_string())

    first_decile_pct = float(decile_stats["pct_weather_natural"].iloc[0])
    last_decile_pct = float(decile_stats["pct_weather_natural"].iloc[-1])
    is_monotonic = bool(decile_stats["pct_weather_natural"].is_monotonic_increasing)
    log_step("AppendixG", f"First decile: {first_decile_pct:.2f}%, last decile: {last_decile_pct:.2f}%, "
                           f"monotonic increasing: {is_monotonic}")

    combined_e0_local = combined_wt.loc[combined_wt["customers_v2_event_excl_reinterruptions"].notna()].copy()
    wn_e0 = combined_e0_local.loc[combined_e0_local["cause_group_official"] == "weather_natural"].copy()
    pct_below_full = float((combined_e0_local["gust_0h"] < TURNING_POINT_MS).mean() * 100)
    pct_below_wn = float((wn_e0["gust_0h"] < TURNING_POINT_MS).mean() * 100)
    log_step("AppendixG", f"Share of events with gust < {TURNING_POINT_MS:.2f} m/s: "
                           f"full WT E0 sample = {pct_below_full:.2f}% (n={len(combined_e0_local)}), "
                           f"weather_natural subsample = {pct_below_wn:.2f}% (n={len(wn_e0)})")

    appendixG_result = {
        "table_G1_first_decile_pct_weather_natural": first_decile_pct,
        "table_G1_last_decile_pct_weather_natural": last_decile_pct,
        "table_G1_monotonic_increasing": is_monotonic,
        "table_G1_original_command26": {"first_decile": 6.89, "last_decile": 56.10},
        "turning_point_ms_used": TURNING_POINT_MS,
        "pct_below_turning_point_full_WT_E0": pct_below_full,
        "pct_below_turning_point_weather_natural": pct_below_wn,
        "original_command26_step3": {"full_sample": 63.70, "weather_natural": 36.83},
        "n_full_WT_E0": int(len(combined_e0_local)), "n_weather_natural": int(len(wn_e0)),
    }
    (RAW_DIR / "appendixG_summary_corrected.json").write_text(json.dumps(appendixG_result, indent=2), encoding="utf-8")
    log_step("AppendixG", "Saved appendixG_summary_corrected.json")

    # ================= C09 item 2: VIF with FE =================
    vif_e0_full = compute_vif(Xe0)
    vif_e0_full.to_csv(RAW_DIR / "c09_E0_vif_full_design_corrected.csv", index=False)
    log_step("C09-VIF", "E0 full-design VIF (incl. year/month FE):\n" + vif_e0_full.to_string(index=False))
    log_step("C09-VIF", f"E0 max VIF (full design) = {vif_e0_full['VIF'].max():.3f}")

    vif_r0c_full = compute_vif(Xr0c)
    vif_r0c_full.to_csv(RAW_DIR / "c09_R0c_vif_full_design_corrected.csv", index=False)
    log_step("C09-VIF", "R0c full-design VIF (incl. year/month FE):\n" + vif_r0c_full.to_string(index=False))
    log_step("C09-VIF", f"R0c max VIF (full design) = {vif_r0c_full['VIF'].max():.3f}")

    restricted_cols_e0 = ["z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
                           "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
                           "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    vif_e0_restricted = compute_vif(Xe0[restricted_cols_e0])
    vif_e0_restricted.to_csv(RAW_DIR / "c09_E0_vif_restricted_corrected.csv", index=False)
    log_step("C09-VIF", "E0 restricted (no-FE, matches original methodology) VIF on corrected data:\n"
                         + vif_e0_restricted.to_string(index=False))

    vif_summary = {
        "E0_full_design_max_vif": float(vif_e0_full["VIF"].max()),
        "E0_full_design_n_vars_above_4": int((vif_e0_full["VIF"] > 4).sum()),
        "E0_full_design_n_vars_above_5": int((vif_e0_full["VIF"] > 5).sum()),
        "E0_full_design_n_vars_above_10": int((vif_e0_full["VIF"] > 10).sum()),
        "E0_full_design_vars_above_4_list": vif_e0_full.loc[vif_e0_full["VIF"] > 4, "variable"].tolist(),
        "R0c_full_design_max_vif": float(vif_r0c_full["VIF"].max()),
        "R0c_full_design_n_vars_above_4": int((vif_r0c_full["VIF"] > 4).sum()),
        "R0c_full_design_n_vars_above_5": int((vif_r0c_full["VIF"] > 5).sum()),
        "R0c_full_design_n_vars_above_10": int((vif_r0c_full["VIF"] > 10).sum()),
        "R0c_full_design_vars_above_4_list": vif_r0c_full.loc[vif_r0c_full["VIF"] > 4, "variable"].tolist(),
        "E0_restricted_max_vif_corrected_data": float(vif_e0_restricted["VIF"].max()),
    }
    (RAW_DIR / "c09_vif_summary.json").write_text(json.dumps(vif_summary, indent=2), encoding="utf-8")
    log_step("C09-VIF", json.dumps(vif_summary, indent=2))

    log_step("DONE", "All three analyses complete.")


if __name__ == "__main__":
    main()
