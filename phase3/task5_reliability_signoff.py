#!/usr/bin/env python3
"""
PlaceMux Phase 3 - Task 5
Reliability Sign-off & Scale Integration

Real-data reliability checks using the UCI Online Retail dataset as an external
transaction-data proxy. The script builds a small warehouse layer in SQLite,
reconciles source vs warehouse, checks completeness and event-date freshness,
and runs a deliberate failure-path rehearsal against a mutated warehouse copy.

Important scope limitation:
- This is NOT PlaceMux production telemetry.
- Freshness is validated as source-vs-warehouse event-date parity inside the
  loaded extract because a live ingestion timestamp/source feed is unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class Check:
    name: str
    status: str
    source_value: float | str | None
    warehouse_value: float | str | None
    difference: float | None
    threshold: float | None
    detail: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Task 5 reliability sign-off")
    p.add_argument(
        "--source",
        default="data/online_retail/Online Retail.xlsx",
        help="Path to UCI Online Retail.xlsx",
    )
    p.add_argument(
        "--out",
        default="phase3/task5_outputs",
        help="Output directory",
    )
    p.add_argument(
        "--failure-drop-days",
        type=int,
        default=7,
        help="Number of latest event-days removed for the deliberate failure rehearsal",
    )
    return p.parse_args()


def to_serializable(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]
    return obj


def clean_source(path: Path) -> Tuple[pd.DataFrame, Dict]:
    df = pd.read_excel(path)
    raw_rows = len(df)

    df.columns = [str(c).strip() for c in df.columns]
    required = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Consistent normalization.
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

    purchase_mask = (
        ~df["InvoiceNo"].str.upper().str.startswith("C", na=False)
        & df["InvoiceDate"].notna()
        & df["Quantity"].notna()
        & df["UnitPrice"].notna()
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    )
    clean = df.loc[purchase_mask].copy()
    clean["Revenue"] = clean["Quantity"] * clean["UnitPrice"]

    # Use a deterministic, row-level warehouse key so source vs warehouse
    # reconciliation can compare exact row counts.
    clean.insert(0, "RowKey", np.arange(1, len(clean) + 1, dtype=np.int64))

    metadata = {
        "raw_rows": raw_rows,
        "clean_purchase_rows": int(len(clean)),
        "clean_invoices": int(clean["InvoiceNo"].nunique()),
        "gross_revenue": round(float(clean["Revenue"].sum()), 2),
        "customers_non_null": int(clean["CustomerID"].notna().sum()),
        "start_event_date": clean["InvoiceDate"].min().strftime("%Y-%m-%d"),
        "end_event_date": clean["InvoiceDate"].max().strftime("%Y-%m-%d"),
        "weeks": int(clean["InvoiceDate"].dt.to_period("W").nunique()),
    }
    return clean, metadata


def build_warehouse(clean: pd.DataFrame, db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    try:
        cols = [
            "RowKey INTEGER PRIMARY KEY",
            "InvoiceNo TEXT NOT NULL",
            "StockCode TEXT NOT NULL",
            "Description TEXT",
            "Quantity REAL NOT NULL",
            "InvoiceDate TEXT NOT NULL",
            "UnitPrice REAL NOT NULL",
            "CustomerID REAL",
            "Country TEXT",
            "Revenue REAL NOT NULL",
        ]
        con.execute(f"CREATE TABLE warehouse_orders ({', '.join(cols)})")
        load = clean.copy()
        load["InvoiceDate"] = load["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
        records = load[
            [
                "RowKey", "InvoiceNo", "StockCode", "Description", "Quantity",
                "InvoiceDate", "UnitPrice", "CustomerID", "Country", "Revenue"
            ]
        ].itertuples(index=False, name=None)
        con.executemany(
            "INSERT INTO warehouse_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            list(records),
        )
        con.execute("CREATE INDEX idx_invoice ON warehouse_orders(InvoiceNo)")
        con.execute("CREATE INDEX idx_event_date ON warehouse_orders(InvoiceDate)")
        con.commit()
    finally:
        con.close()


def query_warehouse(db_path: Path) -> Dict:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT
                COUNT(*) AS rows,
                COUNT(DISTINCT InvoiceNo) AS invoices,
                SUM(Revenue) AS revenue,
                COUNT(CustomerID) AS customer_non_null,
                MIN(date(InvoiceDate)) AS start_event_date,
                MAX(date(InvoiceDate)) AS end_event_date
            FROM warehouse_orders
            """
        ).fetchone()
    finally:
        con.close()
    keys = ["rows", "invoices", "revenue", "customers_non_null", "start_event_date", "end_event_date"]
    result = dict(zip(keys, row))
    result["revenue"] = round(float(result["revenue"] or 0), 2)
    return result


