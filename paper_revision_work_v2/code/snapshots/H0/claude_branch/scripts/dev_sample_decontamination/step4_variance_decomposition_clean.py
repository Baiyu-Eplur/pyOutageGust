"""Command #16 Step 4: re-run command #14's nested variance decomposition on the
clean (decontaminated) weather_natural+technical_asset sample.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from clean_sample_builder import build_clean_wt_samples  # noqa: E402

V14_SCRIPT = Path(r"D:\Pyprogramme\STST2603\claude_branch\scripts\variance_decomposition\variance_decomposition_pipeline.py")
OUT_DIR = Path(r"D:\Pyprogramme\STST2603\claude_branch\results\dev_sample_decontamination")
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

spec14 = importlib.util.spec_from_file_location("variance_decomposition_pipeline", V14_SCRIPT)
v14 = importlib.util.module_from_spec(spec14)
spec14.loader.exec_module(v14)


def log_step(msg):
    print(f"[v16-step4] {msg}", flush=True)


def main():
    sample_wt, e0_sample, r0cb_sample, p99_b = build_clean_wt_samples()

    log_step("E0' nested variance decomposition (clean sample)...")
    e0_seq = v14.nested_r2_sequence(e0_sample, "log1p_customers_v2", ["nongust_weather", "gust"], "E0_prime_clean")
    e0_seq.to_csv(RAW_DIR / "E0_prime_clean_variance_decomposition.csv", index=False)
    print(e0_seq.to_string(index=False))

    log_step("R0c'_B nested variance decomposition, order 甲 (customers -> gust), clean sample...")
    r0cb_a = v14.nested_r2_sequence(
        r0cb_sample, "log_duration_B_full_span_hours",
        ["nongust_weather", "customers", "gust"], "R0c_prime_B_clean_order_customers_then_gust")
    r0cb_a.to_csv(RAW_DIR / "R0c_prime_B_clean_order_customers_then_gust.csv", index=False)
    print(r0cb_a.to_string(index=False))

    log_step("R0c'_B nested variance decomposition, order 乙 (gust -> customers), clean sample...")
    r0cb_b = v14.nested_r2_sequence(
        r0cb_sample, "log_duration_B_full_span_hours",
        ["nongust_weather", "gust", "customers"], "R0c_prime_B_clean_order_gust_then_customers")
    r0cb_b.to_csv(RAW_DIR / "R0c_prime_B_clean_order_gust_then_customers.csv", index=False)
    print(r0cb_b.to_string(index=False))

    log_step("Done.")


if __name__ == "__main__":
    main()
