"""
SARIMA Forecasting Pipeline — Main Runner
==========================================

Usage
-----
  # Run full pipeline with defaults (synthetic data):
  python pipeline.py

  # Run with a CSV file:
  python pipeline.py --source csv --csv-path data/my_series.csv --date-col date --value-col sales

  # Skip grid search, use manual order:
  python pipeline.py --no-grid-search --p 2 --d 1 --q 1 --P 1 --D 1 --Q 1 --s 12

  # Disable plots (CI / headless environments):
  python pipeline.py --no-plots

Pipeline steps
--------------
  1. Load / generate data
  2. EDA plots
  3. Preprocessing (transform + differencing + stationarity tests)
  4. ACF / PACF plots on transformed series
  5. SARIMA order selection (grid search or manual)
  6. Model fitting & diagnostics
  7. Forecast generation
  8. Evaluation (test-set metrics + walk-forward)
  9. Export artefacts (model, forecasts, metrics, plots)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── ensure project root is on PYTHONPATH ──────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── imports ───────────────────────────────────────────────────────────────
import pandas as pd

from data.data_generator import (
    generate_synthetic_series,
    load_series_from_csv,
    save_series,
    train_test_split,
)
from data.preprocessor import preprocess, print_report
from models.forecaster import (
    EvaluationMetrics,
    ForecastResult,
    compute_metrics,
    forecast,
    rolling_forecast_eval,
    save_evaluation,
)
from models.sarima_model import (
    ModelDiagnostics,
    SARIMAOrder,
    compute_diagnostics,
    fit_sarima,
    grid_search,
    save_model,
    save_order,
)
from plots.visualizer import (
    plot_acf_pacf,
    plot_decomposition,
    plot_forecast,
    plot_residual_diagnostics,
    plot_rolling_errors,
    plot_series,
    plot_stationarity_check,
)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         SARIMA Forecasting Pipeline                         ║
╚══════════════════════════════════════════════════════════════╝
"""


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Full SARIMA forecasting pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # ── Data source ──────────────────────────────────────────────────────
    p.add_argument("--source", choices=["synthetic", "csv"], default="synthetic",
                   help="Data source.")
    p.add_argument("--csv-path", type=str, default=None,
                   help="Path to CSV file (required when --source=csv).")
    p.add_argument("--date-col", type=str, default="date",
                   help="Date column name in CSV.")
    p.add_argument("--value-col", type=str, default="value",
                   help="Target value column name in CSV.")
    p.add_argument("--freq", type=str, default="MS",
                   help="Pandas date frequency (e.g. MS, D, Q).")

    # ── Synthetic data options ────────────────────────────────────────────
    p.add_argument("--n-periods", type=int, default=240,
                   help="Number of periods for synthetic data.")
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed for synthetic data generation.")

    # ── Pre-processing ────────────────────────────────────────────────────
    p.add_argument("--transform", choices=["none", "log", "boxcox"], default="log",
                   help="Variance-stabilising transformation.")
    p.add_argument("--seasonal-period", type=int, default=12,
                   help="Seasonal period m (e.g. 12=monthly, 4=quarterly).")
    p.add_argument("--d", type=int, default=None,
                   help="Override regular differencing order d.")
    p.add_argument("--D", type=int, default=None,
                   help="Override seasonal differencing order D.")

    # ── Model order ───────────────────────────────────────────────────────
    p.add_argument("--no-grid-search", action="store_true",
                   help="Skip grid search, use manual (p,q,P,Q).")
    p.add_argument("--p", type=int, default=1)
    p.add_argument("--q", type=int, default=1)
    p.add_argument("--P", type=int, default=1)
    p.add_argument("--Q", type=int, default=1)
    p.add_argument("--trend", type=str, default="c",
                   help="Trend parameter for SARIMAX ('n','c','t','ct').")
    p.add_argument("--criterion", choices=["aic", "bic"], default="aic",
                   help="Information criterion for grid search.")

    # ── Evaluation ────────────────────────────────────────────────────────
    p.add_argument("--test-size", type=int, default=24,
                   help="Number of observations in test set.")
    p.add_argument("--alpha", type=float, default=0.05,
                   help="Significance level for prediction intervals.")
    p.add_argument("--rolling-eval", action="store_true",
                   help="Run walk-forward rolling evaluation.")

    # ── Output ────────────────────────────────────────────────────────────
    p.add_argument("--output-dir", type=str, default="outputs",
                   help="Directory for all output artefacts.")
    p.add_argument("--no-plots", action="store_true",
                   help="Disable all visualisation.")
    p.add_argument("--plot-format", type=str, default="png",
                   help="Plot file format (png, pdf, svg).")

    return p


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> None:
    print(BANNER)
    out = ROOT / args.output_dir
    pdir = out / "plots"
    pdir.mkdir(parents=True, exist_ok=True)

    def plot_path(name: str) -> Path | None:
        if args.no_plots:
            return None
        return pdir / f"{name}.{args.plot_format}"

    # ════════════════════════════════════════════════════════════════
    # STEP 1 — Load data
    # ════════════════════════════════════════════════════════════════
    print("[ 1/9 ]  Loading data ...")
    if args.source == "synthetic":
        series = generate_synthetic_series(
            n_periods=args.n_periods,
            seasonal_period=args.seasonal_period,
            seed=args.seed,
            freq=args.freq,
        )
        print(f"         Synthetic series: {len(series)} obs "
              f"({series.index[0].date()} → {series.index[-1].date()})")
    else:
        if not args.csv_path:
            sys.exit("ERROR: --csv-path is required when --source=csv")
        series = load_series_from_csv(
            args.csv_path,
            date_col=args.date_col,
            value_col=args.value_col,
            freq=args.freq,
        )
        print(f"         Loaded {len(series)} obs from '{args.csv_path}'")

    # Save raw series
    save_series(series, out / "raw_series.csv")

    # ════════════════════════════════════════════════════════════════
    # STEP 2 — Train / test split
    # ════════════════════════════════════════════════════════════════
    print(f"\n[ 2/9 ]  Train/test split  (test_size={args.test_size}) ...")
    train, test = train_test_split(series, test_size=args.test_size)
    print(f"         Train: {len(train)} obs  |  Test: {len(test)} obs")

    # ════════════════════════════════════════════════════════════════
    # STEP 3 — EDA plots
    # ════════════════════════════════════════════════════════════════
    print("\n[ 3/9 ]  EDA visualisation ...")
    if not args.no_plots:
        plot_series(series, title="Raw Series Overview",
                    save_path=plot_path("01_series_overview"))
        plot_decomposition(series, seasonal_period=args.seasonal_period,
                           save_path=plot_path("02_decomposition"))
        plot_acf_pacf(series, title="Raw Series",
                      save_path=plot_path("03_acf_pacf_raw"))

    # ════════════════════════════════════════════════════════════════
    # STEP 4 — Preprocessing
    # ════════════════════════════════════════════════════════════════
    print("\n[ 4/9 ]  Preprocessing (transform + stationarity) ...")
    auto_diff = args.d is None and args.D is None
    processed, report = preprocess(
        train,
        seasonal_period=args.seasonal_period,
        transformation=args.transform,
        auto_diff=auto_diff,
        d=args.d,
        D=args.D,
    )
    print_report(report)

    # Stationarity & ACF/PACF on processed series
    if not args.no_plots:
        plot_stationarity_check(
            train, processed, d=report.d, D=report.D,
            seasonal_period=args.seasonal_period,
            save_path=plot_path("04_stationarity_check"),
        )
        plot_acf_pacf(processed, title="Processed Series",
                      save_path=plot_path("05_acf_pacf_processed"))

    # Resolve final d / D from report (may have been auto-detected)
    d_final = report.d
    D_final = report.D

    # ════════════════════════════════════════════════════════════════
    # STEP 5 — Order selection
    # ════════════════════════════════════════════════════════════════
    print("\n[ 5/9 ]  SARIMA order selection ...")
    if args.no_grid_search:
        best_order = SARIMAOrder(
            p=args.p, d=d_final, q=args.q,
            P=args.P, D=D_final, Q=args.Q,
            s=args.seasonal_period,
        )
        print(f"         Manual order: {best_order}")
    else:
        gs_result = grid_search(
            train,
            d=d_final, D=D_final, s=args.seasonal_period,
            criterion=args.criterion,
            trend=args.trend,
            verbose=True,
        )
        best_order = gs_result.best_order
        print(f"\n         Best order: {best_order}  "
              f"{args.criterion.upper()}={gs_result.best_aic:.2f}")
        print("\n         Top-5 leaderboard:")
        for row in gs_result.leaderboard:
            print(f"           {row['order']:40s}  AIC={row['aic']:.2f}  BIC={row['bic']:.2f}")

    save_order(best_order, out / "best_order.json")

    # ════════════════════════════════════════════════════════════════
    # STEP 6 — Model fitting & diagnostics
    # ════════════════════════════════════════════════════════════════
    print(f"\n[ 6/9 ]  Fitting {best_order} on full training set ...")
    fitted_result = fit_sarima(train, best_order, trend=args.trend)
    diag = compute_diagnostics(fitted_result)
    print("\n  Model Diagnostics:")
    print(diag.summary())

    save_model(fitted_result, out / "sarima_model.pkl")

    if not args.no_plots:
        plot_residual_diagnostics(fitted_result,
                                  save_path=plot_path("06_residual_diagnostics"))

    # ════════════════════════════════════════════════════════════════
    # STEP 7 — Forecast
    # ════════════════════════════════════════════════════════════════
    print(f"\n[ 7/9 ]  Forecasting {len(test)} steps ahead ...")
    fc = forecast(fitted_result, steps=len(test), alpha=args.alpha)
    fc.save(out / "forecast.csv")

    if not args.no_plots:
        plot_forecast(
            train, test, fc,
            title=f"{best_order}  —  Forecast",
            save_path=plot_path("07_forecast"),
        )

    # ════════════════════════════════════════════════════════════════
    # STEP 8 — Evaluation
    # ════════════════════════════════════════════════════════════════
    print("\n[ 8/9 ]  Evaluating forecast quality ...")
    metrics = compute_metrics(test, fc, train_series=train,
                              seasonal_period=args.seasonal_period)
    print("\n  Test-Set Metrics:")
    print(metrics.summary())
    save_evaluation(metrics, out / "metrics.json")

    # Optional walk-forward evaluation
    if args.rolling_eval:
        print("\n         Running walk-forward evaluation ...")
        rolling = rolling_forecast_eval(
            series,
            order=best_order,
            initial_train_size=len(train),
            horizon=1,
            step=1,
            alpha=args.alpha,
            seasonal_period=args.seasonal_period,
            trend=args.trend,
        )
        rolling.forecasts.to_csv(out / "rolling_forecasts.csv")
        print("\n  Walk-Forward Aggregate Metrics:")
        print(rolling.aggregate_metrics.summary())
        if not args.no_plots:
            plot_rolling_errors(rolling.forecasts,
                                save_path=plot_path("08_rolling_errors"))

    # ════════════════════════════════════════════════════════════════
    # STEP 9 — Summary
    # ════════════════════════════════════════════════════════════════
    print(f"\n[ 9/9 ]  Pipeline complete.  Artefacts written to → {out.resolve()}")
    print("─" * 65)
    print(f"  Series     : {len(series)} observations")
    print(f"  Model      : {best_order}")
    print(f"  AIC / BIC  : {diag.aic:.2f} / {diag.bic:.2f}")
    print(f"  MAE        : {metrics.mae:.4f}")
    print(f"  RMSE       : {metrics.rmse:.4f}")
    print(f"  sMAPE      : {metrics.smape:.2f}%")
    if metrics.mase is not None:
        print(f"  MASE       : {metrics.mase:.4f}")
    print(f"  PI Coverage: {metrics.coverage * 100:.1f}%")
    print("─" * 65)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args)
