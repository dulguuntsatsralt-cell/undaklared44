"""Run the second stockpile test (results/2026-10-14_stockpile_v2_preregistration.md).

Rule fixed in advance: monthly yard coal fraction (level), negative sign,
scored on January 2022 to December 2024 against official NSO coal exports.
Months before the yard start month (fixed from images alone, see
results/2026-10-14_yard_start.md) are excluded.

Usage: python scripts/score_stockpile_v2.py gashuunsukhait 2022-01
       (second argument: the first month the yard is in use)
Reads data/s2_<aoi>_monthly.csv and data/exports_nso_monthly.csv.
"""
import sys
from pathlib import Path

import pandas as pd

from coalcast.evaluate import fixed_rule_test

name, yard_start = sys.argv[1], sys.argv[2]
start = max(pd.Period(yard_start, "M"), pd.Period("2022-01", "M"))
sig = pd.read_csv(Path("data") / f"s2_{name}_monthly.csv", index_col="month")["yard_coal_frac"]
ex = pd.read_csv(Path("data") / "exports_nso_monthly.csv", index_col="month")["exports_mt"]
sig.index = pd.PeriodIndex(sig.index, freq="M")
ex.index = pd.PeriodIndex(ex.index, freq="M")

res = fixed_rule_test(sig, ex, str(start), "2024-12", sign=-1)
print(f"Months scored: {res['n']} from {start} to 2024-12; per year {res['months_per_year']}; years used {res['years']}")
print(f"Raw r (not part of the rule): {res['r_raw']:+.2f}")
print(f"Within-year detrended r, pooled: {res['r_within_year']:+.2f}  (pass needs <= -0.30)")
print("Per year: " + ", ".join(f"{y} {v:+.2f}" for y, v in res["per_year"].items())
      + f"  (negative in {res['years_with_sign']}; pass needs at least 2)")
print("RESULT:", "PASS" if res["passed"] else "FAIL")
