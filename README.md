# PriceWise

PriceWise is a pricing decision-support website for product-based businesses. It helps users analyze product costs, profit margins, compare prices, and receive rule-based pricing recommendations.

This is an early-stage group project prototype. Results are estimates based on user inputs, not guaranteed optimal prices or demand predictions.

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
- Access input guidance and a pre-filled demo example.

## Requirements

- Python 3.10 or newer.
- No third-party packages required.

## How to Run

Open a terminal in the project folder and run:

```bash
python pricewise_5.py
```

On Windows, you can also use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe pricewise_5.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Keep the terminal open while using the website. Press `Ctrl+C` to stop it.

## Design

The original `pricewise.py` file has been updated with a redesigned interface. The redesigned version is saved as **`PriceWise_5`**.

## Sample Data

The product catalog is based on historical UK retail transactions from 2010–2011 (`Online Retail.xlsx`).

- Historical prices are not current market or competitor prices.
- Competitor reference data is stored separately and is not used for exact-product comparisons.
- The currency selector changes the displayed symbol only; it does not convert currencies.

## Important Limitations

- Recommendations are rule-based, not AI-generated.
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
```
