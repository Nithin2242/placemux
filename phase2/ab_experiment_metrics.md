# A/B Experiment Metrics

## Purpose
Define a production-ready measurement contract for controlled experiments, with a primary outcome, guardrails, uncertainty, and explicit denominator rules.

## Core metrics

| Metric | Definition | Formula | Grain |
|---|---|---|---|
| Eligible Subjects | Unique subjects meeting consent, rights, product, and experiment eligibility rules | `COUNT(DISTINCT subject_id)` | subject x experiment |
| Exposed Subjects | Eligible subjects who actually received a variant exposure | `COUNT(DISTINCT subject_id WHERE exposure_event)` | subject x experiment |
| Assignment Rate | Share of eligible subjects assigned to a valid arm | `assigned / eligible` | experiment |
| Exposure Rate | Share of assigned subjects with confirmed exposure | `exposed / assigned` | experiment x variant |
| Primary Conversion | Share reaching the pre-registered primary outcome in the analysis window | `primary_success / analysis_population` | experiment x variant |
| Absolute Lift | Treatment minus control primary conversion | `rate_treatment - rate_control` | experiment |
| Relative Lift | Absolute lift divided by control conversion | `(treatment - control) / control` | experiment |
| 95% CI | Uncertainty interval around treatment-control difference | two-proportion normal approximation for demo; governed method in production | experiment |
| P-value | Two-sided test statistic for the primary binary outcome | two-proportion z test in demo | experiment |
| Application Start Rate | Share starting the application in the window | `starts / analysis_population` | experiment x variant |
| Interview Completion Rate | Share completing an interview in the window | `interviews / analysis_population` | experiment x variant |
| Offer Rate | Share receiving an offer in the window | `offers / analysis_population` | experiment x variant |
| Rights Breach Count | Subjects exposed or analyzed after consent withdrawal/deletion exclusion should have been applied | count of rule violations | experiment |

## Denominator rules
- Use a single pre-registered analysis population for the primary result.
- Exclude subjects lacking required consent or with a deletion request/withdrawal before exposure.
- Count each subject once per experiment.
- Use the first valid assignment and first valid exposure for subject-level experiments.
- Do not backfill treatment assignment from outcome behavior.

## Guardrails
Production experiments should define guardrail thresholds before launch. Examples include exposure rate, downstream completion, error rate, latency, complaint rate, and any data-subject rights violation. A statistically positive primary metric does not override a failed guardrail.

## Decision framework
- **Ship:** primary effect meets the pre-registered decision rule and all guardrails pass.
- **Iterate:** direction is promising but uncertainty or guardrails require another test.
- **Stop:** rights, safety, quality, integrity, or severe negative guardrail breach occurs.
- **No decision:** insufficient exposure, missing events, or incomplete analysis coverage.

## Synthetic demo note
The accompanying dry run demonstrates the mechanics only. It does not represent PlaceMux production performance.
