# Offer Funnel Tracking Plan

## Purpose

This document defines the event instrumentation required to measure the
PlaceMux offer-generation and e-sign funnel for Phase 2.

The tracking plan supports:

- Offer creation
- Offer delivery
- Offer engagement
- Offer acceptance
- E-sign initiation
- E-sign completion
- Offer finalization
- Funnel conversion
- Funnel drop-off
- Offer turnaround-time analysis

The Day 31 task is a metric-definition and instrumentation design task.
No production performance results are claimed.

---

# 1. Identifier Model

The offer lifecycle should use stable identifiers throughout the journey.

```text
offer_id
application_id
candidate_id
company_id
e_sign_id
event_id