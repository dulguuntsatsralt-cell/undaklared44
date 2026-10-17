"""Run the truck counter test (results/2026-10-17_truck_counter_preregistration.md).

Usage: python scripts/score_trucks.py coal_road
Reads data/trucks_<aoi>_monthly.csv and data/exports_nso_monthly.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from coalcast.evaluate import fixed_rule_test

name = sys.argv[1]
START, END = "2019-01", "2022-08"
tr = pd.read_csv(Path("data") / f"trucks_{name}_monthly.csv", index_col="month")["trucks_per_10km"]
ex = pd.read_csv("data/exports_nso_monthly.csv", index_col="month")["exports_mt"]
tr.index = pd.PeriodIndex(tr.index, freq="M")
ex.index = pd.PeriodIndex(ex.index, freq="M")

j = pd.concat([tr.rename("tr"), ex.rename("ex")], axis=1, join="inner").dropna()
j = j.loc[pd.Period(START, "M"):pd.Period(END, "M")]
r_raw = float(np.corrcoef(j["tr"], j["ex"])[0, 1])
res = fixed_rule_test(tr, ex, START, END, sign=1, min_detrended=0.3, min_years=3)

print(f"Months with data: {res['n']} ({START} to {END}); per year {res['months_per_year']}")
print(f"1. Correlation with exports: {r_raw:+.2f}   (pass needs >= +0.50)")
print(f"2. Within-year detrended, pooled: {res['r_within_year']:+.2f}   (pass needs >= +0.30)")
print("3. Per year: " + ", ".join(f"{y} {v:+.2f}" for y, v in res["per_year"].items())
      + f"   (positive in {res['years_with_sign']}; pass needs at least 3)")
passed = r_raw >= 0.5 and res["passed"]
print("RESULT:", "PASS" if passed else "FAIL")
