"""Download Sentinel-1 radar and Sentinel-2 optical imagery for an AOI.

Uses the Microsoft Planetary Computer STAC API, which is free. Searching needs
no account; the `planetary_computer` package signs asset URLs automatically.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .aois import AOI

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def _catalog():
    import planetary_computer
    import pystac_client
    return pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def search(aoi: AOI, collection: str, start: str, end: str, max_cloud: int | None = None):
    query = {"eo:cloud_cover": {"lt": max_cloud}} if max_cloud is not None else None
    items = _catalog().search(
        collections=[collection], bbox=aoi.bbox(), datetime=f"{start}/{end}", query=query
    ).item_collection()
    return list(items)


def load_s1(aoi: AOI, start: str, end: str):
    """Sentinel-1 radiometrically terrain corrected backscatter (VV, VH), 10 m.

    Returns an xarray Dataset with dims (time, y, x). Trucks and wagons are
    strong reflectors, so they show up as bright pixels in VV.
    """
    import odc.stac
    items = search(aoi, "sentinel-1-rtc", start, end)
    if not items:
        raise RuntimeError(f"No Sentinel-1 scenes for {aoi.name} {start}..{end}")
    return odc.stac.load(items, bands=["vv", "vh"], bbox=aoi.bbox(),
                         crs="EPSG:32648", resolution=10, groupby="solar_day")


def iter_s1_items(aoi: AOI, start: str, end: str, skip=frozenset()):
    """Yield (metadata, vv_db array) for each Sentinel-1 scene, one at a time.

    Each scene is loaded on the same 10 m grid, so arrays from different
    dates line up pixel for pixel. Metadata includes the relative orbit,
    because backscatter depends strongly on viewing angle: only compare
    scenes from the same orbit.
    """
    import odc.stac
    from .features import to_db
    for item in sorted(search(aoi, "sentinel-1-rtc", start, end), key=lambda i: i.datetime):
        if item.id in skip:
            continue
        ds = odc.stac.load([item], bands=["vv"], bbox=aoi.bbox(), crs="EPSG:32648", resolution=10)
        meta = {
            "date": item.datetime.date().isoformat(),
            "item_id": item.id,
            "platform": item.properties.get("platform"),
            "relative_orbit": item.properties.get("sat:relative_orbit"),
            "orbit_state": item.properties.get("sat:orbit_state"),
        }
        yield meta, to_db(ds["vv"].isel(time=0).values).astype(np.float32)


def s1_grid(aoi: AOI, start: str = "2025-06-01", end: str = "2025-07-31"):
    """Pixel-centre coordinates (xs, ys) in EPSG:32648 of the grid used for this AOI's scenes."""
    import odc.stac
    items = search(aoi, "sentinel-1-rtc", start, end)
    if not items:
        raise RuntimeError(f"No Sentinel-1 scenes for {aoi.name} {start}..{end}")
    ds = odc.stac.load(items[:1], bands=["vv"], bbox=aoi.bbox(), crs="EPSG:32648", resolution=10)
    return ds.x.values, ds.y.values


S2_BANDS = ["B02", "B03", "B04", "B08", "SCL"]


def iter_s2_items(aoi: AOI, start: str, end: str, max_cloud: int = 60, skip=frozenset()):
    """Yield (metadata, array) for each Sentinel-2 L2A scene, one at a time.

    The array has shape (5, y, x): B02, B03, B04, B08, SCL as uint16, on the
    same 10 m grid as the radar scenes (same box, projection and pixel
    size), so the hand-drawn masks line up with both. `max_cloud` is the
    whole-tile cloud cover filter; the yard itself is checked later with SCL.
    Scenes whose id is in `skip` are not downloaded.
    """
    import odc.stac
    for item in sorted(search(aoi, "sentinel-2-l2a", start, end, max_cloud=max_cloud), key=lambda i: i.datetime):
        if item.id in skip:
            continue
        ds = odc.stac.load([item], bands=S2_BANDS, bbox=aoi.bbox(), crs="EPSG:32648", resolution=10)
        # pixels outside the scene's footprint come back empty; store them as 0 (= no data)
        arr = np.nan_to_num(np.stack([ds[b].isel(time=0).values for b in S2_BANDS]), nan=0).astype(np.uint16)
        meta = {
            "date": item.datetime.date().isoformat(),
            "item_id": item.id,
            "platform": item.properties.get("platform"),
            "cloud_cover": item.properties.get("eo:cloud_cover"),
        }
        yield meta, arr


def load_s2(aoi: AOI, start: str, end: str, max_cloud: int = 30):
    """Sentinel-2 L2A surface reflectance (B02, B03, B04, B08, SCL), 10 m."""
    import odc.stac
    items = search(aoi, "sentinel-2-l2a", start, end, max_cloud=max_cloud)
    if not items:
        raise RuntimeError(f"No Sentinel-2 scenes for {aoi.name} {start}..{end}")
    return odc.stac.load(items, bands=["B02", "B03", "B04", "B08", "SCL"], bbox=aoi.bbox(),
                         crs="EPSG:32648", resolution=10, groupby="solar_day")


def save_rgb_preview(ds, path: Path) -> Path:
    """Save the clearest Sentinel-2 date as a PNG so you can check the AOI."""
    import matplotlib.pyplot as plt
    clear = (~ds["SCL"].isin([3, 8, 9, 10])).mean(dim=("x", "y"))  # not cloud/shadow
    t = int(clear.argmax(dim="time"))
    rgb = np.stack([ds[b].isel(time=t).values for b in ("B04", "B03", "B02")], axis=-1).astype(float)
    # Stretch each band between its 2nd and 98th percentile. A fixed scale
    # washes out bright desert, so adapt the contrast to the scene instead.
    for i in range(3):
        band = rgb[..., i]
        lo, hi = np.nanpercentile(band[band > 0], [2, 98])
        rgb[..., i] = (band - lo) / max(hi - lo, 1.0)
    plt.imsave(path, np.clip(np.nan_to_num(rgb), 0, 1))
    return path
