# Results log

Each experiment follows the same rule: fix the measure on one period, then test it once on months it has not seen. Failed tests stay in this log.

## 2026-10-13: Road radar signal at Gashuunsukhait

**File:** `2026-10-13_road_signal_test.xlsx`

**Question:** Does radar brightness on the truck road at the Gashuunsukhait crossing track Mongolia's monthly coal exports?

**Rule (fixed before testing):** `road_p90_db` from Sentinel-1 orbit 164, monthly average. This is the brightest 10% of the road area minus a nearby desert control area, so rain and season cancel.

| Period | Months | Correlation with exports | After removing shared trend |
|---|---|---|---|
| 2025 (where the rule was found) | 8 | +0.80 | +0.67 |
| **2026 test (rule unchanged)** | **9** | **+0.11** | **+0.09** |
| 2026, Sentinel-1C scenes only | 9 | +0.21 | +0.23 |

**Result: failed.** The 2025 result was mostly luck from trying 12 combinations (4 measures, 3 orbits) on 8 months.

**Why:** a truck queue measures congestion, not volume. When the border runs smoothly, trucks pass quickly and the queue stays short even at high volume. When it jams, the queue grows while exports fall (September 2026). The measured area is also one yard at one of several crossings, and a growing share of coal moves by rail.

**Data issues found:**
- Sentinel-1D joined orbit 164 in May 2026. Its 29 May scene is implausible (about 43 dB above the desert, roughly 3x any other scene) and is flagged in the workbook.
- Before 2025, only orbit 84 covers the crossing (Sentinel-1C started in 2025), so orbit 164 has no earlier history.

**Earlier attempts (same session, not separately tested):** whole-area bright pixels and change-from-normal pixels both tracked only the shared upward trend; after removing it the correlation was negative.

**Next:** coal stockpile area at the border yards from Sentinel-2, tested the same way.

## 2026-10-13: Coal stockpile area at Gashuunsukhait (Sentinel-2)

**Files:** `2026-10-13_stockpile_preregistration.md` (rule, written before any data), `2026-10-13_stockpile_amendment.md` (unit fix before scoring).

**Question:** Does the share of the border coal yard covered by coal track Mongolia's monthly coal exports?

**Rule (fixed before testing):** share of clear yard pixels darker than 8% reflectance in four bands, monthly mean of scenes with at least 80% of the yard clear. Level or month-to-month change, whichever correlates better with exports in 2025 after removing the trend; scored once on 2026. Pass needs the 2025 sign with |r| of at least 0.5 and |detrended r| of at least 0.3.

| Period | Months | Correlation with exports | After removing shared trend |
|---|---|---|---|
| 2025 (form chosen: level, sign +) | 12 | not used | +0.42 (change: +0.21) |
| **2026 test (rule unchanged)** | **9** | **-0.40** | **-0.69** |

Every month had at least 3 usable scenes (3 to 12).

**Result: failed.** The 2026 correlation has the opposite sign to 2025.

**Changes before scoring, both logged:**
- The first run returned zero coal in every month because Sentinel-2 values carry a +1000 offset that the code did not remove. Fixed to match the written 8% rule; see the amendment.
- The yard outline was redrawn twice after checking it on a true-colour scene (to leave out roofs and cover the whole storage ground). This happened before the monthly coal fraction was compared with exports. A dark striped area north of the crossing was left out because it was not confirmed as coal storage.

**Reading:** the pre-registration listed this risk: coal in a yard is a stock, not a flow. A full yard can mean coal is piling up because it is not crossing, which would push the sign negative, as in 2026. That is a guess drawn from the failed test, not a finding. Testing it would need a new rule (negative sign) fixed now and scored on data not yet seen: months from October 2026 onward, or 2022 to 2024 if export figures for those years are added.

**Next:** decide whether to pre-register the negative-sign stockpile rule on new months, or move to rail (wagon counts at the Gashuunsukhait rail terminal).

## 2026-10-14: Stockpile test v2 (backlog sign, 2022 to 2024)

**Files:** `2026-10-14_stockpile_v2_preregistration.md` (rule, written before any 2022 to 2024 imagery was downloaded), `2026-10-14_yard_start.md` and `2026-10-14_yard_timeline.png` (yard start month, fixed from images alone).

**Question:** The first stockpile test flipped sign between 2025 and 2026. Is the 2026 reading right: does a fuller yard mean lower exports, on three years nobody had looked at?

**Rule (fixed before testing):** same measure and same yard as the first test; level form, negative sign; official NSO coal exports; each series detrended within each year; pass needs a pooled within-year correlation of -0.30 or lower and a negative sign in at least 2 of 3 years.

| | Months | Within-year detrended r |
|---|---|---|
| 2022 | 12 | +0.04 |
| 2023 | 12 | +0.13 |
| 2024 | 12 | -0.22 |
| **Pooled** | **36** | **-0.05** |

Raw correlation (not part of the rule): -0.15.

**Result: failed.** Over 36 unseen months the yard coal fraction has essentially no relation to monthly exports, in either direction.

**Reading:** together with the first test, this says the coal visible in this one yard does not track national exports month to month. The 2025 and 2026 correlations (+0.42, -0.69 after detrending) were most likely noise on short samples, which is what the pre-registration was meant to catch.

**Next:** the satellite measures are closed for now. The project moves to comparing both countries' customs records (see `2026-10-14_mirror_gap.md`).


## 2026-10-14: Mirror gap, Mongolia vs China customs records

**File:** `2026-10-14_mirror_gap.md` (full write-up), `mirror_gap_annual.csv`.

Not a pre-registered test; a first descriptive comparison. Tonnes match: China's record is 95% to 106% of Mongolia's in every year with reported figures, within about 2% since 2017. Values do not: in 2021 and 2022 China valued the same coal at 73% and 78% of Mongolia's figure, $2.2 billion lower in total (2011: $0.7 billion). Four explanations are listed there, each with the data that would separate it from the others. Monthly data is still downloading.

## 2026-10-17: Border congestion vs the price gap (Sentinel-1, 2019 to 2024)

**Files:** `2026-10-15_congestion_gap_preregistration.md` (rule, written before any 2019 to 2024 radar was downloaded), `congestion_gap_monthly.csv`.

**Question:** Is the gap between China's and Mongolia's recorded coal price larger in months when the radar shows a more jammed border?

**Rule (fixed before testing):** `road_p90_db`, orbit 84, monthly mean, against log(China price / Mongolia price); pass needs r of -0.30 or lower over all months and within January 2021 to August 2022.

| Period | Months | r | Spearman |
|---|---|---|---|
| 2019 to 2024 | 61 | **+0.57** | +0.68 |
| Jan 2021 to Aug 2022 | 18 | **+0.26** | +0.26 |

**Result: failed, and in the opposite direction.** The price gap was largest when the road was least bright, not most.

**Why (looked at after scoring):** yearly averages of road brightness: 2019 21.4 dB, 2020 18.0, 2021 16.4, 2022 16.3, 2023 17.9, 2024 20.4. Brightness was lowest in 2021-22, the years of border closures and the lowest exports (15 to 21 Mt a year). So at this crossing the radar mostly shows how many trucks are present, and during closures there were fewer, not more. This was listed as a risk in advance ("a closed border could look less congested than a slow one"). The measure cannot tell a closed border from a quiet one, so it cannot test the scarcity idea.

**What it does show (descriptive, not a test):** the price gap opened in exactly the period when the radar shows the crossing at its emptiest in six years. That is independent, physical confirmation that 2021-22 was a period of choked border trade, which is the setting the scarcity reading needs, but it does not show that scarcity caused the gap.
