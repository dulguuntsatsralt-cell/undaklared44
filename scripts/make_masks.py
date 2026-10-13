"""Turn hand-drawn road and control areas into pixel masks for one AOI.

1. Go to https://geojson.io and zoom to the AOI.
2. Draw one or more polygons along the road where trucks queue. For each,
   add a property  name = road  (click the shape, then "Add row" in the table).
3. Draw one polygon over plain desert nearby with no roads or buildings,
   property  name = control.
4. Save as GeoJSON to data/masks_<aoi>.geojson.
5. Run:  python scripts/make_masks.py gashuunsukhait

Writes data/masks_<aoi>.npz and data/masks_<aoi>.png (masks drawn over the
radar image) so you can check that the road mask sits on the road.
"""
import json
import sys
from pathlib import Path

import numpy as np

from coalcast.aois import AOIS
from coalcast.features import polygon_mask

name = sys.argv[1]
aoi = AOIS[name]
geojson_path = Path("data") / f"masks_{name}.geojson"
raw_dir = Path("data") / "raw" / name
grid_path = raw_dir / "grid.npz"

# grid of the saved scenes
if grid_path.exists():
    g = np.load(grid_path)
    xs, ys = g["xs"], g["ys"]
else:
    from coalcast.fetch import s1_grid
    xs, ys = s1_grid(aoi)
    raw_dir.mkdir(parents=True, exist_ok=True)
    np.savez(grid_path, xs=xs, ys=ys)

# polygons, lon/lat -> UTM zone 48N (same projection as the scenes)
from pyproj import Transformer
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)
polys = {"road": [], "control": []}
for f in json.loads(geojson_path.read_text())["features"]:
    label = str(f.get("properties", {}).get("name", "")).strip().lower()
    if label not in polys:
        print(f"  skipping a shape with name={label!r} (use road or control)")
        continue
    geom = f["geometry"]
    rings = [geom["coordinates"][0]] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
    for ring in rings:
        lon, lat = np.array(ring).T
        x, y = to_utm.transform(lon, lat)
        polys[label].append(np.column_stack([x, y]))

if not polys["road"] or not polys["control"]:
    sys.exit("Need at least one 'road' and one 'control' polygon.")

road = polygon_mask(xs, ys, polys["road"])
control = polygon_mask(xs, ys, polys["control"])
print(f"road: {road.sum()} pixels, control: {control.sum()} pixels")
if road.sum() < 50:
    print("  road mask is very small; check the polygons are inside the AOI box")
np.savez(Path("data") / f"masks_{name}.npz", road=road, control=control)

# overlay on the median radar image for a visual check
scenes = sorted(raw_dir.glob("*.npz"))
scenes = [s for s in scenes if s.name != "grid.npz"][:20]
if scenes:
    import matplotlib.pyplot as plt
    med = np.nanmedian(np.stack([np.load(s)["vv_db"].astype(np.float32) for s in scenes]), axis=0)
    if med.shape != road.shape:
        sys.exit(f"Grid shape {road.shape} does not match saved scenes {med.shape}; delete {grid_path} and rerun.")
    plt.figure(figsize=(8, 8))
    plt.imshow(med, cmap="gray", vmin=-25, vmax=5)
    plt.contour(road, levels=[0.5], colors="red")
    plt.contour(control, levels=[0.5], colors="cyan")
    plt.title(f"{name}: road (red), control (cyan)")
    plt.axis("off")
    out = Path("data") / f"masks_{name}.png"
    plt.savefig(out, dpi=100, bbox_inches="tight")
    print(f"Check {out}")
