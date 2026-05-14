"""
Forecasting and Evaluation Module
------------------------------------
Produces out-of-sample forecasts and computes evaluation metrics.

Metrics implemented:
  - MAE   — Mean Absolute Error
  - RMSE  — Root Mean Squared Error
  - MAPE  — Mean Absolute Percentage Error
  - SMAPE — Symmetric MAPE
  - MASE  — Mean Absolute Scaled Error
  - R²    — Coefficient of determination
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------

def forecast(
    fit,
    steps: int,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Generate out-of-sample point forecasts with confidence intervals.

    Parameters
    ----------
    fit   : Fitted ARIMAResultsWrapper from statsmodels.
    steps : Number of future periods to forecast.
    alpha : Significance level for confidence intervals (default 0.05 → 95% CI).

    Returns
    -------
    pd.DataFrame with columns: ['forecast', 'lower_ci', 'upper_ci'].
    """
    pred = fit.get_forecast(steps=steps)
    mean = pred.predicted_mean
    ci = pred.conf_int(alpha=alpha)

    df = pd.DataFrame(
        {
            "forecast": mean.values,
            "lower_ci": ci.iloc[:, 0].values,
            "upper_ci": ci.iloc[:, 1].values,
        },
        index=mean.index,
    )

    print(f"[forecast] Generated {steps}-step forecast (CI alpha={alpha}).")
    return df


def rolling_forecast(
    train: pd.Series,
    test: pd.Series,
    order: Tuple[int, int, int],
    refit_every: int = 1,
) -> pd.DataFrame:
    """
    Walk-forward (rolling origin) evaluation on the test set.

    At each step we fit on all available history and predict 1 step ahead.
    Optionally refit the model every `refit_every` steps to save compute.

    Parameters
    ----------
    train        : Training series.
    test         : Test series (ground truth).
    order        : ARIMA (p, d, q) order.
    refit_every  : How often to refit the model (1 = every step).

    Returns
    -------
    pd.DataFrame with columns: ['actual', 'forecast'].
    """
    from statsmodels.tsa.arima.model import ARIMA
    import warnings
    warnings.filterwarnings("ignore")

    history = list(train.values)
    predictions = []
    print(f"[rolling_forecast] Running walk-forward over {len(test)} test steps ...")

    fit = None
    for i, (ts, actual) in enumerate(zip(test.index, test.values)):
        if fit is None or i % refit_every == 0:
            model = ARIMA(history, order=order)
            fit = model.fit()
        pred = fit.forecast(steps=1)[0]
        predictions.append(pred)
        history.append(actual)

    result = pd.DataFrame({"actual": test.values, "forecast": predictions}, index=test.index)
    return result


# ---------------------------------------------------------------------------
# Evaluation Metrics
# ---------------------------------------------------------------------------

def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mape(actual: np.ndarray, predicted: np.ndarray, eps: float = 1e-8) -> float:
    """Mean Absolute Percentage Error (%)."""
    return float(np.mean(np.abs((actual - predicted) / (np.abs(actual) + eps))) * 100)


def smape(actual: np.ndarray, predicted: np.ndarray, eps: float = 1e-8) -> float:
    """Symmetric MAPE (%)."""
    denom = (np.abs(actual) + np.abs(predicted)) / 2 + eps
    return float(np.mean(np.abs(actual - predicted) / denom) * 100)


def mase(
    actual: np.ndarray,
    predicted: np.ndarray,
    train: np.ndarray,
    seasonal_period: int = 1,
) -> float:
    """
    Mean Absolute Scaled Error.

    Scales MAE by the in-sample naive seasonal forecast error.
    """
    naive_errors = np.abs(np.diff(train, n=seasonal_period))
    scale = np.mean(naive_errors) if len(naive_errors) > 0 else 1.0
    if scale == 0:
        return float("nan")
    return float(np.mean(np.abs(actual - predicted)) / scale)


def r_squared(actual: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot != 0 else float("nan")


def evaluate(
    actual: pd.Series,
    predicted: pd.Series,
    train: Optional[pd.Series] = None,
    seasonal_period: int = 1,
) -> pd.DataFrame:
    """
    Compute all evaluation metrics in one call.

    Parameters
    ----------
    actual          : Actual (test) values.
    predicted       : Forecast values aligned to the same index.
    train           : Training series (required for MASE).
    seasonal_period : Seasonal period for MASE naïve baseline.

    Returns
    -------
    pd.DataFrame with metric name and value columns.
    """
    a = actual.values.astype(float)
    p = predicted.values.astype(float)

    metrics = {
        "MAE": mae(a, p),
        "RMSE": rmse(a, p),
        "MAPE (%)": mape(a, p),
        "SMAPE (%)": smape(a, p),
        "R²": r_squared(a, p),
    }

    if train is not None:
        metrics["MASE"] = mase(a, p, train.values.astype(float), seasonal_period)

    df = pd.DataFrame(
        [{"metric": k, "value": round(v, 4)} for k, v in metrics.items()]
    )

    print("\n--- Evaluation Metrics ---")
    for _, row in df.iterrows():
        print(f"  {row['metric']:<12}: {row['value']}")

    return df


# ---------------------------------------------------------------------------
# Confidence-interval coverage
# ---------------------------------------------------------------------------

def coverage(actual: pd.Series, forecast_df: pd.DataFrame) -> float:
    """
    Compute the empirical coverage of the confidence intervals.

    Parameters
    ----------
    actual      : Actual test values.
    forecast_df : DataFrame with 'lower_ci' and 'upper_ci' columns.

    Returns
    -------
    Coverage fraction (should be close to 1 - alpha).
    """
    aligned = actual.reindex(forecast_df.index)
    inside = (
        (aligned.values >= forecast_df["lower_ci"].values)
        & (aligned.values <= forecast_df["upper_ci"].values)
    )
    cov = inside.mean()
    print(f"[evaluation] CI coverage: {cov:.1%}")
    return float(cov)
