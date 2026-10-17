"""Count moving coal trucks on an open stretch of road with Sentinel-2.

The road line comes from OpenStreetMap (data/coal_road_osm.geojson). Pixels
within ROAD_WIDTH_M of it form the road mask. Each scene's trucks are found
with coalcast.features.moving_trucks (colour offset of moving vehicles).

Three separate steps, so the test years are never counted before the
detector is fixed:
  (default)  download: save each scene (B02, B03, B04, B08, SCL) to
             data/raw_s2/<aoi>/ plus catalogue.csv; scenes already saved are
             skipped. Counts nothing.
  --tune N   draw zoomed crops of detections on N clear scenes from 2023-2024
             only (data/truck_tune_<aoi>.png), to check the detector by eye
  --signal   count trucks in every scene in the date range; write
             data/trucks_<aoi>.csv and data/trucks_<aoi>_monthly.csv

Usage:
  python scripts/build_trucks.py coal_road 2019-01 2024-12              # download only
  python scripts/build_trucks.py coal_road 2023-01 2024-12 --tune 12   # tuning images
  python scripts/build_trucks.py coal_road 2019-01 2024-12 --signal    # counts
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from coalcast.aois import AOIS
from coalcast.features import l2a_offset, line_buffer_mask, moving_trucks

ROAD_WIDTH_M = 20.0     # half-width of the road mask around the OSM centre line
USABLE_CLEAR = 0.9      # share of road pixels that must be clear

args = [a for a in sys.argv[1:] if not a.startswith("--")]
name, first, last = args[0], args[1], args[2]
signal_only = "--signal" in sys.argv
tune_n = int(sys.argv[sys.argv.index("--tune") + 1]) if "--tune" in sys.argv else 0
aoi = AOIS[name]
raw_dir = Path("data") / "raw_s2" / name
raw_dir.mkdir(parents=True, exist_ok=True)

# ---------- grid and road mask ----------
grid_path = raw_dir / "grid.npz"
if grid_path.exists():
    g = np.load(grid_path)
    xs, ys = g["xs"], g["ys"]
else:
    from coalcast.fetch import s1_grid
    xs, ys = s1_grid(aoi)
    np.savez(grid_path, xs=xs, ys=ys)
from pyproj import Transformer
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)
line = np.array(json.loads(Path("data/coal_road_osm.geojson").read_text())["features"][0]["geometry"]["coordinates"])
lx, ly = to_utm.transform(line[:, 0], line[:, 1])
road = line_buffer_mask(xs, ys, np.column_stack([lx, ly]), ROAD_WIDTH_M)
road_km = road.sum() * 100.0 / (2 * ROAD_WIDTH_M) / 1000.0
np.savez(Path("data") / f"road_{name}.npz", road=road)
print(f"Road mask: {int(road.sum())} pixels, about {road_km:.1f} km of road")

catalogue_path = raw_dir / "catalogue.csv"
catalogue = pd.read_csv(catalogue_path) if catalogue_path.exists() else pd.DataFrame()
have = set(catalogue["item_id"]) if len(catalogue) else set()

# ---------- download ----------
if not signal_only and not tune_n:
    from coalcast.fetch import iter_s2_items
    for month in pd.period_range(first, last, freq="M"):
        start, end = str(month.start_time.date()), str(month.end_time.date())
        n_new = 0
        try:
            for meta, arr in iter_s2_items(aoi, start, end, skip=have):
                if meta["item_id"] in have:
                    continue
                if arr.shape[1:] != road.shape:
                    sys.exit(f"Scene grid {arr.shape[1:]} does not match the road grid {road.shape}.")
                np.savez_compressed(raw_dir / f"{meta['item_id']}.npz", bands=arr)
                catalogue = pd.concat([catalogue, pd.DataFrame([meta])], ignore_index=True)
                have.add(meta["item_id"])
                n_new += 1
        except SystemExit:
            raise
        except Exception as e:  # keep going if one month fails
            print(f"  {month}: error {e}")
        catalogue.to_csv(catalogue_path, index=False)
        print(f"  {month}: {n_new} new scenes")

if not signal_only and not tune_n:
    print("Download finished. Next: --tune 12 on 2023-01 2024-12, then --signal.")
    sys.exit(0)
if catalogue.empty:
    sys.exit("No scenes downloaded yet.")
cat = catalogue.copy()
cat["date"] = pd.to_datetime(cat["date"])
cat = cat[(cat["date"] >= pd.Period(first).start_time) & (cat["date"] <= pd.Period(last).end_time)]


def detect(row):
    b = np.load(raw_dir / f"{row['item_id']}.npz")["bands"]
    off = l2a_offset(row.get("processing_baseline"), row["date"].date().isoformat())
    return b, moving_trucks(b[0], b[1], b[2], b[4], road, offset=off)


# ---------- tuning images (2023-2024 only) ----------
if tune_n:
    import matplotlib.pyplot as plt
    pool = cat[(cat["date"] >= "2023-01-01") & (cat["date"] <= "2024-12-31")].sample(frac=1, random_state=0)
    picked = []
    for _, row in pool.iterrows():
        b, res = detect(row)
        if res["road_clear_frac"] >= USABLE_CLEAR:
            picked.append((row, b, res))
        if len(picked) == tune_n:
            break
    rr, cc = np.where(road)
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(len(picked), 6, figsize=(12, 2.1 * len(picked)))
    for k, (row, b, res) in enumerate(picked):
        off = l2a_offset(row.get("processing_baseline"), row["date"].date().isoformat())
        rgb = np.clip((np.stack([b[2], b[1], b[0]], -1).astype(float) - off) / 2500.0, 0, 1)
        spots = [("TRUCK", p) for p in res["where"][:4]]
        while len(spots) < 6:   # random road crops to look for missed trucks
            i = rng.integers(len(rr))
            spots.append(("road", (rr[i], cc[i])))
        for j, (kind, (r, c)) in enumerate(spots):
            ax = axes[k, j] if len(picked) > 1 else axes[j]
            r0, c0 = max(r - 15, 0), max(c - 15, 0)
            ax.imshow(rgb[r0:r0 + 30, c0:c0 + 30], interpolation="nearest")
            if kind == "TRUCK":
                ax.add_patch(plt.Rectangle((c - c0 - 2.5, r - r0 - 2.5), 5, 5, fill=False, color="yellow", lw=1))
            ax.set_title(f"{row['date'].date()} {kind}" if j == 0 else kind, fontsize=7)
            ax.axis("off")
        print(f"  {row['date'].date()}: {res['n_trucks']} trucks")
    plt.tight_layout()
    out = Path("data") / f"truck_tune_{name}.png"
    plt.savefig(out, dpi=110)
    print(f"Check {out}: yellow boxes should sit on vehicles; 'road' crops show what was not flagged.")
    sys.exit(0)

# ---------- signal ----------
rows = []
for _, row in cat.sort_values("date").iterrows():
    _, res = detect(row)
    rows.append({"date": row["date"].date().isoformat(), "item_id": row["item_id"],
                 "road_clear_frac": res["road_clear_frac"], "n_trucks": res["n_trucks"]})
scenes = pd.DataFrame(rows)
scenes["usable"] = scenes["road_clear_frac"] >= USABLE_CLEAR
scenes["trucks_per_10km"] = scenes["n_trucks"] / (road_km * scenes["road_clear_frac"]) * 10
scenes.to_csv(Path("data") / f"trucks_{name}.csv", index=False)
use = scenes[scenes["usable"]].sort_values("road_clear_frac", ascending=False).drop_duplicates("date")
use = use.assign(month=pd.to_datetime(use["date"]).dt.to_period("M").astype(str))
monthly = use.groupby("month").agg(trucks_per_10km=("trucks_per_10km", "mean"), n_scenes=("date", "size"))
monthly.to_csv(Path("data") / f"trucks_{name}_monthly.csv")
print(f"Wrote {len(scenes)} scenes ({int(scenes['usable'].sum())} usable), {len(monthly)} months")
