
---

# 2. `phase2/revenue_dashboard_model.md`

Paste:

```markdown
# Monetization Integration & Revenue Dashboard Model

## Purpose

This document defines the logical model used to integrate the Phase 2
monetization views into one revenue dashboard.

---

# Architecture

```text
                  ┌──────────────────────────┐
                  │ Day 26 Payment Events    │
                  │ payment_events_demo.csv  │
                  └────────────┬─────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ↓             ↓             ↓
             Revenue        Customer       Payment
             Metrics        Revenue        Health
                 │             │             │
                 ↓             ↓             ↓
             ARPU          Cohorts       Refunds/
                                           Failures

                  ┌──────────────────────────┐
                  │ Day 27 Application Flow  │
                  └────────────┬─────────────┘
                               ↓
                      Application Conversion

                               ↓

                  ┌──────────────────────────┐
                  │ Integrated Revenue       │
                  │ Dashboard                │
                  └──────────────────────────┘