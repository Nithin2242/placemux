# Phase 3 Task 3 - Infrastructure Performance Profile

## Objective
Profile the infrastructure path and remove systemic bottlenecks across database access, connection setup, warm starts, caching and bounded concurrency.

## Data source
The implementation consumes the real UCI Online Retail workbook already used in this project. It is an external real-data proxy, not PlaceMux production telemetry.

## Baseline
The baseline intentionally uses a connection-per-request model, no cache and no warm-start priming.

## Optimized configuration
- bounded SQLite connection pool
- WAL/NORMAL database settings
- warm-start metadata/connection priming
- TTL cache for repeat summary/revenue reads
- bounded client concurrency for repeatable load
- explicit rollback-by-configuration

## Failure rehearsal
The script intentionally creates a one-connection pool and sends an oversubscribed burst. The expected behavior is controlled 503 responses rather than an unbounded hang. `task3_infra_validation.json` records whether this failure path was observed.

## Rollback
Set `pooled=False`, `cache_enabled=False`, `warm=False`, and `pool_size=1` in the config to return to the baseline path. Production rollout would additionally require staged canary traffic and SLO monitoring.
