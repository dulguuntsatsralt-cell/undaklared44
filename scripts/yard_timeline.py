"""Show the yard on one clear Sentinel-2 scene per quarter, to see when it was built.

Used to fix the yard start month for the second stockpile test from images
alone. It does not compute the coal fraction.

Usage: python scripts/yard_timeline.py gashuunsukhait 2022-01 2025-03
Writes data/yard_timeline_<aoi>.png.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from coalcast.features import SCL_NOT_CLEAR

name, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
yard = np.load(Path("data") / f"masks_{name}.npz")["yard"]
raw_dir = Path("data") / "raw_s2" / name
cat = pd.read_csv(raw_dir / "catalogue.csv", parse_dates=["date"])
cat = cat[(cat["date"] >= pd.Period(first).start_time) & (cat["date"] <= pd.Period(last).end_time)]
cat["quarter"] = cat["date"].dt.to_period("Q")

ys, xs = np.where(yard)
pad = 80
y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, yard.shape[0])
x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, yard.shape[1])

picks = []
for q, g in cat.groupby("quarter"):
    best = None
    for item in g["item_id"]:
        b = np.load(raw_dir / f"{item}.npz")["bands"]
        crop_scl, crop_b = b[4, y0:y1, x0:x1], b[0, y0:y1, x0:x1]
        clear = ((crop_b > 0) & ~np.isin(crop_scl, SCL_NOT_CLEAR)).mean()
        if best is None or clear > best[0]:
            best = (clear, item, g.loc[g["item_id"] == item, "date"].iloc[0])
    picks.append((q, *best))

cols = 4
rows = int(np.ceil(len(picks) / cols))
fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
for ax in np.ravel(axes):
    ax.axis("off")
for ax, (q, clear, item, date) in zip(np.ravel(axes), picks):
    b = np.load(raw_dir / f"{item}.npz")["bands"].astype(np.float32)[:, y0:y1, x0:x1]
    rgb = np.stack([b[2], b[1], b[0]], axis=-1)
    lo, hi = np.nanpercentile(rgb[rgb > 0], [2, 98]) if (rgb > 0).any() else (0, 1)
    ax.imshow(np.clip((rgb - lo) / max(hi - lo, 1), 0, 1))
    ax.contour(yard[y0:y1, x0:x1], levels=[0.5], colors="yellow", linewidths=0.8)
    ax.set_title(f"{q}  {date.date()}  ({clear:.0%} clear)", fontsize=9)
out = Path("data") / f"yard_timeline_{name}.png"
plt.tight_layout()
plt.savefig(out, dpi=90)
print(f"Wrote {out} ({len(picks)} quarters)")
