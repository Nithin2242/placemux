# Launch Monitoring Data Model

## Entities
- Metric registry: governed definition, owner, threshold and refresh SLA.
- Monitoring observation: timestamped metric value and derived status.
- Alert event: threshold breach or watch trigger with owner and response metadata.
- Launch decision: current aggregate state derived from critical KPI statuses.

## Grain
One monitoring observation per metric per timestamp.

## Key relationships
metric_registry.metric_id -> monitoring_observation.metric_id -> alert/decision state.

## Decision rule
Overall status = BLOCKED if any Critical KPI is BLOCKED; otherwise WATCH if any KPI is WATCH; otherwise PASS.
