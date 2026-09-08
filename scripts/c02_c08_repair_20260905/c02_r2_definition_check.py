"""C02: document the exact R^2 computation method used throughout the project
(pooled out-of-fold R^2, not the mean of 5 per-fold R^2 values) and compute
the alternative "simple average of per-fold R^2" number for comparison, on
the C01-corrected combined sample. No change to the primary method."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from corrected_sample_builder import build_corrected_combined_samples  # noqa: E402

RAW_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\c02_c08_repair_20260905\raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log_step(msg):
    print(f"[C02] {msg}", flush=True)


def main():
    spec14 = importlib.util.spec_from_file_location(
        "variance_decomposition_pipeline",
        r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
    v14 = importlib.util.module_from_spec(spec14)
    spec14.loader.exec_module(v14)

    _, combined_e0, combined_r0cb, _ = build_corrected_combined_samples()

    from sklearn.model_selection import GroupKFold

    def add_fresh_folds(df):
        d = df.copy()
        d["incident_date_utc"] = pd.to_datetime(d["incident_date_utc"], errors="coerce")
        gkf = GroupKFold(n_splits=5)
        d["cv_fold_v3"] = -1
        groups = d["incident_date_utc"].dt.date.astype(str)
        X_dummy = np.zeros(len(d))
        for fold_idx, (_, valid_idx) in enumerate(gkf.split(X_dummy, groups=groups)):
            d.iloc[valid_idx, d.columns.get_loc("cv_fold_v3")] = fold_idx
        return d

    def per_fold_and_pooled_r2(df, y_col, block_order):
        df = add_fresh_folds(df)
        y_all = df[y_col].astype(float)

        def oof_preds_and_perfold(blocks_included):
            preds = pd.Series(index=df.index, dtype=float)
            per_fold_r2 = []
            for fold in range(5):
                va_mask = df["cv_fold_v3"].eq(fold)
                tr_mask = df["cv_fold_v3"].ne(fold) & df["cv_fold_v3"].ge(0)
                tr, va = df.loc[tr_mask], df.loc[va_mask]
                Xtr, Xva = v14.build_block_baseline(tr, va)
                for block in blocks_included:
                    Xtr, Xva = v14.BLOCK_BUILDERS[block](Xtr, Xva, tr, va)
                ytr, yva = tr[y_col].astype(float), va[y_col].astype(float)
                res = sm.OLS(ytr, Xtr.astype(float)).fit()
                pred_va = res.predict(Xva.astype(float))
                preds.loc[va.index] = pred_va.values
                ss_res = float(((yva - pred_va) ** 2).sum())
                ss_tot = float(((yva - yva.mean()) ** 2).sum())
                per_fold_r2.append(1 - ss_res / ss_tot)
            return preds, per_fold_r2

        ss_tot_all = float(((y_all - y_all.mean()) ** 2).sum())
        rows = []
        cumulative = []
        preds0, pf0 = oof_preds_and_perfold([])
        pooled0 = 1 - float(((y_all - preds0) ** 2).sum()) / ss_tot_all
        rows.append({"step": "baseline", "pooled_oof_r2": pooled0, "simple_mean_of_5fold_r2": float(np.mean(pf0)),
                      "per_fold_r2": pf0})
        for block in block_order:
            cumulative.append(block)
            preds, pf = oof_preds_and_perfold(cumulative)
            pooled = 1 - float(((y_all - preds) ** 2).sum()) / ss_tot_all
            rows.append({"step": block, "pooled_oof_r2": pooled, "simple_mean_of_5fold_r2": float(np.mean(pf)),
                          "per_fold_r2": pf})
        return rows

    log_step("E0: comparing pooled-OOF R^2 vs simple mean of 5 per-fold R^2...")
    e0_rows = per_fold_and_pooled_r2(combined_e0, "log1p_customers_v2", ["nongust_weather", "gust"])
    for r in e0_rows:
        log_step(f"  E0 {r['step']}: pooled={r['pooled_oof_r2']*100:.4f}%, "
                  f"mean-of-5={r['simple_mean_of_5fold_r2']*100:.4f}%, per-fold%={[f'{x*100:.3f}' for x in r['per_fold_r2']]}")

    log_step("R0c (gust-then-customers): comparing pooled-OOF R^2 vs simple mean of 5 per-fold R^2...")
    r0c_rows = per_fold_and_pooled_r2(combined_r0cb, "log_duration_B_full_span_hours", ["nongust_weather", "gust", "customers"])
    for r in r0c_rows:
        log_step(f"  R0c {r['step']}: pooled={r['pooled_oof_r2']*100:.4f}%, "
                  f"mean-of-5={r['simple_mean_of_5fold_r2']*100:.4f}%, per-fold%={[f'{x*100:.3f}' for x in r['per_fold_r2']]}")

    def js(obj):
        def default(o):
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            raise TypeError(str(type(o)))
        return json.dumps(obj, ensure_ascii=False, indent=2, default=default)

    (RAW_DIR / "c02_r2_definition_comparison.json").write_text(
        js({"E0": e0_rows, "R0c_gust_then_customers": r0c_rows}), encoding="utf-8")
    log_step("Saved c02_r2_definition_comparison.json")


if __name__ == "__main__":
    main()
