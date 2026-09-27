# PlaceMux Task 19 - Bulk Onboarding & Recruiter Views

## Run
```bash
python recruiter_dashboard_demo.py
```
Then open:
```text
recruiter_dashboard.html
```

## Included views
- Recruiter Overview
- Bulk Onboarding (filters by status/company/recruiter)
- Candidate Pipeline

## Source chain
`recruiter_dashboard_demo.py` -> synthetic CSVs -> validation/metrics JSON -> `recruiter_dashboard.html`

The synthetic data is deterministic (seed 1907) so another run reproduces the same demonstration dataset and KPI totals.
