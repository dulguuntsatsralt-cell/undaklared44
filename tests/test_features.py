import numpy as np
import pandas as pd
import pytest

from coalcast.aois import AOIS
from coalcast.features import bright_fraction, coal_fraction, monthly_features, to_db


def test_to_db_known_values():
    assert to_db(np.array([1.0]))[0] == pytest.approx(0.0)
    assert to_db(np.array([0.1]))[0] == pytest.approx(-10.0)


def test_bright_fraction_counts_only_masked_pixels():
    img = np.full((10, 10), -15.0)
    img[0, :5] = 5.0                      # 5 bright "trucks" on the road row
    road = np.zeros((10, 10), bool)
    road[0, :] = True                     # road is the first row
    assert bright_fraction(img, road) == pytest.approx(0.5)
    assert bright_fraction(img) == pytest.approx(0.05)


def test_bright_fraction_handles_empty_and_nan():
    img = np.full((4, 4), np.nan)
    assert np.isnan(bright_fraction(img))
    assert np.isnan(bright_fraction(np.zeros((4, 4)), np.zeros((4, 4), bool)))


def test_coal_fraction_detects_dark_pixels_and_respects_clear_mask():
    bright = np.full((10, 10), 3000.0)
    dark = bright.copy()
    dark[:2, :] = 300.0                   # 20% coal
    assert coal_fraction(dark, dark, dark, dark) == pytest.approx(0.2)
    clear = np.ones((10, 10), bool)
    clear[:2, :] = False                  # coal rows covered by cloud
    assert coal_fraction(dark, dark, dark, dark, clear) == pytest.approx(0.0)


def test_monthly_features_and_vintage_cutoff():
    idx = pd.to_datetime(["2026-01-05", "2026-01-15", "2026-01-25", "2026-02-03"])
    s = pd.Series([0.1, 0.2, 0.6, 0.3], index=idx)
    full = monthly_features(s, "q")
    assert full.loc["2026-01", "q_n_obs"] == 3
    assert full.loc["2026-01", "q_max"] == pytest.approx(0.6)
    assert full.loc["2026-01", "q_slope"] > 0
    early = monthly_features(s, "q", as_of_day=10)
    assert early.loc["2026-01", "q_n_obs"] == 1    # only the 5th is known by the 10th
    assert early.loc["2026-01", "q_mean"] == pytest.approx(0.1)


def test_aoi_boxes_are_small_and_centred():
    for aoi in AOIS.values():
        min_lon, min_lat, max_lon, max_lat = aoi.bbox()
        assert min_lon < aoi.lon < max_lon and min_lat < aoi.lat < max_lat
        assert (max_lat - min_lat) * 111 == pytest.approx(2 * aoi.half_km, rel=1e-6)
        assert 41.5 < aoi.lat < 52.2 and 87.7 < aoi.lon < 120.0   # inside Mongolia's extent


def test_transient_ignores_static_buildings_and_finds_trucks():
    from coalcast.features import transient_bright_fraction
    rng = np.random.default_rng(0)
    stack = rng.normal(-15, 0.5, (6, 20, 20))
    stack[:, :5, :5] = 10.0                     # a building: bright in every image
    stack[2, 10, :10] = 5.0                     # trucks on a road in image 2 only
    frac = transient_bright_fraction(stack)
    assert frac[2] == pytest.approx(10 / 400)
    assert np.all(np.delete(frac, 2) == 0)     # building never counts
    road = np.zeros((20, 20), bool)
    road[10, :] = True
    assert transient_bright_fraction(stack, mask=road)[2] == pytest.approx(0.5)


def test_rolling_transient_ignores_rain_and_new_construction():
    from coalcast.features import rolling_transient_fraction, transient_bright_fraction
    rng = np.random.default_rng(0)
    n = 30
    dates = pd.date_range("2025-01-01", periods=n, freq="12D")
    stack = rng.normal(-15, 0.3, (n, 40, 40))
    stack[15:, :10, :10] = 5.0             # a yard built halfway through the year
    stack[8] += 4.0                        # rain: whole scene 4 dB brighter
    stack[22, 30, :20] = 5.0               # trucks
    old = transient_bright_fraction(stack)
    new = rolling_transient_fraction(stack, dates)
    assert old[8] > 0.5 and new[8] < 0.01           # rain no longer counts
    assert old[25] > 0.05 and new[25] < 0.01        # construction absorbed months later
    assert new[22] == pytest.approx(20 / 1600, abs=0.002)   # trucks still found


def test_polygon_mask_on_utm_grid():
    from coalcast.features import polygon_mask
    xs = np.arange(5, 100, 10.0)            # 10 pixel centres, 10 m apart
    ys = np.arange(95, 0, -10.0)            # top to bottom, like a north-up image
    square = np.array([[0, 0], [50, 0], [50, 50], [0, 50]])
    m = polygon_mask(xs, ys, [square])
    assert m.sum() == 25                    # 5 x 5 pixel centres inside
    assert m[-1, 0] and not m[0, -1]        # bottom-left inside, top-right outside


