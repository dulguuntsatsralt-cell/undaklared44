# Pre-registration: moving-truck counter on the coal road (2026-10-17)

Written on 2026-10-17, before any Sentinel-2 scene of the road was downloaded or looked at. This file is not edited after the first results; changes go in a new, dated file.

## Why

Customs records on both sides already agree on how much coal crossed, so a satellite count of the border adds nothing they do not. What no record covers is the road between the mines and the border, and in particular how much coal left the state mine. Before using satellites for that, the counter has to show that it measures coal flow at all. This test checks it on the main coal road, in years when nearly all of that coal went by road.

## Method

- **Road:** the paved Ukhaa Khudag to Gashuun Sukhait coal road, OpenStreetMap way 258363586 (`data/coal_road_osm.geojson`), on an open stretch about 75 km from the border, away from towns (AOI `coal_road`, centre 42.858 N, 106.860 E, 8 km box). Road mask: pixels within 20 m of the OSM centre line.
- **Detector:** `coalcast.features.moving_trucks`, following Fisser et al. (2022, Remote Sensing 14:1595). Sentinel-2 captures blue, green and red a fraction of a second apart, so a moving vehicle shows a blue-tinted pixel with a red-tinted pixel a few metres further on; parked vehicles and buildings do not. A truck is a group of blue pixels (blue at least 0.02 above the road's median, blue/red ratio at least 1.15 times the road's usual ratio) with a red pixel (the mirror rule) within 3 pixels.
- **Scenes:** Sentinel-2 L2A, same processing and offset rules as the stockpile tests. Usable if at least 90% of road pixels are clear. One scene per day (most clear road). Count per scene is trucks per 10 km of clear road.
- **Monthly value:** mean trucks per 10 km over usable scenes. Empty months stay empty.

## Tuning, before the test

The three thresholds above are starting values. They may be changed **only** by looking at zoomed image crops from 2023 and 2024 (`--tune`), judging whether flagged spots are vehicles and whether visible vehicles are missed. No counts from 2019 to 2022 are computed and nothing is compared with exports during tuning. Any change is written to a new dated file, with the crops, and committed before the `--signal` step is run.

## Test (once)

Months: January 2019 to August 2022. The Tavan Tolgoi to Gashuun Sukhait railway was completed in September 2022, so before that this road carried nearly all coal from the Tavan Tolgoi area to the border. Target: official NSO monthly coal exports (`data/exports_nso_monthly.csv`). National exports also include other crossings; the road's share is not known month by month, which works against a pass, not for it.

**Pass** if all three hold:

1. Pearson correlation of monthly trucks per 10 km with monthly exports is **0.50 or higher**.
2. After removing a straight-line trend within each calendar year from both series, the pooled correlation is **0.30 or higher**.
3. That within-year correlation is positive in **at least 3 of the 4 years** (2022 has 8 months).

Anything else is a fail, reported with the numbers. If it fails, the next steps (counting trucks out of the state mine and comparing with its reported sales) are not attempted with this detector.

## Known limits, stated in advance

- 10 m pixels: small or slow vehicles, and trucks travelling close together, can be missed or merged.
- Dust plumes and cloud edges can create colour offsets that look like trucks.
- One 8 km stretch of a 245 km road; some coal moved on parallel unpaved tracks and is not counted.
- 2020 and 2021 include long border closures, which make exports swing a lot. Condition 2 and 3 are there so the test cannot pass on those swings alone.
