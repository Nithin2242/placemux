
---

# 3. `phase2/refund_failure_dashboard.md`

Paste:

```markdown
# Refund & Failure Dashboard

## Purpose

The Refund & Failure Dashboard is the Day 28 operational view for
monitoring failed payments, refunds, chargebacks, and payment-value
reconciliation.

The task requirement is to make refund/failure analytics available
through a live dashboard.

---

# Primary Business Question

> Where are payment failures and payment-value adjustments occurring,
> and does the payment event stream reconcile correctly?

---

# Headline KPIs

The dashboard should show:

```text
Payment Attempts
Failed Payments
Successful Payments
Payment Failure Rate

Refunded Payments
Refund Amount
Refund Value Rate

Chargeback Transactions
Chargeback Amount

Gross Payment Volume
Net Retained Payment Value
Retention Rate

Reconciliation Gap