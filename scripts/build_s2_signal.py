"""Coal stockpile signal from Sentinel-2 for the yards of one AOI.

Measure fixed in results/2026-10-13_stockpile_preregistration.md.

Two steps:
  1. download: save each Sentinel-2 scene (B02, B03, B04, B08, SCL) as a
     compressed file in data/raw_s2/<aoi>/ plus a catalogue CSV. Scenes
     already saved are skipped. Radar files are never touched.
  2. signal: for each scene, the share of clear yard pixels that look like
     coal. Writes data/s2_<aoi>.csv (one row per scene) and
     data/s2_<aoi>_monthly.csv (usable scenes averaged by month), plus
     data/yards_<aoi>.png showing the yard outline on a clear scene.

Usage:
  python scripts/build_s2_signal.py gashuunsukhait 2025-01 2026-09
  python scripts/build_s2_signal.py gashuunsukhait 2025-01 2026-09 --signal-only
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from coalcast.aois import AOIS
from coalcast.features import yard_coal_stats

USABLE_CLEAR = 0.8   # pre-registered: at least 80% of yard pixels clear

name, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
signal_only = "--signal-only" in sys.argv
aoi = AOIS[name]

mask_path = Path("data") / f"masks_{name}.npz"
if not mask_path.exists() or "yard" not in np.load(mask_path).files:
    sys.exit(f"No yard mask. Draw polygons named 'yard' in data/masks_{name}.geojson, "
             f"then run: python scripts/make_masks.py {name}")
yard = np.load(mask_path)["yard"]

raw_dir = Path("data") / "raw_s2" / name
raw_dir.mkdir(parents=True, exist_ok=True)
catalogue_path = raw_dir / "catalogue.csv"
catalogue = pd.read_csv(catalogue_path) if catalogue_path.exists() else pd.DataFrame()
have = set(catalogue["item_id"]) if len(catalogue) else set()

# ---------- step 1: download ----------
if not signal_only:
    from coalcast.fetch import iter_s2_items
    for month in pd.period_range(first, last, freq="M"):
        start, end = str(month.start_time.date()), str(month.end_time.date())
        n_new = 0
        try:
            for meta, arr in iter_s2_items(aoi, start, end, skip=have):
                if meta["item_id"] in have:
                    continue
                if arr.shape[1:] != yard.shape:
                    sys.exit(f"Scene grid {arr.shape[1:]} does not match the mask grid {yard.shape}.")
                np.savez_compressed(raw_dir / f"{meta['item_id']}.npz", bands=arr)
                catalogue = pd.concat([catalogue, pd.DataFrame([meta])], ignore_index=True)
                have.add(meta["item_id"])
                n_new += 1
        except SystemExit:
            raise
        except Exception as e:  # keep going if one month fails
            print(f"  {month}: error {e}")
        catalogue.to_csv(catalogue_path, index=False)  # save as we go
        print(f"  {month}: {n_new} new scenes")

# ---------- step 2: signal ----------
if catalogue.empty:
    sys.exit("No scenes downloaded yet.")
cat = catalogue.copy()
cat["date"] = pd.to_datetime(cat["date"])
cat = cat[(cat["date"] >= pd.Period(first).start_time) & (cat["date"] <= pd.Period(last).end_time)]

rows, best = [], None
for _, r in cat.sort_values("date").iterrows():
    b02, b03, b04, b08, scl = np.load(raw_dir / f"{r['item_id']}.npz")["bands"].astype(np.float32)
    stats = yard_coal_stats(b02, b03, b04, b08, scl, yard)
    rows.append({"date": r["date"].date().isoformat(), "item_id": r["item_id"],
                 "platform": r.get("platform"), "cloud_cover": r.get("cloud_cover"), **stats})
    if best is None or stats["yard_clear_frac"] > best[0]:
        best = (stats["yard_clear_frac"], r["item_id"])

scenes = pd.DataFrame(rows)
scenes["usable"] = scenes["yard_clear_frac"] >= USABLE_CLEAR
out = Path("data") / f"s2_{name}.csv"
scenes.to_csv(out, index=False)

# one scene per day (most clear yard pixels), usable only, then monthly mean
use = scenes[scenes["usable"]].sort_values("yard_clear_frac", ascending=False).drop_duplicates("date")
use = use.assign(month=pd.to_datetime(use["date"]).dt.to_period("M").astype(str))
monthly = use.groupby("month").agg(yard_coal_frac=("yard_coal_frac", "mean"), n_scenes=("date", "size"))
monthly.to_csv(Path("data") / f"s2_{name}_monthly.csv")

print(f"Wrote {len(scenes)} scenes to {out} ({int(scenes['usable'].sum())} usable)")
print(monthly.round(4).to_string())
missing = [str(m) for m in pd.period_range(first, last, freq="M") if str(m) not in monthly.index]
if missing:
    print("Months with no usable scene:", ", ".join(missing))

# visual check: yard outline on the clearest scene
if best is not None:
    import matplotlib.pyplot as plt
    b = np.load(raw_dir / f"{best[1]}.npz")["bands"].astype(np.float32)
    rgb = np.stack([b[2], b[1], b[0]], axis=-1)
    lo, hi = np.nanpercentile(rgb[rgb > 0], [2, 98])
    plt.figure(figsize=(8, 8))
    plt.imshow(np.clip((rgb - lo) / max(hi - lo, 1), 0, 1))
    plt.contour(yard, levels=[0.5], colors="yellow")
    plt.title(f"{name}: yards (yellow) on {best[1][:30]}")
    plt.axis("off")
    plt.savefig(Path("data") / f"yards_{name}.png", dpi=100, bbox_inches="tight")
    print(f"Check data/yards_{name}.png")
