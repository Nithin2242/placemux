# A/B Experiment Tracking Plan

## Purpose
Provide an auditable event contract for experiment assignment, exposure, outcome measurement, data-subject rights, and resilience checks.

## Stable identifiers
`experiment_id`, `subject_id`, `assignment_id`, `exposure_id`, `event_id`, `application_id`, `consent_version`.

## Required events

| Event | Required properties | Purpose |
|---|---|---|
| `experiment_eligible` | experiment_id, subject_id, eligibility_reason, consent_version, event_id, occurred_at | Prove eligibility before assignment |
| `experiment_assigned` | experiment_id, subject_id, assignment_id, variant, assignment_rule_version, event_id, occurred_at | Record stable arm assignment |
| `experiment_exposed` | experiment_id, subject_id, exposure_id, variant, surface, event_id, occurred_at | Confirm actual treatment/control exposure |
| `application_started` | experiment_id, subject_id, application_id, variant, event_id, occurred_at | Guardrail / secondary outcome |
| `application_submitted` | experiment_id, subject_id, application_id, variant, event_id, occurred_at | Primary outcome |
| `interview_completed` | experiment_id, subject_id, application_id, variant, event_id, occurred_at | Downstream guardrail |
| `offer_received` | experiment_id, subject_id, application_id, variant, event_id, occurred_at | Downstream outcome |
| `consent_withdrawn` | subject_id, consent_version, reason_code, event_id, occurred_at | Stop future experimentation processing |
| `deletion_requested` | subject_id, request_id, event_id, occurred_at | Trigger governed deletion workflow |

## Assignment rules
1. Determine eligibility before assignment.
2. Use a stable deterministic allocation function based on `subject_id` and an approved assignment-rule version.
3. Persist `assignment_id`, variant, and assignment-rule version.
4. Prevent re-assignment after first valid assignment unless a new experiment version is explicitly created.
5. Exclude holdouts, internal/test subjects, and policy-defined exclusions before assignment.

## Exposure rules
- An assignment is not an exposure.
- Primary analysis may use exposed eligible subjects for the demo; production should pre-register whether intent-to-treat, treatment-on-exposed, or both will be reported.
- Exposure must carry the same experiment and variant IDs as assignment.
- Do not count an exposure after consent withdrawal or deletion request is effective.

## Data-subject controls
- Do not use direct identifiers in analytical exports.
- Consent and purpose metadata must be versioned.
- Deletion and withdrawal events must suppress future exposure and be represented in validation outputs.
- Derived experiment datasets should follow the governed retention/deletion workflow.
- Access to subject-level records follows least privilege and need-to-know.

## Resilience / QA rules
- Unique event IDs and subject IDs at the expected grain.
- No exposed subject without valid eligibility and assignment.
- Variant must match the immutable assignment for the experiment.
- Control/treatment allocation imbalance must remain within the approved tolerance.
- Event timestamps should preserve lifecycle order.
- Backfills must be versioned and auditable.
- Any failed integrity or rights check blocks production experiment reporting until resolved.
