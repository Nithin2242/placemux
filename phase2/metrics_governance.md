# Task 24 - Metrics Governance

## Purpose
Lock the launch KPI layer before release so executive and operational reporting uses certified definitions, owners, freshness rules, and validation gates.

## Core launch KPIs
| Metric | Definition | Formula | Grain | Owner | Refresh | Release rule |
|---|---|---|---|---|---|---|
| Eligible Students | Students satisfying the launch eligibility rule | distinct eligible student_id | student | College Analytics | daily | certified |
| Applications Submitted | Valid submitted applications in the reporting window | distinct application_id with submitted state | application | Marketplace Analytics | hourly | certified |
| Offers | Offers issued to eligible candidates | distinct offer_id with offer_sent | offer | Recruiter Analytics | hourly | certified |
| Placements | Candidates with a confirmed placement outcome | distinct student_id with placement_confirmed | student | College Analytics | daily | certified |
| Placement Rate | Share of eligible students with placement | placed students / eligible students | student-period | College Analytics | daily | certified |
| Offer Rate | Share of submitted applications reaching an offer | offers / submitted applications | application-period | Recruiter Analytics | hourly | certified |
| Active Companies | Companies with a qualifying marketplace action | distinct company_id with active event | company | Marketplace Analytics | daily | certified |
| Revenue | Recognized marketplace revenue | sum of governed recognized revenue | payment | Finance Analytics | daily | certified |

## Governance requirements
Every launch metric must have: business definition, formula, numerator, denominator where applicable, grain, source, transformation logic, owner, reviewer, refresh SLA, freshness status, version, exclusions, and validation checks.

## Certification states
- **CERTIFIED**: all mandatory controls pass and freshness is within SLA.
- **STALE**: source or derived layer exceeds freshness SLA.
- **DEGRADED**: metric is available but one or more non-blocking quality thresholds are breached.
- **BLOCKED**: critical validation, reconciliation, lineage, or ownership control fails.

## Launch gates
1. No duplicate metric IDs or names.
2. Every KPI has an owner and reviewer.
3. Every formula has an explicit numerator/denominator or aggregation rule.
4. Source and refresh metadata are present.
5. Critical metrics reconcile to their governed source.
6. No certified KPI is stale or blocked.
7. Deprecated metrics are excluded from launch views.
8. Version and change reason are recorded.

## Change policy
Any definition, source, denominator, or transformation change requires version increment, owner review, impact note, and downstream dashboard inventory check.

## Demo scope
This task uses a synthetic governance registry and validation run. It demonstrates the controls; it is not a production financial, placement, or compliance certification.
