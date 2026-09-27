# A/B Experiment Logical Data Model

## Entities

### Experiment
- `experiment_id` (PK)
- name
- hypothesis
- primary_metric
- analysis_window
- status
- allocation_rule_version
- owner
- approved_at

### Experiment Assignment
- `assignment_id` (PK)
- `experiment_id` (FK)
- `subject_id` (FK)
- variant
- assignment_rule_version
- assigned_at

### Experiment Exposure
- `exposure_id` (PK)
- `experiment_id` (FK)
- `assignment_id` (FK)
- `subject_id` (FK)
- variant
- surface
- exposed_at

### Experiment Outcome Event
- `event_id` (PK)
- `experiment_id` (FK)
- `subject_id` (FK)
- `variant`
- event_name
- application_id (nullable)
- occurred_at

### Consent / Rights State
- `subject_id` (PK/FK)
- consent_status
- consent_version
- withdrawal_at
- deletion_requested_at
- effective_at

## Relationships
`Experiment -> Assignment -> Exposure -> Outcome Events`

`Subject -> Consent/Rights State` governs whether assignment/exposure/analysis is allowed.

## Derived analytical view
One row per `experiment_id + subject_id` containing:
- first valid assignment
- first valid exposure
- primary outcome within window
- secondary outcomes
- rights state at exposure
- exclusion reason
- analysis population flag

## Governance principles
- Immutable experiment metadata after launch except through versioned change control.
- Preserve assignment history; never overwrite the original arm silently.
- Keep event-level facts for auditability and aggregated results for routine reporting.
- Separate experiment design metadata from subject-level event data.
- Make the denominator definition and decision rule explicit in the experiment record.
