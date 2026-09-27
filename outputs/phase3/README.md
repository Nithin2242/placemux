# Phase 3 Task 1 - Post-Launch Health

## Scope

Task 1 requires a launch performance report on real data, an evidence-backed ranked problem list, and a Phase-3 analytics backlog tied to decisions.

Because the supplied Task 1 brief contains no PlaceMux production dataset, this implementation uses the real UCI Online Retail dataset as an explicit external-data proxy. Do not call the output PlaceMux production telemetry.

## Run

```bash
cd ~/placemux-day1
python phase3/launch_performance_analysis.py --source "data/online_retail/Online Retail.xlsx"
open phase3/launch_dashboard.html
```

## Outputs

- `launch_performance_metrics.csv`
- `launch_quality.csv`
- `launch_revenue_monthly.csv`
- `launch_problem_rankings.csv`
- `launch_validation.json`
- `launch_dashboard_data.json`
- `launch_dashboard.html`
- `task1_launch_performance_report.md`
- `task1_problem_rankings.md`
- `task1_analytics_backlog.md`

## Source

UCI Machine Learning Repository - Online Retail, DOI 10.24432/C5BW33, CC BY 4.0.

The UCI source reports 541,909 transaction lines and the schema used by the analysis. Existing project work independently verified the cleaned-source facts used as a baseline: 397,884 valid purchase rows, 18,532 invoices, 4,338 identified customers and £8,911,407.90 retained gross revenue.

## Governance / honesty note

This is a real external dataset substitution. It is not evidence about actual PlaceMux launch performance. A future production run should use the exact same calculation contract on PlaceMux source tables.
