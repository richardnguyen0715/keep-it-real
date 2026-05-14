"""
Preprocessing & Stationarity Testing for SARIMA Forecasting Pipeline.

Steps covered
-------------
1. Log / Box-Cox transformation (variance stabilisation)
2. Differencing (regular + seasonal)
3. ADF & KPSS stationarity tests
4. ACF / PACF lag summary
5. Seasonality detection helper
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.statespace.tools import diff
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# Dataclasses for structured results
# ---------------------------------------------------------------------------

@dataclass
class StationarityResult:
    test: str
    statistic: float
    p_value: float
    critical_values: dict[str, float]
    is_stationary: bool
    conclusion: str


@dataclass
class PreprocessingReport:
    original_length: int
    transformation: str
    lambda_boxcox: float | None
    d: int                          # regular differencing order
    D: int                          # seasonal differencing order
    seasonal_period: int
    stationarity_tests: list[StationarityResult] = field(default_factory=list)
    durbin_watson: float | None = None
    acf_lags: list[float] = field(default_factory=list)
    pacf_lags: list[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transformation
# ---------------------------------------------------------------------------

def apply_log_transform(series: pd.Series) -> pd.Series:
    """Natural log transform. Requires strictly positive values."""
    if (series <= 0).any():
        raise ValueError("Log transform requires strictly positive values.")
    return np.log(series)


def apply_boxcox(series: pd.Series) -> tuple[pd.Series, float]:
    """
    Box-Cox transform with automatic lambda selection.

    Returns
    -------
    (transformed_series, lambda_value)
    """
    if (series <= 0).any():
        raise ValueError("Box-Cox transform requires strictly positive values.")
    transformed, lam = stats.boxcox(series.values)
    return pd.Series(transformed, index=series.index, name=series.name), float(lam)


def inverse_boxcox(series: pd.Series, lam: float) -> pd.Series:
    """Invert a Box-Cox transformation."""
    if abs(lam) < 1e-8:
        return np.exp(series)
    return pd.Series(
        np.power(series.values * lam + 1, 1.0 / lam),
        index=series.index,
        name=series.name,
    )


# ---------------------------------------------------------------------------
# Differencing helpers
# ---------------------------------------------------------------------------

def difference(
    series: pd.Series,
    d: int = 1,
    D: int = 0,
    s: int = 12,
) -> pd.Series:
    """
    Apply regular (d) and/or seasonal (D) differencing.

    Parameters
    ----------
    d : Regular differencing order.
    D : Seasonal differencing order.
    s : Seasonal period.
    """
    arr = series.values.astype(float)
    if d > 0:
        arr = diff(arr, k_diff=d)
    if D > 0:
        arr = diff(arr, k_seasonal_diff=D, seasonal_periods=s)
    # Trim index to match differenced length
    return pd.Series(arr, index=series.index[-len(arr) :], name=series.name)


# ---------------------------------------------------------------------------
# Stationarity tests
# ---------------------------------------------------------------------------

def adf_test(series: pd.Series, alpha: float = 0.05) -> StationarityResult:
    """
    Augmented Dickey-Fuller test.
    H0: unit root (non-stationary)  →  reject H0 → stationary
    """
    result = adfuller(series.dropna(), autolag="AIC")
    stat, pval, _, _, crit, _ = result
    is_stat = pval < alpha
    return StationarityResult(
        test="ADF",
        statistic=float(stat),
        p_value=float(pval),
        critical_values={k: float(v) for k, v in crit.items()},
        is_stationary=is_stat,
        conclusion="Stationary" if is_stat else "Non-stationary (unit root)",
    )


def kpss_test(
    series: pd.Series,
    alpha: float = 0.05,
    regression: Literal["c", "ct"] = "c",
) -> StationarityResult:
    """
    KPSS test.
    H0: stationary  →  fail to reject H0 → stationary
    """
    stat, pval, _, crit = kpss(series.dropna(), regression=regression, nlags="auto")
    is_stat = pval >= alpha
    return StationarityResult(
        test="KPSS",
        statistic=float(stat),
        p_value=float(pval),
        critical_values={k: float(v) for k, v in crit.items()},
        is_stationary=is_stat,
        conclusion="Stationary" if is_stat else "Non-stationary (level/trend shift)",
    )


# ---------------------------------------------------------------------------
# Order selection helpers
# ---------------------------------------------------------------------------

def suggest_differencing_order(
    series: pd.Series,
    max_d: int = 2,
    alpha: float = 0.05,
) -> int:
    """
    Incrementally difference until ADF indicates stationarity.
    Returns the minimum differencing order d.
    """
    s = series.copy()
    for d in range(max_d + 1):
        res = adf_test(s, alpha=alpha)
        if res.is_stationary:
            return d
        s = s.diff().dropna()
    return max_d


def suggest_seasonal_differencing_order(
    series: pd.Series,
    seasonal_period: int = 12,
    max_D: int = 1,
    alpha: float = 0.05,
) -> int:
    """
    Suggest seasonal differencing order D based on ADF after seasonal diff.
    """
    s = series.copy()
    for D in range(max_D + 1):
        res = adf_test(s.dropna(), alpha=alpha)
        if res.is_stationary:
            return D
        s = s.diff(seasonal_period).dropna()
    return max_D


# ---------------------------------------------------------------------------
# ACF / PACF helpers
# ---------------------------------------------------------------------------

def compute_acf_pacf(
    series: pd.Series,
    nlags: int = 40,
    alpha: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ACF and PACF with confidence bounds.

    Returns
    -------
    (acf_values, acf_confint, pacf_values, pacf_confint)
    """
    acf_vals, acf_ci = acf(series.dropna(), nlags=nlags, alpha=alpha, fft=True)
    pacf_vals, pacf_ci = pacf(series.dropna(), nlags=nlags, alpha=alpha)
    return acf_vals, acf_ci, pacf_vals, pacf_ci


