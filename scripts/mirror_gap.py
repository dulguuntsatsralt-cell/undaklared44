"""Compare both sides' records of the Mongolia-China coal trade, by year.

Mongolia's side: NSO coal exports (all destinations; almost all goes to China)
and, where reported, Mongolia's own Comtrade filing of exports to China.
China's side: China's Comtrade filing of imports from Mongolia.
Coal = HS 2701 + 2702 + 2704 on the Comtrade side.

China's tonnage for 2016 and 2023 is a UN estimate, not a reported figure,
so tonnage comparisons skip those years. Values are always reported.

Usage: python scripts/mirror_gap.py
Reads data/trade_nso_coal.csv and data/trade_comtrade_coal.csv,
writes results/mirror_gap_annual.csv.
"""
from pathlib import Path

import pandas as pd

nso = pd.read_csv("data/trade_nso_coal.csv")
nso["year"] = nso["month"].str[:4].astype(int)
full_years = nso.groupby("year")["month"].size().loc[lambda s: s == 12].index
nso = nso[nso["year"].isin(full_years)].groupby("year").agg(mn_nso_mt=("volume_mt", "sum"),
                                                           mn_nso_musd=("value_musd", "sum"))

ct = pd.read_csv("data/trade_comtrade_coal.csv")
ct = ct[ct["freq"] == "A"].copy()
ct["year"] = ct["period"].astype(int)
ct["mt"] = ct["net_kg"] / 1e9
ct["musd"] = ct["value_usd"] / 1e6


def side(reporter, prefix):
    s = ct[ct["reporter"] == reporter].groupby("year")
    return pd.DataFrame({f"{prefix}_mt": s["mt"].sum(), f"{prefix}_musd": s["musd"].sum(),
                         f"{prefix}_mt_estimated": s["qty_estimated"].any()})


t = side(156, "cn").join(side(496, "mn_un"), how="outer").join(nso, how="outer")
t = t[t.index >= 2011]
reported = ~t["cn_mt_estimated"].fillna(True).astype(bool)
t["tonnes_ratio"] = (t["cn_mt"] / t["mn_nso_mt"]).where(reported)
t["value_ratio"] = t["cn_musd"] / t["mn_nso_musd"]
t["value_gap_musd"] = t["cn_musd"] - t["mn_nso_musd"]
t["cn_price"] = (t["cn_musd"] / t["cn_mt"]).where(reported)
t["mn_price"] = t["mn_nso_musd"] / t["mn_nso_mt"]

Path("results").mkdir(exist_ok=True)
t.round(4).to_csv("results/mirror_gap_annual.csv")
show = t[["mn_nso_mt", "cn_mt", "tonnes_ratio", "mn_nso_musd", "cn_musd", "value_ratio", "value_gap_musd"]]
print(show.round(2).to_string())
ok = t["tonnes_ratio"].dropna()
print(f"\nTonnes, China / Mongolia, years with reported figures: median {ok.median():.3f}, "
      f"range {ok.min():.3f} to {ok.max():.3f} ({len(ok)} years)")
print(f"Value gap 2021+2022: {t.loc[[2021, 2022], 'value_gap_musd'].sum():,.0f} million USD")
