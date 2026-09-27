# PlaceMux Task 21 - Reporting Governance

## Purpose

Apply compliance-aware reporting governance to the PlaceMux analytics layer so that reports are trustworthy, traceable, privacy-conscious, and safe to use for operational decisions.

This task is a governance and reporting-design task. No production performance dataset is supplied by the brief, so this deliverable defines the control framework rather than inventing production compliance results.

## 1. Governance Principles

1. **Purpose limitation** - collect and report only fields required for an explicit business purpose.
2. **Data minimization** - dashboards should use stable analytical IDs rather than unnecessary personal identifiers.
3. **Traceability** - every KPI must have a definition, source, owner, refresh cadence, and transformation logic.
4. **Access by role** - expose only the minimum information required for each stakeholder role.
5. **Metric consistency** - certified metrics must use a single governed definition across dashboards.
6. **Auditability** - material changes to metric logic, source tables, or access rules must be versioned.
7. **Privacy by default** - reporting layers should avoid displaying sensitive personal attributes unless explicitly required and approved.
8. **Exception visibility** - suppressed, stale, incomplete, or quality-failed data must be signaled rather than silently blended into reporting.

## 2. Reporting Classification

| Reporting Class | Intended Use | Controls |
|---|---|---|
| Executive KPI | Strategic decisions | Certified metric definitions, aggregate-only output, refresh SLA |
| Operational Dashboard | Day-to-day workflow | Role-based access, row-level filters, freshness indicator |
| Analytical Dataset | Investigation | Governed access, documented grain, lineage and quality checks |
| Sensitive Detail | Case-level review | Explicit authorization, minimum necessary fields, audit logging |
| External / Shared Report | Outside internal analytics | Aggregation, privacy review, approved definitions, export controls |

## 3. Core Governance Metadata

Every certified metric should retain:

- Metric name
- Business definition
- Formula
- Numerator and denominator where relevant
- Data grain
- Inclusion and exclusion rules
- Source event/table
- Transformation logic
- Owner
- Reviewer/approver
- Refresh cadence and expected freshness
- Version
- Effective date
- Known limitations
- Data classification

## 4. Data Quality Gates

A report should not be marked certified when a blocking control fails. Minimum gates are:

| Gate | Example Control | Action on Failure |
|---|---|---|
| Completeness | Required IDs and timestamps present | Block affected metric |
| Uniqueness | Primary event/entity IDs are unique | Block affected grain |
| Referential integrity | Child records map to valid parent IDs | Quarantine broken records |
| Valid values | Status/event names match approved taxonomy | Reject invalid values |
| Temporal integrity | Event timestamps follow lifecycle order | Flag or quarantine records |
| Freshness | Source updated within stated SLA | Mark dashboard stale |
| Reconciliation | Derived totals agree with source controls | Hold certification |
| Privacy | Sensitive fields absent from unauthorized layer | Block publication |

## 5. Freshness and Certification Status

Use explicit reporting states:

- **CERTIFIED** - quality gates passed and data is within freshness SLA.
- **STALE** - data is older than the agreed reporting SLA.
- **DEGRADED** - non-blocking quality issues exist and are disclosed.
- **BLOCKED** - a critical quality, privacy, or reconciliation control failed.

Dashboards should display the current status, last successful refresh timestamp, source, and reporting period.

## 6. Role-Based Reporting Access

### Student
View personal application and placement status only.

### College / TPO
View aggregated college performance and authorized student records needed for placement operations.

### Recruiter / Company
View only candidates and applications the recruiter/company is authorized to access.

### Finance / Operations
View required payment and operational metrics, with financial identifiers minimized in reporting views.

### Data / Analytics
Access governed analytical datasets subject to the relevant authorization and audit controls.

### Administrators
Manage access and governance configuration; administrative access should itself be logged.

## 7. Privacy-Safe Reporting Pattern

The default reporting layer should prefer:

`candidate_id`, `company_id`, `college_id`, `application_id`, `offer_id`, and aggregate measures.

Avoid publishing direct contact information, authentication secrets, payment credentials, or unnecessary personal attributes in dashboard datasets. Detailed records should remain in controlled application systems and be joined only when the analytical purpose and authorization require it.

## 8. Metric Change Management

A certified metric change requires:

1. Proposed definition or logic change.
2. Impact assessment on existing dashboards.
3. Version increment.
4. Reviewer approval.
5. Effective date.
6. Backfill decision, when historical comparability is affected.
7. Documentation update.
8. Validation against reconciliation controls.

Definitions must not be silently changed while retaining the same version.

## 9. Reporting Lineage

Minimum lineage path:

`Source Events / Tables -> Validated Layer -> Transformation -> Certified Metric Table -> Dashboard / Report`

Each production dashboard should reference the exact source and metric version used for its displayed KPIs.

## 10. Governance Review Cadence

| Review | Suggested Cadence | Owner |
|---|---|---|
| Data quality checks | Every refresh | Data / Analytics |
| Freshness review | Every refresh | Dashboard owner |
| Metric certification | On release and material change | Analytics owner + reviewer |
| Access review | Periodic | Platform / Admin owner |
| Privacy review | Before new sensitive reporting use | Compliance / designated reviewer |
| Governance framework review | Quarterly or on major system change | Analytics governance owner |

## 11. Release Checklist

Before a governed report is released:

- [ ] Metric definitions are documented and versioned.
- [ ] Source lineage is recorded.
- [ ] Owner and reviewer are assigned.
- [ ] Freshness SLA is stated.
- [ ] Data-quality gates have passed.
- [ ] Sensitive fields are removed or access-controlled.
- [ ] Role permissions are verified.
- [ ] Reconciliation checks pass where applicable.
- [ ] Dashboard status and reporting period are visible.
- [ ] Known limitations are disclosed.

## Status

**Reporting governance applied at the design level.**

The task brief asks for compliance-aware reporting governance and considers the task complete when reporting governance is applied. This deliverable does not claim that production controls have been deployed or that a legal compliance certification has been completed.

## 12. DPDP-Aware Consent and Purpose Controls

Where personal data is used in reporting, the reporting layer should preserve the purpose for which the data was collected and avoid repurposing it without an approved basis. Consent records, where applicable, should be tied to a stable subject identifier and purpose/version rather than treated as a generic account-level flag.

Minimum consent metadata for analytics use:

- `consent_id`
- `subject_id` or governed customer/candidate identifier
- `purpose_code`
- `consent_status`
- `consent_version`
- `captured_at`
- `withdrawn_at` when applicable
- `source_system`
- `record_version`

Reporting extracts should apply the relevant purpose/consent rule before personal data reaches the analytical layer. Withdrawal or change in permission should propagate to downstream reporting according to the organization's approved retention and deletion policy.

## 13. Security Foundations for Reporting

Reporting systems should enforce least privilege, authenticated access, encrypted transport, protected storage, secrets management, audit logs, environment separation, and controlled exports. Production dashboards should not expose passwords, authentication tokens, payment credentials, or other security secrets.

Security incidents or unauthorized access affecting reporting data should trigger the organization's incident-response and escalation process. The reporting layer should retain enough audit information to identify what was accessed or changed without copying unnecessary sensitive content into logs.
