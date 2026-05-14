"""
Data Generator & Loader for SARIMA Forecasting Pipeline.

Supports:
  - Synthetic seasonal time series generation
  - Loading from CSV / external sources
"""

import numpy as np
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Synthetic data
# ---------------------------------------------------------------------------

def generate_synthetic_series(
    n_periods: int = 240,
    seasonal_period: int = 12,
    trend_slope: float = 0.05,
    seasonal_amplitude: float = 10.0,
    noise_std: float = 2.0,
    ar_params: list[float] | None = None,
    ma_params: list[float] | None = None,
    seed: int = 42,
    freq: str = "MS",
    start: str = "2004-01-01",
) -> pd.Series:
    """
    Generate a synthetic time series that mimics monthly data with:
      - A linear trend
      - Seasonal (sinusoidal) component
      - Optional AR / MA noise
      - Gaussian noise

    Parameters
    ----------
    n_periods        : Number of time steps.
    seasonal_period  : Periodicity (e.g. 12 for monthly/yearly seasonality).
    trend_slope      : Slope of the linear trend per period.
    seasonal_amplitude: Amplitude of the seasonal sine wave.
    noise_std        : Std-dev of additive Gaussian noise.
    ar_params        : AR coefficients for the noise process (optional).
    ma_params        : MA coefficients for the noise process (optional).
    seed             : Random seed for reproducibility.
    freq             : Pandas date frequency string.
    start            : Start date for the index.

    Returns
    -------
    pd.Series  with a DatetimeIndex.
    """
    rng = np.random.default_rng(seed)

    # --- Base components ---
    t = np.arange(n_periods)
    trend = trend_slope * t
    seasonal = seasonal_amplitude * np.sin(2 * np.pi * t / seasonal_period)

    # --- Noise (simple ARMA if params provided) ---
    white_noise = rng.normal(0, noise_std, n_periods)
    noise = _apply_arma(white_noise, ar_params or [], ma_params or [])

    values = 100.0 + trend + seasonal + noise  # base level = 100

    index = pd.date_range(start=start, periods=n_periods, freq=freq)
    return pd.Series(values, index=index, name="value")


def _apply_arma(
    innovations: np.ndarray,
    ar: list[float],
    ma: list[float],
) -> np.ndarray:
    """Apply ARMA filtering to innovations."""
    n = len(innovations)
    out = np.zeros(n)
    p, q = len(ar), len(ma)
    for i in range(n):
        ar_part = sum(ar[j] * out[i - j - 1] for j in range(min(p, i)))
        ma_part = sum(ma[j] * innovations[i - j - 1] for j in range(min(q, i)))
        out[i] = innovations[i] + ar_part + ma_part
    return out


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_series_from_csv(
    filepath: str | Path,
    date_col: str = "date",
    value_col: str = "value",
    freq: str | None = None,
    fill_method: str = "ffill",
) -> pd.Series:
    """
    Load a univariate time series from a CSV file.

    Parameters
    ----------
    filepath    : Path to the CSV.
    date_col    : Column name containing dates.
    value_col   : Column name containing the target variable.
    freq        : Optional pandas frequency to enforce on the index.
    fill_method : How to handle missing values ('ffill', 'bfill', 'interpolate').

    Returns
    -------
    pd.Series with a DatetimeIndex.
    """
    df = pd.read_csv(filepath, parse_dates=[date_col], index_col=date_col)
    if value_col not in df.columns:
        raise ValueError(
            f"Column '{value_col}' not found. Available: {df.columns.tolist()}"
        )
    series = df[value_col].sort_index()

    if freq:
        series = series.asfreq(freq)

    # Handle NaNs
    if fill_method == "interpolate":
        series = series.interpolate(method="time")
    elif fill_method in ("ffill", "bfill"):
        series = series.fillna(method=fill_method)  # type: ignore[arg-type]

    return series


# ---------------------------------------------------------------------------
# Train / test split
# ---------------------------------------------------------------------------

def train_test_split(
    series: pd.Series,
    test_size: int | float = 0.2,
) -> tuple[pd.Series, pd.Series]:
    """
    Split a time series into train and test sets.

    Parameters
    ----------
    series    : Full time series.
    test_size : If int, number of test observations.
                If float (0 < x < 1), fraction of total length.

    Returns
    -------
    (train, test) tuple of pd.Series.
    """
    n = len(series)
    if isinstance(test_size, float):
        n_test = int(np.ceil(n * test_size))
    else:
        n_test = test_size

    if n_test >= n:
        raise ValueError(
            f"test_size ({n_test}) must be smaller than series length ({n})."
        )

    train = series.iloc[: n - n_test]
    test = series.iloc[n - n_test :]
    return train, test


# ---------------------------------------------------------------------------
# Quick-save helper
# ---------------------------------------------------------------------------

def save_series(series: pd.Series, path: str | Path) -> None:
    """Persist a series to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    series.to_csv(path, header=True)


if __name__ == "__main__":
    # Smoke test
    s = generate_synthetic_series()
    print(f"Generated series: {len(s)} obs  |  {s.index[0]} -> {s.index[-1]}")
    print(s.head())
