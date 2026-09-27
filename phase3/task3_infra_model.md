# Task 3 Infrastructure Model

## Components
- HTTP service layer
- SQLite persistence layer
- bounded connection pool
- TTL cache
- warm-start initializer
- load-test client
- machine-readable validation outputs

## Blast radius
The optimization changes DB connection lifecycle, repeat-read behavior and concurrency assumptions for the local service. It does not mutate source data semantics. The only intentional failure mode in the rehearsal is pool exhaustion under an explicitly undersized configuration.

## Rollback
All behavior is configuration-controlled. Disable pooling, caching and warm-start flags to restore baseline behavior. No manual console state is required.
