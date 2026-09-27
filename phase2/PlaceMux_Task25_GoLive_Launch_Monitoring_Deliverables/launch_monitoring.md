# Task 25 - Go-Live Launch Monitoring

## Scope
Build a launch monitoring layer that gives leadership and operators a clear live view of business KPIs, reliability, data freshness, MLOps health, alert thresholds and launch decision rules.

## Demonstration approach
Synthetic deterministic monitoring data is used because the task brief does not provide production telemetry. The dashboard is explicitly labeled as a synthetic launch rehearsal.

## Monitoring states
- PASS: metric is within the approved target.
- WATCH: metric is close to its approved threshold and needs active monitoring.
- BLOCKED: threshold breach that blocks launch for the governed metric.

## Go-live gate
Proceed only when no launch-critical KPI is BLOCKED, data freshness remains within SLA, and all WATCH metrics have an assigned owner and response path.

## Current rehearsal snapshot
Overall status: **WATCH**

PASS: **8**  |  WATCH: **4**  |  BLOCKED: **0**

Watch items are API p95 latency (710 ms vs 750 ms ceiling) and model drift (PSI 0.085 vs 0.10 ceiling). No blocking breach is present in the synthetic run.

## Reproduction
```bash
python phase2/launch_monitoring_demo.py
open phase2/launch_monitoring_dashboard.html
```
