# Phase 3 Task 4 — Horizontal Scale & Load Readiness

This implementation follows the supplied Task 4 brief. It uses the real UCI Online Retail workbook as an explicit external transaction proxy because no PlaceMux production traffic dataset was supplied. It builds monthly demand, rolling seasonal backtests, a six-month forecast, 2x/5x/10x normalized capacity/cost scenarios, documented assumptions, and a deliberate capacity-guardrail failure path.

Important: invoice counts are a transaction-demand proxy, not PlaceMux HTTP request/application traffic. Capacity and cost are normalized planning units, not cloud-provider quotations.
