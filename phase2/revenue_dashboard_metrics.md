# Monetization Integration & Revenue Dashboard Metrics

## Purpose

This document defines the integrated revenue dashboard for PlaceMux
Phase 2 Task 10.

The task focuses on shipping a revenue dashboard and making that
dashboard live and demonstrable.

The dashboard integrates the following existing Phase 2 analytical
layers:

1. Day 26 payment and revenue metrics
2. Day 27 Pay-per-Application conversion
3. Day 28 refund/failure/reconciliation analytics
4. Day 29 ARPU and cohort revenue

---

# Important Data Design Principle

The Day 26, Day 27, Day 28, and Day 29 demonstrations are not one
single production event stream.

Therefore:

- Day 26 is the authoritative demonstration source for payment,
  revenue, refund, chargeback, ARPU, and cohort revenue metrics.
- Day 27 is used for the Pay-per-Application conversion layer.
- Day 28 is used for payment-health and reconciliation evidence.
- Day 29 is based on the same Day 26 payment source and provides
  customer-level monetization and cohort views.

Revenue values from separate demonstration streams are NOT added
together.

This prevents double counting and preserves traceability.

---

# 1. Gross Payment Volume

## Definition

Total value of successfully captured payment transactions.

## Formula

```text
Gross Payment Volume =
SUM(captured payment amount)