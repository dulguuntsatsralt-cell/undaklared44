"""Turn imagery into numbers: per-date signals, then monthly features.

All functions take plain numpy arrays so they are easy to test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def to_db(linear: np.ndarray) -> np.ndarray:
    """Convert linear radar backscatter to decibels (dB)."""
    return 10.0 * np.log10(np.clip(linear, 1e-6, None))


def bright_fraction(vv_db: np.ndarray, mask: np.ndarray | None = None, threshold_db: float = 0.0) -> float:
    """Share of pixels brighter than `threshold_db` inside `mask`.

    On a road or rail-siding mask, this rises when trucks or wagons are
    queued. Returns NaN when the mask has no valid pixels.
    """
    valid = np.isfinite(vv_db)
    if mask is not None:
        valid &= mask.astype(bool)
    n = valid.sum()
    if n == 0:
        return float("nan")
    return float((vv_db[valid] > threshold_db).sum() / n)


def transient_bright_fraction(stack_db: np.ndarray, threshold_db: float = 3.0,
                              mask: np.ndarray | None = None) -> np.ndarray:
    """Per-image share of pixels much brighter than their usual level.

    `stack_db` has shape (time, y, x) and must come from ONE satellite orbit
    (same viewing angle). Buildings, fences and rock are bright in every
    image, so the per-pixel median over time captures them; trucks and
    wagons come and go, so they show up as pixels more than `threshold_db`
    above that median. Returns one value per image.
    """
    stack_db = np.asarray(stack_db, dtype=float)
    background = np.nanmedian(stack_db, axis=0)
    excess = stack_db - background[None, :, :]
    valid = np.isfinite(excess)
    if mask is not None:
        valid &= mask.astype(bool)[None, :, :]
    hits = (excess > threshold_db) & valid
    n = valid.sum(axis=(1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, hits.sum(axis=(1, 2)) / n, np.nan)


def rolling_transient_fraction(stack_db: np.ndarray, dates, window_days: int = 60,
                               threshold_db: float = 3.0, mask: np.ndarray | None = None,
                               normalize: bool = True) -> np.ndarray:
    """Like `transient_bright_fraction`, with two fixes for real scenes.

    - Background is the per-pixel median of the OTHER same-orbit scenes within
      `window_days` of each scene, so slow change (construction, new yards)
      is absorbed instead of counting as trucks for the rest of the series.
    - `normalize` removes each scene's overall brightness shift (the median
      difference from background across the box) before thresholding. Rain
      and frozen ground brighten everything at once; trucks brighten a few
      pixels.
    Scenes with no neighbours in the window get NaN.
    """
    stack_db = np.asarray(stack_db, dtype=float)
    dates = pd.to_datetime(pd.Series(dates)).to_numpy()
    out = np.full(len(stack_db), np.nan)
    valid_mask = None if mask is None else mask.astype(bool)
    for i in range(len(stack_db)):
        gap = np.abs((dates - dates[i]) / np.timedelta64(1, "D"))
        nb = np.where((gap <= window_days) & (np.arange(len(stack_db)) != i))[0]
        if len(nb) == 0:
            continue
        background = np.nanmedian(stack_db[nb], axis=0)
        excess = stack_db[i] - background
        if normalize:
            excess = excess - np.nanmedian(excess)
        valid = np.isfinite(excess)
        if valid_mask is not None:
            valid &= valid_mask
        n = valid.sum()
        if n:
            out[i] = ((excess > threshold_db) & valid).sum() / n
    return out


def polygon_mask(xs: np.ndarray, ys: np.ndarray, polygons_xy: list[np.ndarray]) -> np.ndarray:
    """Boolean (len(ys), len(xs)) mask of pixel centres inside any polygon.

    `xs`, `ys` are pixel-centre coordinates of the image grid; each polygon
    is an (N, 2) array of (x, y) vertices in the same projection.
    """
    from matplotlib.path import Path as MplPath
    X, Y = np.meshgrid(xs, ys)
    pts = np.column_stack([X.ravel(), Y.ravel()])
    mask = np.zeros(len(pts), dtype=bool)
    for poly in polygons_xy:
        mask |= MplPath(np.asarray(poly)).contains_points(pts)
    return mask.reshape(len(ys), len(xs))


def road_signal(vv_db: np.ndarray, road: np.ndarray, control: np.ndarray, k_db: float = 6.0) -> float:
    """Share of road pixels at least `k_db` brighter than nearby plain desert.

    The control area's median sets the reference level in each image, so rain,
    frozen ground and season (which brighten road and desert alike) cancel.
    Metal trucks and wagons are strong radar reflectors and stand out well
    above bare ground. Tune `k_db` once you have masks (5 to 8 dB is typical).
    """
    road, control = road.astype(bool), control.astype(bool)
    ref = np.nanmedian(vv_db[control & np.isfinite(vv_db)]) if (control & np.isfinite(vv_db)).any() else np.nan
    valid = road & np.isfinite(vv_db)
    if not valid.any() or not np.isfinite(ref):
        return float("nan")
    return float((vv_db[valid] > ref + k_db).sum() / valid.sum())


def road_stats(vv_db: np.ndarray, road: np.ndarray, control: np.ndarray) -> dict:
    """Continuous road measures relative to the control desert (all in dB or shares).

    A fixed threshold saturates when the road area is bright to begin with
    (paving, fences, nearby buildings): every pixel passes and the signal
    sits at 1.0. These measures keep varying:
      road_excess_db  median road brightness minus median control brightness
      road_p90_db     90th percentile of road minus control median (busiest parts)
      road_frac12     share of road pixels 12 dB above control (strong metal returns)
    """
    road, control = road.astype(bool), control.astype(bool)
    r = vv_db[road & np.isfinite(vv_db)]
    c = vv_db[control & np.isfinite(vv_db)]
    if len(r) == 0 or len(c) == 0:
        return {"road_excess_db": np.nan, "road_p90_db": np.nan, "road_frac12": np.nan}
    ref = float(np.median(c))
    return {
        "road_excess_db": float(np.median(r) - ref),
        "road_p90_db": float(np.percentile(r, 90) - ref),
        "road_frac12": float((r > ref + 12.0).mean()),
    }


# Sentinel-2 scene classification (SCL) classes that are not usable ground:
# 0 no data, 1 saturated, 3 cloud shadow, 8 cloud medium, 9 cloud high, 10 cirrus, 11 snow
SCL_NOT_CLEAR = (0, 1, 3, 8, 9, 10, 11)


L2A_OFFSET = 1000.0  # processing baseline 04.00+ (all scenes since Jan 2022) stores reflectance*10000 + 1000
BASELINE_04_START = "2022-01-25"  # first acquisitions processed with baseline 04.00


def l2a_offset(processing_baseline=None, date=None) -> float:
    """The value to subtract from raw Sentinel-2 L2A bands to get reflectance x 10000.

    Uses the scene's processing baseline when known (04.00 or later has the
    +1000 offset); otherwise falls back to the acquisition date.
    """
    if processing_baseline is not None and str(processing_baseline) not in ("", "nan", "None"):
        return L2A_OFFSET if float(processing_baseline) >= 4.0 else 0.0
    if date is None:
        raise ValueError("Need a processing baseline or a date.")
    return L2A_OFFSET if str(date)[:10] >= BASELINE_04_START else 0.0


def yard_coal_stats(b02, b03, b04, b08, scl, yard, max_reflectance: float = 800.0,
                    offset: float = L2A_OFFSET) -> dict:
    """Coal cover inside the yard mask for one Sentinel-2 scene.

    Returns `yard_clear_frac` (share of yard pixels that are clear ground)
    and `yard_coal_frac` (share of clear yard pixels that look like coal:
    all four bands below `max_reflectance` after removing the L2A `offset`,
    i.e. below 8% reflectance). Raw value 0 means no data.
    `yard_coal_frac` is NaN when no yard pixel is clear.
    """
    yard = np.asarray(yard, bool)
    n_yard = int(yard.sum())
    if n_yard == 0:
        return {"yard_clear_frac": float("nan"), "yard_coal_frac": float("nan")}
    bands = [np.asarray(b, float) for b in (b02, b03, b04, b08)]
    has_data = np.all([np.isfinite(b) & (b > 0) for b in bands], axis=0)
    clear = yard & has_data & ~np.isin(np.asarray(scl), SCL_NOT_CLEAR)
    n_clear = int(clear.sum())
    out = {"yard_clear_frac": n_clear / n_yard}
    if n_clear == 0:
        out["yard_coal_frac"] = float("nan")
    else:
        dark = np.all([(b - offset) < max_reflectance for b in bands], axis=0)
        out["yard_coal_frac"] = float((dark & clear).sum() / n_clear)
    return out


def coal_fraction(b02: np.ndarray, b03: np.ndarray, b04: np.ndarray, b08: np.ndarray,
                  clear: np.ndarray | None = None, max_reflectance: float = 800.0) -> float:
    """Share of clear pixels that look like coal: very dark in visible and near-infrared.

    Reflectance is in Sentinel-2 L2A digital numbers (0..10000). Coal piles are
    typically below about 8% reflectance in all four bands. Tune the threshold
    on a few hand-labelled images before trusting it.
    """
    dark = (b02 < max_reflectance) & (b03 < max_reflectance) & (b04 < max_reflectance) & (b08 < max_reflectance)
    valid = np.isfinite(b02) & (b02 > 0)
    if clear is not None:
        valid &= clear.astype(bool)
    n = valid.sum()
    if n == 0:
        return float("nan")
    return float((dark & valid).sum() / n)


def monthly_features(signal: pd.Series, name: str, as_of_day: int | None = None) -> pd.DataFrame:
    """Aggregate a dated signal into monthly features.

    `as_of_day` builds a nowcast vintage: only observations on or before that
    day of each month are used (e.g. 10 = what you knew on the 10th).
    """
    s = signal.dropna().sort_index()
    if as_of_day is not None:
        s = s[s.index.day <= as_of_day]
    g = s.groupby(s.index.to_period("M"))
    out = pd.DataFrame({
        f"{name}_mean": g.mean(),
        f"{name}_max": g.max(),
        f"{name}_n_obs": g.size(),
    })
    out[f"{name}_slope"] = g.apply(_slope)
    return out


def _slope(x: pd.Series) -> float:
    if len(x) < 2:
        return 0.0
    days = (x.index - x.index[0]).days.to_numpy(dtype=float)
    if days.max() == 0:
        return 0.0
    return float(np.polyfit(days, x.to_numpy(dtype=float), 1)[0])


def line_buffer_mask(xs: np.ndarray, ys: np.ndarray, line_xy: np.ndarray, width_m: float) -> np.ndarray:
    """Pixels whose centre lies within `width_m` metres of a polyline (same projected units as xs, ys)."""
    X, Y = np.meshgrid(xs, ys)
    best = np.full(X.shape, np.inf)
    for (x0, y0), (x1, y1) in zip(line_xy[:-1], line_xy[1:]):
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1) if L2 > 0 else 0.0
        best = np.minimum(best, np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)))
    return best <= width_m


# Moving-truck detector for Sentinel-2 (after Fisser et al. 2022, Remote Sensing 14:1595).
# The blue, green and red bands are captured a fraction of a second apart, so a
# moving truck lands in a slightly different place in each: a blue-tinted pixel
# with a red-tinted pixel a few metres further along. Parked trucks and buildings
# have no colour offset. Thresholds are in reflectance (0..1).
TRUCK_PARAMS = dict(min_rise=0.02, tint=1.15, max_gap_px=3)


def moving_trucks(b02, b03, b04, scl, road, offset: float = 1000.0, min_rise: float = TRUCK_PARAMS["min_rise"],
                  tint: float = TRUCK_PARAMS["tint"], max_gap_px: int = TRUCK_PARAMS["max_gap_px"]) -> dict:
    """Count moving trucks on the road mask in one Sentinel-2 scene.

    A blue pixel: blue at least `min_rise` above the road's median blue, and its
    blue/red ratio at least `tint` times the road's usual ratio. A red pixel: the
    same with red and blue swapped. A truck is a connected group of blue pixels
    with a red pixel within `max_gap_px` pixels. Returns road_clear_frac,
    n_trucks, and the (row, col) of each truck (first blue pixel).
    """
    from scipy import ndimage
    road = np.asarray(road, bool)
    bands = [(np.asarray(b, float) - offset) / 10000.0 for b in (b02, b03, b04)]
    raw = [np.asarray(b, float) for b in (b02, b03, b04)]
    has_data = np.all([np.isfinite(r) & (r > 0) for r in raw], axis=0)
    clear = road & has_data & ~np.isin(np.asarray(scl), SCL_NOT_CLEAR)
    n_road = int(road.sum())
    out = {"road_clear_frac": clear.sum() / n_road if n_road else float("nan"), "n_trucks": 0, "where": []}
    if clear.sum() < 20:
        out["n_trucks"] = float("nan")
        return out
    blue, _, red = bands
    bg_b, bg_r = np.median(blue[clear]), np.median(red[clear])
    ratio = (bg_b + 1e-6) / (bg_r + 1e-6)
    with np.errstate(divide="ignore", invalid="ignore"):
        is_blue = clear & (blue - bg_b > min_rise) & (blue / red > ratio * tint)
        is_red = clear & (red - bg_r > min_rise) & (red / blue > tint / ratio)
    near_red = ndimage.binary_dilation(is_red, iterations=max_gap_px)
    labels, n = ndimage.label(is_blue, structure=np.ones((3, 3)))
    where = []
    for i, sl in enumerate(ndimage.find_objects(labels), start=1):
        comp = labels[sl] == i
        if (near_red[sl] & comp).any():
            r, c = np.argwhere(comp)[0]
            where.append((sl[0].start + r, sl[1].start + c))
    out["n_trucks"], out["where"] = len(where), where
    return out
