"""Download both sides of the Mongolia-China coal trade.

Mongolia's side: National Statistics Office (NSO), table DT_NSO_1400_006V2_month,
coal export volume (thousand tonnes) and value (thousand USD), cumulative by
month since 2011, turned into monthly figures.

Both sides by customs code: UN Comtrade public preview API (no key needed),
HS 2701 (hard coal), 2702 (lignite), 2704 (coke). China imports from Mongolia
(reporter 156, partner 496) and Mongolia exports to China (reporter 496,
partner 156), annual from 2010 and monthly from 2017. The preview API takes
one period per call, about one call per second, and a limited number of
calls per hour; the script waits when the quota runs out. Periods already in
data/trade_comtrade_coal.csv are not fetched again. A period where a side
reported nothing is asked again on each run (cheap, and picks up late filings).

Usage:
  python scripts/fetch_trade.py            # everything
  python scripts/fetch_trade.py --nso-only
Writes data/trade_nso_coal.csv and data/trade_comtrade_coal.csv.
"""
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

NSO_URL = "https://data.1212.mn/api/v1/en/NSO/Economy, environment/Foreign Trade/DT_NSO_1400_006V2_month.px"
CT_URL = "https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS"
CODES = "2701,2702,2704"
SIDES = [(156, 496, "M"), (496, 156, "X")]   # China imports from Mongolia, Mongolia exports to China


def fetch_nso() -> pd.DataFrame:
    meta = requests.get(NSO_URL, timeout=60).json()
    ind, com, mon = meta["variables"]
    coal = com["values"][com["valueTexts"].index(next(t for t in com["valueTexts"] if t.strip().startswith("Coal")))]
    out = {}
    for code, col in (("0", "ytd_kt"), ("1", "ytd_kusd")):
        q = {"query": [{"code": ind["code"], "selection": {"filter": "item", "values": [code]}},
                       {"code": com["code"], "selection": {"filter": "item", "values": [coal]}},
                       {"code": mon["code"], "selection": {"filter": "all", "values": ["*"]}}],
             "response": {"format": "json"}}
        data = requests.post(NSO_URL, json=q, timeout=60).json()["data"]
        names = dict(zip(mon["values"], mon["valueTexts"]))
        out[col] = pd.Series({names[d["key"][2]]: float(d["values"][0]) for d in data})
    df = pd.DataFrame(out).sort_index()
    df.index.name = "month"
    year = df.index.str[:4]
    df["volume_mt"] = (df["ytd_kt"].groupby(year).diff().fillna(df["ytd_kt"]) / 1000).round(4)
    df["value_musd"] = (df["ytd_kusd"].groupby(year).diff().fillna(df["ytd_kusd"]) / 1000).round(3)
    return df.reset_index()


def _get(url, params, tries=6):
    for a in range(tries):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.json().get("data", [])
        if r.status_code == 429:
            time.sleep(3 * (a + 1))
            continue
        if r.status_code == 403 and "quota" in r.text.lower():
            # hourly call quota: "Quota will be replenished in HH:MM:SS"
            m = re.search(r"(\d+):(\d+):(\d+)", r.text)
            wait = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + 30 if m else 1800
            print(f"\n  UN quota used up; waiting {wait // 60} minutes")
            time.sleep(wait)
            continue
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    raise RuntimeError("rate limited too many times")


def fetch_comtrade(last_month: str, have: pd.DataFrame) -> pd.DataFrame:
    """Fetch every (frequency, period, side) not already in `have`; return old and new rows together."""
    done = set(zip(have["freq"], have["period"].astype(str), have["reporter"])) if len(have) else set()
    jobs = [("A", str(y)) for y in range(2010, int(last_month[:4]) + 1)]
    jobs += [("M", p.strftime("%Y%m")) for p in pd.period_range("2017-01", last_month, freq="M")]
    rows = have.to_dict("records") if len(have) else []
    for i, (freq, period) in enumerate(jobs):
        for rep, par, flow in SIDES:
            if (freq, period, rep) in done:
                continue
            params = {"reporterCode": rep, "partnerCode": par, "flowCode": flow, "cmdCode": CODES, "period": period}
            for d in _get(CT_URL.format(freq=freq), params):
                rows.append({"freq": freq, "period": d["period"], "reporter": rep, "flow": d["flowCode"],
                             "hs": d["cmdCode"], "net_kg": d["netWgt"], "qty": d["qty"],
                             "qty_unit": d["qtyUnitCode"], "qty_estimated": d["isQtyEstimated"],
                             "netwgt_estimated": d["isNetWgtEstimated"], "value_usd": d["primaryValue"],
                             "cif_usd": d["cifvalue"], "fob_usd": d["fobvalue"]})
            time.sleep(1.1)
        print(f"  {i + 1}/{len(jobs)} {freq} {period}", end="\r")
    print()
    return pd.DataFrame(rows)


if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    nso = fetch_nso()
    nso.to_csv("data/trade_nso_coal.csv", index=False)
    print(f"NSO: {len(nso)} months, last {nso['month'].iloc[-1]}")
    if "--nso-only" not in sys.argv:
        path = Path("data/trade_comtrade_coal.csv")
        have = pd.read_csv(path) if path.exists() else pd.DataFrame()
        ct = fetch_comtrade(nso["month"].iloc[-1], have)
        ct.to_csv("data/trade_comtrade_coal.csv", index=False)
        print(f"Comtrade: {len(ct)} rows")
