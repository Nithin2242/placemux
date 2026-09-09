# Company Funnel Metrics

## Purpose

This document defines a proposed company-side funnel for the PlaceMux marketplace.

The Day 23 brief focuses on Search & Discovery and requires a live company funnel view. The brief does not prescribe exact funnel stages or formulas, so the definitions below are proposed for implementation and validation.

---

# Company-Side Funnel

The proposed company journey is:

Search
→ Search Result Viewed
→ Candidate / Listing Viewed
→ Contact Initiated
→ Application / Engagement Started
→ Match Created
→ Successful Outcome

This funnel is intended to measure progression from discovery to meaningful marketplace engagement.

---

# 1. Searches Performed

## Definition

Number of distinct search actions performed by companies during the selected period.

## Calculation

```text
Distinct Search Sessions =
COUNT(DISTINCT search_id)