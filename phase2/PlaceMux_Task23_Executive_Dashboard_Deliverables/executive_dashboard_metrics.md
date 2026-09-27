# Executive Dashboard Metrics

## Purpose
Executive reporting for placement outcomes, marketplace activity, reliability and MLOps health.

## Core metrics
- Registered Students = distinct student records.
- Eligible Students = students meeting the governed eligibility rule.
- Placement Rate = distinct placed students / eligible students x 100.
- Offer Rate = offer-stage applications / applications x 100.
- Average Package = mean package value among placed students with a valid package.
- API Availability = successful service time / observed service time x 100.
- P95 Latency = 95th percentile request latency for the reporting period.
- Data Freshness = minutes between latest trusted data timestamp and report refresh.
- Model Drift PSI = population stability index on governed model monitoring features.
- Pipeline Success = successful scheduled pipeline runs / total scheduled runs x 100.

All dashboard values in the dry run are synthetic demonstration metrics.
