# Task 19 - Recruiter Dashboard Logical Model

## Entities
- **Recruiter**: recruiter_id, recruiter name, operating location
- **Company**: company_id, company name
- **Onboarding Batch**: batch_id, recruiter_id, company_id, upload timestamp, row counts, processing duration, status
- **Candidate**: candidate_id, batch_id, recruiter_id, company_id, role, stage, import source, skill focus
- **Application**: application_id, candidate_id, recruiter_id, company_id, role, stage, applied_at

## Relationships
Recruiter 1-to-many Onboarding Batch; Company 1-to-many Onboarding Batch; Onboarding Batch 1-to-many Candidate; Candidate 1-to-many Application.

## Recruiter views
1. **Recruiter Overview** - workload, import acceptance, company output, application funnel, validation state.
2. **Bulk Onboarding** - filterable batch register with status, accepted/rejected rows, processing time and quality rate.
3. **Candidate Pipeline** - stage distribution and operational follow-up queue.

## Governance
The dashboard distinguishes operational source data from derived metrics, preserves stable identifiers, and exposes a demo-only label so synthetic figures are not mistaken for PlaceMux production performance.
