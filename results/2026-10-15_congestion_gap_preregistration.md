# Pre-registration: border congestion and the price gap (2026-10-15)

Written on 2026-10-15, before any Sentinel-1 radar data for 2019 to 2024 was downloaded or looked at. This file is not edited after the first results; changes go in a new, dated file.

## Why

The mirror comparison (`2026-10-14_mirror_gap.md`) found that from January 2021 to August 2022, China recorded Mongolian coal at a price about a fifth to a third lower than Mongolia did, while the tonnes matched. This happened only for Mongolian coal.

The first radar test (2026-10-13) found that brightness on the truck road at Gashuun Sukhait measures **congestion**, not volume: a jammed border has a long queue whatever the volume. In 2021-22 the border was repeatedly closed or slowed by COVID controls. When coal cannot cross, whoever gets it across can buy cheaply on the Mongolian side and sell dear in China, and the price recorded by each side can come apart.

**Question:** in months when the radar shows a more jammed border, is the gap between the two sides' prices larger?

This uses the radar for what the first test showed it measures. The price gap has already been seen; the radar data for these years has not. The radar measure is the one from the first test, unchanged, so it cannot have been tuned to the gap.

## Data

- **Congestion:** Sentinel-1 radar (VV), relative orbit **84** only, the one orbit that covers the crossing for the whole period. Same 10 m grid, same hand-drawn `road` and `control` polygons (`data/masks_gashuunsukhait.geojson`, as committed in f38ce78). Measure: `road_p90_db`, the brightest 10% of the road area minus the median of the control desert, averaged over all orbit 84 scenes in the month. Sentinel-1B stopped in December 2021, so later months have fewer scenes; every month with at least one scene is used.
- **Price gap:** `log(China price per tonne / Mongolia price per tonne)` for the month. China: Comtrade imports from Mongolia, HS 2701 + 2702 + 2704, value / net weight. Mongolia: NSO coal exports, value / volume. Using price per tonne, not total value, removes the effect of coal crossing in one month and being recorded in the next. Months where either side records less than 0.5 Mt are left out, because the price is unreliable on small amounts.
- **Period:** January 2019 to December 2024 (China's monthly series ends there).

## Test (once)

Two correlations (Pearson), congestion against the price gap. A more negative price gap means China's price is further below Mongolia's, so the expected sign is **negative**.

1. **All months**, 2019 to 2024.
2. **Within the gap period**, January 2021 to August 2022 only. This checks that any relation is not just "both were unusual in 2021-22": within the episode, worse months should still have bigger gaps.

**Pass** if both correlations are -0.30 or lower. If only the first passes, it is reported as "consistent but driven by one episode", not as a pass. Anything else is a fail, reported with the numbers. A rank correlation (Spearman) is reported alongside but is not part of the rule.

## Known limits, stated in advance

- The road mask covers a few kilometres on the Mongolian side. In the worst months the queue ran far beyond it, so the measure can saturate: a full road looks the same whether the queue is 5 or 50 km.
- When the border was fully closed, trucks may have stopped coming, so a closed border could look less congested than a slow one.
- Correlation is not cause. A pass shows that the price gap moved with border congestion, which fits the scarcity reading, not that congestion caused it or who gained from it.
