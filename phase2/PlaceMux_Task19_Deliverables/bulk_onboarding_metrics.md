# Task 19 - Bulk Onboarding & Recruiter Dashboard Metrics

## Scope
A demo-ready recruiter dashboard that connects bulk onboarding quality with recruiter-side candidate pipeline visibility. Because the task brief does not provide a production dataset, this implementation uses a deterministic synthetic demonstration stream.

## Core metrics
| Metric | Definition | Formula | Grain |
|---|---|---|---|
| Onboarding Batches | Distinct bulk-upload jobs received | COUNT(DISTINCT batch_id) | batch |
| Rows Uploaded | Total candidate rows received | SUM(rows_uploaded) | reporting period |
| Rows Accepted | Rows that pass validation | SUM(rows_accepted) | reporting period |
| Import Acceptance | Share of rows accepted | rows_accepted / rows_uploaded | reporting period |
| Batch Completion | Completed batches / all batches | completed / total | reporting period |
| Avg Processing Time | Mean processing duration | SUM(processing_minutes) / batches | batch |
| Active Recruiters | Recruiters with non-failed onboarding activity | COUNT(DISTINCT recruiter_id) | reporting period |
| Applications | Candidate applications represented in recruiter view | COUNT(DISTINCT application_id) | reporting period |
| Shortlisted | Applications currently at shortlist or beyond | COUNT DISTINCT by stage rule | reporting period |
| Interviews | Applications at interview stage or beyond | COUNT DISTINCT by stage rule | reporting period |
| Offers | Applications at offer stage or beyond | COUNT DISTINCT by stage rule | reporting period |
| Placements | Applications with placed outcome | COUNT DISTINCT where stage=Placed | reporting period |

## Denominator discipline
Acceptance uses uploaded rows as its denominator. Batch completion uses all onboarding batches. Funnel stage conversion uses the immediately preceding valid stage. These denominators are intentionally kept separate so a high-volume import does not distort downstream pipeline rates.

## Data quality
The demo validates unique batch/candidate/application identifiers, row arithmetic (uploaded = accepted + rejected), required recruiter/company identifiers, and application-to-candidate relationships.
