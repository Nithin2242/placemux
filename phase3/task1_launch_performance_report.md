# Phase 3 Task 1 - Post-Launch Performance Report

## Source decision

The Task 1 brief requires real production data but no PlaceMux production dataset is supplied. This implementation therefore uses the real UCI Online Retail dataset as an explicit external-data proxy. The substitution is disclosed throughout the deliverables; the results must not be described as PlaceMux production telemetry.

**Source:** UCI Machine Learning Repository, Online Retail, DOI 10.24432/C5BW33. The source contains 541,909 transaction lines covering 2010-12-01 through 2011-12-09. The dataset documentation identifies `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, and `Country` as the main fields.

## Launch-performance proxy

The analysis measures four required areas using the source's actual transaction grain:

| Area | Metric | Definition | Decision |
|---|---|---|---|
| Funnel / flow | Clean-purchase retention | valid purchase lines / raw lines | Decide whether the source is fit for commercial reporting |
| Revenue | Retained gross revenue | sum(Quantity x UnitPrice) over valid purchases | Set commercial baseline and prioritise revenue controls |
| Retention | Repeat-purchase continuity | invoice states followed by a later invoice / clean invoices | Size repeat-purchase behaviour before building cohort interventions |
| Quality | Source-quality exception rates | invalid / raw lines by issue type | Prioritise data controls and quarantine rules |

## Reproduction

```bash
cd ~/placemux-day1
python phase3/launch_performance_analysis.py --source "data/online_retail/Online Retail.xlsx"
```

The script writes all metric, quality, problem-ranking, validation and dashboard outputs into `phase3/`.

## Validation principles

Every headline number is derived from source data in the script. Revenue is reconciled from line-level `Quantity * UnitPrice` to the invoice aggregation. Data-quality exceptions are counted before filtering and are presented as separate issue types because they can overlap. The analysis is descriptive and does not claim that an observed retail pattern is causal.

## Current verified source facts

Previous verified executions of the same real UCI Online Retail source in this project recorded:

- 541,909 raw transaction rows
- 397,884 valid purchase rows after removing cancellations, missing CustomerID, non-positive quantities/prices, and missing descriptions
- 18,532 clean invoices
- 4,338 identified customers
- 3,665 stock codes
- £8,911,407.90 retained gross revenue

The same source has already been used in the project for RFM and market-basket analysis. The RFM work retained 4,338 customers, and the market-basket work validated 530,104 valid purchase rows under a broader basket-cleaning rule. Those different row counts reflect different analytical inclusion rules, not conflicting source totals.

## Important limitation

This is not a PlaceMux post-launch dataset. The deliverable is a governed real-data rehearsal using a documented public transaction source because the brief supplies no production export. A production hand-off requires the same model to be run against actual PlaceMux event, payment, retention and quality tables.
