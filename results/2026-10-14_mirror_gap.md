# Mirror gap: both sides' records of the Mongolia-China coal trade (2026-10-14)

**Files:** `mirror_gap_annual.csv` (built by `scripts/mirror_gap.py` from `data/trade_nso_coal.csv` and `data/trade_comtrade_coal.csv`), chart `assets/mirror-gap-light.png` / `-dark.png`.

**Question:** If coal leaves Mongolia without being declared, China's customs should record more coal arriving than Mongolia's customs records leaving. Do the two records agree?

**Data:**
- Mongolia: National Statistics Office, coal exports, volume and value, every month since 2011. Nearly all of it goes to China.
- China: China's own customs filing to UN Comtrade, imports from Mongolia, HS 2701 (hard coal), 2702 (lignite) and 2704 (coke), yearly since 2010.
- Mongolia's own Comtrade filing (2013 to 2023) is kept as a cross-check.

## Result 1: the tonnes match

In the 13 years where China reported its tonnage, China's figure is between 95% and 106% of Mongolia's, with a median of 99.3%. From 2017 on it is within 2.5% every year. Over 2017 to 2025 (leaving out 2023), China records about 2 Mt less than Mongolia, not more.

China's tonnage for 2016 and 2023 is a UN estimate, not a reported number, and is left out. In both years the estimate is about half of Mongolia's figure while the dollar values agree, so the estimate is the problem, not the trade.

**At the level of national customs records, there is no sign of coal crossing undeclared.** If the coal theft case involved coal that never appeared in customs records, it was not large enough to show in yearly totals, or it was declared at the border under other names or companies. That second case would not show up in this comparison at all.

## Result 2: the dollars do not, in two periods

| Year | Mongolia records (USD m) | China records (USD m) | China / Mongolia |
|---|---|---|---|
| 2011 | 2,273 | 1,615 | 71% |
| 2012 | 1,902 | 1,713 | 90% |
| 2013 to 2020 | | | 94% to 112% |
| **2021** | **2,774** | **2,018** | **73%** |
| **2022** | **6,503** | **5,051** | **78%** |
| 2023 to 2025 | | | 96% to 97% |

In 2021 and 2022 China recorded the same tonnes of Mongolian coal as worth **$2.2 billion less** than Mongolia did ($1.4 billion using Mongolia's own Comtrade filing, which is lower than the statistics office's revised figures). In 2011 the gap was $0.7 billion.

This runs the opposite way from normal. China records imports including freight and insurance (CIF); Mongolia records exports without them (FOB). China's figure should be slightly higher, not 22 to 29% lower.

## What could explain it (not yet tested)

1. **Under-valuation at Chinese import.** Importers declare a lower price to pay less import VAT. This is the textbook reading of a mirror gap in this direction.
2. **Mongolian valuation rules.** If Mongolian customs valued coal at a reference or benchmark price rather than the contract price, Mongolia's figure would run high when prices spike. 2011 and 2021-22 were both price booms, which fits this reading as well.
3. **Timing.** Prices rose fast in 2021-22; if one side values at contract signing and the other at crossing, a gap opens during a rally. This should mostly cancel over two years, and here it does not.
4. **Revisions.** Mongolia's statistics office figure for 2021 ($2.77bn) is higher than Mongolia's own Comtrade filing ($2.49bn), so part of the gap is inside Mongolia's own records.

The gap closing after 2022 lines up with the investigations that followed the coal theft case and with coal sales moving onto the Mongolian Mining Exchange from around 2023 (exact dates to confirm). It also lines up with falling prices. Telling these apart needs the monthly data and the price series, and is the next step.

## Limits

- Yearly totals hide timing. The monthly series (from 2017) is only partly downloaded; the UN preview service limits calls per hour. `scripts/fetch_trade.py` resumes it.
- Coal codes: both sides use HS 2701, 2702 and 2704 here. Small amounts under other codes are not counted.
- A gap in records is not proof of wrongdoing. It is where to look.
