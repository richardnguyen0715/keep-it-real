"""
Data Generation and Loading Module
-----------------------------------
Generates synthetic time series data or loads real CSV data
for use in the ARIMA forecasting pipeline.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional


def generate_arima_series(
    n: int = 365,
    ar_params: list = [0.6, -0.2],
    ma_params: list = [0.4],
    d: int = 1,
    noise_std: float = 1.0,
    trend: float = 0.05,
    seasonality: bool = True,
    seasonal_period: int = 12,
    seasonal_amplitude: float = 5.0,
    seed: int = 42,
) -> pd.Series:
    """
    Generate a synthetic ARIMA(p,d,q) time series with optional trend
    and seasonal components.

    Parameters
    ----------
    n               : Number of observations.
    ar_params       : AR coefficients (phi).
    ma_params       : MA coefficients (theta).
    d               : Integration order (differencing).
    noise_std       : Standard deviation of white noise.
    trend           : Linear trend slope per time step.
    seasonality     : Whether to add a sinusoidal seasonal component.
    seasonal_period : Period of the seasonal cycle.
    seasonal_amplitude : Amplitude of the seasonal cycle.
    seed            : Random seed for reproducibility.

    Returns
    -------
    pd.Series with a DatetimeIndex (monthly frequency).
    """
    rng = np.random.default_rng(seed)

    p = len(ar_params)
    q = len(ma_params)
    burn = 100  # burn-in samples to remove initialization effects
    total = n + burn

    noise = rng.normal(0, noise_std, total)
    series = np.zeros(total)
    errors = np.zeros(total)

    for t in range(max(p, q), total):
        ar_term = sum(ar_params[i] * series[t - i - 1] for i in range(p))
        ma_term = sum(ma_params[i] * errors[t - i - 1] for i in range(q))
        errors[t] = noise[t]
        series[t] = ar_term + ma_term + noise[t]

    # Drop burn-in
    series = series[burn:]

    # Apply integration (cumulative sum)
    for _ in range(d):
        series = np.cumsum(series)

    # Add deterministic components
    t_index = np.arange(n)
    series += trend * t_index

    if seasonality:
        seasonal = seasonal_amplitude * np.sin(
            2 * np.pi * t_index / seasonal_period
        )
        series += seasonal

    # Shift to positive range
    series -= series.min() - 10.0

    dates = pd.date_range(start="2018-01-01", periods=n, freq="ME")
    return pd.Series(series, index=dates, name="value")


def load_csv(filepath: str, date_col: str = "date", value_col: str = "value") -> pd.Series:
    """
    Load a time series from a CSV file.

    Parameters
    ----------
    filepath  : Path to CSV file.
    date_col  : Name of the date column.
    value_col : Name of the value column.

    Returns
    -------
    pd.Series with a DatetimeIndex.
    """
    df = pd.read_csv(filepath, parse_dates=[date_col], index_col=date_col)
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found. Available: {list(df.columns)}")
    series = df[value_col].sort_index()
    series.name = "value"
    return series


def save_series(series: pd.Series, output_dir: str = "data", filename: str = "timeseries.csv") -> Path:
    """Save a pd.Series to CSV."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    fp = path / filename
    series.to_csv(fp, header=True)
    print(f"[data_generator] Saved series to {fp}")
    return fp


def get_dataset(
    source: str = "synthetic",
    filepath: Optional[str] = None,
    **kwargs,
) -> pd.Series:
    """
    Unified entry point to obtain a time series dataset.

    Parameters
    ----------
    source   : 'synthetic' to generate data, 'csv' to load from file.
    filepath : Required when source='csv'.
    **kwargs : Passed to generate_arima_series() when source='synthetic'.

    Returns
    -------
    pd.Series
    """
    if source == "synthetic":
        series = generate_arima_series(**kwargs)
        print(f"[data_generator] Generated synthetic series with {len(series)} observations.")
    elif source == "csv":
        if filepath is None:
            raise ValueError("filepath must be provided when source='csv'.")
        series = load_csv(filepath)
        print(f"[data_generator] Loaded series from {filepath} ({len(series)} observations).")
    else:
        raise ValueError(f"Unknown source '{source}'. Use 'synthetic' or 'csv'.")
    return series
