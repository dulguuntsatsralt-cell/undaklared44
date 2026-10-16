"""Run the congestion vs price gap test (results/2026-10-15_congestion_gap_preregistration.md).

Usage: python scripts/score_congestion_gap.py gashuunsukhait
Reads data/s1_<aoi>.csv, data/trade_comtrade_coal.csv, data/trade_nso_coal.csv.
Writes results/congestion_gap_monthly.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

name = sys.argv[1]
ORBIT, START, END = 84, "2019-01", "2024-12"
EPISODE = ("2021-01", "2022-08")
MIN_MT = 0.5

s1 = pd.read_csv(Path("data") / f"s1_{name}.csv", parse_dates=["date"])
s1 = s1[s1["relative_orbit"] == ORBIT]
s1["month"] = s1["date"].dt.to_period("M")
cong = s1.groupby("month").agg(congestion=("road_p90_db", "mean"), n_scenes=("road_p90_db", "size"))

ct = pd.read_csv("data/trade_comtrade_coal.csv")
cn = ct[(ct["freq"] == "M") & (ct["reporter"] == 156)].copy()
cn["month"] = pd.PeriodIndex(cn["period"].astype(str), freq="M")
cn = cn.groupby("month").agg(cn_kg=("net_kg", "sum"), cn_usd=("value_usd", "sum"))

nso = pd.read_csv("data/trade_nso_coal.csv")
nso.index = pd.PeriodIndex(nso["month"], freq="M")

t = cong.join(cn, how="inner").join(nso[["volume_mt", "value_musd"]], how="inner")
t = t.loc[pd.Period(START, "M"):pd.Period(END, "M")]
t["cn_mt"] = t["cn_kg"] / 1e9
t = t[(t["cn_mt"] >= MIN_MT) & (t["volume_mt"] >= MIN_MT)]
t["price_gap"] = np.log((t["cn_usd"] / 1e6 / t["cn_mt"]) / (t["value_musd"] / t["volume_mt"]))
t[["congestion", "n_scenes", "cn_mt", "volume_mt", "price_gap"]].round(4).to_csv("results/congestion_gap_monthly.csv")


def corr(d):
    return float(np.corrcoef(d["congestion"], d["price_gap"])[0, 1]), float(spearmanr(d["congestion"], d["price_gap"])[0])


ep = t.loc[pd.Period(EPISODE[0], "M"):pd.Period(EPISODE[1], "M")]
r_all, s_all = corr(t)
r_ep, s_ep = corr(ep)
print(f"All months {START} to {END}: n = {len(t)}, r = {r_all:+.2f} (Spearman {s_all:+.2f})   pass needs <= -0.30")
print(f"Gap period {EPISODE[0]} to {EPISODE[1]}: n = {len(ep)}, r = {r_ep:+.2f} (Spearman {s_ep:+.2f})   pass needs <= -0.30")
if r_all <= -0.3 and r_ep <= -0.3:
    print("RESULT: PASS")
elif r_all <= -0.3:
    print("RESULT: consistent but driven by one episode (not a pass)")
else:
    print("RESULT: FAIL")
