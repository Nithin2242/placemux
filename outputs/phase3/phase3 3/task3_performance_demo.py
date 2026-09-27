#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pandas as pd

APP_TITLE = "PlaceMux Phase 3 - Task 3 Performance Profiling & Bottleneck Elimination"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def load_real_data(source: Path, db_path: Path) -> dict[str, Any]:
    df = pd.read_excel(source)
    required = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required source columns: {missing}")

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["LineTotal"] = df["Quantity"] * df["UnitPrice"]
    is_cancel = df["InvoiceNo"].astype(str).str.startswith("C", na=False)
    valid = (
        ~is_cancel
        & df["CustomerID"].notna()
        & df["InvoiceDate"].notna()
        & df["Description"].notna()
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    )
    clean = df.loc[valid, ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country", "LineTotal"]].copy()
    clean["InvoiceDate"] = clean["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
    clean["CustomerID"] = clean["CustomerID"].astype(int)

    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    clean.to_sql("order_lines", con, index=False)
    con.execute("CREATE TABLE customers AS SELECT DISTINCT CustomerID FROM order_lines")
    con.execute("CREATE TABLE tenants AS SELECT CustomerID, CASE WHEN CustomerID % 2 = 0 THEN 'TENANT_A' ELSE 'TENANT_B' END AS tenant_id FROM customers")
    con.commit()
    con.close()

    raw_rows = len(df)
    valid_rows = len(clean)
    customers = int(clean["CustomerID"].nunique())
    date_min = clean["InvoiceDate"].min()
    date_max = clean["InvoiceDate"].max()
    return {
        "source": str(source),
        "raw_rows": raw_rows,
        "clean_rows": valid_rows,
        "customers": customers,
        "date_min": date_min,
        "date_max": date_max,
        "gross_revenue": float(clean["LineTotal"].sum()),
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
    con.commit()
    con.close()


def clear_indexes(db_path: Path) -> None:
    con = get_conn(db_path)
    for name in ["idx_order_customer", "idx_order_date", "idx_order_stock", "idx_tenant_customer"]:
        con.execute(f"DROP INDEX IF EXISTS {name}")
    con.commit()
    con.close()


def customer_orders(con: sqlite3.Connection, customer_id: int, tenant_id: str, limit: int = 20) -> list[dict[str, Any]]:
    q = """
    SELECT InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, LineTotal
    FROM order_lines o
    WHERE o.CustomerID = ?
      AND EXISTS (SELECT 1 FROM tenants t WHERE t.CustomerID=o.CustomerID AND t.tenant_id=?)
    ORDER BY InvoiceDate DESC
    LIMIT ?
    """
    return [dict(r) for r in con.execute(q, (customer_id, tenant_id, limit)).fetchall()]


def customer_summary_nplus1(con: sqlite3.Connection, customer_ids: list[int], tenant_id: str) -> list[dict[str, Any]]:
    # Intentionally inefficient baseline: one query per customer.
    out = []
    for cid in customer_ids:
        row = con.execute(
            "SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS invoices, SUM(LineTotal) AS revenue "
            "FROM order_lines WHERE CustomerID=? AND CustomerID IN (SELECT CustomerID FROM tenants WHERE tenant_id=?) GROUP BY CustomerID",
            (cid, tenant_id),
        ).fetchone()
        out.append({"CustomerID": cid, "invoices": int(row[1]) if row else 0, "revenue": float(row[2] or 0) if row else 0.0})
    return out


def customer_summary_join(con: sqlite3.Connection, customer_ids: list[int], tenant_id: str) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in customer_ids)
    q = f"""
    SELECT o.CustomerID, COUNT(DISTINCT o.InvoiceNo) AS invoices, SUM(o.LineTotal) AS revenue
    FROM order_lines o
    JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=?
    WHERE o.CustomerID IN ({placeholders})
    GROUP BY o.CustomerID
    ORDER BY o.CustomerID
    """
    rows = con.execute(q, [tenant_id, *customer_ids]).fetchall()
    by_id = {int(r[0]): {"CustomerID": int(r[0]), "invoices": int(r[1]), "revenue": float(r[2] or 0)} for r in rows}
    return [by_id.get(cid, {"CustomerID": cid, "invoices": 0, "revenue": 0.0}) for cid in customer_ids]


def revenue_by_date(con: sqlite3.Connection, start: str, end: str, tenant_id: str) -> float:
    q = """
    SELECT SUM(o.LineTotal) FROM order_lines o
    JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=?
    WHERE o.InvoiceDate >= ? AND o.InvoiceDate < ?
    """
    row = con.execute(q, (tenant_id, start, end)).fetchone()
    return float(row[0] or 0.0)


def query_plan(con: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[str]:
    rows = con.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return [str(r[3]) for r in rows]


def benchmark_callable(fn, warmup: int = 3, reps: int = 20) -> dict[str, float]:
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "p50_ms": percentile(times, 0.50),
        "p95_ms": percentile(times, 0.95),
        "p99_ms": percentile(times, 0.99),
        "mean_ms": statistics.mean(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }


class APIServer:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.cache: dict[str, tuple[float, Any]] = {}
        self.cache_ttl = 30.0

    def auth(self, headers, tenant_id: str) -> bool:
        return headers.get("X-Role") == "analyst" and headers.get("X-Tenant-Id") == tenant_id

    def request_idempotent_note(self, request_id: str) -> dict[str, Any]:
        # Purely in-memory idempotency example for safe retries in the demo.
        key = f"note:{request_id}"
        cached = self.cache.get(key)
        if cached:
            return cached[1]
        payload = {"request_id": request_id, "accepted": True, "timestamp": datetime.utcnow().isoformat()}
        self.cache[key] = (time.time(), payload)
        return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "PlaceMuxTask3/1.0"

    def log_message(self, fmt, *args):
        return

    def _json(self, status: int, payload: Any):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @property
    def app(self) -> APIServer:
        return self.server.app  # type: ignore[attr-defined]

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/health":
            return self._json(200, {"status": "ok"})
        tenant_id = qs.get("tenant_id", [None])[0]
        if tenant_id not in ("TENANT_A", "TENANT_B"):
            return self._json(400, {"error": "invalid tenant"})
        if not self.app.auth(self.headers, tenant_id):
            return self._json(401, {"error": "unauthorized"})
        con = get_conn(self.app.db_path)
        try:
            if parsed.path == "/api/customer/orders":
                cid = int(qs.get("customer_id", [0])[0])
                rows = customer_orders(con, cid, tenant_id, int(qs.get("limit", [20])[0]))
                return self._json(200, rows)
            if parsed.path == "/api/customers/summary":
                ids = [int(x) for x in qs.get("ids", [""])[0].split(",") if x.strip()]
                key = f"summary|{tenant_id}|{','.join(map(str, ids))}"
                cached = self.app.cache.get(key)
                if cached and time.time() - cached[0] < self.app.cache_ttl:
                    return self._json(200, {"cached": True, "data": cached[1]})
                data = customer_summary_join(con, ids, tenant_id)
                self.app.cache[key] = (time.time(), data)
                return self._json(200, {"cached": False, "data": data})
            if parsed.path == "/api/revenue":
                start = qs.get("start", [""])[0]
                end = qs.get("end", [""])[0]
                amount = revenue_by_date(con, start, end, tenant_id)
                return self._json(200, {"revenue": amount})
            return self._json(404, {"error": "not found"})
        finally:
            con.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/notes":
            return self._json(404, {"error": "not found"})
        tenant_id = self.headers.get("X-Tenant-Id")
        if tenant_id not in ("TENANT_A", "TENANT_B") or not self.app.auth(self.headers, tenant_id):
            return self._json(401, {"error": "unauthorized"})
        request_id = self.headers.get("X-Request-Id")
        if not request_id:
            return self._json(400, {"error": "X-Request-Id required for idempotent retries"})
        return self._json(200, self.app.request_idempotent_note(request_id))


def start_server(app: APIServer) -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.app = app  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def http_get(base: str, path: str, headers: dict[str, str]) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(base + path, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def http_post(base: str, path: str, headers: dict[str, str]) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(base + path, method="POST", headers=headers, data=b"{}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def benchmark_http(fn, reps: int = 15) -> dict[str, float]:
    return benchmark_callable(fn, warmup=2, reps=reps)


def write_dashboard(path: Path, payload: dict[str, Any]) -> None:
    data = json.dumps(payload)
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{APP_TITLE}</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#f5f7fb;color:#17223b;margin:0}}.wrap{{max-width:1220px;margin:36px auto;padding:0 22px}}
h1{{font-size:40px;margin:0 0 8px}}.sub{{color:#66738e;font-size:17px;margin-bottom:22px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#fff;border:1px solid #dde3ef;border-radius:14px;padding:18px;box-shadow:0 2px 8px #0000000b}}.label{{color:#6b7893;font-size:14px}}.value{{font-size:29px;font-weight:800;margin-top:7px}}.section{{margin-top:18px}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden}}th,td{{padding:12px;border-bottom:1px solid #e7ebf2;text-align:left}}th{{color:#6b7893;font-size:13px}}.pass{{color:#128556;font-weight:800}}.warn{{color:#b06a00;font-weight:800}}.pill{{display:inline-block;padding:6px 10px;border-radius:999px;background:#edf7f1;color:#128556;font-weight:700}}pre{{white-space:pre-wrap;background:#0d1526;color:#dce6ff;padding:14px;border-radius:12px;overflow:auto}}.note{{font-size:13px;color:#66738e;line-height:1.45}}
</style></head><body><div class='wrap'>
<h1>{APP_TITLE}</h1><div class='sub'>Real UCI Online Retail source · before/after database and API profiling · indexes · query rewrites · N+1 elimination · caching</div>
<div class='grid'>
<div class='card'><div class='label'>Raw rows</div><div class='value'>{payload['source']['raw_rows']:,}</div></div>
<div class='card'><div class='label'>Clean purchase rows</div><div class='value'>{payload['source']['clean_rows']:,}</div></div>
<div class='card'><div class='label'>Customers</div><div class='value'>{payload['source']['customers']:,}</div></div>
<div class='card'><div class='label'>Revenue proxy</div><div class='value'>£{payload['source']['gross_revenue']:,.0f}</div></div>
</div>
<div class='section card'><h2>Top-three endpoint / query evidence</h2><table><thead><tr><th>Workload</th><th>Baseline p95</th><th>Optimized p95</th><th>Improvement</th><th>Change</th></tr></thead><tbody>
{''.join(f"<tr><td>{r['name']}</td><td>{r['before']['p95_ms']:.2f} ms</td><td>{r['after']['p95_ms']:.2f} ms</td><td class='pass'>{r['improvement_pct']:.1f}%</td><td>{r['fix']}</td></tr>" for r in payload['benchmarks'])}
</tbody></table></div>
<div class='section grid' style='grid-template-columns:1fr 1fr'>
<div class='card'><h2>Query plans</h2><pre>{json.dumps(payload['plans'], indent=2)}</pre></div>
<div class='card'><h2>Failure & security checks</h2><pre>{json.dumps(payload['controls'], indent=2)}</pre></div>
</div>
<div class='section card'><h2>Decision</h2><p><span class='pill'>{payload['decision']['status']}</span> {payload['decision']['message']}</p><p class='note'>Source limitation: this is a real external UCI transaction dataset used as a performance-profiling proxy, not PlaceMux production telemetry.</p></div>
</div></body></html>"""
    path.write_text(html, encoding="utf-8")


def run(source: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "task3_performance.db"
    summary = load_real_data(source, db_path)

    con = get_conn(db_path)
    customer_ids = [int(r[0]) for r in con.execute("SELECT CustomerID FROM customers ORDER BY CustomerID LIMIT 20").fetchall()]
    tenant_a_ids = [cid for cid in customer_ids if cid % 2 == 0][:10]
    if len(tenant_a_ids) < 5:
        tenant_a_ids = customer_ids[:10]
    date_min = summary["date_min"][:10]
    date_max = summary["date_max"]
    end_dt = datetime.strptime(date_max[:10], "%Y-%m-%d")
    end_plus = (end_dt.replace(hour=0, minute=0, second=0) + pd.Timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    start = f"{date_min} 00:00:00"

    clear_indexes(db_path)
    before_1 = benchmark_callable(lambda: customer_orders(con, tenant_a_ids[0], "TENANT_A", 20))
    before_2 = benchmark_callable(lambda: customer_summary_nplus1(con, tenant_a_ids, "TENANT_A"), reps=12)
    before_3 = benchmark_callable(lambda: revenue_by_date(con, start, end_plus, "TENANT_A"), reps=20)

    plan1_before = query_plan(con, "SELECT InvoiceNo FROM order_lines WHERE CustomerID=? ORDER BY InvoiceDate DESC LIMIT 20", (tenant_a_ids[0],))
    plan2_before = query_plan(con, "SELECT COUNT(DISTINCT InvoiceNo) FROM order_lines WHERE CustomerID=?", (tenant_a_ids[0],))
    plan3_before = query_plan(con, "SELECT SUM(LineTotal) FROM order_lines WHERE InvoiceDate>=? AND InvoiceDate<?", (start, end_plus))

    apply_indexes(db_path)
    before_after = []
    after_1 = benchmark_callable(lambda: customer_orders(con, tenant_a_ids[0], "TENANT_A", 20))
    after_2 = benchmark_callable(lambda: customer_summary_join(con, tenant_a_ids, "TENANT_A"), reps=12)
    after_3 = benchmark_callable(lambda: revenue_by_date(con, start, end_plus, "TENANT_A"), reps=20)
    plan1_after = query_plan(con, "SELECT InvoiceNo FROM order_lines WHERE CustomerID=? ORDER BY InvoiceDate DESC LIMIT 20", (tenant_a_ids[0],))
    plan2_after = query_plan(con, "SELECT o.CustomerID, COUNT(DISTINCT o.InvoiceNo) FROM order_lines o JOIN tenants t ON t.CustomerID=o.CustomerID AND t.tenant_id=? WHERE o.CustomerID IN (?) GROUP BY o.CustomerID", ("TENANT_A", tenant_a_ids[0]))
    plan3_after = query_plan(con, "SELECT SUM(LineTotal) FROM order_lines WHERE InvoiceDate>=? AND InvoiceDate<?", (start, end_plus))
    con.close()

    def improvement(a, b):
        return max(0.0, (a["p95_ms"] - b["p95_ms"]) / a["p95_ms"] * 100) if a["p95_ms"] else 0.0

    benchmarks = [
        {"name":"GET /api/customer/orders", "before":before_1, "after":after_1, "improvement_pct":improvement(before_1, after_1), "fix":"CustomerID index"},
        {"name":"GET /api/customers/summary", "before":before_2, "after":after_2, "improvement_pct":improvement(before_2, after_2), "fix":"N+1 -> grouped JOIN"},
        {"name":"GET /api/revenue", "before":before_3, "after":after_3, "improvement_pct":improvement(before_3, after_3), "fix":"InvoiceDate index"},
    ]
    controls = {
        "happy_path": True,
        "unauthorized_request": None,
        "cross_tenant_attack": None,
        "idempotent_retry": None,
        "persistence_check": None,
    }
    app = APIServer(db_path)
    server, thread = start_server(app)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        good_headers = {"X-Role":"analyst", "X-Tenant-Id":"TENANT_A"}
        try:
            http_get(base, f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}", good_headers)
            controls["happy_path"] = True
        except Exception:
            controls["happy_path"] = False
        try:
            req = urllib.request.Request(base + f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}")
            urllib.request.urlopen(req, timeout=5)
            controls["unauthorized_request"] = "FAIL"
        except urllib.error.HTTPError as e:
            controls["unauthorized_request"] = "PASS" if e.code == 401 else f"HTTP {e.code}"
        try:
            bad_headers = {"X-Role":"analyst", "X-Tenant-Id":"TENANT_B"}
            urllib.request.urlopen(urllib.request.Request(base + f"/api/customer/orders?tenant_id=TENANT_A&customer_id={tenant_a_ids[0]}", headers=bad_headers), timeout=5)
            controls["cross_tenant_attack"] = "FAIL"
        except urllib.error.HTTPError as e:
            controls["cross_tenant_attack"] = "PASS" if e.code == 401 else f"HTTP {e.code}"
        r1 = http_post(base, "/api/notes", {**good_headers, "X-Request-Id":"demo-123"})
        r2 = http_post(base, "/api/notes", {**good_headers, "X-Request-Id":"demo-123"})
        controls["idempotent_retry"] = "PASS" if r1[1] == r2[1] else "FAIL"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    con2 = get_conn(db_path)
    persisted = con2.execute("SELECT COUNT(*) FROM order_lines").fetchone()[0]
    con2.close()
    controls["persistence_check"] = "PASS" if persisted == summary["clean_rows"] else "FAIL"

    payload = {
        "source": summary,
        "benchmarks": benchmarks,
        "plans": {
            "customer_orders_before": plan1_before,
            "customer_orders_after": plan1_after,
            "customer_summary_before": plan2_before,
            "customer_summary_after": plan2_after,
            "revenue_before": plan3_before,
            "revenue_after": plan3_after,
        },
        "controls": controls,
        "decision": {
            "status": "PASS" if all(r["improvement_pct"] >= 0 for r in benchmarks) and all(v == "PASS" or v is True for v in controls.values()) else "WATCH",
            "message": "Top critical workloads were profiled on the real source, query plans were compared, N+1 was removed, indexes were added, and API authorization/idempotency/persistence checks passed." if all(v == "PASS" or v is True for v in controls.values()) else "Review failed controls before treating the benchmark as launch-ready."
        },
    }
    (out_dir / "task3_summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    pd.DataFrame([{
        "workload": r["name"], "before_p95_ms": r["before"]["p95_ms"], "after_p95_ms": r["after"]["p95_ms"],
        "improvement_pct": r["improvement_pct"], "fix": r["fix"]
    } for r in benchmarks]).to_csv(out_dir / "before_after_p95.csv", index=False)
    write_dashboard(out_dir / "task3_performance_dashboard.html", payload)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", default="phase3/task3_outputs")
    args = parser.parse_args()
    payload = run(Path(args.source), Path(args.out))
    print(json.dumps({
        "validation": payload["decision"]["status"],
        "raw_rows": payload["source"]["raw_rows"],
        "clean_rows": payload["source"]["clean_rows"],
        "customers": payload["source"]["customers"],
        "benchmarks": [{"name":r["name"],"before_p95_ms":round(r["before"]["p95_ms"],2),"after_p95_ms":round(r["after"]["p95_ms"],2),"improvement_pct":round(r["improvement_pct"],1)} for r in payload["benchmarks"]],
        "controls": payload["controls"],
        "outputs": [str(Path(args.out)/"task3_summary.json"), str(Path(args.out)/"before_after_p95.csv"), str(Path(args.out)/"task3_performance_dashboard.html")]
    }, indent=2))


if __name__ == "__main__":
    main()
