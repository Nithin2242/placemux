# Executive Dashboard Tracking Plan

Required business keys: student_id, application_id, college_id/company_id, recruiter_id, report_date.
Operational keys: run_id, pipeline_id, model_version.

Minimum events/signals: application submitted, interview stage entered, offer created, placement recorded, pipeline run completed, data freshness check, model drift measurement, service availability and latency observation.

Governance: certified metrics use governed definitions; sensitive subject-level data stays outside executive aggregates; dashboards must display freshness and validation state.
