# Task 3 Infrastructure Tracking & Runbook

| Signal | Definition | Source | Decision |
|---|---|---|---|
| p50 latency | median request latency | load-test timings | detect normal-path regressions |
| p95 latency | 95th percentile request latency | load-test timings | primary performance gate |
| throughput | successful requests completed per benchmark window | load-test harness | capacity planning |
| error rate | non-200 responses / requests | server responses | failure detection |
| pool exhaustion | requests that cannot acquire a DB connection within timeout | pool | scale pool / reduce concurrency |
| cache hit path | requests served from TTL cache | service cache | reduce DB load |
| warm-start benefit | first-request versus warmed benchmark latency | service timings | cold-start mitigation |

### 3am runbook
1. Check p95 latency and error rate.
2. Check connection-pool exhaustion.
3. Confirm cache freshness/TTL and cache error rate.
4. Compare current workload concurrency against configured capacity.
5. Roll back the optimization flags if error rate rises while latency is still healthy.
6. Re-run the benchmark before re-enabling the change.
