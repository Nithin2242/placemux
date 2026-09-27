
---

# 2. `phase2/refund_failure_tracking_plan.md`

Paste:

```markdown
# Refund & Failure Tracking Plan

## Purpose

This tracking plan defines the events and properties required to
support refund, payment-failure, chargeback, and reconciliation
analytics.

The Day 28 task requires refund/failure analytics and a live
refund/failure dashboard.

---

# Event Taxonomy

The payment lifecycle uses:

```text
payment_initiated
payment_authorized
payment_failed
payment_captured
payment_refunded
payment_chargeback
revenue_recognized