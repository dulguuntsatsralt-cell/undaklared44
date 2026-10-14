import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge

from coalcast.evaluate import (bootstrap_ci, diebold_mariano, mape, naive_last,
                               rolling_origin, seasonal_naive, summary)


def _synthetic(n=96, seed=0):
    """Exports driven partly by a satellite signal, plus seasonality and noise."""
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2018-01", periods=n, freq="M")
    signal = rng.normal(0, 1, n)
    season = np.sin(2 * np.pi * idx.month / 12)
    y = pd.Series(6 + 1.0 * signal + 0.5 * season + rng.normal(0, 0.2, n), index=idx)
    X = pd.DataFrame({"queue": signal, "season": season}, index=idx)
    return y, X


def test_baselines():
    y = pd.Series(np.arange(1, 25, dtype=float))
    assert naive_last(y) == 24.0
    assert seasonal_naive(y.iloc[:5]) == 5.0          # too short: falls back to naive
    flat = pd.Series(np.full(24, 3.0))
    assert seasonal_naive(flat) == pytest.approx(3.0)


def test_rolling_origin_never_sees_the_future():
    y, X = _synthetic()
    seen = []

    class Spy(Ridge):
        def fit(self, Xtr, ytr):
            seen.append(len(ytr))
            return super().fit(Xtr, ytr)

    res = rolling_origin(y, X, lambda: Spy(alpha=1.0), min_train=24)
    assert len(res) == len(y) - 24
    assert seen == list(range(24, len(y)))            # train size grows by one each step
    assert res.index[0] == y.index[24]


def test_model_with_real_signal_beats_baselines():
    y, X = _synthetic()
    res = rolling_origin(y, X, lambda: Ridge(alpha=1.0), min_train=24)
    s = summary(res)
    assert s.loc["model", "MAPE_%"] < s.loc["naive_last", "MAPE_%"]
    assert s.loc["model", "MAPE_%"] < s.loc["seasonal_naive", "MAPE_%"]
    stat, p = diebold_mariano(res["actual"], res["model"], res["naive_last"])
    assert stat < 0 and p < 0.01


def test_metrics_and_ci():
    a = np.array([10.0, 20.0])
    assert mape(a, np.array([11.0, 18.0])) == pytest.approx(10.0)
    lo, hi = bootstrap_ci(np.full(30, 10.0), np.full(30, 11.0))
    assert lo == pytest.approx(10.0) and hi == pytest.approx(10.0)


def test_dm_identical_forecasts():
    a = np.arange(10.0)
    assert diebold_mariano(a, a + 1, a + 1) == (0.0, 1.0)


def test_stockpile_test_picks_form_on_2025_and_scores_2026():
    from coalcast.evaluate import stockpile_test
    idx = pd.period_range("2025-01", "2026-09", freq="M")
    rng = np.random.default_rng(1)
    ex = pd.Series(8 + np.sin(np.arange(len(idx))) * 2 + np.arange(len(idx)) * 0.1, index=idx)
    good = pd.Series(0.2 + 0.03 * (ex.values - 8) + rng.normal(0, 0.003, len(idx)), index=idx)
    res = stockpile_test(good, ex)
    assert res["form"] == "level" and res["sign"] == 1 and res["passed"]
    noise = pd.Series(rng.normal(0.2, 0.05, len(idx)), index=idx)
    assert not stockpile_test(noise, ex)["passed"]                # unrelated signal fails
    gappy = good.drop([pd.Period("2026-03", "M")])            # a gap removes one change value, not the test
    assert stockpile_test(gappy, ex)["n_test"] == 8
