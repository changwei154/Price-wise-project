"""PriceWise: a small, dependency-free pricing website for the project prototype.

Run with: python pricewise.py
Then open: http://127.0.0.1:8000
"""

from __future__ import annotations

import csv
import html
import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
PRODUCT_FILE = ROOT / "dataset" / "product_catalog.csv"
HOST, PORT = "127.0.0.1", 8000


def load_product_catalog():
    """Load product descriptions and exact-item historical price summaries."""
    try:
        with PRODUCT_FILE.open("r", encoding="utf-8-sig", newline="") as source:
            products = {}
            for row in csv.DictReader(source):
                name = (row.get("product_name") or "").strip()
                if name:
                    try:
                        product = {
                            "product_name": name,
                            "transaction_rows": int(row["transaction_rows"]),
                            "median_price": float(row["median_unit_price"]),
                            "min_price": float(row["min_unit_price"]),
                            "max_price": float(row["max_unit_price"]),
                            "latest_transaction": row.get("latest_transaction", ""),
                        }
                    except (TypeError, ValueError):
                        continue
                    if (
                        product["transaction_rows"] <= 0
                        or not all(math.isfinite(product[key]) and product[key] > 0 for key in ("median_price", "min_price", "max_price"))
                        or product["min_price"] > product["median_price"]
                        or product["median_price"] > product["max_price"]
                    ):
                        continue
                    products[name.casefold()] = product
            return products
    except (OSError, csv.Error, KeyError):
        return {}


PRODUCT_REFERENCE = load_product_catalog()
PRODUCT_CATALOG = [
    item["product_name"]
    for item in sorted(PRODUCT_REFERENCE.values(), key=lambda p: (-p["transaction_rows"], p["product_name"].casefold()))
]
PRODUCT_SEARCH_INDEX = [(name, name.casefold()) for name in PRODUCT_CATALOG]


def safe_float(values, key, default=None):
    try:
        value = float(values.get(key, [""])[0])
        return value if math.isfinite(value) else default
    except (TypeError, ValueError, IndexError):
        return default


def money(value, currency):
    return f"{html.escape(currency)}{value:,.2f}"


def help_tip(field_id, label, explanation):
    safe_label = html.escape(label, quote=True)
    safe_explanation = html.escape(explanation, quote=True)
    return (
        f'<button type="button" class="help-button" aria-label="Help for {safe_label}: {safe_explanation}" '
        f'aria-describedby="help-{field_id}" title="{safe_explanation}">'
        f'<span aria-hidden="true">!</span><span class="help-popover" id="help-{field_id}" '
        f'role="tooltip">{safe_explanation}</span></button>'
    )


