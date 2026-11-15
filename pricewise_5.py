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
:root {{ color-scheme:dark; --bg:#070a09; --surface:#101714; --ink:#f1f6f3; --muted:#9aa9a2; --line:#26352f; --teal:#27b394; --bright:#53d2ad; --pale:#102923; }}
* {{ box-sizing:border-box; }} html {{ min-height:100%; background:var(--bg); }}
body {{ min-height:100vh; margin:0; color:var(--ink); background:radial-gradient(ellipse at 80% 7%,#0d3028 0,transparent 34%),radial-gradient(ellipse at 4% 60%,#10211c 0,transparent 30%),var(--bg); font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
header {{ border-bottom:1px solid #ffffff12; background:#080c0be8; }} .top {{ max-width:1180px; min-height:76px; margin:auto; padding:16px 28px; display:flex; align-items:center; justify-content:space-between; gap:18px; }}
.brand {{ display:flex; align-items:center; gap:11px; font-weight:850; font-size:20px; letter-spacing:-.7px; }} .brand:before {{ content:"PW"; display:grid; place-items:center; width:36px; height:36px; border:1px solid #36c7a044; border-radius:12px; background:linear-gradient(145deg,#1b8066,#10483b); color:#eafff8; font-size:12px; box-shadow:0 6px 24px #12a47c30; }} .brand span {{ color:var(--bright); }}
.tag {{ display:flex; align-items:center; gap:9px; color:var(--muted); font-size:12px; }} .tag:before {{ content:""; width:7px; height:7px; border-radius:50%; background:var(--bright); box-shadow:0 0 12px var(--bright); }}
main {{ max-width:1180px; margin:auto; padding:54px 28px 38px; }} .intro {{ margin:0 auto 34px; max-width:790px; text-align:center; }} .intro:before {{ content:"PRICING, WITH CLARITY"; display:inline-flex; margin-bottom:17px; padding:6px 11px; border:1px solid #36c7a044; border-radius:99px; background:#0c211b; color:var(--bright); font-size:10px; font-weight:800; letter-spacing:.16em; }}
h1 {{ margin:0 0 13px; font-size:clamp(34px,5vw,56px); line-height:1.03; letter-spacing:-2.6px; }} p {{ margin:0 0 12px; }} .sub {{ max-width:650px; margin:0 auto; color:var(--muted); font-size:16px; }}
.layout {{ display:grid; grid-template-columns:minmax(0,1.08fr) minmax(300px,.92fr); gap:22px; align-items:start; }} .card {{ position:relative; padding:26px; border:1px solid #ffffff12; border-radius:20px; background:linear-gradient(145deg,#121a17f5,#0d1311f5); box-shadow:0 22px 65px #0008,inset 0 1px #ffffff08; }}
h2 {{ margin:0 0 12px; font-size:18px; font-weight:750; letter-spacing:-.35px; }} .section {{ margin:22px 0; padding:0 0 20px; border-bottom:1px solid var(--line); }} .section:last-child {{ margin-bottom:0; padding:0; border:0; }} .result-title {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
label {{ display:block; margin:0 0 7px; color:#d8e2dd; font-size:12px; font-weight:700; letter-spacing:.025em; }} .label-line {{ display:flex; align-items:center; gap:7px; margin:0 0 7px; }} .label-line label {{ margin:0; }}
input,select {{ width:100%; min-height:46px; padding:11px 13px; border:1px solid #30413a; border-radius:10px; outline:none; background:#090e0c; color:var(--ink); font:inherit; transition:border-color .18s,box-shadow .18s; }} input::placeholder {{ color:#66766f; }} input:hover,select:hover {{ border-color:#4b6a5f; }} input:focus,select:focus {{ border-color:var(--teal); box-shadow:0 0 0 3px #27b39420; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }} .field {{ margin-bottom:15px; }} .hint {{ margin-top:6px; color:#82928b; font-size:11px; line-height:1.45; }}
.help-button {{ position:relative; display:inline-grid; place-items:center; flex:none; width:16px; height:16px; padding:0; border:1px solid #54796d; border-radius:50%; background:#10231d; color:var(--bright); font:inherit; font-size:10px; cursor:help; }} .help-popover {{ display:none; position:absolute; z-index:10; left:50%; bottom:calc(100% + 8px); transform:translateX(-50%); width:220px; padding:10px 12px; border:1px solid #33483f; border-radius:10px; background:#050807; color:white; font-size:12px; line-height:1.45; text-align:left; box-shadow:0 10px 25px #000a; }} .help-button:hover .help-popover,.help-button:focus .help-popover {{ display:block; }}
.button {{ display:flex; justify-content:center; width:100%; min-height:50px; margin-top:18px; padding:13px 16px; border:1px solid #59d5b1; border-radius:11px; background:linear-gradient(115deg,#16866c,#20a47f); color:#f4fffa; font:inherit; font-weight:800; cursor:pointer; box-shadow:0 8px 22px #16866c30; transition:transform .18s,filter .18s; }} .button:hover {{ transform:translateY(-1px); filter:brightness(1.12); }} .mini-button {{ padding:7px 10px; border:1px solid #356457; border-radius:8px; background:#10231d; color:#78d9bc; font:inherit; font-size:11px; font-weight:750; cursor:pointer; }} .mini-button:hover {{ background:#17372c; }}
.metric {{ margin-bottom:11px; padding:16px; border:1px solid #244a3d; border-radius:13px; background:linear-gradient(130deg,#112b22,#10201b); }} .metric small {{ display:block; color:#a8b9b1; font-size:11px; }} .metric strong {{ display:block; margin-top:3px; color:#e7fff5; font-size:25px; letter-spacing:-.7px; }} .badge {{ padding:5px 10px; border:1px solid #2a725d; border-radius:99px; background:#102d24; color:#7be0bf; font-size:11px; font-weight:750; }}
.price-chart {{ margin:18px 0 22px; padding:16px; border:1px solid var(--line); border-radius:13px; background:#0a100e; }} .price-chart h3 {{ margin:0 0 5px; font-size:14px; }} .chart-note {{ margin:0 0 15px; color:var(--muted); font-size:11px; }} .chart-row {{ margin:12px 0; }} .chart-label {{ display:flex; justify-content:space-between; gap:12px; margin-bottom:5px; font-size:12px; }} .chart-label strong {{ white-space:nowrap; }} .chart-track {{ height:9px; overflow:hidden; border-radius:99px; background:#202a26; }} .chart-fill {{ display:block; height:100%; min-width:0; border-radius:99px; }} .chart-current {{ background:linear-gradient(90deg,#16866c,#53d2ad); }} .chart-cost {{ background:#66756f; }} .chart-reference {{ background:#397a70; }} .chart-axis {{ display:flex; justify-content:space-between; margin-top:5px; color:var(--muted); font-size:10px; }}
.notice {{ padding:12px; border:1px solid #263d34; border-radius:10px; background:#0d1914; color:#a6b6ae; font-size:11px; }} .advice {{ margin:0; padding:0; list-style:none; }} .advice li {{ padding:11px 0; border-bottom:1px solid var(--line); }} .advice li:last-child {{ border:0; }} .advice li:before {{ margin-right:9px; color:var(--bright); content:"•"; font-weight:900; }} .advice small {{ display:block; margin:5px 0 0 19px; color:var(--muted); }}
.picker {{ position:relative; }} .picker-menu {{ position:absolute; z-index:5; top:100%; right:0; left:0; max-height:250px; overflow:auto; margin-top:5px; border:1px solid #30483d; border-radius:10px; background:#0c1310; box-shadow:0 12px 30px #000b; }} .picker-option {{ display:block; width:100%; padding:10px 12px; border:0; background:#0c1310; color:var(--ink); text-align:left; font:inherit; cursor:pointer; }} .picker-option:hover,.picker-option:focus {{ outline:0; background:#173128; }} .picker-status {{ padding:9px 12px; color:var(--muted); font-size:11px; }}
.error {{ margin-bottom:14px; padding:11px 12px; border-radius:9px; background:#351d1a; color:#ffaaa0; }} .field[hidden],[hidden] {{ display:none !important; }} footer {{ margin-top:24px; color:#788881; font-size:11px; text-align:center; }}
@media(max-width:760px) {{ main {{ padding:38px 18px 28px; }} .top {{ min-height:66px; padding:12px 18px; }} .tag {{ font-size:10px; }} .intro {{ margin-bottom:26px; }} .sub {{ font-size:14px; }} .layout {{ grid-template-columns:1fr; }} .card {{ padding:20px; border-radius:16px; }} }} @media(max-width:440px) {{ .top {{ align-items:flex-start; }} .tag {{ max-width:120px; text-align:right; }} .grid2 {{ grid-template-columns:1fr; gap:0; }} h1 {{ letter-spacing:-1.7px; }} }}
/* Art-directed hero treatment */
.brand:before {{ display:none; }}
.intro {{ position:relative; max-width:none; min-height:280px; margin:0 0 30px; padding:34px 0 30px; text-align:left; isolation:isolate; }}
.intro:before {{ margin-bottom:18px; padding:7px 12px; background:#0d241e; }}
.intro:after {{ content:none; display:none; }}
.intro h1 {{ position:relative; max-width:620px; }}
.intro .sub {{ position:relative; max-width:560px; margin:0; }}
@media(max-width:760px) {{ .intro {{ min-height:250px; padding-top:20px; }} .intro:after {{ top:10px; right:-10px; width:46%; height:210px; opacity:.5; }} .intro h1,.intro .sub {{ max-width:78%; }} }}
@media(max-width:440px) {{ .intro {{ min-height:240px; }} .intro:after {{ top:80px; width:58%; height:155px; opacity:.26; }} .intro h1,.intro .sub {{ max-width:100%; }} }}
/* Readable, balanced result dashboard and accessible form actions */
.hint,footer,.chart-note {{ color:#b7c5bf; }}
.tag {{ color:#bdc9c3; }}
.result-card {{ position:sticky; top:18px; }}
.metrics-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:15px; }}
.metrics-grid .metric {{ min-width:0; margin:0; padding:14px; }}
.metrics-grid .metric strong {{ font-size:22px; overflow-wrap:anywhere; }}
.advice {{ margin-top:4px; }}
.advice li {{ padding:14px 0; }}
.advice li strong {{ display:block; font-size:13px; line-height:1.5; }}
.advice-detail {{ margin:8px 0 0 18px; }}
.advice-detail summary {{ width:max-content; color:#7ed9bc; font-size:11px; cursor:pointer; }}
.advice-detail summary:hover {{ color:#c0f7e3; }}
.advice-detail small {{ display:block; margin:7px 0 0; color:#b7c5bf; font-size:11px; line-height:1.55; }}
.button {{ position:sticky; bottom:12px; z-index:4; box-shadow:0 7px 22px #000b,0 0 0 6px #0e1512; }}
@media(max-width:760px) {{ .result-card {{ position:static; }} .metrics-grid {{ gap:8px; }} .metrics-grid .metric {{ padding:12px; }} .button {{ bottom:8px; }} }}
@media(max-width:440px) {{ .metrics-grid {{ grid-template-columns:1fr 1fr; }} .metrics-grid .metric strong {{ font-size:19px; }} }}
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
    product_hint = (
        f"Search {len(PRODUCT_CATALOG):,} item descriptions from Online Retail.xlsx, or type your own product. The dataset has names and sales prices, but no unit costs."
        if PRODUCT_CATALOG else
        "No sample product list is available yet. Type your own product name, or select Load example to try the demo."
    )
    content = f"""
<div class="intro"><h1>Understand your product pricing</h1><p class="sub">Enter a few details to see your margin, compare prices, and get clear guidance. Start with a demo if you want to explore first.</p></div>
<div class="layout"><section class="card"><div class="result-title"><h2>Product details</h2><button class="mini-button" id="load-example" type="button">Load example</button></div><p class="hint">Example costs and prices are illustrative; replace them with your figures.</p>{error_box}
<form method="post" action="/">
<div class="section"><div class="field"><div class="label-line"><label for="product">Product name</label>{help_tip('product', 'Product name', 'Choose a name from the historical product list, or type your own. The product list does not provide unit costs.')}</div><div class="picker"><input id="product" name="product" autocomplete="off" aria-autocomplete="list" aria-controls="product-menu" aria-expanded="false" placeholder="Click to browse or type to search" value="{html.escape(values.get('product',[''])[0], quote=True)}" required><div id="product-menu" class="picker-menu" role="listbox" hidden></div></div><div class="hint">{html.escape(product_hint)}</div></div>
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
    advice_html = "".join(f'<li><strong>{html.escape(headline)}</strong><details class="advice-detail"><summary>Calculation details</summary><small>{html.escape(explanation)}</small></details></li>' for headline, explanation in advice)
    return f"""<div class="card result-card"><div class="result-title"><h2>{html.escape(product)}</h2><span class="badge">Your snapshot</span></div>
<div class="metrics-grid">
<div class="metric"><small>Gross profit per unit</small><strong>{money(gross_unit, currency)}</strong><small>Selling price minus unit cost</small></div>
<div class="metric"><small>Gross margin</small><strong>{margin_pct:.1f}%</strong><small>Profit per unit divided by selling price</small></div>
{benchmark_card}
<div class="metric"><small>Estimated profit after fixed costs</small><strong>{money(after_fixed, currency)}</strong><small>{volume:,.0f} units in your stated period; before other expenses</small></div>
</div>
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
    document.getElementById('source').value = 'manual';
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
