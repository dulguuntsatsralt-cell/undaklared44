# Pre-registration: coal stockpile area at Gashuun Sukhait

Written on 2026-10-13, before any Sentinel-2 yard data was downloaded or looked at. This file is not edited after the first results; changes go in a new, dated file.

## Why this measure

The road radar signal failed its out-of-sample test (see `README.md`, 2026-10-13 entry). The likely reason is that a truck queue measures congestion, not volume. Coal waiting in the border yards is closer to volume: yards fill when coal arrives faster than it crosses and empty when it crosses faster than it arrives.

## Data

- Sentinel-2 L2A surface reflectance, bands B02, B03, B04, B08 and the scene classification layer (SCL), 10 m grid, same area box as the radar work.
- Yard areas: hand-drawn polygons labelled `yard` in `data/masks_gashuunsukhait.geojson`, drawn from the satellite basemap before any measurement.
- Target: `data/exports_monthly.csv` as of this date (21 months, January 2025 to September 2026).

## Measure (fixed)

For each scene:

- A yard pixel is **clear** if it has data and its SCL class is not no-data, saturated, cloud shadow, cloud (medium or high), cirrus or snow.
- A clear pixel counts as **coal** if all four bands are below 800 (8% reflectance).
- `yard_coal_frac` = coal pixels / clear pixels.
- A scene is **usable** if at least 80% of yard pixels are clear. On days with more than one usable scene, the one with the most clear pixels is kept.

For each month: **the mean `yard_coal_frac` of its usable scenes.** Months with no usable scene are left empty, not filled.

## Two candidate forms, chosen on 2025 only

1. **Level:** monthly mean coal fraction.
2. **Change:** this month's level minus last month's.

The form with the larger absolute correlation with exports after removing a straight-line trend from both, over 2025 months only, is selected. Its sign is fixed at the same time.

## Test (once)

The selected form is scored once on January to September 2026. No thresholds, masks or months are changed after seeing 2026.

**Pass** if, on 2026 months with data:

- Pearson correlation with exports has the sign fixed on 2025 and absolute value of at least 0.5, and
- correlation after removing each series' straight-line trend has the same sign and absolute value of at least 0.3.

Anything else is reported as a fail, with the numbers.

## Known limits, stated in advance

- Coal sitting in a yard is a stock, not a flow. A full yard can mean high volume or a backlog.
- Thin clouds missed by the SCL layer can lower the coal fraction.
- 2025 has 12 months and 2026 has 9, so even a pass is weak evidence. A pass leads to adding earlier years, not to a claim.
