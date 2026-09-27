# Marketplace Liquidity Dashboard Metrics

## Purpose

This document defines the proposed metrics for the PlaceMux Marketplace
Liquidity Dashboard.

The Day 25 brief focuses on shipping the liquidity dashboard and making
the marketplace liquidity dashboard live.

The metrics below combine the Phase 2 marketplace instrumentation
developed across:

- Marketplace health metrics
- Job supply
- Search & Discovery
- Applications & Shortlisting

The current demonstration uses synthetic event streams.

---

# Marketplace Liquidity

Liquidity describes how effectively marketplace demand and supply
interact and progress toward useful outcomes.

The dashboard therefore combines:

- Buyer / company activity
- Seller / job-supply activity
- Search and discovery
- Applications
- Matching
- Successful outcomes

---

# 1. Active Buyers

## Definition

Number of distinct companies that actively participate in discovery
during the selected reporting period.

## Demonstration Calculation

```text
Active Buyers =
COUNT(DISTINCT company_id)