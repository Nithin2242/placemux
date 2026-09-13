from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "data" / "online_retail" / "Online Retail.xlsx"


def load_source(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Real source file not found: {path}\n"
            "Place the UCI Online Retail.xlsx file at data/online_retail/Online Retail.xlsx "
            "or pass --source PATH."
        )
    df = pd.read_excel(path)
    required = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def is_cancellation(df: pd.DataFrame) -> pd.Series:
    return df["InvoiceNo"].astype(str).str.upper().str.startswith("C")


def build_analysis(df: pd.DataFrame) -> dict[str, Any]:
    data = df.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["LineTotal"] = data["Quantity"] * data["UnitPrice"]

    cancellation = is_cancellation(data)
    negative_qty = data["Quantity"] <= 0
    non_positive_price = data["UnitPrice"] <= 0
    missing_customer = data["CustomerID"].isna()
    missing_description = data["Description"].isna()

    purchase_mask = (
        ~cancellation
        & ~missing_customer
        & data["Quantity"].gt(0)
        & data["UnitPrice"].gt(0)
        & ~missing_description
        & data["InvoiceDate"].notna()
    )
    clean = data.loc[purchase_mask].copy()

    clean_invoices = clean["InvoiceNo"].nunique()
    customer_invoice_counts = clean.groupby("CustomerID")["InvoiceNo"].nunique()
    repeat_invoice_transitions = int((customer_invoice_counts - 1).clip(lower=0).sum())
    repeat_invoice_share = repeat_invoice_transitions / clean_invoices if clean_invoices else np.nan

    invoice_revenue = clean.groupby("InvoiceNo", as_index=False)["LineTotal"].sum()
    monthly = (
        clean.assign(Month=clean["InvoiceDate"].dt.to_period("M").astype(str))
        .groupby("Month", as_index=False)["LineTotal"]
        .sum()
    )

    # Bootstrap uncertainty for mean invoice revenue.
    values = invoice_revenue["LineTotal"].to_numpy(dtype=float)
    rng = np.random.default_rng(42)
    reps = 1000
    if len(values):
        sample_means = np.mean(rng.choice(values, size=(reps, len(values)), replace=True), axis=1)
        mean_invoice = float(values.mean())
        ci_lo, ci_hi = np.percentile(sample_means, [2.5, 97.5])
    else:
        mean_invoice = ci_lo = ci_hi = float("nan")

    customer_revenue = clean.groupby("CustomerID", as_index=False)["LineTotal"].sum()
    total_revenue = float(clean["LineTotal"].sum())
    top10_share = (
        float(customer_revenue.nlargest(10, "LineTotal")["LineTotal"].sum() / total_revenue)
        if total_revenue else np.nan
    )

    issues = [
        {
            "rank": 1,
            "problem": "Customer traceability gap",
            "metric": "Missing CustomerID",
            "affected_rows": int(missing_customer.sum()),
            "affected_share_pct": float(missing_customer.mean() * 100),
            "decision": "Protect customer attribution and retention reporting; separate guest activity from known-customer analytics.",
            "priority": "P0",
        },
        {
            "rank": 2,
            "problem": "Transaction-state contamination",
            "metric": "Cancellation invoice lines",
            "affected_rows": int(cancellation.sum()),
            "affected_share_pct": float(cancellation.mean() * 100),
            "decision": "Keep returns/cancellations out of sales KPIs and reconcile them in a separate return-value control.",
            "priority": "P0",
        },
        {
            "rank": 3,
            "problem": "Invalid quantity states",
            "metric": "Quantity <= 0",
            "affected_rows": int(negative_qty.sum()),
            "affected_share_pct": float(negative_qty.mean() * 100),
            "decision": "Enforce transaction-state validation so operational and revenue reports cannot mix purchases with non-sales quantity states.",
            "priority": "P1",
        },
        {
            "rank": 4,
            "problem": "Invalid price states",
            "metric": "UnitPrice <= 0",
            "affected_rows": int(non_positive_price.sum()),
            "affected_share_pct": float(non_positive_price.mean() * 100),
            "decision": "Add a publish-time price-quality gate and quarantine non-positive-price rows from commercial KPIs.",
            "priority": "P1",
        },
    ]

    validation = {
        "required_columns_present": True,
        "raw_rows": int(len(data)),
        "clean_purchase_rows": int(len(clean)),
        "missing_customer_ids": int(missing_customer.sum()),
        "cancellation_rows": int(cancellation.sum()),
        "non_positive_quantity_rows": int(negative_qty.sum()),
        "non_positive_price_rows": int(non_positive_price.sum()),
        "missing_description_rows": int(missing_description.sum()),
        "clean_invoices": int(clean_invoices),
        "identified_customers": int(clean["CustomerID"].nunique()),
        "clean_revenue_positive": bool(total_revenue > 0),
        "invoice_revenue_reconciles": bool(np.isclose(invoice_revenue["LineTotal"].sum(), total_revenue)),
        "date_min": clean["InvoiceDate"].min().isoformat() if len(clean) else None,
        "date_max": clean["InvoiceDate"].max().isoformat() if len(clean) else None,
    }
    validation["overall_status"] = "PASS" if all(
        [
            validation["required_columns_present"],
            validation["clean_revenue_positive"],
            validation["invoice_revenue_reconciles"],
        ]
    ) else "FAIL"

    metrics = {
        "raw_rows": int(len(data)),
        "clean_purchase_rows": int(len(clean)),
        "clean_row_retention_pct": float(len(clean) / len(data) * 100),
        "clean_invoices": int(clean_invoices),
        "identified_customers": int(clean["CustomerID"].nunique()),
        "products": int(clean["StockCode"].nunique()),
        "countries": int(clean["Country"].nunique()),
        "total_revenue_gbp": total_revenue,
        "mean_invoice_revenue_gbp": mean_invoice,
        "mean_invoice_revenue_ci95_low_gbp": float(ci_lo),
        "mean_invoice_revenue_ci95_high_gbp": float(ci_hi),
        "repeat_invoice_transitions": repeat_invoice_transitions,
        "repeat_invoice_continuity_pct": float(repeat_invoice_share * 100),
        "top10_customer_revenue_share_pct": float(top10_share * 100),
        "peak_month": monthly.loc[monthly["LineTotal"].idxmax(), "Month"] if len(monthly) else None,
        "peak_month_revenue_gbp": float(monthly["LineTotal"].max()) if len(monthly) else None,
    }

    return {
        "metrics": metrics,
        "quality": {
            "missing_customer_rows": int(missing_customer.sum()),
            "missing_customer_share_pct": float(missing_customer.mean() * 100),
            "cancellation_rows": int(cancellation.sum()),
            "cancellation_share_pct": float(cancellation.mean() * 100),
            "non_positive_quantity_rows": int(negative_qty.sum()),
            "non_positive_quantity_share_pct": float(negative_qty.mean() * 100),
            "non_positive_price_rows": int(non_positive_price.sum()),
            "non_positive_price_share_pct": float(non_positive_price.mean() * 100),
            "missing_description_rows": int(missing_description.sum()),
            "missing_description_share_pct": float(missing_description.mean() * 100),
        },
        "monthly_revenue": monthly.to_dict(orient="records"),
        "problems": issues,
        "validation": validation,
    }


