
---

# 3. `phase2/offer_funnel_model.md`

Paste:

```markdown
# Offer Funnel Logical Data Model

## Purpose

This document defines the logical data model supporting offer generation,
offer acceptance, e-signature, and offer finalization.

---

# Entity Relationship

```text
Candidate
    │
    │
    └──────────────┐
                   ↓
             Application
                   │
                   │
                   ↓
                 Offer
                   │
           ┌───────┴────────┐
           ↓                ↓
      Offer Events      E-Sign Workflow
                              │
                              ↓
                        E-Sign Events
                              │
                              ↓
                       Offer Finalized