"""Save a cloud-free Sentinel-2 image of an AOI so you can check the box.

Usage: python scripts/preview_aoi.py gashuunsukhait [2026-06-01] [2026-09-30]
"""
import sys
from pathlib import Path

from coalcast.aois import AOIS
from coalcast.fetch import load_s2, save_rgb_preview

name = sys.argv[1]
start = sys.argv[2] if len(sys.argv) > 2 else "2026-06-01"
end = sys.argv[3] if len(sys.argv) > 3 else "2026-09-30"

aoi = AOIS[name]
print(f"{name}: bbox {aoi.bbox()}")
ds = load_s2(aoi, start, end, max_cloud=10)
out = Path("data") / f"preview_{name}.png"
save_rgb_preview(ds, out)
print(f"Saved {out}. Open it and check the road / yard / mine is inside the box.")
