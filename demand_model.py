"""Optional category-level demand estimate for the PriceWise website.

The estimator predicts monthly quantity from a broad retail category, the
proposed/current price ratio, and month of year. It is supplementary to the
website's deterministic target-margin price calculation.

Install with: python -m pip install -r requirements.txt
Run evaluation with: python demand_model.py
"""

from __future__ import annotations

import csv
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "dataset" / "retail_price.csv"
CATEGORICAL_FEATURES = ["product_category_name"]
NUMERIC_FEATURES = ["price_ratio", "month"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def load_rows() -> list[dict]:
    """Load usable rows and create a currency-independent relative price."""
    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as source:
        rows = []
        for row in csv.DictReader(source):
            try:
                date = datetime.strptime(row["month_year"], "%d-%m-%Y")
                quantity = float(row["qty"])
                unit_price = float(row["unit_price"])
                lag_price = float(row["lag_price"])
                category = row["product_category_name"].strip()
                if quantity < 0 or unit_price <= 0 or lag_price <= 0 or not category:
                    continue
                rows.append(
                    {
                        "product_category_name": category,
                        "price_ratio": unit_price / lag_price,
                        "month": date.month,
                        "qty": quantity,
                        "date": date,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return sorted(rows, key=lambda item: item["date"])


def available_categories() -> list[str]:
    return sorted({row["product_category_name"] for row in load_rows()})


def make_model() -> Pipeline:
    numeric = Pipeline([("fill_missing", SimpleImputer(strategy="median"))])
    categorical = Pipeline(
        [
            ("fill_missing", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric, [1, 2]),
            ("category", categorical, [0]),
        ]
    )
    return Pipeline(
        [
            ("features", preprocess),
            (
                "regressor",
                GradientBoostingRegressor(
                    n_estimators=80,
                    learning_rate=0.05,
                    max_depth=2,
                    loss="huber",
                    random_state=42,
                ),
            ),
        ]
    )


def _inputs(rows: list[dict]) -> list[list]:
    return [[row[name] for name in FEATURES] for row in rows]


@lru_cache(maxsize=1)
def trained_estimator() -> tuple[Pipeline, dict]:
    """Run expanding, complete-month holdouts, then fit all rows for use."""
    rows = load_rows()
    if len(rows) < 30:
        raise ValueError("The demand dataset has too few usable rows.")

    months = sorted({row["date"] for row in rows})
    if len(months) < 12:
        raise ValueError("At least 12 distinct months are needed for time-based validation.")

    actual = []
    predicted = []
    baseline = []
    # Each test window contains two full months; all records from the same
    # month stay together. Five expanding-window folds cover the latest ten
    # months while preserving their time order.
    fold_starts = range(max(10, len(months) - 10), len(months) - 1, 2)
    fold_count = 0
    for start in fold_starts:
        train = [row for row in rows if row["date"] < months[start]]
        holdout_months = set(months[start : start + 2])
        holdout = [row for row in rows if row["date"] in holdout_months]
        if not train or not holdout:
            continue

        model = make_model()
        model.fit(_inputs(train), [row["qty"] for row in train])
        predicted.extend(max(0.0, float(value)) for value in model.predict(_inputs(holdout)))
        actual.extend(row["qty"] for row in holdout)

        category_history: dict[str, list[float]] = {}
        for row in train:
            category_history.setdefault(row["product_category_name"], []).append(row["qty"])
        overall_average = sum(row["qty"] for row in train) / len(train)
        baseline.extend(
            sum(category_history.get(row["product_category_name"], [overall_average]))
            / len(category_history.get(row["product_category_name"], [overall_average]))
            for row in holdout
        )
        fold_count += 1

    if not actual:
        raise ValueError("Could not create time-based validation folds from the dataset.")

    absolute_error_total = sum(abs(expected - estimate) for expected, estimate in zip(actual, predicted))
    actual_total = sum(actual)
    baseline_absolute_error_total = sum(abs(expected - estimate) for expected, estimate in zip(actual, baseline))
    metrics = {
        "rows": len(rows),
        "folds": fold_count,
        "holdout_rows": len(actual),
        "holdout_start": months[max(10, len(months) - 10)],
        "holdout_end": months[-1],
        "mae": mean_absolute_error(actual, predicted),
        "rmse": mean_squared_error(actual, predicted) ** 0.5,
        "r2": r2_score(actual, predicted),
        "baseline_mae": mean_absolute_error(actual, baseline),
        "wape": absolute_error_total / actual_total * 100 if actual_total else 0.0,
        "baseline_wape": baseline_absolute_error_total / actual_total * 100 if actual_total else 0.0,
    }

    # Fit the production estimator on all rows after computing out-of-time
    # validation metrics.
    model = make_model()
    model.fit(_inputs(rows), [row["qty"] for row in rows])
    return model, metrics


def predict_monthly_demand(category: str, price_ratio: float, month: int) -> tuple[float, dict]:
    """Estimate monthly units; price_ratio is proposed price / current price."""
    model, metrics = trained_estimator()
    features = [[category, price_ratio, month]]
    estimate = float(model.predict(features)[0])
    return max(0.0, estimate), metrics


def main() -> None:
    model, metrics = trained_estimator()
    del model
    print("PriceWise optional demand-estimation model")
    print(f"Rows: {metrics['rows']} | Rolling validation: {metrics['folds']} two-month future windows | Tested rows: {metrics['holdout_rows']}")
    print(f"Validation period: {metrics['holdout_start']:%b %Y} to {metrics['holdout_end']:%b %Y}")
    print("\nRegression validation (lower MAE/RMSE/WAPE is better):")
    print(f"Gradient Boosting MAE: {metrics['mae']:.2f} units per product-month")
    print(f"Category-average baseline MAE: {metrics['baseline_mae']:.2f} units per product-month")
    print(f"Gradient Boosting RMSE: {metrics['rmse']:.2f} units per product-month")
    print(f"Gradient Boosting R-squared: {metrics['r2']:.3f} (closer to 1 is better; negative means poor fit)")
    print(f"WAPE: {metrics['wape']:.1f}% | WAPE-based score: {100 - metrics['wape']:.1f}%")
    print(f"Baseline WAPE: {metrics['baseline_wape']:.1f}% | Baseline WAPE-based score: {100 - metrics['baseline_wape']:.1f}%")
    print("\nThis is an experimental estimate from a small, older dataset. It does not")
    print("replace PriceWise's cost, target-margin, or competitor-based guidance.")


if __name__ == "__main__":
    main()
