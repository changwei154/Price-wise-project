# PriceWise

PriceWise is a small pricing decision-support website for product-based businesses. It helps a user review a product's unit economics, compare its current price with competitor references, and read simple rule-based guidance.

The site is an early group-project prototype. Its results are estimates based on the values entered by the user; it does not predict demand or identify a guaranteed best price.

## Features

- Enter a product name, unit cost, current selling price, sales volume, and optional fixed costs.
- Search and select from 4,015 product descriptions with usable historical price records, or type a different product name.
- Open a small help tip beside each input for field-specific guidance.
- Load a filled-in demo example to see how the interface works.
- Calculate gross profit per unit, gross margin, and estimated profit after fixed costs.
- View a bar graph comparing selling price, unit cost, and an available reference price.
- Compare the current price with competitor prices entered manually, or view historical sale prices for the exact selected item.
- See rule-based recommendations with the formulas and arithmetic that produced each result.

## Requirements

- Python 3.10 or newer
- No third-party Python packages are required; the app uses the Python standard library.

## Run the website

Open a terminal in this project folder and run:

```bash
python pricewise.py
```

On Windows, if you want to use the project's existing virtual environment:

```powershell
.\.venv\Scripts\python.exe pricewise.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Keep the terminal window open while using the site. Press `Ctrl+C` in that window to stop it.

## Sample data

The current sample mode uses `dataset/product_catalog.csv`, derived from the `Description` and `UnitPrice` columns of `dataset/Online Retail.xlsx`. It shows a median, range, and count of historical sale-price entries for the exact item description selected. The catalog excludes cancelled invoices and non-positive quantities. These UK transactions are from 2010–2011, so they are past sale prices, not competitor prices or current market quotes. The source workbook does not contain acquisition costs.

The separate `dataset/retail_price.csv` file contains category-level competitor references without product descriptions that match the Excel workbook. The site does not use it for product comparisons because there is no shared product identifier. The files can remain in the repository for future exploration, but category-level figures should not be presented as exact-product comparisons.

The Excel workbook stores numeric prices without an explicit currency field. The currency selector changes the displayed symbol only; it does not convert values. Confirm the source currency before comparing its historical prices with your own. Product names from the catalog are suggestions; the cost, current price, and sales volume in the demo button are illustrative values, not copied from the workbook.

## Important limitations

- Recommendations are rule-based, not AI-generated.
- Gross profit uses the unit cost entered by the user and does not automatically include taxes, shipping, payment fees, or other costs.
- Estimated profit after fixed costs is `(selling price - unit cost) × units sold - fixed costs`. Enter fixed costs and sales volume for the same time period; the result is before other expenses and is not net profit.
- The same-item sample prices are historical and may not reflect today's prices or the user's market; they are not competitor prices.
- The currency selector changes the symbol only. It does not convert values between currencies.
- Competitor prices are comparison points, not proof that customers will buy at a given price.

## Main files

```text
pricewise.py                 Website and calculations
dataset/retail_price.csv     Category-level competitor sample; not used for item matching
dataset/product_catalog.csv Searchable item names with historical price summaries
dataset/Online Retail.xlsx   Source workbook for the product catalog; not needed at runtime
```

## GitHub collaboration notes

For a group repository, commit the source code, README, and the data files the group intends to share. Avoid committing the local `.venv` environment or PyCharm's `.idea` settings folder; each teammate can create their own environment and IDE settings. Before making the repository public, check the license and sharing terms for both source datasets and the derived product catalog. The current prototype does not include AI-generated explanations.
