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


def _detrended_r(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation after removing a straight-line trend (in month order) from each series."""
    t = np.arange(len(a), dtype=float)
    ra = a - np.polyval(np.polyfit(t, a, 1), t)
    rb = b - np.polyval(np.polyfit(t, b, 1), t)
    return float(np.corrcoef(ra, rb)[0, 1])


def stockpile_test(signal: pd.Series, exports: pd.Series,
                   discovery=("2025-01", "2025-12"), test=("2026-01", "2026-09"),
                   min_r: float = 0.5, min_detrended: float = 0.3) -> dict:
    """The pre-registered stockpile test (results/2026-10-13_stockpile_preregistration.md).

    `signal` and `exports` are monthly series indexed by Period. The change
    form is this month minus last month, so it needs consecutive months.
    """
    full = signal.sort_index()
    full = full.reindex(pd.period_range(full.index.min(), full.index.max(), freq="M"))
    forms = {"level": full.dropna(), "change": full.diff().dropna()}   # a gap month gives no change value

    def window(s, lo, hi):
        j = pd.concat([s.rename("sig"), exports.rename("ex")], axis=1, join="inner").dropna()
        return j.loc[pd.Period(lo, "M"):pd.Period(hi, "M")]

    disc = {}
    for k, s in forms.items():
        w = window(s, *discovery)
        disc[k] = _detrended_r(w["sig"].to_numpy(float), w["ex"].to_numpy(float)) if len(w) >= 4 else float("nan")
    valid = {k: v for k, v in disc.items() if np.isfinite(v)}
    if not valid:
        raise ValueError("Not enough 2025 months to choose a form.")
    form = max(valid, key=lambda k: abs(valid[k]))
    sign = 1 if valid[form] >= 0 else -1

    w = window(forms[form], *test)
    if len(w) < 4:
        raise ValueError(f"Only {len(w)} test months with data; need at least 4.")
    x, y = w["sig"].to_numpy(float), w["ex"].to_numpy(float)
    r = float(np.corrcoef(x, y)[0, 1])
    rd = _detrended_r(x, y)
    passed = (np.sign(r) == sign and abs(r) >= min_r and np.sign(rd) == sign and abs(rd) >= min_detrended)
    return {"form": form, "sign": sign, "discovery": disc, "n_test": len(w),
            "r": r, "r_detrended": rd, "passed": bool(passed)}


def _within_year_residuals(s: pd.Series) -> pd.Series:
    """Remove a separate straight-line trend (in calendar months) from each year."""
    out = []
    for _, g in s.groupby(s.index.year):
        t = np.array([p.month for p in g.index], dtype=float)
        out.append(g - np.polyval(np.polyfit(t, g.to_numpy(float), 1), t))
    return pd.concat(out)


def fixed_rule_test(signal: pd.Series, exports: pd.Series, start: str, end: str, sign: int = -1,
                    min_detrended: float = 0.3, min_years: int = 2, min_months_per_year: int = 6) -> dict:
    """Score a rule whose form and sign were fixed in advance (stockpile test v2).

    Both series are monthly, indexed by Period. Months from `start` to `end`
    with data in both are used; years with fewer than `min_months_per_year`
    such months are dropped. Each series has its own straight-line trend
    removed within each year, so the multi-year growth in exports does not
    drive the result. Pass if the pooled within-year correlation has the
    fixed sign with size at least `min_detrended`, and the sign holds in at
    least `min_years` of the years.
    """
    j = pd.concat([signal.rename("sig"), exports.rename("ex")], axis=1, join="inner").dropna()
    j = j.loc[pd.Period(start, "M"):pd.Period(end, "M")]
    counts = j.groupby(j.index.year).size()
    years = [int(y) for y, n in counts.items() if n >= min_months_per_year]
    j = j[j.index.year.isin(years)]
    if len(years) < min_years:
        raise ValueError(f"Only {len(years)} years with at least {min_months_per_year} months; need {min_years}.")
    rs, re_ = _within_year_residuals(j["sig"]), _within_year_residuals(j["ex"])
    pooled = float(np.corrcoef(rs, re_)[0, 1])
    per_year = {y: float(np.corrcoef(rs[rs.index.year == y], re_[re_.index.year == y])[0, 1]) for y in years}
    raw = float(np.corrcoef(j["sig"], j["ex"])[0, 1])
    n_right = sum(1 for v in per_year.values() if np.sign(v) == sign)
    passed = np.sign(pooled) == sign and abs(pooled) >= min_detrended and n_right >= min_years
    return {"n": len(j), "years": years, "months_per_year": {y: int(counts[y]) for y in counts.index},
            "r_raw": raw, "r_within_year": pooled, "per_year": per_year,
            "years_with_sign": n_right, "passed": bool(passed)}


def summary(results: pd.DataFrame) -> pd.DataFrame:
    """MAPE, RMSE and 95% bootstrap CI for every forecast column."""
    rows = {}
    for col in results.columns.drop("actual"):
        lo, hi = bootstrap_ci(results["actual"], results[col])
        rows[col] = {"MAPE_%": mape(results["actual"], results[col]),
                     "MAPE_CI_low": lo, "MAPE_CI_high": hi,
                     "RMSE": rmse(results["actual"], results[col])}
    return pd.DataFrame(rows).T
