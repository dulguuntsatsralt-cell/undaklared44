# Truck counter tuning (2026-10-17)

Change to the detector fixed in `2026-10-17_truck_counter_preregistration.md`, made before any 2019 to 2022 scene was counted or compared with exports. Only 2023 and 2024 scenes were looked at.

## What the first tuning images showed

`--tune 12` on 2023-2024: 12 clear days, 4 detections in total. The road mask sat on the road in every crop. On 2023-01-09 two of the random road crops showed a row of coloured dots on the asphalt, the pattern of moving vehicles, and none were flagged.

## Why

Pixel values on that scene (road median: blue 0.087, red 0.134 reflectance): the bluest road pixels had blue of only 0.063 to 0.082, below the road median, and sat one to three pixels from the reddest road pixels. The trucks are dark (coal loads on dark asphalt), so the original rule, which required a moving vehicle to be at least 0.02 brighter than the road, could never fire on them. The colour offset itself was strong.

## Change

Brightness is no longer required. The detector uses only the colour shift, with colour index d = (blue - red) / (blue + red) compared with the road's median d in the scene:

- blue pixel: d at least **0.12** above the median (above the 99th percentile of road pixels on the test scene)
- red pixel: d at least **0.15** below the median
- truck: a group of blue pixels with a red pixel within **3** pixels (unchanged)

On 2023-01-09 this finds 8 trucks (0.10 / 0.12 gives 10, 0.15 / 0.18 gives 4). 0.12 / 0.15 was chosen as the middle setting before looking at any other scene.

## Next

Rerun `--tune 12` on 2023-2024 and check the new crops by eye: yellow boxes should sit on vehicles, and the random road crops should not show obvious unflagged vehicles. If that looks right, these values are final and `--signal` is run. Any further change gets its own dated note here.

## Second look (same day, settings now final)

`--tune 12` with the new settings (`2026-10-17_truck_tune.png`): 38 trucks over the 12 days, 0 to 13 per day.

- Most yellow boxes sit on dark spots with a blue or red fringe on the asphalt, which look like vehicles (2023-01-09, 2023-11-30, 2024-11-19).
- One likely false detection: 2023-11-10, a hazy, dark scene where the box sits on plain road.
- 2024-11-14 and 2024-11-19 show a second, brighter carriageway next to the old road. Some boxes sit where the dark and bright surfaces meet, which could be an edge effect. This road was built after the test period, so it does not affect 2019 to 2022, but it matters for any later use.
- Some vehicles are missed: one random road crop on 2023-01-09 shows coloured dots that were not flagged. A counter that misses a steady share of trucks can still track changes; one that misses them unevenly cannot. The test will show which.

**Decision: blue_shift 0.12, red_shift 0.15, max_gap 3 px are final.** No more changes before scoring.
