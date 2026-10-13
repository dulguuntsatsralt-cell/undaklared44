"""Baselines, rolling-origin evaluation and significance tests.

The rule everywhere: a forecast for month t may only use data from months
before t (plus satellite features for month t itself, which is the point of a
nowcast). No random splits.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats


# ---------- baselines (use only past exports) ----------

def naive_last(y_past: pd.Series) -> float:
    return float(y_past.iloc[-1])


def seasonal_naive(y_past: pd.Series) -> float:
    """Same month last year, scaled by the ratio of the last 3 months to a year earlier."""
    if len(y_past) < 15:
        return naive_last(y_past)
    last_year_same = y_past.iloc[-12]
    recent = y_past.iloc[-3:].mean()
    year_ago = y_past.iloc[-15:-12].mean()
    growth = recent / year_ago if year_ago > 0 else 1.0
    return float(last_year_same * growth)


# ---------- rolling-origin evaluation ----------

def rolling_origin(
    y: pd.Series,
    X: pd.DataFrame | None,
    make_model: Callable[[], object] | None,
    min_train: int = 24,
) -> pd.DataFrame:
    """Walk forward one month at a time.

    Returns a frame indexed by month with the actual value, the two baselines
    and (if a model is given) the model's nowcast.
    """
    y = y.sort_index()
    rows = []
    for i in range(min_train, len(y)):
        t = y.index[i]
        y_past = y.iloc[:i]
        row = {"month": t, "actual": float(y.iloc[i]),
               "naive_last": naive_last(y_past), "seasonal_naive": seasonal_naive(y_past)}
        if make_model is not None and X is not None:
            train_idx = y.index[:i]
            model = make_model()
            model.fit(X.loc[train_idx].to_numpy(), y_past.to_numpy())
            row["model"] = float(model.predict(X.loc[[t]].to_numpy())[0])
        rows.append(row)
    return pd.DataFrame(rows).set_index("month")


def mape(actual: np.ndarray, pred: np.ndarray) -> float:
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)


def rmse(actual: np.ndarray, pred: np.ndarray) -> float:
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    return float(np.sqrt(np.mean((actual - pred) ** 2)))


def bootstrap_ci(actual, pred, metric=mape, n_boot: int = 2000, seed: int = 0, alpha: float = 0.05):
    """Percentile bootstrap confidence interval for an error metric."""
    rng = np.random.default_rng(seed)
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    n = len(actual)
    vals = [metric(actual[idx], pred[idx]) for idx in (rng.integers(0, n, n) for _ in range(n_boot))]
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def diebold_mariano(actual, pred_a, pred_b, power: int = 2) -> tuple[float, float]:
    """Diebold-Mariano test for equal accuracy of two one-step forecasts.

    Negative statistic means forecast A has smaller loss. Returns (stat, two-sided p).
    Uses the Harvey, Leybourne and Newbold small-sample correction.
    """
    actual = np.asarray(actual, float)
    d = np.abs(actual - np.asarray(pred_a, float)) ** power - np.abs(actual - np.asarray(pred_b, float)) ** power
    n = len(d)
    var = np.var(d, ddof=1)
    if var == 0:
        return 0.0, 1.0
    dm = d.mean() / np.sqrt(var / n)
    dm *= np.sqrt((n - 1) / n)  # HLN correction for h = 1
    p = 2 * stats.t.sf(abs(dm), df=n - 1)
    return float(dm), float(p)


def summary(results: pd.DataFrame) -> pd.DataFrame:
    """MAPE, RMSE and 95% bootstrap CI for every forecast column."""
    rows = {}
    for col in results.columns.drop("actual"):
        lo, hi = bootstrap_ci(results["actual"], results[col])
        rows[col] = {"MAPE_%": mape(results["actual"], results[col]),
                     "MAPE_CI_low": lo, "MAPE_CI_high": hi,
                     "RMSE": rmse(results["actual"], results[col])}
    return pd.DataFrame(rows).T
