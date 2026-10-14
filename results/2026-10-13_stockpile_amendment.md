# Amendment to the stockpile pre-registration (2026-10-13)

Written on 2026-10-13, before the stockpile test was scored.

## What went wrong

The first signal run gave `yard_coal_frac` = 0 in every month (one month at 0.0012). The coal rule could not fire: Sentinel-2 L2A scenes processed with baseline 04.00 or later (every scene since January 2022) store values as reflectance x 10000 + 1000. The code compared raw values with 800, but in raw units 8% reflectance is 1800. On the clearest scenes the lowest 1% of pixels in the whole area were around 1300 to 1500 raw, so nothing was ever below 800.

## Change

Coal is now: all four bands below 800 **after subtracting the 1000 offset**, which is the 8% reflectance rule as written in the pre-registration. The rule itself is unchanged; only the unit conversion was fixed. Raw value 0 still means no data.

## What was seen before this change

- The monthly table from the broken run, which was all zeros and says nothing about how the measure relates to exports.
- The yard band values (5th, 50th and 95th percentiles) on four clear scenes, used to confirm the offset.

The monthly coal fraction after the fix has not been compared with exports. Thresholds, masks, the usable rule, the candidate forms and the pass criteria are as pre-registered.
