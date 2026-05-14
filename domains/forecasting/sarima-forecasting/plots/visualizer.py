"""
Visualisation Module for SARIMA Forecasting Pipeline.

Plots
-----
1. Raw series overview
2. Decomposition (trend / seasonal / residual)
3. ACF & PACF correlograms
4. Stationarity: original vs differenced
5. Forecast plot with prediction intervals
6. Residual diagnostics (4-panel)
7. Rolling evaluation error heatmap
8. Metric comparison bar chart
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAXResultsWrapper


# ---------------------------------------------------------------------------
# Style defaults
# ---------------------------------------------------------------------------

PALETTE = {
    "actual": "#2C7BB6",
    "forecast": "#D7191C",
    "train": "#1A9641",
    "ci": "#FDAE61",
    "residual": "#7B2D8B",
    "neutral": "#636363",
}

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.size": 10,
    }
)


def _save_or_show(fig: plt.Figure, path: str | Path | None) -> None:
    if path is not None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, bbox_inches="tight")
        print(f"  Plot saved → {p}")
    else:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Series overview
# ---------------------------------------------------------------------------

def plot_series(
    series: pd.Series,
    title: str = "Time Series Overview",
    save_path: str | Path | None = None,
) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=False)

    # Raw values
    axes[0].plot(series.index, series.values, color=PALETTE["actual"], linewidth=1.2)
    axes[0].set_title(title)
    axes[0].set_ylabel("Value")

    # Rolling mean / std
    rm = series.rolling(12, center=True).mean()
    rs = series.rolling(12, center=True).std()
    axes[1].plot(series.index, series.values, color=PALETTE["neutral"], alpha=0.5, linewidth=0.8)
    axes[1].plot(rm.index, rm.values, color=PALETTE["train"], label="12-period rolling mean")
    axes[1].fill_between(rs.index, rm - 2 * rs, rm + 2 * rs, alpha=0.2, color=PALETTE["train"])
    axes[1].legend(fontsize=8)
    axes[1].set_ylabel("Rolling stats")

    # Histogram
    axes[2].hist(series.dropna().values, bins=30, color=PALETTE["actual"], edgecolor="white", alpha=0.8)
    axes[2].set_ylabel("Frequency")
    axes[2].set_xlabel("Value")

    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 2. Seasonal decomposition
# ---------------------------------------------------------------------------

def plot_decomposition(
    series: pd.Series,
    seasonal_period: int = 12,
    model: str = "additive",
    save_path: str | Path | None = None,
) -> None:
    decomp = seasonal_decompose(series.dropna(), model=model, period=seasonal_period)

    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    components = [
        ("Observed", decomp.observed),
        ("Trend", decomp.trend),
        ("Seasonal", decomp.seasonal),
        ("Residual", decomp.resid),
    ]
    colors = [PALETTE["actual"], PALETTE["train"], PALETTE["ci"], PALETTE["residual"]]

    for ax, (label, data), color in zip(axes, components, colors):
        ax.plot(data.index, data.values, color=color, linewidth=1.0)
        ax.set_ylabel(label)

    axes[0].set_title(f"Seasonal Decomposition  ({model}, m={seasonal_period})")
    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 3. ACF & PACF
# ---------------------------------------------------------------------------

def plot_acf_pacf(
    series: pd.Series,
    lags: int = 40,
    title: str = "ACF / PACF",
    save_path: str | Path | None = None,
) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6))
    plot_acf(series.dropna(), lags=lags, ax=ax1, color=PALETTE["actual"])
    plot_pacf(series.dropna(), lags=lags, ax=ax2, color=PALETTE["forecast"], method="ywm")
    ax1.set_title(f"{title} — ACF")
    ax2.set_title(f"{title} — PACF")
    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 4. Stationarity: original vs differenced
# ---------------------------------------------------------------------------

def plot_stationarity_check(
    original: pd.Series,
    differenced: pd.Series,
    d: int,
    D: int,
    seasonal_period: int = 12,
    save_path: str | Path | None = None,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=False)

    axes[0].plot(original.index, original.values, color=PALETTE["actual"], linewidth=1)
    axes[0].set_title("Original Series")
    axes[0].set_ylabel("Value")

    axes[1].plot(differenced.index, differenced.values, color=PALETTE["train"], linewidth=1)
    axes[1].axhline(0, color="grey", linestyle="--", linewidth=0.8)
    axes[1].set_title(
        f"After Differencing  (d={d}, D={D}, s={seasonal_period})"
    )
    axes[1].set_ylabel("Differenced Value")

    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 5. Forecast plot
# ---------------------------------------------------------------------------

def plot_forecast(
    train: pd.Series,
    test: pd.Series,
    forecast_result,            # ForecastResult
    title: str = "SARIMA Forecast",
    n_train_show: int = 60,
    save_path: str | Path | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))

    train_plot = train.iloc[-n_train_show:]
    ax.plot(
        train_plot.index, train_plot.values,
        color=PALETTE["train"], linewidth=1.5, label="Train"
    )
    ax.plot(
        test.index, test.values,
        color=PALETTE["actual"], linewidth=1.5, label="Actual (Test)"
    )
    ax.plot(
        forecast_result.forecast.index, forecast_result.forecast.values,
        color=PALETTE["forecast"], linewidth=1.5, linestyle="--", label="Forecast"
    )
    ax.fill_between(
        forecast_result.lower.index,
        forecast_result.lower.values,
        forecast_result.upper.values,
        color=PALETTE["ci"],
        alpha=0.35,
        label=f"{forecast_result.confidence_level}% PI",
    )
    ax.axvline(test.index[0], color="grey", linestyle=":", linewidth=1)
    ax.set_title(title)
    ax.set_ylabel("Value")
    ax.legend(fontsize=9)
    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 6. Residual diagnostics (4-panel)
# ---------------------------------------------------------------------------

def plot_residual_diagnostics(
    result: SARIMAXResultsWrapper,
    save_path: str | Path | None = None,
) -> None:
    from scipy import stats as sp_stats

    resid = result.resid.dropna()

    fig = plt.figure(figsize=(14, 8))
    gs = gridspec.GridSpec(2, 2, figure=fig)

    # Panel 1: Residual time plot
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(resid.index, resid.values, color=PALETTE["residual"], linewidth=0.8)
    ax1.axhline(0, color="grey", linestyle="--")
    ax1.set_title("Residuals over Time")
    ax1.set_ylabel("Residual")

    # Panel 2: ACF of residuals
    ax2 = fig.add_subplot(gs[0, 1])
    plot_acf(resid, lags=min(40, len(resid) // 2 - 1), ax=ax2, color=PALETTE["residual"])
    ax2.set_title("ACF of Residuals")

    # Panel 3: Histogram + KDE
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.hist(resid.values, bins=25, density=True, color=PALETTE["residual"],
             edgecolor="white", alpha=0.7)
    x_range = np.linspace(resid.min(), resid.max(), 200)
    ax3.plot(x_range, sp_stats.norm.pdf(x_range, resid.mean(), resid.std()),
             color="black", linewidth=1.5, label="N(μ,σ)")
    ax3.set_title("Residual Distribution")
    ax3.legend(fontsize=8)

    # Panel 4: Q-Q plot
    ax4 = fig.add_subplot(gs[1, 1])
    sp_stats.probplot(resid.values, plot=ax4)
    ax4.set_title("Q-Q Plot")

    fig.suptitle("Residual Diagnostics", fontsize=13, y=1.01)
    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 7. Rolling evaluation error
# ---------------------------------------------------------------------------

def plot_rolling_errors(
    rolling_df: pd.DataFrame,      # RollingEvalResult.forecasts
    save_path: str | Path | None = None,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(14, 6))

    errors = rolling_df["actual"] - rolling_df["forecast"]

    axes[0].plot(rolling_df.index, rolling_df["actual"], label="Actual",
                 color=PALETTE["actual"], linewidth=1.2)
    axes[0].plot(rolling_df.index, rolling_df["forecast"], label="Forecast",
                 color=PALETTE["forecast"], linewidth=1.2, linestyle="--")
    axes[0].fill_between(rolling_df.index, rolling_df["lower"], rolling_df["upper"],
                         alpha=0.25, color=PALETTE["ci"], label="PI")
    axes[0].set_title("Walk-Forward Forecast vs Actual")
    axes[0].legend(fontsize=8)

    axes[1].bar(rolling_df.index, errors.values,
                color=[PALETTE["forecast"] if e < 0 else PALETTE["train"] for e in errors],
                width=20, alpha=0.7)
    axes[1].axhline(0, color="grey", linestyle="--")
    axes[1].set_title("Forecast Error  (actual − forecast)")
    axes[1].set_ylabel("Error")

    fig.tight_layout()
    _save_or_show(fig, save_path)


# ---------------------------------------------------------------------------
# 8. Metrics comparison bar chart
# ---------------------------------------------------------------------------

def plot_metrics_comparison(
    metrics_dict: dict[str, "EvaluationMetrics"],
    metric_names: list[str] | None = None,
    save_path: str | Path | None = None,
) -> None:
    """
    Compare multiple model evaluations side by side.

    Parameters
    ----------
    metrics_dict  : {model_label: EvaluationMetrics}
    metric_names  : Which metrics to plot (default: mae, rmse, smape).
    """
    if metric_names is None:
        metric_names = ["mae", "rmse", "smape"]

    labels = list(metrics_dict.keys())
    x = np.arange(len(metric_names))
    width = 0.8 / len(labels)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (label, m) in enumerate(metrics_dict.items()):
        vals = [getattr(m, mn) or 0 for mn in metric_names]
        ax.bar(x + i * width, vals, width, label=label, alpha=0.85)

    ax.set_xticks(x + width * (len(labels) - 1) / 2)
    ax.set_xticklabels([n.upper() for n in metric_names])
    ax.set_title("Model Metrics Comparison")
    ax.legend(fontsize=9)
    fig.tight_layout()
    _save_or_show(fig, save_path)
