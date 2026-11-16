# PriceWise

PriceWise is a pricing decision-support website for product-based businesses. It helps users analyze product costs, profit margins, compare prices, and receive rule-based pricing recommendations.

This is an early-stage group project prototype. Its main purpose is pricing decision support; results are estimates, not guaranteed optimal prices or demand predictions.

## Group Members

| Name | Email |
|---|---|
| Changwei Yuan | [cyuan@eada.net](mailto:cyuan@eada.net) |
| Sarvin Kalantari bengar | [skalantaribengar@eada.net](mailto:skalantaribengar@eada.net) |
| Sean Addison Smyth | [saddisonsmyth@eada.net](mailto:saddisonsmyth@eada.net) |
| Lila Carolina Emelinckx | [lemelinckx@eada.net](mailto:lemelinckx@eada.net) |

## Features

- Enter product details, costs, selling prices, and sales volume.
- Search from 4,015 product descriptions with historical price records.
- Calculate gross profit, profit margins, and estimated profit after fixed costs.
- Compare selling prices with competitor references and historical prices.
- View price comparisons through interactive charts.
- Get rule-based recommendations with transparent calculations.
- Optionally select a broad sample-data category to see experimental monthly sales estimates at the current and target-margin prices, plus validation error measures. This does not replace the website's pricing guidance.
- Access input guidance and a pre-filled demo example.

## Requirements

- Python 3.10 or newer.
- The website itself uses only Python's standard library.
- `demand_model.py` additionally requires scikit-learn, listed in `requirements.txt`.

## How to Run

Open a terminal in the project folder and run:

```bash
python pricewise_5.py
```

On Windows, you can also use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe pricewise_5.py
```

The app prints the demand model's validation metrics, starts the local server, and opens the page in your default browser. It tries ports 8000–8010 and reports the address it uses. Keep the run window open while using the website. Press `Ctrl+C` in that window to stop it. If the browser does not open automatically, use the address printed in the run window.

## Optional demand model

The website's target-margin price is calculated from unit cost and the chosen margin. If you select a category in the optional demand-estimate field, a separate Gradient Boosting regression model estimates monthly quantity at your current and target-margin prices. It uses the category, the ratio between proposed and current prices, and month of year from `dataset/retail_price.csv`. Its estimates are supplementary and do not change the website's rule-based guidance.

Install the model dependency and run it with:

```bash
python -m pip install -r requirements.txt
python demand_model.py
```

The model is evaluated across five expanding, time-ordered folds, each testing two complete future months. When running `pricewise_5.py` in PyCharm, its console shows MAE and RMSE (prediction errors in units), R-squared, and comparison with a category-average baseline. You can also run `demand_model.py` by itself to print the same report. Current rolling validation gives MAE 10.79 units, RMSE 17.65, R-squared -0.065, and WAPE 66.6% (a 33.4% WAPE-based score), compared with 72.7% WAPE for the category-average baseline. The negative R-squared still indicates a weak fit, so treat predictions as a project experiment rather than a dependable forecast. The dataset has only 676 observations from 2017–2018. Regression does not have a simple classification-style accuracy percentage.

## Design

The original `pricewise.py` file has been updated with a redesigned interface. The redesigned version is saved as **`pricewise_5.py`**.

## Sample Data

The product catalog is based on historical UK retail transactions from 2010–2011 (`Online Retail.xlsx`).

- Historical prices are not current market or competitor prices.
- Competitor reference data is stored separately and is not used for exact-product comparisons.
- The currency selector changes the displayed symbol only; it does not convert currencies.

## Important Limitations

- Website recommendations are rule-based, not AI-generated.
- Calculations exclude additional expenses such as taxes, shipping, and payment fees unless included in the inputs.
- Estimated profit is not net profit.
- Historical prices may not reflect current market conditions.
- Competitor prices are reference points, not guarantees of customer demand.

## Main Files

```text
pricewise.py                 Main website and calculations
PriceWise_5                  Redesigned version
dataset/product_catalog.csv  Searchable products and historical prices
dataset/retail_price.csv     Category-level competitor references
dataset/Online Retail.xlsx   Original data source
demand_model.py              Optional monthly sales-volume model
requirements.txt             Optional model dependency
```
