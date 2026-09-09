"""Command #16 Step 2: refit E0' and R0c'_B on the clean (decontaminated) sample."""
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

sys.path.insert(0, str(Path(__file__).parent))
from clean_sample_builder import build_clean_wt_samples, v9  # noqa: E402

OUT_DIR = result_path('dev_sample_decontamination')
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


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


def stability_row(fold_df, model, term):
    g = fold_df[(fold_df["model"] == model) & (fold_df["term"] == term)]
    n = len(g)
    n_pos, n_neg = (g["coefficient"] > 0).sum(), (g["coefficient"] < 0).sum()
    same = max(n_pos, n_neg)
    n_sig = (g["p_value"] < 0.05).sum()
    mean = g["coefficient"].mean()
    cv = float(g["coefficient"].std(ddof=1) / abs(mean) * 100) if mean != 0 else np.nan
    return {
        "model": model, "term": term, "n_folds": int(n), "same_sign_folds": int(same),
        "significant_folds": int(n_sig), "mean_coefficient": float(mean), "coef_cv_pct": cv,
        "all_same_sign": bool(same == n), "fold_values": g.sort_values("fold")["coefficient"].tolist(),
    }


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_clean_wt_samples()

    print("[v16-step2] Fitting E0'_clean...")
    e0_fold = v9.run_model(e0_sample, "log1p_customers_v2", "E0_prime_clean", v9.TERMS_OF_INTEREST)
    e0_fold.to_csv(RAW_DIR / "E0_prime_clean_fold_coefs.csv", index=False)

    print("[v16-step2] Fitting R0c'_B_clean...")
    r0cb_fold = v9.run_model(
        r0cb_sample, "log_duration_B_full_span_hours", "R0c_prime_B_clean",
        v9.TERMS_OF_INTEREST + v9.CUST_TERMS_OF_INTEREST, use_customers_covariate=True,
    )
    r0cb_fold.to_csv(RAW_DIR / "R0c_prime_B_clean_fold_coefs.csv", index=False)

    all_fold = pd.concat([e0_fold, r0cb_fold], ignore_index=True)
    stab_rows = []
    for model, term in [
        ("E0_prime_clean", "z_gust_0h"), ("E0_prime_clean", "z_gust_0h_sq"),
        ("R0c_prime_B_clean", "z_gust_0h"), ("R0c_prime_B_clean", "z_gust_0h_sq"),
        ("R0c_prime_B_clean", "z_log1p_customers_v2"), ("R0c_prime_B_clean", "z_log1p_customers_v2_sq"),
    ]:
        stab_rows.append(stability_row(all_fold, model, term))
    stab_df = pd.DataFrame(stab_rows)
    stab_df.to_csv(RAW_DIR / "step2_stability_summary_clean.csv", index=False)
    print(stab_df.drop(columns=["fold_values"]).to_string(index=False))

    sizes = {
        "n_wt_clean": int(len(sample_wt)), "n_e0_prime_clean": int(len(e0_sample)),
        "n_r0c_prime_b_clean": int(len(r0cb_sample)), "duration_B_p99_cap_hours_clean": float(p99_b),
    }
    (RAW_DIR / "step2_sample_sizes_clean.json").write_text(js(sizes), encoding="utf-8")
    print("[v16-step2] Done.")


if __name__ == "__main__":
    main()
