"""Run the pre-registered stockpile test.

Follows results/2026-10-13_stockpile_preregistration.md exactly:
  - two candidate forms (level, month-over-month change),
  - choose the one with the larger absolute detrended correlation on 2025,
  - score it once on January to September 2026,
  - pass if |r| >= 0.5 and |detrended r| >= 0.3, both with the 2025 sign.

Usage: python scripts/score_stockpile.py gashuunsukhait
Reads data/s2_<aoi>_monthly.csv and data/exports_monthly.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from coalcast.evaluate import stockpile_test

name = sys.argv[1]
sig = pd.read_csv(Path("data") / f"s2_{name}_monthly.csv", index_col="month")["yard_coal_frac"]
ex = pd.read_csv(Path("data") / "exports_monthly.csv", index_col="month")["exports_mt"]
sig.index = pd.PeriodIndex(sig.index, freq="M")
ex.index = pd.PeriodIndex(ex.index, freq="M")

res = stockpile_test(sig, ex)
print(f"Form chosen on 2025: {res['form']} (sign {res['sign']:+d})")
print(f"2025 detrended r for each form: " + ", ".join(f"{k} {v:+.2f}" for k, v in res["discovery"].items()))
print(f"2026 test: n = {res['n_test']}, r = {res['r']:+.2f}, detrended r = {res['r_detrended']:+.2f}")
print("RESULT:", "PASS" if res["passed"] else "FAIL")
