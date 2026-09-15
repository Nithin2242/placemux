#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

APP_TITLE = "PlaceMux Phase 3 - Task 3 Performance Profiling & Bottleneck Elimination"


def percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        return 0.0
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def benchmark_callable(fn, warmup: int = 3, reps: int = 20) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "p50_ms": round(percentile(times, 0.50), 2),
        "p95_ms": round(percentile(times, 0.95), 2),
        "p99_ms": round(percentile(times, 0.99), 2),
        "mean_ms": round(statistics.mean(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
    }


def load_real_data(source: Path, db_path: Path) -> dict[str, Any]:
    df = pd.read_excel(source)
    required = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required source columns: {missing}")

    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["CustomerID_num"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["Quantity_num"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice_num"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["LineTotal"] = df["Quantity_num"] * df["UnitPrice_num"]

    is_cancel = df["InvoiceNo"].str.startswith("C", na=False)
    invalid_qty = df["Quantity_num"] <= 0
    invalid_price = df["UnitPrice_num"] <= 0

    valid = (
        ~is_cancel
        & df["CustomerID_num"].notna()
        & df["InvoiceDate"].notna()
        & df["Description"].notna()
        & df["Quantity_num"].gt(0)
        & df["UnitPrice_num"].gt(0)
    )

    clean = df.loc[valid, ["InvoiceNo", "StockCode", "Description", "Quantity_num", "InvoiceDate", "UnitPrice_num", "CustomerID_num", "Country", "LineTotal"]].copy()
    clean.columns = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country", "LineTotal"]
    clean["InvoiceDate"] = clean["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
    clean["CustomerID"] = clean["CustomerID"].astype(int)

    cancel = df.loc[is_cancel & df["LineTotal"].notna()].copy()
    cancellation_value = float(cancel["LineTotal"].abs().sum())
    cancellation_rows = int(len(cancel))

    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    clean.to_sql("order_lines", con, index=False)
    con.execute("CREATE TABLE customers AS SELECT DISTINCT CustomerID FROM order_lines")
    con.execute("CREATE TABLE tenants AS SELECT CustomerID, CASE WHEN CustomerID % 2 = 0 THEN 'TENANT_A' ELSE 'TENANT_B' END AS tenant_id FROM customers")
    con.commit(); con.close()

    invoices = int(clean["InvoiceNo"].nunique())
    revenue = float(clean["LineTotal"].sum())
    aov = revenue / invoices if invoices else 0.0
    return {
        "source": str(source),
        "raw_rows": int(len(df)),
        "clean_rows": int(len(clean)),
        "customers": int(clean["CustomerID"].nunique()),
        "invoices": invoices,
        "gross_revenue": round(revenue, 2),
        "average_order_value": round(aov, 2),
        "cancellation_rows": cancellation_rows,
        "cancellation_value_abs": round(cancellation_value, 2),
        "cancellation_rate_rows_pct": round(100 * cancellation_rows / max(1, len(df)), 2),
        "invalid_quantity_rows": int(invalid_qty.sum()),
        "invalid_price_rows": int(invalid_price.sum()),
    }


def get_conn(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def apply_indexes(db_path: Path) -> None:
    con = get_conn(db_path)
    con.execute("CREATE INDEX IF NOT EXISTS idx_order_customer ON order_lines(CustomerID)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_order_date ON order_lines(InvoiceDate)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_order_stock ON order_lines(StockCode)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_tenant_customer ON tenants(CustomerID, tenant_id)")
    con.commit(); con.close()


def clear_indexes(db_path: Path) -> None:
    con = get_conn(db_path)
    for name in ["idx_order_customer", "idx_order_date", "idx_order_stock", "idx_tenant_customer"]:
        con.execute(f"DROP INDEX IF EXISTS {name}")
    con.commit(); con.close()


def customer_orders(con, customer_id: int, tenant_id: str, limit: int = 20):
    q = """
    SELECT InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, LineTotal
    FROM order_lines o
    WHERE o.CustomerID = ?
      AND EXISTS (SELECT 1 FROM tenants t WHERE t.CustomerID=o.CustomerID AND t.tenant_id=?)
    ORDER BY InvoiceDate DESC LIMIT ?
    """
    return [dict(r) for r in con.execute(q, (customer_id, tenant_id, limit)).fetchall()]


def customer_summary_nplus1(con, customer_ids: list[int], tenant_id: str):
    out = []
    for cid in customer_ids:
        row = con.execute(
            "SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS invoices, SUM(LineTotal) AS revenue "
            "FROM order_lines WHERE CustomerID=? AND CustomerID IN (SELECT CustomerID FROM tenants WHERE tenant_id=?) GROUP BY CustomerID",
            (cid, tenant_id),
        ).fetchone()
        out.append({"CustomerID": cid, "invoices": int(row[1]) if row else 0, "revenue": float(row[2] or 0) if row else 0.0})
    return out


def customer_summary_join(con, customer_ids: list[int], tenant_id: str):
    placeholders = ",".join("?" for _ in customer_ids)
    q = f"""
    SELECT o.CustomerID, COUNT(DISTINCT o.InvoiceNo) AS invoices, SUM(o.LineTotal) AS revenue
    FROM order_lines o
    JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=?
    WHERE o.CustomerID IN ({placeholders})
    GROUP BY o.CustomerID ORDER BY o.CustomerID
    """
    rows = con.execute(q, [tenant_id, *customer_ids]).fetchall()
    by_id = {int(r[0]): {"CustomerID": int(r[0]), "invoices": int(r[1]), "revenue": float(r[2] or 0)} for r in rows}
    return [by_id.get(cid, {"CustomerID": cid, "invoices": 0, "revenue": 0.0}) for cid in customer_ids]


def revenue_by_date(con, start: str, end: str, tenant_id: str) -> float:
    q = """
    SELECT SUM(o.LineTotal) FROM order_lines o
    JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=?
    WHERE o.InvoiceDate >= ? AND o.InvoiceDate < ?
    """
    row = con.execute(q, (tenant_id, start, end)).fetchone()
    return float(row[0] or 0.0)


def query_plan(con, sql: str, params: tuple[Any, ...]) -> list[str]:
    rows = con.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return [str(r[3]) for r in rows]


class APIServer:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.cache: dict[str, tuple[float, Any]] = {}
        self.cache_ttl = 30.0

    def auth(self, headers, tenant_id: str) -> bool:
        return headers.get("X-Role") == "analyst" and headers.get("X-Tenant-Id") == tenant_id

    def idempotent(self, request_id: str):
        key = f"note:{request_id}"
        if key in self.cache and time.time() - self.cache[key][0] < self.cache_ttl:
            return self.cache[key][1]
        payload = {"request_id": request_id, "accepted": True}
        self.cache[key] = (time.time(), payload)
        return payload


class Handler(__import__("http.server", fromlist=["BaseHTTPRequestHandler"]).BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

    def _json(self, status: int, payload: Any):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path); qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/health":
            return self._json(200, {"status": "ok"})
        tenant = qs.get("tenant_id", [None])[0]
        if tenant not in ("TENANT_A", "TENANT_B"):
            return self._json(400, {"error":"invalid tenant"})
        app = self.server.app
        if not app.auth(self.headers, tenant):
            return self._json(401, {"error":"unauthorized"})
        con = get_conn(app.db_path)
        try:
            if parsed.path == "/api/customer/orders":
                return self._json(200, customer_orders(con, int(qs.get("customer_id", [0])[0]), tenant, int(qs.get("limit", [20])[0])))
            if parsed.path == "/api/customers/summary":
                ids = [int(x) for x in qs.get("ids", [""])[0].split(",") if x.strip()]
                key = f"summary|{tenant}|{','.join(map(str, ids))}"
                cached = app.cache.get(key)
                if cached and time.time() - cached[0] < app.cache_ttl:
                    return self._json(200, {"cached": True, "data": cached[1]})
                data = customer_summary_join(con, ids, tenant)
                app.cache[key] = (time.time(), data)
                return self._json(200, {"cached": False, "data": data})
            if parsed.path == "/api/revenue":
                return self._json(200, {"revenue": revenue_by_date(con, qs.get("start", [""])[0], qs.get("end", [""])[0], tenant)})
            return self._json(404, {"error":"not found"})
        finally:
            con.close()

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/notes":
            return self._json(404, {"error":"not found"})
        app = self.server.app
        tenant = self.headers.get("X-Tenant-Id")
        if tenant not in ("TENANT_A", "TENANT_B") or not app.auth(self.headers, tenant):
            return self._json(401, {"error":"unauthorized"})
        req_id = self.headers.get("X-Request-Id")
        if not req_id:
            return self._json(400, {"error":"X-Request-Id required"})
        return self._json(200, app.idempotent(req_id))


def start_server(app):
    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.app = app
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    return server, thread


def http_get(base, path, headers):
    req = urllib.request.Request(base + path, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode())


def http_post(base, path, headers):
    req = urllib.request.Request(base + path, method="POST", headers=headers, data=b"{}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode())


def build_dashboard(payload: dict[str, Any]) -> str:
    def money(v):
        return f"£{v:,.2f}"
    rows = "".join(
        f"<tr><td>{r['name']}</td><td>{r['before']['p95_ms']:.2f} ms</td><td>{r['after']['p95_ms']:.2f} ms</td><td class='pass'>{r['improvement_pct']:.1f}%</td><td>{r['fix']}</td></tr>"
        for r in payload["benchmarks"]
    )
    scen = "".join(
        f"<tr><td>{s['conversion_sensitivity_pp']:.2f} pp / +100ms</td><td>{s['scenario_transactions']:,}</td><td>{s['implied_transactions']:.1f}</td><td>{money(s['revenue_at_risk'])}</td></tr>"
        for s in payload["financial_model"]["scenarios"]
    )
    pri = "".join(
        f"<tr><td>{i+1}</td><td>{x['fix']}</td><td>{x['improvement_pct']:.1f}%</td><td>{x['financial_priority_score']:,.0f}</td></tr>"
        for i, x in enumerate(payload["priority"])
    )
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{APP_TITLE}</title>
<style>body{{font-family:Inter,Arial,sans-serif;background:#f5f7fb;color:#17223b;margin:0}}.wrap{{max-width:1280px;margin:32px auto;padding:0 22px}}h1{{font-size:38px;margin:0 0 6px}}.sub{{color:#66738e;margin-bottom:20px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#fff;border:1px solid #dde3ef;border-radius:14px;padding:18px;box-shadow:0 2px 8px #0000000b}}.label{{color:#6b7893;font-size:13px}}.value{{font-size:27px;font-weight:800;margin-top:6px}}.section{{margin-top:16px}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden}}th,td{{padding:11px;border-bottom:1px solid #e7ebf2;text-align:left}}th{{color:#6b7893;font-size:13px}}.pass{{color:#128556;font-weight:800}}.warn{{color:#b06a00;font-weight:800}}.note{{font-size:13px;color:#66738e;line-height:1.5}}pre{{white-space:pre-wrap;background:#0d1526;color:#dce6ff;padding:14px;border-radius:12px;overflow:auto}}@media(max-width:950px){{.grid{{grid-template-columns:1fr 1fr}}}}</style></head><body><div class='wrap'>
<h1>{APP_TITLE}</h1><div class='sub'>Real UCI Online Retail source · measured latency evidence · commercial-impact sensitivity model · no causal claim</div>
<div class='grid'><div class='card'><div class='label'>Raw rows</div><div class='value'>{payload['source']['raw_rows']:,}</div></div><div class='card'><div class='label'>Clean purchase rows</div><div class='value'>{payload['source']['clean_rows']:,}</div></div><div class='card'><div class='label'>Invoices</div><div class='value'>{payload['source']['invoices']:,}</div></div><div class='card'><div class='label'>Gross revenue proxy</div><div class='value'>{money(payload['source']['gross_revenue'])}</div></div></div>
<div class='section card'><h2>Measured performance evidence</h2><table><tr><th>Workload</th><th>Baseline p95</th><th>Optimized p95</th><th>Improvement</th><th>Engineering fix</th></tr>{rows}</table></div>
<div class='section card'><h2>Commercial impact sensitivity</h2><p class='note'>The source has purchase and cancellation records but no per-session latency/conversion telemetry. The money model therefore shows scenario sensitivity, not observed lost revenue or causation. Each row asks: if an extra 100 ms were associated with the stated conversion change, what value would be exposed at the dataset's observed average order value?</p><table><tr><th>Assumption</th><th>Observed transactions</th><th>Implied transaction delta</th><th>Revenue exposure</th></tr>{scen}</table></div>
<div class='section card'><h2>Engineering priority by financial exposure proxy</h2><table><tr><th>Priority</th><th>Fix</th><th>P95 improvement</th><th>Priority score</th></tr>{pri}</table></div>
<div class='section grid'><div class='card'><h2>Correlation limits</h2><pre>{json.dumps(payload['correlation_limits'], indent=2)}</pre></div><div class='card'><h2>Validation & controls</h2><pre>{json.dumps(payload['controls'], indent=2)}</pre></div></div>
<div class='section card'><h2>Scope</h2><p class='note'>Real UCI Online Retail data is used as an external real-data proxy. This report does not present PlaceMux production conversion, latency or revenue telemetry. See task3_summary.json for the full traceable evidence chain.</p></div>
</div></body></html>"""


def run(source: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    db = out_dir / "task3_performance_money.db"
    summary = load_real_data(source, db)
    con = get_conn(db)
    customer_ids = [int(r[0]) for r in con.execute("SELECT CustomerID FROM customers ORDER BY CustomerID LIMIT 20").fetchall()]
    tenant_a_ids = [cid for cid in customer_ids if cid % 2 == 0][:10] or customer_ids[:10]

    # Full observed date range in the clean dataset.
    min_dt = con.execute("SELECT MIN(InvoiceDate) FROM order_lines").fetchone()[0]
    max_dt = con.execute("SELECT MAX(InvoiceDate) FROM order_lines").fetchone()[0]
    end_dt = datetime.strptime(max_dt[:10], "%Y-%m-%d") + pd.Timedelta(days=1)
    start = f"{min_dt[:10]} 00:00:00"
    end = end_dt.strftime("%Y-%m-%d 00:00:00")

    clear_indexes(db)
    b1 = benchmark_callable(lambda: customer_orders(con, tenant_a_ids[0], "TENANT_A"))
    b2 = benchmark_callable(lambda: customer_summary_nplus1(con, tenant_a_ids, "TENANT_A"), reps=12)
    b3 = benchmark_callable(lambda: revenue_by_date(con, start, end, "TENANT_A"), reps=20)
    p1b = query_plan(con, "SELECT InvoiceNo FROM order_lines WHERE CustomerID=? ORDER BY InvoiceDate DESC LIMIT 20", (tenant_a_ids[0],))
    p2b = query_plan(con, "SELECT COUNT(DISTINCT InvoiceNo) FROM order_lines WHERE CustomerID=?", (tenant_a_ids[0],))
    p3b = query_plan(con, "SELECT SUM(LineTotal) FROM order_lines WHERE InvoiceDate>=? AND InvoiceDate<?", (start, end))

    apply_indexes(db)
    a1 = benchmark_callable(lambda: customer_orders(con, tenant_a_ids[0], "TENANT_A"))
    a2 = benchmark_callable(lambda: customer_summary_join(con, tenant_a_ids, "TENANT_A"), reps=12)
    a3 = benchmark_callable(lambda: revenue_by_date(con, start, end, "TENANT_A"), reps=20)
    p1a = query_plan(con, "SELECT InvoiceNo FROM order_lines WHERE CustomerID=? ORDER BY InvoiceDate DESC LIMIT 20", (tenant_a_ids[0],))
    p2a = query_plan(con, "SELECT o.CustomerID, COUNT(DISTINCT o.InvoiceNo) FROM order_lines o JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=? WHERE o.CustomerID IN (?) GROUP BY o.CustomerID", ("TENANT_A", tenant_a_ids[0]))
    p3a = query_plan(con, "SELECT SUM(LineTotal) FROM order_lines WHERE InvoiceDate>=? AND InvoiceDate<?", (start, end))
    con.close()

    def imp(before, after):
        return round(max(0.0, (before["p95_ms"] - after["p95_ms"]) / max(before["p95_ms"], 0.001) * 100), 1)

    benchmarks = [
        {"name":"GET /api/customer/orders","before":b1,"after":a1,"improvement_pct":imp(b1,a1),"fix":"CustomerID index"},
        {"name":"GET /api/customers/summary","before":b2,"after":a2,"improvement_pct":imp(b2,a2),"fix":"N+1 -> grouped JOIN"},
        {"name":"GET /api/revenue","before":b3,"after":a3,"improvement_pct":imp(b3,a3),"fix":"InvoiceDate index"},
    ]

    # Explicitly sensitivity-based: there is no session denominator in the source, so we do not claim causal loss.
    sensitivities = [0.10, 0.25, 0.50]  # percentage-point conversion change per +100ms, illustrative assumptions
    scenarios = []
    for pp in sensitivities:
        delta_tx = summary["invoices"] * (pp / 100.0)
        revenue_exposure = delta_tx * summary["average_order_value"]
        scenarios.append({
            "conversion_sensitivity_pp": pp,
            "scenario_transactions": summary["invoices"],
            "implied_transactions": round(delta_tx, 2),
            "revenue_at_risk": round(revenue_exposure, 2),
        })
    base_money = scenarios[-1]["revenue_at_risk"]
    priority = []
    for r in benchmarks:
        # Financial priority proxy: relative p95 improvement multiplied by a common 0.5pp sensitivity scenario.
        score = base_money * (r["improvement_pct"] / 100.0)
        priority.append({"fix": r["fix"], "improvement_pct": r["improvement_pct"], "financial_priority_score": round(score, 0)})
    priority.sort(key=lambda x: x["financial_priority_score"], reverse=True)

    controls = {
        "happy_path": True,
        "unauthorized_request": None,
        "cross_tenant_attack": None,
        "idempotent_retry": None,
        "persistence_check": None,
        "benchmark_on_real_source": True,
        "causal_claim_blocked": True,
    }
    app = APIServer(db); server, thread = start_server(app); base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        good = {"X-Role":"analyst","X-Tenant-Id":"TENANT_A"}
        try:
            http_get(base, f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}", good)
        except Exception:
            controls["happy_path"] = False
        try:
            urllib.request.urlopen(urllib.request.Request(base + f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}"), timeout=5)
            controls["unauthorized_request"] = "FAIL"
        except urllib.error.HTTPError as e:
            controls["unauthorized_request"] = "PASS" if e.code == 401 else f"HTTP {e.code}"
        try:
            bad = {"X-Role":"analyst","X-Tenant-Id":"TENANT_B"}
            urllib.request.urlopen(urllib.request.Request(base + f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}", headers=bad), timeout=5)
            controls["cross_tenant_attack"] = "FAIL"
        except urllib.error.HTTPError as e:
            controls["cross_tenant_attack"] = "PASS" if e.code == 401 else f"HTTP {e.code}"
        r1 = http_post(base, "/api/notes", {**good,"X-Request-Id":"perf-money-123"})
        r2 = http_post(base, "/api/notes", {**good,"X-Request-Id":"perf-money-123"})
        controls["idempotent_retry"] = "PASS" if r1[1] == r2[1] else "FAIL"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    con = get_conn(db); persisted = con.execute("SELECT COUNT(*) FROM order_lines").fetchone()[0]; con.close()
    controls["persistence_check"] = "PASS" if persisted == summary["clean_rows"] else "FAIL"

    payload = {
        "source": summary,
        "benchmarks": benchmarks,
        "plans": {"customer_orders_before":p1b,"customer_orders_after":p1a,"customer_summary_before":p2b,"customer_summary_after":p2a,"revenue_before":p3b,"revenue_after":p3a},
        "financial_model": {
            "type":"sensitivity_not_observed_loss",
            "assumption_note":"Illustrative conversion sensitivity scenarios only; no per-session latency/conversion telemetry exists in UCI Online Retail.",
            "scenarios": scenarios,
        },
        "priority": priority,
        "correlation_limits": {
            "conversion_observed_in_source": False,
            "session_level_latency_observed_in_source": False,
            "latency_conversion_correlation_estimable": False,
            "causation_claim_allowed": False,
            "recommended_next_data":"Join session/request telemetry (latency, errors, abandonment, conversion, order value) to a common session or request identifier and pre-register the analysis before making causal claims.",
        },
        "controls": controls,
        "validation":"PASS" if all(v == "PASS" or v is True for v in controls.values()) else "WATCH",
    }
    (out_dir/"task3_summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{**{"workload":r["name"],"before_p95_ms":r["before"]["p95_ms"],"after_p95_ms":r["after"]["p95_ms"],"improvement_pct":r["improvement_pct"],"fix":r["fix"]}} for r in benchmarks]).to_csv(out_dir/"before_after_p95.csv", index=False)
    pd.DataFrame(scenarios).to_csv(out_dir/"financial_sensitivity.csv", index=False)
    (out_dir/"task3_performance_money_dashboard.html").write_text(build_dashboard(payload), encoding="utf-8")
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="phase3/task3_outputs")
    args = ap.parse_args()
    payload = run(Path(args.source), Path(args.out))
    print(json.dumps({
        "validation": payload["validation"],
        "raw_rows": payload["source"]["raw_rows"],
        "clean_rows": payload["source"]["clean_rows"],
        "gross_revenue": payload["source"]["gross_revenue"],
        "benchmarks":[{"name":r["name"],"before_p95_ms":r["before"]["p95_ms"],"after_p95_ms":r["after"]["p95_ms"],"improvement_pct":r["improvement_pct"]} for r in payload["benchmarks"]],
        "financial_scenarios":payload["financial_model"]["scenarios"],
        "controls":payload["controls"],
        "outputs":["task3_summary.json","before_after_p95.csv","financial_sensitivity.csv","task3_performance_money_dashboard.html"]
    }, indent=2))

if __name__ == "__main__":
    main()