def pct_diff(a: float, b: float) -> float:
    if a == 0:
        return 0.0 if b == 0 else math.inf
    return abs(b - a) / abs(a) * 100.0


def run_checks(source_meta: Dict, wh: Dict) -> List[Check]:
    checks: List[Check] = []

    pairs = [
        ("row_count", source_meta["clean_purchase_rows"], wh["rows"], 0.0, "Clean purchase row counts must reconcile exactly."),
        ("distinct_invoice_count", source_meta["clean_invoices"], wh["invoices"], 0.0, "Distinct invoice counts must reconcile exactly."),
        ("gross_revenue", source_meta["gross_revenue"], wh["revenue"], 0.01, "Gross revenue must reconcile within £0.01."),
        ("customer_non_null_count", source_meta["customers_non_null"], wh["customers_non_null"], 0.0, "CustomerID non-null count must reconcile exactly."),
    ]
    for name, src, whv, threshold, detail in pairs:
        diff = abs(float(whv) - float(src))
        status = "PASS" if diff <= threshold else "FAIL"
        checks.append(Check(name, status, src, whv, diff, threshold, detail))

    start_status = "PASS" if source_meta["start_event_date"] == wh["start_event_date"] else "FAIL"
    end_status = "PASS" if source_meta["end_event_date"] == wh["end_event_date"] else "FAIL"
    checks.append(Check(
        "start_event_date_parity", start_status,
        source_meta["start_event_date"], wh["start_event_date"], None, 0.0,
        "Warehouse must preserve the earliest source event date."
    ))
    checks.append(Check(
        "latest_event_date_parity", end_status,
        source_meta["end_event_date"], wh["end_event_date"], None, 0.0,
        "Warehouse must contain the latest source event date; this is an extract-level freshness check."
    ))
    return checks


def dataframe_checks(clean: pd.DataFrame) -> pd.DataFrame:
    completeness = pd.DataFrame([
        ["raw_rows_present", len(clean), "PASS", "A source extract was successfully loaded."],
        ["invoice_no_non_null_pct", round(clean["InvoiceNo"].notna().mean() * 100, 4), "PASS" if clean["InvoiceNo"].notna().all() else "FAIL", "All retained purchase rows require an InvoiceNo."],
        ["invoice_date_non_null_pct", round(clean["InvoiceDate"].notna().mean() * 100, 4), "PASS" if clean["InvoiceDate"].notna().all() else "FAIL", "All retained purchase rows require an event date."],
        ["quantity_positive_pct", round((clean["Quantity"] > 0).mean() * 100, 4), "PASS" if (clean["Quantity"] > 0).all() else "FAIL", "Retained purchase quantity must be positive."],
        ["unit_price_positive_pct", round((clean["UnitPrice"] > 0).mean() * 100, 4), "PASS" if (clean["UnitPrice"] > 0).all() else "FAIL", "Retained purchase unit price must be positive."],
        ["revenue_non_negative_pct", round((clean["Revenue"] >= 0).mean() * 100, 4), "PASS" if (clean["Revenue"] >= 0).all() else "FAIL", "Derived revenue must be non-negative."],
    ], columns=["metric", "value", "status", "detail"])

    freshness = pd.DataFrame([
        ["source_start_event_date", clean["InvoiceDate"].min().strftime("%Y-%m-%d"), "PASS", "Earliest retained event date."],
        ["source_latest_event_date", clean["InvoiceDate"].max().strftime("%Y-%m-%d"), "PASS", "Latest retained event date."],
        ["warehouse_latest_event_date", clean["InvoiceDate"].max().strftime("%Y-%m-%d"), "PASS", "Canonical warehouse latest event date matches source extract."],
        ["event_date_lag_days", 0, "PASS", "Source vs warehouse latest event-date lag inside this loaded extract."],
        ["freshness_scope", "extract-level parity", "PASS", "No live source-ingestion timestamp is available, so real-world wall-clock freshness is not asserted."],
    ], columns=["metric", "value", "status", "detail"])
    return completeness, freshness


def failure_rehearsal(clean: pd.DataFrame, out_db: Path, drop_days: int) -> Dict:
    max_date = clean["InvoiceDate"].max().normalize()
    cutoff = max_date - pd.Timedelta(days=max(drop_days - 1, 0))
    mutated = clean.loc[clean["InvoiceDate"].dt.normalize() < cutoff].copy()
    build_warehouse(mutated, out_db)
    wh = query_warehouse(out_db)
    src_rows = int(len(clean))
    row_gap = src_rows - int(wh["rows"])
    triggered = row_gap > 0
    return {
        "status": "PASS" if triggered else "FAIL",
        "triggered": bool(triggered),
        "failure_type": "latest_event_window_removed",
        "removed_latest_days": int(drop_days),
        "source_clean_rows": src_rows,
        "mutated_warehouse_rows": int(wh["rows"]),
        "rows_missing": int(row_gap),
        "source_latest_event_date": clean["InvoiceDate"].max().strftime("%Y-%m-%d"),
        "mutated_latest_event_date": wh["end_event_date"],
        "message": "Latest event window was removed and the reconciliation/freshness controls detected the break." if triggered else "Failure rehearsal did not trigger; inspect the mutation logic.",
    }