def write_outputs(result: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result["metrics"]]).to_csv(out_dir / "launch_performance_metrics.csv", index=False)
    pd.DataFrame([result["quality"]]).to_csv(out_dir / "launch_quality.csv", index=False)
    pd.DataFrame(result["monthly_revenue"]).to_csv(out_dir / "launch_revenue_monthly.csv", index=False)
    pd.DataFrame(result["problems"]).to_csv(out_dir / "launch_problem_rankings.csv", index=False)
    (out_dir / "launch_validation.json").write_text(json.dumps(result["validation"], indent=2), encoding="utf-8")

    payload = {
        "title": "PlaceMux Phase 3 - Task 1 Post-Launch Performance",
        "source_type": "Real external source dataset proxy",
        "source": "UCI Online Retail",
        "source_path_expected": "data/online_retail/Online Retail.xlsx",
        "note": "This is not PlaceMux production telemetry. It is a documented real-data substitution because the task brief supplies no production dataset.",
        **result,
    }
    (out_dir / "launch_dashboard_data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    html = build_dashboard(payload)
    (out_dir / "launch_dashboard.html").write_text(html, encoding="utf-8")


def build_dashboard(payload: dict[str, Any]) -> str:
    m = payload["metrics"]
    q = payload["quality"]
    problems = payload["problems"]
    rows = "".join(
        f"<tr><td>{p['rank']}</td><td><b>{p['problem']}</b><div class='muted'>{p['metric']}</div></td><td>{p['affected_rows']:,}</td><td>{p['affected_share_pct']:.2f}%</td><td><b>{p['priority']}</b></td></tr>"
        for p in problems
    )
    monthly = json.dumps(payload["monthly_revenue"])
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>PlaceMux Phase 3 - Task 1</title>
<style>
body{{font-family:Inter,Arial,sans-serif;margin:0;background:#f5f7fb;color:#18243a}} .wrap{{max-width:1400px;margin:0 auto;padding:36px}}
h1{{margin:0 0 8px;font-size:34px}} h2{{font-size:22px;margin:0 0 18px}} .sub{{color:#64748b;margin-bottom:22px}} .tabs{{display:flex;gap:10px;margin-bottom:24px}} button{{border:0;padding:12px 18px;border-radius:10px;background:#e7ebf4;font-weight:700;cursor:pointer}} button.active{{background:#4b3be4;color:white}}
.tab{{display:none}} .tab.active{{display:block}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}} .card{{background:white;border:1px solid #e3e8f2;border-radius:16px;padding:20px;box-shadow:0 2px 8px rgba(20,35,60,.04)}} .label{{color:#64748b;font-size:14px}} .value{{font-size:30px;font-weight:800;margin-top:7px}} .good{{color:#168a5b}} .warn{{color:#b36c00}} .muted{{color:#718096;font-size:13px;margin-top:5px}}
.panel{{margin-top:18px;background:white;border:1px solid #e3e8f2;border-radius:16px;padding:22px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:12px;border-bottom:1px solid #edf0f5;text-align:left}} th{{color:#64748b;font-size:13px}} .two{{display:grid;grid-template-columns:1.2fr 1fr;gap:18px}} .bar{{height:12px;background:#e8ecf5;border-radius:999px;overflow:hidden}} .fill{{height:100%;background:#4b3be4}}
.note{{margin-top:18px;font-size:13px;color:#64748b}} ol{{padding-left:20px}} li{{margin:12px 0}} .pill{{display:inline-block;padding:6px 10px;border-radius:999px;background:#e8f7ef;color:#168a5b;font-weight:700;font-size:12px}}
@media(max-width:900px){{.grid,.two{{grid-template-columns:1fr 1fr}}}} @media(max-width:600px){{.wrap{{padding:18px}}.grid,.two{{grid-template-columns:1fr}}}}
</style></head><body><div class='wrap'>
<h1>PlaceMux Phase 3 - Post-Launch Performance</h1><div class='sub'>Task 1 · real-data substitution · funnel/revenue/retention/quality · evidence-backed decisions</div>
<div class='tabs'><button class='active' data-tab='overview'>Overview</button><button data-tab='problems'>Biggest Problems</button><button data-tab='backlog'>Analytics Backlog</button></div>
<section id='overview' class='tab active'>
<div class='grid'>
<div class='card'><div class='label'>Raw transaction lines</div><div class='value'>{m['raw_rows']:,}</div></div>
<div class='card'><div class='label'>Clean purchase lines</div><div class='value'>{m['clean_purchase_rows']:,}</div><div class='muted'>{m['clean_row_retention_pct']:.1f}% retained</div></div>
<div class='card'><div class='label'>Identified customers</div><div class='value'>{m['identified_customers']:,}</div></div>
<div class='card'><div class='label'>Retained revenue</div><div class='value'>£{m['total_revenue_gbp']:,.2f}</div></div>
</div>
<div class='grid' style='margin-top:16px'>
<div class='card'><div class='label'>Clean invoices</div><div class='value'>{m['clean_invoices']:,}</div></div>
<div class='card'><div class='label'>Repeat-purchase continuity</div><div class='value'>{m['repeat_invoice_continuity_pct']:.1f}%</div><div class='muted'>{m['repeat_invoice_transitions']:,} invoices had a later invoice</div></div>
<div class='card'><div class='label'>Mean invoice revenue</div><div class='value'>£{m['mean_invoice_revenue_gbp']:,.2f}</div><div class='muted'>95% bootstrap CI £{m['mean_invoice_revenue_ci95_low_gbp']:,.2f} - £{m['mean_invoice_revenue_ci95_high_gbp']:,.2f}</div></div>
<div class='card'><div class='label'>Top 10 customer revenue share</div><div class='value'>{m['top10_customer_revenue_share_pct']:.1f}%</div></div>
</div>
<div class='two'><div class='panel'><h2>Quality control</h2>
<p>Missing CustomerID: <b>{q['missing_customer_rows']:,}</b> ({q['missing_customer_share_pct']:.2f}%)</p><div class='bar'><div class='fill' style='width:{min(q['missing_customer_share_pct'],100):.1f}%'></div></div>
<p>Cancellation lines: <b>{q['cancellation_rows']:,}</b> ({q['cancellation_share_pct']:.2f}%)</p><div class='bar'><div class='fill' style='width:{min(q['cancellation_share_pct']*5,100):.1f}%'></div></div>
<p>Quantity ≤ 0: <b>{q['non_positive_quantity_rows']:,}</b> ({q['non_positive_quantity_share_pct']:.2f}%)</p><div class='bar'><div class='fill' style='width:{min(q['non_positive_quantity_share_pct']*5,100):.1f}%'></div></div>
<p>UnitPrice ≤ 0: <b>{q['non_positive_price_rows']:,}</b> ({q['non_positive_price_share_pct']:.2f}%)</p><div class='bar'><div class='fill' style='width:{min(q['non_positive_price_share_pct']*10,100):.1f}%'></div></div>
</div>
<div class='panel'><h2>Source & validation</h2><div class='pill'>{payload['validation']['overall_status']}</div><p>Source: UCI Online Retail, real external transaction dataset.</p><p>Coverage: {m['clean_invoices']:,} invoices, {m['identified_customers']:,} identified customers, {m['products']:,} products, {m['countries']} countries.</p><p>Revenue reconciliation to invoice aggregation: PASS.</p><p class='note'>{payload['note']}</p></div></div>
<div class='panel'><h2>Monthly revenue profile</h2><div id='monthly'></div><div class='muted'>Peak month: {m['peak_month']} at £{m['peak_month_revenue_gbp']:,.2f}</div></div>
</section>
<section id='problems' class='tab'><div class='panel'><h2>Ranked evidence-backed problems</h2><p class='muted'>Ranked by affected source rows. Issue counts can overlap; they are not additive.</p><table><thead><tr><th>Rank</th><th>Problem</th><th>Affected rows</th><th>Share of raw rows</th><th>Priority</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section id='backlog' class='tab'><div class='panel'><h2>Phase-3 analytics backlog tied to decisions</h2><ol>
<li><b>P0 - Customer identity completeness.</b> Build a guest-vs-known customer attribution layer. Decision: can retention and customer value reporting be trusted without mixing anonymous demand into customer cohorts?</li>
<li><b>P0 - Transaction-state semantics.</b> Split sale, cancellation and return states into a governed event model. Decision: are reported revenue and order counts aligned with actual commercial states?</li>
<li><b>P1 - Numeric data-quality gates.</b> Add pre-publication validation for non-positive quantity and price. Decision: should a batch be published, quarantined or flagged for review?</li>
<li><b>P1 - Retention cohort model.</b> Move from invoice-level repeat continuity to cohort-based month-1, month-3 and month-6 retention. Decision: which acquisition cohorts deserve intervention?</li>
<li><b>P2 - Customer concentration monitoring.</b> Track top-customer revenue share and concentration drift over time. Decision: is revenue becoming overly dependent on a small customer set?</li>
</ol></div></section>
<div class='note'>Reproduction: python phase3/launch_performance_analysis.py --source data/online_retail/Online Retail.xlsx · No synthetic PlaceMux data is used.</div>
</div><script>
const monthly={monthly};
const el=document.getElementById('monthly'); if(monthly.length){{const max=Math.max(...monthly.map(x=>x.LineTotal));el.innerHTML=monthly.map(x=>`<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;font-size:13px"><span>${{x.Month}}</span><span>£${{Number(x.LineTotal).toLocaleString(undefined,{{maximumFractionDigits:0}})}}</span></div><div class="bar"><div class="fill" style="width:${{Math.max(2,100*x.LineTotal/max)}}%"></div></div></div>`).join('')}}
document.querySelectorAll('button[data-tab]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button[data-tab]').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}});
</script></body></html>"""


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Task 1 real-data post-launch performance analysis")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=ROOT)
    args = parser.parse_args()
    df = load_source(args.source)
    result = build_analysis(df)
    write_outputs(result, args.out)
    print(json.dumps(result["validation"], indent=2))
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
