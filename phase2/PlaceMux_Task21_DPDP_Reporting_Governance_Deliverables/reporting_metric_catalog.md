# PlaceMux Task 21 - Governed Metric Catalog Template

This template standardizes the metadata required before a metric is treated as certified reporting.

| Field | Required | Example |
|---|---|---|
| metric_name | Yes | Application-to-Payment Rate |
| business_definition | Yes | Paid applications divided by submitted applications |
| formula | Yes | paid_applications / submitted_applications |
| numerator | When applicable | Distinct applications reaching paid state |
| denominator | When applicable | Distinct submitted applications |
| grain | Yes | application_id |
| source | Yes | Governed application/payment events |
| transformation | Yes | Validated lifecycle aggregation |
| owner | Yes | Analytics owner |
| reviewer | Yes | Assigned reviewer |
| refresh_cadence | Yes | Daily / event-driven / agreed SLA |
| freshness_sla | Yes | Approved reporting window |
| data_classification | Yes | Internal / Restricted / Sensitive |
| version | Yes | v1.0 |
| effective_date | Yes | Release date |
| limitations | Yes | Known coverage or attribution constraints |
| validation_status | Yes | CERTIFIED / STALE / DEGRADED / BLOCKED |

## Certification Rule

A metric may be labelled **CERTIFIED** only when its definition, lineage, owner, freshness requirement and applicable quality controls are documented and the current validation state is acceptable.
