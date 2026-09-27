# Application Funnel Metrics

## Purpose

This document defines the proposed application and shortlisting funnel
for the PlaceMux marketplace.

The Day 24 task focuses on Applications & Shortlisting and requires a
live application funnel. The task brief does not prescribe exact
funnel stages or formulas, so the definitions below are proposed for
implementation and validation.

---

# Application Funnel

The proposed journey is:

Application Started
→ Application Submitted
→ Application Reviewed
→ Shortlisted
→ Interview / Next Step
→ Selected
→ Successful Outcome

---

# 1. Applications Started

## Definition

Number of distinct application attempts initiated by candidates.

## Calculation

```text
Applications Started =
COUNT(DISTINCT application_id)