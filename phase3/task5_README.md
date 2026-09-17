# PlaceMux Phase 3 — Task 5: Reliability Sign-off & Scale Integration

## Goal
Verify that decision-critical data is complete, current within the loaded extract, reconciled between source and warehouse, and safe to use for scale planning.

## Real source
UCI Online Retail: `data/online_retail/Online Retail.xlsx`

This is an external transaction-data proxy, not PlaceMux production telemetry.

## Run
```bash
cd ~/placemux-day1
python phase3/task5_reliability_signoff.py --source "data/online_retail/Online Retail.xlsx"
```

## Outputs
`phase3/task5_outputs/`

- `task5_validation.json`
- `task5_summary.json`
- `task5_assumptions.json`
- `task5_reconciliation_report.csv`
- `task5_completeness_report.csv`
- `task5_freshness_report.csv`
- `task5_failure_rehearsal.json`
- `task5_reliability_dashboard.html`
- `task5_warehouse.db`
- `task5_failure_rehearsal.db`

## Failure rehearsal
The script creates a separate mutated warehouse copy with the latest event window removed, then verifies that reconciliation/freshness controls detect the break. The canonical warehouse remains intact.

## Freshness note
Because there is no live source feed or ingestion timestamp in this exercise, freshness is defined as source-vs-warehouse event-date parity within the loaded extract. The report explicitly avoids claiming wall-clock production freshness.
