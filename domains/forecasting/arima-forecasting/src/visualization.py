"""
Visualization Module
----------------------
All plotting functions for the ARIMA forecasting pipeline.
Each function saves the figure to disk and optionally shows it.

Plots generated:
  1. Raw time series
  2. Decomposition (trend / seasonal / residual)
  3. ACF and PACF
  4. Stationarity comparison (original vs differenced)
  5. Forecast with confidence intervals
  6. Walk-forward (rolling) forecast vs actual
  7. Residual diagnostics (4-panel)
  8. Metric bar chart
"""

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from typing import Optional

matplotlib.use("Agg")  # headless / non-interactive backend

PLOT_DIR = Path("outputs/plots")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

STYLE = "seaborn-v0_8-darkgrid"


def _save(fig, name: str, output_dir: Path = PLOT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fp = output_dir / f"{name}.png"
    fig.savefig(fp, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved → {fp}")
    return fp


# ---------------------------------------------------------------------------
# 1. Raw time series
# ---------------------------------------------------------------------------

def plot_series(
    series: pd.Series,
    title: str = "Time Series",
    train: Optional[pd.Series] = None,
    test: Optional[pd.Series] = None,
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Plot a time series, optionally highlighting train/test split."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(14, 4))

        if train is not None and test is not None:
            ax.plot(train.index, train.values, label="Train", color="#2196F3", linewidth=1.5)
            ax.plot(test.index, test.values, label="Test", color="#FF5722", linewidth=1.5)
            ax.axvline(test.index[0], color="gray", linestyle="--", linewidth=1, label="Split")
        else:
            ax.plot(series.index, series.values, color="#2196F3", linewidth=1.5)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend()
        fig.tight_layout()
    return _save(fig, "01_raw_series", output_dir)


# ---------------------------------------------------------------------------
# 2. Seasonal decomposition
# ---------------------------------------------------------------------------

def plot_decomposition(
    series: pd.Series,
    period: int = 12,
    model: str = "additive",
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Decompose and plot trend, seasonal, and residual components."""
    decomp = seasonal_decompose(series.dropna(), model=model, period=period, extrapolate_trend="freq")

    with plt.style.context(STYLE):
        fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
        components = {
            "Observed": decomp.observed,
            "Trend": decomp.trend,
            "Seasonal": decomp.seasonal,
            "Residual": decomp.resid,
        }
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
        for ax, (name, comp), color in zip(axes, components.items(), colors):
            ax.plot(comp.index, comp.values, color=color, linewidth=1.2)
            ax.set_ylabel(name, fontsize=11)
            ax.tick_params(labelsize=9)

        axes[0].set_title(f"Seasonal Decomposition ({model.capitalize()}, period={period})",
                          fontsize=13, fontweight="bold")
        axes[-1].set_xlabel("Date")
        fig.tight_layout()
    return _save(fig, "02_decomposition", output_dir)


# ---------------------------------------------------------------------------
# 3. ACF and PACF
# ---------------------------------------------------------------------------

def plot_acf_pacf(
    series: pd.Series,
    nlags: int = 40,
    title_prefix: str = "",
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Side-by-side ACF and PACF plots."""
    with plt.style.context(STYLE):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))
        plot_acf(series.dropna(), lags=nlags, ax=ax1, color="#2196F3", alpha=0.05)
        plot_pacf(series.dropna(), lags=nlags, ax=ax2, color="#FF5722", alpha=0.05, method="ywm")
        ax1.set_title(f"{title_prefix} ACF", fontsize=12, fontweight="bold")
        ax2.set_title(f"{title_prefix} PACF", fontsize=12, fontweight="bold")
        fig.tight_layout()
    return _save(fig, "03_acf_pacf", output_dir)


# ---------------------------------------------------------------------------
# 4. Stationarity comparison
# ---------------------------------------------------------------------------

def plot_stationarity_comparison(
    original: pd.Series,
    differenced: pd.Series,
    d: int = 1,
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Plot original series alongside its differenced counterpart."""
    with plt.style.context(STYLE):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=False)
        ax1.plot(original.index, original.values, color="#2196F3", linewidth=1.2)
        ax1.set_title("Original Series", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Value")

        ax2.plot(differenced.index, differenced.values, color="#4CAF50", linewidth=1.2)
        ax2.set_title(f"After {d}-order Differencing", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Δ Value")
        ax2.set_xlabel("Date")
        fig.tight_layout()
    return _save(fig, "04_stationarity_comparison", output_dir)


# ---------------------------------------------------------------------------
# 5. Forecast with confidence intervals
# ---------------------------------------------------------------------------

def plot_forecast(
    train: pd.Series,
    test: pd.Series,
    forecast_df: pd.DataFrame,
    title: str = "ARIMA Forecast",
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Plot training history, actual test values, and forecast with CI."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(14, 5))

        # Show last portion of train for context
        n_context = min(len(train), 60)
        ax.plot(train.index[-n_context:], train.values[-n_context:],
                color="#2196F3", linewidth=1.5, label="Train (context)")
        ax.plot(test.index, test.values,
                color="#FF5722", linewidth=1.5, label="Actual (test)")
        ax.plot(forecast_df.index, forecast_df["forecast"],
                color="#4CAF50", linewidth=2.0, linestyle="--", label="Forecast")
        ax.fill_between(
            forecast_df.index,
            forecast_df["lower_ci"],
            forecast_df["upper_ci"],
            alpha=0.2,
            color="#4CAF50",
            label="95% CI",
        )

        ax.axvline(test.index[0], color="gray", linestyle=":", linewidth=1)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend(loc="upper left")
        fig.tight_layout()
    return _save(fig, "05_forecast", output_dir)


# ---------------------------------------------------------------------------
# 6. Rolling forecast vs actual
# ---------------------------------------------------------------------------

def plot_rolling_forecast(
    rolling_df: pd.DataFrame,
    title: str = "Walk-Forward Forecast",
    output_dir: Path = PLOT_DIR,
) -> Path:
    """Plot walk-forward (rolling) forecast against actual values."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(rolling_df.index, rolling_df["actual"],
                color="#FF5722", linewidth=1.5, label="Actual")
        ax.plot(rolling_df.index, rolling_df["forecast"],
                color="#4CAF50", linewidth=1.5, linestyle="--", label="Rolling Forecast")

        errors = rolling_df["actual"] - rolling_df["forecast"]
        ax.fill_between(rolling_df.index,
                        rolling_df["actual"],
                        rolling_df["forecast"],
                        where=(errors >= 0), alpha=0.1, color="#4CAF50", label="Over-forecast")
        ax.fill_between(rolling_df.index,
                        rolling_df["actual"],
                        rolling_df["forecast"],
                        where=(errors < 0), alpha=0.1, color="#FF5722", label="Under-forecast")

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend(loc="upper left")
        fig.tight_layout()
    return _save(fig, "06_rolling_forecast", output_dir)


# ---------------------------------------------------------------------------
# 7. Residual diagnostics (4-panel)
# ---------------------------------------------------------------------------

def plot_residual_diagnostics(fit, output_dir: Path = PLOT_DIR) -> Path:
    """
    4-panel residual diagnostic plot:
      - Residuals over time
      - Histogram with KDE
      - ACF of residuals
      - Q-Q plot
    """
    from scipy.stats import probplot
    from statsmodels.graphics.tsaplots import plot_acf as sm_acf

    residuals = fit.resid.dropna()

    with plt.style.context(STYLE):
        fig = plt.figure(figsize=(14, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

        # Panel 1: Residuals over time
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(residuals.index, residuals.values, color="#9C27B0", linewidth=1.0)
        ax1.axhline(0, color="gray", linestyle="--", linewidth=1)
        ax1.set_title("Residuals Over Time", fontweight="bold")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Residual")

        # Panel 2: Histogram
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(residuals.values, bins=30, density=True, color="#9C27B0", alpha=0.7, edgecolor="white")
        from scipy.stats import norm
        xr = np.linspace(residuals.min(), residuals.max(), 200)
        ax2.plot(xr, norm.pdf(xr, residuals.mean(), residuals.std()),
                 color="#FF5722", linewidth=2, label="Normal fit")
        ax2.set_title("Residual Distribution", fontweight="bold")
        ax2.set_xlabel("Residual")
        ax2.set_ylabel("Density")
        ax2.legend()

        # Panel 3: ACF of residuals
        ax3 = fig.add_subplot(gs[1, 0])
        sm_acf(residuals, lags=30, ax=ax3, color="#2196F3", alpha=0.05)
        ax3.set_title("ACF of Residuals", fontweight="bold")

        # Panel 4: Q-Q plot
        ax4 = fig.add_subplot(gs[1, 1])
        (osm, osr), (slope, intercept, r) = probplot(residuals.values, dist="norm")
        ax4.scatter(osm, osr, s=10, color="#4CAF50", alpha=0.8)
        ax4.plot(osm, slope * np.array(osm) + intercept, color="#FF5722", linewidth=2, label=f"R²={r**2:.3f}")
        ax4.set_title("Normal Q-Q Plot", fontweight="bold")
        ax4.set_xlabel("Theoretical Quantiles")
        ax4.set_ylabel("Sample Quantiles")
        ax4.legend()

        fig.suptitle("Residual Diagnostics", fontsize=15, fontweight="bold", y=1.01)
    return _save(fig, "07_residual_diagnostics", output_dir)


# ---------------------------------------------------------------------------
# 8. Metric bar chart
# ---------------------------------------------------------------------------

def plot_metrics(metrics_df: pd.DataFrame, output_dir: Path = PLOT_DIR) -> Path:
    """Horizontal bar chart of evaluation metrics."""
    plot_df = metrics_df[~metrics_df["metric"].isin(["R²"])].copy()

    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(8, max(3, len(plot_df) * 0.8)))
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#FF5722"]
        bars = ax.barh(
            plot_df["metric"],
            plot_df["value"],
            color=colors[: len(plot_df)],
            edgecolor="white",
            height=0.5,
        )
        for bar, val in zip(bars, plot_df["value"]):
            ax.text(
                bar.get_width() + 0.01 * plot_df["value"].max(),
                bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}",
                va="center",
                fontsize=10,
            )
        ax.set_title("Forecast Evaluation Metrics", fontsize=13, fontweight="bold")
        ax.set_xlabel("Value")
        fig.tight_layout()
    return _save(fig, "08_metrics", output_dir)
