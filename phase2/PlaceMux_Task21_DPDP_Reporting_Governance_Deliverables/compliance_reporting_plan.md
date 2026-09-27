# PlaceMux Task 21 - Compliance-Aware Reporting Plan

## Objective

Translate the reporting governance framework into a practical reporting lifecycle that analysts and dashboard owners can follow.

## Reporting Lifecycle

`Define Purpose -> Classify Data -> Map Lineage -> Validate -> Apply Access Controls -> Publish -> Monitor Freshness/Quality -> Review Changes`

## Control Matrix

| Area | Control | Evidence | Owner |
|---|---|---|---|
| Purpose | Business use documented | Report metadata | Report owner |
| Data classification | Fields classified before publication | Data dictionary | Data owner |
| Minimization | Unnecessary sensitive fields removed | Schema check | Analyst |
| Access | Role permissions mapped to report | Access matrix | Platform owner |
| Metric governance | Formula and version recorded | Metric catalog | Analytics owner |
| Quality | Completeness/uniqueness/validity checks | Validation output | Data/Analytics |
| Freshness | Refresh timestamp compared with SLA | Freshness monitor | Dashboard owner |
| Reconciliation | Totals agree with governed source controls | Reconciliation result | Analyst |
| Privacy | Unauthorized personal data excluded | Privacy checklist | Designated reviewer |
| Change management | Material changes approved and versioned | Change record | Analytics owner |
| Auditability | Publication/change events logged | Audit record | Platform owner |

## Dashboard Minimum Footer

Each governed dashboard should expose:

- Reporting period
- Last successful refresh
- Data freshness status
- Metric definition/version reference
- Source system or governed dataset
- Data classification
- Known limitations or caveats

## Safe Failure Behaviour

A dashboard should not silently display misleading numbers when a blocking control fails. The report should show **BLOCKED** or **STALE**, identify the affected metric/domain, retain the previous certified snapshot where policy allows, and direct the owner to the underlying validation result.

## Task 21 Acceptance Criteria

The governance layer is considered applied when:

- Reporting classifications are defined.
- Metric certification metadata is defined.
- Data-quality gates are explicit.
- Privacy and access controls are mapped to stakeholder roles.
- Freshness states are standardized.
- Metric changes are versioned and reviewed.
- Reporting lineage is documented.
- Release and monitoring checklists exist.

## Scope Note

This plan is a Phase 3 governance design deliverable. The task brief does not provide production event data or a production compliance audit environment, so no production compliance result is fabricated.
