"""
ARIMA Forecasting Pipeline — Main Runner
==========================================
Orchestrates all pipeline stages end-to-end:

  Stage 1  → Data acquisition (synthetic generation or CSV load)
  Stage 2  → Preprocessing & EDA (missing values, outliers, stats)
  Stage 3  → Stationarity tests (ADF, KPSS, differencing order)
  Stage 4  → Order selection (ACF/PACF heuristic + grid search)
  Stage 5  → Model fitting & diagnostics
  Stage 6  → Forecasting (out-of-sample + rolling walk-forward)
  Stage 7  → Evaluation (MAE, RMSE, MAPE, SMAPE, MASE, R²)
  Stage 8  → Visualization (8 plots saved to outputs/plots/)
  Stage 9  → Results export (CSV + JSON summary)

Usage
-----
  python pipeline.py                           # synthetic data, auto order
  python pipeline.py --source csv --filepath data/my_data.csv
  python pipeline.py --order 2 1 2             # fix ARIMA order manually
  python pipeline.py --no-grid-search          # skip grid search
  python pipeline.py --test-size 0.15 --steps 24
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Make src/ importable when running from the project root
# ---------------------------------------------------------------------------
SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))

from data_generator import get_dataset, save_series
from preprocessing import (
    handle_missing,
    cap_outliers,
    detect_outliers_iqr,
    train_test_split,
    eda_summary,
    infer_frequency,
    difference,
)
from stationarity import stationarity_report, recommend_differencing
from model import (
    suggest_order_from_acf_pacf,
    auto_arima_search,
    fit_arima,
    model_summary,
    residual_diagnostics,
)
from evaluation import forecast, rolling_forecast, evaluate, coverage
from visualization import (
    plot_series,
    plot_decomposition,
    plot_acf_pacf,
    plot_stationarity_comparison,
    plot_forecast,
    plot_rolling_forecast,
    plot_residual_diagnostics,
    plot_metrics,
    PLOT_DIR,
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEPARATOR = "\n" + "=" * 70 + "\n"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> dict:
    results = {}

    # -----------------------------------------------------------------------
    # Stage 1 — Data Acquisition
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 1 — DATA ACQUISITION")

    series = get_dataset(
        source=args.source,
        filepath=args.filepath,
        n=args.n_obs,
        seed=args.seed,
    )
    save_series(series, output_dir="data", filename="timeseries.csv")

    # -----------------------------------------------------------------------
    # Stage 2 — Preprocessing & EDA
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 2 — PREPROCESSING & EDA")

    infer_frequency(series)
    series = handle_missing(series, method="interpolate")

    outlier_mask = detect_outliers_iqr(series, k=3.0)
    if outlier_mask.sum() > 0:
        series = cap_outliers(series, k=3.0)

    summary_df = eda_summary(series)
    print("\n[eda] Summary Statistics:")
    print(summary_df.to_string(index=False))
    summary_df.to_csv(OUTPUT_DIR / "eda_summary.csv", index=False)

    train, test = train_test_split(series, test_size=args.test_size)

    # -----------------------------------------------------------------------
    # Stage 3 — Stationarity Tests
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 3 — STATIONARITY TESTS")

    stat_report = stationarity_report(train, alpha=0.05)
    print("\n[stationarity] Report:")
    print(stat_report.to_string(index=False))
    stat_report.to_csv(OUTPUT_DIR / "stationarity_report.csv", index=False)

    recommended_d, stationary_train = recommend_differencing(train, max_d=3)
    results["recommended_d"] = recommended_d

    # -----------------------------------------------------------------------
    # Stage 4 — Order Selection
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 4 — ORDER SELECTION")

    if args.order:
        best_order = tuple(args.order)
        print(f"[order_selection] Using manually specified order: ARIMA{best_order}")
    else:
        # Heuristic suggestion from ACF/PACF
        heuristic = suggest_order_from_acf_pacf(stationary_train, d=recommended_d)

        if not args.no_grid_search:
            search_result = auto_arima_search(
                train,
                p_range=range(0, args.p_max + 1),
                d_range=range(0, recommended_d + 2),
                q_range=range(0, args.q_max + 1),
                criterion="aic",
            )
            best_order = search_result["best_order"]
            search_result["all_results"].to_csv(OUTPUT_DIR / "grid_search_results.csv", index=False)
        else:
            best_order = (heuristic["p"], heuristic["d"], heuristic["q"])
            print(f"[order_selection] Grid search skipped. Using heuristic: ARIMA{best_order}")

    results["best_order"] = best_order

    # -----------------------------------------------------------------------
    # Stage 5 — Model Fitting & Diagnostics
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 5 — MODEL FITTING")

    fit = fit_arima(train, order=best_order)
    summary_str = model_summary(fit)
    (OUTPUT_DIR / "model_summary.txt").write_text(summary_str)
    print(summary_str)

    diag = residual_diagnostics(fit)
    results["diagnostics"] = diag

    # -----------------------------------------------------------------------
    # Stage 6 — Forecasting
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 6 — FORECASTING")

    steps = args.steps if args.steps else len(test)
    forecast_df = forecast(fit, steps=steps, alpha=0.05)
    forecast_df.index = test.index[:steps]
    forecast_df.to_csv(OUTPUT_DIR / "forecast.csv")

    print("\n[forecast] First 10 forecast rows:")
    print(forecast_df.head(10).to_string())

    # Walk-forward
    print("\n[rolling_forecast] Running walk-forward evaluation ...")
    rolling_df = rolling_forecast(train, test, order=best_order, refit_every=5)
    rolling_df.to_csv(OUTPUT_DIR / "rolling_forecast.csv")

    # -----------------------------------------------------------------------
    # Stage 7 — Evaluation
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 7 — EVALUATION")

    # Align forecast to test length
    common_idx = test.index[:steps]
    actual_aligned = test.loc[common_idx]
    forecast_aligned = forecast_df.loc[common_idx, "forecast"]

    metrics_df = evaluate(actual_aligned, forecast_aligned, train=train)
    metrics_df.to_csv(OUTPUT_DIR / "metrics.csv", index=False)
    results["metrics"] = metrics_df.set_index("metric")["value"].to_dict()

    ci_cov = coverage(actual_aligned, forecast_df.loc[common_idx])
    results["ci_coverage"] = round(ci_cov, 4)

    # Rolling metrics
    rolling_metrics = evaluate(rolling_df["actual"], rolling_df["forecast"], train=train)
    rolling_metrics.to_csv(OUTPUT_DIR / "rolling_metrics.csv", index=False)

    # -----------------------------------------------------------------------
    # Stage 8 — Visualization
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 8 — VISUALIZATION")

    plot_series(series, title="Time Series Overview", train=train, test=test, output_dir=PLOT_DIR)
    plot_decomposition(train, period=12, model="additive", output_dir=PLOT_DIR)
    plot_acf_pacf(train, nlags=40, title_prefix="Train", output_dir=PLOT_DIR)
    plot_stationarity_comparison(train, stationary_train, d=recommended_d, output_dir=PLOT_DIR)
    plot_forecast(train, test, forecast_df, title=f"ARIMA{best_order} Forecast", output_dir=PLOT_DIR)
    plot_rolling_forecast(rolling_df, output_dir=PLOT_DIR)
    plot_residual_diagnostics(fit, output_dir=PLOT_DIR)
    plot_metrics(metrics_df, output_dir=PLOT_DIR)

    # -----------------------------------------------------------------------
    # Stage 9 — Export Summary
    # -----------------------------------------------------------------------
    print(SEPARATOR + "STAGE 9 — EXPORT SUMMARY")

    summary = {
        "arima_order": best_order,
        "recommended_d": recommended_d,
        "n_train": len(train),
        "n_test": len(test),
        "forecast_steps": steps,
        "ci_coverage_95pct": results["ci_coverage"],
        "metrics": results["metrics"],
        "residual_diagnostics": {
            k: v for k, v in diag.items()
            if not isinstance(v, (dict, list))
        },
    }

    summary_path = OUTPUT_DIR / "pipeline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[pipeline] Summary saved → {summary_path}")

    print(SEPARATOR + "PIPELINE COMPLETE")
    print(f"  Best ARIMA Order : {best_order}")
    print(f"  Forecast Steps   : {steps}")
    print(f"  CI Coverage      : {ci_cov:.1%}")
    for metric, val in results["metrics"].items():
        print(f"  {metric:<14}: {val}")
    print(f"\n  All outputs in   : {OUTPUT_DIR.resolve()}")
    print(f"  All plots in     : {PLOT_DIR.resolve()}\n")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Full ARIMA Forecasting Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Data
    data_group = parser.add_argument_group("Data")
    data_group.add_argument("--source", choices=["synthetic", "csv"], default="synthetic",
                            help="Data source.")
    data_group.add_argument("--filepath", type=str, default=None,
                            help="Path to CSV file (required if --source csv).")
    data_group.add_argument("--n-obs", type=int, default=240,
                            help="Number of synthetic observations to generate.")
    data_group.add_argument("--seed", type=int, default=42,
                            help="Random seed for synthetic data.")

    # Split
    split_group = parser.add_argument_group("Train/Test Split")
    split_group.add_argument("--test-size", type=float, default=0.2,
                             help="Fraction of data to reserve for testing.")
    split_group.add_argument("--steps", type=int, default=None,
                             help="Forecast horizon (default = test set length).")

    # Order selection
    order_group = parser.add_argument_group("Order Selection")
    order_group.add_argument("--order", type=int, nargs=3, metavar=("p", "d", "q"),
                             default=None, help="Fix ARIMA order manually (skips selection).")
    order_group.add_argument("--no-grid-search", action="store_true",
                             help="Skip grid search; use ACF/PACF heuristic only.")
    order_group.add_argument("--p-max", type=int, default=3, help="Max AR order for grid search.")
    order_group.add_argument("--q-max", type=int, default=3, help="Max MA order for grid search.")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args)