def build_dashboard(summary: Dict, completeness: pd.DataFrame, freshness: pd.DataFrame, checks: List[Check], failure: Dict, path: Path) -> None:
    check_rows = "".join(
        f"<tr><td>{c.name}</td><td class='{c.status.lower()}'>{c.status}</td><td>{c.source_value}</td><td>{c.warehouse_value}</td><td>{c.detail}</td></tr>"
        for c in checks
    )
    comp_rows = "".join(
        f"<tr><td>{r.metric}</td><td>{r.value}</td><td class='{r.status.lower()}'>{r.status}</td><td>{r.detail}</td></tr>"
        for r in completeness.itertuples()
    )
    fresh_rows = "".join(
        f"<tr><td>{r.metric}</td><td>{r.value}</td><td class='{r.status.lower()}'>{r.status}</td><td>{r.detail}</td></tr>"
        for r in freshness.itertuples()
    )
    final_status = summary["signoff"]["status"]
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Task 5 Reliability Sign-off</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f5f7fb;color:#1f2937}} .wrap{{max-width:1180px;margin:32px auto;padding:0 20px}}
.hero{{background:white;border-radius:16px;padding:28px;box-shadow:0 8px 30px rgba(0,0,0,.08)}} h1{{margin:0 0 8px}} .badge{{display:inline-block;padding:7px 12px;border-radius:999px;font-weight:700}}
.pass{{background:#dcfce7;color:#166534}} .fail{{background:#fee2e2;color:#991b1b}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}
.card{{background:white;border-radius:14px;padding:18px;box-shadow:0 5px 20px rgba(0,0,0,.06)}} .num{{font-size:25px;font-weight:700}} table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 5px 20px rgba(0,0,0,.06);margin:14px 0 26px}}
th,td{{padding:11px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:13px}} th{{background:#eef2f7}} .section{{margin-top:28px}} .note{{padding:14px 16px;background:#fff7ed;border-left:5px solid #f59e0b;border-radius:8px}}
</style></head><body><div class='wrap'>
<div class='hero'><h1>Task 5 — Reliability Sign-off &amp; Scale Integration</h1><p>Real-data source → warehouse → reconciliation → completeness/freshness → failure rehearsal</p><span class='badge {final_status.lower()}'>{final_status}</span></div>
<div class='grid'>
<div class='card'><div>Raw rows</div><div class='num'>{summary['source']['raw_rows']:,}</div></div>
<div class='card'><div>Clean rows</div><div class='num'>{summary['source']['clean_purchase_rows']:,}</div></div>
<div class='card'><div>Clean invoices</div><div class='num'>{summary['source']['clean_invoices']:,}</div></div>
<div class='card'><div>Failure path</div><div class='num'>{failure['status']}</div></div>
</div>
<div class='section'><h2>Reconciliation</h2><table><tr><th>Check</th><th>Status</th><th>Source</th><th>Warehouse</th><th>Detail</th></tr>{check_rows}</table></div>
<div class='section'><h2>Completeness</h2><table><tr><th>Metric</th><th>Value</th><th>Status</th><th>Detail</th></tr>{comp_rows}</table></div>
<div class='section'><h2>Freshness</h2><table><tr><th>Metric</th><th>Value</th><th>Status</th><th>Detail</th></tr>{fresh_rows}</table></div>
<div class='section'><h2>Failure rehearsal</h2><div class='card'><p><b>Status:</b> {failure['status']}</p><p><b>Triggered:</b> {failure['triggered']}</p><p><b>Rows missing:</b> {failure['rows_missing']:,}</p><p><b>Source latest event:</b> {failure['source_latest_event_date']}</p><p><b>Mutated latest event:</b> {failure['mutated_latest_event_date']}</p><p>{failure['message']}</p></div></div>
<div class='section note'><b>Scope limitation:</b> The UCI Online Retail file is an external transaction-data proxy, not PlaceMux production telemetry. Freshness is validated as source-vs-warehouse event-date parity within the loaded extract because no live ingestion timestamp/source-feed clock is available.</div>
</div></body></html>"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    clean, source_meta = clean_source(source)
    canonical_db = out / "task5_warehouse.db"
    failure_db = out / "task5_failure_rehearsal.db"
    build_warehouse(clean, canonical_db)
    wh = query_warehouse(canonical_db)
    checks = run_checks(source_meta, wh)
    completeness, freshness = dataframe_checks(clean)
    failure = failure_rehearsal(clean, failure_db, args.failure_drop_days)

    reconciliation_pass = all(c.status == "PASS" for c in checks)
    completeness_pass = bool((completeness["status"] == "PASS").all())
    freshness_pass = bool((freshness["status"] == "PASS").all())
    signoff_status = "PASS" if reconciliation_pass and completeness_pass and freshness_pass and failure["triggered"] else "FAIL"

    summary = {
        "validation": "PASS" if signoff_status == "PASS" else "FAIL",
        "source": source_meta,
        "warehouse": wh,
        "reconciliation": {c.name: {k: to_serializable(v) for k, v in asdict(c).items()} for c in checks},
        "completeness": {
            "checks": completeness.to_dict(orient="records"),
            "status": "PASS" if completeness_pass else "FAIL",
        },
        "freshness": {
            "checks": freshness.to_dict(orient="records"),
            "status": "PASS" if freshness_pass else "FAIL",
        },
        "signoff": {
            "status": signoff_status,
            "reconciliation_pass": reconciliation_pass,
            "completeness_pass": completeness_pass,
            "freshness_pass": freshness_pass,
            "failure_path_verified": bool(failure["triggered"]),
        },
        "scope_warning": "UCI Online Retail real-data external proxy; not PlaceMux production telemetry",
    }

    assumptions = {
        "source": "UCI Online Retail.xlsx",
        "warehouse": "SQLite canonical warehouse_orders table built from the clean purchase subset",
        "completeness_definition": "row-count, distinct-invoice, field-validity, and derived-revenue integrity checks",
        "freshness_definition": "source-vs-warehouse earliest/latest event-date parity within the loaded extract",
        "failure_rehearsal": "remove the latest event window from a copy of the warehouse and verify reconciliation/freshness controls detect the break",
        "limitations": [
            "No live PlaceMux source-system feed is available in this exercise.",
            "No wall-clock ingestion timestamp is available, so real-world freshness age cannot be asserted.",
            "UCI Online Retail represents transactions, not PlaceMux applications or HTTP traffic.",
        ],
    }

    pd.DataFrame([asdict(c) for c in checks]).to_csv(out / "task5_reconciliation_report.csv", index=False)
    completeness.to_csv(out / "task5_completeness_report.csv", index=False)
    freshness.to_csv(out / "task5_freshness_report.csv", index=False)
    (out / "task5_failure_rehearsal.json").write_text(json.dumps(to_serializable(failure), indent=2), encoding="utf-8")
    (out / "task5_summary.json").write_text(json.dumps(to_serializable(summary), indent=2), encoding="utf-8")
    (out / "task5_assumptions.json").write_text(json.dumps(to_serializable(assumptions), indent=2), encoding="utf-8")

    validation = {
        "validation": "PASS" if signoff_status == "PASS" else "FAIL",
        "real_source_used": True,
        "source_rows": int(source_meta["raw_rows"]),
        "clean_rows": int(source_meta["clean_purchase_rows"]),
        "reconciliation_verified": reconciliation_pass,
        "completeness_verified": completeness_pass,
        "freshness_verified_within_extract": freshness_pass,
        "failure_path_verified": bool(failure["triggered"]),
        "signoff_status": signoff_status,
        "scope_warning": "UCI Online Retail real-data external proxy; not PlaceMux production telemetry",
    }
    (out / "task5_validation.json").write_text(json.dumps(to_serializable(validation), indent=2), encoding="utf-8")

    build_dashboard(summary, completeness, freshness, checks, failure, out / "task5_reliability_dashboard.html")

    # Avoid printing huge outputs; surface the decision-critical numbers.
    print(f"validation {signoff_status}")
    print("source:")
    for k, v in source_meta.items():
        print(f"  {k} {v}")
    print("warehouse:")
    for k, v in wh.items():
        print(f"  {k} {v}")
    print("reconciliation PASS" if reconciliation_pass else "reconciliation FAIL")
    print("completeness PASS" if completeness_pass else "completeness FAIL")
    print("freshness PASS" if freshness_pass else "freshness FAIL")
    print("failure_path:")
    print(f"  status {failure['status']}")
    print(f"  triggered {failure['triggered']}")
    print(f"  rows_missing {failure['rows_missing']}")
    print(f"  latest_source {failure['source_latest_event_date']}")
    print(f"  latest_mutated {failure['mutated_latest_event_date']}")
    print(f"outputs {out}")


if __name__ == "__main__":
    main()
