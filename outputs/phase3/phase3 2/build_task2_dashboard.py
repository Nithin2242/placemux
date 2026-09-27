from __future__ import annotations

import argparse
import json
from pathlib import Path


def money(v):
    return f"£{v:,.2f}" if v is not None else "-"


def pct(v):
    return f"{v*100:.2f}%" if v is not None else "-"


def build(snapshot_path, dq_path, validation_path, out_path):
    metrics = json.loads(Path(snapshot_path).read_text())
    dq = json.loads(Path(dq_path).read_text())
    validation = json.loads(Path(validation_path).read_text())

    status = validation.get("overall_status", "UNKNOWN")
    cards = [
        ("Raw transaction lines", f"{metrics['raw_transaction_lines']:,}"),
        ("Valid purchase lines", f"{metrics['valid_purchase_lines']:,}"),
        ("Net revenue proxy", money(metrics['net_revenue_proxy'])),
        ("Identified customers", f"{metrics['identified_customers']:,}"),
        ("Repeat customer rate", pct(metrics['repeat_customer_rate'])),
        ("CustomerID null rate", pct(metrics['customerid_null_rate'])),
    ]

    null_rows = "".join(
        f"<tr><td>{k}</td><td>{v:,}</td></tr>" for k, v in dq["required_field_nulls"].items()
    )
    checks = "".join([
        f"<li>Metric IDs unique: {'PASS' if validation['metric_dictionary_unique_ids'] else 'FAIL'}</li>",
        f"<li>Metric names unique: {'PASS' if validation['metric_dictionary_unique_names'] else 'FAIL'}</li>",
        f"<li>Cross-surface metric parity: {'PASS' if validation['metric_parity_pass'] else 'FAIL'}</li>",
        f"<li>Intentional failure path detected: {'PASS' if validation['failure_path_detected'] else 'FAIL'}</li>",
        f"<li>Volume check: {'PASS' if validation['dq_volume_pass'] else 'FAIL'}</li>",
        f"<li>Duplicate full rows: {validation['duplicate_full_rows']}</li>",
    ])

    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>PlaceMux Task 2 - Semantic Layer</title>
<style>
body{{font-family:Inter,Arial,sans-serif;margin:0;background:#f5f7fb;color:#1e293b}}.wrap{{max-width:1400px;margin:0 auto;padding:36px}}
h1{{margin:0 0 8px;font-size:42px}}.sub{{color:#64748b;font-size:17px;margin-bottom:24px}}.pill{{display:inline-block;padding:8px 14px;border-radius:999px;background:#dcfce7;color:#166534;font-weight:800}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:20px 0}}.card,.panel{{background:#fff;border:1px solid #e2e8f0;border-radius:18px;padding:22px;box-shadow:0 5px 16px rgba(15,23,42,.05)}}
.label{{color:#64748b;font-size:14px}}.value{{font-size:32px;font-weight:800;margin-top:8px}}h2{{margin-top:0;font-size:22px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}}th{{color:#64748b;font-size:14px}}.ok{{color:#15803d;font-weight:800}}.warn{{color:#b45309;font-weight:800}}.note{{background:#eef2ff;border-left:5px solid #4f46e5;padding:14px 16px;border-radius:10px;margin-top:14px}}ul{{line-height:1.8}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class='wrap'>
<h1>PlaceMux Semantic Metric Layer</h1><div class='sub'>Task 2 · Observability Deep-Dive · one definition per metric · quality checks · published dictionary</div>
<div class='pill'>Validation {status}</div>
<div class='grid'>{''.join(f"<div class='card'><div class='label'>{a}</div><div class='value'>{b}</div></div>" for a,b in cards)}</div>
<div class='panel'><h2>Semantic Metric Contract</h2><p>All governed consumers use the same metric IDs, definitions, formulas, grains, sources, owners, SLAs and decision use. The sample source is the real UCI Online Retail dataset already present in the project; it is an external proxy, not PlaceMux production telemetry.</p></div>
<div class='grid'><div class='panel'><h2>Data Quality</h2><table><tr><th>Check</th><th>Value</th></tr><tr><td>Source max invoice date</td><td>{dq['source_max_invoice_date']}</td></tr><tr><td>Duplicate full rows</td><td>{dq['duplicate_full_rows']}</td></tr><tr><td>CustomerID null rate</td><td>{pct(dq['customerid_null_rate'])}</td></tr><tr><td>Cancellation rate</td><td>{pct(dq['cancellation_rate'])}</td></tr><tr><td>Invalid quantity rate</td><td>{pct(dq['invalid_quantity_rate'])}</td></tr><tr><td>Invalid price rate</td><td>{pct(dq['invalid_price_rate'])}</td></tr></table></div>
<div class='panel'><h2>Required-field null counts</h2><table><tr><th>Field</th><th>Null rows</th></tr>{null_rows}</table></div></div>
<div class='grid'><div class='panel'><h2>Cross-surface parity</h2><ul>{checks}</ul><div class='note'>The dashboard, executive view and ad-hoc query consume the same semantic values. The failure-path test deliberately changes one downstream value and verifies that the mismatch is detected.</div></div>
<div class='panel'><h2>Governance states</h2><ul><li><b>PASS</b>: within approved tolerance.</li><li><b>WATCH</b>: near threshold; owner action required.</li><li><b>BLOCKED</b>: critical metric cannot be trusted until resolved.</li></ul><p><b>Source limitation:</b> historical external dataset. Production freshness requires ingestion and publication timestamps from the real warehouse.</p></div></div>
</div></body></html>"""
    Path(out_path).write_text(html)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--snapshot', required=True)
    p.add_argument('--dq', required=True)
    p.add_argument('--validation', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    build(a.snapshot, a.dq, a.validation, a.out)
    print(a.out)
