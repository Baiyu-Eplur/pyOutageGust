"""Command #9: re-validate gust coefficient stability using customers_v2/duration_A/duration_B.

Read-only against rebuild_v3_full_stage/ and data/ (LAD shapefile only, for the small
residual LAD gap-fill). Writes all outputs under claude_branch/results/v3_validation/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster
from sklearn.model_selection import GroupKFold

SRC = Path(r"D:\Pyprogramme\STST2603\rebuild_v3_full_stage\outputs\ukpn_full_stage_dataset_v3.csv")
LAD_SHP = Path(r"D:\Pyprogramme\STST2603\data\Local_Authority_Districts_December_2021_UK_BGC_2022\LAD_DEC_2021_UK_BGC.shp")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\v3_validation")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_COL = "Incident Reference"

USECOLS = [
    INCIDENT_COL, "weather_status_v3", "cause_group_official",
    "gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h",
    "LAD21CD", "population", "income_deprivation_rate", "deprivation_gap_pct",
    "morans_i", "rural_urban_classification",
    "customers_v2_event_excl_reinterruptions",
    "duration_A_customer_weighted_hours", "duration_B_full_span_hours",
    "incident_date_utc", "lat", "lon",
]

SCALE_COLS = ["gust_0h", "precipitation_24h_sum", "temperature_0h", "pressure_msl_0h"]
BASE_NUMERIC = SCALE_COLS + ["urban_binary", "log_population", "income_deprivation_rate",
                             "deprivation_gap_pct", "morans_i"]
TERMS_OF_INTEREST = ["z_gust_0h", "z_gust_0h_sq"]
CUST_TERMS_OF_INTEREST = ["z_log1p_customers_v2", "z_log1p_customers_v2_sq"]


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


def log_step(msg):
    print(f"[v3_validation] {msg}", flush=True)


# ---------------- Step 0: build event-level weather-matched sample ----------------

def step0_build_sample():
    log_step("Step 0: loading v3 dataset and deduplicating to event level...")
    df = pd.read_csv(SRC, usecols=USECOLS, low_memory=False)
    event = df.drop_duplicates(INCIDENT_COL).copy()
    n_total_events = len(event)

    matched = event[event["weather_status_v3"] == "matched"].copy()
    n_matched = len(matched)

    step0_summary = {
        "n_total_events_v3": int(n_total_events),
        "n_weather_matched_events": int(n_matched),
        "weather_matched_pct": float(n_matched / n_total_events * 100),
        "cause_group_counts_in_matched_sample": matched["cause_group_official"].value_counts(dropna=False).to_dict(),
    }
    (RAW_DIR / "step0_sample.json").write_text(js(step0_summary), encoding="utf-8")
    log_step(f"Step 0 done: {n_matched} weather-matched events out of {n_total_events} total.")
    return matched, step0_summary


# ---------------- Step 1: light-weight LAD gap-fill (only where genuinely missing) ----------------

def step1_lad_gapfill(matched: pd.DataFrame):
    log_step("Step 1: checking LAD21CD coverage in the weather-matched sample...")
    n_missing_before = int(matched["LAD21CD"].isna().sum())
    n_total = len(matched)

    result = {
        "n_events_in_sample": int(n_total),
        "n_missing_LAD21CD_before": n_missing_before,
        "missing_LAD21CD_before_pct": float(n_missing_before / n_total * 100),
    }

    if n_missing_before == 0:
        result["gapfill_performed"] = False
        result["note"] = (
            "所有 121,313 个天气匹配事件在 v3 数据集中已经带有 LAD21CD（rebuild_v3_full_stage 的下游"
            "合并脚本 match_lad_v3.py / poppulation_merge_v3.py / GVA_merge_with_crosswalk_v3.py 等"
            "已经对全部 237,901 行跑过完整的空间连接+人口+GVA+剥夺指数合并，不是命令#9背景假设的"
            "‘新增事件目前没有LAD归属’。因此本步骤跳过冗余的sjoin重算，只做覆盖率核实。"
        )
        (RAW_DIR / "step1_lad_gapfill.json").write_text(js(result), encoding="utf-8")
        log_step("Step 1 done: LAD21CD already 100% present in weather-matched sample, no gap-fill needed.")
        return matched, result

    import geopandas as gpd

    missing_mask = matched["LAD21CD"].isna()
    to_fill = matched.loc[missing_mask].copy()
    has_coord = to_fill["lat"].notna() & to_fill["lon"].notna()
    to_fill_valid = to_fill.loc[has_coord]

    gdf_points = gpd.GeoDataFrame(
        to_fill_valid,
        geometry=gpd.points_from_xy(to_fill_valid["lon"], to_fill_valid["lat"]),
        crs="EPSG:4326",
    )
    lad = gpd.read_file(LAD_SHP).to_crs("EPSG:4326")
    joined = gpd.sjoin(gdf_points, lad, how="left", predicate="within")
    filled_lad = joined["LAD21CD_right"] if "LAD21CD_right" in joined.columns else joined["LAD21CD"]

    matched.loc[to_fill_valid.index, "LAD21CD"] = filled_lad.values

    n_missing_after = int(matched["LAD21CD"].isna().sum())
    result.update({
        "gapfill_performed": True,
        "n_events_attempted_gapfill": int(len(to_fill)),
        "n_events_no_coordinates": int((~has_coord).sum()),
        "n_events_sjoin_matched": int(filled_lad.notna().sum()),
        "n_events_sjoin_outside_boundary": int(filled_lad.isna().sum()),
        "n_missing_LAD21CD_after": n_missing_after,
    })
    (RAW_DIR / "step1_lad_gapfill.json").write_text(js(result), encoding="utf-8")
    log_step(f"Step 1 done: gap-filled {len(to_fill)} events, {n_missing_after} still missing.")
    return matched, result


# ---------------- Step 2: build outcome-blind date-grouped 5-fold CV ----------------

def step2_build_folds(sample: pd.DataFrame):
    log_step("Step 2: building GroupKFold(date, 5) folds...")
    sample = sample.copy()
    sample["incident_date_utc"] = pd.to_datetime(sample["incident_date_utc"], errors="coerce")
    valid_date = sample["incident_date_utc"].notna()
    sample = sample.loc[valid_date].copy()

    gkf = GroupKFold(n_splits=5)
    sample["cv_fold_v3"] = -1
    groups = sample["incident_date_utc"].dt.date.astype(str)
    X_dummy = np.zeros(len(sample))
    for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
        sample.iloc[valid_idx, sample.columns.get_loc("cv_fold_v3")] = fold_idx

    # self-check: no date appears in more than one fold
    date_fold_counts = sample.groupby(groups)["cv_fold_v3"].nunique()
    dates_crossing_folds = int((date_fold_counts > 1).sum())
    fold_sizes = sample["cv_fold_v3"].value_counts().sort_index().to_dict()

    result = {
        "n_events_with_valid_date": int(len(sample)),
        "n_dates_crossing_folds": dates_crossing_folds,
        "fold_sizes": {str(k): int(v) for k, v in fold_sizes.items()},
    }
    (RAW_DIR / "step2_folds.json").write_text(js(result), encoding="utf-8")
    log_step(f"Step 2 done: {dates_crossing_folds} dates crossing folds (expect 0).")
    return sample, result


# ---------------- shared prep ----------------

def prep_predictors(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    urban_source = d["rural_urban_classification"].astype("string").str.lower()
    d["urban_binary"] = np.where(
        urban_source.str.contains("urban", na=False), 1.0,
        np.where(urban_source.notna(), 0.0, np.nan),
    )
    d["log_population"] = np.log(pd.to_numeric(d["population"], errors="coerce").where(lambda x: x > 0))
    for c in SCALE_COLS + ["income_deprivation_rate", "deprivation_gap_pct", "morans_i"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["incident_year"] = d["incident_date_utc"].dt.year
    d["incident_month"] = d["incident_date_utc"].dt.month
    return d


def complete_predictors_mask(d: pd.DataFrame) -> pd.Series:
    needed = BASE_NUMERIC + ["incident_year", "incident_month", "LAD21CD"]
    return d[needed].notna().all(axis=1)


def design_train_valid(train: pd.DataFrame, valid: pd.DataFrame, extra_scale_cols=None):
    tr = train.copy()
    va = valid.copy()
    extra_scale_cols = extra_scale_cols or []
    for c in SCALE_COLS + extra_scale_cols:
        mu, sd = tr[c].mean(), tr[c].std(ddof=1)
        if not np.isfinite(sd) or sd == 0:
            raise ValueError(f"zero/invalid training SD: {c}")
        tr["z_" + c] = (tr[c] - mu) / sd
        va["z_" + c] = (va[c] - mu) / sd
    for x in (tr, va):
        x["z_gust_0h_sq"] = x["z_gust_0h"] ** 2
        x["z_gust_pressure"] = x["z_gust_0h"] * x["z_pressure_msl_0h"]
        if "customers_v2_log1p" in extra_scale_cols:
            x["z_log1p_customers_v2_sq"] = x["z_customers_v2_log1p"] ** 2

    cols = ["Intercept", "z_gust_0h", "z_gust_0h_sq", "z_precipitation_24h_sum", "z_temperature_0h",
            "z_pressure_msl_0h", "z_gust_pressure", "urban_binary", "log_population",
            "income_deprivation_rate", "deprivation_gap_pct", "morans_i"]
    if "customers_v2_log1p" in extra_scale_cols:
        cols += ["z_customers_v2_log1p", "z_log1p_customers_v2_sq"]

    Xtr = pd.DataFrame({"Intercept": 1.0}, index=tr.index)
    Xva = pd.DataFrame({"Intercept": 1.0}, index=va.index)
    for c in cols[1:]:
        Xtr[c] = tr[c].astype(float)
        Xva[c] = va[c].astype(float)
    for c in ["incident_year", "incident_month"]:
        levels = sorted(pd.Series(tr[c].dropna().unique()).tolist())
        for level in levels[1:]:
            name = f"{c}[{level}]"
            Xtr[name] = (tr[c] == level).astype(float)
            Xva[name] = (va[c] == level).astype(float)

    # rename z_customers_v2_log1p -> the term-of-interest name used for reporting
    rename_map = {"z_customers_v2_log1p": "z_log1p_customers_v2"}
    Xtr = Xtr.rename(columns=rename_map)
    Xva = Xva.rename(columns=rename_map)
    return Xtr.astype(float), Xva.astype(float)


def fit_fold_terms(train, valid, target_col, terms_of_interest, use_customers_covariate=False):
    tr = train.copy()
    va = valid.copy()
    extra_scale_cols = None
    if use_customers_covariate:
        tr["customers_v2_log1p"] = np.log1p(tr["customers_v2_event_excl_reinterruptions"].astype(float))
        va["customers_v2_log1p"] = np.log1p(va["customers_v2_event_excl_reinterruptions"].astype(float))
        extra_scale_cols = ["customers_v2_log1p"]
    Xtr, Xva = design_train_valid(tr, va, extra_scale_cols=extra_scale_cols)
    ytr = tr[target_col].astype(float)
    res = sm.OLS(ytr, Xtr).fit()
    groups_lad = pd.factorize(tr["LAD21CD"])[0]
    cov = cov_cluster(res, groups_lad)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = res.params.to_numpy() / se
    p = 2 * stats.norm.sf(np.abs(z))
    rows = []
    for term, coef, s, pv in zip(res.params.index, res.params, se, p):
        if term not in terms_of_interest:
            continue
        rows.append({"term": term, "coefficient": coef, "std_error": s,
                     "ci_low": coef - 1.96 * s, "ci_high": coef + 1.96 * s, "p_value": pv})
    return rows, len(tr), len(va)


def run_model(sample_with_folds: pd.DataFrame, target_col: str, model_name: str,
              terms_of_interest, use_customers_covariate=False):
    all_rows = []
    for fold in range(5):
        va_mask = sample_with_folds["cv_fold_v3"].eq(fold)
        tr_mask = sample_with_folds["cv_fold_v3"].ne(fold) & sample_with_folds["cv_fold_v3"].ge(0)
        assert va_mask.any() and tr_mask.any()
        rows, n_train, n_valid = fit_fold_terms(
            sample_with_folds.loc[tr_mask], sample_with_folds.loc[va_mask],
            target_col, terms_of_interest, use_customers_covariate,
        )
        for r in rows:
            r.update({"model": model_name, "fold": fold, "n_obs_in_fold_train": n_train,
                      "n_obs_in_fold_valid": n_valid, "inference": "LAD_cluster"})
            all_rows.append(r)
    return pd.DataFrame(all_rows)


def stability_summary(fold_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, term), g in fold_df.groupby(["model", "term"]):
        n = len(g)
        n_pos = (g["coefficient"] > 0).sum()
        n_neg = (g["coefficient"] < 0).sum()
        same_sign_folds = max(n_pos, n_neg)
        n_sig = (g["p_value"] < 0.05).sum()
        mean_coef = g["coefficient"].mean()
        cv = float(g["coefficient"].std(ddof=1) / abs(mean_coef) * 100) if mean_coef != 0 else np.nan
        rows.append({
            "model": model, "term": term, "n_folds": n,
            "same_sign_folds": int(same_sign_folds), "significant_folds": int(n_sig),
            "mean_coefficient": mean_coef, "coef_cv_pct": cv,
            "all_same_sign": bool(same_sign_folds == n),
        })
    return pd.DataFrame(rows)


def main():
    matched, s0 = step0_build_sample()
    matched, s1 = step1_lad_gapfill(matched)
    sample, s2 = step2_build_folds(matched)
    sample = prep_predictors(sample)
    comp_mask = complete_predictors_mask(sample)
    log_step(f"Complete-predictor mask: {comp_mask.sum()} / {len(sample)} events retained.")
    sample = sample.loc[comp_mask].copy()

    # ---------------- Step 3: E0' (customers_v2, log1p) ----------------
    log_step("Step 3: fitting E0' (log1p customers_v2)...")
    e0_sample = sample.loc[sample["customers_v2_event_excl_reinterruptions"].notna()].copy()
    e0_sample["log1p_customers_v2"] = np.log1p(e0_sample["customers_v2_event_excl_reinterruptions"].astype(float))
    e0_prime = run_model(e0_sample, "log1p_customers_v2", "E0_prime_customers_v2", TERMS_OF_INTEREST)
    e0_prime.to_csv(RAW_DIR / "E0_prime_fold_coefs.csv", index=False)
    log_step(f"E0' done, n={len(e0_sample)}.")

    # ---------------- Step 4: R0'_A and R0'_B ----------------
    log_step("Step 4: fitting R0'_A (log duration_A) and R0'_B (log duration_B)...")

    def build_duration_sample(col):
        s = sample.loc[sample[col].notna() & (sample[col] > 0)].copy()
        p99 = s[col].quantile(0.99)
        s = s.loc[s[col] <= p99].copy()
        s["log_" + col] = np.log(s[col].astype(float))
        return s, float(p99)

    r0a_sample, r0a_p99 = build_duration_sample("duration_A_customer_weighted_hours")
    r0b_sample, r0b_p99 = build_duration_sample("duration_B_full_span_hours")

    r0a_prime = run_model(r0a_sample, "log_duration_A_customer_weighted_hours", "R0_prime_A_duration_A", TERMS_OF_INTEREST)
    r0b_prime = run_model(r0b_sample, "log_duration_B_full_span_hours", "R0_prime_B_duration_B", TERMS_OF_INTEREST)
    r0a_prime.to_csv(RAW_DIR / "R0_prime_A_fold_coefs.csv", index=False)
    r0b_prime.to_csv(RAW_DIR / "R0_prime_B_fold_coefs.csv", index=False)
    log_step(f"R0'_A done, n={len(r0a_sample)} (p99 cap={r0a_p99:.2f}h). R0'_B done, n={len(r0b_sample)} (p99 cap={r0b_p99:.2f}h).")

    step4_summary = {
        "duration_A_sample_n": int(len(r0a_sample)),
        "duration_A_p99_cap_hours": r0a_p99,
        "duration_A_excluded_missing_n": int(sample["duration_A_customer_weighted_hours"].isna().sum()),
        "duration_B_sample_n": int(len(r0b_sample)),
        "duration_B_p99_cap_hours": r0b_p99,
    }
    (RAW_DIR / "step4_duration_samples.json").write_text(js(step4_summary), encoding="utf-8")

    # ---------------- Step 5: R0c'_A and R0c'_B (control for customers_v2) ----------------
    log_step("Step 5: fitting R0c'_A and R0c'_B (customers_v2-adjusted)...")

    r0ca_sample = r0a_sample.loc[r0a_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()
    r0cb_sample = r0b_sample.loc[r0b_sample["customers_v2_event_excl_reinterruptions"].notna()].copy()

    r0ca_prime = run_model(r0ca_sample, "log_duration_A_customer_weighted_hours", "R0c_prime_A_custadj",
                            TERMS_OF_INTEREST + CUST_TERMS_OF_INTEREST, use_customers_covariate=True)
    r0cb_prime = run_model(r0cb_sample, "log_duration_B_full_span_hours", "R0c_prime_B_custadj",
                            TERMS_OF_INTEREST + CUST_TERMS_OF_INTEREST, use_customers_covariate=True)
    r0ca_prime.to_csv(RAW_DIR / "R0c_prime_A_fold_coefs.csv", index=False)
    r0cb_prime.to_csv(RAW_DIR / "R0c_prime_B_fold_coefs.csv", index=False)
    log_step(f"R0c'_A done, n={len(r0ca_sample)}. R0c'_B done, n={len(r0cb_sample)}.")

    step5_summary = {
        "r0ca_sample_n": int(len(r0ca_sample)),
        "r0cb_sample_n": int(len(r0cb_sample)),
    }
    (RAW_DIR / "step5_custadj_samples.json").write_text(js(step5_summary), encoding="utf-8")

    # ---------------- combine + stability summary ----------------
    all_fold_coefs = pd.concat([e0_prime, r0a_prime, r0b_prime, r0ca_prime, r0cb_prime], ignore_index=True)
    all_fold_coefs.to_csv(RAW_DIR / "all_v3_fold_coefs.csv", index=False)
    stab = stability_summary(all_fold_coefs)
    stab.to_csv(RAW_DIR / "stability_summary_v3.csv", index=False)

    log_step("All steps complete.")
    print(stab.to_string(index=False))


if __name__ == "__main__":
    main()
