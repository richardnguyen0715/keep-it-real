"""
Preprocessing and Exploratory Data Analysis Module
----------------------------------------------------
Handles missing value imputation, outlier detection, frequency inference,
train/test splitting, and summary statistics for the time series.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Missing Values & Outliers
# ---------------------------------------------------------------------------

def handle_missing(series: pd.Series, method: str = "interpolate") -> pd.Series:
    """
    Fill missing values in a time series.

    Parameters
    ----------
    series : Input time series (may contain NaNs).
    method : 'interpolate' (linear), 'forward', 'backward', or 'drop'.

    Returns
    -------
    pd.Series with missing values handled.
    """
    n_missing = series.isna().sum()
    if n_missing == 0:
        print("[preprocessing] No missing values found.")
        return series

    print(f"[preprocessing] Found {n_missing} missing values — applying '{method}' strategy.")

    if method == "interpolate":
        return series.interpolate(method="time")
    elif method == "forward":
        return series.ffill()
    elif method == "backward":
        return series.bfill()
    elif method == "drop":
        return series.dropna()
    else:
        raise ValueError(f"Unknown method '{method}'. Use 'interpolate', 'forward', 'backward', or 'drop'.")


def detect_outliers_iqr(series: pd.Series, k: float = 3.0) -> pd.Series:
    """
    Flag outliers using the IQR fence method.

    Parameters
    ----------
    series : Time series.
    k      : Multiplier for IQR fence (default 3.0 for conservative detection).

    Returns
    -------
    Boolean pd.Series (True = outlier).
    """
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    mask = (series < lower) | (series > upper)
    n_outliers = mask.sum()
    if n_outliers:
        print(f"[preprocessing] Detected {n_outliers} outlier(s) (IQR k={k}).")
    else:
        print("[preprocessing] No outliers detected via IQR.")
    return mask


def cap_outliers(series: pd.Series, k: float = 3.0) -> pd.Series:
    """
    Cap outliers at the IQR fence boundaries (Winsorization).
    """
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return series.clip(lower=lower, upper=upper)


# ---------------------------------------------------------------------------
# Differencing helpers
# ---------------------------------------------------------------------------

def difference(series: pd.Series, lag: int = 1) -> pd.Series:
    """Apply lag differencing to remove a unit root or seasonality."""
    return series.diff(lag).dropna()


def inverse_difference(
    original: pd.Series,
    diff_series: pd.Series,
    lag: int = 1,
) -> pd.Series:
    """
    Reverse a single-order differencing operation.

    Parameters
    ----------
    original    : The undifferenced series (used to obtain the first value).
    diff_series : The differenced forecast values.
    lag         : Differencing lag used (default 1).

    Returns
    -------
    pd.Series with values on the original scale.
    """
    base = original.iloc[-lag]
    recovered = diff_series.copy()
    recovered.iloc[0] = base + diff_series.iloc[0]
    for i in range(1, len(recovered)):
        recovered.iloc[i] = recovered.iloc[i - 1] + diff_series.iloc[i]
    return recovered


# ---------------------------------------------------------------------------
# Train / Test Split
# ---------------------------------------------------------------------------

def train_test_split(
    series: pd.Series,
    test_size: float = 0.2,
) -> Tuple[pd.Series, pd.Series]:
    """
    Split a time series into train and test sets (no shuffling).

    Parameters
    ----------
    series    : Full time series.
    test_size : Fraction of data to use as test set.

    Returns
    -------
    (train, test) tuple of pd.Series.
    """
    cutoff = int(len(series) * (1 - test_size))
    train, test = series.iloc[:cutoff], series.iloc[cutoff:]
    print(
        f"[preprocessing] Train: {len(train)} obs "
        f"({train.index[0].date()} → {train.index[-1].date()}) | "
        f"Test: {len(test)} obs "
        f"({test.index[0].date()} → {test.index[-1].date()})"
    )
    return train, test


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def eda_summary(series: pd.Series) -> pd.DataFrame:
    """
    Compute descriptive statistics for the time series.

    Returns
    -------
    pd.DataFrame with stats as rows.
    """
    stats = {
        "n_observations": len(series),
        "start_date": str(series.index.min().date()),
        "end_date": str(series.index.max().date()),
        "mean": series.mean(),
        "std": series.std(),
        "min": series.min(),
        "25%": series.quantile(0.25),
        "50%": series.median(),
        "75%": series.quantile(0.75),
        "max": series.max(),
        "skewness": series.skew(),
        "kurtosis": series.kurt(),
        "n_missing": series.isna().sum(),
    }
    df = pd.DataFrame(list(stats.items()), columns=["statistic", "value"])
    return df


def infer_frequency(series: pd.Series) -> Optional[str]:
    """Attempt to infer the time series frequency string."""
    try:
        freq = pd.infer_freq(series.index)
        print(f"[preprocessing] Inferred frequency: {freq}")
        return freq
    except Exception:
        print("[preprocessing] Could not infer frequency.")
        return None
