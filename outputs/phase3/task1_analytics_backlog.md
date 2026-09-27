# Phase 3 Task 1 - Analytics Backlog Tied to Decisions

| Priority | Work item | Decision it changes | Evidence |
|---|---|---|---|
| P0 | Customer identity completeness / guest-vs-known model | Can retention and customer value reporting be trusted? | 135,080 raw rows missing CustomerID |
| P0 | Sale/cancellation/return event model | Are order and revenue KPIs aligned with commercial state? | 9,288 cancellation lines; 10,624 non-positive-quantity lines |
| P1 | Pre-publication numeric quality gates | Should a batch publish, quarantine or require review? | 2,517 non-positive-price lines |
| P1 | Cohort retention model | Which acquisition cohorts require intervention? | Current source supports repeat transitions but not a PlaceMux lifecycle |
| P2 | Revenue concentration monitoring | Is commercial risk becoming concentrated? | Customer-level revenue can be recomputed from clean source |
