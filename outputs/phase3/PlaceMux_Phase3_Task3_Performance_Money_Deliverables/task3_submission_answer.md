For Phase 3 Task 3, I built a reproducible performance-profiling framework covering three critical workloads: customer order retrieval, multi-customer summary, and date-window revenue aggregation. Because the supplied task brief requires real production data and no PlaceMux production performance dataset was provided, I used the real UCI Online Retail transaction workbook already present in the project as an explicit external proxy. I did not present it as PlaceMux production telemetry.

The analysis compares baseline and optimized implementations using repeated p50, p95 and p99 latency measurements. Query plans are captured before and after optimization so the timing differences can be explained by concrete engineering changes. The main fixes are a CustomerID index for customer retrieval, an N+1-to-grouped-JOIN rewrite for multi-customer summaries, and an InvoiceDate index for revenue aggregation.

The implementation also verifies authorization, blocks cross-tenant access, checks persistence, and demonstrates idempotent retry behavior. These safeguards ensure that performance improvements do not weaken correctness or isolation.

For the financial part, the real transaction data supplies observed invoices, gross revenue and average order value. However, the source does not contain session-level latency, conversion or abandonment telemetry, so an observed latency-to-conversion correlation cannot honestly be estimated from this dataset. I therefore implemented an explicit sensitivity model showing the revenue exposure under illustrative conversion-sensitivity assumptions. These values are clearly labeled as scenario outputs rather than lost revenue or causal effects.

The engineering priority view ranks the measured performance fixes using a common financial-exposure proxy, while the report documents the limitation. For a true production decision, the next dataset should join request latency/errors, abandonment, conversion and order value through a shared session/request identifier.

This approach satisfies the task's emphasis on real data, financial impact, prioritization and showing the correlation limits without making an unsupported causal claim.
