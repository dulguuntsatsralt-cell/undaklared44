# Pre-registration: stockpile test v2 (backlog sign, 2022 to 2024)

Written on 2026-10-14, before any Sentinel-2 data for 2022 to 2024 was downloaded or looked at, and before the 2022 to 2024 export figures were compared with anything. This file is not edited after the first results; changes go in a new, dated file.

## Where this comes from

The first stockpile test (2026-10-13) failed: the yard coal fraction moved with exports in 2025 (detrended r +0.42) and against them in 2026 (detrended r -0.69). One reading, listed as a risk before that test, is that coal in a yard is a stock: a full yard can mean coal is piling up because it is not crossing. This test checks that reading on three years nobody has looked at. The sign comes from the 2026 result, so 2025 and 2026 are not part of this test.

## Data

- **Exports:** official monthly coal export volume from the National Statistics Office of Mongolia, table DT_NSO_1400_006V2_month (cumulative, thousand tonnes), turned into monthly figures by differencing within each year. Saved as `data/exports_nso_monthly.csv`. It matches the series used in the first test to within 0.3 Mt in every month of 2025 and 2026.
- **Imagery:** Sentinel-2 L2A, same bands, grid and area box as before.
- **Yard:** the `yard` polygon in `data/masks_gashuunsukhait.geojson` exactly as committed in f38ce78 (md5 e91c3100ad6982ac7f6fff83af4676b1). It is not redrawn for this test.

## Measure (unchanged from the first test)

- Clear pixel: has data and SCL not in no-data, saturated, cloud shadow, cloud medium or high, cirrus, snow.
- Coal pixel: all four bands below 8% reflectance. Raw values have the L2A offset removed: 1000 for scenes with processing baseline 04.00 or later, 0 for earlier scenes (before 25 January 2022). If a scene has no baseline recorded, the acquisition date decides.
- Usable scene: at least 80% of yard pixels clear; one scene per day (most clear pixels).
- Monthly value: mean coal fraction of usable scenes. Empty months stay empty.
- Form: **level**. Sign: **negative** (more coal in the yard, lower exports).

## Yard start month

The yard may not have existed in its current form in early 2022. Before the coal fraction for 2022 to 2024 is computed, one clear true-colour image per quarter is made with `scripts/yard_timeline.py` (it shows the yard and computes nothing else). The first month the yard area is clearly in use as coal storage is chosen from those images alone and written to `results/2026-10-14_yard_start.md`, with the image, before scoring. Earlier months are excluded.

## Test (once)

`scripts/score_stockpile_v2.py`, months from the yard start month (at the earliest January 2022) to December 2024.

Each series has its own straight-line trend removed **within each calendar year**. This is different from the first test, which removed one line over the whole period. Exports roughly tripled from 2022 to 2024, with a slow start in 2022, so a single line would leave most of that growth in, and the backlog idea is about month-to-month swings, not growth. Years with fewer than 6 scored months are dropped.

**Pass** if both hold:

1. The pooled within-year detrended correlation is **-0.30 or lower**.
2. The within-year correlation is negative in **at least 2 of the years** scored.

The raw correlation is reported but is not part of the rule, because shared growth can make it positive even when the backlog reading is right.

Anything else is a fail, reported with the numbers.

## Known limits, stated in advance

- One border yard on the Chinese side. Coal also crosses at other ports and by rail.
- 2022 includes border closures and reopening, which can move both series for reasons unrelated to the yard.
- A pass would show a pattern in three years of history, not a working nowcast. The next step after a pass would be to score October 2026 onward as it is released.
