# Task 2 - Data Quality Tests & Alerting

## Required checks

### Freshness
Track the maximum source `InvoiceDate` and compare it with the declared refresh expectation. The current external dataset is historical, so the report preserves source coverage date separately from system refresh time. Production should attach ingestion and refresh timestamps.

### Volume
Source row count must be non-zero. Unexpected day-over-day volume changes should trigger a warning or block according to the metric criticality policy.

### Nulls
Required analytical fields are checked for nulls. `CustomerID` is allowed to be null in the raw source but its rate is surfaced explicitly because it affects customer-level reporting.

### Uniqueness
Full-row duplication is checked. Production event/transaction keys should additionally be unique at their governed grain.

### Semantic validity
Cancellation state, quantity sign and price positivity are evaluated before the valid-purchase metric is calculated.

## Alert states

- **PASS** - within the approved tolerance.
- **WATCH** - near threshold; owner action required.
- **BLOCKED** - critical metric cannot be trusted until the issue is resolved.

## Failure path

The demo intentionally tampers with one dashboard metric after calculation. The parity validator must detect the mismatch and report failure. The original semantic value remains unchanged, demonstrating that downstream surfaces should be blocked from silently diverging.
