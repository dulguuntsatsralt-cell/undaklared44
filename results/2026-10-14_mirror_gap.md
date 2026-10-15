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

## Result 3 (2026-10-15): the monthly data pins down when

Monthly figures (China: Comtrade, Mongolia: NSO), value China records as a share of Mongolia's:

| Period | Value gap (USD m) | China / Mongolia, value | China / Mongolia, tonnes |
|---|---|---|---|
| 2018 to 2020 | -63 | 99% | 100% |
| 2021 | -756 | 73% | 102% |
| Jan to Aug 2022 | -1,266 | 67% | 96% |
| Sep to Dec 2022 | -185 | 93% | 99% |
| 2023 to 2024 | -651 | 96% | 100% |

The gap opens in early 2021, is widest from February to August 2022 (China's figure 57% to 77% of Mongolia's in single months), and closes in September 2022. It does not come back.

**Timing does not explain it.** China's monthly price moves with Mongolia's in the same month (correlation 0.93 at no lag, falling to 0.81 at one month and 0.69 at two). China's price is simply lower, by about a fifth on average from mid-2020 to mid-2023, and it never catches up later.

## Result 4 (2026-10-15): it is specific to Mongolia

The same comparison for hard coal (HS 2701) from other suppliers, value China records as a share of the exporter's own record (`data/trade_comtrade_control.csv`):

| Year | Indonesia | Canada | Mongolia (own UN filing) |
|---|---|---|---|
| 2019 | 95% | 104% | 102% |
| 2020 | 118% | 125% | 100% |
| **2021** | **106%** | **104%** | **81%** |
| **2022** | **97%** | **119%** | **84%** |
| 2023 | 105% | 100% | 97% |
| 2024 | 102% | 110% | n/a |

China recorded Indonesian and Canadian coal at the same value as those countries did, or higher, as expected when one side includes freight. Only Mongolia's coal was recorded lower, and only in 2021-22. So this is not a general feature of how China valued coal imports in those years. Australia (Chinese import ban in 2021-22), Russia (stopped reporting in 2022) and the United States (estimated quantities) are not clean comparisons and are left out of the table, though their data is in the file.

Using Mongolia's own Comtrade filing for HS 2701 the gap is smaller (81% and 84%) than using the statistics office's revised totals (73% and 78%), so part of it sits inside Mongolia's own records.

## Timeline around the closing

- 9 September 2022: the Tavan Tolgoi to Gashuun Sukhait railway was completed ([Global Times](https://www.globaltimes.cn/page/202301/1283486.shtml)).
- September 2022: the gap closes.
- October 2022: the chief executive of Erdenes Tavan Tolgoi, the state coal company, was fired; he was later arrested over alleged off-the-books coal sales to Chinese buyers at the border ([Al Jazeera](https://www.aljazeera.com/economy/2023/1/25/after-anti-corruption-protests-mongolia-rethinks-coal-sales)).
- December 2022: protests in Ulaanbaatar.
- February 2023: state coal moves to auctions on the stock exchange instead of private contracts ([Al Jazeera](https://www.aljazeera.com/economy/2023/1/25/after-anti-corruption-protests-mongolia-rethinks-coal-sales)).

The gap closes about a month before the first visible action against the state coal company. That is suggestive, not proof: Mongolia's coal price was also falling fast from May to September 2022, and the gap shrinks as it falls.

## What could explain it (not yet tested)

1. **Under-valuation at Chinese import, specific to Mongolian coal.** Buyers of Mongolian coal declared a lower price than the one Mongolia recorded. Result 4 shows China did not do this for Indonesian or Canadian coal in the same years, so if this is the cause, it is about how Mongolian coal was sold, not about Chinese customs in general.
2. **Mongolian valuation rules.** If Mongolian customs valued coal at a reference or benchmark price rather than the contract price, Mongolia's figure would run high when prices spike. 2011 and 2021-22 were both price booms, which fits. If this is the cause, the gap is the distance between the benchmark and the price coal was actually sold at, and the question becomes why state coal sold so far below the benchmark in exactly the years of the alleged theft. **Not yet confirmed whether Mongolian customs used reference prices in 2021-22; this needs Mongolian-language sources.**
3. **Timing.** Ruled out by the monthly data (Result 3): no lag, and the gap never reverses.
4. **Revisions.** Mongolia's statistics office figure for 2021 ($2.77bn) is higher than Mongolia's own Comtrade filing ($2.49bn), so part of the gap is inside Mongolia's own records.

Explanations 1 and 2 both point to coal being sold, or at least declared, far below the price Mongolia recorded, in the period of the alleged theft, and only for Mongolian coal. They differ on which record is the odd one. Settling it needs Mongolia's customs valuation rules for 2021-22 and, ideally, the 6-digit split between coking coal and other coal.

## Limits

- Monthly data: China's side is complete for 2017 to 2024; Mongolia's own Comtrade filing stops at 2021, so the statistics office series is used for Mongolia.
- Coal codes: both sides use HS 2701, 2702 and 2704 here. Small amounts under other codes are not counted.
- A gap in records is not proof of wrongdoing. It is where to look.
