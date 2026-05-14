"""
ARIMA Model Training Module
-----------------------------
Covers:
  - ACF / PACF-based manual order selection
  - Grid-search auto order selection (AIC/BIC)
  - Model fitting with statsmodels ARIMA
  - Model diagnostics (residual analysis, Ljung-Box test)
"""

import warnings
import itertools
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf, pacf
from typing import Dict, Optional, Tuple


warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# ACF / PACF helpers
# ---------------------------------------------------------------------------

def compute_acf_pacf(
    series: pd.Series, nlags: int = 40
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute ACF and PACF arrays.

    Returns
    -------
    (acf_values, pacf_values) — each includes lag-0.
    """
    acf_vals = acf(series.dropna(), nlags=nlags, fft=True)
    pacf_vals = pacf(series.dropna(), nlags=nlags)
    return acf_vals, pacf_vals


def suggest_order_from_acf_pacf(
    series: pd.Series, d: int = 0, nlags: int = 20, alpha: float = 0.05
) -> Dict:
    """
    Heuristic rule-based suggestion for ARIMA (p, d, q) based on ACF/PACF patterns.

    Rules applied:
      - PACF cuts off at lag p  → AR(p) process
      - ACF cuts off at lag q   → MA(q) process
      - Both tail off           → ARMA(p,q) — use small values

    Parameters
    ----------
    series : (Differenced) stationary series.
    d      : Differencing order already applied.
    nlags  : Number of lags to inspect.
    alpha  : Significance level for confidence bands.

    Returns
    -------
    dict with suggested p, d, q.
    """
    acf_vals, pacf_vals = compute_acf_pacf(series, nlags=nlags)
    n = len(series)
    conf = 1.96 / np.sqrt(n)  # approximate 95% CI half-width

    # Find where ACF / PACF first drop inside the CI band
    acf_sig = [i for i in range(1, nlags + 1) if abs(acf_vals[i]) > conf]
    pacf_sig = [i for i in range(1, nlags + 1) if abs(pacf_vals[i]) > conf]

    q = max(acf_sig) if acf_sig else 0
    p = max(pacf_sig) if pacf_sig else 0

    # Cap at reasonable defaults
    p = min(p, 3)
    q = min(q, 3)

    print(f"\n[order_selection] ACF significant lags: {acf_sig[:10]}")
    print(f"[order_selection] PACF significant lags: {pacf_sig[:10]}")
    print(f"[order_selection] Heuristic suggestion: ARIMA({p},{d},{q})")
    return {"p": p, "d": d, "q": q}


# ---------------------------------------------------------------------------
# Grid-search auto order selection
# ---------------------------------------------------------------------------

def auto_arima_search(
    series: pd.Series,
    p_range: range = range(0, 4),
    d_range: range = range(0, 3),
    q_range: range = range(0, 4),
    criterion: str = "aic",
    seasonal: bool = False,
) -> Dict:
    """
    Exhaustive grid search over ARIMA(p,d,q) orders.

    Parameters
    ----------
    series    : Training series.
    p_range   : Range of AR orders to test.
    d_range   : Range of differencing orders to test.
    q_range   : Range of MA orders to test.
    criterion : 'aic' or 'bic' (lower is better).
    seasonal  : If True, also searches seasonal parameters (not yet implemented).

    Returns
    -------
    dict with best (p, d, q), score, and full results DataFrame.
    """
    print(f"\n[auto_arima] Grid searching {len(p_range)*len(d_range)*len(q_range)} ARIMA models ...")
    results = []

    for p, d, q in itertools.product(p_range, d_range, q_range):
        try:
            model = ARIMA(series, order=(p, d, q))
            fit = model.fit()
            score = fit.aic if criterion == "aic" else fit.bic
            results.append({"p": p, "d": d, "q": q, criterion: round(score, 2)})
        except Exception:
            pass

    if not results:
        raise RuntimeError("No ARIMA model converged during grid search.")

    results_df = pd.DataFrame(results).sort_values(criterion).reset_index(drop=True)
    best = results_df.iloc[0]

    print(f"[auto_arima] Best ARIMA({int(best.p)},{int(best.d)},{int(best.q)}) "
          f"→ {criterion.upper()}={best[criterion]:.2f}")

    return {
        "best_order": (int(best.p), int(best.d), int(best.q)),
        "best_score": best[criterion],
        "criterion": criterion,
        "all_results": results_df,
    }


# ---------------------------------------------------------------------------
# Model Fitting
# ---------------------------------------------------------------------------

def fit_arima(
    series: pd.Series,
    order: Tuple[int, int, int],
    trend: Optional[str] = None,
) -> "ARIMAResultsWrapper":
    """
    Fit an ARIMA model.

    Parameters
    ----------
    series : Training time series.
    order  : (p, d, q) tuple.
    trend  : 'n', 'c', 't', 'ct' — or None to let statsmodels decide.

    Returns
    -------
    Fitted ARIMAResultsWrapper.
    """
    p, d, q = order
    print(f"\n[fit_arima] Fitting ARIMA({p},{d},{q}) ...")
    kwargs = {"order": order}
    if trend is not None:
        kwargs["trend"] = trend

    model = ARIMA(series, **kwargs)
    fit = model.fit()

    print(f"[fit_arima] AIC={fit.aic:.2f}  BIC={fit.bic:.2f}  HQIC={fit.hqic:.2f}")
    return fit


def model_summary(fit) -> str:
    """Return the full statsmodels summary as a string."""
    return str(fit.summary())


# ---------------------------------------------------------------------------
# Residual Diagnostics
# ---------------------------------------------------------------------------

def residual_diagnostics(fit) -> Dict:
    """
    Analyse model residuals to check for autocorrelation and normality.

    Tests performed:
      - Ljung-Box test (H0: no autocorrelation in residuals)
      - Jarque-Bera test (H0: residuals are normally distributed)
      - Residual mean and std

    Returns
    -------
    dict with diagnostic results.
    """
    residuals = fit.resid

    # Ljung-Box test at lags 5, 10, 15
    lags = [5, 10, 15]
    lb = acorr_ljungbox(residuals, lags=lags, return_df=True)

    lb_results = {
        f"lb_stat_lag{lag}": round(lb.loc[lag, "lb_stat"], 4)
        for lag in lags
        if lag in lb.index
    }
    lb_pvalues = {
        f"lb_pvalue_lag{lag}": round(lb.loc[lag, "lb_pvalue"], 4)
        for lag in lags
        if lag in lb.index
    }

    # Jarque-Bera
    from scipy.stats import jarque_bera, shapiro
    jb_stat, jb_p = jarque_bera(residuals.dropna())

    diag = {
        "residual_mean": round(float(residuals.mean()), 6),
        "residual_std": round(float(residuals.std()), 6),
        **lb_results,
        **lb_pvalues,
        "jarque_bera_stat": round(jb_stat, 4),
        "jarque_bera_pvalue": round(jb_p, 4),
        "residuals_normal": jb_p > 0.05,
        "no_autocorrelation": all(
            lb.loc[lag, "lb_pvalue"] > 0.05
            for lag in lags
            if lag in lb.index
        ),
    }

    print("\n--- Residual Diagnostics ---")
    print(f"  Mean     : {diag['residual_mean']}")
    print(f"  Std      : {diag['residual_std']}")
    for lag in lags:
        key = f"lb_pvalue_lag{lag}"
        if key in diag:
            status = "OK" if diag[key] > 0.05 else "AUTOCORRELATION"
            print(f"  Ljung-Box lag={lag}: p={diag[key]}  [{status}]")
    print(f"  Jarque-Bera p-value: {diag['jarque_bera_pvalue']} "
          f"[{'NORMAL' if diag['residuals_normal'] else 'NON-NORMAL'}]")

    return diag
