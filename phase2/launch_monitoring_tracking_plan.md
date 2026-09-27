# Launch Monitoring Tracking Plan

## Required monitoring domains
Business outcomes, reliability, data quality/freshness, MLOps and marketplace responsiveness.

## Required fields
metric_id, metric_name, category, unit, value, target, direction, observed_at, owner, refresh_sla, criticality, status.

## Monitoring rules
1. Every launch KPI has one approved target and direction.
2. Current status is derived from governed thresholds, not manual labels.
3. Critical metrics are launch blocking when status is BLOCKED.
4. WATCH requires an owner and response path.
5. Missing or duplicate monitoring rows fail the validation job.
6. The dashboard must expose freshness and the monitoring timestamp.
