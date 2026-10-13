"""Build a dated truck/wagon signal from Sentinel-1 radar for one AOI.

Two steps:
  1. download: save each radar scene as a small compressed file in
     data/raw/<aoi>/ plus a catalogue CSV (skips scenes already saved).
  2. signal: for each satellite orbit separately, compare every scene with
     that orbit's per-pixel median, and record the share of pixels that are
     much brighter than usual (trucks, wagons). Static bright things like
     buildings cancel out.

Usage:
  python scripts/build_s1_signal.py gashuunsukhait 2025-01 2025-12
  python scripts/build_s1_signal.py gashuunsukhait 2025-01 2025-12 --signal-only
Writes data/s1_<aoi>.csv with columns date, relative_orbit, orbit_state,
platform, transient_fraction, bright_fraction.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from coalcast.aois import AOIS
from coalcast.features import (bright_fraction, road_signal, road_stats, rolling_transient_fraction,
                               transient_bright_fraction)

name, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
signal_only = "--signal-only" in sys.argv
aoi = AOIS[name]
raw_dir = Path("data") / "raw" / name
raw_dir.mkdir(parents=True, exist_ok=True)
catalogue_path = raw_dir / "catalogue.csv"
catalogue = pd.read_csv(catalogue_path) if catalogue_path.exists() else pd.DataFrame()
have = set(catalogue["item_id"]) if len(catalogue) else set()

# ---------- step 1: download ----------
if not signal_only:
    from coalcast.fetch import iter_s1_items
    for month in pd.period_range(first, last, freq="M"):
        start, end = str(month.start_time.date()), str(month.end_time.date())
        n_new = 0
        try:
            for meta, vv_db in iter_s1_items(aoi, start, end):
                if meta["item_id"] in have:
                    continue
                np.savez_compressed(raw_dir / f"{meta['item_id']}.npz", vv_db=vv_db.astype(np.float16))
                catalogue = pd.concat([catalogue, pd.DataFrame([meta])], ignore_index=True)
                have.add(meta["item_id"])
                n_new += 1
        except Exception as e:  # keep going if one month fails
            print(f"  {month}: error {e}")
        catalogue.to_csv(catalogue_path, index=False)  # save as we go
        print(f"  {month}: {n_new} new scenes")

# ---------- step 2: signal ----------
cat = catalogue.copy()
cat["date"] = pd.to_datetime(cat["date"])
cat = cat[(cat["date"] >= pd.Period(first).start_time) & (cat["date"] <= pd.Period(last).end_time)]
mask_path = Path("data") / f"masks_{name}.npz"
masks = np.load(mask_path) if mask_path.exists() else None
if masks is None:
    print(f"  no {mask_path}; road_signal column will be empty (see scripts/make_masks.py)")
rows = []
for orbit, group in cat.groupby("relative_orbit"):
    group = group.sort_values("date")
    stack = np.stack([np.load(raw_dir / f"{i}.npz")["vv_db"].astype(np.float32) for i in group["item_id"]])
    if len(group) < 5:
        print(f"  orbit {orbit}: only {len(group)} scenes, transient signal unreliable")
    transient = transient_bright_fraction(stack)
    rolling = rolling_transient_fraction(stack, group["date"])
    for (_, r), t, rt, img in zip(group.iterrows(), transient, rolling, stack):
        road = road_signal(img, masks["road"], masks["control"]) if masks is not None else np.nan
        extra = road_stats(img, masks["road"], masks["control"]) if masks is not None else {}
        rows.append({**r.drop("item_id").to_dict(), "road_signal": road, **extra, "transient_fraction": t,
                     "rolling_transient": rt, "bright_fraction": bright_fraction(img)})

out = Path("data") / f"s1_{name}.csv"
pd.DataFrame(rows).sort_values("date").to_csv(out, index=False)
print(f"Wrote {len(rows)} rows to {out}")
print(cat.groupby(["relative_orbit", "orbit_state"]).size().rename("scenes").to_string())
