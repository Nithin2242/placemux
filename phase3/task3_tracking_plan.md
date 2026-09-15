# Task 3 Performance Observation Contract

| Field | Definition |
|---|---|
| workload_id | Stable identifier for a profiled endpoint/query |
| endpoint | API route under test |
| query_shape | Parameterized SQL shape |
| tenant_id | Explicit tenant partition used in security predicates |
| request_id | Retry/idempotency key for writes |
| started_at / completed_at | Profiling timestamps |
| duration_ms | End-to-end duration |
| status_code | API response status |
| cache_hit | Whether the cache served the request |
| query_plan | EXPLAIN QUERY PLAN output |
| before_p95_ms / after_p95_ms | Benchmark evidence |
| fix_type | index / rewrite / N+1 / cache |

## Acceptance gates

- p95 measured over repeated runs, not one request.
- Query plan captured before and after the fix.
- Authorization enforced before data access.
- Tenant predicate included in every tenant-scoped query.
- Retry behavior is idempotent for write operations.
- Persistence is proven with a reread from the database.