def significant_lags(values: np.ndarray, confint: np.ndarray) -> list[int]:
    """Return lag indices where the value lies outside the confidence interval."""
    sig = []
    for i, (v, ci) in enumerate(zip(values[1:], confint[1:]), start=1):
        lo, hi = ci[0] - v, ci[1] - v  # CI is centered; shift back
        if v < lo or v > hi:
            sig.append(i)
    return sig


# ---------------------------------------------------------------------------
# High-level preprocessing pipeline
# ---------------------------------------------------------------------------

def preprocess(
    series: pd.Series,
    seasonal_period: int = 12,
    transformation: Literal["none", "log", "boxcox"] = "log",
    auto_diff: bool = True,
    d: int | None = None,
    D: int | None = None,
    alpha: float = 0.05,
) -> tuple[pd.Series, PreprocessingReport]:
    """
    Full preprocessing pipeline.

    Parameters
    ----------
    series          : Raw time series.
    seasonal_period : Periodicity (m).
    transformation  : Variance-stabilising transform.
    auto_diff       : Automatically detect d and D if True.
    d               : Override regular differencing order.
    D               : Override seasonal differencing order.
    alpha           : Significance level for stationarity tests.

    Returns
    -------
    (processed_series, PreprocessingReport)
    """
    report = PreprocessingReport(
        original_length=len(series),
        transformation=transformation,
        lambda_boxcox=None,
        d=0,
        D=0,
        seasonal_period=seasonal_period,
    )

    # ── 1. Transform ──────────────────────────────────────────────────────
    transformed = series.copy()
    if transformation == "log":
        transformed = apply_log_transform(series)
    elif transformation == "boxcox":
        transformed, lam = apply_boxcox(series)
        report.lambda_boxcox = lam

    # ── 2. Differencing orders ────────────────────────────────────────────
    if auto_diff:
        _D = suggest_seasonal_differencing_order(
            transformed, seasonal_period=seasonal_period, alpha=alpha
        )
        _d = suggest_differencing_order(transformed, alpha=alpha)
    else:
        _d = d if d is not None else 0
        _D = D if D is not None else 0

    report.d = _d
    report.D = _D

    # ── 3. Apply differencing ─────────────────────────────────────────────
    processed = difference(transformed, d=_d, D=_D, s=seasonal_period).dropna()

    # ── 4. Stationarity tests on processed series ─────────────────────────
    report.stationarity_tests.append(adf_test(processed, alpha=alpha))
    report.stationarity_tests.append(kpss_test(processed, alpha=alpha))

    # ── 5. Durbin-Watson ──────────────────────────────────────────────────
    report.durbin_watson = float(durbin_watson(processed.values))

    # ── 6. ACF / PACF ─────────────────────────────────────────────────────
    nlags = min(40, len(processed) // 2 - 1)
    acf_v, acf_ci, pacf_v, pacf_ci = compute_acf_pacf(processed, nlags=nlags)
    report.acf_lags = significant_lags(acf_v, acf_ci)
    report.pacf_lags = significant_lags(pacf_v, pacf_ci)

    return processed, report


def print_report(report: PreprocessingReport) -> None:
    """Pretty-print a PreprocessingReport."""
    print("=" * 60)
    print("  PREPROCESSING REPORT")
    print("=" * 60)
    print(f"  Original length    : {report.original_length}")
    print(f"  Transformation     : {report.transformation}", end="")
    if report.lambda_boxcox is not None:
        print(f"  (λ = {report.lambda_boxcox:.4f})", end="")
    print()
    print(f"  Seasonal period    : {report.seasonal_period}")
    print(f"  Differencing order : d={report.d}, D={report.D}")
    print()
    for t in report.stationarity_tests:
        print(f"  [{t.test}]  stat={t.statistic:.4f}  p={t.p_value:.4f}  → {t.conclusion}")
    print()
    if report.durbin_watson is not None:
        print(f"  Durbin-Watson      : {report.durbin_watson:.4f}")
    print(f"  Significant ACF lags  : {report.acf_lags[:10]}")
    print(f"  Significant PACF lags : {report.pacf_lags[:10]}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from data_generator import generate_synthetic_series

    s = generate_synthetic_series()
    processed, rpt = preprocess(s, seasonal_period=12, transformation="log")
    print_report(rpt)
    print(f"\nProcessed series length: {len(processed)}")
