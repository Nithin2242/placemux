# Task 5 — Reliability Sign-off & Scale Integration

For this task, I built a real-data reliability pipeline to verify that the numbers used for scale decisions are complete, current within the available extract, and reconciled between a source dataset and a warehouse layer.

I used the UCI Online Retail dataset as an external transaction-data proxy because PlaceMux production source-system telemetry was not available. The source file contained 541,909 raw rows. After applying the documented purchase-data cleaning rules, 530,104 valid purchase rows remained, covering 54 weeks from 2010-11-29 to 2011-12-05. The cleaned data contained 19,960 distinct invoices and gross revenue of GBP 10,666,684.54.

A canonical SQLite warehouse table was created from the cleaned source data. I then reconciled source-level and warehouse-level decision metrics including clean row count, distinct invoice count, gross revenue, customer identifier completeness, earliest event date, and latest event date. The canonical source and warehouse values were required to match exactly for counts and within GBP 0.01 for revenue.

Completeness checks also validated required fields and derived values. Invoice identifiers and event timestamps were checked for non-null values, purchase quantities and unit prices were required to be positive, and derived revenue was required to be non-negative.

Freshness was defined carefully because this exercise does not have a live ingestion timestamp or production source-feed clock. Instead of claiming real-world freshness, I verified that the warehouse preserved the source extract's earliest and latest event dates. The latest event-date lag between the source extract and canonical warehouse was therefore zero days within the loaded extract.

I also implemented a deliberate failure-path rehearsal. A separate copy of the warehouse had the latest event window removed. This produced a measurable row-count gap and a stale latest-event date. The reconciliation and freshness controls detected the break, so the failure path was successfully verified without modifying the canonical warehouse.

The final reliability sign-off passes only when completeness, freshness, reconciliation, and failure-path verification all pass. The final validation therefore provides a single sign-off status together with the individual control results.

The main limitation is that the available dataset is an external transaction source and not PlaceMux production telemetry. In addition, no ingestion timestamp is available, so the exercise cannot establish wall-clock freshness relative to the present time. In a production implementation, the same controls should be connected directly to PlaceMux source systems and warehouse tables, using ingestion timestamps, batch identifiers, source-system counts, and production SLAs.
