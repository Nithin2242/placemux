# Task 3 Performance Model

## Logical layers

`HTTP request -> authorization -> endpoint handler -> parameterized SQL -> indexes/query plan -> SQLite persistence`

## Performance evidence model

Each workload records a baseline implementation and an optimized implementation. The benchmark compares p50, p95, p99, mean, minimum and maximum latency. The primary launch evidence is the change in p95.

## Security model

Tenant identity is required at the request boundary and repeated in SQL predicates. Cross-tenant requests are rejected. The demo uses an in-memory idempotency store to prove the retry contract; production implementations should persist idempotency keys in the transaction boundary.
