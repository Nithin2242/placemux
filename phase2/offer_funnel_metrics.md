# Offer Funnel Metrics

## Purpose

This document defines the offer-generation and e-sign funnel metrics
for PlaceMux Phase 2.

The Day 31 task focuses on:

- Offer funnel metrics
- Offer lifecycle measurement
- E-sign progression
- Drop-off and turnaround analysis

The current task is a metric-definition and instrumentation design task.
No synthetic performance results are required for completion.

---

# Offer Funnel

The proposed offer funnel is:

```text
Offer Created
      ↓
Offer Sent
      ↓
Offer Viewed
      ↓
Offer Accepted
      ↓
E-Sign Initiated
      ↓
E-Sign Completed
      ↓
Offer Finalized