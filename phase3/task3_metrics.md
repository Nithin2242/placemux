# Phase 3 Task 3 - Performance Profiling & Bottleneck Elimination

## Scope

Task 3 requires a profile of the slowest endpoints and queries, concrete performance fixes, and before/after p95 evidence. This implementation uses the real UCI Online Retail dataset already present in the project as an external performance-profiling proxy. It is not PlaceMux production telemetry.

## Top workloads

1. `GET /api/customer/orders` - customer-scoped order retrieval. Baseline exercises an unindexed CustomerID filter; the optimized path adds a CustomerID index and keeps tenant filtering explicit.
2. `GET /api/customers/summary` - multi-customer summary. Baseline intentionally demonstrates the N+1 pattern; optimized path performs one grouped JOIN.
3. `GET /api/revenue` - date-window revenue aggregation. Optimized path adds an InvoiceDate index.

## Fixes

### Indexes
- `idx_order_customer` on `order_lines(CustomerID)`
- `idx_order_date` on `order_lines(InvoiceDate)`
- `idx_order_stock` on `order_lines(StockCode)`
- `idx_tenant_customer` on `tenants(CustomerID, tenant_id)`

### Query rewrite
The customer summary query is rewritten from one aggregate query per customer to one grouped JOIN with an `IN` set.

### N+1 elimination
The baseline summary deliberately executes one query per customer. The optimized version uses one database round trip for all requested customers.

### Caching
The API caches repeated customer-summary requests for a short TTL. Cache keys include tenant and customer IDs. Production invalidation must be tied to writes affecting the summarized entities; the demo uses a read-only TTL cache because the source is immutable.

## Security and correctness

The demo API requires role and tenant headers, rejects missing authorization, rejects cross-tenant access, and uses explicit tenant predicates in SQL. A POST idempotency example uses `X-Request-Id` to make concurrent/retried requests safe within the demonstration process. The SQLite database is reread after the profiling run to prove persistence.

## Failure modes

The demo explicitly checks unauthorized requests, cross-tenant access, retry idempotency and persistence. Query parameters are parameterized; invalid tenant values are rejected before query execution.

## Run

```bash
python phase3/task3_performance_demo.py --source "data/online_retail/Online Retail.xlsx"
```

Outputs are written under `phase3/task3_outputs/`.