def page(content, title="PriceWise"):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light; --ink:#182522; --muted:#687672; --line:#e3eae6; --green:#176b50; --pale:#eff7f2; --cream:#fafbf8; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--cream); color:var(--ink); font:16px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
header {{ background:#fff; border-bottom:1px solid var(--line); }} .top {{ max-width:1040px; margin:auto; padding:20px 24px; display:flex; align-items:center; justify-content:space-between; gap:16px; }}
.brand {{ font-weight:800; font-size:20px; letter-spacing:-.5px; }} .brand span {{ color:var(--green); }} .tag {{ color:var(--muted); font-size:13px; }}
main {{ max-width:1040px; margin:38px auto; padding:0 24px 48px; }} .intro {{ margin-bottom:24px; }} h1 {{ font-size:clamp(28px,4vw,38px); line-height:1.1; letter-spacing:-1px; margin:0 0 9px; }}
p {{ margin:0 0 12px; }} .sub {{ color:var(--muted); max-width:680px; }} .layout {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(280px,.8fr); gap:20px; align-items:start; }}
.card {{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:22px; box-shadow:0 5px 18px #1b38200a; }} h2 {{ font-size:18px; margin:0 0 16px; letter-spacing:-.3px; }} .section {{ padding-bottom:18px; margin-bottom:18px; border-bottom:1px solid var(--line); }}
.section:last-child {{ border-bottom:0; padding:0; margin:0; }} label {{ display:block; font-size:13px; font-weight:650; margin:0 0 6px; }} .label-line {{ display:flex; align-items:center; gap:6px; margin:0 0 6px; }} .label-line label {{ margin:0; }} input,select {{ width:100%; border:1px solid #d5dfd9; border-radius:9px; background:white; color:var(--ink); padding:11px 12px; font:inherit; outline:none; }}
input:focus,select:focus {{ border-color:var(--green); box-shadow:0 0 0 3px #176b501a; }} .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }} .field {{ margin-bottom:13px; }} .hint {{ color:var(--muted); font-size:12px; margin-top:5px; }}
.help-button {{ position:relative; display:inline-grid; place-items:center; flex:none; width:16px; height:16px; border:1px solid #78958a; border-radius:50%; padding:0; background:#fff; color:var(--green); font:inherit; font-size:11px; line-height:1; cursor:help; }}
.help-popover {{ display:none; position:absolute; z-index:10; left:50%; bottom:calc(100% + 8px); transform:translateX(-50%); width:220px; padding:10px 12px; border-radius:9px; background:#182522; color:white; font-size:12px; font-weight:450; line-height:1.45; text-align:left; box-shadow:0 6px 18px #18252230; }}
.help-button:hover .help-popover,.help-button:focus .help-popover {{ display:block; }} .help-button:focus-visible {{ outline:3px solid #176b5040; outline-offset:2px; }}
.button {{ display:inline-block; width:100%; border:0; border-radius:10px; padding:13px 16px; background:var(--green); color:white; font:inherit; font-weight:700; cursor:pointer; }} .button:hover {{ background:#10563f; }}
.metric {{ padding:15px; background:var(--pale); border-radius:11px; margin-bottom:11px; }} .metric small {{ display:block; color:var(--muted); font-size:12px; }} .metric strong {{ display:block; font-size:24px; margin-top:2px; letter-spacing:-.5px; }}
.price-chart {{ margin:18px 0 22px; padding:16px; border:1px solid var(--line); border-radius:12px; }} .price-chart h3 {{ margin:0 0 5px; font-size:15px; }} .chart-note {{ color:var(--muted); font-size:12px; margin:0 0 15px; }} .chart-row {{ margin:12px 0; }} .chart-label {{ display:flex; justify-content:space-between; gap:12px; margin-bottom:5px; font-size:13px; }} .chart-label strong {{ white-space:nowrap; }} .chart-track {{ height:11px; background:#eef1ef; border-radius:99px; overflow:hidden; }} .chart-fill {{ display:block; height:100%; border-radius:99px; min-width:0; }} .chart-current {{ background:var(--green); }} .chart-cost {{ background:#92a39b; }} .chart-reference {{ background:#5b83bf; }} .chart-axis {{ display:flex; justify-content:space-between; color:var(--muted); font-size:11px; margin-top:5px; }}
.notice {{ font-size:12px; color:var(--muted); background:#f5f7f5; border-radius:10px; padding:12px; }} .result-title {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }} .badge {{ background:var(--pale); color:var(--green); padding:4px 9px; border-radius:999px; font-weight:700; font-size:12px; }}
.advice {{ list-style:none; margin:0; padding:0; }} .advice li {{ padding:11px 0; border-bottom:1px solid var(--line); }} .advice li:last-child {{ border-bottom:0; }} .advice li:before {{ content:"•"; color:var(--green); font-weight:900; margin-right:9px; }} .advice small {{ display:block; margin:5px 0 0 19px; color:var(--muted); }}
.picker {{ position:relative; }} .picker-menu {{ position:absolute; z-index:5; top:100%; left:0; right:0; max-height:250px; overflow:auto; background:white; border:1px solid var(--line); border-radius:10px; box-shadow:0 8px 20px #1b38201a; margin-top:4px; }}
.picker-option {{ display:block; width:100%; border:0; text-align:left; background:white; padding:10px 12px; font:inherit; cursor:pointer; }} .picker-option:hover,.picker-option:focus {{ background:var(--pale); outline:0; }} .picker-status {{ padding:9px 12px; color:var(--muted); font-size:12px; }} .mini-button {{ border:1px solid var(--line); color:var(--green); background:white; border-radius:8px; padding:7px 11px; font:inherit; font-weight:600; font-size:12px; cursor:pointer; }} .mini-button:hover {{ background:var(--pale); }}
.error {{ color:#9f2d24; background:#fff2ef; border-radius:9px; padding:11px 12px; margin-bottom:14px; }} .field[hidden], [hidden] {{ display:none !important; }} footer {{ color:var(--muted); font-size:12px; text-align:center; margin-top:20px; }}
@media(max-width:760px) {{ main {{ margin-top:25px; }} .layout {{ grid-template-columns:1fr; }} .top {{ padding:16px 20px; }} }}
</style></head><body><header><div class="top"><div class="brand">Price<span>Wise</span></div><div class="tag">Simple pricing decisions, made clearer</div></div></header>
<main>{content}<footer>PriceWise gives illustrative decision support. It does not predict demand or choose a guaranteed best price.</footer></main><script src="/app.js"></script></body></html>"""


def render_form(values, error=""):
    currency = values.get("currency", ["€"])[0]
    source = values.get("source", ["manual"])[0]

    result = ""
    if values.get("analyze", [""])[0] == "1":
        try:
            result = render_results(values)
        except ValueError as exc:
            error = error or str(exc)
    error_box = f'<div class="error">{html.escape(error)}</div>' if error else ""
    content = f"""
<div class="intro"><h1>Understand your product pricing</h1><p class="sub">Enter a few details to see your margin, compare prices, and get clear guidance. Start with a demo if you want to explore first.</p></div>
<div class="layout"><section class="card"><div class="result-title"><h2>Product details</h2><button class="mini-button" id="load-example" type="button">Load example</button></div><p class="hint">Example costs and prices are illustrative; replace them with your figures.</p>{error_box}
<form method="post" action="/">
<div class="section"><div class="field"><div class="label-line"><label for="product">Product name</label>{help_tip('product', 'Product name', 'Choose a name from the historical product list, or type your own. The product list does not provide unit costs.')}</div><div class="picker"><input id="product" name="product" autocomplete="off" aria-autocomplete="list" aria-controls="product-menu" aria-expanded="false" placeholder="Click to browse or type to search" value="{html.escape(values.get('product',[''])[0], quote=True)}" required><div id="product-menu" class="picker-menu" role="listbox" hidden></div></div><div class="hint">Search {len(PRODUCT_CATALOG):,} item descriptions from Online Retail.xlsx, or type your own product. The dataset has names and sales prices, but no unit costs.</div></div>
<div class="grid2"><div class="field"><div class="label-line"><label for="cost">Your unit cost</label>{help_tip('cost', 'Unit cost', 'Enter what you pay to buy or make one unit. Keep it in the same currency as your selling price. Fixed costs go in the separate field.')}</div><input id="cost" name="cost" type="number" min="0" step="0.01" placeholder="e.g. 12.00" value="{html.escape(values.get('cost',[''])[0], quote=True)}" required><div class="hint">What you pay to buy or make one unit.</div></div><div class="field"><div class="label-line"><label for="price">Your current selling price</label>{help_tip('price', 'Current selling price', 'Enter the amount customers pay for one unit. Use the same currency as unit cost. Taxes and fees are not added automatically.')}</div><input id="price" name="price" type="number" min="0" step="0.01" placeholder="e.g. 25.00" value="{html.escape(values.get('price',[''])[0], quote=True)}" required></div></div>
<div class="grid2"><div class="field"><div class="label-line"><label for="fixed">Fixed costs (optional)</label>{help_tip('fixed', 'Fixed costs', 'Enter total fixed costs for the same period as the units sold, such as monthly rent. These costs do not change directly with the number of units.')}</div><input id="fixed" name="fixed" type="number" step="0.01" placeholder="e.g. 500.00" value="{html.escape(values.get('fixed',[''])[0], quote=True)}"><div class="hint">Total fixed costs for the same period as sales.</div></div><div class="field"><div class="label-line"><label for="volume">Units sold in that period</label>{help_tip('volume', 'Units sold', 'Enter the number of units sold during the period covered by your fixed costs. For example, pair monthly units with monthly fixed costs.')}</div><input id="volume" name="volume" type="number" min="0" step="1" placeholder="e.g. 100" value="{html.escape(values.get('volume',[''])[0], quote=True)}" required></div></div>
<div class="field"><div class="label-line"><label for="target">Target gross margin (%)</label>{help_tip('target', 'Target gross margin', 'This is your review threshold, not a markup. Gross margin is (selling price - unit cost) divided by selling price. The default 25% is only an example.')}</div><input id="target" name="target" type="number" min="0" max="90" step="1" value="{html.escape(values.get('target',['25'])[0], quote=True)}"><div class="hint">A review threshold you set; 25% is only a starting example.</div></div>
<div class="field"><div class="label-line"><label for="currency">Display currency</label>{help_tip('currency', 'Display currency', 'This changes the currency symbol shown next to results. It does not convert your input values or historical sample prices.')}</div><select id="currency" name="currency">{''.join(f'<option value="{s}"{" selected" if currency == s else ""}>{s}</option>' for s in ('€','$','£','R$'))}</select><div class="hint">Changes the symbol only; it does not convert prices.</div></div></div>
<div class="section"><div class="field"><div class="label-line"><label for="source">Compare prices</label>{help_tip('source', 'Price comparison source', 'Enter competitor prices for a current market comparison, or view historical selling prices recorded for the exact item selected above. Historical item prices are not competitor prices.')}</div><select id="source" name="source"><option value="manual"{' selected' if source == 'manual' else ''}>I will enter competitor prices</option><option value="historical"{' selected' if source == 'historical' else ''}>Show this item's historical prices</option></select></div>
<div id="manual-market" class="field"><div class="label-line"><label for="competitors">Competitor prices</label>{help_tip('competitors', 'Competitor prices', 'Enter one or more prices separated by commas. Compare similar products and make sure the currency and product size or unit match.')}</div><input id="competitors" name="competitors" placeholder="e.g. 22.50, 24.00, 27.99" value="{html.escape(values.get('competitors',[''])[0], quote=True)}"><div class="hint">Enter one or more prices, separated by commas.</div></div>
<div id="historical-market" class="notice">Shows the recorded selling-price median and range for the exact item selected above, using UK transaction data from 2010–2011. This is historical sales data, not competitor pricing or a current market quote. For a true competitor comparison, enter prices manually.</div>
<div class="notice">Competitor prices help with comparison. They do not tell us what customers will buy.</div></div>
<input type="hidden" name="analyze" value="1"><button class="button" type="submit">Show my pricing guidance</button></form></section>
<section>{result or '<div class="card"><h2>Your pricing snapshot</h2><p class="sub">Your results and recommendations will appear here.</p><div class="notice" style="margin-top:18px">Use your own figures, or load the demo to see how it works.</div></div>'}</section></div>"""
    return page(content)


def render_price_chart(price, cost, currency, benchmark=None, benchmark_label=""):
    """Render a small same-scale horizontal bar chart using only HTML and CSS."""
    rows = [
        ("Current selling price", price, "chart-current"),
        ("Unit cost", cost, "chart-cost"),
    ]
    if benchmark is not None:
        rows.append((benchmark_label, benchmark, "chart-reference"))
    scale_max = max((value for _, value, _ in rows), default=1) or 1
    bars = []
    for label, value, color in rows:
        width = min(100, max(0, value / scale_max * 100))
        bars.append(
            f'<div class="chart-row"><div class="chart-label"><span>{html.escape(label)}</span>'
            f'<strong>{money(value, currency)}</strong></div><div class="chart-track" aria-hidden="true">'
            f'<span class="chart-fill {color}" style="width:{width:.2f}%"></span></div></div>'
        )
    description = "; ".join(f"{label}: {money(value, currency)}" for label, value, _ in rows)
    note = "The reference bar is historical or user-entered; it is not a demand prediction." if benchmark is not None else "Compare your selling price with the cost of one unit."
    return (
        f'<div class="price-chart" role="img" aria-label="Bar chart. {html.escape(description, quote=True)}">'
        '<h3>Price comparison per unit</h3>'
        f'<p class="chart-note">Each bar uses the same scale. {note}</p>'
        f'{"".join(bars)}<div class="chart-axis"><span>{money(0, currency)}</span>'
        f'<span>{money(scale_max, currency)}</span></div></div>'
    )


def render_results(values):
    product = values.get("product", [""])[0].strip() or "Your product"
    cost = safe_float(values, "cost")
    price = safe_float(values, "price")
    fixed_raw = values.get("fixed", [""])[0].strip()
    fixed = 0.0 if not fixed_raw else safe_float(values, "fixed")
    volume = safe_float(values, "volume")
    target_raw = values.get("target", [""])[0].strip()
    target_pct = 25.0 if not target_raw else safe_float(values, "target")
    currency = values.get("currency", ["€"])[0]
    if (
        cost is None or price is None or volume is None or fixed is None or target_pct is None
        or cost < 0 or price <= 0 or volume < 0 or not volume.is_integer() or fixed < 0
        or target_pct < 0 or target_pct > 90
        or max(cost, price, fixed, volume) > 1_000_000_000_000
        or currency not in ("€", "$", "£", "R$")
    ):
        raise ValueError("Enter a valid price, non-negative costs, and a whole-number sales volume. Target margin must be between 0 and 90%.")

    source = values.get("source", ["manual"])[0]
    if source not in ("manual", "historical"):
        raise ValueError("Choose a valid price comparison source.")
    competitor_prices = []
    historical = None
    source_note = "Competitor prices entered by you"
    benchmark_label = "Competitor price average"
    benchmark_details = ""
    if source == "historical":
        historical = PRODUCT_REFERENCE.get(product.casefold())
        if historical is None:
            raise ValueError("No historical prices were found for that name. Choose an item from the product suggestions, or switch to manual competitor prices.")
        benchmark = historical["median_price"]
        benchmark_label = "Historical median sale price for this item"
        benchmark_details = (
            f'Observed range: {money(historical["min_price"], currency)} to '
            f'{money(historical["max_price"], currency)}; '
            f'{historical["transaction_rows"]:,} recorded sales; latest record '
            f'{historical["latest_transaction"]}'
        )
        source_note = "Historical sales for the exact item description"
    else:
        raw = values.get("competitors", [""])[0]
        if raw.strip():
            try:
                competitor_prices = [float(part.strip()) for part in raw.split(",") if part.strip()]
                if any(not math.isfinite(n) or n <= 0 or n > 1_000_000_000_000 for n in competitor_prices):
                    raise ValueError
            except ValueError:
                raise ValueError("Competitor prices must be positive numbers separated by commas.")
        benchmark = sum(competitor_prices) / len(competitor_prices) if competitor_prices else None
        benchmark_details = f"Based on {len(competitor_prices)} prices you entered" if benchmark is not None else ""

    gross_unit = price - cost
    margin_pct = gross_unit / price * 100
    gross_total = gross_unit * volume
    after_fixed = gross_total - fixed
    target_price = cost / (1 - target_pct / 100) if target_pct > 0 else cost
    advice = []
    if price <= cost:
        advice.append(("Your current price does not cover the unit cost. Review costs or price before selling at this level.", f"{money(price, currency)} selling price - {money(cost, currency)} unit cost = {money(gross_unit, currency)} gross profit per unit."))
    elif margin_pct < target_pct:
        advice.append((f"Your gross margin is {margin_pct:.1f}%, below your {target_pct:.0f}% target. A price of about {money(target_price, currency)} would reach that target before other costs.", f"Margin = (selling price - unit cost) ÷ selling price = ({money(price, currency)} - {money(cost, currency)}) ÷ {money(price, currency)}. Target price = unit cost ÷ (1 - target margin) = {money(cost, currency)} ÷ (1 - {target_pct:.0f}%) = {money(target_price, currency)}."))
    else:
        advice.append((f"Your gross margin is {margin_pct:.1f}%, meeting your {target_pct:.0f}% target based on unit cost alone.", f"Margin = (selling price - unit cost) ÷ selling price = ({money(price, currency)} - {money(cost, currency)}) ÷ {money(price, currency)}. This does not include other variable costs."))
    if benchmark is not None and source == "historical":
        gap = (price - benchmark) / benchmark * 100
        direction = "above" if gap > 0 else "below" if gap < 0 else "in line with"
        advice.append((f"Your price is {abs(gap):.1f}% {direction} this item's historical median of {money(benchmark, currency)}.", f"This median uses {historical['transaction_rows']:,} recorded sale-price entries for the exact product description. The recorded range was {money(historical['min_price'], currency)} to {money(historical['max_price'], currency)}. These are past sales, not competitor quotes or current market prices."))
    elif benchmark is not None:
        gap = (price - benchmark) / benchmark * 100
        direction = "above" if gap > 0 else "below" if gap < 0 else "in line with"
        advice.append((f"Your price is {abs(gap):.1f}% {direction} the competitor average of {money(benchmark, currency)}.", f"Average = sum of {len(competitor_prices)} reference prices ÷ {len(competitor_prices)}. Price difference = (your price - average) ÷ average = ({money(price, currency)} - {money(benchmark, currency)}) ÷ {money(benchmark, currency)}. This is a comparison only, not evidence of demand."))
    else:
        advice.append(("Add competitor prices to see how your current price compares with your chosen references.", "No competitor prices were provided, so PriceWise cannot calculate a comparison."))
    if after_fixed < 0:
        advice.append((f"At {volume:,.0f} units, estimated profit after fixed costs is {money(after_fixed, currency)}. Review your price, unit cost, sales volume, or fixed costs.", f"({money(price, currency)} selling price - {money(cost, currency)} unit cost) × {volume:,.0f} units - {money(fixed, currency)} fixed costs. Other expenses are excluded."))
    else:
        advice.append((f"At {volume:,.0f} units, estimated profit after fixed costs is {money(after_fixed, currency)}. This is before other expenses, so it is not net profit.", f"({money(price, currency)} selling price - {money(cost, currency)} unit cost) × {volume:,.0f} units - {money(fixed, currency)} fixed costs."))

    benchmark_card = f'<div class="metric"><small>{benchmark_label}</small><strong>{money(benchmark, currency)}</strong><small>{html.escape(benchmark_details)}</small></div>' if benchmark is not None else ""
    chart_reference_label = "Historical median (same item)" if source == "historical" else "Competitor average (manual)"
    price_chart = render_price_chart(price, cost, currency, benchmark, chart_reference_label if benchmark is not None else "")
    sample_warning = '<div class="notice" style="margin-top:12px">These exact-item sales records are historical (2010–2011), not competitor prices or current market quotes. The workbook has no explicit currency field; the selected symbol does not convert values. Confirm the currency before comparing.</div>' if source == "historical" else ""
    comparison_note = "Historical sales reference only; not a current competitor price." if source == "historical" else "Competitor prices are reference points, not demand forecasts."
    advice_html = "".join(f'<li><strong>{html.escape(headline)}</strong><small>{html.escape(explanation)}</small></li>' for headline, explanation in advice)
    return f"""<div class="card"><div class="result-title"><h2>{html.escape(product)}</h2><span class="badge">Your snapshot</span></div>
<div class="metric"><small>Gross profit per unit</small><strong>{money(gross_unit, currency)}</strong><small>Selling price minus unit cost</small></div>
<div class="metric"><small>Gross margin</small><strong>{margin_pct:.1f}%</strong><small>Gross profit per unit divided by selling price</small></div>
{benchmark_card}
<div class="metric"><small>Estimated profit after fixed costs</small><strong>{money(after_fixed, currency)}</strong><small>{volume:,.0f} units in your stated period; before other expenses</small></div>
{price_chart}
<h2 style="margin-top:20px">Recommendations</h2><ul class="advice">{advice_html}</ul>
<p class="hint" style="margin-top:15px">{html.escape(source_note)}. {comparison_note}</p>{sample_warning}
<div class="notice" style="margin-top:12px">Calculations use your inputs. They exclude unentered fees, tax, shipping, overhead, and customer response.</div></div>"""


class PriceWiseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/products":
            query = parse_qs(request.query).get("q", [""])[0].strip().casefold()
            query = query[:120]
            matches = [name for name, folded_name in PRODUCT_SEARCH_INDEX if not query or query in folded_name][:30]
            self.send_body(json.dumps(matches, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            return
        if request.path == "/app.js":
            self.send_body(APP_JS.encode("utf-8"), "text/javascript; charset=utf-8")
            return
        if request.path == "/favicon.ico":
            self.send_body(b"", "image/x-icon", status=204)
            return
        if request.path != "/":
            self.send_body(b"Not found", "text/plain; charset=utf-8", status=404)
            return
        self.send_body(page(render_form({})).encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 200_000:
                raise ValueError
            payload = self.rfile.read(size).decode("utf-8")
            values = parse_qs(payload, keep_blank_values=True)
            content = render_form(values)
        except (ValueError, UnicodeDecodeError):
            content = render_form({}, error="Please check the values and try again.")
        self.send_body(content.encode("utf-8"), "text/html; charset=utf-8")

    def send_body(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if status != 204:
            self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body and status != 204:
            self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


APP_JS = r"""
const sourceSelect = document.getElementById('source');
const manualGroup = document.getElementById('manual-market');
const historicalGroup = document.getElementById('historical-market');
const productInput = document.getElementById('product');
const productMenu = document.getElementById('product-menu');
let productSearchRequest = 0;

function updateCompetitorFields() {
  const useHistory = sourceSelect.value === 'historical';
  manualGroup.hidden = useHistory;
  historicalGroup.hidden = !useHistory;
}

function closeProductMenu() {
  productSearchRequest += 1;
  productMenu.hidden = true;
  productInput.setAttribute('aria-expanded', 'false');
}

async function showProductMatches(query) {
  const requestNumber = ++productSearchRequest;
  try {
    const response = await fetch('/products?q=' + encodeURIComponent(query));
    if (!response.ok) throw new Error('Product search failed');
    const products = await response.json();
    if (requestNumber !== productSearchRequest) return;
    productMenu.replaceChildren();
    if (!products.length) {
      const empty = document.createElement('div');
      empty.className = 'picker-status';
      empty.textContent = 'No match found. You can keep typing your own product name.';
      productMenu.appendChild(empty);
    } else {
      for (const name of products) {
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'picker-option';
        option.setAttribute('role', 'option');
        option.textContent = name;
        option.addEventListener('mousedown', event => event.preventDefault());
        option.addEventListener('keydown', event => {
          const options = [...productMenu.querySelectorAll('.picker-option')];
          const index = options.indexOf(option);
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            options[Math.min(index + 1, options.length - 1)].focus();
          } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            if (index === 0) productInput.focus();
            else options[index - 1].focus();
          } else if (event.key === 'Escape') {
            closeProductMenu();
            productInput.focus();
          }
        });
        option.addEventListener('click', () => {
          productInput.value = name;
          closeProductMenu();
          productInput.focus();
        });
        productMenu.appendChild(option);
      }
      const count = document.createElement('div');
      count.className = 'picker-status';
      count.textContent = 'Showing ' + products.length + (products.length === 30 ? ' matches. Type more to narrow the list.' : ' matches.');
      productMenu.appendChild(count);
    }
    productMenu.hidden = false;
    productInput.setAttribute('aria-expanded', 'true');
  } catch (_) {
    if (requestNumber !== productSearchRequest) return;
    productMenu.replaceChildren();
    const message = document.createElement('div');
    message.className = 'picker-status';
    message.textContent = 'Product suggestions are unavailable. You can still type a product name.';
    productMenu.appendChild(message);
    productMenu.hidden = false;
  }
}

if (sourceSelect) {
  sourceSelect.addEventListener('change', updateCompetitorFields);
  updateCompetitorFields();
}
if (productInput) {
  let searchTimer;
  productInput.addEventListener('focus', () => showProductMatches(productInput.value.trim()));
  productInput.addEventListener('click', () => showProductMatches(productInput.value.trim()));
  productInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => showProductMatches(productInput.value.trim()), 120);
  });
  productInput.addEventListener('keydown', event => {
    const options = [...productMenu.querySelectorAll('.picker-option')];
    const activeIndex = options.indexOf(document.activeElement);
    if (event.key === 'ArrowDown' && options.length) {
      event.preventDefault();
      options[Math.min(activeIndex + 1, options.length - 1)].focus();
    } else if (event.key === 'Escape') {
      closeProductMenu();
    }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.picker')) closeProductMenu();
  });
}

const exampleButton = document.getElementById('load-example');
if (exampleButton) {
  exampleButton.addEventListener('click', () => {
    document.getElementById('product').value = 'WHITE HANGING HEART T-LIGHT HOLDER';
    document.getElementById('cost').value = '1.50';
    document.getElementById('price').value = '3.50';
    document.getElementById('fixed').value = '50';
    document.getElementById('volume').value = '100';
    document.getElementById('target').value = '30';
    document.getElementById('currency').value = '€';
    document.getElementById('source').value = 'historical';
    document.getElementById('competitors').value = '3.49, 3.75, 3.99';
    updateCompetitorFields();
    closeProductMenu();
  });
}
"""


if __name__ == "__main__":
    print(f"PriceWise is ready at http://{HOST}:{PORT}")
    print("Press Ctrl+C in this window to stop the website.")
    HTTPServer((HOST, PORT), PriceWiseHandler).serve_forever()
