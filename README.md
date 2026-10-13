# coalcast: nowcasting Mongolia's coal exports from satellite data

Mongolia's Customs General Administration publishes monthly coal export figures about 10 days after each month ends. This project estimates that number earlier, from free satellite imagery of border crossings, mines and rail yards, and measures how accurate and how early the estimate is.

**Status:** starter code. Feature extraction, baselines and evaluation are tested. The imagery download needs to run on your own machine.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest            # 11 tests should pass
```

## First steps

1. **Check the areas of interest.** Coordinates in `src/coalcast/aois.py` are approximate.
   ```bash
   python scripts/preview_aoi.py gashuunsukhait
   ```
   Open `data/preview_gashuunsukhait.png`. You should see the border facility and the approach road with truck traffic. Adjust the box if not. Repeat for each AOI.

2. **Fill in the target data.** Add one row per month to `data/exports_monthly.csv`, from 2017 onward, with the source link for every number. Two rows are there as examples.

3. **Build the first radar signal.**
   ```bash
   python scripts/build_s1_signal.py gashuunsukhait 2017-01 2026-09
   ```
   This writes one bright-pixel value per radar image. Start small (one year) to check it runs, then do the full range.

4. **Plot the signal against monthly exports.** If the monthly mean tracks exports, draw a road mask (a thin polygon along the approach road) and re-run with it. That usually cleans the signal a lot.

## Layout

```
src/coalcast/
  aois.py       areas of interest (verify before use)
  fetch.py      Sentinel-1 and Sentinel-2 download via Microsoft Planetary Computer
  features.py   bright-pixel (trucks, wagons) and dark-pixel (coal) signals, monthly features, nowcast vintages
  evaluate.py   baselines, rolling-origin evaluation, bootstrap CIs, Diebold-Mariano test
scripts/        preview_aoi.py, build_s1_signal.py
tests/          unit tests, including a check that evaluation never uses future data
data/           exports_monthly.csv (target), generated signals
```

## Evaluation rules

- Rolling-origin only: the forecast for month t is trained on months before t.
- Report MAPE and RMSE against naive and seasonal baselines, with bootstrap confidence intervals.
- Use the Diebold-Mariano test before claiming the model beats a baseline.
- Produce nowcasts as of day 10, day 20 and month end (`monthly_features(..., as_of_day=10)`).

## Known risks

- Clouds: use Sentinel-1 radar for the main signal.
- 10 m resolution: measures queue density, not individual trucks.
- About 100 months of data: keep models simple and report uncertainty.
- Regime changes: COVID border closures (2020 to 2022) and the Gashuunsukhait to Gantsmod cross-border railway, which will move coal from trucks to rail.
