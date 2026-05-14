"""
Stationarity Testing Module
-----------------------------
Implements the Augmented Dickey-Fuller (ADF) test, the KPSS test,
and a helper that recommends the differencing order (d) for ARIMA.
"""

import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# ADF Test
# ---------------------------------------------------------------------------

def adf_test(series: pd.Series, alpha: float = 0.05) -> Dict:
    """
    Augmented Dickey-Fuller test for unit root.

    H0 : Series has a unit root (non-stationary).
    H1 : Series is stationary.

    Parameters
    ----------
    series : Time series (no NaNs).
    alpha  : Significance level.

    Returns
    -------
    dict with test statistic, p-value, critical values, and conclusion.
    """
    result = adfuller(series.dropna(), autolag="AIC")
    stat, p_value, n_lags, n_obs = result[0], result[1], result[2], result[3]
    critical_values = result[4]

    is_stationary = p_value < alpha
    conclusion = "Stationary" if is_stationary else "Non-stationary (unit root)"

    output = {
        "test": "ADF",
        "test_statistic": round(stat, 6),
        "p_value": round(p_value, 6),
        "n_lags_used": n_lags,
        "n_observations": n_obs,
        "critical_values": {k: round(v, 4) for k, v in critical_values.items()},
        "alpha": alpha,
        "is_stationary": is_stationary,
        "conclusion": conclusion,
    }

    print(f"\n--- ADF Test ---")
    print(f"  Test Statistic : {stat:.4f}")
    print(f"  p-value        : {p_value:.4f}")
    for cv_level, cv_val in critical_values.items():
        print(f"  Critical Value ({cv_level}): {cv_val:.4f}")
    print(f"  => {conclusion} (alpha={alpha})")

    return output


# ---------------------------------------------------------------------------
# KPSS Test
# ---------------------------------------------------------------------------

def kpss_test(series: pd.Series, regression: str = "c", alpha: float = 0.05) -> Dict:
    """
    KPSS test for stationarity.

    H0 : Series is stationary.
    H1 : Series has a unit root (non-stationary).

    Parameters
    ----------
    series     : Time series (no NaNs).
    regression : 'c' for level stationarity, 'ct' for trend stationarity.
    alpha      : Significance level.

    Returns
    -------
    dict with test statistic, p-value, critical values, and conclusion.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = kpss(series.dropna(), regression=regression, nlags="auto")

    stat, p_value, n_lags = result[0], result[1], result[2]
    critical_values = result[3]

    # KPSS p-value is bounded; statsmodels returns 0.01 or 0.1 at extremes
    is_stationary = p_value >= alpha
    conclusion = "Stationary" if is_stationary else "Non-stationary (reject H0)"

    output = {
        "test": "KPSS",
        "regression": regression,
        "test_statistic": round(stat, 6),
        "p_value": round(p_value, 6),
        "n_lags_used": n_lags,
        "critical_values": {k: round(v, 4) for k, v in critical_values.items()},
        "alpha": alpha,
        "is_stationary": is_stationary,
        "conclusion": conclusion,
    }

    print(f"\n--- KPSS Test ---")
    print(f"  Test Statistic : {stat:.4f}")
    print(f"  p-value        : {p_value:.4f}")
    for cv_level, cv_val in critical_values.items():
        print(f"  Critical Value ({cv_level}): {cv_val:.4f}")
    print(f"  => {conclusion} (alpha={alpha})")

    return output


# ---------------------------------------------------------------------------
# Recommend differencing order
# ---------------------------------------------------------------------------

def recommend_differencing(
    series: pd.Series,
    max_d: int = 3,
    alpha: float = 0.05,
) -> Tuple[int, pd.Series]:
    """
    Sequentially apply differencing until the ADF test declares stationarity,
    capped at max_d.

    Returns
    -------
    (d, stationary_series) tuple.
    """
    print("\n=== Differencing Order Selection ===")
    current = series.copy()
    for d in range(max_d + 1):
        result = adfuller(current.dropna(), autolag="AIC")
        p_value = result[1]
        print(f"  d={d}: ADF p-value = {p_value:.4f}", end="")
        if p_value < alpha:
            print(f"  => STATIONARY at d={d}")
            return d, current.dropna()
        else:
            print(f"  => non-stationary, differencing ...")
            current = current.diff().dropna()

    print(f"  => Could not achieve stationarity within max_d={max_d}. Using d={max_d}.")
    return max_d, current.dropna()


# ---------------------------------------------------------------------------
# Combined stationarity report
# ---------------------------------------------------------------------------

def stationarity_report(series: pd.Series, alpha: float = 0.05) -> pd.DataFrame:
    """
    Run both ADF and KPSS tests and return a combined summary DataFrame.
    """
    adf = adf_test(series, alpha=alpha)
    kpss_c = kpss_test(series, regression="c", alpha=alpha)

    rows = [
        {
            "Test": "ADF",
            "Statistic": adf["test_statistic"],
            "p-value": adf["p_value"],
            "Stationary?": adf["is_stationary"],
            "Conclusion": adf["conclusion"],
        },
        {
            "Test": "KPSS (level)",
            "Statistic": kpss_c["test_statistic"],
            "p-value": kpss_c["p_value"],
            "Stationary?": kpss_c["is_stationary"],
            "Conclusion": kpss_c["conclusion"],
        },
    ]

    df = pd.DataFrame(rows)

    # Interpret combined results
    both_agree_stationary = adf["is_stationary"] and kpss_c["is_stationary"]
    both_agree_nonstationary = (not adf["is_stationary"]) and (not kpss_c["is_stationary"])

    if both_agree_stationary:
        verdict = "Series is STATIONARY (both ADF and KPSS agree)."
    elif both_agree_nonstationary:
        verdict = "Series is NON-STATIONARY (both ADF and KPSS agree) — differencing recommended."
    else:
        # Mixed signals: ADF says stationary, KPSS says non-stationary => trend-stationary
        verdict = "Mixed signals — series may be TREND-STATIONARY. Consider detrending."

    print(f"\n[stationarity_report] Verdict: {verdict}")
    return df
