# College-Value Dashboard Model

Logical entities: College, Student, Application, Company Engagement.

Relationships: College 1-to-many Student; Student 1-to-many Application; College 1-to-many Company Engagement; Company 1-to-many Company Engagement. Stable IDs are college_id, student_id, application_id.

The analytical layer preserves student-level eligibility and profile readiness, application lifecycle stage and company engagement outcomes. College KPIs are derived from these governed grains to avoid mixing student counts with application counts.