def test_road_signal_cancels_rain_and_counts_trucks():
    from coalcast.features import road_signal
    img = np.full((20, 20), -18.0)
    road = np.zeros((20, 20), bool); road[10, :] = True
    control = np.zeros((20, 20), bool); control[:5, :5] = True
    img[10, :8] = 0.0                       # 8 trucks, 18 dB above desert
    assert road_signal(img, road, control) == pytest.approx(8 / 20)
    assert road_signal(img + 5.0, road, control) == pytest.approx(8 / 20)   # rain: everything +5 dB
    assert np.isnan(road_signal(img, road, np.zeros_like(control)))


def test_road_stats_keep_varying_when_threshold_saturates():
    from coalcast.features import road_signal, road_stats
    road = np.zeros((20, 20), bool); road[10, :] = True
    control = np.zeros((20, 20), bool); control[:5, :5] = True
    quiet = np.full((20, 20), -18.0); quiet[10, :] = -8.0          # bright paved road, no trucks
    busy = quiet.copy(); busy[10, :12] = 0.0                       # trucks on 12 of 20 pixels
    assert road_signal(quiet, road, control) == road_signal(busy, road, control) == 1.0   # saturated
    q, b = road_stats(quiet, road, control), road_stats(busy, road, control)
    assert b["road_excess_db"] > q["road_excess_db"]
    assert q["road_frac12"] == 0 and b["road_frac12"] == pytest.approx(0.6)
    assert road_stats(busy + 5, road, control)["road_excess_db"] == pytest.approx(b["road_excess_db"])


def test_yard_coal_stats_counts_coal_and_skips_clouds_and_nodata():
    from coalcast.features import yard_coal_stats
    shape = (10, 10)
    bright = np.full(shape, 3000.0)
    b = [bright.copy() for _ in range(4)]
    for band in b:
        band[:3, :] = 400.0                     # 30 coal pixels
    scl = np.full(shape, 5)                     # 5 = bare soil, clear
    yard = np.ones(shape, bool)
    s = yard_coal_stats(*b, scl, yard)
    assert s["yard_clear_frac"] == 1.0 and s["yard_coal_frac"] == pytest.approx(0.3)
    scl[8:, :] = 9                              # 20 cloudy pixels
    for band in b:
        band[7, :] = 0                          # 10 no-data pixels
    s = yard_coal_stats(*b, scl, yard)
    assert s["yard_clear_frac"] == pytest.approx(0.7)
    assert s["yard_coal_frac"] == pytest.approx(30 / 70)
    assert np.isnan(yard_coal_stats(*b, np.full(shape, 9), yard)["yard_coal_frac"])


def test_yard_coal_stats_removes_l2a_offset():
    from coalcast.features import yard_coal_stats
    shape = (10, 10)
    b = [np.full(shape, 3000.0) for _ in range(4)]  # 20% reflectance: ground
    for band in b:
        band[:4, :] = 1500.0                        # raw 1500 = 5% reflectance: coal
    scl, yard = np.full(shape, 5), np.ones(shape, bool)
    assert yard_coal_stats(*b, scl, yard)["yard_coal_frac"] == pytest.approx(0.4)
    assert yard_coal_stats(*b, scl, yard, offset=0)["yard_coal_frac"] == 0.0


def test_moving_trucks_finds_colour_offset_not_parked_trucks():
    from coalcast.features import moving_trucks
    shape = (20, 60)
    road = np.zeros(shape, bool)
    road[9:12, :] = True                                    # a 3-pixel-wide road
    b02 = np.full(shape, 1000 + 800.0)                      # road: blue 8%, red 13% reflectance
    b03 = np.full(shape, 1000 + 1000.0)
    b04 = np.full(shape, 1000 + 1300.0)
    scl = np.full(shape, 5)
    # moving dark truck: blue-shifted pixel at col 10, red-shifted two columns on; no brighter than the road
    b04[10, 10] = 1000 + 800.0
    b02[10, 12] = 1000 + 450.0
    # parked truck: brighter in all bands, same colour as the road
    b02[10, 40], b03[10, 40], b04[10, 40] = 1000 + 1600.0, 1000 + 2000.0, 1000 + 2600.0
    res = moving_trucks(b02, b03, b04, scl, road)
    assert res["n_trucks"] == 1 and res["where"][0] == (10, 10)
    assert res["road_clear_frac"] == 1.0
    scl[:] = 9                                              # all cloud: no count
    assert np.isnan(moving_trucks(b02, b03, b04, scl, road)["n_trucks"])


def test_line_buffer_mask():
    from coalcast.features import line_buffer_mask
    xs, ys = np.arange(0, 100, 10.0), np.arange(0, 100, 10.0)
    m = line_buffer_mask(xs, ys, np.array([[0.0, 50.0], [100.0, 50.0]]), 10)
    assert m[5].all() and m[4].all() and m[6].all() and not m[3].any()
