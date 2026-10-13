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
